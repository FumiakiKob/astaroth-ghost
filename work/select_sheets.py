import glob, os, sys
from PIL import Image, ImageDraw

OUT = os.path.expanduser("~/ComfyUI/output")
DST = os.path.expanduser("~/ghost_work/sheets")
os.makedirs(DST, exist_ok=True)

# face crop region guess for 832x1216 full body (halo+head+shoulders)
FACE_BOX = (240, 40, 600, 420)

for expr in range(1, 6):
    files = sorted(glob.glob(os.path.join(OUT, f"astaroth_expr{expr}_seed*_00001_.png")))
    if not files:
        print("expr", expr, "NO FILES")
        continue
    # face sheet
    crops = []
    for f in files:
        im = Image.open(f).convert("RGB")
        c = im.crop(FACE_BOX)
        c = c.resize((c.width * 2, c.height * 2), Image.LANCZOS)
        d = ImageDraw.Draw(c)
        seed = os.path.basename(f).split("seed")[1].split("_")[0]
        d.rectangle([0, 0, 190, 34], fill=(0, 0, 0))
        d.text((8, 8), f"expr{expr} seed{seed}", fill=(255, 255, 0))
        crops.append(c)
    sheet = Image.new("RGB", (crops[0].width * len(crops), crops[0].height), (30, 30, 30))
    for i, c in enumerate(crops):
        sheet.paste(c, (i * c.width, 0))
    sheet.save(os.path.join(DST, f"expr{expr}_faces.png"))
    # full body strip (half scale)
    strips = []
    for f in files:
        im = Image.open(f).convert("RGB")
        strips.append(im.resize((416, 608), Image.LANCZOS))
    strip = Image.new("RGB", (416 * len(strips), 608), (30, 30, 30))
    for i, c in enumerate(strips):
        strip.paste(c, (i * 416, 0))
    strip.save(os.path.join(DST, f"expr{expr}_full.png"))
    print("expr", expr, "files", [os.path.basename(f) for f in files])
print("DONE")
