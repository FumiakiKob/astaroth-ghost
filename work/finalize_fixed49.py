import sys, os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

# finalize_expr.py と同一のキーイング。ただし横クロップを基番9のフレーム
# (left=186, width=478) に固定し、ドナーと基番を同一座標系に揃える。
# usage: finalize_fixed.py <src_png> <out_png> [left]
src, out_png = sys.argv[1], sys.argv[2]
LEFT = int(sys.argv[3]) if len(sys.argv) > 3 else 186
TARGET_W = 478

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

mask = alpha > 128
lab2, n2 = ndimage.label(mask)
if n2 > 1:
    sizes = ndimage.sum(mask, lab2, range(1, n2 + 1))
    largest = int(np.argmax(sizes)) + 1
    keep_labels = {largest}
    for i, sz in enumerate(sizes, start=1):
        if i == largest:
            continue
        ys_c, xs_c = np.where(lab2 == i)
        bw = xs_c.max() - xs_c.min() + 1
        if sz >= 2000 or bw >= 110:
            keep_labels.add(i)
    keep = np.isin(lab2, list(keep_labels))
    alpha = np.where(keep, alpha, 0.0)
    print(f"components={n2} kept={len(keep_labels)}")

out = a.copy()
spill = (greenness > 12) & (alpha > 0)
cap = np.maximum(R, B) + 10
out[..., 1] = np.where(spill, np.minimum(G, cap), G)

rgba = np.dstack([out, alpha]).astype(np.uint8)
res = Image.fromarray(rgba, "RGBA")
res = res.crop((LEFT, 0, LEFT + TARGET_W, res.height))

arr = np.asarray(res).copy()
al = arr[..., 3]
arr[..., 0] = np.where(al == 0, 0, arr[..., 0])
arr[..., 1] = np.where(al == 0, 255, arr[..., 1])
arr[..., 2] = np.where(al == 0, 0, arr[..., 2])
final = Image.fromarray(arr, "RGBA")
final.save(out_png)
pna = Image.fromarray(al.astype(np.uint8), "L")
pna.save(out_png.replace(".png", ".pna"), format="PNG")
solid = al > 128
ys, xs = np.where(solid)
print(f"saved {out_png} size={final.size} solidbbox x:{xs.min()}..{xs.max()} y:{ys.min()}..{ys.max()}")
# green residue check: opaque pixels where G >> R,B
op = al > 200
gr = arr[..., 1].astype(int) - np.maximum(arr[..., 0], arr[..., 2]).astype(int)
print("green-residue opaque px (gr>25):", int(((gr > 25) & op).sum()))
