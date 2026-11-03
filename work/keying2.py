import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
a = np.asarray(im).astype(np.float32)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
greenness = G - np.maximum(R, B)

# pass 1: border flood through green-dominant pixels
bg_like = greenness >= 18
lab, n = ndimage.label(bg_like)
border_labels = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
border_labels.discard(0)
bg = np.isin(lab, list(border_labels))
alpha = (~bg).astype(np.float32) * 255.0

# pass 2: greenness falloff kills enclosed bg (halo interior) and green rim
factor = np.clip((70.0 - greenness) / (70.0 - 25.0), 0.0, 1.0)
alpha = alpha * np.where(greenness > 25, factor, 1.0)

alpha_img = Image.fromarray(alpha.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.6))
alpha = np.asarray(alpha_img).astype(np.float32)

# despill on visible fringe
out = a.copy()
spill = (greenness > 12) & (alpha > 0)
cap = np.maximum(R, B) + 10
out[..., 1] = np.where(spill, np.minimum(G, cap), G)

rgba = np.dstack([out, alpha]).astype(np.uint8)
res = Image.fromarray(rgba, "RGBA")
res.save(dst)

solid = alpha > 128
ys, xs = np.where(solid)
print("saved", dst, "size", res.size)
print(f"alpha>128 ratio={solid.mean():.3f} bbox x:{xs.min()}..{xs.max()} y:{ys.min()}..{ys.max()}")
print(f"fully transparent ratio={(alpha==0).mean():.3f}")
print("opaque px top70 (halo ring):", int(solid[:70, :].sum()))
print("corner alpha:", [int(alpha[0,0]), int(alpha[0,-1]), int(alpha[-1,0]), int(alpha[-1,-1])])
# halo interior check: center of halo approx x=mid of top cluster
top_cols = np.where(solid[:40, :].any(axis=0))[0]
if len(top_cols):
    cx = int((top_cols.min() + top_cols.max()) / 2)
    print("halo interior alpha at (cx,35):", int(alpha[35, cx]), "cx=", cx)
