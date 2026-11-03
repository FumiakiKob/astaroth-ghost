import glob, os
from PIL import Image, ImageDraw

OUT = os.path.expanduser("~/ComfyUI/output")
DST = os.path.expanduser("~/ghost_work/furfur_sheets")
os.makedirs(DST, exist_ok=True)

FACE_BOX = (240, 40, 600, 420)

files = sorted(glob.glob(os.path.join(OUT, "furfur_base_seed*_00001_.png")))
print("files", [os.path.basename(f) for f in files])
assert len(files) == 3, files

# face sheet (2x crops)
crops = []
for f in files:
    im = Image.open(f).convert("RGB")
    c = im.crop(FACE_BOX)
    c = c.resize((c.width * 2, c.height * 2), Image.LANCZOS)
    d = ImageDraw.Draw(c)
    seed = os.path.basename(f).split("seed")[1].split("_")[0]
    d.rectangle([0, 0, 230, 34], fill=(0, 0, 0))
    d.text((8, 8), f"furfur base seed{seed}", fill=(255, 255, 0))
    crops.append(c)
sheet = Image.new("RGB", (crops[0].width * len(crops), crops[0].height), (30, 30, 30))
for i, c in enumerate(crops):
    sheet.paste(c, (i * c.width, 0))
sheet.save(os.path.join(DST, "furfur_base_faces.png"))

# full body strip (half scale) on dark canvas
strips = []
for f in files:
    im = Image.open(f).convert("RGB")
    strips.append(im.resize((416, 608), Image.LANCZOS))
strip = Image.new("RGB", (416 * len(strips), 608), (30, 30, 30))
for i, c in enumerate(strips):
    strip.paste(c, (i * 416, 0))
strip.save(os.path.join(DST, "furfur_base_full.png"))
print("DONE", os.listdir(DST))
