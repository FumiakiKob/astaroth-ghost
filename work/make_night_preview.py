import os, sys
from PIL import Image, ImageDraw, ImageFont

# 夜セット候補の選択用プレビューを作成する。
# work/night_candidates/ 内の A1..A4 / P1..P3 / N1..N3 を読み、
# グループ別シート3枚＋統合シート1枚を番号ラベル付きで出力する。
BASE = os.path.expanduser("~/workspace/astaroth-ghost/work/night_candidates")
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
FONT_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
THUMB_W = 416  # 元 832x1216 の半分
GROUPS = [
    ("A", "Astaroth - Negligee", ["A1", "A2", "A3", "A4"]),
    ("P", "Furfur - Pajamas", ["P1", "P2", "P3"]),
    ("N", "Furfur - Short negligee", ["N1", "N2", "N3"]),
]

def load(code):
    for f in sorted(os.listdir(BASE)):
        if f.startswith(code + "_") and f.endswith(".png"):
            return Image.open(os.path.join(BASE, f)).convert("RGB")
    raise FileNotFoundError(code)

def thumb(img):
    return img.resize((THUMB_W, int(img.height * THUMB_W / img.width)))

def label(draw, x, y, text, font=FONT):
    draw.rectangle([x, y, x + 118, y + 62], fill=(20, 20, 30))
    draw.text((x + 16, y + 6), text, font=font, fill=(255, 230, 120))

def sheet(codes, path, title=None):
    imgs = [(c, thumb(load(c))) for c in codes]
    cell_h = max(i.height for _, i in imgs)
    pad = 16
    title_h = 84 if title else 0
    W = pad + sum(i.width + pad for _, i in imgs)
    H = title_h + pad + cell_h + pad
    canvas = Image.new("RGB", (W, H), (38, 34, 48))
    d = ImageDraw.Draw(canvas)
    if title:
        d.text((pad, 14), title, font=FONT_BIG, fill=(240, 235, 255))
    x = pad
    for code, im in imgs:
        canvas.paste(im, (x, title_h + pad))
        label(d, x + 10, title_h + pad + 10, code)
        x += im.width + pad
    canvas.save(path)
    print("saved", path, canvas.size)

for key, title, codes in GROUPS:
    sheet(codes, os.path.join(BASE, f"preview_group_{key}.png"), title)

# 統合シート（3段）
rows = []
for key, title, codes in GROUPS:
    p = os.path.join(BASE, f"preview_group_{key}.png")
    rows.append(Image.open(p))
W = max(r.width for r in rows)
H = sum(r.height for r in rows)
canvas = Image.new("RGB", (W, H), (38, 34, 48))
y = 0
for r in rows:
    canvas.paste(r, (0, y))
    y += r.height
out = os.path.join(BASE, "preview_all.png")
canvas.save(out)
print("saved", out, canvas.size)
