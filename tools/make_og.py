#!/usr/bin/env python3
"""Social preview (1200x630) for schtereb.com, drawn in the style of the site's cover: bordeaux cloth board with a gilt
double-rule frame, the cover photo as an arched tipped-in plate, gold-foil type — and the title block beside it.
Writes tools/img/og.jpg (build_site.py copies it to docs/assets/img/). Pure PIL + numpy; rendered at 2x and downsampled."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "tools", "img"); FONTS = os.path.join(ROOT, "tools", "fonts")
S = 2                                   # supersample
W, H = 1200 * S, 630 * S
BOARD = (63, 19, 27); BOARD_HI = (86, 31, 39); BOARD_LO = (37, 9, 16)
FOIL = (216, 184, 108); FOIL_HI = (246, 231, 182); FOIL_LO = (141, 107, 46)
CREAM = (244, 234, 214); MUTED = (183, 170, 152)

def font(name, size): return ImageFont.truetype(os.path.join(FONTS, f"CormorantGaramond-{name}.ttf"), int(size))

def gradient(w, h, c0, c1, angle_deg=165):
    """Linear gradient between two colours at an angle (CSS convention: 180deg = top→bottom)."""
    a = np.deg2rad(angle_deg); dx, dy = np.sin(a), -np.cos(a)
    x, y = np.meshgrid(np.arange(w), np.arange(h)); t = (x * dx + y * dy); t = (t - t.min()) / (t.max() - t.min())
    arr = np.stack([c0[i] + (c1[i] - c0[i]) * t for i in range(3)], -1)
    return Image.fromarray(arr.astype(np.uint8))

def foil(w, h, angle_deg=100):
    """Gold-foil ramp: lo → foil → hi → foil → lo."""
    stops = [(0, FOIL_LO), (.22, FOIL), (.42, FOIL_HI), (.58, FOIL), (.8, FOIL_LO), (1, FOIL)]
    a = np.deg2rad(angle_deg); dx, dy = np.sin(a), -np.cos(a)
    x, y = np.meshgrid(np.arange(w), np.arange(h)); t = x * dx + y * dy; t = (t - t.min()) / (t.max() - t.min())
    out = np.zeros((h, w, 3))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1); u = ((t - t0) / (t1 - t0))[m]
        for i in range(3): out[..., i][m] = c0[i] + (c1[i] - c0[i]) * u
    return Image.fromarray(out.astype(np.uint8))

def cloth(w, h):
    """Bordeaux cloth: base gradient, two fibre layers (streaked noise) blended soft-light."""
    base = gradient(w, h, BOARD_HI, BOARD_LO, 165)
    rng = np.random.default_rng(7)
    def fibres(kx, ky):
        n = rng.random((max(2, h // ky), max(2, w // kx))) * .22 + .39     # low amplitude around mid-grey
        im = Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
        return Image.merge("RGB", (im, im, im))
    for f in (fibres(1, 14), fibres(14, 1)): base = ImageChops.soft_light(base, f)
    return base

def gold_text(canvas, xy, text, fnt, anchor="la", tracking=0, alpha=255, foil_angle=100):
    """Draw text filled with the foil ramp through a text mask."""
    x, y = xy
    if tracking:
        widths = [fnt.getlength(ch) for ch in text]; total = sum(widths) + tracking * (len(text) - 1)
        if anchor[0] == "m": x -= total / 2
        for ch, wch in zip(text, widths): gold_text(canvas, (x, y), ch, fnt, "l" + anchor[1], 0, alpha, foil_angle); x += wch + tracking
        return
    box = [int(v) for v in ImageDraw.Draw(canvas).textbbox((x, y), text, font=fnt, anchor=anchor)]
    if box[2] <= box[0] or box[3] <= box[1]: return
    pad = 4; bx0, by0, bx1, by1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    mask = Image.new("L", (bx1 - bx0, by1 - by0), 0)
    ImageDraw.Draw(mask).text((x - bx0, y - by0), text, font=fnt, fill=alpha, anchor=anchor)
    shadow = Image.new("L", mask.size, 0); shadow.paste(mask, (0, 1 * S))
    canvas.paste((0, 0, 0), (bx0, by0), shadow.point(lambda v: v * .55))
    canvas.paste(foil(mask.size[0], mask.size[1], foil_angle), (bx0, by0), mask)

def arch_mask(w, h):
    m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    d.ellipse((0, 0, w - 1, w - 1), fill=255); d.rectangle((0, w // 2, w - 1, h - 1), fill=255)
    return m

def arch_outline(d, x, y, w, h, width, fill):
    d.arc((x, y, x + w, y + w), 180, 360, fill=fill, width=width)
    d.line((x, y + w / 2, x, y + h), fill=fill, width=width); d.line((x + w, y + w / 2, x + w, y + h), fill=fill, width=width)
    d.line((x, y + h, x + w, y + h), fill=fill, width=width)

def board(bw, bh):
    """The front board, face on."""
    b = cloth(bw, bh); d = ImageDraw.Draw(b)
    # gilt frame with corner diamonds + stars
    m = int(bw * .06); t = int(bw * .055)
    o = m + int(t * 6 / 30); i = m + int(t * 11 / 30)
    d.rectangle((o, o, bw - o, bh - o), outline=FOIL, width=max(1, int(1.6 * S * bw / 416 / S)))
    d.rectangle((i, i, bw - i, bh - i), outline=tuple(int(c * .6 + BOARD[k] * .4) for k, c in enumerate(FOIL)), width=max(1, S // 2))
    r = int(t * 4 / 30)
    for cx, cy in ((o, o), (bw - o, o), (o, bh - o), (bw - o, bh - o)):
        d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=FOIL)
    sr = int(t * 8.5 / 30)
    for cx, cy in ((i + sr, i + sr), (bw - i - sr, i + sr), (i + sr, bh - i - sr), (bw - i - sr, bh - i - sr)):
        pts = []
        for k in range(4):
            import math
            a = k * math.pi / 2; pts.append((cx + sr * math.cos(a), cy + sr * math.sin(a)))
            a2 = a + math.pi / 4; pts.append((cx + sr * .28 * math.cos(a2), cy + sr * .28 * math.sin(a2)))
        d.polygon(pts, fill=(236, 212, 143))
    # arched plate with the cover photo
    em = bw * .04
    pw = int(em * 11); ph = int(em * 14.5); px = (bw - pw) // 2; py = int(em * 5.6)
    src = Image.open(os.path.join(IMG, "cover.jpg")).convert("RGB")
    sc = max(pw / src.width, ph / src.height); src = src.resize((int(src.width * sc) + 1, int(src.height * sc) + 1), Image.LANCZOS)
    cx0 = (src.width - pw) // 2; cy0 = int((src.height - ph) * .62); plate = src.crop((cx0, cy0, cx0 + pw, cy0 + ph))
    vign = Image.new("L", (pw, ph), 0); ImageDraw.Draw(vign).rectangle((0, 0, pw, ph), fill=0)
    dark = Image.new("RGB", (pw, ph), (20, 10, 8)); grad = np.linspace(0, .35, ph)[:, None].repeat(pw, 1)
    plate = Image.composite(dark, plate, Image.fromarray((grad[::-1] * 255).astype(np.uint8)))
    # bezel rings (drawn under the plate, spread outward like the CSS box-shadows)
    sh = Image.new("L", b.size, 0); ImageDraw.Draw(sh).rectangle((px - 6, py + 30, px + pw + 6, py + ph + 40), fill=200)
    sh = sh.filter(ImageFilter.GaussianBlur(18 * S / 2)); b.paste((0, 0, 0), (0, 0), sh.point(lambda v: v * .6))
    for spread, col in ((int(em * .32), (int(FOIL[0] * .5 + BOARD_LO[0] * .5), int(FOIL[1] * .5 + BOARD_LO[1] * .5), int(FOIL[2] * .5 + BOARD_LO[2] * .5))),
                        (int(em * .26), BOARD_LO), (int(em * .16), FOIL), (1 * S, (0, 0, 0))):
        ring = Image.new("L", (pw + 2 * spread, ph + 2 * spread), 0)
        ImageDraw.Draw(ring).rectangle((0, 0, ring.width, ring.height), fill=0)
        ring.paste(arch_mask(pw + 2 * spread, ph + 2 * spread), (0, 0)); b.paste(col, (px - spread, py - spread), ring)
    b.paste(plate, (px, py), arch_mask(pw, ph))
    # ornament rule, gilt type
    d = ImageDraw.Draw(b)
    ty = py + ph + int(em * 1.1)
    def rule(cy, half):
        d.line((bw / 2 - half, cy, bw / 2 - half * .18, cy), fill=FOIL, width=S); d.line((bw / 2 + half * .18, cy, bw / 2 + half, cy), fill=FOIL, width=S)
        d.ellipse((bw / 2 - 2 * S, cy - 2 * S, bw / 2 + 2 * S, cy + 2 * S), fill=FOIL)
    gold_text(b, (bw / 2, int(em * 3.6)), "ПЕРША ЗБІРКА", font("Medium", em * .66), "mm", tracking=int(em * .2))
    rule(ty, em * 3.5)
    gold_text(b, (bw / 2, ty + int(em * 1.9)), "Ноти життя", font("SemiBold", em * 2.5), "mm")
    gold_text(b, (bw / 2, ty + int(em * 3.6)), "до і після", font("Italic", em * 1.35), "mm")
    rule(ty + int(em * 4.6), em * 2.6)
    gold_text(b, (bw / 2, ty + int(em * 5.6)), "Олег Штереб", font("Italic", em * 1.1), "mm")
    gold_text(b, (bw / 2, ty + int(em * 6.7)), "ВІРШІ I–LXXX · ПІСЛЯ I–II", font("Medium", em * .6), "mm", tracking=int(em * .15), alpha=185)
    # hinge shade + bevel
    joint = gradient(int(bw * .1), bh, (0, 0, 0), (0, 0, 0), 90); jm = Image.fromarray((np.linspace(140, 0, int(bw * .1))[None, :].repeat(bh, 0)).astype(np.uint8))
    b.paste(joint, (0, 0), jm)
    ImageDraw.Draw(b).rectangle((0, 0, bw - 1, bh - 1), outline=(120, 70, 70), width=S // 2 or 1)
    return b

def main():
    im = Image.new("RGB", (W, H), (11, 10, 9))
    # room: warm radial glow
    x, y = np.meshgrid(np.arange(W), np.arange(H)); r = np.sqrt(((x - W * .36) / (W * .55)) ** 2 + ((y - H * .42) / (H * .75)) ** 2)
    g = np.clip(1 - r, 0, 1) ** 1.6
    room = np.stack([11 + (42 - 11) * g, 10 + (35 - 10) * g, 9 + (32 - 9) * g], -1); im = Image.fromarray(room.astype(np.uint8))
    # book: front board + spine strip + gilt fore-edge + floor shadow
    bh = int(H * .80); bw = int(bh * 2 / 3); bx = int(W * .09); by = (H - bh) // 2
    shadow = Image.new("L", im.size, 0); ImageDraw.Draw(shadow).ellipse((bx - bw * .12, by + bh * .93, bx + bw * 1.18, by + bh * 1.06), fill=230)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22 * S)); im.paste((0, 0, 0), (0, 0), shadow)
    edge = int(bw * .03); spine = int(bw * .025)
    im.paste(gradient(spine, bh, (30, 8, 12), (70, 24, 30), 90), (bx - spine, by))                     # spine sliver
    im.paste(foil(edge, bh, 90).resize((edge, bh)), (bx + bw, by + int(bh * .012)))                       # gilt fore-edge
    lines = Image.fromarray(((np.arange(edge) % 3 == 0)[None, :].repeat(bh, 0) * 90).astype(np.uint8))
    im.paste((90, 60, 20), (bx + bw, by + int(bh * .012)), lines)
    im.paste(board(bw, bh), (bx, by))
    # title block
    d = ImageDraw.Draw(im); tx = bx + bw + int(W * .07); cy = H // 2
    d.text((tx, cy - int(H * .19)), "Ноти життя", font=font("Medium", H * .155), fill=CREAM, anchor="ls")
    d.text((tx + int(W * .005), cy - int(H * .08)), "до і після", font=font("Italic", H * .085), fill=CREAM, anchor="ls")
    d.line((tx, cy - int(H * .03), tx + int(W * .1), cy - int(H * .03)), fill=FOIL, width=S)
    gold_text(im, (tx, cy + int(H * .06)), "Oleg Schtereb", font("Italic", H * .075), "ls")
    d.text((tx, cy + int(H * .15)), "Notes of Life: Before and After", font=font("Italic", H * .052), fill=MUTED, anchor="ls")
    d.text((tx, cy + int(H * .24)), "Українська · Русский · English · Español", font=font("Medium", H * .036), fill=(120, 108, 92), anchor="ls")
    small = font("Medium", H * .034); xx = tx
    for ch in "SCHTEREB.COM": d.text((xx, cy + int(H * .31)), ch, font=small, fill=FOIL, anchor="ls"); xx += small.getlength(ch) + int(H * .012)
    out = im.resize((W // S, H // S), Image.LANCZOS)
    out.save(os.path.join(IMG, "og.jpg"), quality=88, optimize=True, progressive=True)
    print("wrote tools/img/og.jpg", out.size)

if __name__ == "__main__": main()
