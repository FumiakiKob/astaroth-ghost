import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.expanduser("~/workspace/astaroth-ghost")
OUT = os.path.join(BASE, "work/v223_out")
OLD = os.path.join(BASE, "work/v223_old_shell")
PREV = os.path.join(BASE, "work/v223_preview")
os.makedirs(PREV, exist_ok=True)

def checker(size, cell=16):
    w, h = size
    img = np.zeros((h, w, 3), dtype=np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    img[((xx // cell) + (yy // cell)) % 2 == 0] = (200, 200, 200)
    img[((xx // cell) + (yy // cell)) % 2 == 1] = (120, 120, 120)
    return Image.fromarray(img, "RGB").convert("RGBA")

def sheet(items, path, cell_w=300, cell_h=470, cols=6, bg=(35, 35, 56, 255), label_prefix=""):
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
        d.text((c * cell_w + 8, r * cell_h + 8), f"{label_prefix}{label}", fill=(255, 255, 120, 255))
    sheet_img.convert("RGB").save(path)
    print("saved", path, sheet_img.size)

def load(root, shell, surf):
    return Image.open(os.path.join(root, shell, f"surface{surf}.png")).convert("RGBA")

# 夜ポーズ一覧（新規分）
night_new = [6, 7, 8, 9, 46, 47, 48, 49, 16, 17, 18, 19, 56, 57, 58, 59, 20, 21]
sheet([(s, load(OUT, "night", s)) for s in night_new], os.path.join(PREV, "night_poses_new.png"), cols=6)

# 夜基本面の再キーイング前後（0と10）
sheet([(f"old{s}", load(OLD, "night", s)) for s in (0, 10)] + [(f"new{s}", load(OUT, "night", s)) for s in (0, 10)],
      os.path.join(PREV, "night_base_rekey_compare.png"), cols=4)

# 光輪内側の検証: night surface0 を市松模様へ合成し上部を拡大
s0 = load(OUT, "night", 0)
bg = checker(s0.size)
comp = Image.alpha_composite(bg, s0)
comp.crop((150, 0, 620, 330)).resize((940, 660)).save(os.path.join(PREV, "night0_halo_checker.png"))
comp.convert("RGB").save(os.path.join(PREV, "night0_checker_full.png"))
print("halo checker saved")

# 頭身比較: 通常フルフル 新旧（10,17）＋アスタロト0と並べる
if os.path.exists(os.path.join(OUT, "master", "surface10.png")):
    items = [("old10", load(OLD, "master", 10)), ("new10", load(OUT, "master", 10)),
             ("old17", load(OLD, "master", 17)), ("new17", load(OUT, "master", 17)),
             ("asta0", load(OLD, "master", 0)), ("new21", load(OUT, "master", 21))]
    sheet(items, os.path.join(PREV, "master_furfur_compare.png"), cols=6, cell_w=320)
    sheet([(s, load(OUT, "master", s)) for s in (10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 56, 57, 58, 59, 21)],
          os.path.join(PREV, "master_furfur_new_all.png"), cols=5)
print("DONE")
