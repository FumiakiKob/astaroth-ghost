import os
from PIL import Image, ImageDraw

BASE = os.path.expanduser("~/workspace/astaroth-ghost")
OUT = os.path.join(BASE, "work/maid_pose_out")
BUILD = os.path.join(BASE, "build/astaroth/shell/maid")
PREV = os.path.join(BASE, "work/maid_pose_preview")
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
    return Image.open(os.path.join(OUT, "maid", f"surface{surf}.png")).convert("RGBA")

def load_build(surf):
    return Image.open(os.path.join(BUILD, f"surface{surf}.png")).convert("RGBA")

new = [6, 7, 8, 9, 46, 47, 48, 49, 16, 17, 18, 19, 56, 57, 58, 59, 20, 21]
sheet([(s, load_out(s)) for s in new], os.path.join(PREV, "maid_poses_new.png"), cols=6)

# バランス確認: maid 基本面（0/10）と新ポーズ代表（17/20/21）を並べる
sheet([("base0", load_build(0)), ("new17", load_out(17)), ("new20", load_out(20)),
       ("base10", load_build(10)), ("new16", load_out(16)), ("new21", load_out(21))],
      os.path.join(PREV, "maid_pose_balance.png"), cols=6, cell_w=320)
print("DONE previews")
