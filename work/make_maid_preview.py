import os
from PIL import Image, ImageDraw, ImageFont

# メイド服シェル方向確認サンプルの統合プレビュー。
# キーイング済み3点を暗背景 (38,34,48) に合成し、ラベル付きで横並びにする。
BASE = os.path.expanduser("~/workspace/astaroth-ghost/work/maid_candidates")
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
FONT_CAP = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
FONT_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
THUMB_W = 416
BG = (38, 34, 48)
ITEMS = [
    ("M1", "M1_seed20261121.png", "Astaroth: classic"),
    ("M2", "M2_seed111701.png", "Furfur: pink"),
    ("M3", "M3_seed777701.png", "Furfur: classic"),
]

def thumb(img):
    return img.resize((THUMB_W, int(img.height * THUMB_W / img.width)))

def label(draw, x, y, text):
    draw.rectangle([x, y, x + 118, y + 62], fill=(20, 20, 30))
    draw.text((x + 16, y + 6), text, font=FONT, fill=(255, 230, 120))

imgs = []
for code, fn, caption in ITEMS:
    im = Image.open(os.path.join(BASE, fn)).convert("RGBA")
    imgs.append((code, caption, thumb(im)))

cell_h = max(i.height for _, _, i in imgs)
pad = 16
title_h = 84
cap_h = 64
W = pad + sum(i.width + pad for _, _, i in imgs)
H = title_h + pad + cell_h + cap_h + pad
canvas = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(canvas)
d.text((pad, 14), "Maid shell samples (2026-11-06)", font=FONT_BIG, fill=(240, 235, 255))
x = pad
for code, caption, im in imgs:
    bgcell = Image.new("RGBA", (im.width, im.height), BG + (255,))
    bgcell.alpha_composite(im)
    canvas.paste(bgcell.convert("RGB"), (x, title_h + pad))
    label(d, x + 10, title_h + pad + 10, code)
    d.text((x + 6, title_h + pad + cell_h + 14), caption, font=FONT_CAP, fill=(220, 215, 235))
    x += im.width + pad
out = os.path.join(BASE, "preview_all.png")
canvas.save(out)
print("saved", out, canvas.size)
