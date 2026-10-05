# -*- coding: utf-8 -*-
"""居家管家 - 闹钟管理页"""
import tkinter as tk
from tkinter import messagebox, ttk

import nihongo
import i18n
from ui_dialogs import AlarmDialog
from ui_style import (BG, BORDER, CARD, CHIP_BG, F, PRIMARY, TEXT, TEXT_SUB,
                      ScrollableFrame, Switch)


class AlarmsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=28, pady=(22, 8))
        tk.Label(head, text="♡ " + i18n.t("alarms_title"), bg=BG, fg=TEXT,
                 font=F(20, True)).pack(side="left")
        tk.Label(head, text=i18n.t("alarms_sub"),
                 bg=BG, fg=TEXT_SUB, font=F(10)).pack(side="left", padx=14, pady=(8, 0))
        ttk.Button(head, text=i18n.t("add_alarm"), style="Accent.TButton",
                   command=self.add).pack(side="right")

        self._word_card()

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(6, 18))
        self.box = self.scroll.inner
        self.rows = {}   # id -> {"time": 时间标签}，供开关就地刷新
        self.refresh()

    def _word_card(self):
        w = nihongo.word_of_day()
        card = tk.Frame(self, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(fill="x", padx=24, pady=(0, 4))
        left = tk.Frame(card, bg=CARD)
        left.pack(side="left", padx=16, pady=10)
        tk.Label(left, text="♡ " + i18n.t("nihongo_title"), bg=CARD, fg=PRIMARY,
                 font=F(10, True)).pack(side="left")
        tk.Label(left, text=w["word"], bg=CARD, fg=TEXT, font=F(15, True)
                 ).pack(side="left", padx=(12, 6))
        tk.Label(left, text="[" + w["kana"] + "]", bg=CARD, fg=TEXT_SUB,
                 font=F(9)).pack(side="left")
        tk.Label(left, text=w["zh"], bg=CARD, fg=TEXT_SUB, font=F(10)
                 ).pack(side="left", padx=10)
        tk.Label(card, text=i18n.t("nihongo_example") + "：" + w["ex_ja"],
                 bg=CARD, fg=TEXT_SUB, font=F(9), anchor="e").pack(
            side="right", padx=16)

    def refresh(self):
        for w in self.box.winfo_children():
            w.destroy()
        self.rows = {}
        alarms = sorted(self.app.store.alarms, key=lambda a: a.get("time", "00:00"))
        if not alarms:
            tk.Label(self.box, text=i18n.t("no_alarms"),
                     bg=BG, fg=TEXT_SUB, font=F(11)).pack(pady=60)
            return
        for a in alarms:
            self._card(a)

    def _card(self, a):
        card = tk.Frame(self.box, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1, bd=0)
        card.pack(fill="x", expand=True, padx=10, pady=7)

        left = tk.Frame(card, bg=CARD)
        left.pack(side="left", padx=20, pady=14)
        enabled = a.get("enabled", True)
        color = PRIMARY if enabled else TEXT_SUB
        time_lbl = tk.Label(left, text=a.get("time", "--:--"), bg=CARD, fg=color,
                            font=F(30, True))
        time_lbl.pack(anchor="w")
        self.rows[a.get("id")] = {"time": time_lbl}
        tk.Label(left, text="♡ " + a.get("name", ""), bg=CARD, fg=TEXT,
                 font=F(12)).pack(anchor="w", pady=(2, 0))
        tk.Label(left, text=i18n.day_text(a.get("days", [])), bg=CARD, fg=TEXT_SUB,
                 font=F(10)).pack(anchor="w")

        right = tk.Frame(card, bg=CARD)
        right.pack(side="right", padx=20)
        sw = Switch(right, value=enabled, bg=CARD,
                    on_toggle=lambda v: self.toggle(a, v))
        sw.pack(side="left", padx=(0, 16))
        btns = tk.Frame(right, bg=CARD)
        btns.pack(side="left")
        ttk.Button(btns, text=i18n.t("edit"), style="Ghost.TButton",
                   command=lambda: self.edit(a)).pack(side="left", padx=4)
        ttk.Button(btns, text=i18n.t("delete"), style="Danger.TButton",
                   command=lambda: self.delete(a)).pack(side="left", padx=4)

    def add(self):
        dlg = AlarmDialog(self.app.root)
        self.wait_window(dlg)
        if dlg.result:
            self.app.store.upsert_alarm(dlg.result)
            self.app.after_change()

    def edit(self, a):
        dlg = AlarmDialog(self.app.root, dict(a))
        self.wait_window(dlg)
        if dlg.result:
            self.app.store.upsert_alarm(dlg.result)
            self.app.after_change()

    def delete(self, a):
        if messagebox.askyesno(i18n.t("tip"),
                               i18n.t("del_alarm_confirm", a.get("name")),
                               parent=self.app.root):
            self.app.store.delete_alarm(a["id"])
            self.app.after_change()

    def toggle(self, a, v):
        a["enabled"] = v
        self.app.store.upsert_alarm(a)
        # 只就地改时间颜色，不重建整页（开关动画本身已提供反馈）
        row = self.rows.get(a.get("id"))
        if row:
            row["time"].config(fg=PRIMARY if v else TEXT_SUB)
