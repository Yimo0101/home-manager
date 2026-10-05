# -*- coding: utf-8 -*-
"""居家管家 - 定时任务页（提醒 / 定时打开程序）"""
import os
import tkinter as tk
from tkinter import messagebox, ttk

import i18n
from ui_dialogs import ProgramTaskDialog, ReminderDialog
from ui_style import (BG, BORDER, CARD, F, GREEN, PRIMARY, TEXT, TEXT_SUB,
                      ScrollableFrame, Switch)


class TasksPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=28, pady=(22, 8))
        tk.Label(head, text="♡ " + i18n.t("tasks_title"), bg=BG, fg=TEXT,
                 font=F(20, True)).pack(side="left")
        tk.Label(head, text=i18n.t("tasks_sub"),
                 bg=BG, fg=TEXT_SUB, font=F(10)).pack(side="left", padx=14, pady=(8, 0))
        ttk.Button(head, text=i18n.t("add_program"), style="Ghost.TButton",
                   command=self.add_program).pack(side="right")
        ttk.Button(head, text=i18n.t("add_reminder"), style="Accent.TButton",
                   command=self.add_reminder).pack(side="right", padx=(0, 10))

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(6, 18))
        self.box = self.scroll.inner
        self.rows = {}   # id -> {"time": 时间标签}，供开关就地刷新
        self.refresh()

    def refresh(self):
        for w in self.box.winfo_children():
            w.destroy()
        self.rows = {}
        tasks = sorted(self.app.store.tasks, key=lambda a: a.get("time", "00:00"))
        if not tasks:
            tk.Label(self.box, text=i18n.t("no_tasks"), bg=BG, fg=TEXT_SUB,
                     font=F(11)).pack(pady=60)
            return
        for t in tasks:
            self._card(t)

    def _repeat_text(self, t):
        if t.get("days"):
            return i18n.day_text(t["days"])
        return i18n.t("once_date", t.get("date", ""))

    def _card(self, t):
        is_prog = t.get("type") == "program"
        tag_bg, tag_fg, tag = (("#E2F5EC", GREEN, i18n.t("tag_program")) if is_prog
                               else ("#FFE3EC", PRIMARY, i18n.t("tag_reminder")))
        card = tk.Frame(self.box, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1, bd=0)
        card.pack(fill="x", expand=True, padx=10, pady=7)

        left = tk.Frame(card, bg=CARD)
        left.pack(side="left", padx=20, pady=14)
        top = tk.Frame(left, bg=CARD)
        top.pack(anchor="w")
        enabled = t.get("enabled", True)
        time_lbl = tk.Label(top, text=t.get("time", "--:--"), bg=CARD,
                            fg=PRIMARY if enabled else TEXT_SUB,
                            font=F(26, True))
        time_lbl.pack(side="left")
        self.rows[t.get("id")] = {"time": time_lbl}
        tag_lbl = tk.Label(top, text=tag, bg=tag_bg, fg=tag_fg, font=F(9, True),
                           padx=8, pady=2)
        tag_lbl.pack(side="left", padx=12, pady=(6, 0))
        tk.Label(left, text=t.get("name", ""), bg=CARD, fg=TEXT,
                 font=F(12)).pack(anchor="w", pady=(2, 0))
        if is_prog:
            detail = os.path.basename(t.get("exe", "")) or i18n.t("no_exe")
            n = len(t.get("clicks", []))
            if n:
                detail += i18n.t("n_clicks", n)
        else:
            detail = t.get("message", "")
        tk.Label(left, text="%s　|　%s" % (self._repeat_text(t), detail),
                 bg=CARD, fg=TEXT_SUB, font=F(10), wraplength=460, justify="left",
                 anchor="w").pack(anchor="w", pady=(2, 0))

        right = tk.Frame(card, bg=CARD)
        right.pack(side="right", padx=20)
        Switch(right, value=enabled, bg=CARD,
               on_toggle=lambda v: self.toggle(t, v)).pack(side="left", padx=(0, 16))
        btns = tk.Frame(right, bg=CARD)
        btns.pack(side="left")
        ttk.Button(btns, text=i18n.t("edit"), style="Ghost.TButton",
                   command=lambda: self.edit(t)).pack(side="left", padx=4)
        ttk.Button(btns, text=i18n.t("delete"), style="Danger.TButton",
                   command=lambda: self.delete(t)).pack(side="left", padx=4)

    def add_reminder(self):
        dlg = ReminderDialog(self.app.root)
        self.wait_window(dlg)
        if dlg.result:
            self.app.store.upsert_task(dlg.result)
            self.app.after_change()

    def add_program(self):
        dlg = ProgramTaskDialog(self.app.root)
        self.wait_window(dlg)
        if dlg.result:
            self.app.store.upsert_task(dlg.result)
            self.app.after_change()

    def edit(self, t):
        cls = ProgramTaskDialog if t.get("type") == "program" else ReminderDialog
        dlg = cls(self.app.root, dict(t))
        self.wait_window(dlg)
        if dlg.result:
            self.app.store.upsert_task(dlg.result)
            self.app.after_change()

    def delete(self, t):
        if messagebox.askyesno(i18n.t("tip"),
                               i18n.t("del_task_confirm", t.get("name")),
                               parent=self.app.root):
            self.app.store.delete_task(t["id"])
            self.app.after_change()

    def toggle(self, t, v):
        t["enabled"] = v
        self.app.store.upsert_task(t)
        # 只就地改时间颜色，不重建整页（开关动画本身已提供反馈）
        row = self.rows.get(t.get("id"))
        if row:
            row["time"].config(fg=PRIMARY if v else TEXT_SUB)
