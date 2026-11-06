import os, re, sys
import numpy as np
from PIL import Image

# 差し替え後の最終画像の実測 bbox から、旧 surfaces.txt の当たり判定を線形変換して更新する。
BASE = os.path.expanduser("~/workspace/astaroth-ghost")
OLD = os.path.join(BASE, "work/v223_old_shell")
OUT = os.path.join(BASE, "work/v223_out")
BUILD = os.path.join(BASE, "build/astaroth/shell")

def bbox_of(path):
    al = np.asarray(Image.open(path).convert("RGBA"))[..., 3]
    ys, xs = np.where(al > 128)
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))

def parse(txt):
    blocks = {}  # surf -> (rects, raw_lines)
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

def update(shell, surfs):
    txt_path = os.path.join(BUILD, shell, "surfaces.txt")
    txt = open(txt_path, encoding="utf-8").read()
    old_txt = open(os.path.join(OLD, shell, "surfaces.txt"), encoding="utf-8").read()
    old_blocks = parse(old_txt)
    lines = txt.splitlines()
    cur = None
    changed = {}
    for i, line in enumerate(lines):
        m = re.match(r"surface(\d+)\s*$", line.strip())
        if m:
            cur = int(m.group(1)); continue
        m = re.match(r"(collision\d+,)(\d+),(\d+),(\d+),(\d+),(\w+)", line.strip())
        if m and cur in surfs:
            if cur not in changed:
                ob = bbox_of(os.path.join(OLD, shell, f"surface{cur}.png"))
                new_path = os.path.join(OUT, shell, f"surface{cur}.png")
                nb = bbox_of(new_path)
                size = Image.open(new_path).size
                changed[cur] = transform(old_blocks[cur], ob, nb, size)
                print(f"{shell} surface{cur}: old bbox {ob} -> new bbox {nb} size {size}")
            idx = int(m.group(1).split("collision")[1].rstrip(","))
            # collision の出現順で対応させる
            rects = changed[cur]
            used = update._used.setdefault(cur, 0)
            if used < len(rects):
                a, b, c, d, name = rects[used]
                lines[i] = f"collision{used},{a},{b},{c},{d},{name}"
                update._used[cur] = used + 1
    open(txt_path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"{shell} surfaces.txt updated for {sorted(changed)}")

update._used = {}
night_surfs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 46, 47, 48, 49, 56, 57, 58, 59]
master_surfs = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 56, 57, 58, 59]
which = sys.argv[1] if len(sys.argv) > 1 else "all"
if which in ("all", "night"):
    update("night", set(night_surfs))
if which in ("all", "master"):
    update._used = {}
    update("master", set(master_surfs))
print("DONE")
