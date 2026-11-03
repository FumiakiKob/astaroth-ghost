import sys, os, json
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage

# usage: finalize_sitting.py <src_dir> <out_dir>
# 座りポーズ（アスタロト20／フルフル21）のキーイング＋配置。
# キーイング本体は二人分それぞれの既存 finalize と同一：
#   アスタロト = finalize_expr.py（ramp 70/25、成分整理 >=2000 or 幅>=110）
#   フルフル   = finalize_furfur.py（yel 判定併用、成分整理 >=20000 or 幅>=250&高さ>=120）
# 配置はポーズ差分の方式（H=1216、幅は bbox＋マージンでセンタリング）。
# 下端は椅子の脚下端を既存立ち絵の接地ライン（アスタロト1212／フルフル1211）に合わせる。
src_dir, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)

JOBS = [
    (20, "astaroth_sit20_seed201103_00001_.png", "astaroth", 1212),
    (21, "furfur_sit21_seed21101_00001_.png", "furfur", 1211),
]

def key_astaroth(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    greenness = G - np.maximum(R, B)

    bg_like = greenness >= 18
    lab, n = ndimage.label(bg_like)
    border_labels = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    border_labels.discard(0)
    bg = np.isin(lab, list(border_labels))
    alpha = (~bg).astype(np.float32) * 255.0

    factor = np.clip((70.0 - greenness) / (70.0 - 25.0), 0.0, 1.0)
    alpha = alpha * np.where(greenness > 25, factor, 1.0)

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
            bw = int(xs_c.max() - xs_c.min() + 1)
            if sz >= 2000 or bw >= 110:
                keep_labels.add(i)
            else:
                dropped.append((i, int(sz), bw))
        keep = np.isin(lab2, list(keep_labels))
        alpha = np.where(keep, alpha, 0.0)

    out = a.copy()
    spill = (greenness > 12) & (alpha > 0)
    cap = np.maximum(R, B) + 10
    out[..., 1] = np.where(spill, np.minimum(G, cap), G)
    rgba = np.dstack([out, alpha]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA"), dropped

def key_furfur(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    greenness = G - np.maximum(R, B)

    yel = np.minimum(R, G) - B
    bg_like = (greenness >= 18) | (yel >= 60)
    lab, n = ndimage.label(bg_like)
    border_labels = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    border_labels.discard(0)
    bg = np.isin(lab, list(border_labels))
    alpha = (~bg).astype(np.float32) * 255.0

    factor = np.clip((32.0 - greenness) / (32.0 - 22.0), 0.0, 1.0)
    alpha = alpha * np.where(greenness > 22, factor, 1.0)
    yfactor = np.clip((60.0 - yel) / (60.0 - 35.0), 0.0, 1.0)
    alpha = alpha * np.where(yel > 35, yfactor, 1.0)

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
            bw = int(xs_c.max() - xs_c.min() + 1)
            bh = int(ys_c.max() - ys_c.min() + 1)
            if sz >= 20000 or (bw >= 250 and bh >= 120):
                keep_labels.add(i)
            else:
                dropped.append((i, int(sz), bw, bh))
        keep = np.isin(lab2, list(keep_labels))
        alpha = np.where(keep, alpha, 0.0)

    out = a.copy()
    spill = (greenness > 12) & (alpha > 0)
    cap = np.maximum(R, B) + 10
    out[..., 1] = np.where(spill, np.minimum(G, cap), G)
    rgba = np.dstack([out, alpha]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA"), dropped

H = 1216
MARGIN = 8
report = {}
for surf, fname, who, bottom in JOBS:
    key_fn = key_astaroth if who == "astaroth" else key_furfur
    img, dropped = key_fn(os.path.join(src_dir, fname))
    al0 = np.asarray(img)[..., 3]
    ys, xs = np.where(al0 > 128)
    bb = (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))
    bw = bb[1] - bb[0] + 1
    W = bw + MARGIN * 2
    cx = (bb[0] + bb[1]) / 2.0
    dx = int(round((W - 1) / 2.0 - cx))
    dy = int(bottom - bb[3])
    top = bb[2] + dy
    if top < 0:
        dy -= top
        top = 0
        print(f"  surface{surf}: dy adjusted to {dy} (bottom={bb[3] + dy}) to fit top")
    canvas = Image.new("RGBA", (W, H), (0, 255, 0, 0))
    canvas.paste(img, (dx, dy))
    arr = np.asarray(canvas).copy()
    al = arr[..., 3]
    arr[..., 0] = np.where(al == 0, 0, arr[..., 0])
    arr[..., 1] = np.where(al == 0, 255, arr[..., 1])
    arr[..., 2] = np.where(al == 0, 0, arr[..., 2])
    final = Image.fromarray(arr, "RGBA")
    png_path = os.path.join(out_dir, f"surface{surf}.png")
    final.save(png_path)
    pna = Image.fromarray(al.astype(np.uint8), "L")
    pna_path = os.path.join(out_dir, f"surface{surf}.pna")
    pna.save(pna_path, format="PNG")

    pna_back = np.asarray(Image.open(pna_path))
    ys2, xs2 = np.where(al > 128)
    corners = [int(al[0, 0]), int(al[0, -1]), int(al[-1, 0]), int(al[-1, -1])]
    info = {
        "size": [W, H], "dx": dx, "dy": dy, "src_bbox": bb,
        "bbox": [int(xs2.min()), int(xs2.max()), int(ys2.min()), int(ys2.max())],
        "corners_alpha": corners,
        "pna_matches_alpha": bool(np.array_equal(pna_back, al.astype(np.uint8))),
        "transparent_rgb_unique": np.unique(arr[al == 0].reshape(-1, 4), axis=0).tolist(),
        "dropped": dropped,
    }
    report[surf] = info
    print(f"surface{surf} saved size={W}x{H} dx={dx} dy={dy} bbox={info['bbox']} corners={corners} pna_ok={info['pna_matches_alpha']} dropped={dropped}", flush=True)

    bgc = Image.new("RGBA", final.size, (35, 35, 56, 255))
    comp = Image.alpha_composite(bgc, final).convert("RGB")
    comp.save(os.path.join(out_dir, f"surface{surf}_dark.png"))
    grid = comp.copy()
    gd = ImageDraw.Draw(grid)
    for gx in range(0, W, 50):
        gd.line([(gx, 0), (gx, H)], fill=(255, 80, 80) if gx % 200 == 0 else (120, 120, 160), width=1)
        gd.text((gx + 2, 4), str(gx), fill=(255, 255, 120))
    for gy in range(0, H, 50):
        gd.line([(0, gy), (W, gy)], fill=(255, 80, 80) if gy % 200 == 0 else (120, 120, 160), width=1)
        gd.text((4, gy + 2), str(gy), fill=(255, 255, 120))
    grid.save(os.path.join(out_dir, f"surface{surf}_grid.png"))
    grid.crop((0, 0, W, 640)).resize((W * 2, 1280)).save(os.path.join(out_dir, f"surface{surf}_grid_upper.png"))

with open(os.path.join(out_dir, "sitting_finalize_report.json"), "w") as f:
    json.dump(report, f, indent=1)
print("ALL DONE")
