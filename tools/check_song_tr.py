#!/usr/bin/env python3
"""Song translations vs. originals: which songs are translated into which languages, and where line counts differ."""
import os, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "docs", "data", "poems.json"), encoding="utf-8"))
def lines(t): return [l for c in t["chunks"] for l in c] if "chunks" in t else t["text"].split("\n")
songs = [p for p in D["poems"] if p.get("song")]
missing = []
for p in songs:
    if p["song"]["status"] == "pending": continue
    o = lines(p["texts"][p["orig"]]); no = len([l for l in o if l.strip()])
    row = []
    for l in ("uk", "ru", "en", "es"):
        if l == p["orig"]: continue
        if l in (p.get("tr") or []):
            t = lines(p["texts"][l]); nt = len([x for x in t if x.strip()])
            row.append(f"{l}:{nt}/{no}" + ("" if nt == no else " !"))
        else: row.append(f"{l}:—"); missing.append((p["song"]["apple_id"], l))
    print(f'{p["roman"]:>7} {p["song"]["apple_id"]} {p["texts"]["en"]["title"][:28]:<28} orig={p["orig"]} ' + "  ".join(row))
print(f"missing: {len(missing)}")
