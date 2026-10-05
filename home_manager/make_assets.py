# -*- coding: utf-8 -*-
"""生成居家管家默认资源：铃声 default_ring.wav、背景 default_bg.png、图标 icon"""
import math
import os
import struct
import wave

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)


# ---------------- 铃声 ----------------
def make_ring(path):
    rate = 44100
    # 清脆晨铃：C6 E6 G6 C7 上行琶音，每个音带钟琴泛音与衰减
    notes = [
        (1046.50, 0.0, 0.55),   # C6
        (1318.51, 0.16, 0.55),  # E6
        (1567.98, 0.32, 0.55),  # G6
        (2093.00, 0.48, 0.9),   # C7
        (1567.98, 1.05, 0.55),
        (2093.00, 1.21, 1.1),
    ]
    total = 2.8
    n = int(rate * total)
    samples = [0.0] * n

    def bell(freq, start, dur, amp=0.55):
        s0 = int(start * rate)
        for i in range(int(dur * rate)):
            idx = s0 + i
            if idx >= n:
                break
            t = i / rate
            env = math.exp(-3.2 * t)
            v = (
                math.sin(2 * math.pi * freq * t) * 1.0
                + math.sin(2 * math.pi * freq * 2.01 * t) * 0.35
                + math.sin(2 * math.pi * freq * 2.99 * t) * 0.18
            )
            # 淡入避免爆音
            fade = min(1.0, t / 0.008)
            samples[idx] += amp * env * fade * v / 1.53

    for f, s, d in notes:
        bell(f, s, d)

    # 归一化
    peak = max(0.01, max(abs(x) for x in samples))
    gain = 0.9 / peak
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = b"".join(
            struct.pack("<h", int(max(-1, min(1, x * gain)) * 32767))
            for x in samples
        )
        w.writeframes(frames)
    print("铃声已生成:", path)


# ---------------- 背景 ----------------
def _font(size, bold=True):
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _heart(d, cx, cy, s, fill):
    """以 (cx, cy) 为中心画爱心，s 为整体尺寸"""
    r = s / 4
    d.ellipse((cx - s / 2, cy - s / 4 - r, cx - s / 2 + 2 * r, cy - s / 4 + r), fill=fill)
    d.ellipse((cx + s / 2 - 2 * r, cy - s / 4 - r, cx + s / 2, cy - s / 4 + r), fill=fill)
    d.polygon([(cx - s / 2, cy - s / 8), (cx + s / 2, cy - s / 8),
               (cx, cy + s / 2)], fill=fill)


def make_bg(path, w=1920, h=1080):
    # 粉桃奶油渐变
    top = (255, 226, 235)
    bottom = (255, 244, 232)
    img = Image.new("RGB", (w, h), top)
    px = img.load()
    for y in range(h):
        r = y / h
        col = tuple(int(top[i] + (bottom[i] - top[i]) * r) for i in range(3))
        for x in range(w):
            px[x, y] = col

    # 柔和光斑
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    circles = [
        (300, 220, 260, (255, 255, 255, 60)),
        (1600, 180, 320, (255, 255, 255, 48)),
        (1500, 880, 420, (255, 205, 222, 50)),
        (220, 900, 360, (255, 222, 200, 46)),
        (960, 120, 180, (255, 255, 255, 40)),
    ]
    for cx, cy, rad, color in circles:
        d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=color)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.alpha_composite(img.convert("RGBA"), glow)

    # 漂浮的小爱心与圆点（结衣风装饰，低透明度不抢文字）
    deco = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    hearts = [
        (180, 180, 46, (240, 114, 158, 38)),
        (1720, 260, 60, (240, 114, 158, 32)),
        (1480, 760, 40, (255, 158, 132, 34)),
        (330, 780, 54, (240, 114, 158, 30)),
        (980, 180, 34, (255, 178, 135, 30)),
        (760, 880, 38, (240, 114, 158, 26)),
    ]
    for cx, cy, s, col in hearts:
        _heart(dd, cx, cy, s, col)
    for cx, cy, rad, col in [
        (560, 300, 14, (255, 255, 255, 90)),
        (1300, 180, 10, (255, 255, 255, 80)),
        (1180, 900, 12, (255, 255, 255, 80)),
        (420, 480, 9, (255, 255, 255, 70)),
        (1660, 600, 11, (255, 255, 255, 70)),
    ]:
        dd.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=col)
    deco = deco.filter(ImageFilter.GaussianBlur(1.2))
    img = Image.alpha_composite(img, deco)

    img.convert("RGB").save(path, quality=92)
    print("背景已生成:", path)


# ---------------- 图标 ----------------
def make_icon(png_path, ico_path):
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # 圆角方形底（粉桃渐变）
    radius = 56
    grad = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    c1, c2 = (250, 150, 184), (238, 105, 148)
    for y in range(size):
        r = y / size
        col = tuple(int(c1[i] + (c2[i] - c1[i]) * r) for i in range(3)) + (255,)
        gd.line([(0, y), (size, y)], fill=col)
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    img = Image.composite(grad, img, mask)

    d = ImageDraw.Draw(img)
    # 白色房子
    body = (64, 120, size - 64, size - 70)
    d.rounded_rectangle(body, radius=14, fill=(255, 255, 255, 255))
    roof = [(128, 40), (52, 108), (204, 108)]
    d.polygon(roof, fill=(255, 255, 255, 255))
    # 门（粉色镂空感）
    d.rounded_rectangle((112, 150, 144, 190), radius=6, fill=(240, 114, 158, 255))
    # 房门上的小爱心
    _heart(d, 128, 168, 16, (255, 255, 255, 255))
    # 桃色小圆点装饰
    d.ellipse((176, 132, 206, 162), fill=(255, 201, 138, 255))
    d.line((191, 147, 191, 138), fill=(190, 80, 120, 255), width=4)
    d.line((191, 147, 198, 150), fill=(190, 80, 120, 255), width=4)

    img.save(png_path)
    img.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("图标已生成:", png_path, ico_path)


if __name__ == "__main__":
    make_ring(os.path.join(ASSETS, "default_ring.wav"))
    make_bg(os.path.join(ASSETS, "default_bg.png"))
    make_icon(os.path.join(ASSETS, "icon.png"), os.path.join(ASSETS, "icon.ico"))
