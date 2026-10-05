# -*- coding: utf-8 -*-
"""居家管家 - 设置页（含三语切换）"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import autostart
import i18n
from config import APP_VERSION, DATA_DIR
from media import SoundPlayer
from ui_style import (BG, BORDER, CARD, CHIP_BG, F, GREEN, ORANGE, PRIMARY,
                      TEXT, TEXT_SUB, ScrollableFrame, Switch, mascot_photo,
                      round_rect)
from wake import enable_wake_timers_elevated, query_wake_timer_status


class SettingsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._player = SoundPlayer()
        self._thumb = None

        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=28, pady=(22, 8))
        tk.Label(head, text="♡ " + i18n.t("settings_title"), bg=BG, fg=TEXT,
                 font=F(20, True)).pack(side="left")

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(6, 18))
        box = self.scroll.inner

        self._card_language(box)
        self._card_startup(box)
        self._card_wake(box)
        self._card_morning(box)
        self._card_media(box)
        self._card_data(box)
        self._card_update(box)
        self._card_about(box)

    # ---------- 界面语言 ----------
    def _card_language(self, box):
        card = self._card(box, i18n.t("card_language"))
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=4)
        cur = i18n.get_lang()
        for code, name in i18n.LANGS:
            style = "LangOn.TButton" if code == cur else "Lang.TButton"
            ttk.Button(row, text=name, style=style,
                       command=lambda c=code: self.app.change_language(c)
                       ).pack(side="left", padx=(0, 10))
        tk.Label(card, text=i18n.t("language_hint"), bg=CARD, fg=TEXT_SUB,
                 font=F(9), justify="left", anchor="w").pack(fill="x", pady=(8, 0))

    # ---------- 开机启动 ----------
    def _card_startup(self, box):
        card = self._card(box, i18n.t("card_startup"))
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=6)
        tk.Label(row, text=i18n.t("autostart"), bg=CARD, fg=TEXT,
                 font=F(11)).pack(side="left")
        Switch(row, value=autostart.is_enabled(), bg=CARD,
               on_toggle=self._toggle_autostart).pack(side="right")
        tk.Label(card, text=i18n.t("autostart_desc"),
                 bg=CARD, fg=TEXT_SUB, font=F(9), justify="left",
                 anchor="w").pack(fill="x")

    def _toggle_autostart(self, v):
        try:
            autostart.set_enabled(v)
            if autostart.is_enabled() != v:
                raise RuntimeError("registry verify failed")
            self.app.store.update_settings(autostart=v)
        except Exception as e:
            messagebox.showerror(i18n.t("set_failed"),
                                 i18n.t("autostart_fail", e), parent=self.app.root)

    # ---------- 唤醒 ----------
    def _card_wake(self, box):
        card = self._card(box, i18n.t("card_wake"))
        s = self.app.store.settings
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=6)
        tk.Label(row, text=i18n.t("wake_row"),
                 bg=CARD, fg=TEXT, font=F(11)).pack(side="left")
        Switch(row, value=s.get("wake_enabled", True), bg=CARD,
               on_toggle=lambda v: self.app.store.update_settings(wake_enabled=v)
               ).pack(side="right")

        status_row = tk.Frame(card, bg=CARD)
        status_row.pack(fill="x", pady=(6, 2))
        self.wake_status = tk.Label(status_row, text=i18n.t("wake_checking"),
                                    bg=CARD, fg=TEXT_SUB, font=F(10), anchor="w")
        self.wake_status.pack(side="left")
        ttk.Button(status_row, text=i18n.t("enable_wake_btn"),
                   command=self._enable_wake).pack(side="right")
        tk.Label(card, text=i18n.t("wake_desc"),
                 bg=CARD, fg=TEXT_SUB, font=F(9), justify="left", wraplength=640,
                 anchor="w").pack(fill="x", pady=(4, 0))
        ahead = tk.Frame(card, bg=CARD)
        ahead.pack(fill="x", pady=(8, 0))
        tk.Label(ahead, text=i18n.t("wake_ahead"), bg=CARD, fg=TEXT, font=F(10)
                 ).pack(side="left")
        self.ahead_var = tk.StringVar(value=i18n.t("seconds", s.get("wake_ahead_seconds", 20)))
        cb = ttk.Combobox(ahead, textvariable=self.ahead_var, state="readonly",
                          width=10, values=[i18n.t("seconds", v) for v in (10, 20, 30, 60)])
        cb.pack(side="left", padx=10)
        cb.bind("<<ComboboxSelected>>", self._change_ahead)

    def _change_ahead(self, _=None):
        import re
        m = re.search(r"\d+", self.ahead_var.get())
        if m:
            self.app.store.update_settings(wake_ahead_seconds=int(m.group()))

    def _enable_wake(self):
        ok = enable_wake_timers_elevated()
        if not ok:
            messagebox.showwarning(i18n.t("uac_cancel_title"),
                                   i18n.t("uac_cancel"), parent=self.app.root)
            return
        messagebox.showinfo(i18n.t("uac_done_title"), i18n.t("uac_done"),
                            parent=self.app.root)
        self.after(4000, self.refresh_wake_status)

    # ---------- 一键早安 ----------
    def _card_morning(self, box):
        card = self._card(box, i18n.t("card_morning"))
        s = self.app.store.settings
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=6)
        tk.Label(row, text=i18n.t("morning_row"), bg=CARD, fg=TEXT,
                 font=F(11)).pack(side="left")
        Switch(row, value=bool(s.get("morning_enabled", False)), bg=CARD,
               on_toggle=lambda v: self.app.store.update_settings(morning_enabled=v)
               ).pack(side="right")
        tk.Label(card, text=i18n.t("morning_desc"), bg=CARD, fg=TEXT_SUB,
                 font=F(9), justify="left", wraplength=640, anchor="w"
                 ).pack(fill="x")
        pick = tk.Frame(card, bg=CARD)
        pick.pack(fill="x", pady=(10, 0))
        self.morning_apps_var = tk.StringVar()
        tk.Label(pick, textvariable=self.morning_apps_var, bg=CARD, fg=TEXT_SUB,
                 font=F(10), anchor="w").pack(side="left")
        ttk.Button(pick, text=i18n.t("morning_pick"),
                   command=self._pick_morning_apps).pack(side="right", padx=4)
        ttk.Button(pick, text=i18n.t("morning_clear"),
                   command=self._clear_morning_apps).pack(side="right")
        self._refresh_morning_apps()

    def _refresh_morning_apps(self):
        apps = self.app.store.settings.get("morning_apps", [])
        if apps:
            self.morning_apps_var.set(
                i18n.t("morning_apps_n", len(apps)) + "："
                + "、".join(os.path.basename(p) for p in apps[:4])
                + ("…" if len(apps) > 4 else ""))
        else:
            self.morning_apps_var.set(i18n.t("morning_pick"))

    def _pick_morning_apps(self):
        files = filedialog.askopenfilenames(
            title=i18n.t("morning_pick"),
            filetypes=[(i18n.t("all_files"), "*.exe *.lnk *.bat *.url"),
                       (i18n.t("all_files"), "*.*")])
        if files:
            apps = list(self.app.store.settings.get("morning_apps", []))
            for f in files:
                if f not in apps:
                    apps.append(f)
            self.app.store.update_settings(morning_apps=apps)
            self._refresh_morning_apps()

    def _clear_morning_apps(self):
        self.app.store.update_settings(morning_apps=[])
        self._refresh_morning_apps()

    # ---------- 版本与更新 ----------
    def _card_update(self, box):
        card = self._card(box, i18n.t("card_update"))
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x")
        self.update_status = tk.Label(row, text="v" + APP_VERSION, bg=CARD,
                                      fg=TEXT_SUB, font=F(10), anchor="w")
        self.update_status.pack(side="left")
        ttk.Button(row, text=i18n.t("update_check"),
                   command=self._check_update).pack(side="right")

    def _check_update(self):
        import updater
        self.update_status.configure(text=i18n.t("update_checking"))

        def ok(version, notes, page, zip_url):
            if not version:
                self.update_status.configure(text="v" + APP_VERSION)
                messagebox.showinfo(i18n.t("card_update"),
                                    i18n.t("update_latest"), parent=self.app.root)
                return
            if not updater.is_newer(version):
                self.update_status.configure(text="v" + APP_VERSION)
                messagebox.showinfo(i18n.t("card_update"),
                                    i18n.t("update_latest"), parent=self.app.root)
                return
            self.update_status.configure(text="v" + version)
            yes = messagebox.askyesno(
                i18n.t("card_update"),
                i18n.t("update_found", version) + "\n\n" + notes[:600],
                parent=self.app.root)
            if not yes:
                if page:
                    updater.open_page(page)
                return

            def status(phase):
                txt = {"download": i18n.t("update_checking"),
                       "install": i18n.t("update_checking")}.get(phase, "")
                self.update_status.configure(text=txt)

            def done(result):
                if result == "browser":
                    return
                if result == "restart":
                    self.app.root.after(300, self.app.quit_app)
                else:
                    self.update_status.configure(text=i18n.t("update_fail"))

            updater.apply_update(self.app.root, zip_url, page, status, done)

        def err(e):
            self.update_status.configure(text="v" + APP_VERSION)
            messagebox.showwarning(i18n.t("card_update"),
                                   i18n.t("update_fail"), parent=self.app.root)

        updater.check_latest(self.app.root, ok, err)

    def refresh(self):
        """切到设置页 / 数据变化时轻量刷新（不跑 powercfg）"""
        s = self.app.store.settings
        self.ring_var.set(
            os.path.basename(s.get("default_ringtone", "")) or i18n.t("builtin_ring"))
        self.snooze_var.set(i18n.t("minutes", s.get("snooze_minutes", 5)))
        self.ahead_var.set(i18n.t("seconds", s.get("wake_ahead_seconds", 20)))
        self._show_thumb()
        try:
            self._refresh_morning_apps()
        except Exception:
            pass

    def refresh_wake_status(self):
        ac, dc, _ = query_wake_timer_status()
        if ac is None and dc is None:
            self.wake_status.configure(text=i18n.t("wake_unknown"), fg=TEXT_SUB)
            return
        on = (ac is True) or (dc is True)

        def word(v):
            if v is True:
                return i18n.t("wake_allow")
            if v is False:
                return i18n.t("wake_deny")
            return i18n.t("wake_unk")

        text = i18n.t("wake_status",
                      i18n.t("wake_on") if on else i18n.t("wake_off"),
                      word(ac), word(dc))
        self.wake_status.configure(text=text, fg=GREEN if on else ORANGE)

    # ---------- 默认铃声 / 背景 ----------
    def _card_media(self, box):
        card = self._card(box, i18n.t("card_media"))
        s = self.app.store.settings

        r = tk.Frame(card, bg=CARD)
        r.pack(fill="x", pady=4)
        tk.Label(r, text=i18n.t("default_ring_row"), bg=CARD, fg=TEXT, font=F(10),
                 width=12, anchor="w").pack(side="left")
        self.ring_var = tk.StringVar(
            value=os.path.basename(s.get("default_ringtone", "")) or i18n.t("builtin_ring"))
        tk.Entry(r, textvariable=self.ring_var, state="readonly", width=34,
                 relief="solid", bd=1).pack(side="left", padx=6)
        ttk.Button(r, text=i18n.t("select"), command=self._pick_ring).pack(side="left", padx=3)
        self.preview_btn = ttk.Button(r, text=i18n.t("preview"), command=self._preview_ring)
        self.preview_btn.pack(side="left", padx=3)
        ttk.Button(r, text=i18n.t("reset_builtin"), command=self._reset_ring).pack(
            side="left", padx=3)

        i = tk.Frame(card, bg=CARD)
        i.pack(fill="x", pady=(10, 4))
        tk.Label(i, text=i18n.t("default_bg_row"), bg=CARD, fg=TEXT, font=F(10),
                 width=12, anchor="w").pack(side="left", anchor="n")
        self.img_lbl = tk.Label(i, bg=CHIP_BG, bd=1, relief="solid")
        self.img_lbl.pack(side="left", padx=6)
        ops = tk.Frame(i, bg=CARD)
        ops.pack(side="left", padx=6, anchor="n")
        ttk.Button(ops, text=i18n.t("choose_image"), command=self._pick_image).pack(anchor="w")
        ttk.Button(ops, text=i18n.t("reset_builtin"), command=self._reset_image).pack(
            anchor="w", pady=6)
        self._show_thumb()

        sn = tk.Frame(card, bg=CARD)
        sn.pack(fill="x", pady=(10, 0))
        tk.Label(sn, text=i18n.t("snooze_len"), bg=CARD, fg=TEXT, font=F(10),
                 width=12, anchor="w").pack(side="left")
        self.snooze_var = tk.StringVar(value=i18n.t("minutes", s.get("snooze_minutes", 5)))
        cb = ttk.Combobox(sn, textvariable=self.snooze_var, state="readonly", width=10,
                          values=[i18n.t("minutes", v) for v in (5, 10, 15)])
        cb.pack(side="left", padx=6)
        cb.bind("<<ComboboxSelected>>", self._change_snooze)

    def _change_snooze(self, _=None):
        import re
        m = re.search(r"\d+", self.snooze_var.get())
        if m:
            self.app.store.update_settings(snooze_minutes=int(m.group()))

    def _pick_ring(self):
        p = filedialog.askopenfilename(
            title=i18n.t("choose_ring_title"),
            filetypes=[(i18n.t("audio_files"), "*.wav *.mp3 *.wma *.m4a"),
                       (i18n.t("all_files"), "*.*")])
        if p:
            self._player.stop()
            self.preview_btn.configure(text=i18n.t("preview"))
            self.app.store.update_settings(default_ringtone=p)
            self.ring_var.set(os.path.basename(p))

    def _reset_ring(self):
        self._player.stop()
        self.preview_btn.configure(text=i18n.t("preview"))
        self.app.store.update_settings(default_ringtone="")
        self.ring_var.set(i18n.t("builtin_ring"))

    def _preview_ring(self):
        from media import resolve_ringtone
        p = resolve_ringtone(self.app.store.settings, "")
        if self._player.play(p, loop=False):
            self.preview_btn.configure(text=i18n.t("stop"))
            self.after(3000, self._stop_preview)

    def _stop_preview(self):
        self._player.stop()
        try:
            self.preview_btn.configure(text=i18n.t("preview"))
        except tk.TclError:
            pass

    def _pick_image(self):
        p = filedialog.askopenfilename(
            title=i18n.t("choose_bg_title"),
            filetypes=[(i18n.t("image_files"), "*.png *.jpg *.jpeg *.bmp *.gif"),
                       (i18n.t("all_files"), "*.*")])
        if p:
            self.app.store.update_settings(default_image=p)
            self._show_thumb()

    def _reset_image(self):
        self.app.store.update_settings(default_image="")
        self._show_thumb()

    def _show_thumb(self):
        from PIL import Image, ImageTk
        from media import resolve_image
        p = resolve_image(self.app.store.settings, "")
        try:
            img = Image.open(p).convert("RGB")
            img.thumbnail((180, 100))
            self._thumb = ImageTk.PhotoImage(img)
            self.img_lbl.configure(image=self._thumb, width=img.width, height=img.height,
                                   text="")
        except Exception:
            self.img_lbl.configure(image="", text=i18n.t("default_bg_text"),
                                   width=20, height=6)

    # ---------- 数据 ----------
    def _card_data(self, box):
        card = self._card(box, i18n.t("card_data"))
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x")
        tk.Label(row, text=i18n.t("data_saved", DATA_DIR), bg=CARD, fg=TEXT_SUB,
                 font=F(9), anchor="w").pack(side="left")
        ttk.Button(row, text=i18n.t("open_data_folder"), style="Ghost.TButton",
                   command=lambda: os.startfile(DATA_DIR)).pack(side="right")
        tk.Label(card, text=i18n.t("data_desc"),
                 bg=CARD, fg=TEXT_SUB, font=F(9), anchor="w", justify="left"
                 ).pack(fill="x", pady=(6, 0))

    # ---------- 关于 ----------
    def _card_about(self, box):
        card = self._card(box, i18n.t("card_about"))
        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x")
        # 左侧吉祥物贴纸卡
        cnv = tk.Canvas(top, width=150, height=175, bg=CARD, highlightthickness=0)
        cnv.pack(side="left", padx=(0, 16))
        photo, mw, mh = mascot_photo(120)
        round_rect(cnv, 12, 8, 138, 168, r=20, fill=CHIP_BG, outline=BORDER)
        cnv.create_image(75, 88, image=photo)
        cnv._photo = photo
        info = tk.Frame(top, bg=CARD)
        info.pack(side="left", fill="both", expand=True, pady=(18, 0))
        tk.Label(info, text=i18n.t("about_line1", APP_VERSION), bg=CARD, fg=TEXT,
                 font=F(12, True), anchor="w").pack(fill="x")
        tk.Label(info, text=i18n.t("about_line2"), bg=CARD, fg=TEXT_SUB,
                 font=F(9), anchor="w", wraplength=440, justify="left").pack(
            fill="x", pady=(6, 0))
        tk.Label(info, text="♡ " + i18n.t("theme_note"), bg=CARD, fg=PRIMARY,
                 font=F(9, True), anchor="w").pack(fill="x", pady=(8, 0))

    def _card(self, box, title):
        outer = tk.Frame(box, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        outer.pack(fill="x", expand=True, padx=10, pady=8)
        tk.Label(outer, text=title, bg=CARD, fg=TEXT, font=F(13, True),
                 anchor="w").pack(fill="x", padx=18, pady=(14, 6))
        body = tk.Frame(outer, bg=CARD)
        body.pack(fill="x", padx=18, pady=(0, 16))
        return body
