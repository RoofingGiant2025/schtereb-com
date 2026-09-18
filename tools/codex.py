#!/usr/bin/env python3
"""Codex cuts: the author's manuscript sheets and drawings as ink on the book's own paper.

tools/manuscripts.py turns the archive photos into flat, colour-graded sheets (docs/assets/ms|art/*-x.jpg).
This tool lifts the INK off those sheets — the paper, the table, the neighbouring sheets, the fingers all go
white — and cuts the writing into fragments with torn, feathered edges. Rendered with mix-blend-mode:multiply
the fragments sit on the leaf as if written there (white = the leaf itself), the way a study sits on a page
of a Leonardo notebook.

Per manuscript:  <n>[-p].jpg   the main cut (title + opening stanzas, or the whole sheet)
                 <n>[-p]-d.jpg the detail: the signature / date cluster at the foot of the sheet (when found)
Per art plate:   <key>.jpg     the drawing, flattened and cut out
Settings live in content/manuscripts.json ("codex": {...} per page / art entry):
  cut      [y0, y1]       fraction of the INK box to keep vertically for the main cut (default whole)
  detail   [x0,y0,x1,y1]  fraction of the ink box — overrides the automatic signature/date detection; false = none
  mode     ink | colour | paint   ballpoint/pencil → sepia ink; coloured drawing → its own colours on white;
                                  paint → the picture is kept as a wash (gouache), only the edge is cut
  tone     sepia | graphite | sanguine   ink colour for mode=ink (default sepia)
  texture  0–1            how much of the paper's grain/folds/ruling to keep under the ink (default .22 / 0 for art)
  lo, hi                  ink thresholds on the flattened sheet (defaults .08 / .42)
Output: docs/assets/codex/*.jpg + docs/assets/codex/manifest.json (merged into poems.json by build_site.py).
Usage: python3 tools/codex.py [--debug] [keys…]
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAN = os.path.join(ROOT, "content", "manuscripts.json")
MS, ART = os.path.join(ROOT, "docs", "assets", "ms"), os.path.join(ROOT, "docs", "assets", "art")
OUT = os.path.join(ROOT, "docs", "assets", "codex")
DEBUG = os.path.join(ROOT, "archive", "codex-debug")
MAIN_PX, DETAIL_PX, ART_PX = 1500, 900, 1500
TONES = {"sepia": (106, 70, 44), "graphite": (66, 60, 56), "sanguine": (150, 66, 42), "ballpoint": (46, 48, 84)}


def load(path):
    im = Image.open(path).convert("RGB")
    return np.asarray(im).astype(np.float32) / 255.0


def paper_estimate(gray, sigma):
    """The paper tone under the ink: masked, iterated Gaussian estimate (ink and dark edges excluded).
    Computed at 1/6 scale — the paper tone is smooth — then resized back."""
    h, w = gray.shape; s = 6
    g = cv2.resize(gray, (max(8, w // s), max(8, h // s)), interpolation=cv2.INTER_AREA)
    sg = max(2.0, sigma / s)
    k = int(sg) | 1
    bg = cv2.morphologyEx(g, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, k // 2) | 1,) * 2))
    bg = cv2.GaussianBlur(bg, (0, 0), sg)
    for _ in range(3):
        mask = (g > bg * 0.86).astype(np.float32)
        num = cv2.GaussianBlur(g * mask, (0, 0), sg); den = cv2.GaussianBlur(mask, (0, 0), sg)
        bg = np.where(den > 0.02, num / np.maximum(den, 1e-3), bg)
    return np.maximum(cv2.resize(bg, (w, h), interpolation=cv2.INTER_CUBIC), 0.05)


def flatten(rgb, sigma):
    """rgb / paper → paper becomes 1.0 (white), strokes keep their darkness and hue."""
    gray = rgb.mean(2)
    bg = paper_estimate(gray, sigma)
    flat = np.empty_like(rgb)
    for c in range(3):
        bgc = paper_estimate(rgb[..., c], sigma)
        flat[..., c] = np.clip(rgb[..., c] / bgc, 0, 1.15)
    return flat, np.clip(gray / bg, 0, 1.15)


def paper_region(rgb, mode):
    """Soft mask of the sheet itself: the bright connected area around the centre, holes (ink, drawings) filled,
    shrunk a little so the sheet's own edge and the shadows beside it are left out. Everything outside is not paper."""
    h, w = rgb.shape[:2]; s = 4
    small = cv2.resize(rgb, (w // s, h // s), interpolation=cv2.INTER_AREA)
    v = small.max(2); sat = (small.max(2) - small.min(2)) / np.maximum(small.max(2), 1e-3)
    paper = np.percentile(v, 75)
    bright = ((v > paper * (0.5 if mode == "paint" else 0.62)) & (sat < (0.75 if mode != "ink" else 0.55))).astype(np.uint8)
    k = max(3, int(0.02 * max(bright.shape))) | 1
    bright = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(bright)
    if n < 2: return np.ones((h, w), np.float32)
    cy, cx = bright.shape[0] // 2, bright.shape[1] // 2
    idx = lab[cy, cx]
    if idx == 0:   # centre on ink: the biggest component
        idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    comp = (lab == idx).astype(np.uint8)
    # fill holes: flood the background from the border, what is not reached is inside the sheet
    ff = comp.copy(); pad = np.pad(ff, 1); mask = np.zeros((pad.shape[0] + 2, pad.shape[1] + 2), np.uint8)
    cv2.floodFill(pad, mask, (0, 0), 2)
    comp = ((pad[1:-1, 1:-1] != 2)).astype(np.uint8)
    e = max(3, int(0.02 * max(comp.shape))) | 1
    comp = cv2.erode(comp, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (e, e)))
    soft = cv2.GaussianBlur(comp.astype(np.float32), (0, 0), max(1.0, 0.004 * max(comp.shape)))
    return cv2.resize(soft, (w, h), interpolation=cv2.INTER_LINEAR)


def ink_alpha(flat, lo, hi):
    """0 = paper, 1 = full ink. Uses the darkest channel so coloured pencil counts as ink too."""
    dev = 1.0 - flat.min(2)
    a = np.clip((dev - lo) / max(hi - lo, 1e-3), 0, 1)
    return a ** 0.85


def remove_blobs(a, strokes_only, size):
    """Shadows and table left inside the region: thick dark patches. A stroke of the pen is a few pixels wide —
    anything that survives an opening with a kernel wider than a stroke is a patch. Manuscripts drop every patch;
    drawings (which have solid dark areas of their own) only the patches touching the border."""
    k = max(5, int(0.011 * size)) | 1
    thick = cv2.morphologyEx((a > 0.15).astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(thick)
    if n < 2: return a
    h, w = a.shape; drop = np.zeros(n, bool)
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        border = x <= 2 or y <= 2 or x + bw >= w - 2 or y + bh >= h - 2
        if strokes_only or border or area > 0.02 * a.size: drop[i] = True
    if not drop.any(): return a
    kill = drop[lab].astype(np.uint8)
    kill = cv2.dilate(kill, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k * 2 + 1, k * 2 + 1)))
    soft = cv2.GaussianBlur(kill.astype(np.float32), (0, 0), k * 0.6)
    return a * (1.0 - np.clip(soft * 1.5, 0, 1))


def clean_mask(a, min_frac=1.2e-5):
    """Binary ink mask without dust: drop components smaller than min_frac of the image."""
    b = (a > 0.35).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(b)
    keep = np.zeros(n, bool); keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_frac * a.size
    return keep[lab]


def ink_box(mask, pad=0.025):
    ys, xs = np.where(mask)
    if len(ys) < 50: return 0, 0, mask.shape[1], mask.shape[0]
    h, w = mask.shape
    # robust: ignore the outermost 0.3 % of ink pixels on each side (stray marks, fold edges)
    y0, y1 = np.percentile(ys, [0.05, 99.95]); x0, x1 = np.percentile(xs, [0.05, 99.95])
    py, px = pad * h, pad * w
    return int(max(0, x0 - px)), int(max(0, y0 - py)), int(min(w, x1 + px)), int(min(h, y1 + py))


def torn_edge(h, w, feather, amp, seed):
    """Soft mask: 1 inside, fading to 0 at an irregular, torn boundary."""
    rng = np.random.default_rng(seed); s = 4
    small = rng.standard_normal((max(4, h // s), max(4, w // s))).astype(np.float32)
    noise = cv2.GaussianBlur(small, (0, 0), max(2.0, 0.035 * max(h, w) / s))
    noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_CUBIC)
    noise = noise / (np.abs(noise).max() + 1e-6)
    inner = np.zeros((h, w), np.uint8); m = max(2, int(feather * 0.35))
    inner[m:h - m, m:w - m] = 1
    dist = cv2.distanceTransform(inner, cv2.DIST_L2, 5)
    d = dist + noise * amp - feather * 0.5
    return np.clip(d / max(feather, 1), 0, 1) ** 1.6


def compose(flat, a, norm, mode, tone, texture, seed, feather_frac=0.045, amp_frac=0.03, gamma=1.0):
    """The fragment on white: ink (tinted or in its own colours), a trace of the paper's grain, torn edges."""
    b = int((feather_frac + amp_frac + 0.015) * max(a.shape))     # white margin: the fade happens beside the ink, not over it
    flat = np.pad(flat, ((b, b), (b, b), (0, 0)), constant_values=1.0)
    a = np.pad(a, b, constant_values=0.0); norm = np.pad(norm, b, constant_values=1.0)
    h, w = a.shape
    white = np.ones_like(flat)
    if mode == "paint":
        body = np.clip(flat * 0.96, 0, 1)
    else:
        if mode == "ink":
            col = np.array(TONES[tone], np.float32) / 255.0
            # keep the stroke's own darkness: heavier ink is darker
            dark = np.clip(1.0 - flat.mean(2), 0, 1)[..., None]
            inkcol = col * (1.0 - 0.42 * dark)
            body = white * (1 - a[..., None]) + inkcol * a[..., None]
        else:   # colour: the flattened stroke colours, slightly warmed and deepened (gamma > 1 = deeper)
            c = np.clip(flat, 0, 1) ** gamma
            warm = c * np.array([1.0, 0.96, 0.9], np.float32)
            body = white * (1 - a[..., None]) + np.clip(warm, 0, 1) * a[..., None]
        if texture > 0:
            grain = np.clip(norm, 0, 1)
            tex = 1.0 - texture * (1.0 - grain)
            tex = np.clip(cv2.GaussianBlur(tex, (0, 0), 1.2), 0, 1)
            body = body * tex[..., None]
    edge = torn_edge(h, w, feather_frac * max(h, w), amp_frac * max(h, w), seed)[..., None]
    out = white * (1 - edge) + body * edge
    return np.clip(out * 255, 0, 255).astype(np.uint8)


def find_detail(mask, box):
    """The signature / date cluster: the last group of ink rows in the lower part of the ink box, and its columns."""
    x0, y0, x1, y1 = box
    sub = mask[y0:y1, x0:x1]; h, w = sub.shape
    rows = sub.sum(1) > max(2, 0.002 * w)
    groups, start = [], None
    for i, r in enumerate(list(rows) + [False]):
        if r and start is None: start = i
        elif not r and start is not None:
            if groups and i - groups[-1][1] < 0.012 * h: groups[-1][1] = i    # tiny gap: same block
            else: groups.append([start, i])
            start = None
    if not groups: return None
    gy0, gy1 = groups[-1]
    # merge a second short group right above it (name + date on two lines)
    if len(groups) > 1 and gy0 - groups[-2][1] < 0.05 * h and (groups[-2][1] - groups[-2][0]) < 0.08 * h:
        gy0 = groups[-2][0]
    if gy0 < 0.5 * h or (gy1 - gy0) > 0.3 * h: return None       # not a foot-of-sheet cluster
    cols = sub[gy0:gy1].sum(0) > 0
    xs = np.where(cols)[0]
    if len(xs) == 0: return None
    cx0, cx1 = xs[0], xs[-1]
    if sub[gy0:gy1, cx0:cx1].sum() < 0.0006 * mask.size: return None    # a smudge, not writing
    pad = 0.035 * max(h, w)
    return (int(max(0, x0 + cx0 - pad)), int(max(0, y0 + gy0 - pad)), int(min(mask.shape[1], x0 + cx1 + pad)), int(min(mask.shape[0], y0 + gy1 + pad)))


def save(arr, path, maxdim):
    im = Image.fromarray(arr); im.thumbnail((maxdim, maxdim), Image.LANCZOS)
    im.save(path, "JPEG", quality=82, optimize=True, progressive=True)
    return im.size


class Sheet:
    """A flattened sheet: ink alpha, paper grain, the ink box."""
    def __init__(self, src, cfg, is_art):
        self.rgb = load(src); self.h, self.w = self.rgb.shape[:2]
        self.mode = cfg.get("mode", "colour" if is_art else "ink")
        self.flat, self.norm = flatten(self.rgb, 0.05 * max(self.h, self.w))
        region = paper_region(self.rgb, self.mode) if cfg.get("region", True) else np.ones((self.h, self.w), np.float32)
        self.flat = self.flat * region[..., None] + (1.0 - region[..., None])      # outside the sheet: white
        self.norm = self.norm * region + (1.0 - region)
        lo = cfg.get("lo", {"ink": 0.16, "colour": 0.1, "paint": 0.04}[self.mode]); hi = cfg.get("hi", 0.5 if self.mode == "ink" else 0.42)
        self.a = ink_alpha(self.flat, lo, hi)
        if self.mode != "paint" and cfg.get("deblob", True):
            self.a = remove_blobs(self.a, strokes_only=not is_art, size=max(self.h, self.w))
            gone = (self.a < 0.02)[..., None]
            self.flat = np.where(gone, np.maximum(self.flat, 0.55), self.flat)   # the patch must not darken the grain either
        self.mask = clean_mask(self.a) if self.mode != "paint" else clean_mask(1.0 - self.flat.min(2) - 0.05, 1e-4)
        self.box = ink_box(self.mask, pad=cfg.get("pad", 0.09))
        if "box" in cfg:                       # explicit crop, fraction of the sheet
            bx = cfg["box"]; self.box = (int(bx[0] * self.w), int(bx[1] * self.h), int(bx[2] * self.w), int(bx[3] * self.h))
        self.texture = cfg.get("texture", 0.0 if is_art else 0.12)
        self.tone = cfg.get("tone", "sepia"); self.gamma = cfg.get("gamma", 1.0)

    def cut(self, x0, y0, x1, y1, seed, **kw):
        return compose(self.flat[y0:y1, x0:x1], self.a[y0:y1, x0:x1], self.norm[y0:y1, x0:x1], self.mode, self.tone, self.texture, seed, gamma=self.gamma, **kw)


def rel(path): return os.path.relpath(path, os.path.join(ROOT, "docs"))


def debug_view(sheet, name, boxes):
    os.makedirs(DEBUG, exist_ok=True)
    vis = (np.clip(sheet.flat, 0, 1) * 255).astype(np.uint8).copy()
    for (bx, col) in boxes:
        if bx: cv2.rectangle(vis, (int(bx[0]), int(bx[1])), (int(bx[2]), int(bx[3])), col, 6)
    Image.fromarray(vis).resize((sheet.w // 3, sheet.h // 3)).save(os.path.join(DEBUG, name + ".jpg"), quality=70)


def process_poem(n, entry, debug):
    """Main cut from the first sheet (at most ~1.05:1 tall, so the hand stays legible on the leaf);
    the detail — signature / date — from the last sheet, when the main cut does not already show it."""
    cfg_all = entry.get("codex", {})
    sheets = []
    for i, pg in enumerate(entry["pages"]):
        name = f"{n}" + (f"-{i + 1}" if i else "")
        src = os.path.join(MS, name + "-x.jpg")
        if not os.path.exists(src): print("missing", src); return None
        cfg = dict(cfg_all); cfg.update(pg.get("codex", {}))
        sheets.append((name, Sheet(src, cfg, False), cfg))
    name, first, cfg = sheets[0]
    x0, y0, x1, y1 = first.box; bw, bh = x1 - x0, y1 - y0
    cy0, cy1 = cfg.get("cut", [0, min(1.0, cfg.get("max_aspect", 1.05) * bw / max(bh, 1))])
    my0, my1 = int(y0 + cy0 * bh), int(y0 + cy1 * bh)
    out = {}
    main = first.cut(x0, my0, x1, my1, seed=int(n) * 10)
    mw, mh = save(main, os.path.join(OUT, name + ".jpg"), MAIN_PX)
    out["main"] = {"src": rel(os.path.join(OUT, name + ".jpg")), "w": mw, "h": mh}
    lname, last, lcfg = sheets[-1]
    det = lcfg.get("detail", "auto"); dbox = None
    if det == "auto": dbox = find_detail(last.mask, last.box)
    elif det:
        lx0, ly0, lx1, ly1 = last.box
        dbox = (int(lx0 + det[0] * (lx1 - lx0)), int(ly0 + det[1] * (ly1 - ly0)), int(lx0 + det[2] * (lx1 - lx0)), int(ly0 + det[3] * (ly1 - ly0)))
    partial = cy1 < 0.999 or len(sheets) > 1
    if dbox is None and partial:            # no signature cluster found: the foot of the last sheet
        lx0, ly0, lx1, ly1 = last.box; dbox = (lx0, int(ly1 - 0.2 * (ly1 - ly0)), lx1, ly1)
    if dbox and (partial or det != "auto"):
        d = last.cut(*dbox, seed=int(n) * 10 + 7, feather_frac=0.07, amp_frac=0.045)
        dw, dh = save(d, os.path.join(OUT, name + "-d.jpg"), DETAIL_PX)
        out["detail"] = {"src": rel(os.path.join(OUT, name + "-d.jpg")), "w": dw, "h": dh, "page": len(sheets)}
    out["cut"] = [round(cy0, 3), round(cy1, 3)]
    if debug:
        debug_view(first, "p" + name, [(first.box, (0, 120, 255)), ((x0, my0, x1, my1), (0, 170, 0))] + ([(dbox, (220, 0, 0))] if len(sheets) == 1 else []))
        if len(sheets) > 1: debug_view(last, "p" + lname, [(last.box, (0, 120, 255)), (dbox, (220, 0, 0))])
    print(f"poem {n}: main {mw}x{mh} cut {out['cut']}" + (f", detail {out['detail']['w']}x{out['detail']['h']}" if "detail" in out else ""))
    return out


def process_art(key, entry, debug):
    src = os.path.join(ART, key + "-x.jpg")
    if not os.path.exists(src): print("missing", src); return None
    cfg = entry.get("codex", {})
    sh = Sheet(src, cfg, True)
    img = sh.cut(*sh.box, seed=sum(map(ord, key)))
    w, h = save(img, os.path.join(OUT, key + ".jpg"), ART_PX)
    if debug: debug_view(sh, "art-" + key, [(sh.box, (0, 120, 255))])
    print(f"art {key}: {w}x{h}")
    return {"src": rel(os.path.join(OUT, key + ".jpg")), "w": w, "h": h}


def main(argv):
    debug = "--debug" in argv; keys = [a for a in argv if not a.startswith("--")]
    man = json.load(open(MAN, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    mf_path = os.path.join(OUT, "manifest.json")
    manifest = json.load(open(mf_path)) if os.path.exists(mf_path) else {"poems": {}, "art": {}}
    for n, e in man["poems"].items():
        if keys and n not in keys: continue
        r = process_poem(n, e, debug)
        if r: manifest["poems"][n] = r
    for k, e in man["art"].items():
        if keys and k not in keys: continue
        if e.get("codex") is False: continue
        r = process_art(k, e, debug)
        if r: manifest["art"][k] = r
    json.dump(manifest, open(mf_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
