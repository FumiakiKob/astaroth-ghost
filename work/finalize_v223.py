import sys, os, json, re
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage

# v2.23 後処理: 色距離ベースのキーイング（囲み領域にも届く方式）
# - 境界フラッドフィルで外側背景を除去
# - 全画素に緑優位度ランプを適用し、光輪内側・ツインテール内側等の囲まれた背景も除去
# - キー色（四隅サンプルの中央値）への色距離が小さい画素は囲まれていても除去
# - デスピル強化（縁の緑み抑制）
# 配置は参照面（差し替え前の同番号面）の solid bbox へ中心・下端を合わせる方式と、
# ポーズ用の単体配置（bbox+マージン、下端1211）方式。
# 当たり判定は旧面の bbox → 新面の bbox の線形変換で実測ベースに付け替える。

RAW = os.path.expanduser("~/workspace/astaroth-ghost/work/v223_raw")
OLD = os.path.expanduser("~/workspace/astaroth-ghost/work/v223_old_shell")
OUTROOT = os.path.expanduser("~/workspace/astaroth-ghost/work/v223_out")

def key_image(path, mode):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    greenness = G - np.maximum(R, B)
    yel = np.minimum(R, G) - B
    # キー色: 四隅 20x20 の中央値
    corners = np.concatenate([
        a[:20, :20].reshape(-1, 3), a[:20, -20:].reshape(-1, 3),
        a[-20:, :20].reshape(-1, 3), a[-20:, -20:].reshape(-1, 3)])
    key = np.median(corners, axis=0)
    dist = np.sqrt(((a - key) ** 2).sum(axis=2))

    bg_like = (greenness >= 18) | (yel >= 60)
    lab, n = ndimage.label(bg_like)
    border_labels = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    border_labels.discard(0)
    bg = np.isin(lab, list(border_labels))
    alpha = (~bg).astype(np.float32) * 255.0

    if mode == "furfur":
        factor = np.clip((32.0 - greenness) / (32.0 - 22.0), 0.0, 1.0)
        alpha = alpha * np.where(greenness > 22, factor, 1.0)
        yfactor = np.clip((60.0 - yel) / (60.0 - 35.0), 0.0, 1.0)
        alpha = alpha * np.where(yel > 35, yfactor, 1.0)
    else:
        factor = np.clip((70.0 - greenness) / (70.0 - 25.0), 0.0, 1.0)
        alpha = alpha * np.where(greenness > 25, factor, 1.0)
    # 床影: 暗く緑優位な画素は影として除去（ガウン裾に接していても落とす）
    shadow = (greenness >= 6) & (np.maximum(np.maximum(R, G), B) <= 120)
    alpha = np.where(shadow, 0.0, alpha)
    # 囲まれた背景: キー色に近い画素は連結性によらず除去（色距離ベース）
    enclosed = (dist < 55.0) & (greenness > 12)
    alpha = np.where(enclosed, 0.0, alpha)
    near_key = (dist < 110.0) & (greenness > 8)
    alpha = alpha * np.where(near_key, np.clip((dist - 55.0) / 55.0, 0.0, 1.0), 1.0)

    alpha_img = Image.fromarray(alpha.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.6))
    alpha = np.asarray(alpha_img).astype(np.float32)

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
            bw = int(xs_c.max() - xs_c.min() + 1); bh = int(ys_c.max() - ys_c.min() + 1)
            if mode == "furfur":
                keep = sz >= 20000 or (bw >= 250 and bh >= 120)
            else:
                keep = sz >= 2000 or bw >= 110
            if keep:
                keep_labels.add(i)
            else:
                dropped.append((i, int(sz), bw, bh))
        keep_mask = np.isin(lab2, list(keep_labels))
        alpha = np.where(keep_mask, alpha, 0.0)

    out = a.copy()
    spill = (greenness > 8) & (alpha > 0)
    cap = np.maximum(R, B) + 8
    out[..., 1] = np.where(spill, np.minimum(G, cap), G)
    rgba = np.dstack([out, alpha]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA"), dropped

def solid_bbox(img):
    al = np.asarray(img)[..., 3]
    ys, xs = np.where(al > 128)
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))

def green_residue(img):
    arr = np.asarray(img).astype(np.float32)
    al = arr[..., 3]
    g = arr[..., 1] - np.maximum(arr[..., 0], arr[..., 2])
    return int(((al > 128) & (g > 30)).sum())

def save_surface(img, out_dir, surf):
    os.makedirs(out_dir, exist_ok=True)
    arr = np.asarray(img).copy()
    al = arr[..., 3]
    arr[..., 0] = np.where(al == 0, 0, arr[..., 0])
    arr[..., 1] = np.where(al == 0, 255, arr[..., 1])
    arr[..., 2] = np.where(al == 0, 0, arr[..., 2])
    final = Image.fromarray(arr, "RGBA")
    final.save(os.path.join(out_dir, f"surface{surf}.png"))
    Image.fromarray(al.astype(np.uint8), "L").save(os.path.join(out_dir, f"surface{surf}.pna"), format="PNG")
    pna_back = np.asarray(Image.open(os.path.join(out_dir, f"surface{surf}.pna")))
    corners = [int(al[0, 0]), int(al[0, -1]), int(al[-1, 0]), int(al[-1, -1])]
    return {"size": list(final.size), "bbox": list(solid_bbox(final)), "corners": corners,
            "pna_ok": bool(np.array_equal(pna_back, al.astype(np.uint8))),
            "green_residue_px": green_residue(final)}

def place_align(keyed, ref_img):
    """参照面と同寸キャンバスに、bbox中心x・下端yを合わせて配置"""
    kb = solid_bbox(keyed); rb = solid_bbox(ref_img)
    W, H = ref_img.size
    dx = int(round((rb[0] + rb[1]) / 2.0 - (kb[0] + kb[1]) / 2.0))
    dy = int(rb[3] - kb[3])
    canvas = Image.new("RGBA", (W, H), (0, 255, 0, 0))
    canvas.paste(keyed, (dx, dy))
    return canvas, dx, dy

def place_single(keyed, bottom=1211):
    kb = solid_bbox(keyed)
    bw = kb[1] - kb[0] + 1
    W = bw + 16; H = 1216
    dy = bottom - kb[3]
    if kb[2] + dy < 0:
        dy = -kb[2]
    dx = -kb[0] + 8
    canvas = Image.new("RGBA", (W, H), (0, 255, 0, 0))
    canvas.paste(keyed, (dx, dy))
    return canvas, dx, dy

def place_group(items, bottom=1211):
    """items: [(surf, keyed)] を中心・下端統一で配置（フルフル基本面用）"""
    H = 1216; MARGIN = 6
    need_half = 0.0
    for surf, img in items:
        bb = solid_bbox(img)
        cx = (bb[0] + bb[1]) / 2.0
        need_half = max(need_half, cx - bb[0], bb[1] - cx)
    W = int(np.ceil(need_half * 2)) + 1 + MARGIN * 2
    CX = (W - 1) / 2.0
    out = {}
    for surf, img in items:
        bb = solid_bbox(img)
        dx = int(round(CX - (bb[0] + bb[1]) / 2.0)); dy = int(bottom - bb[3])
        canvas = Image.new("RGBA", (W, H), (0, 255, 0, 0))
        canvas.paste(img, (dx, dy))
        out[surf] = canvas
    return out

def parse_collisions(surfaces_txt):
    res = {}
    cur = None
    for line in surfaces_txt.splitlines():
        m = re.match(r"surface(\d+)\s*$", line.strip())
        if m:
            cur = int(m.group(1)); res[cur] = []
            continue
        m = re.match(r"collision(\d+),(\d+),(\d+),(\d+),(\d+),(\w+)", line.strip())
        if m and cur is not None:
            res[cur].append((int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), m.group(6)))
    return res

def transform_collisions(old_rects, old_bb, new_bb):
    ox0, ox1, oy0, oy1 = old_bb; nx0, nx1, ny0, ny1 = new_bb
    sx = (nx1 - nx0) / max(1, (ox1 - ox0)); sy = (ny1 - ny0) / max(1, (oy1 - oy0))
    out = []
    for (x0, y0, x1, y1, name) in old_rects:
        out.append((int(round(nx0 + (x0 - ox0) * sx)), int(round(ny0 + (y0 - oy0) * sy)),
                    int(round(nx0 + (x1 - ox0) * sx)), int(round(ny0 + (y1 - oy0) * sy)), name))
    return out

report = {}

def do_align(shell, surf, raw_name, mode):
    raw = os.path.join(RAW, raw_name)
    keyed, dropped = key_image(raw, mode)
    ref = Image.open(os.path.join(OLD, shell, f"surface{surf}.png")).convert("RGBA")
    placed, dx, dy = place_align(keyed, ref)
    info = save_surface(placed, os.path.join(OUTROOT, shell), surf)
    info.update({"raw": raw_name, "dropped": dropped, "dx": dx, "dy": dy, "mode": "align"})
    report[f"{shell}/{surf}"] = info
    print(f"{shell} surface{surf} align dx={dx} dy={dy} bbox={info['bbox']} residue={info['green_residue_px']} dropped={dropped}", flush=True)
    return placed

def do_single(shell, surf, raw_name, mode):
    raw = os.path.join(RAW, raw_name)
    keyed, dropped = key_image(raw, mode)
    placed, dx, dy = place_single(keyed)
    info = save_surface(placed, os.path.join(OUTROOT, shell), surf)
    info.update({"raw": raw_name, "dropped": dropped, "dx": dx, "dy": dy, "mode": "single"})
    report[f"{shell}/{surf}"] = info
    print(f"{shell} surface{surf} single size={info['size']} bbox={info['bbox']} residue={info['green_residue_px']} dropped={dropped}", flush=True)
    return placed

which = sys.argv[1] if len(sys.argv) > 1 else "all"

if which in ("all", "night-rekey"):
    for surf, raw in [(0, "night_A7_seed777401_00001_.png"), (1, "night_expr_NE1_seed777401_00001_.png"),
                      (2, "night_expr_NE2_seed777401_00001_.png"), (3, "night_expr_NE3_seed777401_00001_.png"),
                      (4, "night_expr_NE4_seed777401_00001_.png"), (5, "night_expr_NE5_seed777401_00001_.png")]:
        do_align("night", surf, raw, "asta")
    for surf, raw in [(10, "night_N5_seed121601_00001_.png"), (11, "night_expr_NF11_seed121601_00001_.png"),
                      (12, "night_expr_NF12_seed121601_00001_.png"), (13, "night_expr_NF13_seed121601_00001_.png"),
                      (14, "night_expr_NF14_seed121601_00001_.png"), (15, "night_expr_NF15_seed121601_00001_.png")]:
        do_align("night", surf, raw, "furfur")

if which in ("all", "night-poses"):
    for surf in (6, 7, 8, 9, 46, 47, 48, 49):
        seed = {6: 20261101, 7: 20262102, 8: 98101, 9: 20261101, 46: 20261101, 47: 20262102, 48: 98101, 49: 20261101}[surf]
        do_single("night", surf, f"v223_NA{surf}_seed{seed}_00001_.png", "asta")
    for surf in (16, 17, 18, 19, 56, 57, 58, 59):
        seed = {16: 16101, 17: 17102, 18: 1031, 19: 1031, 56: 16101, 57: 17102, 58: 1031, 59: 1031}[surf]
        do_single("night", surf, f"v223_NF{surf}_seed{seed}_00001_.png", "furfur")
    do_single("night", 20, "v223_NA20_seed201103_00001_.png", "asta")
    do_single("night", 21, "v223_NF21_seed21101_00001_.png", "furfur")

if which in ("all", "master"):
    items = []
    for surf in (10, 11, 12, 13, 14, 15):
        keyed, dropped = key_image(os.path.join(RAW, f"v223_MF{surf}_seed1031_00001_.png"), "furfur")
        items.append((surf, keyed))
        print(f"master surface{surf} keyed dropped={dropped}", flush=True)
    placed = place_group(items)
    for surf, img in placed.items():
        info = save_surface(img, os.path.join(OUTROOT, "master"), surf)
        info.update({"raw": f"v223_MF{surf}_seed1031_00001_.png", "mode": "group"})
        report[f"master/{surf}"] = info
        print(f"master surface{surf} group size={info['size']} bbox={info['bbox']} residue={info['green_residue_px']}", flush=True)
    for surf in (16, 17, 18, 19, 56, 57, 58, 59):
        seed = {16: 16101, 17: 17102, 18: 1031, 19: 1031, 56: 16101, 57: 17102, 58: 1031, 59: 1031}[surf]
        do_single("master", surf, f"v223_MF{surf}_seed{seed}_00001_.png", "furfur")
    do_single("master", 21, "v223_MF21_seed21101_00001_.png", "furfur")

with open(os.path.join(OUTROOT, f"finalize_report_{which}.json"), "w") as f:
    json.dump(report, f, indent=1, ensure_ascii=False)
print("ALL DONE", which)
