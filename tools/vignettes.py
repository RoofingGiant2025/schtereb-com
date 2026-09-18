#!/usr/bin/env python3
"""Small drawings from the author's archive as vignettes: docs/assets/art/v-<key>.jpg (+ -x zoom).

content/manuscripts.json "vignettes": {"<key>": {...}} — same keys as the art entries in manuscripts.py
(img, rotate, quad, pad, colour, gamma, title, note) plus:
  "to":    [[x,y]×4]  the true shape of "quad" (any units, e.g. pixels read off the rectified full sheet) — the
           close-up is mapped onto it, so camera perspective goes but the hand-drawn skew of a frame stays;
           without it the quad is straightened into a rectangle
  "mat":   true       paper outside the quad (stray text, stains) is replaced by clean paper of the same tone
  "level": degrees    rotate the result (clockwise) after the warp — to level a frame or a signature
  "poem":  n          the drawing faces the title plate of poem n (its blank verso); build_site/book.js use it
Usage: python3 tools/vignettes.py [--debug] [keys…]
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manuscripts import load, order, grade, save, MAN, OUT_ART, OUT_MS, DEBUG, LEAF, ZOOM, ROOT

def paper_fill(rgb, k=31, sigma=18):
    """The sheet without its ink: grey-dilate the strokes away, then smooth — used to matte outside the drawing."""
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    return cv2.GaussianBlur(cv2.dilate(rgb, ker), (0, 0), sigma)

def process(entry, out_base, dbg_name=None):
    rgb = load(entry["img"])
    rot = entry.get("rotate", 0)
    if rot: rgb = np.rot90(rgb, k={90: 3, 180: 2, 270: 1}[rot])
    h, w = rgb.shape[:2]
    src = order([[x * w, y * h] for x, y in entry["quad"]])
    if "to" in entry:
        dst = order(entry["to"]); dst -= dst.min(0)
        # keep the close-up's resolution: scale the true shape so its longest side matches the source's
        s = max(np.linalg.norm(src[1] - src[0]), np.linalg.norm(src[2] - src[1]), np.linalg.norm(src[3] - src[2]), np.linalg.norm(src[0] - src[3])) \
            / max(np.linalg.norm(dst[1] - dst[0]), np.linalg.norm(dst[2] - dst[1]), np.linalg.norm(dst[3] - dst[2]), np.linalg.norm(dst[0] - dst[3]))
        dst = dst * s
    else:
        tl, tr, br, bl = src
        W = max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)); H = max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr))
        dst = np.array([[0, 0], [W, 0], [W, H], [0, H]], np.float32)
    bw, bh = dst.max(0) - dst.min(0)
    pad = entry.get("pad", 0.04) * bw
    extra = pad * 3 + 0.15 * max(bw, bh)        # room for the levelling rotation, cropped away below
    off = np.array([extra, extra], np.float32)
    M = cv2.getPerspectiveTransform(src.astype(np.float32), (dst + off).astype(np.float32))
    CW, CH = int(bw + 2 * extra), int(bh + 2 * extra)
    out = cv2.warpPerspective(rgb, M, (CW, CH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    if entry.get("mat"):
        mask = np.zeros((CH, CW), np.uint8)
        cv2.fillPoly(mask, [(dst + off).astype(np.int32)], 255)
        mask = cv2.GaussianBlur(mask, (0, 0), 3).astype(np.float32)[..., None] / 255
        out = (out * mask + paper_fill(out) * (1 - mask)).astype(np.uint8)
    lvl = entry.get("level", 0)
    if lvl:
        R = cv2.getRotationMatrix2D((CW / 2, CH / 2), -lvl, 1.0)          # cv2 rotates counter-clockwise for +angle
        out = cv2.warpAffine(out, R, (CW, CH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    # final crop: the (levelled) quad's box plus the margin
    pts = (dst + off).reshape(-1, 1, 2).astype(np.float32)
    if lvl: pts = cv2.transform(pts, R)
    x0, y0 = pts.reshape(-1, 2).min(0) - pad; x1, y1 = pts.reshape(-1, 2).max(0) + pad
    x0, y0 = max(int(x0), 0), max(int(y0), 0); x1, y1 = min(int(x1), CW), min(int(y1), CH)
    out = out[y0:y1, x0:x1]
    if dbg_name:
        os.makedirs(DEBUG, exist_ok=True)
        d = rgb.copy(); cv2.polylines(d, [src.astype(np.int32)], True, (255, 0, 0), 8)
        for i, p in enumerate(src): cv2.putText(d, str(i), tuple(p.astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 6)
        Image.fromarray(d).resize((w // 3, h // 3)).save(os.path.join(DEBUG, dbg_name + ".jpg"), quality=70)
    out = grade(out, keep_colour=entry.get("colour", False), gamma=entry.get("gamma", 1.0))
    zw, zh = save(out, out_base + "-x.jpg", ZOOM)
    lw, lh = save(out, out_base + ".jpg", LEAF)
    return {"w": lw, "h": lh, "zw": zw, "zh": zh}

def main(argv):
    debug = "--debug" in argv; keys = [a for a in argv if not a.startswith("--")]
    man = json.load(open(MAN, encoding="utf-8"))
    os.makedirs(OUT_ART, exist_ok=True)
    mf_path = os.path.join(OUT_MS, "manifest.json")
    manifest = json.load(open(mf_path)) if os.path.exists(mf_path) else {"poems": {}, "art": {}}
    for k, e in man.get("vignettes", {}).items():
        if keys and k not in keys: continue
        base = os.path.join(OUT_ART, "v-" + k)
        info = process(e, base, "v-" + k if debug else None)
        info["src"] = os.path.relpath(base + ".jpg", os.path.join(ROOT, "docs"))
        info.update({x: e[x] for x in ("title", "note", "poem") if x in e})
        manifest["art"]["v-" + k] = info; print(f"vignette {k}: {info['w']}x{info['h']}")
    json.dump(manifest, open(mf_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main(sys.argv[1:])
