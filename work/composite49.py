import numpy as np
from PIL import Image, ImageFilter

# 体×顔合成: 基番9 (finalize済み, 現行 surface9 と画素一致) の体に、
# ドナー c1101 の顔パーツ領域だけを位置合わせして移植する。
# アルファは基番9を全面保持するので、体・輪郭・当たり判定は完全不変。
BASE = "base9_refinal.png"
DONOR = "cand_fin/pose49c20261101.png"
OUT = "surface49_new.png"
DX, DY = 1, 5  # ドナー -> 基番 の平行移動 (目クラスタ実測差)

base = np.asarray(Image.open(BASE).convert("RGBA")).astype(np.float32)
donor = np.asarray(Image.open(DONOR).convert("RGBA")).astype(np.float32)
H, W = base.shape[:2]

# ドナーを DX,DY ずらしたキャンバス
shifted = np.zeros_like(donor)
ys0, ys1 = max(0, DY), min(H, H + DY)
xs0, xs1 = max(0, DX), min(W, W + DX)
dy0, dy1 = ys0 - DY, ys1 - DY
dx0, dx1 = xs0 - DX, xs1 - DX
shifted[ys0:ys1, xs0:xs1] = donor[dy0:dy1, dx0:dx1]

# 肌色マッチ: マスク外周リング (頬の肌) の平均色差でドナーを補正
def ring_stats(img):
    pts = []
    for (x0, x1, y0, y1) in [(140, 152, 225, 262), (310, 322, 225, 262), (205, 258, 272, 282)]:
        pts.append(img[y0:y1, x0:x1, :3].reshape(-1, 3))
    return np.concatenate(pts).mean(axis=0)

mb = ring_stats(base)
md = ring_stats(shifted)
shift_rgb = np.clip(shifted[..., :3] + (mb - md), 0, 255)
print("skin tone base", mb, "donor", md, "shift", mb - md)

# マスク: 顔パーツ帯 (目・眉・鼻・口) の楕円。中心 (231,230), rx=84, ry=46
yy, xx = np.mgrid[0:H, 0:W]
ell = ((xx - 231) / 84.0) ** 2 + ((yy - 230) / 46.0) ** 2
mask = (ell <= 1.0).astype(np.float32) * 255.0
mask = np.asarray(Image.fromarray(mask.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(7)))
mask = mask.astype(np.float32) / 255.0
# 基番が透明な所には貼らない
mask = mask * (base[..., 3] > 200)

out = base.copy()
for c in range(3):
    out[..., c] = base[..., c] * (1 - mask) + shift_rgb[..., c] * mask
out[..., 3] = base[..., 3]

arr = out.astype(np.uint8)
# 透明画素 RGB 規約は基番側で既に満たされ、マスク内は不透明なので不変
Image.fromarray(arr, "RGBA").save(OUT)
pna = Image.fromarray(arr[..., 3].astype(np.uint8), "L")
pna.save(OUT.replace(".png", ".pna"), format="PNG")

# 検証: マスク外の差分ゼロ / マスク内の差分あり
core = mask > 0.999
outer = mask < 0.001
diff = np.abs(arr[..., :3].astype(int) - base[..., :3].astype(int)).max(axis=2)
print("outer max diff (must be 0):", int(diff[outer].max()) if outer.any() else None)
print("alpha identical:", bool((arr[..., 3] == base[..., 3]).all()))
print("core changed frac:", float((diff[core] > 10).mean()))
op = arr[..., 3] > 200
gr = arr[..., 1].astype(int) - np.maximum(arr[..., 0], arr[..., 2]).astype(int)
print("green residue opaque px:", int(((gr > 25) & op).sum()))
print("saved", OUT, arr.shape)
