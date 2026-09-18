#!/usr/bin/env python3
"""Record every poem — and its headnote (ПРО ВІРШ) — in every language with macOS speech voices.
  docs/audio/<lang>/<n>.m4a        the poem
  docs/audio/<lang>/<n>-note.m4a   the headnote
  docs/audio/manifest.json         {lang: {n: {s: seconds, v: hash}}, "notes": {lang: {n: {s, v}}}}
Uses `say` (Apple voices) and `afconvert` (AAC). Stanza breaks become pauses. Re-runs skip files whose text hash is unchanged
(<file>.sha), so `python3 tools/make_audio.py [lang …]` after a text edit only re-records what changed.
`v` is what the reader appends as ?v= to the audio URL (cache-busting)."""
import os, json, re, subprocess, hashlib, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "audio")
VOICE = {"uk": "Lesya", "ru": "Milena", "en": "Samantha", "es": "Mónica"}
RATE = {"uk": 150, "ru": 150, "en": 150, "es": 155}
D = json.load(open(os.path.join(ROOT, "docs", "data", "poems.json"), encoding="utf-8"))

def clean(t):
    t = re.sub(r"[„“”«»\"]", "", t.strip())
    return t.replace("…", "...").replace("—", ",").replace("–", ",")

def speakable(title, chunks):
    lines = [l for c in chunks for l in c]
    out = []
    if title and title != "* * *": out.append(title + " [[slnc 900]]")
    for l in lines:
        if l.strip() == "": out.append("[[slnc 650]]"); continue
        if re.fullmatch(r"\*(.+)\*", l.strip()): continue          # translator's notes are not read
        out.append(clean(l) + " [[slnc 260]]")
    return "\n".join(out)

def speakable_note(note):
    """the headnote as prose: *italics* markers dropped, a breath between sentences"""
    t = clean(re.sub(r"\*([^*]+)\*", r"\1", note))
    return re.sub(r"([.!?])\s+", r"\1 [[slnc 350]] ", t)

def record(lang, text, m4a):
    """render text → m4a unless the same text+voice is already recorded (sha next to the file); returns the hash"""
    h = hashlib.sha1((VOICE[lang] + str(RATE[lang]) + text).encode()).hexdigest()[:10]
    meta = m4a + ".sha"
    if not (os.path.exists(m4a) and os.path.exists(meta) and open(meta).read() == h):
        aiff = f"/tmp/claude-501/say-{lang}.aiff"
        subprocess.run(["say", "-v", VOICE[lang], "-r", str(RATE[lang]), "-o", aiff, text], check=True)
        subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "56000", "-q", "127", "-s", "3", aiff, m4a], check=True, capture_output=True)
        open(meta, "w").write(h)
    return h

def seconds(m4a):
    dur = subprocess.run(["afinfo", m4a], capture_output=True, text=True).stdout
    return round(float(re.search(r"estimated duration: ([\d.]+)", dur).group(1))) if "estimated duration" in dur else 0

def main():
    manifest, notes = {}, {}
    only = set(sys.argv[1:])
    for lang in VOICE:
        if only and lang not in only: continue
        os.makedirs(os.path.join(OUT, lang), exist_ok=True)
        manifest[lang], notes[lang] = {}, {}
        for p in D["poems"]:
            n = str(p["n"]); t = p["texts"][lang]
            m4a = os.path.join(OUT, lang, f"{n}.m4a")
            chunks = t["chunks"] if "chunks" in t else [t["text"].split("\n")]   # poems.json carries either chunked lines or one text block
            h = record(lang, speakable(t["title"], chunks), m4a)
            manifest[lang][n] = {"s": seconds(m4a), "v": h}
            note = (p.get("note") or {}).get(lang, "").strip()
            if note:
                m4a = os.path.join(OUT, lang, f"{n}-note.m4a")
                h = record(lang, speakable_note(note), m4a)
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
