#!/usr/bin/env python3
"""Record every poem — and its headnote (ПРО ВІРШ) — in every language with macOS speech voices.
  docs/audio/<lang>/<n>.m4a        the poem
  docs/audio/<lang>/<n>-note.m4a   the headnote
  docs/audio/manifest.json         {lang: {n: {s: seconds, v: hash}}, "notes": {lang: {n: {s, v}}}}
Uses `say` (Apple voices) and `afconvert` (AAC). The poem is marked up as a reading: a breath at every line end scaled by its
punctuation, a rest between stanzas, a lift on the opening line and on questions, a falling cadence on the closing line of a
stanza and of the poem (these voices honour [[slnc]] and [[pbas]]; inline rate/emphasis are ignored — [[pbas]] is cumulative,
so Pitch() emits deltas). The best installed edition of each voice is used: download "Enhanced"/"Premium" voices in
System Settings → Accessibility → Spoken Content → System voice → Manage Voices, re-run, and only the affected language re-records.
Re-runs skip files whose text hash is unchanged
(<file>.sha), so `python3 tools/make_audio.py [lang …]` after a text edit only re-records what changed.
`v` is what the reader appends as ?v= to the audio URL (cache-busting)."""
import os, json, re, subprocess, hashlib, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "audio")
PREFER = {"uk": ["Lesya (Enhanced)", "Lesya (Premium)", "Lesya"],
          "ru": ["Milena (Premium)", "Milena (Enhanced)", "Milena"],
          "en": ["Ava (Premium)", "Zoe (Premium)", "Samantha (Enhanced)", "Samantha"],
          "es": ["Mónica (Premium)", "Mónica (Enhanced)", "Marisol (Enhanced)", "Mónica"]}
INSTALLED = [re.split(r"\s{2,}", l)[0].strip() for l in subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout.splitlines()]
VOICE = {lang: next(v for v in names if v in INSTALLED) for lang, names in PREFER.items()}
RATE = {"uk": 138, "ru": 138, "en": 138, "es": 145}          # poems: a reading pace (words/min)
NOTE_RATE = {"uk": 150, "ru": 150, "en": 150, "es": 155}     # headnotes: prose
D = json.load(open(os.path.join(ROOT, "docs", "data", "poems.json"), encoding="utf-8"))

def clean(t):
    t = re.sub(r"[„“”«»\"]", "", t.strip())
    t = re.sub(r"\s*[—–]\s*", ", ", t.replace("…", "..."))       # a dash is a pause, spoken as a comma
    return re.sub(r",\s*,", ",", t)

class Pitch:
    """[[pbas ±n]] is relative to the current pitch, so keep the offset and emit only the delta to reach a target"""
    def __init__(self): self.off = 0
    def to(self, target):
        d = target - self.off; self.off = target
        return f"[[pbas {d:+d}]] " if d else ""

def breath(line):
    """pause after a line, from its final punctuation (ms)"""
    t = line.rstrip()
    if t.endswith(("...", "…")): return 750
    if t.endswith(("?", "!")): return 560
    if t.endswith("."): return 520
    if t.endswith((";", ":")): return 430
    if t.endswith((",", "—", "–", "-")): return 360
    return 300                                              # enjambment: a short breath, the thought runs on

def speakable(title, chunks):
    stanzas = [[]]
    for l in (l for c in chunks for l in c):
        if l.strip() == "":
            if stanzas[-1]: stanzas.append([])
        elif re.fullmatch(r"\*(.+)\*", l.strip()): continue          # translator's notes are not read
        else: stanzas[-1].append(l.strip())
    stanzas = [st for st in stanzas if st]
    v, out = Pitch(), []
    if title and title != "* * *": out.append(v.to(1) + clean(title) + " [[slnc 1300]]")
    for si, st in enumerate(stanzas):
        last_st = si == len(stanzas) - 1
        for li, l in enumerate(st):
            first, last = li == 0, li == len(st) - 1
            if last and last_st: t = -2                      # the poem's last line: falls, lands
            elif first: t = 1                                # each stanza opens a little brighter
            elif last: t = -1                                # and settles at its end
            else: t = 0
            if l.endswith("?"): t = 2
            if last and last_st and len(st) > 1: out.append("[[slnc 420]]")   # a beat before the last line
            out.append(v.to(t) + clean(l) + f" [[slnc {breath(l)}]]")
        if not last_st: out.append("[[slnc 1100]]")         # stanza rest
    out.append("[[slnc 500]]")
    return "\n".join(out)

def speakable_note(note):
    """the headnote as prose: *italics* markers dropped, a breath between sentences"""
    t = clean(re.sub(r"\*([^*]+)\*", r"\1", note))
    return re.sub(r"([.!?])\s+", r"\1 [[slnc 350]] ", t)

def record(lang, text, m4a, rate):
    """render text → m4a unless the same text+voice+rate is already recorded (sha next to the file); returns the hash"""
    h = hashlib.sha1((VOICE[lang] + str(rate) + text).encode()).hexdigest()[:10]
    meta = m4a + ".sha"
    if not (os.path.exists(m4a) and os.path.exists(meta) and open(meta).read() == h):
        aiff = f"/tmp/claude-501/say-{lang}-{os.getpid()}.aiff"          # per process: several recorders may run at once
        for attempt in range(3):
            subprocess.run(["say", "-v", VOICE[lang], "-r", str(rate), "-o", aiff, text], check=True)
            r = subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "56000", "-q", "127", "-s", "3", aiff, m4a + ".part"], capture_output=True)
            if r.returncode == 0: break
            print("afconvert retry", m4a, r.stderr.decode(errors="replace").strip()[-120:], flush=True)
        else: raise RuntimeError("afconvert failed: " + m4a)
        os.replace(m4a + ".part", m4a)
        open(meta, "w").write(h)
    return h

def seconds(m4a):
    dur = subprocess.run(["afinfo", m4a], capture_output=True, text=True).stdout
    return round(float(re.search(r"estimated duration: ([\d.]+)", dur).group(1))) if "estimated duration" in dur else 0

def main():
    manifest, notes = {}, {}
    only = set(sys.argv[1:])
    print("voices:", VOICE, flush=True)
    for lang in VOICE:
        if only and lang not in only: continue
        os.makedirs(os.path.join(OUT, lang), exist_ok=True)
        manifest[lang], notes[lang] = {}, {}
        for p in D["poems"]:
            n = str(p["n"]); t = p["texts"][lang]
            m4a = os.path.join(OUT, lang, f"{n}.m4a")
            chunks = t["chunks"] if "chunks" in t else [t["text"].split("\n")]   # poems.json carries either chunked lines or one text block
            h = record(lang, speakable(t["title"], chunks), m4a, RATE[lang])
            manifest[lang][n] = {"s": seconds(m4a), "v": h}
            note = (p.get("note") or {}).get(lang, "").strip()
            if note:
                m4a = os.path.join(OUT, lang, f"{n}-note.m4a")
                h = record(lang, speakable_note(note), m4a, NOTE_RATE[lang])
                notes[lang][n] = {"s": seconds(m4a), "v": h}
            print(lang, n, manifest[lang][n]["s"], "s", "+ note", notes[lang].get(n, {}).get("s", "-"), "s", flush=True)
    mp = os.path.join(OUT, "manifest.json")
    old = json.load(open(mp)) if os.path.exists(mp) else {}
    old.update(manifest)
    old.setdefault("notes", {}).update(notes)
    json.dump(old, open(mp, "w"), separators=(",", ":"))
    print("manifest:", {k: (len(v) if k != "notes" else {l: len(x) for l, x in v.items()}) for k, v in old.items()})

if __name__ == "__main__":
    main()
