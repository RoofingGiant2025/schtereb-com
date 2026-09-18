#!/usr/bin/env python3
"""Generate the book site (docs/) from docs/data/poems.json produced by build_content.py.

Pages (every one is the same book shell; the JS opens it at the right leaf):
  /                         closed book (cover) + language choice
  /<lang>/                  open at the epigraph
  /<lang>/<n>-<slug>.html   open at that poem (server-rendered spread for crawlers / no-JS)
"""
import os, json, re, html, shutil, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "docs")
DATA = os.path.join(SITE, "data", "poems.json")
LANGS = ["uk", "ru", "en", "es"]
LSHORT = {"uk": "УК", "ru": "РУ", "en": "EN", "es": "ES"}
LNAME = {"uk": "Українська", "ru": "Русский", "en": "English", "es": "Español"}
MAX_LINES = 16
EDITION = json.load(open(os.path.join(ROOT, "print", "edition.json")))   # price_usd, order_url (Lulu bookstore link; empty = "coming soon")
PRINT_SPEC = json.load(open(os.path.join(ROOT, "print", "spec.json")))
ORDER_URL = EDITION.get("order_url", "")

# the hardcover edition page (/<lang>/order.html) — copy per language
EDITION_UI = {
 "uk": dict(kick="Перше видання · Тверда палітурка",
            lead="Вісімдесят два вірші чотирма мовами, зроблені як книжка, яку зберігають: тканинна палітурка, золоте тиснення на корінці, друкована суперобкладинка, кремовий папір. Кожен примірник друкується на замовлення й надсилається вам із найближчої друкарні.",
            plus="плюс доставка", ship="Друкує й надсилає Lulu — зі США, Великої Британії, Євросоюзу чи Австралії, звідки ближче до вас. Доставка приблизно два–три тижні; є швидші варіанти.",
            specs_h="Видання", specs=[("Палітурка", "Тверда, тканинна (чорний льон), корінець із золотим тисненням"), ("Суперобкладинка", "Друкована, з клапанами, матова"),
                                      ("Папір", "Кремовий, некрейдований, ≈ 90 г/м²"), ("Формат", "152 × 229 мм (6 × 9″) · {pages} сторінки"),
                                      ("Усередині", "82 вірші — кожен мовою оригіналу та у віршованих перекладах: українською, російською, англійською, іспанською. Сторінка видання для номера примірника й підпису автора."),
                                      ("Видання", "Перше, 2026 · друк на замовлення, по одному примірнику")],
            jacket="Суперобкладинка: задній клапан, задня сторона, корінець, передня сторона, передній клапан.", jacket_alt="Розгорнута суперобкладинка книжки"),
 "ru": dict(kick="Первое издание · Твёрдый переплёт",
            lead="Восемьдесят два стихотворения на четырёх языках, сделанные как книга, которую хранят: тканевый переплёт, золотое тиснение на корешке, печатная суперобложка, кремовая бумага. Каждый экземпляр печатается под заказ и отправляется вам из ближайшей типографии.",
            plus="плюс доставка", ship="Печатает и отправляет Lulu — из США, Великобритании, Евросоюза или Австралии, откуда ближе к вам. Доставка примерно две–три недели; есть варианты быстрее.",
            specs_h="Издание", specs=[("Переплёт", "Твёрдый, тканевый (чёрный лён), корешок с золотым тиснением"), ("Суперобложка", "Печатная, с клапанами, матовая"),
                                      ("Бумага", "Кремовая, немелованная, ≈ 90 г/м²"), ("Формат", "152 × 229 мм (6 × 9″) · {pages} страницы"),
                                      ("Внутри", "82 стихотворения — каждое на языке оригинала и в стихотворных переводах: украинском, русском, английском, испанском. Страница издания для номера экземпляра и подписи автора."),
                                      ("Издание", "Первое, 2026 · печать под заказ, по одному экземпляру")],
            jacket="Суперобложка: задний клапан, задняя сторона, корешок, передняя сторона, передний клапан.", jacket_alt="Развёрнутая суперобложка книги"),
 "en": dict(kick="First edition · Hardcover",
            lead="Eighty-two poems in four languages, made as a book to keep: cloth over boards, a spine stamped in gold, a printed dust jacket, cream paper. Every copy is printed to order and posted to you from the nearest press.",
            plus="plus shipping", ship="Printed and shipped by Lulu from the United States, the United Kingdom, the European Union or Australia — whichever is nearest to you. Delivery in about two to three weeks; faster options exist.",
            specs_h="The edition", specs=[("Binding", "Cloth-bound hardcover, black linen, spine stamped in gold foil"), ("Jacket", "Printed dust jacket with flaps, matte"),
                                          ("Paper", "Cream, uncoated, 60 lb"), ("Format", "6 × 9 in (152 × 229 mm) · {pages} pages"),
                                          ("Inside", "82 poems, each in its original language and in verse translation — Ukrainian, Russian, English, Spanish. An edition page for the author's number and signature."),
                                          ("Edition", "First edition, 2026 · printed to order, one copy at a time")],
            jacket="The dust jacket: back flap, back, spine, front, front flap.", jacket_alt="The book's dust jacket, opened flat"),
 "es": dict(kick="Primera edición · Tapa dura",
            lead="Ochenta y dos poemas en cuatro idiomas, hechos como un libro para guardar: tapas enteladas, lomo estampado en oro, sobrecubierta impresa, papel crema. Cada ejemplar se imprime bajo pedido y se le envía desde la imprenta más cercana.",
            plus="más envío", ship="Lulu imprime y envía desde Estados Unidos, el Reino Unido, la Unión Europea o Australia, según lo que le quede más cerca. Entrega en unas dos o tres semanas; hay opciones más rápidas.",
            specs_h="La edición", specs=[("Encuadernación", "Tapa dura entelada (lino negro), lomo estampado en oro"), ("Sobrecubierta", "Impresa, con solapas, mate"),
                                         ("Papel", "Crema, no estucado, ≈ 90 g/m²"), ("Formato", "15,2 × 22,9 cm (6 × 9″) · {pages} páginas"),
                                         ("Contenido", "82 poemas, cada uno en su lengua original y en traducción en verso: ucraniano, ruso, inglés, español. Una página de edición para el número del ejemplar y la firma del autor."),
                                         ("Edición", "Primera, 2026 · impresa bajo pedido, ejemplar a ejemplar")],
            jacket="La sobrecubierta: solapa trasera, contraportada, lomo, portada, solapa delantera.", jacket_alt="La sobrecubierta del libro, extendida"),
}

UI = {
 "uk": dict(manuscript="Рукопис", autograph="Автограф", zoom="Розглянути", of_pages="з", ms_close="Закрити", ms_hint="Торкніться аркуша, щоб роздивитися",
            listen="Слухати", stop="Зупинити", order="Друкована книжка", order_btn="Замовити книжку", order_soon="Друковане видання готується — незабаром тут з’явиться кнопка замовлення.",
            order_text="Паперове видання: м’яка обкладинка, 152 × 229 мм (6 × 9″), 422 сторінки, кремовий папір. Усі 82 вірші мовою оригіналу та в перекладах — українською, російською, англійською, іспанською. Друкується на замовлення й надсилається поштою в будь-яку країну.",
            main="Ноти життя", sub="до і після", first="Перша збірка", count="Вірші I–LXXX · Після I–II", open="Відкрити книжку",
            contents="Зміст", close="Закрити", original="Оригінал", translation="Переклад", continued="продовження",
            edition="Перше видання", house="Штереб", rights="Усі права застережено.", published="Видано на schtereb.com",
            epigraph="Мистецтво не знає мов", dedication="Тим, хто живе мрією", epigraph_short="Епіграф", titlepage="Титул", colophon_short="Колофон",
            facing="Оригінал ліворуч, переклад праворуч.",
            about="Про автора", about_caption="Олег Штереб і Ґуччі", about_poem="Про вірш", about_btn="Про вірш",
            about_text="Олег Штереб пише українською, російською та англійською. Вісімдесят віршів частини «До» вперше оприлюднено на shtereb.com у 2019 році; два вірші «Після» написано пізніше, англійською. «Ноти життя» — його перша збірка, яку тут читають чотирма мовами, поряд з оригіналами.",
            note="У частині «До» кожен вірш надруковано спершу мовою оригіналу — українською або російською: правопис, пунктуація й окремі англійські слова лишені так, як написав автор. Українська, російська, англійська та іспанська версії — віршовані переклади 2026 року. Два вірші «Після» написані англійською. Факсиміле рукописів і малюнки — з архіву автора, 1998–2006.",
            colophon="Набрано гарнітурами Cormorant Garamond і Source Serif. Зроблено як книжку для читання, а не сторінку для гортання. Оригінали вперше оприлюднено на shtereb.com (2019). Дім Штереба."),
 "ru": dict(manuscript="Рукопись", autograph="Автограф", zoom="Рассмотреть", of_pages="из", ms_close="Закрыть", ms_hint="Коснитесь листа, чтобы рассмотреть",
            listen="Слушать", stop="Остановить", order="Печатная книга", order_btn="Заказать книгу", order_soon="Печатное издание готовится — скоро здесь появится кнопка заказа.",
            order_text="Бумажное издание: мягкая обложка, 152 × 229 мм (6 × 9″), 422 страницы, кремовая бумага. Все 82 стихотворения на языке оригинала и в переводах — украинском, русском, английском, испанском. Печатается под заказ и отправляется почтой в любую страну.",
            main="Ноты жизни", sub="до и после", first="Первый сборник", count="Стихи I–LXXX · После I–II", open="Открыть книгу",
            contents="Содержание", close="Закрыть", original="Оригинал", translation="Перевод", continued="продолжение",
            edition="Первое издание", house="Штереб", rights="Все права защищены.", published="Издано на schtereb.com",
            epigraph="Искусство не знает языков", dedication="Тем, кто живёт мечтой", epigraph_short="Эпиграф", titlepage="Титул", colophon_short="Колофон",
            facing="Оригинал слева, перевод справа.",
            about="Об авторе", about_caption="Олег Штереб и Гуччи", about_poem="О стихотворении", about_btn="Заметка",
            about_text="Олег Штереб пишет на украинском, русском и английском. Восемьдесят стихотворений части «До» впервые опубликованы на shtereb.com в 2019 году; два стихотворения «После» написаны позже, по-английски. «Ноты жизни» — его первый сборник, который здесь читают на четырёх языках, рядом с оригиналами.",
            note="В части «До» каждое стихотворение напечатано сначала на языке оригинала — украинском или русском: орфография, пунктуация и отдельные английские слова оставлены так, как написал автор. Украинская, русская, английская и испанская версии — стихотворные переводы 2026 года. Два стихотворения «После» написаны по-английски. Факсимиле рукописей и рисунки — из архива автора, 1998–2006.",
            colophon="Набрано гарнитурами Cormorant Garamond и Source Serif. Сделано как книга для чтения, а не страница для прокрутки. Оригиналы впервые опубликованы на shtereb.com (2019). Дом Штереба."),
 "en": dict(manuscript="Manuscript", autograph="Autograph", zoom="Look closer", of_pages="of", ms_close="Close", ms_hint="Tap the sheet to look closer",
            listen="Listen", stop="Stop", order="The printed book", order_btn="Order the book", order_soon="The printed edition is being prepared — the order button will appear here soon.",
            order_text="Paperback, 6 × 9 in (152 × 229 mm), 422 pages, cream paper. All 82 poems in their original language and in verse translation — Ukrainian, Russian, English, Spanish. Printed on demand and shipped to any country.",
            main="Notes of Life", sub="Before and After", first="A first collection", count="Poems I–LXXX · After I–II", open="Open the book",
            contents="Contents", close="Close", original="Original", translation="Translation", continued="continued",
            edition="First edition", house="Schtereb", rights="All rights reserved.", published="Published at schtereb.com",
            epigraph="Art Knows No Languages", dedication="To Those Who Are Living the Dream", epigraph_short="Epigraph", titlepage="Title page", colophon_short="Colophon",
            facing="Original on the left, translation on the right.",
            about="About the author", about_caption="Oleg Schtereb and Gucci", about_poem="About the poem", about_btn="About",
            about_text="Oleg Schtereb writes in Ukrainian, Russian and English. The eighty poems of Before were first published on shtereb.com in 2019; the two poems of After were written later, in English. Notes of Life is his first collection — read here in four languages, beside the originals.",
            note="In Before, each poem is printed first in its original Ukrainian or Russian — spelling, punctuation and the occasional English word left as the author wrote them. The Ukrainian, Russian, English and Spanish versions are verse translations made in 2026. The two poems of After were written in English. The manuscript facsimiles and drawings are from the author’s archive, 1998–2006.",
            colophon="Set in Cormorant Garamond and Source Serif. Designed as a book to be read, not a page to be scrolled. Originals first published at shtereb.com (2019). The house of Schtereb."),
 "es": dict(manuscript="Manuscrito", autograph="Autógrafo", zoom="Ver de cerca", of_pages="de", ms_close="Cerrar", ms_hint="Toca la hoja para verla de cerca",
            listen="Escuchar", stop="Detener", order="El libro impreso", order_btn="Pedir el libro", order_soon="La edición impresa se está preparando — pronto aparecerá aquí el botón de pedido.",
            order_text="Tapa blanda, 15,2 × 22,9 cm (6 × 9″), 422 páginas, papel crema. Los 82 poemas en su lengua original y en traducción en verso — ucraniano, ruso, inglés, español. Impreso bajo demanda y enviado a cualquier país.",
            main="Notas de la vida", sub="antes y después", first="Primera colección", count="Poemas I–LXXX · Después I–II", open="Abrir el libro",
            contents="Índice", close="Cerrar", original="Original", translation="Traducción", continued="continúa",
            edition="Primera edición", house="Schtereb", rights="Todos los derechos reservados.", published="Publicado en schtereb.com",
            epigraph="El arte no conoce idiomas", dedication="A quienes viven el sueño", epigraph_short="Epígrafe", titlepage="Portada", colophon_short="Colofón",
            facing="Original a la izquierda, traducción a la derecha.",
            about="Sobre el autor", about_caption="Oleg Schtereb y Gucci", about_poem="Sobre el poema", about_btn="Nota",
            about_text="Oleg Schtereb escribe en ucraniano, ruso e inglés. Los ochenta poemas de Antes se publicaron por primera vez en shtereb.com en 2019; los dos poemas de Después se escribieron más tarde, en inglés. Notas de la vida es su primera colección, que aquí se lee en cuatro idiomas, junto a los originales.",
            note="En Antes, cada poema se imprime primero en su original ucraniano o ruso: grafía, puntuación y las palabras inglesas ocasionales se dejan como las escribió el autor. Las versiones ucraniana, rusa, inglesa y española son traducciones en verso de 2026. Los dos poemas de Después se escribieron en inglés. Los facsímiles de los manuscritos y los dibujos proceden del archivo del autor, 1998–2006.",
            colophon="Compuesto en Cormorant Garamond y Source Serif. Hecho para leerse como un libro, no para desplazarse como una página. Originales publicados por primera vez en shtereb.com (2019). La casa de Schtereb."),
}

SONG_UI = {
 "uk": dict(song="Пісня", single="Сингл", from_poem="з вірша", lyrics_author="Текст автора", lyrics_transcribed="Розшифровка запису · до вичитки", lyrics_pending="Текст ще не додано", preview="Фрагмент 30 с"),
 "ru": dict(song="Песня", single="Сингл", from_poem="из стихотворения", lyrics_author="Авторский текст", lyrics_transcribed="Расшифровка записи · до вычитки", lyrics_pending="Текст ещё не добавлен", preview="Фрагмент 30 с"),
 "en": dict(song="Song", single="Single", from_poem="from poem", lyrics_author="The author's lyric sheet", lyrics_transcribed="Transcribed from the recording · unproofed", lyrics_pending="Lyrics not yet added", preview="30-second preview"),
 "es": dict(song="Canción", single="Sencillo", from_poem="del poema", lyrics_author="Letra del autor", lyrics_transcribed="Transcrita de la grabación · sin revisar", lyrics_pending="Letra aún no añadida", preview="Fragmento de 30 s"),
}
for _l in SONG_UI: UI[_l].update(SONG_UI[_l])

TR = {**dict(zip("абвгдежзийклмнопрстуфхцчшщъыьэюя", ["a","b","v","g","d","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","kh","ts","ch","sh","shch","","y","","e","yu","ya"])),
      "ё":"e","є":"ye","і":"i","ї":"yi","ґ":"g","á":"a","é":"e","í":"i","ó":"o","ú":"u","ñ":"n","ü":"u"}
def slug(s):
    s = "".join(TR.get(c, c) for c in s.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:48].rstrip("-") or "poem"
def esc(s): return html.escape(s, quote=True)
def old_slug_redirects(poems):
    """One RedirectPermanent per former slug listed in content/old-slugs.json that differs from the poem's current slug."""
    path = os.path.join(ROOT, "content", "old-slugs.json")
    if not os.path.exists(path): return ""
    reg = json.load(open(path, encoding="utf-8"))
    by_n = {p["n"]: p for p in poems}
    out = []
    for lang, d in reg.items():
        for n, olds in d.items():
            cur = by_n[int(n)]["slug"][lang]
            for old in olds:
                if f"{n}-{old}" != cur:
                    out.append(f"RedirectPermanent /{lang}/{n}-{old}.html https://schtereb.com/{lang}/{cur}.html")
    return "\n".join(out) + ("\n" if out else "")

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
LISTEN_SVG = '<svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true"><path d="M3 7.5v5h3l4 3.5v-12l-4 3.5H3z" fill="currentColor"/><path d="M12.5 6.5a4.5 4.5 0 0 1 0 7M14.5 4a8 8 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>'
ABOUT_SVG = '<svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true"><circle cx="10" cy="10" r="7.25" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M10 9v5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="10" cy="6.4" r=".9" fill="currentColor"/></svg>'
def poem_block(title, lines, kicker, drop, n=None, lang=None, listen="", note=""):
    btn = f'<button class="listen" type="button" data-n="{n}" data-lang="{lang}" data-listen="{esc(listen)}" data-stop="" aria-label="{esc(listen)}">{LISTEN_SVG}<span>{esc(listen)}</span></button>' if n else ""
    tail = ""
    if n and note:   # the headnote in the reading language: "About" button (opens the sheet once the reader runs) + a <details> for crawlers and no-JS readers
        ui = UI[lang]
        btn += f'<button class="about-btn" type="button" data-about="{n}" aria-label="{esc(ui["about_poem"])}">{ABOUT_SVG}<span>{esc(ui["about_btn"])}</span></button>'
        note_html = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", esc(note))   # *word* = italics, as in the reader
        tail = f'<details class="headnote"><summary>{esc(ui["about_poem"])}</summary><p>{note_html}</p></details>'
    return '<div class="poem"><div class="poem-head">' + (f'<p class="kick">{esc(kicker)}</p>' if kicker else "<p></p>") + f'<span class="poem-tools">{btn}</span></div>' + f"<h2>{esc(title)}</h2>{ORN_RULE}{verse_html(lines, drop)}{tail}</div>"
def meta_desc(s, limit=155):
    """The headnote as the page description, cut at a word boundary."""
    s = s.replace("*", "")
    if len(s) <= limit: return s
    cut = s[:limit].rsplit(" ", 1)[0].rstrip(",;:—– ")
    return cut + " …"
def ms_leaf(p, lang, D):
    """Facsimile plate: the sheet lying on the leaf; caption with roman numeral, date and medium."""
    ui = UI[lang]; m = p["ms"]; pg = m["pages"][0]
    cap = " · ".join(x for x in (ui["autograph"], m.get("date", ""), m.get("medium", {}).get(lang, "")) if x)
    more = f'<span class="ms-more">1 {esc(ui["of_pages"])} {len(m["pages"])}</span>' if len(m["pages"]) > 1 else ""
    return (f'<div class="leaf plate"><div class="leaf-body"><figure class="ms" data-n="{p["n"]}">'
            f'<button type="button" class="ms-sheet" aria-label="{esc(ui["zoom"])}"><img src="/{pg["src"]}?v={D.get("_ver", "0")}" alt="{esc(ui["manuscript"])} — {esc(p["texts"][lang]["title"])}" width="{pg["w"]}" height="{pg["h"]}" decoding="async">{more}</button>'
            f'<figcaption><span class="r">{p["roman"]}</span><span class="c">{esc(cap)}</span></figcaption></figure></div>'
            f'<footer class="leaf-foot"><span class="n"></span><span>{esc(ui["manuscript"])}</span></footer></div>')
def leaf(body, side, folio, lang, D):
    ui = UI[lang]
    foot = f'<span class="n">{folio}</span><span>{esc(D["author"][lang])}</span>' if side == "left" else f'<span>{esc(ui["main"])}</span><span class="n">{folio}</span>'
    return f'<div class="leaf"><div class="leaf-body">{body}</div><footer class="leaf-foot">{foot}</footer></div>'

def shell(D, lang, *, open_, left, right, title, desc, n=None, canonical="", alternates=None):
    ui = UI[lang]; ver = D.get("_ver", "0")
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
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="https://schtereb.com/assets/img/og.jpg"><meta property="og:type" content="book"><meta property="og:url" content="https://schtereb.com{canonical}"><meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/book.css?v={ver}">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml"><link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
</head>
<body>
<main class="room" id="book-root" data-lang="{lang}" data-open="{"1" if open_ else "0"}" data-base="/" data-v="{ver}"{f' data-n="{n}"' if n else ""}>
  <header class="chrome">
    <a class="wordmark" href="/">Штереб</a>
    <div class="chrome-right"><a class="order-link" href="/{lang}/order.html">{esc(ui["order"])}</a><nav class="langs" id="langs" aria-label="Language">{langs}</nav></div>
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
      </div>
      <div class="tome-shadow" aria-hidden="true"></div>
      <div class="tome" id="cover" data-open="{"true" if open_ else "false"}" aria-hidden="{"true" if open_ else "false"}">
        <div class="bd back" aria-hidden="true">
          <div class="f bk"></div><div class="f bi"></div>
          <div class="f be et"></div><div class="f be er"></div><div class="f be eb"></div>
        </div>
        <div class="f spine3" aria-hidden="true">
          <i class="band"></i><span class="sp-t">{esc(ui["main"])}: {esc(ui["sub"])}</span><span class="sp-a">{esc(D["author"][lang])}</span><span class="sp-m">Ш</span><i class="band"></i>
        </div>
        <div class="f pg pt" aria-hidden="true"></div><div class="f pg pr" aria-hidden="true"></div><div class="f pg pb" aria-hidden="true"></div><div class="f fly" aria-hidden="true"></div>
        <div class="f rib3" aria-hidden="true"></div>
        <div class="bd front">
          <button type="button" class="f fr" id="cover-open" aria-label="{esc(ui["open"])}">
            <div class="frame" aria-hidden="true"></div>
            <div class="type">
              <p class="k gilt">{esc(ui["first"])}</p>
              <div class="plate"><img src="/assets/img/cover.jpg" alt="" width="960" height="1440" fetchpriority="high"></div>
              {ORN_STAFF}
              <h1 class="gilt">{esc(ui["main"])}</h1>
              <p class="s gilt">{esc(ui["sub"])}</p>
              {ORN_RULE}
              <p class="a gilt">{esc(D["author"][lang])}</p>
              <p class="c">{esc(ui["count"])}</p>
              <p class="ll">Українська · Русский · English · Español</p>
            </div>
            <div class="sheen"></div><div class="joint"></div><div class="bevel"></div>
          </button>
          <div class="f fi" aria-hidden="true"></div>
          <div class="f be et" aria-hidden="true"></div><div class="f be er" aria-hidden="true"></div><div class="f be eb" aria-hidden="true"></div>
        </div>
      </div>
    </div>
    <button class="tome-cta" id="cover-cta" type="button" tabindex="-1" aria-hidden="true"{"" if not open_ else " hidden"}><span>{esc(ui["open"])}</span> <svg viewBox="0 0 20 20" width="12" height="12" aria-hidden="true"><path d="M4 10h11M10 5l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
  </div>
  <div class="chrome-bottom" id="chrome-bottom"{"" if open_ else " hidden"}>
    <button class="btn-toc" id="toc-btn" type="button">☰ <span>{esc(ui["contents"])}</span></button>
    <p class="folio-ind" id="folio-ind"></p>
  </div>
  <div class="overlay" id="overlay" hidden><div class="sheet" id="sheet" role="dialog" aria-label="{esc(ui["contents"])}"></div></div>
  <div class="lightbox" id="lightbox" hidden role="dialog" aria-label="{esc(ui["manuscript"])}">
    <button class="lb-close" id="lb-close" type="button" aria-label="{esc(ui["ms_close"])}">×</button>
    <div class="lb-stage" id="lb-stage"><img id="lb-img" alt="" draggable="false"></div>
    <div class="lb-bar"><button class="lb-nav" id="lb-prev" type="button" aria-label="Previous">‹</button><p class="lb-cap" id="lb-cap"></p><button class="lb-nav" id="lb-next" type="button" aria-label="Next">›</button></div>
  </div>
</main>
<script src="/assets/book.js?v={ver}" defer></script>
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
            p["slug"][l] = (f's{p["n"] - 1000:02d}-' if p.get("song") else f'{p["n"]}-') + slug(base)
            tst = stanzas(t["text"])
            t["chunks"] = [apply(tst, g) for g in groups]
            for extra in tst[len(orig_st):]:          # e.g. a translator's note stanza with no counterpart in the original
                t["chunks"][-1] += [""] + extra
            del t["text"]
    D["ui"] = UI
    # facsimiles: docs/assets/ms/manifest.json is written by tools/manuscripts.py from content/manuscripts.json
    mf_path = os.path.join(SITE, "assets", "ms", "manifest.json")
    MF = json.load(open(mf_path, encoding="utf-8")) if os.path.exists(mf_path) else {"poems": {}, "art": {}}
    MAN = json.load(open(os.path.join(ROOT, "content", "manuscripts.json"), encoding="utf-8"))
    for p in D["poems"]:
        m = MF["poems"].get(str(p["n"]))
        if m and all(os.path.exists(os.path.join(SITE, pg["src"])) for pg in m["pages"]):
            src = MAN["poems"].get(str(p["n"]), {})
            p["ms"] = {"pages": m["pages"], "date": src.get("date", ""), "medium": src.get("medium", {}), "note": src.get("note", {})}
    D["art"] = {k: v for k, v in MF["art"].items() if os.path.exists(os.path.join(SITE, v["src"]))}
    # author portrait spread (before the colophon) — only when the photo exists; tools/img/author.jpg → /assets/img/author.jpg
    if os.path.exists(os.path.join(ROOT, "tools", "img", "author.jpg")): D["portrait"] = "assets/img/author.jpg"
    blob = json.dumps(D, ensure_ascii=False, separators=(",", ":"))
    am_path = os.path.join(SITE, "audio", "manifest.json")   # audio manifest is part of the version: re-recordings bust its URL too
    am = open(am_path, encoding="utf-8").read() if os.path.exists(am_path) else ""
    D["_ver"] = hashlib.sha1((blob + am + open(os.path.join(ROOT, "tools", "book.js")).read() + open(os.path.join(ROOT, "tools", "book.css")).read()).encode()).hexdigest()[:10]
    open(DATA, "w", encoding="utf-8").write(blob)
    poems = D["poems"]
    def write(path, s):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(s)

    # root: closed book
    write(os.path.join(SITE, "index.html"), shell(D, "uk", open_=False, left="", right="",
          title="Олег Штереб — Ноти життя: до і після", desc="Oleg Schtereb — Notes of Life: Before and After. A first collection of poems in Ukrainian, Russian, English and Spanish, read as a book.",
          canonical="/", alternates={l: "" for l in LANGS}))
    urls = ["https://schtereb.com/"]
    for lang in LANGS:
        ui = UI[lang]
        left = leaf(f'<div class="center">{ORN_STAFF}<p class="epi">Art Knows No Languages</p><p class="epi-by">Oleg Schtereb</p>' + (f'<p class="epi-tr">{esc(ui["epigraph"])}</p>' if lang != "en" else "") + "</div>", "left", 1, lang, D)
        right = leaf(f'<div class="center"><p class="kick">{esc(ui["first"])}</p><h2 class="ht-main">{esc(ui["main"])}</h2><p class="ht-sub">{esc(ui["sub"])}</p></div>', "right", 2, lang, D)
        write(os.path.join(SITE, lang, "index.html"), shell(D, lang, open_=True, left=left, right=right,
              title=f'{D["title"][lang]} — {D["author"][lang]}', desc=ui["note"], canonical=f"/{lang}/", alternates={l: "" for l in LANGS}))
        urls.append(f"https://schtereb.com/{lang}/")
        for p in poems:
            t = p["texts"][lang]; o = p["texts"][p["orig"]]
            if lang == p["orig"] or p.get("single"):   # (an autograph, when there is one, faces the title plate on the spread before — as the reader lays it out)
                left = leaf(poem_block(t["title"], t["chunks"][0], "", True, p["n"], lang, ui["listen"], p["note"][lang]), "left", 1, lang, D)
                right = leaf(poem_block(t["title"], t["chunks"][1], ui["continued"], False), "right", 2, lang, D) if len(t["chunks"]) > 1 else leaf('<div style="height:100%"></div>', "right", 2, lang, D)
            else:
                left = leaf(poem_block(o["title"], o["chunks"][0], ui["original"], False, p["n"], p["orig"], UI[p["orig"]]["listen"]), "left", 1, lang, D)
                right = leaf(poem_block(t["title"], t["chunks"][0], ui["translation"], True, p["n"], lang, ui["listen"], p["note"][lang]), "right", 2, lang, D)
            ptitle = t["title"] if t["title"] != "* * *" else "* * * " + next(x for x in t["chunks"][0] if x.strip()).strip()
            alts = {l: p["slug"][l] + ".html" for l in LANGS}
            write(os.path.join(SITE, lang, p["slug"][lang] + ".html"), shell(D, lang, open_=True, left=left, right=right, n=p["n"],
                  title=f'{ptitle} — {D["title"][lang]} — {D["author"][lang]}', desc=meta_desc(p["note"][lang]), canonical=f'/{lang}/{p["slug"][lang]}.html', alternates=alts))
            urls.append(f'https://schtereb.com/{lang}/{p["slug"][lang]}.html')
    for lang in LANGS:
        ui = UI[lang]
        eu = EDITION_UI[lang]
        btn = f'<a class="btn-order" href="{ORDER_URL}" rel="noopener">{esc(ui["order_btn"])} →</a>' if ORDER_URL else f'<p class="soon">{esc(ui["order_soon"])}</p>'
        html_ = shell(D, lang, open_=False, left="", right="", title=f'{ui["order"]} — {D["title"][lang]}', desc=eu["lead"], canonical=f"/{lang}/order.html", alternates={l: "order.html" for l in LANGS})
        # the closed 3-D book from the home page, as a still object (no JS on this page): lift its markup out of the shell
        tome = html_[html_.index('<div class="tome-shadow"'):html_.index('<button class="tome-cta"')]
        tome = tome[:tome.rindex("</div>")]                      # drop the .stage closer
        tome = tome.replace('<button type="button" class="f fr" id="cover-open"', '<div class="f fr"').replace("</button>", "</div>").replace(' id="cover"', "")
        specs = "".join(f'<div><dt>{esc(k)}</dt><dd>{esc(v.format(pages=PRINT_SPEC["pages"]))}</dd></div>' for k, v in eu["specs"])
        body = f'''<main class="room order-room edition"><header class="chrome"><a class="wordmark" href="/">Штереб</a><nav class="langs" aria-label="Language">{"".join(f'<a href="/{l}/order.html" class="{"on" if l == lang else ""}" hreflang="{l}">{LSHORT[l]}</a>' for l in LANGS)}</nav></header>
<section class="ed-hero">
  <div class="stage-wrap ed-stage" aria-hidden="true"><div class="stage closed">{tome}</div></div>
  <div class="ed-text">
    <p class="kick ed-kick">{esc(eu["kick"])}</p>
    <h1>{esc(D["title"][lang])}</h1>
    <p class="order-author">{esc(D["author"][lang])}</p>
    <p class="order-desc ed-lead">{esc(eu["lead"])}</p>
    <div class="ed-buy">
      <p class="ed-price"><span class="ed-num">${EDITION["price_usd"]}</span><span class="ed-plus">USD · {esc(eu["plus"])}</span></p>
      {btn}
    </div>
    <p class="ed-ship">{esc(eu["ship"])}</p>
  </div>
</section>
<section class="ed-specs">
  <h2 class="kick">{esc(eu["specs_h"])}</h2>
  <dl>{specs}</dl>
</section>
<figure class="ed-jacket">
  <img src="/assets/img/jacket.jpg" alt="{esc(eu["jacket_alt"])}" width="2000" height="928" loading="lazy">
  <figcaption>{esc(eu["jacket"])}</figcaption>
</figure>
<p class="order-back ed-back"><a href="/{lang}/">← {esc(ui["main"])}</a></p>
</main>'''
        html_ = html_[:html_.index('<main class="room"')] + body + '\n</body>\n</html>\n'
        write(os.path.join(SITE, lang, "order.html"), html_)
        urls.append(f"https://schtereb.com/{lang}/order.html")
    write(os.path.join(SITE, "sitemap.xml"), '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write(os.path.join(SITE, "robots.txt"), "User-agent: *\nAllow: /\nSitemap: https://schtereb.com/sitemap.xml\n")
    write(os.path.join(SITE, ".htaccess"), """AddDefaultCharset UTF-8
ErrorDocument 404 /404.html
AddType audio/mp4 .m4a
AddType application/json .json
DirectoryIndex index.html
Options -Indexes
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteRule ^(.*)$ https://schtereb.com/$1 [R=301,L]
RewriteCond %{HTTP_HOST} ^www\\.schtereb\\.com$ [NC]
RewriteRule ^(.*)$ https://schtereb.com/$1 [R=301,L]
# former poem URLs (content/old-slugs.json; a slug follows the title / first line, so a retranslation can move a page)
""" + old_slug_redirects(poems) + """<IfModule mod_headers.c>
  Header set X-Content-Type-Options "nosniff"
  Header set Strict-Transport-Security "max-age=31536000"
  Header set Referrer-Policy "strict-origin-when-cross-origin"
  <FilesMatch "\\.(css|js|jpg|svg|json)$">
    Header set Cache-Control "public, max-age=3600"
  </FilesMatch>
  <FilesMatch "\\.m4a$">
    Header set Cache-Control "public, max-age=604800"
  </FilesMatch>
  <FilesMatch "\\.html$">
    Header set Cache-Control "public, max-age=300"
  </FilesMatch>
</IfModule>
""")
    # custom 404 (served for any missing path)
    nf = shell(D, "uk", open_=False, left="", right="", title="404 — Ноти життя: до і після", desc="Сторінку не знайдено · Page not found", canonical="/404.html")
    nf = nf[:nf.index('<main class="room"')] + '''<main class="room order-room"><header class="chrome"><a class="wordmark" href="/">Штереб</a></header>
<section class="order" style="grid-template-columns:1fr;text-align:center;max-width:36rem"><div class="order-text">
<p class="kick" style="color:var(--fg-muted)">404</p><h1>Такої сторінки немає</h1>
<p class="order-desc" style="margin:0 auto">No such page · Нет такой страницы · No existe esta página</p>
<p class="order-back" style="margin-top:2rem"><a href="/uk/">Українська</a> · <a href="/ru/">Русский</a> · <a href="/en/">English</a> · <a href="/es/">Español</a></p>
</div></section></main>\n</body>\n</html>\n'''
    write(os.path.join(SITE, "404.html"), nf)
    try:
        from PIL import Image, ImageDraw, ImageFont
        for size, name in ((180, "apple-touch-icon.png"), (32, "favicon.ico")):
            im = Image.new("RGB", (size, size), "#f4ead6"); dr = ImageDraw.Draw(im)
            f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia.ttf", int(size * 0.66))
            w, h = dr.textbbox((0, 0), "Ш", font=f)[2:]
            dr.text(((size - w) / 2, (size - h) / 2 - size * 0.08), "Ш", font=f, fill="#6e2c2c")
            im.save(os.path.join(SITE, name), format="PNG" if name.endswith("png") else "ICO", sizes=[(32, 32)] if name.endswith("ico") else None)
    except Exception as e:
        print("icons skipped:", e)
    for lang in LANGS:  # drop stale v1 pages
        keep = {p["slug"][lang] + ".html" for p in poems} | {"index.html", "order.html"}
        d = os.path.join(SITE, lang)
        for f in os.listdir(d):
            if f not in keep: os.remove(os.path.join(d, f))
    print("site built:", len(urls), "urls")

if __name__ == "__main__":
    build()
