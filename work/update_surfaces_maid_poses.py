import os, re, shutil
import numpy as np
from PIL import Image

# v2.27: maid シェルのポーズ・座り 18 面の当たり判定付け替え＋画像差し替え。
# 現在の maid 面（master 仮置きコピー）の bbox → 新面 bbox の線形変換で、
# maid 側 surfaces.txt の該当ブロックだけを最終画像の実測に合わせる。
# update_surfaces_maid.py（v2.26 基本面）と同方式。

BASE = os.path.expanduser("~/workspace/astaroth-ghost")
OUT = os.path.join(BASE, "work/maid_pose_out")
MAID = os.path.join(BASE, "build/astaroth/shell/maid")

TARGETS = {6, 7, 8, 9, 46, 47, 48, 49, 16, 17, 18, 19, 56, 57, 58, 59, 20, 21}

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

txt_path = os.path.join(MAID, "surfaces.txt")
txt = open(txt_path, encoding="utf-8").read()
old_blocks = parse(txt)

# ヘッダ注記の更新（仮置き→ v2.27 でポーズ・座りも差し替え済み）
old_note = ("// それ以外の番号（6〜9、16〜21、26〜30、46〜49、56〜59）は master の画像を\n"
            "// 仮置きコピーしてあり、当たり判定も master と同一。")
new_note = ("// surface6〜9・46〜49・20: アスタロト メイド ポーズ＋座り（v2.27 で差し替え）。\n"
            "// surface16〜19・56〜59・21: フルフル メイド ポーズ＋座り（同上、頭身指示つき）。\n"
            "//   ポーズ・座りも色距離キーイング＋単体配置（下端1211）で作り、当たり判定は\n"
            "//   仮置き面の bbox → 新面 bbox の線形変換で最終画像の実測に付け替えた。\n"
            "// 残る仮置きは看板 26〜30 のみ（master の画像コピー、当たり判定も同一）。")
assert old_note in txt, "header note not found"
txt = txt.replace(old_note, new_note)
txt = txt.replace("第3シェル「maid」（2026-11-07、nar v2.26）", "第3シェル「maid」（2026-11-07、nar v2.26／ポーズ・座りは v2.27）")

lines = txt.splitlines()
cur = None
changed = {}
used = {}
for i, line in enumerate(lines):
    m = re.match(r"surface(\d+)\s*$", line.strip())
    if m:
        cur = int(m.group(1)); continue
    m = re.match(r"(collision\d+,)(\d+),(\d+),(\d+),(\d+),(\w+)", line.strip())
    if m and cur in TARGETS:
        if cur not in changed:
            ob = bbox_of(os.path.join(MAID, "surface%d.png" % cur))
            new_path = os.path.join(OUT, "maid", "surface%d.png" % cur)
            nb = bbox_of(new_path)
            size = Image.open(new_path).size
            changed[cur] = transform(old_blocks[cur], ob, nb, size)
            print("maid surface%d: old bbox %s -> new bbox %s size %s rects %s" % (cur, ob, nb, size, changed[cur]))
        rects = changed[cur]
        u = used.get(cur, 0)
        if u < len(rects):
            a, b, c, d, name = rects[u]
            lines[i] = "collision%d,%d,%d,%d,%d,%s" % (u, a, b, c, d, name)
            used[cur] = u + 1

assert sorted(changed) == sorted(TARGETS), f"changed={sorted(changed)}"
with open(txt_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("maid surfaces.txt updated for", sorted(changed))

for surf in sorted(TARGETS):
    for ext in ("png", "pna"):
        src = os.path.join(OUT, "maid", f"surface{surf}.{ext}")
        dst = os.path.join(MAID, f"surface{surf}.{ext}")
        shutil.copyfile(src, dst)
print("images copied into build/astaroth/shell/maid")
print("DONE")
