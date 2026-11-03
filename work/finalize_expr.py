import sys, os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

# usage: finalize_expr.py <expr_no> <src_png> <out_dir>
# keying2.py と同じキーイング → 478幅センタリング → 透明RGB=(0,255,0) → png + pna + 暗背景プレビュー
expr, src, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out_dir, exist_ok=True)

im = Image.open(src).convert("RGB")
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

# --- detached-component cleanup: drop small floating artifacts (manga sigh puffs,
# sweat squiggles, sparkles). Keep largest component, components >= 2000px,
# and wide flat components near the top (the halo ring). ---
mask = alpha > 128
lab2, n2 = ndimage.label(mask)
if n2 > 1:
    sizes = ndimage.sum(mask, lab2, range(1, n2 + 1))
    largest = int(np.argmax(sizes)) + 1
    keep_labels = {largest}
    dropped = []
    for i, sz in enumerate(sizes, start=1):
        if i == largest:
            continue
        ys_c, xs_c = np.where(lab2 == i)
        bw = xs_c.max() - xs_c.min() + 1
        if sz >= 2000 or bw >= 110:
            keep_labels.add(i)
        else:
            dropped.append((i, int(sz), int(bw)))
    keep = np.isin(lab2, list(keep_labels))
    alpha = np.where(keep, alpha, 0.0)
    print(f"expr{expr} components={n2} kept={len(keep_labels)} dropped={dropped}")
else:
    print(f"expr{expr} components=1 (no cleanup)")

out = a.copy()
spill = (greenness > 12) & (alpha > 0)
cap = np.maximum(R, B) + 10
out[..., 1] = np.where(spill, np.minimum(G, cap), G)

rgba = np.dstack([out, alpha]).astype(np.uint8)
res = Image.fromarray(rgba, "RGBA")

# --- crop: full height, width 478 centered on solid bbox center (fallback: bbox+margin) ---
alpha_np = np.asarray(res)[..., 3]
solid = alpha_np > 128
ys, xs = np.where(solid)
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
print(f"expr{expr} solid bbox x:{x0}..{x1} y:{y0}..{y1} (w={x1-x0+1})")
W, H = res.size
TARGET_W = 478
if x1 - x0 + 1 <= TARGET_W:
    cx = (x0 + x1) / 2.0
    left = int(round(cx - TARGET_W / 2.0))
    left = max(0, min(left, W - TARGET_W))
else:
    left = max(0, x0 - 8)
    TARGET_W = min(W - left, x1 - x0 + 1 + 16)
    print(f"expr{expr} WARNING: char wider than 478, using width {TARGET_W}")
res = res.crop((left, 0, left + TARGET_W, H))
print(f"expr{expr} cropped x:{left}..{left+TARGET_W} size={res.size}")

arr = np.asarray(res).copy()
al = arr[..., 3]
arr[..., 0] = np.where(al == 0, 0, arr[..., 0])
arr[..., 1] = np.where(al == 0, 255, arr[..., 1])
arr[..., 2] = np.where(al == 0, 0, arr[..., 2])
final = Image.fromarray(arr, "RGBA")
png_path = os.path.join(out_dir, f"surface{expr}.png")
final.save(png_path)

pna = Image.fromarray(al.astype(np.uint8), "L")
pna_path = os.path.join(out_dir, f"surface{expr}.pna")
pna.save(pna_path, format="PNG")

# dark composite preview (full + upper body crop)
bgc = Image.new("RGBA", final.size, (35, 35, 56, 255))
comp = Image.alpha_composite(bgc, final).convert("RGB")
comp.save(os.path.join(out_dir, f"surface{expr}_dark.png"))
comp.crop((0, 0, final.width, 560)).save(os.path.join(out_dir, f"surface{expr}_dark_upper.png"))

solid2 = al > 128
ys2, xs2 = np.where(solid2)
print(f"expr{expr} saved {png_path} size={final.size} solidbbox x:{xs2.min()}..{xs2.max()} y:{ys2.min()}..{ys2.max()}")
print(f"expr{expr} corners alpha:", [int(al[0,0]), int(al[0,-1]), int(al[-1,0]), int(al[-1,-1])],
      "transparent px rgb unique:", np.unique(arr[al == 0].reshape(-1, 4), axis=0)[:3].tolist())
print(f"expr{expr} pna saved {pna_path}")
