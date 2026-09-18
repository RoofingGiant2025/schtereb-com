#!/usr/bin/env python3
"""Wraparound paperback cover for Lulu: bleed + back + spine + front + bleed. Reads print/spec.json for the page count."""
import os, json
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import rl_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "tools", "fonts")
pdfmetrics.registerFont(TTFont("CG", os.path.join(F, "CormorantGaramond-Medium.ttf")))
pdfmetrics.registerFont(TTFont("CG-I", os.path.join(F, "CormorantGaramond-Italic.ttf")))
pdfmetrics.registerFont(TTFont("CG-SB", os.path.join(F, "CormorantGaramond-SemiBold.ttf")))
rl_config.canvas_basefontname = "CG"

spec = json.load(open(os.path.join(ROOT, "print", "spec.json")))
TRIM_W, TRIM_H = spec["trim_in"][0] * inch, spec["trim_in"][1] * inch
SPINE = spec["spine_in"] * inch
BLEED = 0.125 * inch
W = BLEED + TRIM_W + SPINE + TRIM_W + BLEED
H = BLEED + TRIM_H + BLEED
ROOM, PAPER, GILT, MUTED = colors.HexColor("#12100e"), colors.HexColor("#f4ead6"), colors.HexColor("#c4b59a"), colors.HexColor("#b7aa98")

def build(out):
    c = Canvas(out, pagesize=(W, H), initialFontName="CG")
    c.setTitle("Ноти життя: до і після — cover"); c.setAuthor("Oleg Shtereb")
    # whole sheet: room colour (covers back, spine, and all bleed)
    c.setFillColor(ROOM); c.rect(0, 0, W, H, stroke=0, fill=1)
    # ---- front panel: painting full-bleed, cropped to the panel + bleed
    fx0 = BLEED + TRIM_W + SPINE                     # left edge of front trim
    panel_w = TRIM_W + BLEED; panel_h = H
    img_w = panel_h * (1152 / 1728)                  # keep aspect; height fills the sheet
    c.saveState(); p = c.beginPath(); p.rect(fx0, 0, panel_w, panel_h); c.clipPath(p, stroke=0)
    c.drawImage(os.path.join(ROOT, "tools", "img", "cover-print.jpg"), fx0 - (img_w - panel_w) / 2, 0, img_w, panel_h)
    # bottom shade for legibility (stacked translucent bands)
    for i in range(40):
        c.setFillColor(colors.Color(0.043, 0.039, 0.035, alpha=0.028))
        c.rect(fx0, 0, panel_w, panel_h * 0.62 * (1 - i / 40), stroke=0, fill=1)
    c.restoreState()
    cx = fx0 + TRIM_W / 2
    def ctext(y, s, font, size, col=PAPER, tracking=0):
        c.setFont(font, size); c.setFillColor(col)
        if tracking:
            tw = pdfmetrics.stringWidth(s, font, size) + tracking * (len(s) - 1)
            x = cx - tw / 2
            for ch in s:
                c.drawString(x, y, ch); x += pdfmetrics.stringWidth(ch, font, size) + tracking
        else:
            c.drawCentredString(cx, y, s)
    base = BLEED + 1.05 * inch
    ctext(base + 3.05 * inch, "ПЕРША ЗБІРКА", "CG", 9, MUTED, tracking=3)
    ctext(base + 2.25 * inch, "Ноти життя", "CG", 46)
    ctext(base + 1.72 * inch, "до і після", "CG-I", 22)
    ctext(base + 1.28 * inch, "ВІРШІ I–LXXX · ПІСЛЯ I–II", "CG", 8.5, MUTED, tracking=2.4)
    ctext(base + 0.72 * inch, "Олег Штереб", "CG-I", 17)
    ctext(base + 0.22 * inch, "Ukrainian · Русский · English · Español", "CG", 8, MUTED, tracking=1.2)
    # ---- spine
    c.saveState(); c.translate(BLEED + TRIM_W + SPINE / 2, H / 2); c.rotate(-90)
    c.setFillColor(GILT); c.setFont("CG", 15); c.drawCentredString(0.35 * inch, -5, "Ноти життя: до і після")
    c.setFont("CG-I", 11); c.drawCentredString(-2.6 * inch, -4, "Олег Штереб")
    c.restoreState()
    # ---- back panel
    bx = BLEED + 0.55 * inch; bw = TRIM_W - 1.1 * inch
    from reportlab.platypus import Paragraph, Frame
    from reportlab.lib.styles import ParagraphStyle
    st = ParagraphStyle("b", fontName="CG", fontSize=11, leading=16, textColor=PAPER)
    sti = ParagraphStyle("bi", parent=st, fontName="CG-I", fontSize=13.5, leading=19)
    stm = ParagraphStyle("bm", parent=st, fontSize=9, leading=13, textColor=MUTED)
    story = [
        Paragraph("Art Knows No Languages", ParagraphStyle("e", parent=sti, fontSize=17, leading=22, alignment=1, textColor=GILT)),
        Paragraph("<br/>Вісімдесят віршів, написаних українською та російською, і два — англійською: "
                  "від першого захоплення й самотності юності до віри. Кожен вірш надруковано мовою "
                  "оригіналу й у віршованих перекладах — українською, російською, англійською та іспанською.", st),
        Paragraph("<br/>Eighty poems written in Ukrainian and Russian, and two in English — from first "
                  "infatuation and the loneliness of youth to faith. Each poem appears in its original "
                  "language and in verse translation: Ukrainian, Russian, English, Spanish.", st),
        Paragraph("<br/><br/>Олег Штереб · Oleg Shtereb", sti),
        Paragraph("Перша збірка · A first collection", stm),
        Paragraph("<br/>schtereb.com", ParagraphStyle("u", parent=stm, textColor=GILT)),
    ]
    Frame(bx, BLEED + 2.3 * inch, bw, TRIM_H - 3.0 * inch, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0).addFromList(story, c)
    # barcode area (Lulu places the ISBN barcode here): keep clear, bottom-right of the back panel
    # 2.5 x 1.5 in, 0.375 in from trim edges — no text, no art.
    c.save()
    print(out, f"{W/inch:.4f} x {H/inch:.4f} in  (spine {SPINE/inch:.4f} in, pages {spec['pages']})")

if __name__ == "__main__":
    build(os.path.join(ROOT, "print", "cover-6x9-paperback.pdf"))
