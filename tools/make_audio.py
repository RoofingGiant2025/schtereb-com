#!/usr/bin/env python3
"""Record every poem in every language with macOS speech voices → docs/audio/<lang>/<n>.m4a + manifest.json.
Uses `say` (Apple voices) and `afconvert` (AAC). Stanza breaks become pauses. Re-runs skip files whose text hash is unchanged."""
import os, json, re, subprocess, hashlib, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "audio")
VOICE = {"uk": "Lesya", "ru": "Milena", "en": "Samantha", "es": "Mónica"}
RATE = {"uk": 150, "ru": 150, "en": 150, "es": 155}
D = json.load(open(os.path.join(ROOT, "docs", "data", "poems.json"), encoding="utf-8"))

def speakable(title, chunks):
    lines = [l for c in chunks for l in c]
    out = []
    if title and title != "* * *": out.append(title + " [[slnc 900]]")
    for l in lines:
        if l.strip() == "": out.append("[[slnc 650]]"); continue
        if re.fullmatch(r"\*(.+)\*", l.strip()): continue          # translator's notes are not read
        t = l.strip()
        t = re.sub(r"[„“”«»\"]", "", t)
        t = t.replace("…", "...").replace("—", ",").replace("–", ",")
        out.append(t + " [[slnc 260]]")
    return "\n".join(out)

def main():
    manifest = {}
    only = set(sys.argv[1:])
    for lang in VOICE:
        if only and lang not in only: continue
        os.makedirs(os.path.join(OUT, lang), exist_ok=True)
        manifest[lang] = {}
        for p in D["poems"]:
            t = p["texts"][lang]
            text = speakable(t["title"], t["chunks"])
            h = hashlib.sha1((VOICE[lang] + str(RATE[lang]) + text).encode()).hexdigest()[:10]
            m4a = os.path.join(OUT, lang, f'{p["n"]}.m4a'); meta = m4a + ".sha"
            if not (os.path.exists(m4a) and os.path.exists(meta) and open(meta).read() == h):
                aiff = "/tmp/claude-501/say.aiff"
                subprocess.run(["say", "-v", VOICE[lang], "-r", str(RATE[lang]), "-o", aiff, text], check=True)
                subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "56000", "-q", "127", "-s", "3", aiff, m4a], check=True, capture_output=True)
                open(meta, "w").write(h)
            dur = subprocess.run(["afinfo", m4a], capture_output=True, text=True).stdout
            sec = float(re.search(r"estimated duration: ([\d.]+)", dur).group(1)) if "estimated duration" in dur else 0
            manifest[lang][str(p["n"])] = round(sec)
            print(lang, p["n"], round(sec), "s", flush=True)
    old = {}
    mp = os.path.join(OUT, "manifest.json")
    if os.path.exists(mp): old = json.load(open(mp))
    old.update(manifest)
    json.dump(old, open(mp, "w"), separators=(",", ":"))
    print("manifest:", {k: len(v) for k, v in old.items()})

if __name__ == "__main__":
    main()
