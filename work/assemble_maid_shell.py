import os, shutil, re
import numpy as np
from PIL import Image

# shell/maid の組み立てと静的確認。
# - descript.txt は night を土台に name を maid へ
# - 新規12面（0〜5・10〜15）は work/maid_out/maid から
# - 仮置き面（6〜9・16〜21・26〜30・46〜49・56〜59）は master からコピー
# - surfaces.txt は update_surfaces_maid.py が生成済みのものを使う（本スクリプト
#   では生成しない。先にそちらを実行すること）
BASE = os.path.expanduser("~/workspace/astaroth-ghost")
BUILD = os.path.join(BASE, "build/astaroth/shell")
OUT = os.path.join(BASE, "work/maid_out/maid")
MAID = os.path.join(BUILD, "maid")
MASTER = os.path.join(BUILD, "master")
NEW = [0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15]
PLACEHOLDER = [6, 7, 8, 9, 16, 17, 18, 19, 20, 21, 26, 27, 28, 29, 30,
               46, 47, 48, 49, 56, 57, 58, 59]
ALL = sorted(NEW + PLACEHOLDER)

os.makedirs(MAID, exist_ok=True)

# descript
night_desc = open(os.path.join(BUILD, "night", "descript.txt"), encoding="utf-8").read()
maid_desc = night_desc.replace("name,night", "name,maid")
assert "name,maid" in maid_desc
with open(os.path.join(MAID, "descript.txt"), "w", encoding="utf-8") as f:
    f.write(maid_desc)
print("descript.txt written (name,maid)")

for n in NEW:
    for ext in ("png", "pna"):
        src = os.path.join(OUT, f"surface{n}.{ext}")
        assert os.path.exists(src), src
        shutil.copy2(src, os.path.join(MAID, f"surface{n}.{ext}"))
for n in PLACEHOLDER:
    for ext in ("png", "pna"):
        src = os.path.join(MASTER, f"surface{n}.{ext}")
        assert os.path.exists(src), src
        shutil.copy2(src, os.path.join(MAID, f"surface{n}.{ext}"))
print(f"copied new {len(NEW)} + placeholder {len(PLACEHOLDER)} surfaces")

assert os.path.exists(os.path.join(MAID, "surfaces.txt")), "surfaces.txt missing: run update_surfaces_maid.py first"

# 静的確認: 定義数＝png数＝pna数、欠けなし
txt = open(os.path.join(MAID, "surfaces.txt"), encoding="utf-8").read()
defined = sorted(int(m.group(1)) for m in re.finditer(r"^surface(\d+)\s*$", txt, re.M))
pngs = sorted(int(m.group(1)) for m in
              (re.match(r"surface(\d+)\.png$", f) for f in os.listdir(MAID)) if m)
pnas = sorted(int(m.group(1)) for m in
              (re.match(r"surface(\d+)\.pna$", f) for f in os.listdir(MAID)) if m)
print(f"defined={len(defined)} png={len(pngs)} pna={len(pnas)}")
print(f"defined set == ALL: {defined == ALL}, png set == ALL: {pngs == ALL}, pna set == ALL: {pnas == ALL}")
assert defined == ALL and pngs == ALL and pnas == ALL

def green_residue(img):
    arr = np.asarray(img).astype(np.float32)
    al = arr[..., 3]
    g = arr[..., 1] - np.maximum(arr[..., 0], arr[..., 2])
    return int(((al > 128) & (g > 30)).sum())

ok = True
for n in ALL:
    im = Image.open(os.path.join(MAID, f"surface{n}.png")).convert("RGBA")
    al = np.asarray(im)[..., 3]
    pna = np.asarray(Image.open(os.path.join(MAID, f"surface{n}.pna")))
    pna_ok = bool(np.array_equal(pna, al.astype(np.uint8)))
    corners = [int(al[0, 0]), int(al[0, -1]), int(al[-1, 0]), int(al[-1, -1])]
    res = green_residue(im) if n in NEW else -1
    flag = pna_ok and corners == [0, 0, 0, 0] and (res == 0 if n in NEW else True)
    if not flag:
        ok = False
    print(f"surface{n}: size={im.size} pna_ok={pna_ok} corners={corners} green_residue={res if n in NEW else '(placeholder)'}")
print("STATIC CHECK:", "ALL OK" if ok else "PROBLEM")
assert ok
print("DONE")
