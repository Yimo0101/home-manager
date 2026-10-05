# -*- coding: utf-8 -*-
"""居家管家 - 编辑对话框：闹钟 / 提醒 / 定时打开程序 / 日历日程（三语）"""
import datetime
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import i18n
from actions import (find_bettergi, find_window, get_cursor_pos, launch_task,
                     window_rect)
from media import SoundPlayer
from ui_style import (BG, BORDER, CARD, CHIP_BG, CHIP_OFF, F, PRIMARY, TEXT,
                      TEXT_SUB, TimePicker, WeekdayPicker)


def valid_hm(s):
    try:
        h, m = str(s).split(":")
        h, m = int(h), int(m)
        return 0 <= h <= 23 and 0 <= m <= 59
    except Exception:
        return False


def valid_date(s):
    try:
        datetime.datetime.strptime(str(s), "%Y-%m-%d")
        return True
    except Exception:
        return False


class Modal(tk.Toplevel):
    def __init__(self, parent, title, width=520, height=600):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.result = None
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + max(0, (pw - width) // 2)
        y = py + max(0, (ph - height) // 2 - 20)
        self.geometry("%dx%d+%d+%d" % (width, height, x, max(40, y)))
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=22, pady=(18, 8))
        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=22, pady=(0, 18))
        ttk.Button(footer, text=i18n.t("cancel"), command=self._cancel).pack(
            side="right", padx=(10, 0))
        ttk.Button(footer, text=i18n.t("ok"), style="Accent.TButton",
                   command=self._ok).pack(side="right")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def row(self, label, row):
        tk.Label(self.body, text=label, bg=BG, fg=TEXT_SUB, font=F(10),
                 anchor="w").grid(row=row, column=0, sticky="w", pady=(8, 2))

    def _ok(self):
        if self.validate():
            self.result = self.collect()
            self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()

    def validate(self):
        return True

    def collect(self):
        return {}


class RingImagePicker(tk.Frame):
    """铃声 + 背景图选择行"""

    def __init__(self, parent, ring="", image="", bg=BG):
        super().__init__(parent, bg=bg)
        self.ring = ring
        self.image = image
        self._player = SoundPlayer()
        self._thumb_img = None

        tk.Label(self, text=i18n.t("ringtone"), bg=bg, fg=TEXT_SUB, font=F(10)).grid(
            row=0, column=0, sticky="w", pady=4)
        self.ring_var = tk.StringVar(value=self._ring_name(ring))
        tk.Entry(self, textvariable=self.ring_var, width=30, state="readonly",
                 relief="solid", bd=1, highlightbackground=BORDER).grid(
            row=0, column=1, sticky="w", padx=8)
        ttk.Button(self, text=i18n.t("select"), width=5,
                   command=self.pick_ring).grid(row=0, column=2)
        self.preview_btn = ttk.Button(self, text=i18n.t("preview"), width=5,
                                      command=self.toggle_play)
        self.preview_btn.grid(row=0, column=3, padx=(8, 0))

        tk.Label(self, text=i18n.t("background"), bg=bg, fg=TEXT_SUB, font=F(10)).grid(
            row=1, column=0, sticky="w", pady=4)
        self.thumb = tk.Label(self, bg=CHIP_BG, width=22, height=6, bd=1, relief="solid")
        self.thumb.grid(row=1, column=1, sticky="w", padx=8, pady=(6, 4))
        btns = tk.Frame(self, bg=bg)
        btns.grid(row=1, column=2, columnspan=2, sticky="nw", padx=4, pady=(6, 0))
        ttk.Button(btns, text=i18n.t("choose_image"),
                   command=self.pick_image).pack(anchor="w")
        ttk.Button(btns, text=i18n.t("use_default_image"),
                   command=self.clear_image).pack(anchor="w", pady=6)
        self._show_thumb()

    @staticmethod
    def _ring_name(path):
        return os.path.basename(path) if path else i18n.t("default_ring")

    def pick_ring(self):
        p = filedialog.askopenfilename(
            title=i18n.t("choose_ring_title"),
            filetypes=[(i18n.t("audio_files"), "*.wav *.mp3 *.wma *.m4a"),
                       (i18n.t("all_files"), "*.*")])
        if p:
            self.stop_play()
            self.ring = p
            self.ring_var.set(os.path.basename(p))

    def toggle_play(self):
        if getattr(self, "_playing", False):
            self.stop_play()
        else:
            from media import resolve_ringtone
            p = resolve_ringtone({"default_ringtone": ""}, self.ring)
            if p and self._player.play(p, loop=False):
                self._playing = True
                self.preview_btn.configure(text=i18n.t("stop"))

    def stop_play(self):
        self._player.stop()
        self._playing = False
        try:
            self.preview_btn.configure(text=i18n.t("preview"))
        except tk.TclError:
            pass

    def pick_image(self):
        p = filedialog.askopenfilename(
            title=i18n.t("choose_bg_title"),
            filetypes=[(i18n.t("image_files"), "*.png *.jpg *.jpeg *.bmp *.gif"),
                       (i18n.t("all_files"), "*.*")])
        if p:
            self.image = p
            self._show_thumb()

    def clear_image(self):
        self.image = ""
        self._show_thumb()

    def _show_thumb(self):
        from PIL import Image, ImageTk
        from media import resolve_image
        p = resolve_image({"default_image": ""}, self.image)
        try:
            img = Image.open(p).convert("RGB")
            img.thumbnail((190, 100))
            self._thumb_img = ImageTk.PhotoImage(img)
            self.thumb.configure(image=self._thumb_img, width=img.width, height=img.height)
        except Exception:
            self.thumb.configure(image="", text=i18n.t("default_bg_text"),
                                 width=22, height=6)

    def destroy(self):
        self.stop_play()
        super().destroy()


class AlarmDialog(Modal):
    def __init__(self, parent, item=None):
        self.item = item or {"name": i18n.t("new_alarm"), "time": "07:00",
                             "days": list(range(7)),
                             "enabled": True, "ringtone": "", "image": ""}
        super().__init__(parent, i18n.t("dlg_alarm_title"), 560, 470)
        self._build()

    def _build(self):
        b = self.body
        self.row(i18n.t("alarm_name"), 0)
        self.name_var = tk.StringVar(value=self.item.get("name", ""))
        tk.Entry(b, textvariable=self.name_var, width=34, relief="solid", bd=1,
                 font=F(11)).grid(row=0, column=1, columnspan=3, sticky="w", padx=(10, 0))
        self.row(i18n.t("time"), 1)
        self.time = TimePicker(b, self.item.get("time", "07:00"), bg=BG)
        self.time.grid(row=1, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=6)
        self.row(i18n.t("repeat"), 2)
        self.days = WeekdayPicker(b, self.item.get("days", []), bg=BG)
        self.days.grid(row=2, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=6)
        self.row(i18n.t("ring_bg"), 3)
        self.picker = RingImagePicker(b, self.item.get("ringtone", ""),
                                      self.item.get("image", ""), bg=BG)
        self.picker.grid(row=3, column=1, columnspan=3, sticky="w", padx=(10, 0),
                         pady=(10, 0))

    def validate(self):
        if not self.name_var.get().strip():
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_alarm_name"), parent=self)
            return False
        if not valid_hm(self.time.get()):
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_time"), parent=self)
            return False
        if not self.days.get():
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_days"), parent=self)
            return False
        return True

    def collect(self):
        return {
            **self.item,
            "name": self.name_var.get().strip(),
            "time": self.time.get(),
            "days": self.days.get(),
            "ringtone": self.picker.ring,
            "image": self.picker.image,
        }


class RepeatMixin:
    """提醒/任务共用：重复星期 or 一次性日期"""

    def build_repeat(self, b, row, item):
        self.row(i18n.t("repeat"), row)
        wrap = tk.Frame(b, bg=BG)
        wrap.grid(row=row, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=6)
        self.mode_var = tk.StringVar(value="once" if item.get("date") else "repeat")
        ttk.Radiobutton(wrap, text=i18n.t("repeat_weekly"), variable=self.mode_var,
                        value="repeat", command=self._mode_change).pack(side="left")
        ttk.Radiobutton(wrap, text=i18n.t("once"), variable=self.mode_var,
                        value="once", command=self._mode_change).pack(side="left", padx=14)
        self.days = WeekdayPicker(b, item.get("days", list(range(7))), bg=BG)
        self.days.grid(row=row + 1, column=1, columnspan=3, sticky="w", padx=(10, 0))
        once = tk.Frame(b, bg=BG)
        once.grid(row=row + 2, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=4)
        tk.Label(once, text=i18n.t("date_label"), bg=BG, fg=TEXT_SUB).pack(side="left")
        d = item.get("date") or (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        self.date_var = tk.StringVar(value=d)
        tk.Entry(once, textvariable=self.date_var, width=12, relief="solid", bd=1,
                 font=F(10)).pack(side="left", padx=8)
        tk.Label(once, text=i18n.t("date_hint"), bg=BG, fg=TEXT_SUB,
                 font=F(9)).pack(side="left")
        self._once_frame = once
        self._mode_change()

    def _mode_change(self):
        if self.mode_var.get() == "repeat":
            self.days.grid()
            self._once_frame.grid_remove()
        else:
            self.days.grid_remove()
            self._once_frame.grid()

    def validate_repeat(self):
        if self.mode_var.get() == "repeat":
            if not self.days.get():
                messagebox.showwarning(i18n.t("tip"), i18n.t("warn_weekday"), parent=self)
                return False
        elif not valid_date(self.date_var.get()):
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_date"), parent=self)
            return False
        return True

    def collect_repeat(self):
        if self.mode_var.get() == "repeat":
            return {"days": self.days.get(), "date": ""}
        return {"days": [], "date": self.date_var.get().strip()}


class ReminderDialog(Modal, RepeatMixin):
    def __init__(self, parent, item=None):
        self.item = item or {"name": i18n.t("new_reminder"), "type": "reminder",
                             "time": "09:00",
                             "days": list(range(7)), "date": "", "enabled": True,
                             "message": "", "ringtone": "", "image": ""}
        super().__init__(parent, i18n.t("dlg_reminder_title"), 560, 560)
        self._build()

    def _build(self):
        b = self.body
        self.row(i18n.t("reminder_name"), 0)
        self.name_var = tk.StringVar(value=self.item.get("name", ""))
        tk.Entry(b, textvariable=self.name_var, width=40, relief="solid", bd=1,
                 font=F(11)).grid(row=0, column=1, columnspan=3, sticky="w", padx=(10, 0))
        self.row(i18n.t("time"), 1)
        self.time = TimePicker(b, self.item.get("time", "09:00"), bg=BG)
        self.time.grid(row=1, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=6)
        self.build_repeat(b, 2, self.item)
        self.row(i18n.t("message"), 5)
        self.msg = tk.Text(b, width=40, height=3, relief="solid", bd=1, font=F(10),
                           wrap="word")
        self.msg.grid(row=5, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=6)
        self.msg.insert("1.0", self.item.get("message", ""))
        self.row(i18n.t("ring_bg"), 6)
        self.picker = RingImagePicker(b, self.item.get("ringtone", ""),
                                      self.item.get("image", ""), bg=BG)
        self.picker.grid(row=6, column=1, columnspan=3, sticky="w", padx=(10, 0),
                         pady=(10, 0))

    def validate(self):
        if not self.name_var.get().strip():
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_reminder_name"), parent=self)
            return False
        if not valid_hm(self.time.get()):
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_time"), parent=self)
            return False
        return self.validate_repeat()

    def collect(self):
        return {
            **self.item,
            "type": "reminder",
            "name": self.name_var.get().strip(),
            "time": self.time.get(),
            "message": self.msg.get("1.0", "end").strip(),
            "ringtone": self.picker.ring,
            "image": self.picker.image,
            **self.collect_repeat(),
        }


class ProgramTaskDialog(Modal, RepeatMixin):
    def __init__(self, parent, item=None):
        self.item = item or {"name": i18n.t("default_program_name"), "type": "program",
                             "time": "08:30",
                             "days": list(range(7)), "date": "", "enabled": True,
                             "exe": "", "args": "", "window_title": "",
                             "wait_window": 30, "clicks": []}
        self.steps = [dict(s) for s in self.item.get("clicks", [])]
        super().__init__(parent, i18n.t("dlg_program_title"), 800, 700)
        self._build()

    def _build(self):
        b = self.body
        self.row(i18n.t("task_name"), 0)
        self.name_var = tk.StringVar(value=self.item.get("name", ""))
        tk.Entry(b, textvariable=self.name_var, width=52, relief="solid", bd=1,
                 font=F(11)).grid(row=0, column=1, columnspan=3, sticky="w", padx=(10, 0))
        self.row(i18n.t("exe_path"), 1)
        self.exe_var = tk.StringVar(value=self.item.get("exe", ""))
        tk.Entry(b, textvariable=self.exe_var, width=52, relief="solid", bd=1,
                 font=F(10)).grid(row=1, column=1, columnspan=3, sticky="w",
                                  padx=(10, 0), pady=(4, 0))
        row2 = tk.Frame(b, bg=BG)
        row2.grid(row=2, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=(4, 0))
        ttk.Button(row2, text=i18n.t("browse"), command=self._browse).pack(side="left")
        ttk.Button(row2, text=i18n.t("bettergi_tpl"),
                   command=self._apply_bettergi).pack(side="left", padx=8)
        ttk.Button(row2, text=i18n.t("test_run"),
                   command=self._test_run).pack(side="left")
        self.row(i18n.t("args"), 3)
        self.args_var = tk.StringVar(value=self.item.get("args", ""))
        tk.Entry(b, textvariable=self.args_var, width=36, relief="solid", bd=1,
                 font=F(10)).grid(row=3, column=1, columnspan=3, sticky="w",
                                  padx=(10, 0))
        self.row(i18n.t("win_title"), 4)
        winrow = tk.Frame(b, bg=BG)
        winrow.grid(row=4, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=(8, 0))
        self.win_var = tk.StringVar(value=self.item.get("window_title", ""))
        tk.Entry(winrow, textvariable=self.win_var, width=24, relief="solid", bd=1,
                 font=F(10)).pack(side="left")
        tk.Label(winrow, text=i18n.t("win_wait"), bg=BG, fg=TEXT_SUB,
                 font=F(10)).pack(side="left", padx=(16, 4))
        self.wait_var = tk.IntVar(value=int(self.item.get("wait_window", 30) or 30))
        ttk.Spinbox(winrow, from_=1, to=300, width=5,
                    textvariable=self.wait_var).pack(side="left")
        self.row(i18n.t("time"), 5)
        self.time = TimePicker(b, self.item.get("time", "08:30"), bg=BG)
        self.time.grid(row=5, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=6)
        self.build_repeat(b, 6, self.item)

        self.row(i18n.t("after_click"), 9)
        table = tk.Frame(b, bg=BG)
        table.grid(row=9, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=(6, 0))
        cols = ("delay", "pos", "act")
        self.tree = ttk.Treeview(table, columns=cols, height=4, show="headings")
        self.tree.heading("delay", text=i18n.t("col_wait"))
        self.tree.heading("pos", text=i18n.t("col_pos"))
        self.tree.heading("act", text=i18n.t("col_act"))
        self.tree.column("delay", width=80, anchor="center")
        self.tree.column("pos", width=230, anchor="center")
        self.tree.column("act", width=96, anchor="center")
        self.tree.pack(side="left")
        ops = tk.Frame(table, bg=BG)
        ops.pack(side="left", padx=10, anchor="n")
        ttk.Button(ops, text=i18n.t("add_click"), command=self._add_step).pack(
            fill="x", pady=2)
        ttk.Button(ops, text=i18n.t("pick_coord"), command=self._pick_selected).pack(
            fill="x", pady=2)
        ttk.Button(ops, text=i18n.t("toggle_double"), command=self._toggle_double).pack(
            fill="x", pady=2)
        ttk.Button(ops, text=i18n.t("del_selected"), command=self._del_step).pack(
            fill="x", pady=2)
        tk.Label(b, text=i18n.t("click_hint"),
                 bg=BG, fg=TEXT_SUB, font=F(9), wraplength=500, justify="left",
                 anchor="w").grid(
            row=10, column=1, columnspan=3, sticky="ew", padx=(10, 14), pady=(6, 0))
        self._refresh_tree()

    def _browse(self):
        p = filedialog.askopenfilename(
            title=i18n.t("choose_exe_title"),
            filetypes=[(i18n.t("exe_filter"), "*.exe *.lnk *.bat *.cmd"),
                       (i18n.t("all_files"), "*.*")])
        if p:
            self.exe_var.set(p)
            if not self.name_var.get().strip() or \
                    self.name_var.get() == i18n.t("default_program_name"):
                self.name_var.set(os.path.splitext(os.path.basename(p))[0])

    def _apply_bettergi(self):
        exe = self.exe_var.get().strip() or find_bettergi()
        if exe:
            self.exe_var.set(exe)
        self.win_var.set("BetterGI|更好的原神")
        self.wait_var.set(30)
        if not self.name_var.get().strip() or \
                self.name_var.get() == i18n.t("default_program_name"):
            self.name_var.set(i18n.t("bettergi_name"))
        # 基于 BetterGI 900x600 标准窗口比例：左侧栏「一条龙」→ 任务列表▶开始
        self.steps = [
            {"delay": 2, "x": 0, "y": 0, "rx": 47 / 900, "ry": 221 / 600,
             "double": False},
            {"delay": 1.5, "x": 0, "y": 0, "rx": 326 / 900, "ry": 65 / 600,
             "double": False},
        ]
        self._refresh_tree()
        if not exe:
            messagebox.showinfo(i18n.t("tip"),
                                i18n.t("bettergi_pick_exe"), parent=self)

    def _refresh_tree(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for i, s in enumerate(self.steps):
            if s.get("rx") is not None and s.get("ry") is not None:
                pos = i18n.t("pos_relative", round(float(s["rx"]) * 100, 1),
                             round(float(s["ry"]) * 100, 1))
            else:
                pos = "%d, %d" % (s.get("x", 0), s.get("y", 0))
            self.tree.insert("", "end", iid=str(i),
                             values=(s.get("delay", 2), pos,
                                     i18n.t("double_click") if s.get("double")
                                     else i18n.t("single_click")))

    def _add_step(self):
        self.steps.append({"delay": 3, "x": 0, "y": 0, "rx": None, "ry": None,
                           "double": False})
        self._refresh_tree()

    def _selected_index(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _del_step(self):
        i = self._selected_index()
        if i is not None:
            del self.steps[i]
            self._refresh_tree()

    def _toggle_double(self):
        i = self._selected_index()
        if i is not None:
            self.steps[i]["double"] = not self.steps[i].get("double")
            self._refresh_tree()
            self.tree.selection_set(str(i))

    def _pick_selected(self):
        i = self._selected_index()
        if i is None:
            messagebox.showinfo(i18n.t("tip"), i18n.t("pick_row_first"), parent=self)
            return
        rel = self.win_var.get().strip()
        CoordPicker(self, rel_title=rel,
                    on_pick=lambda x, y, rx=None, ry=None:
                    self._set_pos(i, x, y, rx, ry))

    def _set_pos(self, i, x, y, rx=None, ry=None):
        self.steps[i]["x"] = x
        self.steps[i]["y"] = y
        self.steps[i]["rx"] = rx
        self.steps[i]["ry"] = ry
        self._refresh_tree()
        self.tree.selection_set(str(i))

    def _test_run(self):
        if not self.validate():
            return
        data = self.collect()

        def work():
            try:
                launch_task(data)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    i18n.t("tip"), str(e), parent=self))
        threading.Thread(target=work, daemon=True).start()
        messagebox.showinfo(i18n.t("tip"), i18n.t("test_started"), parent=self)

    def validate(self):
        if not self.name_var.get().strip():
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_task_name"), parent=self)
            return False
        exe = self.exe_var.get().strip().strip('"')
        if not exe:
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_choose_exe"), parent=self)
            return False
        try:
            wait_s = int(self.wait_var.get())
            if not 1 <= wait_s <= 300:
                raise ValueError
        except (TypeError, ValueError, tk.TclError):
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_wait"), parent=self)
            return False
        if not valid_hm(self.time.get()):
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_time"), parent=self)
            return False
        for s in self.steps:
            has_rel = s.get("rx") is not None and s.get("ry") is not None
            has_abs = (s.get("x") or 0) != 0 or (s.get("y") or 0) != 0
            if not has_rel and not has_abs:
                messagebox.showwarning(i18n.t("tip"), i18n.t("warn_no_coord"),
                                       parent=self)
                return False
        return self.validate_repeat()

    def collect(self):
        return {
            **self.item,
            "type": "program",
            "name": self.name_var.get().strip(),
            "exe": self.exe_var.get().strip(),
            "args": self.args_var.get().strip(),
            "window_title": self.win_var.get().strip(),
            "wait_window": int(self.wait_var.get()),
            "time": self.time.get(),
            "clicks": self.steps,
            **self.collect_repeat(),
        }


class CoordPicker(tk.Toplevel):
    """全屏半透明坐标拾取：3 秒倒计时后拾取鼠标位置，点击立即拾取，Esc 取消"""

    def __init__(self, parent, on_pick, rel_title=None):
        super().__init__(parent)
        self.on_pick = on_pick
        self.rel_title = rel_title
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.28)
        self.w = self.winfo_screenwidth()
        self.h = self.winfo_screenheight()
        self.geometry("%dx%d+0+0" % (self.w, self.h))
        self.configure(bg="#000000")
        self.canvas = tk.Canvas(self, bg="#3A2230", highlightthickness=0,
                                width=self.w, height=self.h)
        self.canvas.pack(fill="both", expand=True)
        self.attributes("-alpha", 0.3)
        self.tip = tk.Toplevel(self)
        self.tip.overrideredirect(True)
        self.tip.attributes("-topmost", True)
        self.tip.configure(bg="#FFE3EC")
        self.count = 3
        self.label = tk.Label(self.tip, text="", bg="#FFE3EC", fg="#A04A63",
                              font=F(16, True), padx=26, pady=14)
        self.label.pack()
        self.tip.geometry("+%d+80" % (self.w // 2 - 200))
        self._tick_text()
        self.canvas.bind("<Motion>", self._move)
        self.canvas.bind("<Button-1>", lambda e: self._finish())
        self.bind("<Escape>", lambda e: self._cancel())
        self.tip.bind("<Escape>", lambda e: self._cancel())
        self.grab_set()
        self.focus_force()
        self._after = self.after(1000, self._countdown)

    def _tick_text(self):
        self.label.configure(text=i18n.t("pick_tip", self.count))

    def _countdown(self):
        self.count -= 1
        if self.count <= 0:
            self._finish()
        else:
            self._tick_text()
            self._after = self.after(1000, self._countdown)

    def _move(self, e):
        self.canvas.delete("cross")
        self.canvas.create_line(0, e.y, self.w, e.y, fill="#FFFFFF", width=2, tags="cross")
        self.canvas.create_line(e.x, 0, e.x, self.h, fill="#FFFFFF", width=2, tags="cross")
        self.canvas.create_oval(e.x - 8, e.y - 8, e.x + 8, e.y + 8,
                                outline="#F0729E", width=3, tags="cross")

    def _finish(self):
        try:
            self.after_cancel(self._after)
        except Exception:
            pass
        x, y = get_cursor_pos()
        rx = ry = None
        # 配置了目标窗口标题时，若点击落在该窗口内，自动换算为窗口相对比例
        if self.rel_title:
            try:
                hwnd = find_window(self.rel_title)
                rc = window_rect(hwnd) if hwnd else None
                if rc:
                    l, t, r, b = rc
                    if l <= x <= r and t <= y <= b:
                        rx = (x - l) / max(1, r - l)
                        ry = (y - t) / max(1, b - t)
            except Exception:
                rx = ry = None
        self.destroy()
        self.on_pick(x, y, rx, ry)

    def _cancel(self):
        try:
            self.after_cancel(self._after)
        except Exception:
            pass
        self.destroy()


class EventDialog(Modal):
    """日历日程"""

    def __init__(self, parent, date_str, item=None):
        self.item = item or {"title": "", "date": date_str, "all_day": False,
                             "time": "09:00", "end_time": "", "remind_minutes": 10,
                             "note": "", "reminded": False}
        self.remind_options = [
            (i18n.t("remind_on_time"), 0),
            (i18n.t("remind_m_before", 5), 5),
            (i18n.t("remind_m_before", 10), 10),
            (i18n.t("remind_m_before", 15), 15),
            (i18n.t("remind_m_before", 30), 30),
            (i18n.t("remind_h_before"), 60),
            (i18n.t("no_remind"), -1),
        ]
        super().__init__(parent, i18n.t("dlg_event_title"), 480, 560)
        self._build()

    def _build(self):
        b = self.body
        self.row(i18n.t("event_title"), 0)
        self.title_var = tk.StringVar(value=self.item.get("title", ""))
        tk.Entry(b, textvariable=self.title_var, width=34, relief="solid", bd=1,
                 font=F(11)).grid(row=0, column=1, columnspan=3, sticky="w", padx=(10, 0))
        self.row(i18n.t("date"), 1)
        self.date_var = tk.StringVar(value=self.item.get("date", ""))
        tk.Entry(b, textvariable=self.date_var, width=14, relief="solid", bd=1,
                 font=F(10)).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=6)
        tk.Label(b, text=i18n.t("date_hint"), bg=BG, fg=TEXT_SUB, font=F(9)
                 ).grid(row=1, column=2, columnspan=2, sticky="w")
        self.all_day = tk.BooleanVar(value=self.item.get("all_day", False))
        ttk.Checkbutton(b, text=i18n.t("all_day_check"), variable=self.all_day,
                        command=self._toggle_all_day).grid(
            row=2, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=4)
        self.row(i18n.t("start_time"), 3)
        self.time = TimePicker(b, self.item.get("time", "09:00"), bg=BG)
        self.time.grid(row=3, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=4)
        self.row(i18n.t("end_time"), 4)
        end_wrap = tk.Frame(b, bg=BG)
        end_wrap.grid(row=4, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=4)
        self.has_end = tk.BooleanVar(value=bool(self.item.get("end_time")))
        ttk.Checkbutton(end_wrap, text=i18n.t("set_end"), variable=self.has_end,
                        command=self._toggle_end).pack(side="left")
        self.end_time = TimePicker(end_wrap, self.item.get("end_time") or "10:00", bg=BG)
        self.end_time.pack(side="left", padx=12)
        self.row(i18n.t("remind"), 5)
        self.remind_var = tk.StringVar()
        self.remind_map = {text: val for text, val in self.remind_options}
        cur = self.item.get("remind_minutes", 10)
        for text, val in self.remind_options:
            if val == cur:
                self.remind_var.set(text)
        ttk.Combobox(b, textvariable=self.remind_var, state="readonly", width=18,
                     values=[t for t, _ in self.remind_options]).grid(
            row=5, column=1, sticky="w", padx=(10, 0), pady=4)
        self.row(i18n.t("note"), 6)
        self.note = tk.Text(b, width=38, height=4, relief="solid", bd=1, font=F(10),
                            wrap="word")
        self.note.grid(row=6, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=4)
        self.note.insert("1.0", self.item.get("note", ""))
        self._toggle_all_day()
        self._toggle_end()

    def _toggle_all_day(self):
        state = "disabled" if self.all_day.get() else "readonly"
        for child in self.time.winfo_children():
            if isinstance(child, ttk.Combobox):
                child.configure(state=state)

    def _toggle_end(self):
        state = "readonly" if self.has_end.get() else "disabled"
        for child in self.end_time.winfo_children():
            if isinstance(child, ttk.Combobox):
                child.configure(state=state)

    def validate(self):
        if not self.title_var.get().strip():
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_event_title"), parent=self)
            return False
        if not valid_date(self.date_var.get()):
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_date"), parent=self)
            return False
        if not self.all_day.get() and not valid_hm(self.time.get()):
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_start_time"), parent=self)
            return False
        return True

    def collect(self):
        all_day = self.all_day.get()
        end = ""
        if not all_day and self.has_end.get():
            end = self.end_time.get()
        return {
            **self.item,
            "title": self.title_var.get().strip(),
            "date": self.date_var.get().strip(),
            "all_day": all_day,
            "time": "" if all_day else self.time.get(),
            "end_time": end,
            "remind_minutes": self.remind_map.get(self.remind_var.get(), 10),
            "note": self.note.get("1.0", "end").strip(),
            "reminded": False,
        }


class AnniversaryDialog(Modal):
    """纪念日 / 倒数日（公历或农历，可每年重复）"""

    def __init__(self, parent, item=None):
        import datetime as _dt
        today = _dt.date.today().strftime("%Y-%m-%d")
        self.item = item or {"title": "", "date": today,
                             "calendar": "solar", "yearly": True}
        super().__init__(parent, i18n.t("ann_countdown"), 460, 380)
        self._build()

    def _build(self):
        b = self.body
        self.row(i18n.t("event_title"), 0)
        self.title_var = tk.StringVar(value=self.item.get("title", ""))
        tk.Entry(b, textvariable=self.title_var, width=32, relief="solid", bd=1,
                 font=F(11)).grid(row=0, column=1, columnspan=3, sticky="w",
                                 padx=(10, 0))
        self.row(i18n.t("date"), 1)
        self.date_var = tk.StringVar(value=self.item.get("date", ""))
        tk.Entry(b, textvariable=self.date_var, width=14, relief="solid", bd=1,
                 font=F(10)).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=6)
        self.date_hint = tk.Label(b, text="", bg=BG, fg=TEXT_SUB, font=F(9))
        self.date_hint.grid(row=1, column=2, columnspan=2, sticky="w")

        tk.Label(b, text="", bg=BG).grid(row=2, column=0, sticky="w")
        cal_row = tk.Frame(b, bg=BG)
        cal_row.grid(row=2, column=1, columnspan=3, sticky="w", padx=(10, 0), pady=4)
        self.cal_var = tk.StringVar(value=self.item.get("calendar", "solar"))
        self.cal_btns = {}
        for key in ("solar", "lunar"):
            btn = tk.Label(cal_row, text=i18n.t("ann_" + key), bg=CHIP_OFF,
                           fg=TEXT, font=F(10, True), padx=16, pady=5,
                           cursor="hand2")
            btn.pack(side="left", padx=(0, 10))
            btn.bind("<Button-1>", lambda e, k=key: self._set_cal(k))
            self.cal_btns[key] = btn

        self.yearly = tk.BooleanVar(value=self.item.get("yearly", True))
        ttk.Checkbutton(b, text=i18n.t("ann_yearly"), variable=self.yearly
                        ).grid(row=3, column=1, columnspan=3, sticky="w",
                               padx=(4, 0), pady=8)
        self._set_cal(self.cal_var.get())

    def _set_cal(self, k):
        self.cal_var.set(k)
        for key2, btn in self.cal_btns.items():
            btn.configure(bg=PRIMARY if key2 == k else CHIP_OFF,
                          fg="#FFFFFF" if key2 == k else TEXT)
        if k == "lunar":
            self.date_hint.configure(text=i18n.t("ann_lunar_hint"))
            self.yearly.set(True)
        else:
            self.date_hint.configure(text=i18n.t("date_hint"))

    def validate(self):
        if not self.title_var.get().strip():
            messagebox.showwarning(i18n.t("tip"), i18n.t("ann_need_title"), parent=self)
            return False
        if not valid_date(self.date_var.get()):
            messagebox.showwarning(i18n.t("tip"), i18n.t("warn_date"), parent=self)
            return False
        if self.cal_var.get() == "lunar":
            try:
                import anniversaries as _ann
                _ann.lunar_occurrence({"date": self.date_var.get().strip(),
                                       "calendar": "lunar"},
                                      __import__("datetime").date.today().year)
            except Exception:
                messagebox.showwarning(i18n.t("tip"), i18n.t("warn_date"), parent=self)
                return False
        return True

    def collect(self):
        return {
            **self.item,
            "title": self.title_var.get().strip(),
            "date": self.date_var.get().strip(),
            "calendar": self.cal_var.get(),
            "yearly": bool(self.yearly.get()),
        }
