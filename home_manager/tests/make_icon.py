# -*- coding: utf-8 -*-
"""把 icon_master.png 裁成圆角方形应用图标，输出多尺寸 icon.ico 与 icon.png"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
SRC = os.path.join(ASSETS, "icon_master.png")

img = Image.open(SRC).convert("RGBA")
w, h = img.size
px = img.load()

# 1. 找到粉色圆角方块的边界（非近白像素）
T = 245
minx, miny, maxx, maxy = w, h, 0, 0
for y in range(h):
    for x in range(w):
        r, g, b, _ = px[x, y]
        if r < T or g < T or b < T:
            if x < minx:
                minx = x
            if x > maxx:
                maxx = x
            if y < miny:
                miny = y
            if y > maxy:
                maxy = y
tile = img.crop((minx, miny, maxx + 1, maxy + 1))
tw, th = tile.size
# 以最长边对称扩展成正方形（多出的边为白色，随后被圆角遮罩裁掉）
s = max(tw, th)
square = Image.new("RGBA", (s, s), (255, 255, 255, 255))
square.paste(tile, ((s - tw) // 2, (s - th) // 2))

# 2. 全幅粉底：瓷砖圆角之外的白边全部用瓷砖边缘粉填满（任何壁纸上都无白边）
master = square.resize((512, 512), Image.LANCZOS)
mp = master.load()
TT = 245
bx0, by0, bx1, by1 = 512, 512, 0, 0
for y in range(512):
    for x in range(512):
        r, g, b, _ = mp[x, y]
        if r < TT or g < TT or b < TT:
            bx0, by0 = min(bx0, x), min(by0, y)
            bx1, by1 = max(bx1, x), max(by1, y)
cx, cy = (bx0 + bx1) // 2, (by0 + by1) // 2
edge_samples = [
    mp[cx, min(511, by0 + 12)], mp[cx, max(0, by1 - 12)],
    mp[min(511, bx0 + 12), cy], mp[max(0, bx1 - 12), cy],
]
edge = tuple(sum(c[i] for c in edge_samples) // 4 for i in range(3))
# 瓷砖自身圆角半径约为其高度的 10%
radius = int(round((by1 - by0) * 0.102))
inside = Image.new("L", (512, 512), 0)
ImageDraw.Draw(inside).rounded_rectangle(
    (bx0, by0, bx1, by1), radius=radius, fill=255)
in_px = inside.load()
# 把瓷砖边缘颜色沿圆角几何外扩到白边区域，使角落成为瓷砖底色的无缝延续
import math

canvas = master.copy()
cp = canvas.load()
w2 = (bx1 - bx0) / 2.0
h2 = (by1 - by0) / 2.0
R = float(radius)
for y in range(512):
    for x in range(512):
        if in_px[x, y] > 0:
            continue
        sx = 1 if x >= cx else -1
        sy = 1 if y >= cy else -1
        dx, dy = x - cx, y - cy
        qx = max(abs(dx) - (w2 - R), 0.0)
        qy = max(abs(dy) - (h2 - R), 0.0)
        if qx > 0 and qy > 0:
            dd = math.hypot(qx, qy)
            ux = cx + sx * (w2 - R) + sx * R * qx / dd
            uy = cy + sy * (h2 - R) + sy * R * qy / dd
        elif qx == 0:
            ux, uy = x, cy + sy * (h2 - R) + sy * R
        else:
            ux, uy = cx + sx * (w2 - R) + sx * R, y
        # 向内收 12px 取样，避开瓷砖自身的浅色描边/高光边
        ux = int(round(ux - sx * 12))
        uy = int(round(uy - sy * 12))
        ux = max(0, min(511, ux))
        uy = max(0, min(511, uy))
        r, g, b, _ = mp[ux, uy]
        cp[x, y] = (r, g, b, 255)
master = canvas

# 3. 输出 png 与多尺寸 ico（app.* 为新缓存身份，icon.* 保留兼容）
icon_png = master.resize((256, 256), Image.LANCZOS)
for name in ("app.png", "icon.png"):
    icon_png.save(os.path.join(ASSETS, name))
for name in ("app.ico", "icon.ico"):
    icon_png.save(os.path.join(ASSETS, name),
                  format="ICO",
                  sizes=[(256, 256), (128, 128), (64, 64), (48, 48),
                         (32, 32), (16, 16)])
print("app.ico / app.png saved; tile bbox:", (minx, miny, maxx, maxy))
