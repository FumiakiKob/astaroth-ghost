import os, re
import numpy as np
from PIL import Image

BASE = os.path.expanduser("~/workspace/astaroth-ghost")
OUT = os.path.join(BASE, "work/maid_out")
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

SURFS = {0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15}
master_txt_path = os.path.join(BUILD, "master", "surfaces.txt")
maid_dir = os.path.join(BUILD, "maid")
os.makedirs(maid_dir, exist_ok=True)
txt = open(master_txt_path, encoding="utf-8").read()
old_blocks = parse(txt)

header = "charset,UTF-8\n\ndescript\n{\nversion,1\n}\n\n"
header += "// 【メイドシェル】第3シェル「maid」（2026-11-07、nar v2.26）。\n"
header += "// surface0〜5: アスタロト メイドセット（M1: クラシックメイド黒×白、seed 20261121）。\n"
header += "// surface10〜15: フルフル メイドセット（M3: クラシックメイド黒×白、seed 777701、\n"
header += "//   頭身指示つき）。両セットとも色距離キーイング＋一括正規化（中心・下端1211統一）\n"
header += "//   で配置し、当たり判定は master の判定を旧 bbox → 新 bbox の線形変換で\n"
header += "//   最終画像の実測に基づき付け替えた。\n"
header += "// それ以外の番号（6〜9、16〜21、26〜30、46〜49、56〜59）は master の画像を\n"
header += "// 仮置きコピーしてあり、当たり判定も master と同一。\n"

idx = txt.index("surface0\n{")
body = txt[idx:]
lines = body.splitlines()
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
            ob = bbox_of(os.path.join(BUILD, "master", "surface%d.png" % cur))
            new_path = os.path.join(OUT, "maid", "surface%d.png" % cur)
            nb = bbox_of(new_path)
            size = Image.open(new_path).size
            changed[cur] = transform(old_blocks[cur], ob, nb, size)
            print("maid surface%d: master bbox %s -> maid bbox %s size %s rects %s" % (cur, ob, nb, size, changed[cur]))
        rects = changed[cur]
        u = used.get(cur, 0)
        if u < len(rects):
            a, b, c, d, name = rects[u]
            lines[i] = "collision%d,%d,%d,%d,%d,%s" % (u, a, b, c, d, name)
            used[cur] = u + 1

out_txt = header + "\n".join(lines) + "\n"
with open(os.path.join(maid_dir, "surfaces.txt"), "w", encoding="utf-8") as f:
    f.write(out_txt)
print("maid surfaces.txt written for %s" % sorted(changed))
print("DONE")
