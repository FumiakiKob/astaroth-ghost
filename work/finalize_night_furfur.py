import sys, os, json
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

# usage: finalize_furfur.py <src_dir> <out_dir>
# フルフル surface10〜15 の一括キーイング＋正規化。
# キーイング本体は finalize_expr.py（アスタロト）と同一処理。
# 正規化はフルフル専用: 全6枚で「solid bbox の中心 x」と「solid bbox の下端 y」を
# 統一して配置し、全枚同一寸法（H=1216、W は翼幅から算出）にする。
src_dir, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)

JOBS = [
    (10, "night_expr_NF10_seed121601_00001_.png"),
    (11, "night_expr_NF11_seed121601_00001_.png"),
    (12, "night_expr_NF12_seed121601_00001_.png"),
    (13, "night_expr_NF13_seed121601_00001_.png"),
    (14, "night_expr_NF14_seed121601_00001_.png"),
    (15, "night_expr_NF15_seed121601_00001_.png"),
]

def key_image(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    greenness = G - np.maximum(R, B)

    # 黄緑軸: 背景は B が極端に低い（min(R,G)-B が 150超）。肌は最大でも 45 程度、
    # 白髪・翼の陰影は負値なので、yel>=60 も背景候補に含める（脚の間など
    # 影になった囲み背景は greenness が 10 程度まで落ち、緑軸だけでは漏れる）。
    yel = np.minimum(R, G) - B
    bg_like = (greenness >= 18) | (yel >= 60)
    lab, n = ndimage.label(bg_like)
    border_labels = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    border_labels.discard(0)
    bg = np.isin(lab, list(border_labels))
    alpha = (~bg).astype(np.float32) * 255.0

    # フルフルの背景は黄緑（greenness 中央値≈42、本体内部はほぼ 0 以下）。
    # アスタロト用（純緑 greenness≈200 前提）の減衰曲線では囲まれた背景が
    # 半透明で残るため、実測に基づく ramp（22→32 で 0）に差し替える。
    factor = np.clip((32.0 - greenness) / (32.0 - 22.0), 0.0, 1.0)
    alpha = alpha * np.where(greenness > 22, factor, 1.0)
    yfactor = np.clip((60.0 - yel) / (60.0 - 35.0), 0.0, 1.0)
    alpha = alpha * np.where(yel > 35, yfactor, 1.0)

    alpha_img = Image.fromarray(alpha.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.6))
    alpha = np.asarray(alpha_img).astype(np.float32)

    # detached-component cleanup: フルフルには光輪がないので、アスタロト用の
    # 「>=2000px は保持」ルールは使わない（surface12 の驚きマークが約2500pxで
    # 残ってしまったため）。最大成分（本体＋翼）に加え、翼が万一分離した場合に
    # 備えて翼スケールの成分（>=20000px、または幅250以上かつ高さ120以上）だけ保持する。
    mask = alpha > 128
    lab2, n2 = ndimage.label(mask)
    dropped = []
    if n2 > 1:
        sizes = ndimage.sum(mask, lab2, range(1, n2 + 1))
        largest = int(np.argmax(sizes)) + 1
        keep_labels = {largest}
        for i, sz in enumerate(sizes, start=1):
            if i == largest:
                continue
            ys_c, xs_c = np.where(lab2 == i)
            bw = int(xs_c.max() - xs_c.min() + 1)
            bh = int(ys_c.max() - ys_c.min() + 1)
            if sz >= 20000 or (bw >= 250 and bh >= 120):
                keep_labels.add(i)
                print(f"  kept extra component label={i} size={int(sz)} w={bw} h={bh}")
            else:
                dropped.append((i, int(sz), bw, bh))
        keep = np.isin(lab2, list(keep_labels))
        alpha = np.where(keep, alpha, 0.0)

    out = a.copy()
    spill = (greenness > 12) & (alpha > 0)
    cap = np.maximum(R, B) + 10
    out[..., 1] = np.where(spill, np.minimum(G, cap), G)

    rgba = np.dstack([out, alpha]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA"), dropped

# ---- pass 1: key all, measure solid bboxes ----
keyed = {}
for surf, fname in JOBS:
    img, dropped = key_image(os.path.join(src_dir, fname))
    al = np.asarray(img)[..., 3]
    ys, xs = np.where(al > 128)
    bb = (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))
    keyed[surf] = (img, bb)
    print(f"surface{surf} src bbox x:{bb[0]}..{bb[1]} y:{bb[2]}..{bb[3]} dropped={dropped}", flush=True)

# ---- unified placement ----
H = 1216
BOTTOM = 1211  # アスタロトの bbox 下端に合わせる
MARGIN = 6
need_half = 0.0
for surf, (img, bb) in keyed.items():
    cx = (bb[0] + bb[1]) / 2.0
    need_half = max(need_half, cx - bb[0], bb[1] - cx)
W = int(np.ceil(need_half * 2)) + 1 + MARGIN * 2
CX = (W - 1) / 2.0
print(f"canvas W={W} H={H} center_x={CX} bottom={BOTTOM}", flush=True)

report = {}
for surf, (img, bb) in keyed.items():
    cx = (bb[0] + bb[1]) / 2.0
    dx = int(round(CX - cx))
    dy = int(BOTTOM - bb[3])
    top = bb[2] + dy
    assert top >= 0, f"surface{surf} top overflow {top}"
    canvas = Image.new("RGBA", (W, H), (0, 255, 0, 0))
    canvas.paste(img, (dx, dy))
    arr = np.asarray(canvas).copy()
    al = arr[..., 3]
    arr[..., 0] = np.where(al == 0, 0, arr[..., 0])
    arr[..., 1] = np.where(al == 0, 255, arr[..., 1])
    arr[..., 2] = np.where(al == 0, 0, arr[..., 2])
    final = Image.fromarray(arr, "RGBA")
    png_path = os.path.join(out_dir, f"surface{surf}.png")
    final.save(png_path)
    pna = Image.fromarray(al.astype(np.uint8), "L")
    pna_path = os.path.join(out_dir, f"surface{surf}.pna")
    pna.save(pna_path, format="PNG")

    # verification: pna == alpha, corners
    pna_back = np.asarray(Image.open(pna_path))
    ys, xs = np.where(al > 128)
    corners = [int(al[0, 0]), int(al[0, -1]), int(al[-1, 0]), int(al[-1, -1])]
    info = {
        "size": [W, H], "dx": dx, "dy": dy,
        "bbox": [int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())],
        "corners_alpha": corners,
        "pna_matches_alpha": bool(np.array_equal(pna_back, al.astype(np.uint8))),
        "transparent_rgb_unique": np.unique(arr[al == 0].reshape(-1, 4), axis=0).tolist(),
    }
    report[surf] = info
    print(f"surface{surf} saved dx={dx} dy={dy} bbox={info['bbox']} corners={corners} pna_ok={info['pna_matches_alpha']}", flush=True)

    # dark previews
    bgc = Image.new("RGBA", final.size, (35, 35, 56, 255))
    comp = Image.alpha_composite(bgc, final).convert("RGB")
    comp.save(os.path.join(out_dir, f"surface{surf}_dark.png"))
    comp.crop((0, 0, W, 560)).save(os.path.join(out_dir, f"surface{surf}_dark_upper.png"))

with open(os.path.join(out_dir, "furfur_finalize_report.json"), "w") as f:
    json.dump(report, f, indent=1)
print("ALL DONE")
