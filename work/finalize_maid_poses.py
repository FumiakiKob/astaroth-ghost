import sys, os, json
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

# v2.27 後処理: maid シェルのポーズ・座り 18 面のキーイングと配置。
# キーイングは finalize_maid.py / finalize_v223.py と同一方式（色距離ベース＋
# 囲み領域除去＋デスピル強化）。配置はポーズ用の単体配置（place_single:
# bbox+マージン、下端1211）で、夜シェル v2.23 のポーズ量産と同方式。

GHOST = os.path.expanduser("~/workspace/astaroth-ghost")
RAW = os.path.join(GHOST, "work/maid_pose_raw")
OUTROOT = os.path.join(GHOST, "work/maid_pose_out")

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

def place_single(keyed, bottom=1211):
    kb = solid_bbox(keyed)
    bw = kb[1] - kb[0] + 1
    W = bw + 16; H = 1216
    dy = bottom - kb[3]
    if kb[2] + dy < 0:
        dy = -kb[2]
    dx = -kb[0] + 8
    canvas = Image.new("RGBA", (W, H), (0, 255, 0, 0))
    canvas.paste(keyed, (dx, dy))
    return canvas, dx, dy

ASTA_SEED = 20261121
FUR_SEED = 777701
JOBS = []
for s in (6, 7, 8, 9, 46, 47, 48, 49, 20):
    JOBS.append((s, f"maid_pose_MA{s}_seed{ASTA_SEED}_00001_.png", "asta"))
for s in (16, 17, 18, 19, 56, 57, 58, 59, 21):
    JOBS.append((s, f"maid_pose_MF{s}_seed{FUR_SEED}_00001_.png", "furfur"))

report = {}
for surf, raw_name, mode in JOBS:
    raw = os.path.join(RAW, raw_name)
    keyed, dropped = key_image(raw, mode)
    placed, dx, dy = place_single(keyed)
    info = save_surface(placed, os.path.join(OUTROOT, "maid"), surf)
    info.update({"raw": raw_name, "dropped": dropped, "dx": dx, "dy": dy, "mode": "single"})
    report[f"maid/{surf}"] = info
    print(f"maid surface{surf} single size={info['size']} bbox={info['bbox']} residue={info['green_residue_px']} pna_ok={info['pna_ok']} corners={info['corners']} dropped={dropped}", flush=True)

with open(os.path.join(OUTROOT, "finalize_report_maid_poses.json"), "w") as f:
    json.dump(report, f, indent=1, ensure_ascii=False)
print("ALL DONE maid poses")
