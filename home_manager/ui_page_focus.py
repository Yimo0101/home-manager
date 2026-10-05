# -*- coding: utf-8 -*-
"""居家管家 - 番茄钟专注陪伴页

25/5 循环（时长可在页面上调整），圆环倒计时 + 吉祥物鼓励语；
完成一个专注自动记录到 data.json，并响铃提示休息/继续。
"""
import datetime
import os
import threading
import time
import tkinter as tk
from tkinter import ttk

import ambient
import i18n
from config import AUDIO_DIR
from media import SoundPlayer
from ui_style import (BG, BORDER, CARD, CHIP_BG, F, GREEN, PRIMARY, TEXT,
                      TEXT_SUB, mascot_photo, round_rect)

CHEER_KEYS = ["focus_cheer_1", "focus_cheer_2", "focus_cheer_3",
              "focus_cheer_4", "focus_cheer_5", "focus_cheer_6"]


class FocusPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._player = SoundPlayer()
        self.phase = "focus"       # focus / break
        self.running = False
        self.remaining = 25 * 60
        self._end_at = 0.0
        self._tick_after = None
        self._cheer_after = None
        self._cheer_idx = 0

        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=28, pady=(22, 4))
        tk.Label(head, text="♡ " + i18n.t("focus_title"), bg=BG, fg=TEXT,
                 font=F(20, True)).pack(side="left")
        tk.Label(self, text=i18n.t("focus_sub"), bg=BG, fg=TEXT_SUB,
                 font=F(10)).pack(anchor="w", padx=30)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=30, pady=10)

        # 左：圆环计时
        left = tk.Frame(body, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.ring = tk.Canvas(left, width=280, height=280, bg=CARD,
                              highlightthickness=0)
        self.ring.pack(pady=(26, 6))
        self._draw_ring(1.0)

        self.phase_var = tk.StringVar(value=i18n.t("focus_focusing"))
        tk.Label(left, textvariable=self.phase_var, bg=CARD, fg=PRIMARY,
                 font=F(15, True)).pack()

        btns = tk.Frame(left, bg=CARD)
        btns.pack(pady=16)
        self.main_btn = ttk.Button(btns, text=i18n.t("focus_start"),
                                   command=self._toggle)
        self.main_btn.pack(side="left", padx=8)
        ttk.Button(btns, text=i18n.t("focus_skip"),
                   command=self._skip).pack(side="left", padx=8)

        lens = tk.Frame(left, bg=CARD)
        lens.pack(pady=(0, 20))
        s = app.store.settings
        tk.Label(lens, text=i18n.t("focus_focus_len"), bg=CARD, fg=TEXT,
                 font=F(10)).grid(row=0, column=0, padx=6, pady=4, sticky="e")
        self.focus_len = tk.StringVar(value=str(s.get("focus_minutes", 25)))
        ttk.Combobox(lens, textvariable=self.focus_len, width=5, state="readonly",
                     values=["15", "20", "25", "30", "45", "60"]
                     ).grid(row=0, column=1, padx=6)
        tk.Label(lens, text=i18n.t("focus_break_len"), bg=CARD, fg=TEXT,
                 font=F(10)).grid(row=1, column=0, padx=6, pady=4, sticky="e")
        self.break_len = tk.StringVar(value=str(s.get("break_minutes", 5)))
        ttk.Combobox(lens, textvariable=self.break_len, width=5, state="readonly",
                     values=["5", "10", "15"]).grid(row=1, column=1, padx=6)
        self.focus_len.trace_add("write", lambda *a: self._save_lengths())
        self.break_len.trace_add("write", lambda *a: self._save_lengths())

        # 右：吉祥物 + 鼓励 + 统计
        right = tk.Frame(body, bg=CARD, highlightbackground=BORDER,
                         highlightthickness=1, width=320)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)
        cnv = tk.Canvas(right, width=200, height=210, bg=CHIP_BG,
                        highlightthickness=0)
        cnv.pack(pady=(26, 8))
        photo, w, h = mascot_photo(150)
        cnv.create_image(100, 105, image=photo)
        cnv._photo = photo
        self.cheer_var = tk.StringVar(value=i18n.t(CHEER_KEYS[0]))
        tk.Label(right, textvariable=self.cheer_var, bg=CARD, fg=TEXT,
                 font=F(12, True), wraplength=260, justify="center"
                 ).pack(padx=20, pady=6)
        self.today_var = tk.StringVar()
        self.rounds_var = tk.StringVar()
        tk.Label(right, textvariable=self.today_var, bg=CARD, fg=TEXT_SUB,
                 font=F(11)).pack(pady=(18, 4))
        tk.Label(right, textvariable=self.rounds_var, bg=CARD, fg=GREEN,
                 font=F(11, True)).pack()

        self._set_phase("focus", reset=True)
        self.refresh()
        threading.Thread(target=lambda: ambient.ensure_all(), daemon=True).start()

    # ---------- 绘制 ----------
    def _draw_ring(self, frac):
        c = self.ring
        c.delete("all")
        x0, y0, x1, y1 = 30, 30, 250, 250
        c.create_oval(x0, y0, x1, y1, outline=CHIP_BG, width=14)
        # 剩余进度弧（从12点方向顺时针）
        extent = -359.99 * max(0.0, min(1.0, frac))
        color = PRIMARY if self.phase == "focus" else GREEN
        c.create_arc(x0, y0, x1, y1, start=90, extent=extent, style="arc",
                     outline=color, width=14)
        m, sec = divmod(int(self.remaining + 0.999), 60)
        c.create_text(140, 130, text="%02d:%02d" % (m, sec),
                      fill=TEXT, font=F(52, True))
        c.create_text(140, 190,
                      text=i18n.t("focus_focusing") if self.phase == "focus"
                      else i18n.t("focus_resting"),
                      fill=TEXT_SUB, font=F(12))

    def refresh(self):
        day = datetime.date.today().strftime("%Y-%m-%d")
        minutes, rounds = self.app.store.focus_stat(day)
        self.today_var.set(i18n.t("focus_today", minutes))
        self.rounds_var.set(i18n.t("focus_rounds", rounds))

    # ---------- 计时 ----------
    def _phase_minutes(self):
        s = self.app.store.settings
        if self.phase == "focus":
            return int(s.get("focus_minutes", 25))
        return int(s.get("break_minutes", 5))

    def _set_phase(self, phase, reset=True):
        self.phase = phase
        self.running = False
        if reset:
            self.remaining = self._phase_minutes() * 60
        self.phase_var.set(i18n.t("focus_focusing") if phase == "focus"
                           else i18n.t("focus_resting"))
        try:
            self.main_btn.configure(text=i18n.t("focus_start"))
        except tk.TclError:
            pass
        total = max(1, self._phase_minutes() * 60)
        self._draw_ring(self.remaining / total)
        self._stop_cheer_rotate()

    def _toggle(self):
        if self.running:
            # 暂停
            self.running = False
            self.remaining = max(0, self._end_at - time.monotonic())
            self.main_btn.configure(text=i18n.t("focus_resume"))
            self._stop_cheer_rotate()
            return
        self.running = True
        self._end_at = time.monotonic() + self.remaining
        self.main_btn.configure(text=i18n.t("focus_pause"))
        self._tick()
        if self.phase == "focus":
            self._rotate_cheer()

    def _tick(self):
        if not self.running:
            return
        self.remaining = max(0, self._end_at - time.monotonic())
        total = max(1, self._phase_minutes() * 60)
        self._draw_ring(self.remaining / total)
        if self.remaining <= 0:
            self._complete()
            return
        self._tick_after = self.after(250, self._tick)

    def _skip(self):
        self.running = False
        self._next_phase(completed=False)

    def _complete(self):
        self.running = False
        if self.phase == "focus":
            day = datetime.date.today().strftime("%Y-%m-%d")
            self.app.store.add_focus_minutes(day, self._phase_minutes(), rounds=1)
            self.refresh()
            self._chime()
            self._popup(i18n.t("focus_focus_end"))
            self._next_phase(completed=True)
        else:
            self._chime()
            self._popup(i18n.t("focus_break_end"))
            self._next_phase(completed=True)

    def _next_phase(self, completed):
        nxt = "break" if self.phase == "focus" else "focus"
        self._set_phase(nxt, reset=True)

    def _chime(self):
        def work():
            try:
                paths = ambient.ensure_all()
                p = paths.get("ambient_chime")
                if p and os.path.exists(p):
                    pl = SoundPlayer()
                    pl.play(p, loop=False)
            except Exception:
                pass
        threading.Thread(target=work, daemon=True).start()

    def _popup(self, text):
        top = tk.Toplevel(self.app.root)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.configure(bg=PRIMARY)
        box = tk.Frame(top, bg=PRIMARY)
        box.pack(padx=2, pady=2)
        tk.Label(box, text="♡ " + text, bg=PRIMARY, fg="#FFFFFF",
                 font=F(13, True), padx=26, pady=18).pack()
        ttk.Button(box, text=i18n.t("ok"), command=top.destroy).pack(pady=(0, 16))
        self.app.root.update_idletasks()
        x = self.app.root.winfo_rootx() + self.app.root.winfo_width() // 2 - 190
        y = self.app.root.winfo_rooty() + self.app.root.winfo_height() // 2 - 90
        top.geometry("+%d+%d" % (x, y))
        top.after(12000, lambda: top.winfo_exists() and top.destroy())

    # ---------- 鼓励语轮换 ----------
    def _rotate_cheer(self):
        self._cheer_idx = (self._cheer_idx + 1) % len(CHEER_KEYS)
        self.cheer_var.set(i18n.t(CHEER_KEYS[self._cheer_idx]))
        self._cheer_after = self.after(12000, self._rotate_cheer)

    def _stop_cheer_rotate(self):
        if self._cheer_after:
            try:
                self.after_cancel(self._cheer_after)
            except Exception:
                pass
            self._cheer_after = None

    def _save_lengths(self):
        try:
            fm = int(self.focus_len.get())
            bm = int(self.break_len.get())
            self.app.store.update_settings(focus_minutes=fm, break_minutes=bm)
            if not self.running:
                self._set_phase(self.phase, reset=True)
        except (ValueError, tk.TclError):
            pass
