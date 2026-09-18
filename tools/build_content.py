#!/usr/bin/env python3
"""Assemble full per-language files (uk.md, ru.md, es.md) and site/data/poems.json.

Sources:
  content/originals.md   exact originals, 80 poems, with section headers
  content/en.md          English, 80 poems, same order
  content/tr/uk.md       Ukrainian versions of the Russian-language poems ('## N. Title')
  content/tr/ru.md       Russian versions of the Ukrainian-language poems
  content/tr/es.md       Spanish versions of all 80
  content/notes/<lang>.md  one short introduction (headnote) per poem in each of the 4 languages ('## N. Title')
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
    "Після": {"uk": "Після", "ru": "После", "en": "After", "es": "Después"},
    "Пісні": {"uk": "Пісні", "ru": "Песни", "en": "Songs", "es": "Canciones"},
}
N_BEFORE = 80

def roman(n):
    out = ""
    for v, r in [(50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]:
        while n >= v:
            out += r; n -= v
    return out

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
    notes = {l: parse_numbered(os.path.join(ROOT, "content", "notes", f"{l}.md")) for l in ("uk", "ru", "en", "es")}
    assert len(originals) == len(en) == 82, (len(originals), len(en))
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
        for l in notes: assert i in notes[l] and notes[l][i]["body"], f"missing {l} headnote for poem {i} ({o['title']})"
        poems.append({"n": i, "section": o["section"], "orig": o["lang"], "texts": texts,
                      "note": {l: " ".join(x.strip() for x in notes[l][i]["body"] if x.strip()) for l in notes},
                      "roman": roman(i) if i <= N_BEFORE else roman(i - N_BEFORE),
                      "part": "before" if i <= N_BEFORE else "after"})
    # ---- songs (Dr. O Schtereb releases): catalog + transcripts / author lyric sheets → part "songs"
    songs_dir = os.path.join(ROOT, "content", "songs")
    catalog = json.load(open(os.path.join(songs_dir, "apple-catalog.json"), encoding="utf-8"))
    def words(t): return set(w for w in re.findall(r"[a-zа-яіїєґё']+", t.lower()) if len(w) > 3)
    poem_words = [(p["n"], words("\n".join(p["texts"]["en"]["body"] + p["texts"][p["orig"]]["body"]))) for p in poems]
    song_lines = []
    for i, sg in enumerate(catalog, start=1):
        lyr = os.path.join(songs_dir, "lyrics", f'{sg["apple_id"]}.md')       # author's / proofread sheet wins
        trn = os.path.join(songs_dir, "transcripts", f'{sg["apple_id"]}.json')
        status, lines, lang = "pending", [], "en"
        if os.path.exists(lyr):
            raw = open(lyr, encoding="utf-8").read().strip("\n").split("\n")
            lang = (raw[0][6:].strip() if raw and raw[0].startswith("lang: ") else "en")
            lines = [l.rstrip() for l in raw if not l.startswith("lang: ")]
            while lines and not lines[0].strip(): lines.pop(0)
            status = "author"
        elif os.path.exists(trn):
            tj = json.load(open(trn, encoding="utf-8")); lang = tj.get("language") or "en"; status = "transcribed"
            # light clean-up of speech-to-text noise: bracketed cues, sign-offs, and the same line repeated more than three times in a row
            raw = [l for l in tj["lines"] if not re.fullmatch(r"\s*[\[(].*[\])]\s*", l) and not re.fullmatch(r"\s*(thank you|thanks for watching|subtitles by .*|you)\.?\s*", l, re.I)]
            lines, run = [], 0
            for l in raw:
                if lines and l.strip() and l.strip().lower() == lines[-1].strip().lower(): run += 1
                else: run = 0
                if run < 3: lines.append(l)
            while lines and not lines[0].strip(): lines.pop(0)
            while lines and not lines[-1].strip(): lines.pop()
        if lang not in ("uk", "ru", "en", "es"): lang_key = "en"
        else: lang_key = lang
        body = lines if lines else ["—"]
        src = None
        if lines:
            sw = words("\n".join(lines)); best = (0, None)
            for n, pw in poem_words:
                if not pw or not sw: continue
                j = len(sw & pw) / len(sw | pw)
                if j > best[0]: best = (j, n)
            if best[0] >= 0.22: src = best[1]
        title = sg["clean_title"]
        texts = {l: {"title": title, "body": body} for l in ("uk", "ru", "en", "es")}
        meta_note = {"uk": f"Сингл, виданий {sg['released']}." + (" Текст — розшифровка запису, до вичитки автором." if status == "transcribed" else " Текст автора." if status == "author" else " Текст ще не додано."),
                     "ru": f"Сингл, выпущен {sg['released']}." + (" Текст — расшифровка записи, до вычитки автором." if status == "transcribed" else " Авторский текст." if status == "author" else " Текст ещё не добавлен."),
                     "en": f"Single released {sg['released']}." + (" Words transcribed from the recording — awaiting the author's proofreading." if status == "transcribed" else " The author's lyric sheet." if status == "author" else " Lyrics not yet added."),
                     "es": f"Sencillo publicado el {sg['released']}." + (" Letra transcrita de la grabación, pendiente de revisión del autor." if status == "transcribed" else " Letra del autor." if status == "author" else " Letra aún no añadida.")}
        poems.append({"n": 1000 + i, "section": "Пісні", "orig": lang_key, "texts": texts, "roman": roman(i), "part": "songs", "single": True, "note": meta_note,
                      "song": {"released": sg["released"], "apple_url": sg["apple_url"], "spotify": sg["spotify_search"], "preview": sg["preview"],
                               "artwork": sg["artwork"], "seconds": sg["seconds"], "status": status, "lang": lang, "explicit": sg["explicit"],
                               "source_poem": src, "apple_id": sg["apple_id"]}})
        song_lines += [f"## {title}", f"*{sg['released']} · {status}" + (f" · from poem {src}" if src else "") + "*", ""] + body + [""]
    open(os.path.join(ROOT, "content", "songs.md"), "w", encoding="utf-8").write("# Пісні · Songs\n\n" + "\n".join(song_lines))
    n_songs = len(catalog); n_lyrics = sum(1 for p in poems if p.get("song") and p["song"]["status"] != "pending")
    # per-language markdown files (same format as en.md)
    for l in ("uk", "ru", "es"):
        lines = [f"# {TITLE[l]}", f"### Oleg Schtereb", ""]
        cur = None
        for p in poems:
            if p.get("song"): continue
            if p["section"] != cur:
                cur = p["section"]
                lines += ["---", "", f"# {SECTIONS[cur][l]}", ""]
            lines += [f"## {p['texts'][l]['title']}", ""] + p["texts"][l]["body"] + [""]
        open(os.path.join(ROOT, "content", f"{l}.md"), "w", encoding="utf-8").write("\n".join(lines))
    # site data
    os.makedirs(os.path.join(ROOT, "docs", "data"), exist_ok=True)
    data = {"title": TITLE, "author": {"uk": "Олег Штереб", "ru": "Олег Штереб", "en": "Oleg Schtereb", "es": "Oleg Schtereb"},
            "epigraph": "Art Knows No Languages",
            "sections": [{"key": k, **v} for k, v in SECTIONS.items()],
            "parts": {"before": {"uk": "До", "ru": "До", "en": "Before", "es": "Antes"},
                      "after": {"uk": "Після", "ru": "После", "en": "After", "es": "Después"},
                      "songs": {"uk": "Пісні", "ru": "Песни", "en": "Songs", "es": "Canciones"}},
            "poems": [{"n": p["n"], "roman": p["roman"], "part": p["part"], "section": p["section"], "orig": p["orig"], **({"single": True, "song": p["song"]} if p.get("song") else {}), "note": p["note"],
                       "texts": {l: {"title": t["title"], "text": "\n".join(t["body"])} for l, t in p["texts"].items()}}
                      for p in poems]}
    json.dump(data, open(os.path.join(ROOT, "docs", "data", "poems.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"ok: 82 poems x 4 languages + {n_songs} songs ({n_lyrics} with lyrics); wrote content/uk.md ru.md es.md, content/songs.md, docs/data/poems.json")

if __name__ == "__main__":
    main()
