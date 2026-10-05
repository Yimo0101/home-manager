# -*- coding: utf-8 -*-
"""居家管家 - 主窗口（粉桃侧边栏 + 页面切换 + 系统托盘 + 弹窗调度 + 三语切换）"""
import datetime
import logging
import os
import queue
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk
from pystray import Icon, Menu, MenuItem

import autostart
import i18n
from config import APP_NAME, ICON_PNG
from scheduler import Scheduler
from storage import DataStore
from ui_alarm import AlarmWindow
from ui_page_alarms import AlarmsPage
from ui_page_calendar import CalendarPage
from ui_page_focus import FocusPage
from ui_page_market import MarketPage
from ui_page_settings import SettingsPage
from ui_page_tasks import TasksPage
from ui_style import (BG, F, PRIMARY, SIDEBAR_ACTIVE_BG, SIDEBAR_ACTIVE_FG,
                      SIDEBAR_BOTTOM, SIDEBAR_HOVER, SIDEBAR_TEXT,
                      SIDEBAR_TEXT_DIM, SIDEBAR_TOP, freeze_window, init_style,
                      mascot_photo, round_rect, set_mascot)
from wake import WakeManager
import winresize

NAV_KEYS = [("alarms", "nav_alarms", "♡"), ("tasks", "nav_tasks", "♡"),
            ("calendar", "nav_calendar", "♡"), ("focus", "nav_focus", "♡"),
            ("market", "nav_market", "♡"), ("settings", "nav_settings", "♡")]


GRAD_H = 2000  # 侧边栏渐变预渲染高度（远超常见窗口，由画布自动裁剪）


def _build_gradient(width, height, c_top, c_bottom):
    """一次性预渲染纵向渐变位图，缩放窗口时不再逐帧重画"""
    t = tuple(int(c_top[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(c_bottom[i:i + 2], 16) for i in (1, 3, 5))
    data = []
    for y in range(height):
        r = y / max(1, height - 1)
        row = tuple(int(t[i] + (b[i] - t[i]) * r) for i in range(3))
        data.extend([row] * width)
    img = Image.new("RGB", (width, height))
    img.putdata(data)
    return ImageTk.PhotoImage(img)


class Sidebar(tk.Canvas):
    def __init__(self, parent, app, width=208):
        super().__init__(parent, width=width, height=600, highlightthickness=0, bd=0)
        self.app = app
        self.width = width
        self._caps = {}
        self._active = None
        self.pill = None
        self._pill_cy = None
        self._pill_after = None
        self._relayout_after = None
        self._drawn = False
        self.clock_id = self.hint_id = self._overflow = None
        self._grad = _build_gradient(width, GRAD_H, SIDEBAR_TOP, SIDEBAR_BOTTOM)
        _, _, mh = mascot_photo(108)
        self._nav_top = mh + 118  # 与 _draw 中导航起始高度公式保持一致
        # 首次映射时完整绘制一次；之后缩放只做极轻量的坐标重排（事件合并）
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, _event):
        if not self._drawn:
            self._drawn = True
            self._draw()
            return
        if self._relayout_after:
            try:
                self.after_cancel(self._relayout_after)
            except Exception:
                pass
        self._relayout_after = self.after(10, self._relayout)

    def _relayout(self):
        self._relayout_after = None
        try:
            h = self.winfo_height()
            cx = self.width // 2
            if self.clock_id is not None:
                self.coords(self.clock_id, cx, h - 66)
            if self.hint_id is not None:
                self.coords(self.hint_id, cx, h - 34)
            if self._overflow is not None:
                self.coords(self._overflow, 0, GRAD_H, self.width,
                            max(h, GRAD_H))
        except tk.TclError:
            pass

    def _draw(self):
        self.delete("all")
        w, h = self.width, self.winfo_height()
        # 纵向粉桃渐变（预渲染位图，顶部对齐，超出部分由画布裁剪）
        self.create_image(w // 2, 0, anchor="n", image=self._grad)
        self._overflow = self.create_rectangle(
            0, GRAD_H, w, max(h, GRAD_H), fill=SIDEBAR_BOTTOM,
            outline=SIDEBAR_BOTTOM)

        # 吉祥物白色贴纸卡
        photo, mw, mh = mascot_photo(108)
        pad = 12
        cx = w // 2
        card_top = 20
        card_h = mh + pad * 2
        card_x1, card_x2 = cx - mw // 2 - pad, cx + mw // 2 + pad
        round_rect(self, card_x1 + 3, card_top + 4, card_x2 + 3,
                   card_top + card_h + 4, r=22, fill="#E89FB2", outline="")
        round_rect(self, card_x1, card_top, card_x2, card_top + card_h,
                   r=22, fill="#FFFFFF", outline="")
        self.create_image(cx, card_top + pad + mh // 2, image=photo)
        self._mascot = photo  # 防回收

        # 品牌名与标语
        y = card_top + card_h + 14
        self.create_text(cx, y, text=i18n.t("brand"), fill=SIDEBAR_TEXT,
                         font=F(18, True))
        y += 26
        self.create_text(cx, y, text=i18n.t("tagline"), fill=SIDEBAR_TEXT_DIM,
                         font=F(9))

        # 导航胶囊
        self._caps = {}
        top0 = y + 34
        self._nav_top = top0
        # 选中白胶囊（最先绘制，压在文字下层，切换时平滑滑动）
        self.pill = round_rect(self, -100, -42, -86, 0, r=18,
                               fill=SIDEBAR_ACTIVE_BG, outline="")
        for i, (key, tkey, mark) in enumerate(NAV_KEYS):
            cy = top0 + i * 54
            x1, x2 = 14, w - 14
            cap = round_rect(self, x1, cy - 21, x2, cy + 21, r=18,
                             fill="", outline="")
            txt = self.create_text(cx, cy, text=i18n.t(tkey),
                                   fill=SIDEBAR_TEXT, font=F(12, True))
            self._caps[key] = (cap, txt, x1, cy - 21, x2, cy + 21)
            for item in (cap, txt):
                self.tag_bind(item, "<Button-1>",
                              lambda e, k=key: self.app.show_page(k))
                self.tag_bind(item, "<Enter>",
                              lambda e, k=key: self._hover(k, True))
                self.tag_bind(item, "<Leave>",
                              lambda e, k=key: self._hover(k, False))
        self._pill_after = None
        self._pill_cy = None
        self._paint_texts()
        if self._active:
            cy = self._cy_of(self._active)
            self._move_pill(cy)
            self._pill_cy = cy

        # 底部时钟与提示
        self.clock_id = self.create_text(cx, h - 66, text="--:--",
                                         fill=SIDEBAR_TEXT, font=F(24, True))
        self.create_text(cx, h - 34, text=i18n.t("sidebar_hint"),
                         fill=SIDEBAR_TEXT_DIM, font=F(8), width=w - 28,
                         justify="center")
        self._tick()

    def _cy_of(self, key):
        return self._nav_top + [k for k, _, _ in NAV_KEYS].index(key) * 54

    def _hover(self, key, on):
        if key == self._active:
            return
        cap, txt, x1, y1, x2, y2 = self._caps[key]
        self.itemconfigure(cap, fill=SIDEBAR_HOVER if on else "",
                           outline="")

    def set_active(self, key):
        if key == self._active and self._pill_cy is not None:
            return
        self._active = key
        self._paint_texts()
        target = self._cy_of(key)
        if self._pill_cy is None:
            self._move_pill(target)
            self._pill_cy = target
            return
        self._animate_pill(self._pill_cy, target)

    def _paint_texts(self):
        """只刷新导航文字颜色（胶囊由独立动画负责）"""
        for k, (cap, txt, x1, y1, x2, y2) in self._caps.items():
            if k == self._active:
                self.itemconfigure(txt, fill=SIDEBAR_ACTIVE_FG,
                                   font=F(12, True),
                                   text="♡ " + i18n.t(
                                       dict((a, b) for a, b, _ in NAV_KEYS)[k]))
            else:
                self.itemconfigure(cap, fill="", outline="")
                self.itemconfigure(txt, fill=SIDEBAR_TEXT, font=F(12, True),
                                   text=i18n.t(
                                       dict((a, b) for a, b, _ in NAV_KEYS)[k]))

    def _move_pill(self, cy):
        """把白胶囊瞬时放到指定中心高度（按圆角矩形多边形重设坐标）"""
        if not self.pill:
            return
        x1, x2 = 14, self.width - 14
        y1, y2, r = cy - 21, cy + 21, 18
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
               x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
               x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        self.coords(self.pill, *pts)

    def _animate_pill(self, y0, y1, steps=9, ms=16):
        """白胶囊在两个导航项之间平滑滑动"""
        if self._pill_after:
            try:
                self.after_cancel(self._pill_after)
            except Exception:
                pass
            self._pill_after = None

        def frame(i):
            if i > steps:
                self._move_pill(y1)
                self._pill_cy = y1
                self._pill_after = None
                return
            t = i / steps
            ease = 1 - (1 - t) ** 3
            self._move_pill(y0 + (y1 - y0) * ease)
            self._pill_after = self.after(ms, lambda: frame(i + 1))

        frame(0)

    def _tick(self):
        try:
            now = datetime.datetime.now()
            self.itemconfigure(self.clock_id, text=now.strftime("%H:%M"))
            self.after(1000, self._tick)
        except tk.TclError:
            pass


class App:
    def __init__(self):
        # 先建主窗口，再初始化字体与样式（避免 ImageTk 注册到隐藏 root）
        self.root = tk.Tk()
        self.store = DataStore()
        i18n.set_lang(self.store.settings.get("language", "zh"))
        i18n.init_fonts(self.root)
        init_style()
        set_mascot(self.store.settings.get("mascot_file", ""))
        self.root.title(i18n.t("brand"))
        self.root.geometry("1080x700")
        self.root.minsize(980, 640)
        self.root.configure(bg=BG)
        try:
            self.root.iconbitmap(self._ico())
        except Exception:
            pass

        self.wake = WakeManager()
        self._queue = queue.Queue()
        self.scheduler = Scheduler(self.store, self._post, self.wake)
        self.scheduler.start()
        self._popups = []
        self._tray = None
        self._hidden_notified = False
        self.current_page = "alarms"
        self._dirty = set()          # 数据有变化、待重建的页面
        self._sliding = None         # 正在滑入的页面
        self._slide_after = None     # 滑入动画定时器

        self._build_body()

        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.root.after(300, self._poll_queue)
        self.root.after(600, self._delayed_status)
        self._build_tray()
        winresize.install(self.root)   # 拖动边框缩放平滑化

    def _ico(self):
        from config import ICON_FILE
        return ICON_FILE if os.path.exists(ICON_FILE) else ICON_PNG

    # ---------- 布局 ----------
    def _build_body(self):
        self.sidebar = Sidebar(self.root, self)
        self.sidebar.pack(side="left", fill="y")
        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        self.pages = {
            "alarms": AlarmsPage(self.content, self),
            "tasks": TasksPage(self.content, self),
            "calendar": CalendarPage(self.content, self),
            "focus": FocusPage(self.content, self),
            "market": MarketPage(self.content, self),
            "settings": SettingsPage(self.content, self),
        }
        for page in self.pages.values():
            page.place(x=0, y=0, relwidth=1, relheight=1)
        self._dirty = set()
        self._sliding = None
        self._slide_after = None
        first = self.current_page
        self.current_page = None   # 强制首次 show_page 完整执行（含 tkraise/滑入）
        self.show_page(first)

    def reload_ui(self):
        """切换语言后重建整个界面与托盘（Windows 下先冻结重绘，
        全部控件重建完成后一次性刷新，避免文字逐个蹦出）"""
        freeze_window(self.root, True)
        cur = self.current_page
        try:
            for child in self.root.winfo_children():
                child.destroy()
            init_style()
            self.current_page = cur
            self._build_body()
            self._rebuild_tray()
            self.root.update_idletasks()
        finally:
            freeze_window(self.root, False)

    def show_page(self, key):
        if key == self.current_page and self._sliding is None:
            self.sidebar.set_active(key)
            return
        self.current_page = key
        self.sidebar.set_active(key)
        page = self.pages[key]
        # 只有数据变化过的页面才重建，避免每次切页都销毁/新建整页控件
        if key in self._dirty:
            page.refresh()
            self._dirty.discard(key)
        elif key == "settings":
            # 设置页的刷新很轻量（同步几个变量与缩略图），每次进都同步
            page.refresh()
        page.tkraise()
        # 鼠标滚轮只作用于当前页的滚动区
        scroll = getattr(page, "scroll", None)
        if scroll is not None:
            self.content.bind_all(
                "<MouseWheel>",
                lambda e: scroll.canvas.yview_scroll(int(-e.delta / 120), "units"))
        else:
            self.content.unbind_all("<MouseWheel>")
        self._slide_in(page)
        if key == "settings":
            self.root.after(220, self.pages["settings"].refresh_wake_status)

    def _slide_in(self, page, dx0=36, steps=12, ms=15):
        """页面以 ease-out 从右侧轻轻滑入"""
        if self._slide_after:
            try:
                self.root.after_cancel(self._slide_after)
            except Exception:
                pass
            self._slide_after = None
        if self._sliding is not None and self._sliding is not page:
            self._sliding.place_configure(x=0, y=0)
        self._sliding = page

        def frame(i):
            try:
                if i > steps:
                    page.place_configure(x=0, y=0, relwidth=1, relheight=1)
                    self._sliding = None
                    self._slide_after = None
                    return
                t = i / steps
                ease = 1 - (1 - t) ** 3
                dx = int(round(dx0 * (1 - ease)))
                page.place_configure(x=dx, y=0, relwidth=1, relheight=1)
                self._slide_after = self.root.after(ms, lambda: frame(i + 1))
            except tk.TclError:
                # 页面在动画途中被重建（如切换语言），动画自然终止
                self._sliding = None
                self._slide_after = None

        frame(0)

    def change_language(self, lang):
        if i18n.get_lang() == lang:
            return
        self.store.update_settings(language=lang)
        i18n.set_lang(lang)
        self.root.title(i18n.t("brand"))
        self.reload_ui()

    def after_change(self):
        """数据增删改后：当前页立即重建，其余页标记为脏（下次打开再重建）"""
        for key, page in self.pages.items():
            if key == self.current_page:
                try:
                    page.refresh()
                except Exception:
                    pass
            else:
                self._dirty.add(key)

    def _delayed_status(self):
        try:
            self.pages["settings"].refresh_wake_status()
        except Exception:
            pass

    # ---------- 托盘 ----------
    def _tray_image(self):
        try:
            return Image.open(ICON_PNG)
        except Exception:
            return Image.new("RGB", (64, 64), PRIMARY)

    def _build_tray(self):
        menu = Menu(
            MenuItem(i18n.t("tray_open"), lambda: self.root.after(0, self.show_window),
                     default=True),
            MenuItem(i18n.t("tray_test"), lambda: self.root.after(0, self.test_alarm)),
            MenuItem(i18n.t("tray_quit"), lambda: self.root.after(0, self.quit_app)),
        )
        self._tray = Icon("HomeManager", self._tray_image(), i18n.t("brand"), menu)
        self._tray.run_detached()

    def _rebuild_tray(self):
        try:
            if self._tray:
                self._tray.stop()
        except Exception:
            pass
        self._build_tray()

    def hide_to_tray(self):
        self.root.withdraw()
        if self._tray and not self._hidden_notified:
            self._tray.notify(i18n.t("hide_title"), i18n.t("hide_body"))
            self._hidden_notified = True

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit_app(self):
        if not messagebox.askyesno(i18n.t("quit_title"), i18n.t("quit_confirm"),
                                   parent=self.root):
            return
        try:
            if self._tray:
                self._tray.stop()
        except Exception:
            pass
        self.scheduler.stop()
        self.wake.cancel()
        try:
            self.root.destroy()
        except Exception:
            pass

    # ---------- 弹窗调度 ----------
    def _post(self, payload):
        """调度线程调用：投递到主线程"""
        self._queue.put(payload)

    def _poll_queue(self):
        try:
            try:
                while True:
                    payload = self._queue.get_nowait()
                    self._show_popup(payload)
            except queue.Empty:
                pass
            self.root.after(300, self._poll_queue)
        except tk.TclError:
            pass

    def _show_popup(self, payload):
        payload = dict(payload)
        payload["snooze_minutes"] = self.store.settings.get("snooze_minutes", 5)

        def on_closed(w):
            if w in self._popups:
                self._popups.remove(w)
            # 一键早安：闹钟被“停止”（非贪睡）后弹出今日简报
            if (payload.get("kind") == "alarm" and not getattr(w, "_snoozed", False)
                    and self.store.settings.get("morning_enabled", False)):
                self._show_morning()

        win = AlarmWindow(
            self.root, payload,
            on_snooze=lambda p: self.scheduler.add_snooze(
                p, self.store.settings.get("snooze_minutes", 5)),
            on_close=on_closed)
        self._popups.append(win)

    def _show_morning(self):
        from ui_morning import MorningWindow
        try:
            MorningWindow(self.root, self)
        except Exception:
            logging.getLogger("home_manager").exception("早安简报失败")

    def test_alarm(self):
        from media import resolve_image, resolve_ringtone
        s = self.store.settings
        self._show_popup({
            "kind": "alarm",
            "title": i18n.t("test_alarm_title"),
            "line2": i18n.t("test_alarm_line"),
            "ringtone": resolve_ringtone(s, ""),
            "image": resolve_image(s, ""),
        })

    def run(self):
        self.root.mainloop()
