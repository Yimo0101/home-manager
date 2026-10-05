# -*- coding: utf-8 -*-
"""居家管家 - 日历页：月视图，点选日期直接添加 / 查看日程

- 每格显示：日期号 + 农历/节气/节日（节日优先，独占第二行，绝不重叠）
- 点格子只做原地颜色过渡动画，不重建整个月历（无闪烁）
- 支持方向键移动日期、PageUp/PageDown 切月、Home 回今天
- 导航栏显示距最近一个节气/节日的倒计时
"""
import calendar
import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import anniversaries as ann_mod
import holidays
import i18n
from ui_dialogs import AnniversaryDialog, EventDialog
from ui_style import (ANIM_MS, BG, BORDER, CARD, CHIP_BG, CHIP_OFF, F,
                      MARK_OFF, NUM_OFF, NUM_ON, PRIMARY_LIGHT, SEL_BG,
                      PRIMARY, TEXT, TEXT_SUB, freeze_window, morph_colors)

TERM_COLOR = "#3E9E7E"   # 节气青绿
FEST_COLOR = PRIMARY     # 节日玫瑰粉

_COUNTDOWN = {
    "zh": ("今天就是{name}呀♡", "距{name}还有 {n} 天 ♡"),
    "ja": ("今日は{name}です♡", "{name}まで あと{n}日 ♡"),
    "en": ("Today is {name} ♡", "{n} days until {name} ♡"),
}


class CalendarPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        today = datetime.date.today()
        self.year = today.year
        self.month = today.month
        self.selected = today
        self._cells = {}          # date -> 格子控件信息
        self._sel_cancel = None   # 选中动画取消句柄

        # 右侧当日日程（先 pack，保证固定宽度不被挤压）
        right = tk.Frame(self, bg=CARD, width=300, highlightbackground=BORDER,
                         highlightthickness=1)
        right.pack(side="right", fill="y", padx=(12, 24), pady=(20, 20))
        right.pack_propagate(False)
        self.day_title = tk.Label(right, text="", bg=CARD, fg=TEXT,
                                  font=F(14, True), anchor="w")
        self.day_title.pack(fill="x", padx=16, pady=(16, 6))
        ttk.Button(right, text=i18n.t("add_event"), style="Accent.TButton",
                   command=self.add_event).pack(fill="x", padx=16, pady=(0, 10))
        # 倒数日（固定在右侧面板底部，先于扩展区占位）
        ann_wrap = tk.Frame(right, bg=CARD, highlightbackground=BORDER,
                            highlightthickness=1)
        ann_wrap.pack(side="bottom", fill="x", padx=10, pady=(0, 12))
        head = tk.Frame(ann_wrap, bg=CARD)
        head.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(head, text="♡ " + i18n.t("ann_countdown"), bg=CARD, fg=TEXT,
                 font=F(11, True)).pack(side="left")
        tk.Button(head, text=i18n.t("ann_add"), bd=0, fg=PRIMARY, bg=CARD,
                  cursor="hand2", font=F(9, True), relief="flat",
                  activebackground=CARD, command=self.add_ann).pack(side="right")
        self.ann_box = tk.Frame(ann_wrap, bg=CARD)
        self.ann_box.pack(fill="x", padx=6, pady=(0, 8))
        list_wrap = tk.Frame(right, bg=CARD)
        list_wrap.pack(fill="both", expand=True, padx=8)
        self.day_list = list_wrap

        # 左侧日历
        left = tk.Frame(self, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(24, 12), pady=(20, 20))
        nav = tk.Frame(left, bg=BG)
        nav.pack(fill="x")
        ttk.Button(nav, text="‹", width=3, command=self.prev_month).pack(side="left")
        self.title_lbl = tk.Label(nav, text="", bg=BG, fg=TEXT,
                                  font=F(18, True), width=14)
        self.title_lbl.pack(side="left", padx=10)
        ttk.Button(nav, text="›", width=3, command=self.next_month).pack(side="left")
        ttk.Button(nav, text=i18n.t("today_btn"), style="Ghost.TButton",
                   command=self.go_today).pack(side="left", padx=12)
        # 距下一个节气/节日的倒计时
        self.count_lbl = tk.Label(left, text="", bg=BG, font=F(10, True),
                                  anchor="w")
        self.count_lbl.pack(fill="x", pady=(8, 0))

        grid_wrap = tk.Frame(left, bg=CARD, highlightbackground=BORDER,
                             highlightthickness=1, takefocus=True)
        grid_wrap.pack(fill="both", expand=True, pady=(10, 0))
        for c in range(7):
            tk.Label(grid_wrap, text=i18n.weekday_short(c), bg=CARD, fg=TEXT_SUB,
                     font=F(11, True)).grid(row=0, column=c, sticky="nsew", pady=(10, 6))
        for c in range(7):
            grid_wrap.columnconfigure(c, weight=1, uniform="cal")
        for r in range(1, 7):
            grid_wrap.rowconfigure(r, weight=1, uniform="cal")
        self.grid_wrap = grid_wrap
        # 键盘操作：方向键移动、PageUp/Down 切月、Home 回今天
        for seq in ("<Left>", "<Right>", "<Up>", "<Down>",
                    "<Prior>", "<Next>", "<Home>"):
            grid_wrap.bind(seq, self._on_key)
        self.refresh()

    # ---------- 月份导航 ----------
    def prev_month(self):
        y, m = self.year, self.month - 1
        if m == 0:
            y, m = y - 1, 12
        self.year, self.month = y, m
        self._frozen_refresh()

    def next_month(self):
        y, m = self.year, self.month + 1
        if m == 13:
            y, m = y + 1, 1
        self.year, self.month = y, m
        self._frozen_refresh()

    def go_today(self):
        t = datetime.date.today()
        self.year, self.month, self.selected = t.year, t.month, t
        self._frozen_refresh()

    def _frozen_refresh(self):
        """月份/语言变化时整月重建：冻结重绘，一次性刷新，杜绝逐格蹦出"""
        freeze_window(self.app.root, True)
        try:
            self.refresh()
            self.app.root.update_idletasks()
        finally:
            freeze_window(self.app.root, False)

    def _on_key(self, event):
        d = self.selected
        if event.keysym == "Left":
            d = d - datetime.timedelta(days=1)
        elif event.keysym == "Right":
            d = d + datetime.timedelta(days=1)
        elif event.keysym == "Up":
            d = d - datetime.timedelta(days=7)
        elif event.keysym == "Down":
            d = d + datetime.timedelta(days=7)
        elif event.keysym == "Prior":
            self.prev_month()
            return
        elif event.keysym == "Next":
            self.next_month()
            return
        elif event.keysym == "Home":
            self.go_today()
            return
        if (d.year, d.month) != (self.year, self.month):
            self.year, self.month = d.year, d.month
            self.selected = d
            self._frozen_refresh()
        else:
            self.select_day(d)

    # ---------- 渲染 ----------
    def refresh(self):
        self.title_lbl.configure(text=i18n.month_title(self.year, self.month))
        for w in self.grid_wrap.grid_slaves():
            if int(w.grid_info()["row"]) >= 1:
                w.destroy()
        self._cells = {}
        self._sel_cancel = None
        today = datetime.date.today()
        cal = calendar.Calendar(firstweekday=0).monthdatescalendar(self.year,
                                                                   self.month)
        events_by_day = {}
        for ev in self.app.store.events:
            events_by_day.setdefault(ev.get("date", ""), []).append(ev)
        ann_by_day = self._ann_map(cal)
        for r, week in enumerate(cal, start=1):
            for c, day in enumerate(week):
                self._make_cell(r, c, day, today,
                                sorted(events_by_day.get(
                                    day.strftime("%Y-%m-%d"), []),
                                    key=lambda e: (e.get("all_day"),
                                                  e.get("time", ""))),
                                ann_by_day.get(day, []))
        self._refresh_countdown()
        self._refresh_day_panel()
        self._refresh_ann_list()

    def _ann_map(self, cal):
        """本屏 42 天里每天对应的纪念日 {date: [item]}"""
        result = {}
        items = self.app.store.anniversaries
        if not items:
            return result
        days = [d for week in cal for d in week]
        for item in items:
            for d in days:
                try:
                    occ, days_left = ann_mod.next_occurrence(item, d)
                    if days_left == 0:
                        result.setdefault(d, []).append(item)
                except Exception:
                    continue
        return result

    def _make_cell(self, r, c, day, today, events, anns=None):
        in_month = day.month == self.month
        is_selected = day == self.selected
        bg = SEL_BG if is_selected else CARD
        cell = tk.Frame(self.grid_wrap, bg=bg,
                        highlightbackground=(PRIMARY if is_selected else BORDER),
                        highlightthickness=2, bd=0, cursor="hand2")
        cell.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)

        num_wrap = tk.Frame(cell, bg=bg)
        num_wrap.pack(fill="x", padx=6, pady=(4, 0))
        painted = [cell, num_wrap]

        # 第一行：日期号
        if day == today:
            cnv = tk.Canvas(num_wrap, width=24, height=24, bg=bg,
                            highlightthickness=0, cursor="hand2")
            cnv.pack(side="left")
            cnv.create_oval(2, 2, 22, 22, fill=PRIMARY, outline=PRIMARY)
            cnv.create_text(12, 13, text=str(day.day), fill="#FFFFFF",
                            font=F(10, True))
            painted.append(cnv)
        else:
            num_lbl = tk.Label(num_wrap, text=str(day.day), bg=bg,
                               fg=(NUM_ON if in_month else NUM_OFF),
                               font=F(11, True), cursor="hand2")
            num_lbl.pack(side="left")
            painted.append(num_lbl)

        # 第二行：农历 / 节气 / 节日（独占一行，从根上避免与数字重叠）
        mark_text, mark_kind = holidays.cell_label(day, i18n.get_lang())
        if not in_month:
            mark_fg = MARK_OFF
        elif mark_kind == "festival":
            mark_fg = FEST_COLOR
        elif mark_kind == "term":
            mark_fg = TERM_COLOR
        else:
            mark_fg = TEXT_SUB
        mark_lbl = tk.Label(cell, text=mark_text, bg=bg, fg=mark_fg,
                            font=F(8, mark_kind == "festival" and in_month),
                            anchor="w", cursor="hand2")
        mark_lbl.pack(fill="x", padx=6, anchor="w")
        painted.append(mark_lbl)

        # 用户日程 chips
        for ev in events[:2]:
            t = (i18n.t("cell_allday") if ev.get("all_day")
                 else (ev.get("time", "") + " ")) + ev.get("title", "")
            tk.Label(cell, text=self._truncate(t, 9),
                     bg=CHIP_BG if in_month else CHIP_OFF,
                     fg=TEXT if in_month else TEXT_SUB, font=F(8), anchor="w",
                     padx=4, pady=1).pack(fill="x", padx=4, pady=1)
        # 纪念日 ♡ 标记（最多显示 1 条，避免格子拥挤）
        for a in (anns or [])[:1]:
            chip = tk.Label(cell, text="♡ " + self._truncate(a.get("title", ""), 8),
                            bg=PRIMARY_LIGHT if in_month else CHIP_OFF,
                            fg=PRIMARY if in_month else TEXT_SUB, font=F(8, True),
                            anchor="w", padx=4, pady=1, cursor="hand2")
            chip.pack(fill="x", padx=4, pady=1)
            painted.append(chip)
        if len(events) > 2:
            more = tk.Label(cell, text=i18n.t("more_n", len(events) - 2),
                            bg=bg, fg=PRIMARY, font=F(8), anchor="w",
                            cursor="hand2")
            more.pack(fill="x", padx=6, anchor="w")
            painted.append(more)

        self._cells[day] = {"frame": cell, "painted": painted}
        self._bind_tree(cell, day)

    def _bind_tree(self, widget, day):
        widget.bind("<Button-1>", lambda e, d=day: self.select_day(d))
        widget.bind("<Double-Button-1>", lambda e, d=day: self.dbl_add(d))
        for ch in widget.winfo_children():
            self._bind_tree(ch, day)

    @staticmethod
    def _truncate(s, n):
        return s if len(s) <= n else s[:n] + "…"

    # ---------- 选中：只在被点的格子上做动画，其余地方纹丝不动 ----------
    def select_day(self, day, animate=True):
        if day == self.selected:
            self.grid_wrap.focus_set()
            return
        old_info = self._cells.get(self.selected)
        new_info = self._cells.get(day)
        self.selected = day
        if self._sel_cancel:
            self._sel_cancel()
            self._sel_cancel = None
        if old_info:
            self._apply_static(old_info, False)
        if new_info:
            if animate and old_info:
                items = []
                for w in new_info["painted"]:
                    items.append((w, "bg", CARD, SEL_BG))
                items.append((new_info["frame"], "highlightbackground",
                              BORDER, PRIMARY))
                if old_info:
                    for w in old_info["painted"]:
                        items.append((w, "bg", SEL_BG, CARD))
                    items.append((old_info["frame"], "highlightbackground",
                                  PRIMARY, BORDER))
                self._sel_cancel = morph_colors(self.app.root, items, ANIM_MS)
            else:
                self._apply_static(new_info, True)
        # 右侧信息原地原子刷新（冻结重绘，无闪烁）
        freeze_window(self.app.root, True)
        try:
            self._refresh_day_panel()
            self.app.root.update_idletasks()
        finally:
            freeze_window(self.app.root, False)
        self.grid_wrap.focus_set()

    @staticmethod
    def _apply_static(info, selected):
        bg = SEL_BG if selected else CARD
        border = PRIMARY if selected else BORDER
        for w in info["painted"]:
            try:
                w.configure(bg=bg)
            except tk.TclError:
                pass
        info["frame"].configure(highlightbackground=border)

    def dbl_add(self, day):
        self.selected = day
        if day not in self._cells:
            self.year, self.month = day.year, day.month
            self._frozen_refresh()
        self.add_event()

    # ---------- 节气/节日倒计时 ----------
    def _refresh_countdown(self):
        lang = i18n.get_lang()
        today = datetime.date.today()
        d = today
        name, kind = None, None
        for _ in range(400):
            fests = holidays.festivals_on(d, lang)
            if fests:
                name, kind = fests[0], "festival"
                break
            term = holidays.term_on(d, lang)
            if term:
                name, kind = term, "term"
                break
            d += datetime.timedelta(days=1)
        if not name:
            self.count_lbl.configure(text="")
            return
        today_tpl, future_tpl = _COUNTDOWN[lang]
        n = (d - today).days
        text = today_tpl.format(name=name) if n == 0 else future_tpl.format(
            name=name, n=n)
        self.count_lbl.configure(
            text=text, fg=(FEST_COLOR if kind == "festival" else TERM_COLOR))

    # ---------- 右侧当日列表 ----------
    def _refresh_day_panel(self):
        for w in self.day_list.winfo_children():
            w.destroy()
        d = self.selected
        today = datetime.date.today()
        suf = (i18n.t("today_suf") if d == today
               else i18n.t("tomorrow_suf") if d == today + datetime.timedelta(days=1)
               else "")
        self.day_title.configure(text=i18n.day_panel_title(d, suf))
        # 内置标记：节日 / 节气 / 农历（只读）
        for text, kind in holidays.panel_lines(d, i18n.get_lang()):
            self._mark_row(text, kind)
        events = sorted(
            [e for e in self.app.store.events if e.get("date") == d.strftime("%Y-%m-%d")],
            key=lambda e: (e.get("all_day"), e.get("time", "")))
        if not events:
            tk.Label(self.day_list, text=i18n.t("no_events"), bg=CARD, fg=TEXT_SUB,
                     font=F(10)).pack(pady=30)
            return
        for ev in events:
            self._event_row(ev)

    def _mark_row(self, text, kind):
        if kind == "festival":
            chip_bg, chip_fg, icon = "#FFE3EC", FEST_COLOR, "♡"
        elif kind == "term":
            chip_bg, chip_fg, icon = "#E4F3EC", TERM_COLOR, "❀"
        else:
            chip_bg, chip_fg, icon = "#F3F0F5", TEXT_SUB, "☾"
        row = tk.Frame(self.day_list, bg=chip_bg)
        row.pack(fill="x", pady=3, padx=4)
        tk.Label(row, text=icon + " " + text, bg=chip_bg, fg=chip_fg,
                 font=F(10, kind == "festival"), anchor="w").pack(
            side="left", padx=10, pady=6)

    def _event_row(self, ev):
        row = tk.Frame(self.day_list, bg=CHIP_BG)
        row.pack(fill="x", pady=4, padx=4)
        if ev.get("all_day"):
            when = i18n.t("all_day")
        else:
            when = ev.get("time", "")
            if ev.get("end_time"):
                when += "–" + ev["end_time"]
        tk.Label(row, text=when, bg=CHIP_BG, fg=PRIMARY, font=F(9, True),
                 width=11, anchor="w").pack(side="left", padx=(8, 4), pady=8)
        tk.Label(row, text=ev.get("title", ""), bg=CHIP_BG, fg=TEXT,
                 font=F(10), anchor="w").pack(side="left", fill="x", expand=True)
        tk.Button(row, text=i18n.t("edit_short"), bd=0, fg=PRIMARY, bg=CHIP_BG,
                  cursor="hand2", font=F(9), relief="flat",
                  activebackground=CHIP_BG,
                  command=lambda: self.edit_event(ev)).pack(side="right")
        tk.Button(row, text=i18n.t("del_short"), bd=0, fg="#F26D7D", bg=CHIP_BG,
                  cursor="hand2", font=F(9), relief="flat",
                  activebackground=CHIP_BG,
                  command=lambda: self.del_event(ev)).pack(side="right")

    def add_event(self):
        dlg = EventDialog(self.app.root, self.selected.strftime("%Y-%m-%d"))
        self.wait_window(dlg)
        if dlg.result:
            self.app.store.upsert_event(dlg.result)
            self.app.after_change()

    def edit_event(self, ev):
        dlg = EventDialog(self.app.root, ev.get("date", ""), dict(ev))
        self.wait_window(dlg)
        if dlg.result:
            self.app.store.upsert_event(dlg.result)
            self.app.after_change()

    def del_event(self, ev):
        if messagebox.askyesno(i18n.t("tip"),
                               i18n.t("del_event_confirm", ev.get("title")),
                               parent=self.app.root):
            self.app.store.delete_event(ev["id"])
            self.app.after_change()

    # ---------- 倒数日 ----------
    def _refresh_ann_list(self):
        for w in self.ann_box.winfo_children():
            w.destroy()
        rows = ann_mod.upcoming(self.app.store.anniversaries, limit=4)
        if not rows:
            tk.Label(self.ann_box, text=i18n.t("ann_empty"), bg=CARD, fg=TEXT_SUB,
                     font=F(9), wraplength=250, justify="left",
                     anchor="w").pack(fill="x", padx=8, pady=6)
            return
        for item, occ, days in rows:
            self._ann_row(item, occ, days)

    def _ann_row(self, item, occ, days):
        row = tk.Frame(self.ann_box, bg=PRIMARY_LIGHT)
        row.pack(fill="x", padx=6, pady=3)
        if days == 0:
            right_text = i18n.t("ann_today")
            right_fg = PRIMARY
        elif days > 0:
            right_text = i18n.t("ann_days_left", days)
            right_fg = TEXT
        else:
            right_text = i18n.t("ann_days_passed", abs(days))
            right_fg = TEXT_SUB
        inner = tk.Frame(row, bg=PRIMARY_LIGHT)
        inner.pack(side="left", fill="x", expand=True, padx=(8, 2), pady=5)
        tk.Label(inner, text="♡ " + item.get("title", ""), bg=PRIMARY_LIGHT,
                 fg=TEXT, font=F(9, True), anchor="w").pack(side="left")
        tk.Label(inner, text=ann_mod.coord_text(item, i18n.get_lang()),
                 bg=PRIMARY_LIGHT, fg=TEXT_SUB, font=F(8)).pack(side="left", padx=6)
        tk.Label(row, text=right_text, bg=PRIMARY_LIGHT, fg=right_fg,
                 font=F(9, True)).pack(side="left", padx=4)
        tk.Button(row, text="✎", bd=0, fg=PRIMARY, bg=PRIMARY_LIGHT, relief="flat",
                  cursor="hand2", activebackground=PRIMARY_LIGHT,
                  command=lambda: self.edit_ann(item)).pack(side="left")
        tk.Button(row, text="×", bd=0, fg="#F26D7D", bg=PRIMARY_LIGHT, relief="flat",
                  cursor="hand2", activebackground=PRIMARY_LIGHT,
                  command=lambda: self.del_ann(item)).pack(side="left", padx=(0, 4))

    def add_ann(self):
        dlg = AnniversaryDialog(self.app.root)
        self.wait_window(dlg)
        if dlg.result:
            self.app.store.upsert_anniversary(dlg.result)
            self.app.after_change()

    def edit_ann(self, item):
        dlg = AnniversaryDialog(self.app.root, dict(item))
        self.wait_window(dlg)
        if dlg.result:
            self.app.store.upsert_anniversary(dlg.result)
            self.app.after_change()

    def del_ann(self, item):
        if messagebox.askyesno(i18n.t("tip"),
                               i18n.t("del_event_confirm", item.get("title")),
                               parent=self.app.root):
            self.app.store.delete_anniversary(item["id"])
            self.app.after_change()
