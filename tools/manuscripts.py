#!/usr/bin/env python3
"""Facsimile plates from the author's archive photos (archive/IMG_*.HEIC, iPhone shots of the manuscript sheets).

content/manuscripts.json maps poems and book plates to photos:
  {"poems": {"6": {"pages": [{"img": "4707"}], "date": "…", "medium": "…"}, …},
   "art":   {"frontispiece": {"img": "4588", "title": {...}}, …}}
Each page/art entry may carry "quad": [[x,y]×4] (normalised 0–1, top-left → clockwise) to override the automatic
sheet detection, "rotate": 0/90/180/270, and "pad": fraction of extra margin to keep around the sheet.

Output: docs/assets/ms/<n>[-<page>].jpg (1000px, the leaf) and docs/assets/ms/<n>[-<page>]-x.jpg (2000px, the zoom),
docs/assets/art/<key>.jpg (+ -x). Writes docs/assets/ms/manifest.json (sizes) for build_site.py.
Usage: python3 tools/manuscripts.py [--debug] [keys…]   (keys: poem numbers or art keys; default: everything)
"""
import os, sys, json, subprocess, tempfile
import numpy as np, cv2
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH = os.path.join(ROOT, "archive")
MAN = os.path.join(ROOT, "content", "manuscripts.json")
OUT_MS = os.path.join(ROOT, "docs", "assets", "ms")
OUT_ART = os.path.join(ROOT, "docs", "assets", "art")
DEBUG = os.path.join(ROOT, "archive", "debug")
LEAF, ZOOM = 1000, 2000
PAPER = np.array([244, 236, 220], dtype=np.float32)   # target tone of the sheet (BGR order below is handled)

def load(img):
    """HEIC → RGB numpy, orientation applied, long side ≤ 3000."""
    src = os.path.join(ARCH, f"IMG_{img}.HEIC")
    with tempfile.TemporaryDirectory() as d:
        tmp = os.path.join(d, "x.jpg")
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "96", "-Z", "3000", src, "--out", tmp],
                       check=True, capture_output=True)
        im = ImageOps.exif_transpose(Image.open(tmp)).convert("RGB")
    return np.array(im)

def detect_quad(rgb):
    """Corners of the brightest large sheet around the image centre (fallback: the whole frame)."""
    h, w = rgb.shape[:2]; s = 900 / max(h, w)
    small = cv2.resize(rgb, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    v = hsv[..., 2].astype(np.float32); sat = hsv[..., 1].astype(np.float32)
    # paper: bright and unsaturated; threshold relative to the picture's own bright end
    thr = np.percentile(v, 55)
    mask = ((v > max(thr, 120)) & (sat < 90)).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k, iterations=2)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(mask)
    if n < 2: return None
    cx, cy = mask.shape[1] / 2, mask.shape[0] / 2
    best, score = None, 0
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 0.08 * mask.size: continue
        inside = x <= cx <= x + bw and y <= cy <= y + bh
        sc = area * (2 if inside else 1)
        if sc > score: best, score = i, sc
    if best is None: return None
    comp = (lab == best).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    hull = cv2.convexHull(c)
    quad = None
    for eps in np.linspace(0.01, 0.12, 24):
        ap = cv2.approxPolyDP(hull, eps * cv2.arcLength(hull, True), True)
        if len(ap) == 4: quad = ap.reshape(4, 2).astype(np.float32); break
    if quad is None:
        quad = cv2.boxPoints(cv2.minAreaRect(hull)).astype(np.float32)
    return order(quad / s)

def order(pts):
    pts = np.array(pts, dtype=np.float32)
    s = pts.sum(1); d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], dtype=np.float32)

def warp(rgb, quad, pad=0.0):
    tl, tr, br, bl = quad
    if pad:
        c = quad.mean(0); quad = c + (quad - c) * (1 + pad); tl, tr, br, bl = quad
    W = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
    H = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
    M = cv2.getPerspectiveTransform(np.array([tl, tr, br, bl], np.float32), np.array([[0, 0], [W, 0], [W, H], [0, H]], np.float32))
    return cv2.warpPerspective(rgb, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def grade(rgb, keep_colour=False, gamma=1.0):
    """Neutralise the tungsten cast on the paper, lift the paper to a cream, keep the ink; gentle sharpen."""
    f = rgb.astype(np.float32)
    flat = f.reshape(-1, 3); lum = flat.mean(1)
    paper = flat[lum > np.percentile(lum, 70)].mean(0)          # the paper tone as photographed
    target = PAPER if not keep_colour else PAPER * 0.55 + paper * 0.45
    gain = target / np.maximum(paper, 1)
    f = f * gain
    lo = np.percentile(f, 0.5); f = (f - lo) * (255 / max(255 - lo, 1))   # a little more contrast into the ink
    if gamma != 1.0: f = 255 * (np.clip(f, 0, 255) / 255) ** gamma      # pencil: deepen the strokes, keep the paper white
    f = np.clip(f, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(f, (0, 0), 1.6)
    return cv2.addWeighted(f, 1.35, blur, -0.35, 0)

def save(rgb, path, maxdim):
    im = Image.fromarray(rgb); im.thumbnail((maxdim, maxdim), Image.LANCZOS)
    im.save(path, "JPEG", quality=84, optimize=True, progressive=True)
    return im.size

def process(entry, out_base, dbg_name=None):
    rgb = load(entry["img"])
    rot = entry.get("rotate", 0)
    if rot: rgb = np.rot90(rgb, k={90: 3, 180: 2, 270: 1}[rot])   # clockwise degrees
    h, w = rgb.shape[:2]
    if "quad" in entry: quad = order([[x * w, y * h] for x, y in entry["quad"]])
    else:
        quad = detect_quad(rgb)
        if quad is None: quad = order([[0, 0], [w, 0], [w, h], [0, h]])
    if dbg_name:
        os.makedirs(DEBUG, exist_ok=True)
        d = rgb.copy(); cv2.polylines(d, [quad.astype(np.int32)], True, (255, 0, 0), 12)
        for i, p in enumerate(quad): cv2.putText(d, str(i), tuple(p.astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 8)
        Image.fromarray(d).resize((w // 4, h // 4)).save(os.path.join(DEBUG, dbg_name + ".jpg"), quality=70)
    sheet = warp(rgb, quad, entry.get("pad", 0.012))
    sheet = grade(sheet, keep_colour=entry.get("colour", False), gamma=entry.get("gamma", 1.0))
    zw, zh = save(sheet, out_base + "-x.jpg", ZOOM)
    lw, lh = save(sheet, out_base + ".jpg", LEAF)
    return {"w": lw, "h": lh, "zw": zw, "zh": zh}

def main(argv):
    debug = "--debug" in argv; keys = [a for a in argv if not a.startswith("--")]
    man = json.load(open(MAN, encoding="utf-8"))
    os.makedirs(OUT_MS, exist_ok=True); os.makedirs(OUT_ART, exist_ok=True)
    mf_path = os.path.join(OUT_MS, "manifest.json")
    manifest = json.load(open(mf_path)) if os.path.exists(mf_path) else {"poems": {}, "art": {}}
    for n, e in man["poems"].items():
        if keys and n not in keys: continue
        pages = []
        for i, pg in enumerate(e["pages"]):
            base = os.path.join(OUT_MS, f"{n}" + (f"-{i + 1}" if i else ""))
            info = process(pg, base, f"p{n}-{i + 1}" if debug else None)
            info["src"] = os.path.relpath(base + ".jpg", os.path.join(ROOT, "docs")); pages.append(info)
            print(f"poem {n} p{i + 1}: {info['w']}x{info['h']}")
        manifest["poems"][n] = {"pages": pages, "date": e.get("date", ""), "medium": e.get("medium", {})}
    for k, e in man["art"].items():
        if keys and k not in keys: continue
        base = os.path.join(OUT_ART, k)
        info = process(e, base, f"art-{k}" if debug else None)
        info["src"] = os.path.relpath(base + ".jpg", os.path.join(ROOT, "docs"))
        info.update({x: e[x] for x in ("title", "note") if x in e})
        manifest["art"][k] = info; print(f"art {k}: {info['w']}x{info['h']}")
    json.dump(manifest, open(mf_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main(sys.argv[1:])
