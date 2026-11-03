import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
a = np.asarray(im).astype(np.float32)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
greenness = G - np.maximum(R, B)

# background-like: green-dominant pixels
bg_like = greenness >= 18
lab, n = ndimage.label(bg_like)
border_labels = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
border_labels.discard(0)
bg = np.isin(lab, list(border_labels))
fg = ~bg

alpha = (fg.astype(np.float32)) * 255.0
# soften alpha edge a touch
alpha_img = Image.fromarray(alpha.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.8))
alpha = np.asarray(alpha_img).astype(np.float32)

# despill: pull green fringe back toward neutral on visible pixels
out = a.copy()
spill = (greenness > 20) & (alpha > 0)
cap = np.maximum(R, B) + 15
out[..., 1] = np.where(spill, np.minimum(G, cap), G)

rgba = np.dstack([out, alpha]).astype(np.uint8)
res = Image.fromarray(rgba, "RGBA")
res.save(dst)

solid = alpha > 128
ys, xs = np.where(solid)
print("saved", dst, "size", res.size)
print(f"alpha>128 ratio={solid.mean():.3f} bbox x:{xs.min()}..{xs.max()} y:{ys.min()}..{ys.max()}")
print(f"fully transparent ratio={(alpha==0).mean():.3f}")
top = solid[:70, :]
print("opaque pixels in top 70 rows (halo):", int(top.sum()))
corners_alpha = [int(alpha[0,0]), int(alpha[0,-1]), int(alpha[-1,0]), int(alpha[-1,-1])]
print("corner alpha:", corners_alpha)
