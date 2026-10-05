# -*- coding: utf-8 -*-
"""居家管家 - UI 主题与通用控件（结衣风粉桃可爱主题 + 三语可爱字体）"""
import os
import sys
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

import i18n

# ---------- 粉桃配色 ----------
BG = "#FFF6F4"           # 奶油粉白背景
CARD = "#FFFFFF"         # 卡片白
SIDEBAR_TOP = "#FCCFDB"  # 侧边栏渐变上（浅粉）
SIDEBAR_BOTTOM = "#F9BCAB"  # 侧边栏渐变下（蜜桃）
SIDEBAR_BG = "#FAC9D2"   # 侧边栏近似底色（个别控件用）
SIDEBAR_TEXT = "#9C4A66"  # 侧边栏深玫红文字
SIDEBAR_TEXT_DIM = "#B9748A"
SIDEBAR_HOVER = "#FBD9E1"
SIDEBAR_ACTIVE_BG = "#FFFFFF"
SIDEBAR_ACTIVE_FG = "#E85F90"
TEXT = "#5B3B47"         # 暖梅棕正文
TEXT_SUB = "#A57E8C"     # 次要文字
TEXT_LIGHT = "#CBA0AE"
PRIMARY = "#F0729E"      # 玫瑰粉主色
PRIMARY_DARK = "#DE5B8A"
PRIMARY_LIGHT = "#FFE3EC"
PEACH = "#FFB287"
DANGER = "#F26D7D"
DANGER_DARK = "#DD5566"
GREEN = "#4FB987"
ORANGE = "#F5A46A"
BORDER = "#F7E2E8"
CHIP_BG = "#FFE9F0"
CHIP_OFF = "#F6EDF1"
SWITCH_OFF = "#EAD5DD"

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
try:
    from config import MASCOT_FILE as _DEFAULT_MASCOT
except Exception:
    _DEFAULT_MASCOT = os.path.join(ASSETS_DIR, "mascot.png")
MASCOT = _DEFAULT_MASCOT


def set_mascot(path):
    """更换侧边栏/弹窗吉祥物（空字符串=恢复自带）"""
    global MASCOT
    MASCOT = path if path and os.path.exists(path) else _DEFAULT_MASCOT
    _mascot_cache.clear()


def mascot_path():
    return MASCOT

# ---------- 统一微动画语言（所有页面共用，时长/缓动一致） ----------
SEL_BG = "#FFEAF1"        # 日历选中格粉底
NUM_ON = "#573F4A"        # 本月日期数字（深）
NUM_OFF = "#D9C5CD"       # 非本月日期数字（浅，明显弱于本月）
MARK_OFF = "#E6D8DE"      # 非本月节气/节日/农历小字
ANIM_MS = 120             # 统一动画时长
ANIM_STEP = 15            # 每帧间隔（约 8 帧，ease-out）


def lerp_color(c1, c2, t):
    """两个 #RRGGBB 颜色之间插值，t 会被夹在 0~1"""
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    a = tuple(int(c1[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(c2[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, round(a[i] + (b[i] - a[i]) * t))) for i in range(3))


def tween(root, duration_ms, on_frame, on_done=None):
    """ease-out 补间动画；on_frame(进度0→1)。返回 cancel()。"""
    n = max(1, round(duration_ms / ANIM_STEP))
    state = {"i": 0, "after": None, "dead": False}

    def frame():
        if state["dead"]:
            return
        if state["i"] >= n:
            on_frame(1.0)
            state["after"] = None
            if on_done:
                on_done()
            return
        t = state["i"] / n
        on_frame(1 - (1 - t) ** 3)
        state["i"] += 1
        state["after"] = root.after(ANIM_STEP, frame)

    frame()

    def cancel():
        state["dead"] = True
        if state["after"]:
            try:
                root.after_cancel(state["after"])
            except Exception:
                pass
        state["after"] = None

    return cancel


def morph_colors(root, items, duration_ms=ANIM_MS):
    """批量颜色过渡：items=[(widget, 选项名, 起始色, 目标色), ...]"""
    def render(te):
        for w, opt, a, b in items:
            try:
                w.configure(**{opt: lerp_color(a, b, te)})
            except tk.TclError:
                pass
    return tween(root, duration_ms, render)


if sys.platform == "win32":
    import ctypes

    _u32 = ctypes.windll.user32

    def freeze_window(root, freeze):
        """冻结/恢复整个窗口重绘。冻结期间批量改控件，恢复时一次性刷新，
        避免文字与格子逐个蹦出（全软件统一的无闪烁刷新方式）。"""
        try:
            hwnd = root.winfo_id()
        except tk.TclError:
            return
        _u32.SendMessageW(hwnd, 0x000B, 0 if freeze else 1, 0)
        if not freeze:
            _u32.RedrawWindow(hwnd, None, None,
                              0x0001 | 0x0004 | 0x0080 | 0x0100)
else:
    def freeze_window(root, freeze):
        pass


_mascot_cache = {}


def F(size, bold=False):
    """当前语言下的可爱 Tk 字体"""
    return i18n.F(size, bold)


def init_style():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(".", background=BG, foreground=TEXT, font=F(10))
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=CARD, foreground=TEXT)
    style.configure("Sub.TLabel", background=BG, foreground=TEXT_SUB, font=F(9))
    style.configure("CardSub.TLabel", background=CARD, foreground=TEXT_SUB, font=F(9))
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=F(18, True))
    style.configure("H1.TLabel", background=CARD, foreground=TEXT, font=F(12, True))
    style.configure("Big.TLabel", background=CARD, foreground=PRIMARY, font=F(22, True))

    style.configure("TButton", padding=(12, 7), font=F(10), borderwidth=1)
    style.configure("Accent.TButton", background=PRIMARY, foreground="#FFFFFF",
                    bordercolor=PRIMARY, focuscolor=PRIMARY, padding=(16, 9),
                    font=F(10, True))
    style.map("Accent.TButton",
              background=[("active", PRIMARY_DARK), ("pressed", PRIMARY_DARK)],
              foreground=[("active", "#FFFFFF")])
    style.configure("Danger.TButton", background=DANGER, foreground="#FFFFFF",
                    bordercolor=DANGER, focuscolor=DANGER, padding=(12, 7))
    style.map("Danger.TButton", background=[("active", DANGER_DARK)],
              foreground=[("active", "#FFFFFF")])
    style.configure("Ghost.TButton", background=CARD, foreground=PRIMARY,
                    bordercolor=PRIMARY_LIGHT, focuscolor=PRIMARY_LIGHT, padding=(10, 7))
    style.map("Ghost.TButton", background=[("active", CHIP_BG)])
    style.configure("Lang.TButton", background=CARD, foreground=TEXT_SUB,
                    bordercolor=BORDER, focuscolor=BORDER, padding=(14, 8),
                    font=F(10))
    style.map("Lang.TButton", background=[("active", CHIP_BG)])
    style.configure("LangOn.TButton", background=PRIMARY, foreground="#FFFFFF",
                    bordercolor=PRIMARY, focuscolor=PRIMARY, padding=(14, 8),
                    font=F(10, True))
    style.map("LangOn.TButton", background=[("active", PRIMARY_DARK)],
              foreground=[("active", "#FFFFFF")])

    style.configure("TEntry", fieldbackground="#FFFDFD", padding=4, bordercolor=BORDER)
    style.configure("TCombobox", padding=3)
    style.map("TCombobox", fieldbackground=[("readonly", "#FFFDFD")],
              bordercolor=[("focus", PRIMARY)])
    style.configure("Treeview", rowheight=32, font=F(10), background=CARD,
                    fieldbackground=CARD, borderwidth=0, foreground=TEXT)
    style.configure("Treeview.Heading", font=F(10, True), padding=6,
                    background=CHIP_BG, foreground=TEXT)
    style.map("Treeview", background=[("selected", PRIMARY_LIGHT)],
              foreground=[("selected", TEXT)])
    style.configure("TCheckbutton", background=BG, foreground=TEXT, font=F(10))
    style.configure("Card.TCheckbutton", background=CARD, foreground=TEXT, font=F(10))
    style.configure("TRadiobutton", background=BG, foreground=TEXT, font=F(10))
    style.configure("TNotebook", borderwidth=0)
    return style


# ---------- Canvas 圆角 ----------
def round_rect(canvas, x1, y1, x2, y2, r=16, **kw):
    """在 tk.Canvas 上画圆角矩形（smooth 多边形近似）"""
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
           x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
           x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def heart(canvas, cx, cy, s, fill, outline=""):
    """在 tk.Canvas 上画小爱心，s 为宽度"""
    r = s / 4
    canvas.create_oval(cx - s / 2, cy - s / 4 - r, cx - s / 2 + 2 * r,
                       cy - s / 4 + r, fill=fill, outline=outline)
    canvas.create_oval(cx + s / 2 - 2 * r, cy - s / 4 - r, cx + s / 2,
                       cy - s / 4 + r, fill=fill, outline=outline)
    canvas.create_polygon(cx - s / 2, cy - s / 8, cx + s / 2, cy - s / 8,
                          cx, cy + s / 2, fill=fill, outline=outline)


# ---------- 卡片 ----------
def make_card(parent, **pack_kw):
    card = tk.Frame(parent, bg=CARD, highlightbackground=BORDER,
                    highlightthickness=1, bd=0)
    if pack_kw:
        card.pack(**pack_kw)
    return card


def mascot_photo(width):
    """按宽度等比加载吉祥物 ImageTk（带缓存），返回 (photo, w, h)"""
    if width in _mascot_cache:
        return _mascot_cache[width]
    img = Image.open(MASCOT).convert("RGBA")
    h = int(img.height * width / img.width)
    img = img.resize((width, h), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    _mascot_cache[width] = (photo, width, h)
    return _mascot_cache[width]


# ---------- 开关 ----------
class Switch(tk.Canvas):
    def __init__(self, parent, value=False, on_toggle=None, bg=CARD, width=52, height=28):
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.value = bool(value)
        self.on_toggle = on_toggle
        self._frac = 1.0 if self.value else 0.0  # 0=关 1=开（用于平滑动画）
        self._after = None
        self.bind("<Button-1>", self._click)
        self.redraw()

    def set(self, v):
        self.value = bool(v)
        self._frac = 1.0 if self.value else 0.0
        self.redraw()

    def get(self):
        return self.value

    def _click(self, _=None):
        self.value = not self.value
        self._animate()
        if self.on_toggle:
            self.on_toggle(self.value)

    def _animate(self):
        """圆点滑动 + 轨道颜色渐变（统一 120ms ease-out）"""
        if self._after:
            self._after()  # 取消上一段动画
        target = 1.0 if self.value else 0.0
        start = self._frac

        def render(te):
            self._frac = start + (target - start) * te
            self.redraw()

        self._after = tween(self, ANIM_MS, render,
                            on_done=lambda: setattr(self, "_after", None))

    def redraw(self):
        self.delete("all")
        w, h = int(self["width"]), int(self["height"])
        f = self._frac
        track = lerp_color(SWITCH_OFF, PRIMARY, f)
        cx = (h / 2 + 2) + (w - h - 4) * f
        round_rect(self, 2, 2, w - 2, h - 2, r=(h - 4) / 2,
                   fill=track, outline="")
        r = h / 2 - 4
        self.create_oval(cx - r, h / 2 - r, cx + r, h / 2 + r,
                         fill="#FFFFFF", outline="")
        if f >= 0.99:
            heart(self, cx, h / 2 + 1, r * 1.05, PRIMARY)


# ---------- 星期选择 ----------
class WeekdayPicker(tk.Frame):
    def __init__(self, parent, value=None, bg=CARD):
        super().__init__(parent, bg=bg)
        self._bg = bg
        self.vars = [tk.BooleanVar(value=(i in (value or []))) for i in range(7)]
        self.buttons = []
        for i in range(7):
            b = tk.Button(self, text=i18n.weekday_short(i), width=3, bd=0,
                          font=F(10, True), cursor="hand2", relief="flat",
                          activebackground=PRIMARY,
                          command=lambda i=i: self._toggle(i))
            b.grid(row=0, column=i, padx=3)
            self.buttons.append(b)
        presets = [(i18n.t("every_day"), list(range(7))),
                   (i18n.t("workday"), [0, 1, 2, 3, 4]),
                   (i18n.t("weekend"), [5, 6])]
        for i, (text, ids) in enumerate(presets, start=1):
            b = tk.Button(self, text=text, bd=0, fg=PRIMARY, bg=CHIP_BG,
                          font=F(9), cursor="hand2", relief="flat",
                          activebackground=PRIMARY_LIGHT,
                          command=lambda ids=ids: self.set(ids))
            b.grid(row=0, column=7 + i, padx=(6, 0))
        self._refresh()

    def _toggle(self, i):
        self.vars[i].set(not self.vars[i].get())
        self._refresh()

    def set(self, ids):
        for i, v in enumerate(self.vars):
            v.set(i in ids)
        self._refresh()

    def get(self):
        return [i for i, v in enumerate(self.vars) if v.get()]

    def _refresh(self):
        for i, b in enumerate(self.buttons):
            if self.vars[i].get():
                b.configure(bg=PRIMARY, fg="#FFFFFF", activebackground=PRIMARY_DARK,
                            activeforeground="#FFFFFF")
            else:
                b.configure(bg=CHIP_OFF, fg=TEXT_SUB, activebackground=PRIMARY_LIGHT,
                            activeforeground=TEXT)


# ---------- 时间选择 ----------
class TimePicker(tk.Frame):
    def __init__(self, parent, value="07:00", bg=CARD):
        super().__init__(parent, bg=bg)
        self.hour = ttk.Combobox(self, width=3, values=["%02d" % i for i in range(24)],
                                 state="readonly", font=F(11))
        self.minute = ttk.Combobox(self, width=3,
                                   values=["%02d" % i for i in range(60)],
                                   state="readonly", font=F(11))
        parts = str(value).split(":")
        h = parts[0] if len(parts) == 2 and parts[0].isdigit() else "10"
        m = parts[1] if len(parts) == 2 and parts[1].isdigit() else "00"
        self.hour.set(h)
        self.minute.set(m)
        self.hour.pack(side="left")
        tk.Label(self, text=":", bg=bg, font=F(12, True)).pack(side="left", padx=2)
        self.minute.pack(side="left")

    def get(self):
        return "%s:%s" % (self.hour.get(), self.minute.get())

    def set(self, v):
        try:
            h, m = v.split(":")
            self.hour.set(h)
            self.minute.set(m)
        except Exception:
            pass


# ---------- 可滚动区域 ----------
class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg=BG, **kw):
        super().__init__(parent, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                       command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfigure(self.win, width=e.width))
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(int(-e.delta / 120), "units"))
