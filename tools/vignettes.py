#!/usr/bin/env python3
"""Small drawings from the author's archive as vignettes: docs/assets/art/v-<key>.jpg (+ -x zoom).

content/manuscripts.json "vignettes": {"<key>": {...}} — same keys as the art entries in manuscripts.py
(img, rotate, quad, pad, colour, gamma, title, note — "colour" may be a 0–1 share of the photographed cast to keep) plus:
  "to":    [[x,y]×4]  the true shape of "quad" (any units, e.g. pixels read off the rectified full sheet) — the
           close-up is mapped onto it, so camera perspective goes but the hand-drawn skew of a frame stays;
           without it the quad is straightened into a rectangle
  "mat":   true       stray ink outside the quad (text of the letter, neighbouring doodles) is inpainted away; the paper stays
  "level": degrees    rotate the result (clockwise) after the warp — to level a frame or a signature
  "sheet": "37"       the full sheet this drawing sits on (a poems entry of manuscripts.json): its rectified image
           supplies the paper around the quad when the close-up runs out of margin; "to" is then read in the
           pixel space of that sheet's -x.jpg (2000 px zoom), so corners can be read straight off docs/assets/ms
  "poem":  n          the drawing faces the title plate of poem n (its blank verso); build_site/book.js use it
Usage: python3 tools/vignettes.py [--debug] [keys…]
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manuscripts import load, order, save, warp, MAN, OUT_ART, OUT_MS, DEBUG, LEAF, ZOOM, ROOT

def clear_ink(rgb, inside, valid):
    """Keep the real paper (stains and all) around the drawing but lift the stray ink off it — text of the letter,
    marks of neighbouring doodles — by inpainting every dark or saturated stroke outside the quad."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    out_px = (inside < 0.5) & (valid > 0.5)
    if out_px.sum() < 500: return rgb
    v0 = np.median(hsv[..., 2][out_px]); s0 = np.median(hsv[..., 1][out_px])
    ink = ((hsv[..., 2] < v0 - 32) | (hsv[..., 1] > s0 + 45)) & (inside < 0.5)
    ink = cv2.dilate(ink.astype(np.uint8) * 255, np.ones((7, 7), np.uint8))
    return cv2.inpaint(rgb, ink, 6, cv2.INPAINT_TELEA)

def grade_v(rgb, keep=0.3, gamma=1.0):
    """manuscripts.grade with a dial on how much of the photographed paper cast survives (0 = cream, 1 = as shot)."""
    from manuscripts import PAPER
    f = rgb.astype(np.float32)
    flat = f.reshape(-1, 3); lum = flat.mean(1)
    paper = flat[lum > np.percentile(lum, 70)].mean(0)
    target = PAPER * (1 - keep) + paper * keep
    f = f * (target / np.maximum(paper, 1))
    lo = np.percentile(f, 0.5); f = (f - lo) * (255 / max(255 - lo, 1))
    if gamma != 1.0: f = 255 * (np.clip(f, 0, 255) / 255) ** gamma
    f = np.clip(f, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(f, (0, 0), 1.6)
    return cv2.addWeighted(f, 1.35, blur, -0.35, 0)

def process(entry, out_base, dbg_name=None, man=None):
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
    mask = np.zeros((CH, CW), np.uint8)
    cv2.fillPoly(mask, [(dst + off).astype(np.int32)], 255)
    mask = cv2.GaussianBlur(mask, (0, 0), 3).astype(np.float32)[..., None] / 255
    valid = cv2.warpPerspective(np.full((h, w), 255, np.uint8), M, (CW, CH), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    valid = cv2.erode(valid, np.ones((15, 15), np.uint8)).astype(np.float32) / 255
    if "sheet" in entry and man:
        # paper around the drawing from the rectified full sheet, the close-up tone-matched to it inside the quad
        pg = man["poems"][entry["sheet"]]["pages"][0]
        srgb = load(pg["img"]); srot = pg.get("rotate", 0)
        if srot: srgb = np.rot90(srgb, k={90: 3, 180: 2, 270: 1}[srot])
        sh, sw = srgb.shape[:2]
        sheet = warp(srgb, order([[x * sw, y * sh] for x, y in pg["quad"]]), pg.get("pad", 0.012))
        zs = ZOOM / max(sheet.shape[:2]); sheet = cv2.resize(sheet, None, fx=zs, fy=zs, interpolation=cv2.INTER_AREA)
        mn = order(entry["to"]).min(0)
        A = np.array([[s, 0, off[0] - s * mn[0]], [0, s, off[1] - s * mn[1]]], np.float32)
        base = cv2.warpAffine(sheet, A, (CW, CH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        ins = (mask[..., 0] > 0.5) & (valid > 0.5)
        def paper_tone(im):
            px = im[ins].reshape(-1, 3).astype(np.float32); lum = px.mean(1)
            return np.median(px[lum > np.percentile(lum, 70)], axis=0)
        out = np.clip(out.astype(np.float32) * (paper_tone(base) / np.maximum(paper_tone(out), 1)), 0, 255).astype(np.uint8)
        out = (out * mask + base * (1 - mask)).astype(np.uint8)
        valid = np.ones((CH, CW), np.float32)
    if entry.get("mat"):
        out = clear_ink(out, mask[..., 0], valid)
    lvl = entry.get("level", 0)
    if lvl:
        R = cv2.getRotationMatrix2D((CW / 2, CH / 2), -lvl, 1.0)          # "level" is clockwise; cv2 turns counter-clockwise for +angle
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
    keep = entry.get("colour", False); keep = 0.3 if keep is True else (keep or 0.0)
    out = grade_v(out, keep=keep, gamma=entry.get("gamma", 1.0))
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
        info = process(e, base, "v-" + k if debug else None, man)
        info["src"] = os.path.relpath(base + ".jpg", os.path.join(ROOT, "docs"))
        info.update({x: e[x] for x in ("title", "note", "poem") if x in e})
        manifest["art"]["v-" + k] = info; print(f"vignette {k}: {info['w']}x{info['h']}")
    json.dump(manifest, open(mf_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main(sys.argv[1:])
