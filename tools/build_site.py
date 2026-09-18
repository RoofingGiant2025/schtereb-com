#!/usr/bin/env python3
"""Generate the book site (docs/) from docs/data/poems.json produced by build_content.py.

Pages (every one is the same book shell; the JS opens it at the right leaf):
  /                         closed book (cover) + language choice
  /<lang>/                  open at the epigraph
  /<lang>/<n>-<slug>.html   open at that poem (server-rendered spread for crawlers / no-JS)
"""
import os, json, re, html, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "docs")
DATA = os.path.join(SITE, "data", "poems.json")
LANGS = ["uk", "ru", "en", "es"]
LSHORT = {"uk": "УК", "ru": "РУ", "en": "EN", "es": "ES"}
LNAME = {"uk": "Українська", "ru": "Русский", "en": "English", "es": "Español"}
MAX_LINES = 16

UI = {
 "uk": dict(main="Ноти життя", sub="до і після", first="Перша збірка", count="Вірші I–LXXX · Після I–II", open="Відкрити книжку",
            contents="Зміст", close="Закрити", original="Оригінал", translation="Переклад", continued="продовження",
            edition="Перше видання", house="Штереб", rights="Усі права застережено.", published="Видано на schtereb.com",
            epigraph="Мистецтво не знає мов", dedication="Тим, хто живе мрією", epigraph_short="Епіграф", titlepage="Титул", colophon_short="Колофон",
            facing="Оригінал ліворуч, переклад праворуч.",
            note="У частині «До» кожен вірш надруковано спершу мовою оригіналу — українською або російською: правопис, пунктуація й окремі англійські слова лишені так, як написав автор. Українська, російська, англійська та іспанська версії — віршовані переклади 2026 року. Два вірші «Після» написані англійською.",
            colophon="Набрано гарнітурами Cormorant Garamond і Source Serif. Зроблено як книжку для читання, а не сторінку для гортання. Оригінали вперше оприлюднено на shtereb.com (2019). Дім Штереба."),
 "ru": dict(main="Ноты жизни", sub="до и после", first="Первый сборник", count="Стихи I–LXXX · После I–II", open="Открыть книгу",
            contents="Содержание", close="Закрыть", original="Оригинал", translation="Перевод", continued="продолжение",
            edition="Первое издание", house="Штереб", rights="Все права защищены.", published="Издано на schtereb.com",
            epigraph="Искусство не знает языков", dedication="Тем, кто живёт мечтой", epigraph_short="Эпиграф", titlepage="Титул", colophon_short="Колофон",
            facing="Оригинал слева, перевод справа.",
            note="В части «До» каждое стихотворение напечатано сначала на языке оригинала — украинском или русском: орфография, пунктуация и отдельные английские слова оставлены так, как написал автор. Украинская, русская, английская и испанская версии — стихотворные переводы 2026 года. Два стихотворения «После» написаны по-английски.",
            colophon="Набрано гарнитурами Cormorant Garamond и Source Serif. Сделано как книга для чтения, а не страница для прокрутки. Оригиналы впервые опубликованы на shtereb.com (2019). Дом Штереба."),
 "en": dict(main="Notes of Life", sub="Before and After", first="A first collection", count="Poems I–LXXX · After I–II", open="Open the book",
            contents="Contents", close="Close", original="Original", translation="Translation", continued="continued",
            edition="First edition", house="Shtereb", rights="All rights reserved.", published="Published at schtereb.com",
            epigraph="Art Knows No Languages", dedication="To Those Who Are Living the Dream", epigraph_short="Epigraph", titlepage="Title page", colophon_short="Colophon",
            facing="Original on the left, translation on the right.",
            note="In Before, each poem is printed first in its original Ukrainian or Russian — spelling, punctuation and the occasional English word left as the author wrote them. The Ukrainian, Russian, English and Spanish versions are verse translations made in 2026. The two poems of After were written in English.",
            colophon="Set in Cormorant Garamond and Source Serif. Designed as a book to be read, not a page to be scrolled. Originals first published at shtereb.com (2019). The house of Shtereb."),
 "es": dict(main="Notas de la vida", sub="antes y después", first="Primera colección", count="Poemas I–LXXX · Después I–II", open="Abrir el libro",
            contents="Índice", close="Cerrar", original="Original", translation="Traducción", continued="continúa",
            edition="Primera edición", house="Shtereb", rights="Todos los derechos reservados.", published="Publicado en schtereb.com",
            epigraph="El arte no conoce idiomas", dedication="A quienes viven el sueño", epigraph_short="Epígrafe", titlepage="Portada", colophon_short="Colofón",
            facing="Original a la izquierda, traducción a la derecha.",
            note="En Antes, cada poema se imprime primero en su original ucraniano o ruso: grafía, puntuación y las palabras inglesas ocasionales se dejan como las escribió el autor. Las versiones ucraniana, rusa, inglesa y española son traducciones en verso de 2026. Los dos poemas de Después se escribieron en inglés.",
            colophon="Compuesto en Cormorant Garamond y Source Serif. Hecho para leerse como un libro, no para desplazarse como una página. Originales publicados por primera vez en shtereb.com (2019). La casa de Shtereb."),
}

TR = {**dict(zip("абвгдежзийклмнопрстуфхцчшщъыьэюя", ["a","b","v","g","d","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","kh","ts","ch","sh","shch","","y","","e","yu","ya"])),
      "ё":"e","є":"ye","і":"i","ї":"yi","ґ":"g","á":"a","é":"e","í":"i","ó":"o","ú":"u","ñ":"n","ü":"u"}
def slug(s):
    s = "".join(TR.get(c, c) for c in s.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:48].rstrip("-") or "poem"
def esc(s): return html.escape(s, quote=True)

# ---- chunking (mirrors the reader: stanza-aware, planned on the original, applied to every language) ----
def stanzas(text):
    out, cur = [], []
    for l in text.split("\n"):
        if l.strip() == "":
            if cur: out.append(cur); cur = []
        else: cur.append(l)
    if cur: out.append(cur)
    return out
def plan(orig_stanzas):
    units = []
    for si, st in enumerate(orig_stanzas):
        n = len(st)
        for i in range(0, n, MAX_LINES): units.append((si, i, min(n, i + MAX_LINES)))
    groups, cur, cnt = [], [], 0
    for u in units:
        ln = u[2] - u[1]; add = ln + (1 if cnt else 0)
        if cur and cnt + add > MAX_LINES: groups.append(cur); cur = [u]; cnt = ln
        else: cur.append(u); cnt += add
    if cur: groups.append(cur)
    return groups or [[]]
def apply(target_stanzas, spans):
    parts = []
    for si, a, b in spans:
        st = target_stanzas[si] if si < len(target_stanzas) else []
        sl = st[a:min(b, len(st))]
        if sl: parts.append(sl)
    lines = []
    for i, p in enumerate(parts):
        if i: lines.append("")
        lines += p
    return lines

ORN_RULE = '<svg class="orn rule" viewBox="0 0 180 12" fill="none" aria-hidden="true"><path d="M2 6h68" stroke="currentColor" stroke-width=".7" stroke-linecap="round"/><circle cx="90" cy="6" r="1.6" fill="currentColor"/><path d="M78 6h24" stroke="currentColor" stroke-width=".7" opacity=".5"/><path d="M110 6h68" stroke="currentColor" stroke-width=".7" stroke-linecap="round"/></svg>'
ORN_STAFF = '<svg class="orn staff" viewBox="0 0 96 36" fill="none" aria-hidden="true"><path d="M4 8h88M4 14h88M4 20h88M4 26h88M4 32h88" stroke="currentColor" stroke-width=".7" opacity=".55"/><path d="M22 26c0-7 5-12 8-18 1 8-2 14-2 20 0 3 2 5 4 5 3 0 5-3 5-6 0-5-4-8-7-8-4 0-8 4-8 9 0 6 5 10 11 10 8 0 13-7 13-15" stroke="currentColor" stroke-width="1.15" stroke-linecap="round"/><ellipse cx="58" cy="24" rx="4.2" ry="3" fill="currentColor"/><path d="M62 24V10" stroke="currentColor" stroke-width="1.1"/><ellipse cx="74" cy="18" rx="4.2" ry="3" fill="currentColor"/><path d="M78 18V6" stroke="currentColor" stroke-width="1.1"/></svg>'

def verse_html(lines, drop):
    out = []
    for i, st in enumerate(stanzas("\n".join(lines))):
        cls = "stanza" + (" drop" if drop and i == 0 and re.match(r"^\w", st[0].strip()) else "")
        spans = []
        for l in st:
            m = re.fullmatch(r"\*(.+)\*", l.strip())
            spans.append(f'<span class="note">{esc(m.group(1))}</span>' if m else f'<span class="l">{esc(l)}</span>')
        out.append(f'<p class="{cls}">' + "".join(spans) + "</p>")
    return '<div class="verse">' + "".join(out) + "</div>"
def poem_block(title, lines, kicker, drop):
    return '<div class="poem">' + (f'<p class="kick">{esc(kicker)}</p>' if kicker else "") + f"<h2>{esc(title)}</h2>{ORN_RULE}{verse_html(lines, drop)}</div>"
def leaf(body, side, folio, lang, D):
    ui = UI[lang]
    foot = f'<span class="n">{folio}</span><span>{esc(D["author"][lang])}</span>' if side == "left" else f'<span>{esc(ui["main"])}</span><span class="n">{folio}</span>'
    return f'<div class="leaf"><div class="leaf-body">{body}</div><footer class="leaf-foot">{foot}</footer></div>'

def shell(D, lang, *, open_, left, right, title, desc, n=None, canonical="", alternates=None):
    ui = UI[lang]
    langs = "".join(f'<a href="/{l}/{(alternates or {}).get(l, "")}" data-lang="{l}" class="{"on" if l == lang else ""}" hreflang="{l}" lang="{l}" title="{LNAME[l]}">{LSHORT[l]}</a>' for l in LANGS)
    alts = "".join(f'<link rel="alternate" hreflang="{l}" href="https://schtereb.com/{l}/{(alternates or {}).get(l, "")}">' for l in LANGS) if alternates is not None else ""
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#0b0a09">
<link rel="canonical" href="https://schtereb.com{canonical}">{alts}
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="https://schtereb.com/assets/img/og.jpg"><meta property="og:type" content="book">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/book.css">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
</head>
<body>
<main class="room" id="book-root" data-lang="{lang}" data-open="{"1" if open_ else "0"}" data-base="/"{f' data-n="{n}"' if n else ""}>
  <header class="chrome">
    <a class="wordmark" href="/">Штереб</a>
    <nav class="langs" id="langs" aria-label="Language">{langs}</nav>
  </header>
  <div class="stage-wrap">
    <div class="stage {"open" if open_ else "closed"}" id="stage">
      <div class="book" id="book" data-dir="none">
        <div class="spine" aria-hidden="true"></div>
        <div class="ribbon" aria-hidden="true"></div>
        <div class="spread">
          <div class="leafwrap left" id="leaf-left">{left}</div>
          <button class="turnzone prev" id="turn-prev-l" type="button" aria-label="Previous"{"" if open_ else " hidden"}></button>
          <div class="leafwrap right" id="leaf-right">{right}</div>
          <button class="turnzone prev" id="turn-prev-r" type="button" aria-label="Previous" hidden></button>
          <button class="turnzone next" id="turn-next-r" type="button" aria-label="Next"{"" if open_ else " hidden"}></button>
        </div>
        <div class="cover" id="cover" data-open="{"true" if open_ else "false"}" aria-hidden="{"true" if open_ else "false"}">
          <button type="button" id="cover-open" aria-label="{esc(ui["open"])}">
            <img src="/assets/img/cover.jpg" alt="" width="960" height="1440" fetchpriority="high">
            <div class="shade"></div>
            <div class="type">
              <p class="k">{esc(ui["first"])}</p>
              <h1>{esc(ui["main"])}</h1>
              <p class="s">{esc(ui["sub"])}</p>
              <p class="k" style="margin-top:.75rem">{esc(ui["count"])}</p>
              <p class="a">{esc(D["author"][lang])}</p>
              <span class="open">{esc(ui["open"])}</span>
            </div>
            <div class="gilt" aria-hidden="true"></div>
          </button>
        </div>
      </div>
    </div>
  </div>
  <div class="chrome-bottom" id="chrome-bottom"{"" if open_ else " hidden"}>
    <button class="btn-toc" id="toc-btn" type="button">☰ <span>{esc(ui["contents"])}</span></button>
    <p class="folio-ind" id="folio-ind"></p>
  </div>
  <div class="overlay" id="overlay" hidden><div class="sheet" id="sheet" role="dialog" aria-label="{esc(ui["contents"])}"></div></div>
</main>
<script src="/assets/book.js" defer></script>
</body>
</html>
'''

def build():
    D = json.load(open(DATA, encoding="utf-8"))
    # assets
    os.makedirs(os.path.join(SITE, "assets", "img"), exist_ok=True)
    for f in ("book.css", "book.js"): shutil.copy(os.path.join(ROOT, "tools", f), os.path.join(SITE, "assets", f))
    for f in os.listdir(os.path.join(ROOT, "tools", "img")): shutil.copy(os.path.join(ROOT, "tools", "img", f), os.path.join(SITE, "assets", "img", f))
    # enrich data: slugs + chunks + ui
    for p in D["poems"]:
        orig_st = stanzas(p["texts"][p["orig"]]["text"])
        groups = plan(orig_st)
        p["slug"] = {}
        for l in LANGS:
            t = p["texts"][l]
            first = next((x for x in t["text"].split("\n") if x.strip()), "")
            base = t["title"] if t["title"] != "* * *" else first
            p["slug"][l] = f'{p["n"]}-{slug(base)}'
            t["chunks"] = [apply(stanzas(t["text"]), g) for g in groups]
            del t["text"]
    D["ui"] = UI
    json.dump(D, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    poems = D["poems"]
    def write(path, s):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(s)

    # root: closed book
    write(os.path.join(SITE, "index.html"), shell(D, "uk", open_=False, left="", right="",
          title="Олег Штереб — Ноти життя: до і після", desc="Oleg Shtereb — Notes of Life: Before and After. A first collection of poems in Ukrainian, Russian, English and Spanish, read as a book.",
          canonical="/", alternates={l: "" for l in LANGS}))
    urls = ["https://schtereb.com/"]
    for lang in LANGS:
        ui = UI[lang]
        left = leaf(f'<div class="center">{ORN_STAFF}<p class="epi">Art Knows No Languages</p><p class="epi-by">Oleg Shtereb</p>' + (f'<p class="epi-tr">{esc(ui["epigraph"])}</p>' if lang != "en" else "") + "</div>", "left", 1, lang, D)
        right = leaf(f'<div class="center"><p class="kick">{esc(ui["first"])}</p><h2 class="ht-main">{esc(ui["main"])}</h2><p class="ht-sub">{esc(ui["sub"])}</p></div>', "right", 2, lang, D)
        write(os.path.join(SITE, lang, "index.html"), shell(D, lang, open_=True, left=left, right=right,
              title=f'{D["title"][lang]} — {D["author"][lang]}', desc=ui["note"], canonical=f"/{lang}/", alternates={l: "" for l in LANGS}))
        urls.append(f"https://schtereb.com/{lang}/")
        for p in poems:
            t = p["texts"][lang]; o = p["texts"][p["orig"]]
            if lang == p["orig"]:
                left = leaf(poem_block(t["title"], t["chunks"][0], "", True), "left", 1, lang, D)
                right = leaf(poem_block(t["title"], t["chunks"][1], ui["continued"], False), "right", 2, lang, D) if len(t["chunks"]) > 1 else leaf('<div style="height:100%"></div>', "right", 2, lang, D)
            else:
                left = leaf(poem_block(o["title"], o["chunks"][0], ui["original"], False), "left", 1, lang, D)
                right = leaf(poem_block(t["title"], t["chunks"][0], ui["translation"], True), "right", 2, lang, D)
            ptitle = t["title"] if t["title"] != "* * *" else "* * * " + next(x for x in t["chunks"][0] if x.strip()).strip()
            first_lines = " / ".join(x.strip() for x in t["chunks"][0] if x.strip())[:150]
            alts = {l: p["slug"][l] + ".html" for l in LANGS}
            write(os.path.join(SITE, lang, p["slug"][lang] + ".html"), shell(D, lang, open_=True, left=left, right=right, n=p["n"],
                  title=f'{ptitle} — {D["title"][lang]} — {D["author"][lang]}', desc=first_lines + " …", canonical=f'/{lang}/{p["slug"][lang]}.html', alternates=alts))
            urls.append(f'https://schtereb.com/{lang}/{p["slug"][lang]}.html')
    write(os.path.join(SITE, "sitemap.xml"), '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write(os.path.join(SITE, "robots.txt"), "User-agent: *\nAllow: /\nSitemap: https://schtereb.com/sitemap.xml\n")
    write(os.path.join(SITE, ".htaccess"), """AddDefaultCharset UTF-8
DirectoryIndex index.html
Options -Indexes
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteRule ^(.*)$ https://schtereb.com/$1 [R=301,L]
RewriteCond %{HTTP_HOST} ^www\\.schtereb\\.com$ [NC]
RewriteRule ^(.*)$ https://schtereb.com/$1 [R=301,L]
<IfModule mod_headers.c>
  Header set X-Content-Type-Options "nosniff"
  Header set Referrer-Policy "strict-origin-when-cross-origin"
  <FilesMatch "\\.(css|js|jpg|svg|json)$">
    Header set Cache-Control "public, max-age=3600"
  </FilesMatch>
  <FilesMatch "\\.html$">
    Header set Cache-Control "public, max-age=300"
  </FilesMatch>
</IfModule>
""")
    for lang in LANGS:  # drop stale v1 pages
        keep = {p["slug"][lang] + ".html" for p in poems} | {"index.html"}
        d = os.path.join(SITE, lang)
        for f in os.listdir(d):
            if f not in keep: os.remove(os.path.join(d, f))
    print("site built:", len(urls), "urls")

if __name__ == "__main__":
    build()
