import sys
from PIL import Image
import numpy as np

for path in sys.argv[1:]:
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    h, w, _ = a.shape
    corners = np.concatenate([a[:20,:20].reshape(-1,3), a[:20,-20:].reshape(-1,3), a[-20:,:20].reshape(-1,3), a[-20:,-20:].reshape(-1,3)])
    bg = corners.mean(axis=0)
    dist = np.abs(a - bg).sum(axis=2)
    mask = dist > 90  # non-background
    ys, xs = np.where(mask)
    print(path)
    print(f"  size={w}x{h} bg_rgb={bg.round(1)} nonbg_ratio={mask.mean():.3f}")
    if len(ys):
        print(f"  bbox x:{xs.min()}..{xs.max()} y:{ys.min()}..{ys.max()}")
        print(f"  margins top={ys.min()} bottom={h-1-ys.max()} left={xs.min()} right={w-1-xs.max()}")
        print(f"  touches top={ys.min()<=2} bottom={ys.max()>=h-3} left={xs.min()<=2} right={xs.max()>=w-3}")
