#!/usr/bin/env python3
"""Assemble full per-language files (uk.md, ru.md, es.md) and site/data/poems.json.

Sources:
  content/originals.md   exact originals, 80 poems, with section headers
  content/en.md          English, 80 poems, same order
  content/tr/uk.md       Ukrainian versions of the Russian-language poems ('## N. Title')
  content/tr/ru.md       Russian versions of the Ukrainian-language poems
  content/tr/es.md       Spanish versions of all 80
For each language the original-language poems are inserted verbatim.
"""
import os, re, json, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from make_pdf import parse  # noqa

TITLE = {"uk": "Ноти життя: до і після", "ru": "Ноты жизни: до и после",
         "en": "Notes of Life: Before and After", "es": "Notas de la vida: antes y después"}
SECTIONS = {
    "Любов як захоплення": {"uk": "Любов як захоплення", "ru": "Любовь как увлечение",
                            "en": "Love as Infatuation", "es": "El amor como fascinación"},
    "Любов як драма": {"uk": "Любов як драма", "ru": "Любовь как драма",
                       "en": "Love as Drama", "es": "El amor como drama"},
    "Любов як істина": {"uk": "Любов як істина", "ru": "Любовь как истина",
                        "en": "Love as Truth", "es": "El amor como verdad"},
}

def parse_numbered(path):
    out = {}
    cur = None
    for raw in open(path, encoding="utf-8").read().split("\n"):
        line = raw.rstrip()
        m = re.match(r"^## (\d+)\. (.*)$", line)
        if m:
            cur = {"title": m.group(2).strip(), "body": []}
            out[int(m.group(1))] = cur
            continue
        if line.startswith("# "):
            continue
        if cur is not None:
            cur["body"].append(line)
    for p in out.values():
        while p["body"] and not p["body"][0].strip(): p["body"].pop(0)
        while p["body"] and not p["body"][-1].strip(): p["body"].pop()
    return out

def main():
    originals = parse(os.path.join(ROOT, "content", "originals.md"))
    en = parse(os.path.join(ROOT, "content", "en.md"))
    tr = {l: parse_numbered(os.path.join(ROOT, "content", "tr", f"{l}.md")) for l in ("uk", "ru", "es")}
    assert len(originals) == len(en) == 80
    poems = []
    for i, (o, e) in enumerate(zip(originals, en), start=1):
        texts = {o["lang"]: {"title": o["title"], "body": o["body"]},
                 "en": {"title": e["title"], "body": e["body"]}}
        for l in ("uk", "ru", "es"):
            if l == o["lang"]:
                assert i not in tr[l], f"{l}.md has a translation for poem {i}, which is already {l}"
                continue
            assert i in tr[l], f"missing {l} translation for poem {i} ({o['title']})"
            texts[l] = tr[l][i]
        poems.append({"n": i, "section": o["section"], "orig": o["lang"], "texts": texts})
    # per-language markdown files (same format as en.md)
    for l in ("uk", "ru", "es"):
        lines = [f"# {TITLE[l]}", f"### Oleg Shtereb", ""]
        cur = None
        for p in poems:
            if p["section"] != cur:
                cur = p["section"]
                lines += ["---", "", f"# {SECTIONS[cur][l]}", ""]
            lines += [f"## {p['texts'][l]['title']}", ""] + p["texts"][l]["body"] + [""]
        open(os.path.join(ROOT, "content", f"{l}.md"), "w", encoding="utf-8").write("\n".join(lines))
    # site data
    os.makedirs(os.path.join(ROOT, "docs", "data"), exist_ok=True)
    data = {"title": TITLE, "author": {"uk": "Олег Штереб", "ru": "Олег Штереб", "en": "Oleg Shtereb", "es": "Oleg Shtereb"},
            "epigraph": "Art Knows No Languages",
            "sections": [{"key": k, **v} for k, v in SECTIONS.items()],
            "poems": [{"n": p["n"], "section": p["section"], "orig": p["orig"],
                       "texts": {l: {"title": t["title"], "text": "\n".join(t["body"])} for l, t in p["texts"].items()}}
                      for p in poems]}
    json.dump(data, open(os.path.join(ROOT, "docs", "data", "poems.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok: 80 poems x 4 languages; wrote content/uk.md ru.md es.md and site/data/poems.json")

if __name__ == "__main__":
    main()
