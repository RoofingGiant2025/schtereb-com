#!/usr/bin/env python3
"""Dust jacket for the Lulu linen-wrap hardcover (US Trade 6 × 9) — the site's cover made physical:
bordeaux cloth ground, gilt double-rule frame with corner ornaments, arched tipped-in plate, staff ornament, gold type.

One sheet: bleed | back flap | back | spine | front | front flap | bleed. Geometry is Lulu's own template for this
binding (print/spec.json → "hardcover"): 21 × 9.75 in, 0.25 in bleed, 6.25 × 9.25 in boards, spine from Lulu's hardcover
table, 3.25 in flaps (+0.125 in fold tolerance), 0.5 in safety, 0.25 in fold safety, barcode area bottom-right of the back
kept clear. The linen underneath is not printed — Lulu stamps its spine in foil; all the art lives on this jacket.
Colours mirror tools/book.css (--board / --foil). Writes print/jacket-6x9-hardcover.pdf and tools/img/jacket.jpg (web).
"""
import os, json, re, tempfile
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab import rl_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "tools", "fonts")
pdfmetrics.registerFont(TTFont("CG", os.path.join(F, "CormorantGaramond-Medium.ttf")))
pdfmetrics.registerFont(TTFont("CG-I", os.path.join(F, "CormorantGaramond-Italic.ttf")))
pdfmetrics.registerFont(TTFont("CG-SB", os.path.join(F, "CormorantGaramond-SemiBold.ttf")))
rl_config.canvas_basefontname = "CG"

spec = json.load(open(os.path.join(ROOT, "print", "spec.json")))
edition = json.load(open(os.path.join(ROOT, "print", "edition.json")))
HC, J = spec["hardcover"], spec["hardcover"]["jacket"]
BOARD_W, BOARD_H = HC["board_in"]
SPINE, BLEED, FLAP, TOL, SAFE = HC["spine_in"], J["bleed_in"], J["flap_in"], J["fold_tolerance_in"], J["safety_in"]
W, H = J["sheet_in"]
FOLD_L = BLEED + FLAP + TOL                 # back flap | back board
SPINE_L = FOLD_L + BOARD_W                  # back board | spine
SPINE_R = SPINE_L + SPINE                   # spine | front board
FOLD_R = SPINE_R + BOARD_W                  # front board | front flap
assert abs(FOLD_R + FLAP + TOL + BLEED - W) < 1e-6, "flap/board/spine arithmetic does not close the sheet"
Y0, Y1 = BLEED, H - BLEED                   # board bottom / top

BOARD, BOARD_HI, BOARD_LO = "#3f131b", "#561f27", "#250910"
FOIL, FOIL_HI, FOIL_LO = colors.HexColor("#d8b86c"), colors.HexColor("#f6e7b6"), colors.HexColor("#8d6b2e")
PAPER, MUTED = colors.HexColor("#f4ead6"), colors.HexColor("#d9c9ad")
PRICE = f"${edition['price_usd']:.2f}" if edition.get("price_usd") else ""
DPI = 300

def I(x): return x * inch
def hex_rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

# ---------- the cloth: bordeaux with a fine woven grain and a soft 165° light, rasterised at 300 dpi for the whole sheet
def cloth_image(path):
    import numpy as np
    from PIL import Image
    w, h = int(W * DPI), int(H * DPI)
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = (xx / w * 0.55 + (1 - yy / h) * 0.45)                           # 0 top-left → 1 bottom-right (165° on the site)
    hi, mid, lo = (np.array(hex_rgb(c), np.float32) for c in (BOARD_HI, BOARD, BOARD_LO))
    base = np.where(t[..., None] < 0.48, hi + (mid - hi) * (t[..., None] / 0.48), mid + (lo - mid) * ((t[..., None] - 0.48) / 0.52))
    # weave: independent horizontal and vertical thread noise, smoothed along the thread
    def threads(axis):
        n = rng.normal(0, 1, (h, w)).astype(np.float32)
        k = 9
        c = np.cumsum(n, axis=axis)
        sl = [slice(None)] * 2
        sl[axis] = slice(k, None); a = c[tuple(sl)]
        sl[axis] = slice(None, -k); b = c[tuple(sl)]
        s = (a - b) / k
        pad = [(0, 0), (0, 0)]; pad[axis] = (k, 0)
        return np.pad(s, pad, mode="edge")
    grain = threads(1) * 4.5 + threads(0) * 4.5 + rng.normal(0, 1.2, (h, w)).astype(np.float32)
    img = np.clip(base + grain[..., None], 0, 255).astype(np.uint8)
    Image.fromarray(img).save(path, "JPEG", quality=90, subsampling=0)
    return path

# ---------- tiny SVG-path subset (M, H, V, Z, c, relative cubic chains) → reportlab path, in a local unit box
def svg_path(c, d, scale, ox, oy, flip_y=True):
    p = c.beginPath()
    nums = re.findall(r"[-+]?\d*\.?\d+", d)
    cmds = re.findall(r"[MHVZchvzCL]", d)
    toks = re.findall(r"[MHVZchvzCL]|[-+]?\d*\.?\d+", d)
    x = y = 0.0
    def T(px, py): return ox + px * scale, oy + (-py if flip_y else py) * scale
    i = 0; cmd = None
    while i < len(toks):
        t = toks[i]
        if t in "MHVZchvzCL":
            cmd = t; i += 1
            if cmd in "Zz": p.close(); continue
        if cmd == "M": x, y = float(toks[i]), float(toks[i + 1]); i += 2; p.moveTo(*T(x, y))
        elif cmd == "H": x = float(toks[i]); i += 1; p.lineTo(*T(x, y))
        elif cmd == "V": y = float(toks[i]); i += 1; p.lineTo(*T(x, y))
        elif cmd == "h": x += float(toks[i]); i += 1; p.lineTo(*T(x, y))
        elif cmd == "v": y += float(toks[i]); i += 1; p.lineTo(*T(x, y))
        elif cmd == "L": x, y = float(toks[i]), float(toks[i + 1]); i += 2; p.lineTo(*T(x, y))
        elif cmd == "c":
            a = [float(v) for v in toks[i:i + 6]]; i += 6
            p.curveTo(*T(x + a[0], y + a[1]), *T(x + a[2], y + a[3]), *T(x + a[4], y + a[5])); x += a[4]; y += a[5]
        elif cmd == "C":
            a = [float(v) for v in toks[i:i + 6]]; i += 6
            p.curveTo(*T(a[0], a[1]), *T(a[2], a[3]), *T(a[4], a[5])); x, y = a[4], a[5]
        else: i += 1
    return p

def star4(c, cx, cy, r):
    """Four-pointed star (the frame's corner ornament): quadratic arcs through the centre, as cubics."""
    pts = [(cx, cy + r), (cx + r, cy), (cx, cy - r), (cx - r, cy)]
    p = c.beginPath(); p.moveTo(*pts[0])
    for k in range(4):
        x0, y0 = pts[k]; x1, y1 = pts[(k + 1) % 4]
        p.curveTo(x0 + 2 / 3 * (cx - x0), y0 + 2 / 3 * (cy - y0), x1 + 2 / 3 * (cx - x1), y1 + 2 / 3 * (cy - y1), x1, y1)
    p.close(); return p

def gilt_frame(c, x0, y0, w, h, ornaments=True):
    """Double rule with diamond + star corners, drawn like the site's border-image (30-unit corners of a 90-unit tile)."""
    u = I(0.3375) / 30                       # 1.35em border at 0.25 in per em, 30 units per corner
    c.setStrokeColor(FOIL); c.setLineWidth(1.6 * u / 0.75)   # svg stroke 1.6 units → points
    c.rect(x0 + 6 * u, y0 + 6 * u, w - 12 * u, h - 12 * u, stroke=1, fill=0)
    c.setStrokeAlpha(0.55); c.setLineWidth(0.8 * u / 0.75)
    c.rect(x0 + 11 * u, y0 + 11 * u, w - 22 * u, h - 22 * u, stroke=1, fill=0); c.setStrokeAlpha(1)
    if not ornaments: return
    for cx, cy in ((x0 + 6 * u, y0 + 6 * u), (x0 + w - 6 * u, y0 + 6 * u), (x0 + 6 * u, y0 + h - 6 * u), (x0 + w - 6 * u, y0 + h - 6 * u)):
        c.setFillColor(FOIL); p = c.beginPath(); r = 3.8 * u
        p.moveTo(cx, cy + r); p.lineTo(cx + r, cy); p.lineTo(cx, cy - r); p.lineTo(cx - r, cy); p.close(); c.drawPath(p, stroke=0, fill=1)
    for cx, cy in ((x0 + 21 * u, y0 + 21 * u), (x0 + w - 21 * u, y0 + 21 * u), (x0 + 21 * u, y0 + h - 21 * u), (x0 + w - 21 * u, y0 + h - 21 * u)):
        c.setFillColor(colors.HexColor("#ecd48f")); c.drawPath(star4(c, cx, cy, 8.5 * u), stroke=0, fill=1)

STAFF_CLEF = "M22 26c0-7 5-12 8-18 1 8-2 14-2 20 0 3 2 5 4 5 3 0 5-3 5-6 0-5-4-8-7-8-4 0-8 4-8 9 0 6 5 10 11 10 8 0 13-7 13-15"
def staff(c, cx, cy, w):
    """The staff ornament from the site (96 × 36 units): five lines, treble clef, two notes."""
    s = w / 96; ox, oy = cx - w / 2, cy + 18 * s
    c.setStrokeColor(FOIL); c.setStrokeAlpha(0.55); c.setLineWidth(0.7 * s / 0.75 * 0.75)
    for yy in (8, 14, 20, 26, 32): c.line(ox + 4 * s, oy - yy * s, ox + 92 * s, oy - yy * s)
    c.setStrokeAlpha(0.92); c.setLineWidth(1.15 * s); c.setLineCap(1)
    c.drawPath(svg_path(c, STAFF_CLEF, s, ox, oy), stroke=1, fill=0)
    c.setFillColor(FOIL); c.setFillAlpha(0.92)
    for ex, ey, lx, ly0, ly1 in ((58, 24, 62, 24, 10), (74, 18, 78, 18, 6)):
        c.ellipse(ox + (ex - 4.2) * s, oy - (ey + 3) * s, ox + (ex + 4.2) * s, oy - (ey - 3) * s, stroke=0, fill=1)
        c.setLineWidth(1.1 * s); c.line(ox + lx * s, oy - ly0 * s, ox + lx * s, oy - ly1 * s)
    c.setFillAlpha(1); c.setStrokeAlpha(1); c.setLineCap(0)

def rule_orn(c, cx, cy, w):
    """The thin rule with a centre dot (site's orn.rule, 180 × 12 units)."""
    s = w / 180; ox = cx - w / 2
    c.setStrokeColor(FOIL); c.setStrokeAlpha(0.8); c.setLineWidth(0.7 * s); c.setLineCap(1)
    c.line(ox + 2 * s, cy, ox + 70 * s, cy); c.line(ox + 110 * s, cy, ox + 178 * s, cy)
    c.setStrokeAlpha(0.4); c.line(ox + 78 * s, cy, ox + 102 * s, cy)
    c.setFillColor(FOIL); c.setFillAlpha(0.8); c.circle(ox + 90 * s, cy, 1.6 * s, stroke=0, fill=1)
    c.setFillAlpha(1); c.setStrokeAlpha(1); c.setLineCap(0)

def tracked(c, x, y, s, font, size, col, tracking, align="c"):
    c.setFont(font, size); c.setFillColor(col)
    tw = pdfmetrics.stringWidth(s, font, size) + tracking * (len(s) - 1)
    xx = x - tw / 2 if align == "c" else (x if align == "l" else x - tw)
    for ch in s:
        c.drawString(xx, y, ch); xx += pdfmetrics.stringWidth(ch, font, size) + tracking

def build(out):
    c = Canvas(out, pagesize=(I(W), I(H)), initialFontName="CG")
    c.setTitle("Ноти життя: до і після — dust jacket"); c.setAuthor("Oleg Schtereb")
    cloth = os.path.join(ROOT, "print", f".cloth-{W}x{H}-{DPI}dpi.jpg")   # cached: the grain takes a while to generate
    if not os.path.exists(cloth): cloth_image(cloth)
    c.drawImage(cloth, 0, 0, I(W), I(H))
    # folds and the spine read a touch darker, like the site's joint shading
    for x, wdt in ((SPINE_L, SPINE), (FOLD_L - 0.05, 0.05), (FOLD_R, 0.05)):
        c.setFillColor(colors.black); c.setFillAlpha(0.18); c.rect(I(x), 0, I(wdt), I(H), stroke=0, fill=1)
    c.setFillAlpha(1)

    # ---------- front board
    fx0, fw = I(SPINE_R), I(BOARD_W); cx = fx0 + fw / 2
    inset = I(0.4375)
    gilt_frame(c, fx0 + inset, I(Y0) + inset, fw - 2 * inset, I(BOARD_H) - 2 * inset)
    tracked(c, cx, I(Y1 - 1.18), "ПЕРША ЗБІРКА", "CG", 11, FOIL, 4.2)
    # arched plate: painting clipped to a round-topped window, gilt frame like the tipped-in plate on the site
    pw, ph = I(2.75), I(3.5); px, py = cx - pw / 2, I(Y1 - 1.45) - ph; r = pw / 2
    def arch(dx):
        p = c.beginPath()
        p.moveTo(px - dx, py - dx); p.lineTo(px - dx, py + ph - r); p.arcTo(px - dx, py + ph - r - (r + dx), px + pw + dx, py + ph + dx, 180, -180)
        p.lineTo(px + pw + dx, py - dx); p.close(); return p
    c.saveState(); c.clipPath(arch(0), stroke=0)
    iw = pw; ih = iw * 1.5; c.drawImage(os.path.join(ROOT, "tools", "img", "cover-print.jpg"), px, py + ph - ih + (ih - ph) * 0.38, iw, ih)
    for i in range(20):   # a little inner shade at the foot of the plate
        c.setFillColor(colors.Color(0.08, 0.04, 0.03, alpha=0.03)); c.rect(px, py, pw, ph * 0.45 * (1 - i / 20), stroke=0, fill=1)
    c.restoreState()
    c.setStrokeColor(colors.Color(0, 0, 0, alpha=0.6)); c.setLineWidth(0.6); c.drawPath(arch(0.4), stroke=1, fill=0)
    c.setStrokeColor(FOIL); c.setLineWidth(I(0.04)); c.drawPath(arch(I(0.02) + 0.8), stroke=1, fill=0)
    c.setStrokeAlpha(0.45); c.setLineWidth(I(0.012)); c.drawPath(arch(I(0.075)), stroke=1, fill=0); c.setStrokeAlpha(1)
    staff(c, cx, py - I(0.4), I(1.55))
    c.setFont("CG-SB", 44); c.setFillColor(FOIL); c.drawCentredString(cx, I(Y0 + 2.9), "Ноти життя")
    c.setFont("CG-I", 24); c.drawCentredString(cx, I(Y0 + 2.44), "до і після")
    rule_orn(c, cx, I(Y0 + 2.17), I(2.25))
    c.setFont("CG-I", 19.5); c.drawCentredString(cx, I(Y0 + 1.76), "Олег Штереб")
    tracked(c, cx, I(Y0 + 1.4), "ВІРШІ I–LXXX · ПІСЛЯ I–II", "CG", 9.5, colors.Color(0.847, 0.722, 0.424, alpha=0.8), 2.6)
    tracked(c, cx, I(Y0 + 1.06), "Українська · Русский · English · Español", "CG", 9, colors.Color(0.847, 0.722, 0.424, alpha=0.6), 1.3)

    # ---------- spine: headband ticks, bands, title, author, monogram — everything 0.125 in clear of the spine edges
    sx = I(SPINE_L + SPINE / 2); sw = I(SPINE)
    for yb in (I(Y1 - 0.34), I(Y0 + 0.3)):
        for k in range(int(sw * 0.84 / 6)):
            xx = I(SPINE_L) + sw * 0.08 + k * 6
            c.setFillColor(FOIL); c.rect(xx, yb, 3, 4, stroke=0, fill=1)
            c.setFillColor(FOIL_HI); c.rect(xx + 5, yb, 1, 4, stroke=0, fill=1)
    c.setStrokeColor(FOIL); c.setLineWidth(1.2)
    for yb in (I(Y0 + SAFE + 0.05), I(Y1 - SAFE - 0.05)):
        c.line(sx - sw * 0.31, yb, sx + sw * 0.31, yb); c.setLineWidth(0.6); c.line(sx - sw * 0.31, yb - 3, sx + sw * 0.31, yb - 3); c.setLineWidth(1.2)
    c.saveState(); c.translate(sx, I(H / 2)); c.rotate(-90)
    c.setFillColor(FOIL); c.setFont("CG", 17); c.drawCentredString(I(0.5), -6, "Ноти життя: до і після")
    c.setFont("CG-I", 12); c.drawCentredString(-I(2.95), -4, "Олег Штереб")
    c.restoreState()
    c.setFont("CG-SB", 18); c.setFillColor(FOIL); c.drawCentredString(sx, I(Y0 + SAFE + 0.3), "Ш")

    # ---------- back board: the same frame, epigraph and two short paragraphs, clear of the barcode area (bottom right)
    bx0 = I(FOLD_L)
    gilt_frame(c, bx0 + inset, I(Y0) + inset, fw - 2 * inset, I(BOARD_H) - 2 * inset)
    st = ParagraphStyle("b", fontName="CG", fontSize=11, leading=16, textColor=PAPER)
    sti = ParagraphStyle("bi", parent=st, fontName="CG-I", fontSize=13.5, leading=19)
    stm = ParagraphStyle("bm", parent=st, fontSize=9, leading=13, textColor=MUTED)
    story = [
        Paragraph("Art Knows No Languages", ParagraphStyle("e", parent=sti, fontSize=19, leading=25, alignment=1, textColor=FOIL)),
        Paragraph("<br/>Вісімдесят віршів, написаних українською та російською, і два — англійською: "
                  "від першого захоплення й самотності юності до віри. Кожен вірш надруковано мовою "
                  "оригіналу й у віршованих перекладах — українською, російською, англійською та іспанською.", st),
        Paragraph("<br/>Eighty poems written in Ukrainian and Russian, and two in English — from first "
                  "infatuation and the loneliness of youth to faith. Each poem appears in its original "
                  "language and in verse translation: Ukrainian, Russian, English, Spanish.", st),
        Paragraph("<br/><br/>Олег Штереб · Oleg Schtereb", sti),
        Paragraph("Перша збірка · A first collection", stm),
        Paragraph("<br/>schtereb.com", ParagraphStyle("u", parent=stm, textColor=FOIL)),
    ]
    bxl, bwl = bx0 + I(SAFE + 0.45), fw - 2 * I(SAFE + 0.45)
    top = I(Y1 - SAFE - 0.7); bottom = I(Y0 + SAFE + J["barcode_in"][1] + 0.35)
    Frame(bxl, bottom, bwl, top - bottom, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0).addFromList(story, c)

    # ---------- flaps: Lulu's live area (0.5 in from the fold and from the trim)
    def flap(x_live, w_live, story, top_extra=0):
        Frame(x_live, I(Y0 + SAFE), w_live, I(Y1 - SAFE - top_extra) - I(Y0 + SAFE), leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0).addFromList(story, c)
    sf = ParagraphStyle("f", fontName="CG", fontSize=10, leading=14.5, textColor=PAPER)
    sfk = ParagraphStyle("fk", parent=sf, fontSize=8, leading=11, textColor=FOIL)
    sfm = ParagraphStyle("fm", parent=sf, fontSize=8.5, leading=12.5, textColor=MUTED)
    fw_live = I(J["flap_live_in"][0]); fx_live = I(FOLD_R + SAFE)
    if PRICE:
        c.setFont("CG", 9.5); c.setFillColor(MUTED); c.drawRightString(fx_live + fw_live, I(Y1 - SAFE - 0.12), PRICE)
    flap(fx_live, fw_live, [
        Paragraph("A FIRST COLLECTION · ПЕРША ЗБІРКА", sfk),
        Paragraph("<br/>Eighty poems written in Ukrainian and Russian between 2005 and 2019, and two written later "
                  "in English. They begin with a wanderer walking the earth, pass through first infatuation, the "
                  "loneliness and drunken Saturdays of youth and the drama of love, and arrive at faith.", sf),
        Paragraph("<br/>Each poem is printed in the language it was written in, followed by its verse translations — "
                  "Ukrainian, Russian, English and Spanish — so that a reader of any of the four holds the whole book.", sf),
        Paragraph("<br/>Вісімдесят віршів, написаних українською та російською у 2005–2019 роках, і два — "
                  "англійською, пізніше. Від мандрівника, що блукає світом, через перше захоплення, самотність "
                  "юності й драму любові — до віри. Кожен вірш надруковано мовою оригіналу, а за ним — у "
                  "віршованих перекладах українською, російською, англійською та іспанською.", sf),
        Paragraph("<br/><br/>First edition · Cloth-bound, spine stamped in gold, cream paper, printed to order.", sfm),
        Paragraph("Перше видання · Тканинна палітурка, золоте тиснення на корінці, кремовий папір, друк на замовлення.", sfm),
    ], top_extra=0.4)
    flap(I(BLEED + SAFE), fw_live, [
        Paragraph("ОЛЕГ ШТЕРЕБ · OLEG SHTEREB", sfk),
        Paragraph("<br/>Олег Штереб пише українською, російською та англійською. Вірші частини «До» він оприлюднив "
                  "на своєму сайті shtereb.com; «Після» — два вірші, написані вже англійською. «Ноти життя: до і після» — "
                  "його перша збірка.", sf),
        Paragraph("<br/>Oleg Schtereb writes in Ukrainian, Russian and English. The poems of Before first appeared on his "
                  "website, shtereb.com; After is two poems written later, in English. Notes of Life: Before and After "
                  "is his first collection.", sf),
        Paragraph("<br/><br/>schtereb.com", ParagraphStyle("u2", parent=sfk, fontSize=10, leading=14)),
        Paragraph("Книжку можна читати й слухати чотирма мовами.<br/>Read and listen to the book in four languages.", sfm),
    ])
    c.save()
    print(out, f"{W} x {H} in — flaps {FLAP}+{TOL} in, boards {BOARD_W} x {BOARD_H} in, spine {SPINE} in, pages {spec['pages']}, price {PRICE or '—'}")

def web_render(pdf, out_jpg, width=2000):
    """Rasterise the jacket for the website (macOS qlmanage + Pillow); silently skipped if unavailable."""
    import shutil, subprocess
    if not shutil.which("qlmanage"): return
    try:
        from PIL import Image
    except ImportError:
        return
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["qlmanage", "-t", "-s", str(width), "-o", d, pdf], capture_output=True)
        png = os.path.join(d, os.path.basename(pdf) + ".png")
        if not os.path.exists(png): return
        im = Image.open(png).convert("RGB")
        im.save(out_jpg, "JPEG", quality=82, optimize=True, progressive=True)
        print(out_jpg, im.size)

if __name__ == "__main__":
    pdf = os.path.join(ROOT, "print", "jacket-6x9-hardcover.pdf")
    build(pdf)
    web_render(pdf, os.path.join(ROOT, "tools", "img", "jacket.jpg"))
