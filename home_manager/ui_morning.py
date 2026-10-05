# -*- coding: utf-8 -*-
"""居家管家 - 早安简报窗口（关闭起床闹钟后弹出）"""
import tkinter as tk
from tkinter import ttk

import i18n
import morning
from ui_style import (BG, BORDER, CARD, CHIP_BG, F, PRIMARY, TEXT, TEXT_SUB,
                      mascot_photo)


class MorningWindow(tk.Toplevel):
    def __init__(self, root, app):
        super().__init__(root)
        self.app = app
        self.title(i18n.t("card_morning"))
        self.configure(bg=BG)
        self.resizable(False, False)
        w, h = 480, 560
        px, py = root.winfo_rootx(), root.winfo_rooty()
        pw, ph = root.winfo_width(), root.winfo_height()
        self.geometry("%dx%d+%d+%d" % (w, h,
                                       px + max(0, (pw - w) // 2),
                                       py + max(40, (ph - h) // 2)))
        self.transient(root)
        self.attributes("-topmost", True)

        # 头部吉祥物 + 问候
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", pady=(18, 6))
        cnv = tk.Canvas(top, width=96, height=104, bg=BG, highlightthickness=0)
        cnv.pack(side="left", padx=(20, 6))
        photo, mw, mh = mascot_photo(90)
        cnv.create_image(48, 52, image=photo)
        cnv._photo = photo
        tk.Label(top, text=i18n.t("morning_brief"), bg=BG, fg=PRIMARY,
                 font=F(15, True), wraplength=320, justify="left", anchor="w"
                 ).pack(side="left", fill="both", expand=True, padx=8)

        body = tk.Frame(self, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1)
        body.pack(fill="both", expand=True, padx=20, pady=8)
        for title, lines in morning.build_brief(app.store):
            if title:
                tk.Label(body, text="♡ " + title, bg=CARD, fg=PRIMARY,
                         font=F(11, True), anchor="w").pack(
                    fill="x", padx=16, pady=(12, 2))
            for line in lines:
                tk.Label(body, text=line, bg=CARD, fg=TEXT, font=F(10),
                         anchor="w", wraplength=400, justify="left").pack(
                    fill="x", padx=22)

        self.status = tk.Label(self, text="", bg=BG, fg=TEXT_SUB, font=F(9))
        self.status.pack(fill="x", padx=22)
        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", padx=20, pady=(4, 16))
        ttk.Button(btns, text=i18n.t("ok"), command=self.destroy).pack(side="right")
        apps = list(app.store.settings.get("morning_apps", []))
        if apps:
            ttk.Button(btns, text=i18n.t("morning_start"),
                       style="Accent.TButton",
                       command=self._launch).pack(side="right", padx=(0, 10))
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _launch(self):
        apps = list(self.app.store.settings.get("morning_apps", []))

        def on_each(name):
            try:
                self.after(0, lambda: self.status.configure(
                    text=i18n.t("morning_launching", name)))
            except tk.TclError:
                pass

        morning.launch_apps(apps, on_each=on_each)
        self.after(max(3000, 2500 * len(apps) + 2000),
                   lambda: self.winfo_exists() and self.destroy())
