#!/usr/bin/env python3
"""Build the bilingual (original + English) PDF book from content/*.md.

Content format: '# ' = section title (first one in a file is the book title and is
skipped), '## ' = poem title, blank line = stanza break, '*...*' whole line = note.
Leading spaces inside poems are the author's indentation and are preserved.
"""
import re, sys, os
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                PageBreak, KeepTogether, NextPageTemplate, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = "/System/Library/Fonts/Supplemental/"
pdfmetrics.registerFont(TTFont("Georgia", FONTS + "Georgia.ttf"))
pdfmetrics.registerFont(TTFont("Georgia-Italic", FONTS + "Georgia Italic.ttf"))
pdfmetrics.registerFont(TTFont("Georgia-Bold", FONTS + "Georgia Bold.ttf"))
pdfmetrics.registerFont(TTFont("Georgia-BoldItalic", FONTS + "Georgia Bold Italic.ttf"))
registerFontFamily("Georgia", normal="Georgia", bold="Georgia-Bold",
                   italic="Georgia-Italic", boldItalic="Georgia-BoldItalic")

PAGE = (6 * inch, 9 * inch)
M_IN, M_OUT, M_TOP, M_BOT = 0.85 * inch, 0.75 * inch, 0.8 * inch, 0.8 * inch

CYR_UK = re.compile(r"[іїєґІЇЄҐ]")
CYR_RU = re.compile(r"[ыэъёЫЭЪЁ]")

def detect_lang(text):
    uk, ru = len(CYR_UK.findall(text)), len(CYR_RU.findall(text))
    # every Ukrainian poem uses і/ї/є; a poem with none of them is Russian; no Cyrillic at all = English
    if uk == 0 and ru == 0 and not re.search(r"[а-яА-Я]", text):
        return "en"
    return "uk" if uk > 0 else "ru"

LANG_NAME = {"uk": "Ukrainian", "ru": "Russian", "en": "English", "es": "Spanish"}
LANG_NATIVE = {"uk": "українська", "ru": "русский", "en": "English", "es": "español"}

def parse(path):
    """Return (book_title, poems) where poems = [{'section','title','body':[lines]}]."""
    poems, section, cur = [], None, None
    seen_title = False
    for raw in open(path, encoding="utf-8").read().split("\n"):
        line = raw.rstrip()
        if line.startswith("# "):
            if not seen_title:
                seen_title = True
                continue
            section = line[2:].strip()
            cur = None
            continue
        if line.startswith("## "):
            cur = {"section": section, "title": line[3:].strip(), "body": []}
            poems.append(cur)
            continue
        if cur is None or line.startswith("### ") or line.strip() == "---":
            continue
        cur["body"].append(line)
    for p in poems:
        while p["body"] and not p["body"][0].strip():
            p["body"].pop(0)
        while p["body"] and not p["body"][-1].strip():
            p["body"].pop()
        p["lang"] = detect_lang("\n".join(p["body"]))
    return poems

# ---------- styles ----------
S = {}
S["title"] = ParagraphStyle("title", fontName="Georgia", fontSize=26, leading=32, alignment=TA_CENTER)
S["subtitle"] = ParagraphStyle("subtitle", fontName="Georgia-Italic", fontSize=13, leading=18, alignment=TA_CENTER)
S["author"] = ParagraphStyle("author", fontName="Georgia", fontSize=15, leading=20, alignment=TA_CENTER,
                             textColor=colors.HexColor("#333333"))
S["section"] = ParagraphStyle("section", fontName="Georgia", fontSize=20, leading=26, alignment=TA_CENTER)
S["section_sub"] = ParagraphStyle("section_sub", fontName="Georgia-Italic", fontSize=12, leading=16, alignment=TA_CENTER,
                                  textColor=colors.HexColor("#555555"))
S["poem_title"] = ParagraphStyle("poem_title", fontName="Georgia", fontSize=14.5, leading=19, spaceAfter=3)
S["lang"] = ParagraphStyle("lang", fontName="Georgia-Italic", fontSize=8.5, leading=11,
                           textColor=colors.HexColor("#777777"), spaceAfter=14)
S["line"] = ParagraphStyle("line", fontName="Georgia", fontSize=10.5, leading=15.5,
                           leftIndent=14, firstLineIndent=-14)
S["note"] = ParagraphStyle("note", fontName="Georgia-Italic", fontSize=8.5, leading=12,
                           textColor=colors.HexColor("#555555"), spaceBefore=10)
S["toc_h"] = ParagraphStyle("toc_h", fontName="Georgia", fontSize=16, leading=22, alignment=TA_CENTER, spaceAfter=14)
S["toc_sec"] = ParagraphStyle("toc_sec", fontName="Georgia-Italic", fontSize=10.5, leading=15, spaceBefore=8, spaceAfter=2)
S["toc0"] = ParagraphStyle("toc0", fontName="Georgia", fontSize=9.5, leading=13.5, leftIndent=10)
S["colophon"] = ParagraphStyle("colophon", fontName="Georgia", fontSize=9, leading=13.5, alignment=TA_CENTER,
                               textColor=colors.HexColor("#444444"))
S["front"] = ParagraphStyle("front", fontName="Georgia", fontSize=10.5, leading=16)

NBSP = " "
def poem_line(text):
    """Preserve leading spaces (author's indentation) and wrap long lines with hanging indent."""
    stripped = text.lstrip(" \t")
    lead = len(text) - len(stripped)
    lead = text[:lead].replace("\t", "        ").count(" ")
    return Paragraph(NBSP * lead + escape(stripped), S["line"])

def poem_flow(p, first_title_style=None):
    out = []
    out.append(Paragraph(escape(p["title"]), S["poem_title"]))
    out.append(Paragraph(p["_langline"], S["lang"]))
    stanza = []
    body = p["body"]
    for line in body + [""]:
        if not line.strip():
            if stanza:
                out.append(KeepTogether(stanza) if len(stanza) <= 14 else stanza)
                out.append(Spacer(1, 10))
                stanza = []
            continue
        m = re.fullmatch(r"\*(.+)\*", line.strip())
        if m:
            stanza.append(Paragraph(escape(m.group(1)), S["note"]))
        else:
            stanza.append(poem_line(line))
    # flatten
    flat = []
    for f in out:
        if isinstance(f, list):
            flat.extend(f)
        else:
            flat.append(f)
    return flat

# ---------- document ----------
class Book(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=PAGE, **kw)
        w, h = PAGE
        fw, fh = w - M_IN - M_OUT, h - M_TOP - M_BOT
        odd = Frame(M_IN, M_BOT, fw, fh, id="odd", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        even = Frame(M_OUT, M_BOT, fw, fh, id="even", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="plain", frames=[odd], onPage=self._plain),
            PageTemplate(id="body", frames=[odd], onPage=self._numbered),
        ])
        self._toc_ready = False
    def _plain(self, canv, doc): pass
    def _numbered(self, canv, doc):
        canv.saveState()
        canv.setFont("Georgia", 8.5)
        canv.setFillColor(colors.HexColor("#666666"))
        canv.drawCentredString(PAGE[0] / 2, 0.45 * inch, str(doc.page))
        canv.setFont("Georgia-Italic", 8)
        canv.drawCentredString(PAGE[0] / 2, PAGE[1] - 0.5 * inch, "Олег Штереб · Ноти життя: до і після")
        canv.restoreState()
    def afterFlowable(self, fl):
        if hasattr(fl, "_toc"):
            level, text = fl._toc
            self.notify("TOCEntry", (level, text, self.page))

LANG_ORDER = ["uk", "ru", "en", "es"]
TITLE = {"uk": "Ноти життя: до і після", "ru": "Ноты жизни: до и после",
         "en": "Notes of Life: Before and After", "es": "Notas de la vida: antes y después"}
SECTION_T = {"Любов як захоплення": {"ru": "Любовь как увлечение", "en": "Love as Infatuation", "es": "El amor como fascinación"},
             "Любов як драма": {"ru": "Любовь как драма", "en": "Love as Drama", "es": "El amor como drama"},
             "Любов як істина": {"ru": "Любовь как истина", "en": "Love as Truth", "es": "El amor como verdad"},
             "Після": {"ru": "После", "en": "After", "es": "Después"}}
ORIG_LINE = {"uk": "Оригінал · українська", "ru": "Оригинал · русский", "en": "Original · English"}
TR_LINE = {"uk": "Переклад українською", "ru": "Перевод на русский", "en": "English translation", "es": "Traducción al español"}

def label(p):
    if p["title"] == "* * *":
        first = next(l.strip() for l in p["body"] if l.strip())
        return "* * *  " + first.rstrip(",;:.—–- ")
    return p["title"]

def build(out_path, texts):
    """texts: dict lang -> list of 80 parsed poems; texts['orig'] = originals (with sections)."""
    originals = texts["orig"]
    for l in LANG_ORDER:
        assert len(texts[l]) == 82, (l, len(texts[l]))
    doc = Book(out_path, title="Ноти життя: до і після — Notes of Life: Before and After", author="Oleg Shtereb",
               subject="First collection, four languages: Ukrainian, Russian, English, Spanish")
    st = []
    # first page inside: the epigraph
    st.append(Spacer(1, 3.4 * inch))
    st.append(Paragraph("Art Knows No Languages", ParagraphStyle("epi", parent=S["title"], fontSize=20, leading=26)))
    st.append(Spacer(1, 10))
    st.append(Paragraph("— Oleg Shtereb", S["subtitle"]))
    st.append(PageBreak())
    # title page
    st.append(Spacer(1, 2.0 * inch))
    st.append(Paragraph("Олег Штереб · Oleg Shtereb", S["author"]))
    st.append(Spacer(1, 26))
    st.append(Paragraph("Ноти життя:<br/>до і після", S["title"]))
    st.append(Spacer(1, 16))
    st.append(Paragraph("Ноты жизни: до и после", S["subtitle"]))
    st.append(Paragraph("Notes of Life: Before and After", S["subtitle"]))
    st.append(Paragraph("Notas de la vida: antes y después", S["subtitle"]))
    st.append(Spacer(1, 26))
    st.append(Paragraph("Перша збірка · First collection", S["subtitle"]))
    st.append(Paragraph("Вірші I–LXXX · Після I–II", S["subtitle"]))
    st.append(Spacer(1, 2.0 * inch))
    st.append(Paragraph("schtereb.com", S["colophon"]))
    st.append(PageBreak())
    # note on the edition (four languages)
    st.append(Spacer(1, 0.6 * inch))
    st.append(Paragraph("Про це видання · Об этом издании<br/>About this edition · Sobre esta edición", S["section_sub"]))
    st.append(Spacer(1, 16))
    for para in [
        "Вірші цієї збірки написані українською та російською мовами і вперше опубліковані на сайті автора (shtereb.com, 2019). "
        "Тут вони подані в авторському порядку і без жодних змін — правопис, пунктуація, великі літери й окремі англійські слова збережені. "
        "Кожен вірш надруковано спочатку мовою оригіналу (позначено вгорі), а потім у перекладах: українською, російською, англійською, іспанською.",
        "Стихи этого сборника написаны на украинском и русском языках и впервые опубликованы на сайте автора (shtereb.com, 2019). "
        "Здесь они приведены в авторском порядке и без изменений. Каждое стихотворение напечатано сначала на языке оригинала, затем в переводах.",
        "The poems were written in Ukrainian and Russian and first first published on the author's website (shtereb.com, 2019). They appear here in their "
        "original order and exactly as the author wrote them; nothing has been corrected. Each poem is printed first in its original language, "
        "marked at the top, and then in the other three. The translations follow the originals line by line where the language allows, keep the "
        "stanza structure, images and register, and rhyme only where rhyme arrived on its own.",
        "Los poemas fueron escritos en ucraniano y ruso y publicados por primera vez en el sitio del autor (shtereb.com, 2019). Aparecen aquí en su orden "
        "original y tal como el autor los escribió. Cada poema se imprime primero en su lengua original y luego en las otras tres.",
    ]:
        st.append(Paragraph(para, ParagraphStyle("fr", parent=S["front"], fontSize=9.5, leading=14)))
        st.append(Spacer(1, 8))
    st.append(PageBreak())
    # contents
    st.append(Paragraph("Зміст · Contents", S["toc_h"]))
    toc = TableOfContents()
    toc.levelStyles = [S["toc0"], S["toc_sec"]]
    toc.dotsMinLevel = 0
    st.append(toc)
    st.append(NextPageTemplate("body"))
    st.append(PageBreak())

    cur_section = None
    for i in range(len(originals)):
        o = originals[i]
        if o["section"] != cur_section:
            cur_section = o["section"]
            t = SECTION_T[cur_section]
            st.append(Spacer(1, 2.8 * inch))
            h = Paragraph(escape(cur_section), S["section"])
            h._toc = (1, f"{cur_section} · {t['en']}")
            st.append(h)
            st.append(Spacer(1, 8))
            st.append(Paragraph(f"{escape(t['ru'])}<br/>{escape(t['en'])}<br/>{escape(t['es'])}", S["section_sub"]))
            st.append(PageBreak())
        o["_langline"] = ORIG_LINE[o["lang"]]
        flow = poem_flow(o)
        en_label = label(texts["en"][i]).replace("* * *  ", "")
        flow[0]._toc = (0, f"{label(o)}  —  {en_label}")
        st.extend(flow)
        st.append(PageBreak())
        for l in LANG_ORDER:
            if l == o["lang"]:
                continue
            p = texts[l][i]
            p["_langline"] = f"{TR_LINE[l]} · {escape(o['title'])}"
            st.extend(poem_flow(p))
            st.append(PageBreak())

    st.append(NextPageTemplate("plain"))
    st.append(Spacer(1, 3.3 * inch))
    for line in ["© Олег Штереб · Oleg Shtereb", "Усі вірші та переклади · All poems and translations.",
                 "Оригінали вперше опубліковано на shtereb.com (2019); нове видання — schtereb.com.",
                 "Переклади українською, російською, англійською та іспанською — 2026.",
                 "Set in Georgia · 6 × 9 in"]:
        st.append(Paragraph(line, S["colophon"]))
    doc.multiBuild(st)

if __name__ == "__main__":
    texts = {"orig": parse(os.path.join(ROOT, "content", "originals.md"))}
    for l in LANG_ORDER:
        texts[l] = parse(os.path.join(ROOT, "content", f"{l}.md"))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "Oleg-Shtereb-Noty-Zhyttia-4-languages.pdf")
    build(out, texts)
    from pypdf import PdfReader
    print(out, len(PdfReader(out).pages), "pages")
