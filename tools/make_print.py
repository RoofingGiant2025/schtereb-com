#!/usr/bin/env python3
"""Print-ready interior for Lulu (US Trade 6x9, hardcover): mirrored margins with the gutter Lulu asks for at 400+ pages,
edition page + dedication, rectos where a book expects them, even page count, fonts embedded. Writes print/spec.json."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_pdf as M
from reportlab.pdfgen.canvas import Canvas
class _Canvas(Canvas):
    def __init__(self, *a, **k):
        k['initialFontName'] = k.get('initialFontName') or 'Georgia'   # page preamble uses embedded Georgia, not Helvetica
        super().__init__(*a, **k)
M.CANVAS_MAKER = _Canvas
M.PRINT_EDITION = True
from reportlab import rl_config
rl_config.canvas_basefontname = 'Georgia'   # showPage() resets the canvas font to this; keep it an embedded face
from reportlab.lib.pagesizes import inch
from reportlab.platypus import PageTemplate, Frame
from reportlab.lib import colors

INNER, OUTER, TOP, BOT = 1.0 * inch, 0.625 * inch, 0.8 * inch, 0.8 * inch   # Lulu: 400–600 pp → ≥1 in total inside margin

class PrintBook(M.Book):
    """Odd pages (recto): inner margin on the left. Even pages (verso): inner margin on the right."""
    def __init__(self, fn, **kw):
        M.BaseDocTemplate.__init__(self, fn, pagesize=M.PAGE, **kw)
        w, h = M.PAGE
        fw, fh = w - INNER - OUTER, h - TOP - BOT
        recto = Frame(INNER, BOT, fw, fh, id="recto", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        verso = Frame(OUTER, BOT, fw, fh, id="verso", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="plain", frames=[recto], onPage=self._plain),
            PageTemplate(id="body", frames=[recto], onPage=self._numbered),       # kept for NextPageTemplate("body") calls
            PageTemplate(id="recto", frames=[recto], onPage=self._numbered),
            PageTemplate(id="verso", frames=[verso], onPage=self._numbered),
        ])
        self._body_mode = False
    def handle_nextPageTemplate(self, pt):
        if pt == "body": self._body_mode = True
        if pt == "plain": self._body_mode = False
        M.BaseDocTemplate.handle_nextPageTemplate(self, pt)
    def handle_pageBegin(self):
        M.BaseDocTemplate.handle_pageBegin(self)
        if self._body_mode:
            nxt = "verso" if (self.page + 1) % 2 == 0 else "recto"
            self._handle_nextPageTemplate(nxt)
    def _numbered(self, canv, doc):
        canv.saveState()
        canv.setFont("Georgia", 8.5); canv.setFillColor(colors.HexColor("#555555"))
        x = OUTER + (M.PAGE[0] - INNER - OUTER) / 2 if doc.page % 2 == 0 else INNER + (M.PAGE[0] - INNER - OUTER) / 2
        canv.drawCentredString(x, 0.5 * inch, str(doc.page))
        canv.setFont("Georgia-Italic", 8)
        canv.drawCentredString(x, M.PAGE[1] - 0.5 * inch, "Олег Штереб · Ноти життя: до і після")
        canv.restoreState()

def main():
    texts = {"orig": M.parse(os.path.join(M.ROOT, "content", "originals.md"))}
    for l in M.LANG_ORDER: texts[l] = M.parse(os.path.join(M.ROOT, "content", f"{l}.md"))
    out = os.path.join(M.ROOT, "print", "interior-6x9.pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    M.Book = PrintBook
    M.build(out, texts)
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject
    r = PdfReader(out); n = len(r.pages)
    w = PdfWriter()
    for pg in r.pages:
        # reportlab lists its base-14 default font in every page's resources even when unused; drop it (printers want 100% embedded)
        fonts = pg["/Resources"].get_object().get("/Font", {}).get_object() if "/Resources" in pg else {}
        used = pg.get_contents().get_data().decode("latin1") if pg.get_contents() else ""
        for k in list(fonts.keys()):
            if "Helvetica" in str(fonts[k].get_object().get("/BaseFont")) and (k + " ") not in used:
                del fonts[NameObject(k)]
        w.add_page(pg)
    if n % 2:  # perfect binding wants an even count: add a final blank
        w.add_blank_page(width=M.PAGE[0], height=M.PAGE[1]); n += 1
    w.add_metadata({"/Title": "Ноти життя: до і після", "/Author": "Oleg Schtereb"})
    w.write(open(out, "wb"))
    import json
    spine_pb = round(n / 444 + 0.06, 4)                      # perfect bound: Lulu formula
    spine_hc = hardcover_spine(n)                            # case/linen wrap: Lulu table
    spec = {"pages": n, "trim_in": [6, 9], "spine_in": spine_pb, "paperback": {"spine_in": spine_pb},
            "hardcover": {"binding": "linen wrap + dust jacket", "spine_in": spine_hc, "board_in": [6.25, 9.25],
                          "pod_package_id": "0600X0900.BW.STD.LW.060UC444.M??",   # ?? = linen colour + foil colour codes chosen on Lulu
                          "jacket": {"sheet_in": [21.0, 9.75], "bleed_in": 0.25, "flap_in": 3.25, "fold_tolerance_in": 0.125,
                                     "flap_live_in": [2.25, 8.25], "cover_live_in": [5.125, 8.25], "safety_in": 0.5,
                                     "barcode_in": [3.625, 1.25]}}}
    print(f"{out}: {n} pages; paperback spine {spine_pb} in; hardcover spine {spine_hc} in (jacket sheet 21 × 9.75 in)")
    json.dump(spec, open(os.path.join(M.ROOT, "print", "spec.json"), "w"), indent=1, ensure_ascii=False)

def hardcover_spine(pages):
    """Lulu hardcover spine width (in) by page count — the guide's table, 444 ppi paper."""
    table = [(84, .25), (140, .5), (168, .625), (194, .688), (222, .75), (250, .813), (278, .875), (306, .938), (334, 1.0),
             (360, 1.063), (388, 1.125), (416, 1.188), (444, 1.25), (472, 1.313), (500, 1.375), (528, 1.438), (556, 1.5),
             (582, 1.563), (610, 1.625), (638, 1.688), (666, 1.75), (694, 1.813), (722, 1.875), (750, 1.938), (778, 2.0), (799, 2.063), (800, 2.125)]
    for hi, w in table:
        if pages <= hi: return w
    raise ValueError("over 800 pages")

if __name__ == "__main__":
    main()
