import sys, os, json
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from scipy import ndimage

# usage: finalize_sign.py <src_png> <out_dir>
# 不在看板（surface26〜30）のキーイング＋配置＋文字合成。
# 土台は文字なしの木製立て看板（gen_sign.py、seed26101）。
# キーイングは finalize_expr.py（アスタロト用）と同一方式。
# 配置: キャンバスは surface0 と同じ 478x1216、看板の高さ 1000px に
# スケールし、下端を既存シェルの接地ライン y=1211 に合わせる。
# 文字は板の矩形を実測して PIL で後入れする（AI に描かせない）。

src_path, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)

FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
INK = (74, 44, 24, 255)
INK_SHADOW = (74, 44, 24, 110)

SIGNS = [
    (26, "入浴中", "覗くと業火で丸焼きよ"),
    (27, "外出中", "留守は任せなさい"),
    (28, "勉強中", "邪魔をすると祟るわよ"),
    (29, "就寝中", "夢の中では静かにね"),
    (30, "お留守番中", "早く帰ってきてねー！"),
]

def key_image(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    greenness = G - np.maximum(R, B)

    bg_like = greenness >= 18
    lab, n = ndimage.label(bg_like)
    border_labels = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    border_labels.discard(0)
    bg = np.isin(lab, list(border_labels))
    alpha = (~bg).astype(np.float32) * 255.0

    factor = np.clip((70.0 - greenness) / (70.0 - 25.0), 0.0, 1.0)
    alpha = alpha * np.where(greenness > 25, factor, 1.0)

    alpha_img = Image.fromarray(alpha.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.6))
    alpha = np.asarray(alpha_img).astype(np.float32)

    # 最大成分（看板本体）だけを残す
    mask = alpha > 128
    lab2, n2 = ndimage.label(mask)
    dropped = []
    if n2 > 1:
        sizes = ndimage.sum(mask, lab2, range(1, n2 + 1))
        largest = int(np.argmax(sizes)) + 1
        for i, sz in enumerate(sizes, start=1):
            if i != largest:
                dropped.append((i, int(sz)))
        alpha = np.where(lab2 == largest, alpha, 0.0)

    out = a.copy()
    spill = (greenness > 12) & (alpha > 0)
    cap = np.maximum(R, B) + 10
    out[..., 1] = np.where(spill, np.minimum(G, cap), G)
    rgba = np.dstack([out, alpha]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA"), dropped

img, dropped = key_image(src_path)
print("dropped components:", dropped)

# ---- 配置（478x1216、下端 1211、高さ 1000 にスケール） ----
W, H, BOTTOM, SIGN_H = 478, 1216, 1211, 1000
al0 = np.asarray(img)[..., 3]
ys, xs = np.where(al0 > 128)
bb = (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))
scale = SIGN_H / float(bb[3] - bb[2] + 1)
new_w = int(round((bb[1] - bb[0] + 1) * scale))
img_r = img.resize((img.width * 0 + int(round(img.width * scale)), int(round(img.height * scale))), Image.LANCZOS)
al_r = np.asarray(img_r)[..., 3]
ys_r, xs_r = np.where(al_r > 128)
bb_r = (int(xs_r.min()), int(xs_r.max()), int(ys_r.min()), int(ys_r.max()))
dx = int(round((W - 1) / 2.0 - (bb_r[0] + bb_r[1]) / 2.0))
dy = int(BOTTOM - bb_r[3])
canvas = Image.new("RGBA", (W, H), (0, 255, 0, 0))
canvas.paste(img_r, (dx, dy))
arr = np.asarray(canvas).copy()
al = arr[..., 3]
arr[..., 0] = np.where(al == 0, 0, arr[..., 0])
arr[..., 1] = np.where(al == 0, 255, arr[..., 1])
arr[..., 2] = np.where(al == 0, 0, arr[..., 2])
base = Image.fromarray(arr, "RGBA")
print(f"src_bbox={bb} scale={scale:.3f} placed_bbox={[bb_r[0]+dx, bb_r[1]+dx, bb_r[2]+dy, bb_r[3]+dy]}")

# ---- 板の矩形を実測（幅が最大幅の80%以上の行の連続範囲） ----
alB = np.asarray(base)[..., 3]
widths = (alB > 128).sum(axis=1)
maxw = int(widths.max())
rows = np.where(widths >= maxw * 0.8)[0]
board_y0, board_y1 = int(rows.min()), int(rows.max())
xs_b = np.where(alB[board_y0:board_y1 + 1] > 128)[1]
board_x0, board_x1 = int(xs_b.min()), int(xs_b.max())
board = (board_x0, board_y0, board_x1, board_y1)
print("board rect:", board)
bw = board_x1 - board_x0 + 1
bh = board_y1 - board_y0 + 1
cx = (board_x0 + board_x1) / 2.0

def draw_centered(draw, y_center, text, font):
    tb = draw.textbbox((0, 0), text, font=font)
    tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    x = cx - tw / 2.0 - tb[0]
    y = y_center - th / 2.0 - tb[1]
    draw.text((x + 2, y + 3), text, font=font, fill=INK_SHADOW)
    draw.text((x, y), text, font=font, fill=INK)
    return tw

report = {"board": board, "signs": {}}
previews = []
for num, title, sub in SIGNS:
    surf = base.copy()
    d = ImageDraw.Draw(surf)
    # タイトル文字サイズ: 板幅の 82% に収まるよう自動調整
    size = 120
    while size > 20:
        f = ImageFont.truetype(FONT, size, index=0)
        tb = d.textbbox((0, 0), title, font=f)
        if tb[2] - tb[0] <= bw * 0.82:
            break
        size -= 4
    f_title = ImageFont.truetype(FONT, size, index=0)
    draw_centered(d, board_y0 + bh * 0.30, title, f_title)
    size2 = 40
    while size2 > 14:
        f2 = ImageFont.truetype(FONT, size2, index=0)
        tb = d.textbbox((0, 0), sub, font=f2)
        if tb[2] - tb[0] <= bw * 0.86:
            break
        size2 -= 2
    f_sub = ImageFont.truetype(FONT, size2, index=0)
    draw_centered(d, board_y0 + bh * 0.68, sub, f_sub)

    a2 = np.asarray(surf)[..., 3]
    png_path = os.path.join(out_dir, f"surface{num}.png")
    surf.save(png_path)
    pna = Image.fromarray(a2.astype(np.uint8), "L")
    pna_path = os.path.join(out_dir, f"surface{num}.pna")
    pna.save(pna_path, format="PNG")
    pna_back = np.asarray(Image.open(pna_path))
    corners = [int(a2[0, 0]), int(a2[0, -1]), int(a2[-1, 0]), int(a2[-1, -1])]
    ok = bool(np.array_equal(pna_back, a2.astype(np.uint8)))
    report["signs"][num] = {"title_px": size, "sub_px": size2, "corners": corners, "pna_ok": ok}
    print(f"surface{num}: title_px={size} sub_px={size2} corners={corners} pna_ok={ok}")
    bgc = Image.new("RGBA", surf.size, (35, 35, 56, 255))
    comp = Image.alpha_composite(bgc, surf).convert("RGB")
    comp.save(os.path.join(out_dir, f"surface{num}_dark.png"))
    previews.append(comp)

# コンタクトシート（5枚横並び、半分に縮小）
sheet = Image.new("RGB", (W // 2 * 5 + 24, H // 2 + 8), (24, 24, 36))
for i, comp in enumerate(previews):
    sheet.paste(comp.resize((W // 2, H // 2), Image.LANCZOS), (4 + i * (W // 2 + 4), 4))
sheet.save(os.path.join(out_dir, "sign_contact.png"))

# グリッド付き（26のみ、当たり判定の実測用）
grid = previews[0].copy()
gd = ImageDraw.Draw(grid)
for gx in range(0, W, 50):
    gd.line([(gx, 0), (gx, H)], fill=(255, 80, 80) if gx % 200 == 0 else (120, 120, 160), width=1)
    gd.text((gx + 2, 4), str(gx), fill=(255, 255, 120))
for gy in range(0, H, 50):
    gd.line([(0, gy), (W, gy)], fill=(255, 80, 80) if gy % 200 == 0 else (120, 120, 160), width=1)
    gd.text((4, gy + 2), str(gy), fill=(255, 255, 120))
grid.save(os.path.join(out_dir, "surface26_grid.png"))

with open(os.path.join(out_dir, "sign_finalize_report.json"), "w") as f:
    json.dump(report, f, indent=1, ensure_ascii=False)
print("ALL DONE")
