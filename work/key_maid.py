import importlib.util, os
import numpy as np
from PIL import Image

# finalize_v224.py の key_image（色距離ベース＋囲み領域除去、黄緑背景対応）を流用。
spec = importlib.util.spec_from_file_location(
    "fv224", os.path.expanduser("~/workspace/astaroth-ghost/work/finalize_v224.py"))
fv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fv)

BASE = os.path.expanduser("~/workspace/astaroth-ghost/work/maid_candidates")
JOBS = [
    ("raw/maid_M1_seed20261121_00001_.png", "M1_seed20261121.png", "astaroth"),
    ("raw/maid_M2_seed111701_00001_.png",   "M2_seed111701.png",   "furfur"),
    ("raw/maid_M3_seed777701_00001_.png",   "M3_seed777701.png",   "furfur"),
]
for src, dst, mode in JOBS:
    img, dropped = fv.key_image(os.path.join(BASE, src), mode)
    res = fv.green_residue(img)
    # 完全透明ピクセルの RGB を黒に寄せ、アルファ無視の表示でも緑が透けないようにする
    arr = np.asarray(img).copy()
    al = arr[..., 3]
    zero = al == 0
    arr[..., 0] = np.where(zero, 0, arr[..., 0])
    arr[..., 1] = np.where(zero, 0, arr[..., 1])
    arr[..., 2] = np.where(zero, 0, arr[..., 2])
    out = Image.fromarray(arr, "RGBA")
    out.save(os.path.join(BASE, dst))
    print("saved", dst, "mode", mode, "green_residue", res, "dropped", dropped,
          "bbox", fv.solid_bbox(img))
print("DONE")
