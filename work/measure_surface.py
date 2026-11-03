import sys
import numpy as np
from PIL import Image
from scipy import ndimage

# usage: measure_surface.py <surface.png> [...]
# 顔は「頭部帯の肌色を行走査し、幅が最大になる辺りを顔、幅が細る所を顎」とする
# 幅プロファイル方式で測る（首・胸の肌と連結しても顔だけを切り出せる）。
# surface0 の既存定義（Head 150,60,320,255 / Face 170,140,300,250 /
# Bust 110,360,360,480）に近づくよう較正した上で全 surface に同じ方法を適用する。

def measure(path):
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im).astype(int)
    alpha = a[..., 3]
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    solid = alpha > 128
    H, W = solid.shape
    rowcount = solid.sum(axis=1)

    # hair top: first row with a wide solid run (>=150px)
    hair_top = next(y for y in range(H) if rowcount[y] >= 150)

    skin = (R > 150) & (G > 95) & (B > 60) & (R > B + 25) & (R >= G - 5) & (G > B)
    # skin width profile in head band
    band_end = min(H, hair_top + 420)
    widths = np.array([skin[y].sum() for y in range(hair_top, band_end)])
    rows = np.arange(hair_top, band_end)
    if widths.max() < 30:
        print(f"{path}: NO FACE")
        return
    peak = int(np.argmax(widths))
    maxw = widths[peak]
    # face top: first row (before peak) with width >= 25% of max
    ft = peak
    while ft > 0 and widths[ft] >= maxw * 0.25:
        ft -= 1
    face_top = rows[ft + 1]
    # chin: after peak, first run of 6 rows with width < 45% of max
    fb = peak
    run = 0
    for i in range(peak, len(widths)):
        if widths[i] < maxw * 0.45:
            run += 1
            if run >= 6:
                fb = i - 5
                break
        else:
            run = 0
    else:
        fb = len(widths) - 1
    face_bottom = rows[fb]
    skin_band = skin[face_top:face_bottom + 1, :]
    ys, xs = np.where(skin_band)
    fx0, fx1 = xs.min(), xs.max()
    fcx = (fx0 + fx1) / 2.0
    fw = fx1 - fx0 + 1

    # head box: surface0 convention (head proper, not whole hair mass)
    head = (int(fcx - fw * 0.85), max(0, hair_top - 4), int(fcx + fw * 0.85), face_bottom + 12)
    face = (fx0 - 6, max(0, face_top - 6), fx1 + 6, face_bottom + 4)
    # bust: solid extent in rows chin+105..chin+225, central trim (exclude hair tips)
    b0, b1 = face_bottom + 105, face_bottom + 225
    sub = solid[b0:b1, :]
    ys2, xs2 = np.where(sub)
    bx0, bx1 = xs2.min(), xs2.max()
    bust = (bx0 + 10, b0, bx1 - 10, b1)
    print(f"{path} size={W}x{H} hair_top={hair_top} face x:{fx0}..{fx1} y:{face_top}..{face_bottom}")
    print(f"  collision0,{head[0]},{head[1]},{head[2]},{head[3]},Head")
    print(f"  collision1,{face[0]},{face[1]},{face[2]},{face[3]},Face")
    print(f"  collision2,{bust[0]},{bust[1]},{bust[2]},{bust[3]},Bust")

for p in sys.argv[1:]:
    measure(p)
