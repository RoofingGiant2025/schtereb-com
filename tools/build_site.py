#!/usr/bin/env python3
"""Generate the static site in site/ from site/data/poems.json.
Pages: /            language choice (epigraph)
       /<lang>/     title page + contents
       /<lang>/<n>-<slug>.html   one poem
"""
import os, json, re, html, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "docs")
D = json.load(open(os.path.join(SITE, "data", "poems.json"), encoding="utf-8"))
LANGS = ["uk", "ru", "en", "es"]
LNAME = {"uk": "Українська", "ru": "Русский", "en": "English", "es": "Español"}
LSHORT = {"uk": "УК", "ru": "РУ", "en": "EN", "es": "ES"}
UI = {
 "uk": dict(contents="Зміст", first="Перша збірка", original="оригінал", translation="переклад", of="з", prev="Попередній", next="Наступний",
            side="Поруч з оригіналом", single="Лише цією мовою", colophon="Усі права застережено", back="До змісту", read="Читати", opening="Вступ",
            about="Вірші написані українською та російською мовами й уперше опубліковані на schtereb.com. Тут вони подані без змін; кожен вірш можна читати мовою оригіналу або в перекладі — українською, російською, англійською, іспанською."),
 "ru": dict(contents="Содержание", first="Первый сборник", original="оригинал", translation="перевод", of="из", prev="Предыдущее", next="Следующее",
            side="Рядом с оригиналом", single="Только на этом языке", colophon="Все права защищены", back="К содержанию", read="Читать", opening="Вступление",
            about="Стихи написаны на украинском и русском языках и впервые опубликованы на schtereb.com. Здесь они приведены без изменений; каждое стихотворение можно читать на языке оригинала или в переводе — на украинском, русском, английском, испанском."),
 "en": dict(contents="Contents", first="The first collection", original="original", translation="translation", of="of", prev="Previous", next="Next",
            side="Beside the original", single="This language only", colophon="All rights reserved", back="To contents", read="Read", opening="Opening",
            about="The poems were written in Ukrainian and Russian and first published on schtereb.com. They appear here unchanged; every poem can be read in its original language or in translation — Ukrainian, Russian, English, Spanish."),
 "es": dict(contents="Índice", first="La primera colección", original="original", translation="traducción", of="de", prev="Anterior", next="Siguiente",
            side="Junto al original", single="Solo en este idioma", colophon="Todos los derechos reservados", back="Al índice", read="Leer", opening="Apertura",
            about="Los poemas fueron escritos en ucraniano y ruso y publicados por primera vez en schtereb.com. Aparecen aquí sin cambios; cada poema puede leerse en su lengua original o en traducción — ucraniano, ruso, inglés, español."),
}
TR = {**dict(zip("абвгдежзийклмнопрстуфхцчшщъыьэюя", ["a","b","v","g","d","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","kh","ts","ch","sh","shch","","y","","e","yu","ya"])),
      "ё":"e","є":"ye","і":"i","ї":"yi","ґ":"g","á":"a","é":"e","í":"i","ó":"o","ú":"u","ñ":"n","ü":"u"}
def slug(s):
    s = s.lower()
    s = "".join(TR.get(c, c) for c in s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:48].rstrip("-") or "poem"

def poem_slug(p, lang):
    t = p["texts"][lang]["title"]
    if t == "* * *":
        t = p["texts"][lang]["text"].strip().split("\n")[0]
    return f"{p['n']}-{slug(t)}"

def esc(s): return html.escape(s, quote=True)

def poem_html(text):
    out = []
    for stanza in re.split(r"\n\s*\n", text.strip("\n")):
        lines = []
        for line in stanza.split("\n"):
            m = re.fullmatch(r"\*(.+)\*", line.strip())
            if m:
                lines.append(f'<span class="note">{esc(m.group(1))}</span>')
                continue
            stripped = line.lstrip(" \t")
            lead = len(line) - len(stripped)
            style = f' style="--in:{lead}ch"' if lead else ""
            lines.append(f'<span class="l"{style}>{esc(stripped)}</span>')
        out.append('<p class="stanza">' + "\n".join(lines) + "</p>")
    return "\n".join(out)

def section_name(key, lang):
    for s in D["sections"]:
        if s["key"] == key: return s[lang]
    return ""

def head(title, lang, depth, desc=""):
    pre = "../" * depth
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc or D['title'][lang] + ' — ' + D['author'][lang])}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,500;1,7..72,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{pre}assets/book.css">
<link rel="icon" href="{pre}assets/favicon.svg" type="image/svg+xml">
</head>
<body>
'''

def lang_switch(current, hrefs, depth):
    items = []
    for l in LANGS:
        cls = ' class="on"' if l == current else ""
        items.append(f'<a{cls} href="{hrefs[l]}" hreflang="{l}" lang="{l}" title="{LNAME[l]}">{LSHORT[l]}</a>')
    return '<nav class="langs" aria-label="Language">' + "".join(items) + "</nav>"

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)

def build():
    poems = D["poems"]
    # assets
    os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, "tools", "book.css"), os.path.join(SITE, "assets", "book.css"))
    shutil.copy(os.path.join(ROOT, "tools", "book.js"), os.path.join(SITE, "assets", "book.js"))
    write(os.path.join(SITE, "assets", "favicon.svg"),
          '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="10" fill="#f4efe6"/><text x="32" y="44" font-family="Georgia,serif" font-size="36" text-anchor="middle" fill="#1d1a16">♪</text></svg>')
    hrefs_all = {p["n"]: {l: poem_slug(p, l) + ".html" for l in LANGS} for p in poems}

    # root: epigraph + language choice
    root = head("Олег Штереб — Ноти життя: до і після", "uk", 0, "Oleg Shtereb — Notes of Life: Before and After. Poems in Ukrainian, Russian, English and Spanish.")
    root += '<main class="cover">'
    root += '<p class="epigraph"><span>Art Knows No Languages</span><cite>— Oleg Shtereb</cite></p>'
    root += '<h1 class="booktitle">Ноти життя:<br>до і після</h1>'
    root += '<p class="author">Олег Штереб · Oleg Shtereb</p>'
    root += '<ul class="choose">' + "".join(
        f'<li><a href="{l}/" lang="{l}"><span class="t">{esc(D["title"][l])}</span><span class="n">{LNAME[l]}</span></a></li>' for l in LANGS) + "</ul>"
    root += '</main><script src="assets/book.js"></script></body></html>'
    write(os.path.join(SITE, "index.html"), root)

    for l in LANGS:
        ui = UI[l]
        # title + contents page
        h = head(f'{D["title"][l]} — {D["author"][l]}', l, 1)
        h += '<header class="top"><a class="home" href="../">♪</a>' + lang_switch(l, {x: f"../{x}/" for x in LANGS}, 1) + "</header>"
        h += '<main class="titlepage">'
        h += f'<p class="author">{esc(D["author"][l])}</p><h1 class="booktitle">{esc(D["title"][l])}</h1>'
        h += f'<p class="sub">{esc(ui["first"])}</p>'
        h += f'<p class="about">{esc(ui["about"])}</p>'
        first = poems[0]
        h += f'<p class="start"><a class="btn" href="{hrefs_all[first["n"]][l]}">{esc(ui["read"])} →</a></p>'
        h += f'<h2 class="contents-h">{esc(ui["contents"])}</h2><ol class="contents">'
        cur = None
        for p in poems:
            if p["section"] != cur:
                cur = p["section"]
                h += f'<li class="sec">{esc(section_name(cur, l))}</li>'
            t = p["texts"][l]["title"]
            if t == "* * *":
                t = "* * *  " + p["texts"][l]["text"].strip().split("\n")[0].strip().rstrip(",;:.—–- ")
            badge = f' <span class="orig-dot" title="{esc(ui["original"])}">•</span>' if p["orig"] == l else ""
            h += f'<li><a href="{hrefs_all[p["n"]][l]}"><span class="num">{p["n"]}</span> {esc(t)}{badge}</a></li>'
        h += "</ol>"
        h += f'<footer class="colophon">© {esc(D["author"][l])} · schtereb.com · {esc(ui["colophon"])}</footer>'
        h += '</main><script src="../assets/book.js"></script></body></html>'
        write(os.path.join(SITE, l, "index.html"), h)

        # poem pages
        for idx, p in enumerate(poems):
            t = p["texts"][l]
            prev_p = poems[idx - 1] if idx > 0 else None
            next_p = poems[idx + 1] if idx + 1 < len(poems) else None
            is_orig = p["orig"] == l
            title_disp = t["title"]
            page_title = title_disp if title_disp != "* * *" else "* * * " + t["text"].strip().split("\n")[0].strip()
            h = head(f'{page_title} — {D["title"][l]}', l, 1, page_title + " — " + D["author"][l])
            h += f'<header class="top"><a class="home" href="./" title="{esc(ui["back"])}">{esc(D["title"][l])}</a>'
            h += lang_switch(l, {x: f"../{x}/{hrefs_all[p['n']][x]}" for x in LANGS}, 1) + "</header>"
            h += f'<main class="page" data-n="{p["n"]}" data-lang="{l}" data-orig="{p["orig"]}"'
            if prev_p: h += f' data-prev="{hrefs_all[prev_p["n"]][l]}"'
            if next_p: h += f' data-next="{hrefs_all[next_p["n"]][l]}"'
            h += ">"
            h += f'<p class="running"><span>{esc(section_name(p["section"], l) or ui["opening"])}</span><span>{p["n"]} {esc(ui["of"])} 80</span></p>'
            h += '<div class="spread">'
            h += f'<article class="poem" lang="{l}"><h1>{esc(title_disp)}</h1>'
            h += f'<p class="mark">{"<b>" + esc(ui["original"]) + "</b>" if is_orig else esc(ui["translation"]) + " · " + esc(ui["original"]) + ": " + LNAME[p["orig"]].lower()}</p>'
            h += poem_html(t["text"]) + "</article>"
            if not is_orig:
                o = p["texts"][p["orig"]]
                h += f'<article class="poem original" lang="{p["orig"]}" hidden><h1>{esc(o["title"])}</h1><p class="mark"><b>{esc(UI[p["orig"]]["original"])}</b></p>'
                h += poem_html(o["text"]) + "</article>"
            h += "</div>"
            h += '<nav class="pager">'
            h += (f'<a class="prev" href="{hrefs_all[prev_p["n"]][l]}" rel="prev">← {esc(ui["prev"])}</a>' if prev_p else '<span></span>')
            if not is_orig:
                h += f'<button class="side" type="button" data-on="{esc(ui["single"])}" data-off="{esc(ui["side"])}">{esc(ui["side"])}</button>'
            else:
                h += '<span></span>'
            h += (f'<a class="next" href="{hrefs_all[next_p["n"]][l]}" rel="next">{esc(ui["next"])} →</a>' if next_p else f'<a class="next" href="./">{esc(ui["back"])} ↑</a>')
            h += "</nav></main>"
            h += '<script src="../assets/book.js"></script></body></html>'
            write(os.path.join(SITE, l, hrefs_all[p["n"]][l]), h)
    # sitemap + robots
    urls = ["https://schtereb.com/"] + [f"https://schtereb.com/{l}/" for l in LANGS] + \
           [f"https://schtereb.com/{l}/{hrefs_all[p['n']][l]}" for l in LANGS for p in poems]
    write(os.path.join(SITE, "sitemap.xml"), '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write(os.path.join(SITE, "robots.txt"), "User-agent: *\nAllow: /\nSitemap: https://schtereb.com/sitemap.xml\n")
    write(os.path.join(SITE, "CNAME"), "schtereb.com\n")
    write(os.path.join(SITE, ".nojekyll"), "")
    print("site built:", len(urls), "urls")

if __name__ == "__main__":
    build()
