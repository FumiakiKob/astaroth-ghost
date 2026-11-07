import sys, os, json
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

# メイド服シェル（第3シェル maid）後処理: 基本＋表情 12 面のキーイングと配置。
# キーイングは finalize_v224.py と同一方式（色距離ベース＋囲み領域除去＋デスピル強化）。
# 配置は基本面の一括正規化（place_group：中心・下端1211統一、v2.23/v2.24 の
# フルフル基本面と同方式）を両名とも採用し、表情間で顔位置を揃える。

GHOST = os.path.expanduser("~/workspace/astaroth-ghost")
CAND = os.path.join(GHOST, "work/maid_candidates/raw")
RAW = os.path.join(GHOST, "work/maid_raw")
OUTROOT = os.path.expanduser("~/workspace/astaroth-ghost/work/maid_out")

def key_image(path, mode):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    greenness = G - np.maximum(R, B)
    yel = np.minimum(R, G) - B
    corners = np.concatenate([
        a[:20, :20].reshape(-1, 3), a[:20, -20:].reshape(-1, 3),
        a[-20:, :20].reshape(-1, 3), a[-20:, -20:].reshape(-1, 3)])
    key = np.median(corners, axis=0)
    dist = np.sqrt(((a - key) ** 2).sum(axis=2))

    bg_like = (greenness >= 18) | (yel >= 60)
    lab, n = ndimage.label(bg_like)
    border_labels = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    border_labels.discard(0)
    bg = np.isin(lab, list(border_labels))
    alpha = (~bg).astype(np.float32) * 255.0

    if mode == "furfur":
        factor = np.clip((32.0 - greenness) / (32.0 - 22.0), 0.0, 1.0)
        alpha = alpha * np.where(greenness > 22, factor, 1.0)
        yfactor = np.clip((60.0 - yel) / (60.0 - 35.0), 0.0, 1.0)
        alpha = alpha * np.where(yel > 35, yfactor, 1.0)
    else:
        factor = np.clip((70.0 - greenness) / (70.0 - 25.0), 0.0, 1.0)
        alpha = alpha * np.where(greenness > 25, factor, 1.0)
    shadow = (greenness >= 6) & (np.maximum(np.maximum(R, G), B) <= 120)
    alpha = np.where(shadow, 0.0, alpha)
    enclosed = (dist < 55.0) & (greenness > 12)
    alpha = np.where(enclosed, 0.0, alpha)
    near_key = (dist < 110.0) & (greenness > 8)
    alpha = alpha * np.where(near_key, np.clip((dist - 55.0) / 55.0, 0.0, 1.0), 1.0)

    alpha_img = Image.fromarray(alpha.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.6))
    alpha = np.asarray(alpha_img).astype(np.float32)

    mask = alpha > 128
    lab2, n2 = ndimage.label(mask)
    dropped = []
    if n2 > 1:
        sizes = ndimage.sum(mask, lab2, range(1, n2 + 1))
        largest = int(np.argmax(sizes)) + 1
        keep_labels = {largest}
        for i, sz in enumerate(sizes, start=1):
            if i == largest:
                continue
            ys_c, xs_c = np.where(lab2 == i)
            bw = int(xs_c.max() - xs_c.min() + 1); bh = int(ys_c.max() - ys_c.min() + 1)
            if mode == "furfur":
                keep = sz >= 20000 or (bw >= 250 and bh >= 120)
            else:
                keep = sz >= 2000 or bw >= 110
            if keep:
                keep_labels.add(i)
            else:
                dropped.append((i, int(sz), bw, bh))
        keep_mask = np.isin(lab2, list(keep_labels))
        alpha = np.where(keep_mask, alpha, 0.0)

    out = a.copy()
    spill = (greenness > 8) & (alpha > 0)
    cap = np.maximum(R, B) + 8
    out[..., 1] = np.where(spill, np.minimum(G, cap), G)
    rgba = np.dstack([out, alpha]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA"), dropped

def solid_bbox(img):
    al = np.asarray(img)[..., 3]
    ys, xs = np.where(al > 128)
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))

def green_residue(img):
    arr = np.asarray(img).astype(np.float32)
    al = arr[..., 3]
    g = arr[..., 1] - np.maximum(arr[..., 0], arr[..., 2])
    return int(((al > 128) & (g > 30)).sum())

def save_surface(img, out_dir, surf):
    os.makedirs(out_dir, exist_ok=True)
    arr = np.asarray(img).copy()
    al = arr[..., 3]
    arr[..., 0] = np.where(al == 0, 0, arr[..., 0])
    arr[..., 1] = np.where(al == 0, 255, arr[..., 1])
    arr[..., 2] = np.where(al == 0, 0, arr[..., 2])
    final = Image.fromarray(arr, "RGBA")
    final.save(os.path.join(out_dir, f"surface{surf}.png"))
    Image.fromarray(al.astype(np.uint8), "L").save(os.path.join(out_dir, f"surface{surf}.pna"), format="PNG")
    pna_back = np.asarray(Image.open(os.path.join(out_dir, f"surface{surf}.pna")))
    corners = [int(al[0, 0]), int(al[0, -1]), int(al[-1, 0]), int(al[-1, -1])]
    return {"size": list(final.size), "bbox": list(solid_bbox(final)), "corners": corners,
            "pna_ok": bool(np.array_equal(pna_back, al.astype(np.uint8))),
            "green_residue_px": green_residue(final)}

def place_group(items, bottom=1211):
    H = 1216; MARGIN = 6
    need_half = 0.0
    for surf, img in items:
        bb = solid_bbox(img)
        cx = (bb[0] + bb[1]) / 2.0
        need_half = max(need_half, cx - bb[0], bb[1] - cx)
    W = int(np.ceil(need_half * 2)) + 1 + MARGIN * 2
    CX = (W - 1) / 2.0
    out = {}
    for surf, img in items:
        bb = solid_bbox(img)
        dx = int(round(CX - (bb[0] + bb[1]) / 2.0)); dy = int(bottom - bb[3])
        canvas = Image.new("RGBA", (W, H), (0, 255, 0, 0))
        canvas.paste(img, (dx, dy))
        out[surf] = canvas
    return out

ASTA_RAW = {
    0: os.path.join(CAND, "maid_M1_seed20261121_00001_.png"),
    1: os.path.join(RAW, "maid_expr_MA1_seed20261121_00001_.png"),
    2: os.path.join(RAW, "maid_expr_MA2_seed20261121_00001_.png"),
    3: os.path.join(RAW, "maid_expr_MA3_seed20261121_00001_.png"),
    4: os.path.join(RAW, "maid_expr_MA4_seed20261121_00001_.png"),
    5: os.path.join(RAW, "maid_expr_MA5_seed20261121_00001_.png"),
}
FUR_RAW = {
    10: os.path.join(CAND, "maid_M3_seed777701_00001_.png"),
    11: os.path.join(RAW, "maid_expr_MF11_seed777701_00001_.png"),
    12: os.path.join(RAW, "maid_expr_MF12_seed777701_00001_.png"),
    13: os.path.join(RAW, "maid_expr_MF13_seed777701_00001_.png"),
    14: os.path.join(GHOST, "work/maid_fix_raw/maid_fix_MF14_seed777701_00001_.png"),
    15: os.path.join(RAW, "maid_expr_MF15_seed777701_00001_.png"),
}

report = {}
for group_name, raws, mode in (("astaroth", ASTA_RAW, "astaroth"), ("furfur", FUR_RAW, "furfur")):
    items = []
    for surf in sorted(raws):
        keyed, dropped = key_image(raws[surf], mode)
        items.append((surf, keyed))
        print(f"maid {group_name} surface{surf} keyed dropped={dropped} bbox={solid_bbox(keyed)}", flush=True)
    placed = place_group(items)
    for surf, img in placed.items():
        info = save_surface(img, os.path.join(OUTROOT, "maid"), surf)
        info.update({"raw": os.path.basename(raws[surf]), "mode": "group"})
        report[f"maid/{surf}"] = info
        print(f"maid surface{surf} group size={info['size']} bbox={info['bbox']} residue={info['green_residue_px']} pna_ok={info['pna_ok']}", flush=True)

with open(os.path.join(OUTROOT, "finalize_report_maid.json"), "w") as f:
    json.dump(report, f, indent=1, ensure_ascii=False)
print("ALL DONE maid")
