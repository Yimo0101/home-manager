# -*- coding: utf-8 -*-
"""把吉祥物白底贴纸抠成透明 PNG（numpy + scipy，边缘泛洪）
画面四周为纯白留白、贴纸轮廓完整闭合：
- 与任一边缘连通的近白区域 = 背景
- 背景外侧 15px 内、极亮低饱和的小杂点 = 删除
角色内部白色（围巾、开衫）由深色描边封闭，完整保留。
"""
import os

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mascot_raw.png")
DST = os.path.join(os.path.dirname(HERE), "assets", "mascot.png")

img = Image.open(SRC).convert("RGBA")
w, h = img.size
rgb = np.asarray(img)[:, :, :3].astype(np.int16)
mn = rgb.min(axis=2)
mx = rgb.max(axis=2)
sat = mx - mn
near = (mn >= 232) & (sat <= 24)
conn = np.ones((3, 3), dtype=int)
lab, n = ndimage.label(near, structure=conn)

border = set(int(v) for v in np.unique(np.concatenate([
    lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])) if v)
remove = np.isin(lab, list(border))

# 背景外侧小杂点
zone = ndimage.binary_dilation(remove, structure=np.ones((31, 31), dtype=int))
sizes = np.bincount(lab.ravel())
mean_mn = ndimage.mean(mn, lab, index=np.arange(1, n + 1))
mean_sat = ndimage.mean(sat, lab, index=np.arange(1, n + 1))
for cid in range(1, n + 1):
    if cid in border:
        continue
    if sizes[cid] < 800 and mean_mn[cid - 1] >= 248 and mean_sat[cid - 1] <= 15:
        comp = lab == cid
        if comp[zone].any():
            remove |= comp

alpha = np.where(remove, 0, 255).astype(np.uint8)
alpha_img = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(1.2))
img.putalpha(alpha_img)
img = img.crop(img.getbbox())
img.save(DST)
print("saved:", DST, img.size)
