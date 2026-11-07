import os
from PIL import Image, ImageDraw, ImageFont

# メイドシェル完成プレビュー: (1) 基本面12点の一覧シート
# (2) アスタロト0＋フルフル10 の並列（下端揃え・等倍）で身長感を見る。
# (3) 物差し比較: フルフル maid10 と master surface17（頭身基準）を並べる。
BASE = os.path.expanduser("~/workspace/astaroth-ghost")
BUILD = os.path.join(BASE, "build/astaroth/shell")
PREV = os.path.join(BASE, "work/maid_preview")
os.makedirs(PREV, exist_ok=True)
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
BG = (38, 34, 48, 255)

def sheet(items, path, cell_w=300, cell_h=470, cols=6):
    rows = (len(items) + cols - 1) // cols
    img = Image.new("RGBA", (cols * cell_w, rows * cell_h), BG)
    d = ImageDraw.Draw(img)
    for i, (label, im) in enumerate(items):
        r, c = divmod(i, cols)
        thumb = im.copy()
        thumb.thumbnail((cell_w - 10, cell_h - 40))
        x = c * cell_w + (cell_w - thumb.width) // 2
        y = r * cell_h + 30 + (cell_h - 40 - thumb.height) // 2
        img.alpha_composite(thumb, (x, y))
        d.text((c * cell_w + 8, r * cell_h + 8), str(label), fill=(255, 255, 120, 255))
    img.convert("RGB").save(path)
    print("saved", path, img.size)

def load(shell, surf):
    return Image.open(os.path.join(BUILD, shell, f"surface{surf}.png")).convert("RGBA")

sheet([(s, load("maid", s)) for s in (0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15)],
      os.path.join(PREV, "maid_base_all.png"), cols=6)

# 並列: 下端揃え等倍
asta = load("maid", 0)
fur = load("maid", 10)
H = 1216
canvas = Image.new("RGBA", (asta.width + fur.width + 30, H), BG)
canvas.alpha_composite(asta, (0, H - asta.height))
canvas.alpha_composite(fur, (asta.width + 30, H - fur.height))
canvas.convert("RGB").save(os.path.join(PREV, "maid_height_pair.png"))
print("saved", os.path.join(PREV, "maid_height_pair.png"), canvas.size)

# 物差し比較: maid フルフル10・11 と master17・night17
sheet([("maid10", load("maid", 10)), ("maid11", load("maid", 11)),
       ("master17(ref)", load("master", 17)), ("night10", load("night", 10)),
       ("maid0", load("maid", 0)), ("master0", load("master", 0))],
      os.path.join(PREV, "maid_balance_compare.png"), cols=6, cell_w=320)

# 光輪内側チェック: maid0 を市松模様に合成
chk = Image.new("RGB", (asta.width, asta.height), (255, 255, 255))
d = ImageDraw.Draw(chk)
s = 24
for yy in range(0, asta.height, s):
    for xx in range(0, asta.width, s):
        if (xx // s + yy // s) % 2 == 0:
            d.rectangle([xx, yy, xx + s - 1, yy + s - 1], fill=(170, 170, 170))
chk.paste(asta, (0, 0), asta)
chk.crop((0, 0, asta.width, 480)).save(os.path.join(PREV, "maid0_halo_checker.png"))
print("saved", os.path.join(PREV, "maid0_halo_checker.png"))
print("DONE")
