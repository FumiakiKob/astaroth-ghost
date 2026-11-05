import os
from PIL import Image, ImageDraw, ImageFont

# 夜セット候補・第2便の選択用プレビューを作成する。
# work/night_candidates/ 内の A5..A8 / P4..P6 / N4..N6 を読み、
# 3段コラージュ preview_round2.png を番号ラベル付きで出力する。
BASE = os.path.expanduser("~/workspace/astaroth-ghost/work/night_candidates")
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
FONT_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
THUMB_W = 416  # 元 832x1216 の半分
GROUPS = [
    ("Astaroth - Negligee (round 2)", ["A5", "A6", "A7", "A8"]),
    ("Furfur - Pajamas (round 2)", ["P4", "P5", "P6"]),
    ("Furfur - Short negligee (round 2)", ["N4", "N5", "N6"]),
]

def load(code):
    for f in sorted(os.listdir(BASE)):
        if f.startswith(code + "_") and f.endswith(".png"):
            return Image.open(os.path.join(BASE, f)).convert("RGB")
    raise FileNotFoundError(code)

def thumb(img):
    return img.resize((THUMB_W, int(img.height * THUMB_W / img.width)))

def label(draw, x, y, text):
    draw.rectangle([x, y, x + 118, y + 62], fill=(20, 20, 30))
    draw.text((x + 16, y + 6), text, font=FONT, fill=(255, 230, 120))

def sheet(codes, title):
    imgs = [(c, thumb(load(c))) for c in codes]
    cell_h = max(i.height for _, i in imgs)
    pad = 16
    title_h = 84
    W = pad + sum(i.width + pad for _, i in imgs)
    H = title_h + pad + cell_h + pad
    canvas = Image.new("RGB", (W, H), (38, 34, 48))
    d = ImageDraw.Draw(canvas)
    d.text((pad, 14), title, font=FONT_BIG, fill=(240, 235, 255))
    x = pad
    for code, im in imgs:
        canvas.paste(im, (x, title_h + pad))
        label(d, x + 10, title_h + pad + 10, code)
        x += im.width + pad
    return canvas

rows = [sheet(codes, title) for title, codes in GROUPS]
W = max(r.width for r in rows)
H = sum(r.height for r in rows)
canvas = Image.new("RGB", (W, H), (38, 34, 48))
y = 0
for r in rows:
    canvas.paste(r, (0, y))
    y += r.height
out = os.path.join(BASE, "preview_round2.png")
canvas.save(out)
print("saved", out, canvas.size)
