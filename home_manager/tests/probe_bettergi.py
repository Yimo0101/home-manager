# -*- coding: utf-8 -*-
"""真机验证：启动/激活 BetterGI，在窗口截图上标出模板的两个点击点（不点击）"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import actions  # noqa: E402
from PIL import Image, ImageDraw, ImageGrab  # noqa: E402

EXE = r"C:\Program Files\BetterGI\BetterGI.exe"
STEPS = [(47 / 900, 221 / 600, "一条龙"), (326 / 900, 65 / 600, "开始▶")]

actions.launch_task({"exe": EXE, "window_title": "BetterGI|更好的原神", "clicks": []})
hwnd = actions.wait_for_window("BetterGI|更好的原神", 40)
if not hwnd:
    print("FAIL: 未等到 BetterGI 窗口")
    sys.exit(1)
actions.focus_window(hwnd)
time.sleep(1.2)
rc = actions.window_rect(hwnd)
l, t, r, b = rc
print("窗口矩形:", rc, "尺寸:", r - l, b - t)

img = ImageGrab.grab(bbox=rc)
draw = ImageDraw.Draw(img)
for rx, ry, name in STEPS:
    px, py = int(rx * (r - l)), int(ry * (b - t))
    draw.ellipse((px - 12, py - 12, px + 12, py + 12),
                 outline=(255, 0, 0), width=4)
    draw.line((px - 18, py, px + 18, py), fill=(255, 0, 0), width=2)
    draw.line((px, py - 18, px, py + 18), fill=(255, 0, 0), width=2)
    draw.text((px + 16, py - 8), name, fill=(255, 0, 0))
    print("点击点 %s: 屏幕(%d,%d) 窗口内(%d,%d)" % (name, l + px, t + py, px, py))

out = os.path.join(HERE, "shots_new", "bettergi_points.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
img.save(out)
print("saved:", out)
