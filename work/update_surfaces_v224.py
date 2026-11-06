import os, re
import numpy as np
from PIL import Image

# v2.24: 差し替え後の最終画像の実測 bbox から、旧 surfaces.txt の当たり判定を
# 線形変換して更新する（update_surfaces_v223.py と同方式、対象は night の 10〜15 のみ）。
BASE = os.path.expanduser("~/workspace/astaroth-ghost")
OLD = os.path.join(BASE, "work/v224_old_shell")
OUT = os.path.join(BASE, "work/v224_out")
BUILD = os.path.join(BASE, "build/astaroth/shell")

def bbox_of(path):
    al = np.asarray(Image.open(path).convert("RGBA"))[..., 3]
    ys, xs = np.where(al > 128)
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))

def parse(txt):
    blocks = {}
    cur = None
    for line in txt.splitlines():
        m = re.match(r"surface(\d+)\s*$", line.strip())
        if m:
            cur = int(m.group(1)); blocks[cur] = []
            continue
        m = re.match(r"collision(\d+),(\d+),(\d+),(\d+),(\d+),(\w+)", line.strip())
        if m and cur is not None:
            blocks[cur].append((int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), m.group(6)))
    return blocks

def transform(rects, ob, nb, new_size):
    ox0, ox1, oy0, oy1 = ob; nx0, nx1, ny0, ny1 = nb
    sx = (nx1 - nx0) / max(1, (ox1 - ox0)); sy = (ny1 - ny0) / max(1, (oy1 - oy0))
    W, H = new_size
    out = []
    for (x0, y0, x1, y1, name) in rects:
        a = int(round(nx0 + (x0 - ox0) * sx)); b = int(round(ny0 + (y0 - oy0) * sy))
        c = int(round(nx0 + (x1 - ox0) * sx)); d = int(round(ny0 + (y1 - oy0) * sy))
        a = max(0, min(a, W - 1)); c = max(a + 1, min(c, W)); b = max(0, min(b, H - 1)); d = max(b + 1, min(d, H))
        out.append((a, b, c, d, name))
    return out

SURFS = {10, 11, 12, 13, 14, 15}
txt_path = os.path.join(BUILD, "night", "surfaces.txt")
txt = open(txt_path, encoding="utf-8").read()
old_txt = open(os.path.join(OLD, "night", "surfaces.txt"), encoding="utf-8").read()
old_blocks = parse(old_txt)
lines = txt.splitlines()
cur = None
changed = {}
used = {}
for i, line in enumerate(lines):
    m = re.match(r"surface(\d+)\s*$", line.strip())
    if m:
        cur = int(m.group(1)); continue
    m = re.match(r"(collision\d+,)(\d+),(\d+),(\d+),(\d+),(\w+)", line.strip())
    if m and cur in SURFS:
        if cur not in changed:
            ob = bbox_of(os.path.join(OLD, "night", f"surface{cur}.png"))
            new_path = os.path.join(OUT, "night", f"surface{cur}.png")
            nb = bbox_of(new_path)
            size = Image.open(new_path).size
            changed[cur] = transform(old_blocks[cur], ob, nb, size)
            print(f"night surface{cur}: old bbox {ob} -> new bbox {nb} size {size}")
        rects = changed[cur]
        u = used.get(cur, 0)
        if u < len(rects):
            a, b, c, d, name = rects[u]
            lines[i] = f"collision{u},{a},{b},{c},{d},{name}"
            used[cur] = u + 1
open(txt_path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"night surfaces.txt updated for {sorted(changed)}")
print("DONE")
