import os
import numpy as np
from PIL import Image, ImageDraw

BASE = os.path.expanduser("~/workspace/astaroth-ghost")
OUT = os.path.join(BASE, "work/v224_out")
OLD = os.path.join(BASE, "work/v224_old_shell")
BUILD = os.path.join(BASE, "build/astaroth/shell")
PREV = os.path.join(BASE, "work/v224_preview")
os.makedirs(PREV, exist_ok=True)

def sheet(items, path, cell_w=300, cell_h=470, cols=6, bg=(35, 35, 56, 255)):
    rows = (len(items) + cols - 1) // cols
    sheet_img = Image.new("RGBA", (cols * cell_w, rows * cell_h), bg)
    d = ImageDraw.Draw(sheet_img)
    for i, (label, img) in enumerate(items):
        r, c = divmod(i, cols)
        thumb = img.copy()
        thumb.thumbnail((cell_w - 10, cell_h - 40))
        x = c * cell_w + (cell_w - thumb.width) // 2
        y = r * cell_h + 30 + (cell_h - 40 - thumb.height) // 2
        sheet_img.alpha_composite(thumb, (x, y))
        d.text((c * cell_w + 8, r * cell_h + 8), str(label), fill=(255, 255, 120, 255))
    sheet_img.convert("RGB").save(path)
    print("saved", path, sheet_img.size)

def load_out(surf):
    return Image.open(os.path.join(OUT, "night", f"surface{surf}.png")).convert("RGBA")

def load_old(surf):
    return Image.open(os.path.join(OLD, "night", f"surface{surf}.png")).convert("RGBA")

def load_build(shell, surf):
    return Image.open(os.path.join(BUILD, shell, f"surface{surf}.png")).convert("RGBA")

# 新しい夜フルフル基本面の一覧
sheet([(s, load_out(s)) for s in (10, 11, 12, 13, 14, 15)],
      os.path.join(PREV, "night_furfur_base_new.png"), cols=6)

# 新旧比較（10のみ）＋基準面（現行 night17 = v2.23 で頭身是正済み）
sheet([("old10", load_old(10)), ("new10", load_out(10)),
       ("night17(v2.23)", load_build("night", 17)), ("old11", load_old(11)), ("new11", load_out(11))],
      os.path.join(PREV, "night_furfur_compare.png"), cols=5, cell_w=320)

# 身長感の並列比較: 夜アスタロト0 と新フルフル10 を下端揃え・等倍で横並び
asta = load_build("night", 0)
fur = load_out(10)
H = 1216
canvas = Image.new("RGBA", (asta.width + fur.width + 30, H), (35, 35, 56, 255))
canvas.alpha_composite(asta, (0, H - asta.height))
canvas.alpha_composite(fur, (asta.width + 30, H - fur.height))
canvas.convert("RGB").save(os.path.join(PREV, "night_height_pair.png"))
print("saved", os.path.join(PREV, "night_height_pair.png"), canvas.size)
print("DONE")
