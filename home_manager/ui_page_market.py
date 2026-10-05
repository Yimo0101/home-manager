# -*- coding: utf-8 -*-
"""居家管家 - 资源集市页（壁纸 / 铃声白噪音 / 吉祥物装扮 / 链接下载）

所有联网操作走 net.py 后台线程，回调在主线程刷新；
标签页切换只 tkraise 预建好的帧，不重建、不闪烁。
"""
import io
import os
import tkinter as tk
from tkinter import filedialog, ttk

import i18n
import net
import ambient
from config import AUDIO_DIR, MASCOT_DIR, WALLPAPER_DIR
from media import SoundPlayer
from ui_style import (BG, BORDER, CARD, CHIP_BG, CHIP_OFF, F, PRIMARY,
                      TEXT, TEXT_SUB, ScrollableFrame, mascot_photo,
                      round_rect, set_mascot)

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None


class MarketPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._player = SoundPlayer()
        self._preview_btn = None
        self._thumbs = []          # 防 PhotoImage 回收
        self._tab = "wallpaper"
        self._category = "waifu"
        self._loaded_cat = None
        self._wp_gen = 0          # 壁纸加载批次号，丢弃过期回调

        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=28, pady=(22, 6))
        tk.Label(head, text="♡ " + i18n.t("market_title"), bg=BG, fg=TEXT,
                 font=F(20, True)).pack(side="left")
        tk.Label(self, text=i18n.t("market_sub"), bg=BG, fg=TEXT_SUB,
                 font=F(10)).pack(anchor="w", padx=30)

        # 标签胶囊
        tabs = tk.Frame(self, bg=BG)
        tabs.pack(fill="x", padx=26, pady=(8, 4))
        self._tab_btns = {}
        for key in ("wallpaper", "ringtone", "mascot", "download"):
            b = tk.Label(tabs, text=i18n.t("tab_" + key), bg=CHIP_OFF, fg=TEXT,
                         font=F(11, True), padx=18, pady=7, cursor="hand2")
            b.pack(side="left", padx=(0, 10))
            b.bind("<Button-1>", lambda e, k=key: self._switch(k))
            self._tab_btns[key] = b

        self._holder = tk.Frame(self, bg=BG)
        self._holder.pack(fill="both", expand=True, padx=18, pady=(2, 14))
        self._frames = {}
        for key, builder in (("wallpaper", self._build_wallpaper),
                             ("ringtone", self._build_ringtone),
                             ("mascot", self._build_mascot),
                             ("download", self._build_download)):
            f = tk.Frame(self._holder, bg=BG)
            f.place(x=0, y=0, relwidth=1, relheight=1)
            self._frames[key] = f
            builder(f)
        self._switch("wallpaper")

    # ---------- 标签切换（仅抬升，无重建） ----------
    def _switch(self, key):
        self._tab = key
        for k, b in self._tab_btns.items():
            b.configure(bg=PRIMARY if k == key else CHIP_OFF,
                        fg="#FFFFFF" if k == key else TEXT)
        self._frames[key].tkraise()
        if key == "wallpaper" and self._loaded_cat != self._category:
            self._load_wallpapers()
        elif key == "ringtone":
            self._refresh_ringtones()
        elif key == "mascot":
            self._refresh_mascot()

    def refresh(self):
        pass

    # ---------- 壁纸 ----------
    def _build_wallpaper(self, f):
        bar = tk.Frame(f, bg=BG)
        bar.pack(fill="x", padx=8, pady=(2, 6))
        cats = net.NEKOS_CATEGORIES
        self._cat_btns = {}
        for cat in cats:
            label = i18n.t("cat_" + cat) if i18n.has("cat_" + cat) else cat
            b = tk.Label(bar, text=label, bg=CHIP_OFF, fg=TEXT_SUB, font=F(9),
                         padx=12, pady=4, cursor="hand2")
            b.pack(side="left", padx=(0, 8))
            b.bind("<Button-1>", lambda e, c=cat: self._change_category(c))
            self._cat_btns[cat] = b
        tk.Label(bar, text=i18n.t("market_more"), bg=PRIMARY, fg="#FFFFFF",
                 font=F(10, True), padx=14, pady=5, cursor="hand2"
                 ).pack(side="right")
        bar.winfo_children()[-1].bind("<Button-1>",
                                      lambda e: self._load_wallpapers(force=True))
        self.more_btn = bar.winfo_children()[-1]

        self.wp_status = tk.Label(f, text="", bg=BG, fg=TEXT_SUB, font=F(10))
        self.wp_status.pack(anchor="w", padx=10)
        self.wp_scroll = ScrollableFrame(f)
        self.wp_scroll.pack(fill="both", expand=True, padx=6, pady=4)
        self.wp_grid = self.wp_scroll.inner
        self.scroll = self.wp_scroll

    def _change_category(self, cat):
        if cat == self._category:
            return
        self._category = cat
        for c, b in self._cat_btns.items():
            b.configure(bg=PRIMARY if c == cat else CHIP_OFF,
                        fg="#FFFFFF" if c == cat else TEXT_SUB)
        self._load_wallpapers()

    def _load_wallpapers(self, force=False):
        # 列表返回前保留旧网格，避免切换时整页空白闪烁
        self._wp_gen += 1
        gen = self._wp_gen
        self.wp_status.configure(text=i18n.t("market_loading"))

        def ok(items):
            self._show_wallpapers(items, gen)

        def err(e):
            if gen != self._wp_gen or not self.wp_status.winfo_exists():
                return
            # 已有旧内容时保留，只在空白网格上提示失败
            if not self.wp_grid.winfo_children():
                self.wp_status.configure(text=i18n.t("market_fail"))
            else:
                self.wp_status.configure(text="")

        net.fetch_wallpapers(
            self.app.root, self._category, 9,
            on_ok=ok, on_err=err, force=force)

    def _show_wallpapers(self, items, gen):
        if gen != self._wp_gen:
            return
        if not self.wp_status.winfo_exists():
            return
        self.wp_status.configure(text="")
        if not items:
            if not self.wp_grid.winfo_children():
                self.wp_status.configure(text=i18n.t("market_fail"))
            return
        for w in self.wp_grid.winfo_children():
            w.destroy()
        self._thumbs = []
        self._loaded_cat = self._category
        for col in range(3):
            self.wp_grid.columnconfigure(col, weight=1)
        for i, item in enumerate(items):
            self._make_thumb_card(self.wp_grid, item, i // 3, i % 3)

    def _make_thumb_card(self, parent, item, r, c):
        card = tk.Frame(parent, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1)
        card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
        cnv = tk.Label(card, bg=CHIP_BG, width=46, height=12, text="…")
        cnv.pack(fill="x", padx=10, pady=(10, 6))

        def show(data):
            if not cnv.winfo_exists():
                return
            try:
                img = Image.open(io.BytesIO(data))
                ph = ImageTk.PhotoImage(img)
                self._thumbs.append(ph)
                cnv.configure(image=ph, text="", width=ph.width(),
                              height=ph.height())
                cnv.image = ph
            except Exception:
                pass

        net.fetch_thumb(self.app.root, item["thumb"],
                        on_ok=show, on_err=lambda e: None,
                        resize=item.get("resize", False),
                        remember=item.get("remember", False))

        title = item["title"]
        if i18n.has("cat_" + str(title)):
            title = i18n.t("cat_" + str(title))
        tk.Label(card, text=str(title)[:18], bg=CARD, fg=TEXT_SUB,
                 font=F(8), wraplength=220, justify="center").pack(padx=8)
        ops = tk.Frame(card, bg=CARD)
        ops.pack(pady=(2, 10))
        ttk.Button(ops, text=i18n.t("market_set_bg"),
                   command=lambda u=item["url"]: self._download_wallpaper(u, "bg")
                   ).pack(side="left", padx=3)
        ttk.Button(ops, text=i18n.t("market_set_mascot"),
                   command=lambda u=item["url"]: self._download_wallpaper(u, "mascot")
                   ).pack(side="left", padx=3)

    def _download_wallpaper(self, url, purpose):
        self.wp_status.configure(text=i18n.t("market_loading"))
        kind_hint = "image"

        def ok(path, kind):
            self.wp_status.configure(text="")
            if purpose == "bg":
                self.app.store.update_settings(default_image=path)
                self._toast(i18n.t("market_saved_bg"))
            else:
                self._apply_mascot(path, toast=True)

        net.download(self.app.root, url, WALLPAPER_DIR, kind_hint=kind_hint,
                     on_ok=ok,
                     on_err=lambda e: self.wp_status.configure(text=i18n.t("market_fail")))

    # ---------- 铃声 / 白噪音 ----------
    def _build_ringtone(self, f):
        top = tk.Frame(f, bg=BG)
        top.pack(fill="x", padx=10, pady=(4, 8))
        tk.Label(top, text=i18n.t("market_ring_hint"), bg=BG, fg=TEXT_SUB,
                 font=F(9), justify="left", wraplength=720).pack(side="left")
        self.ring_scroll = ScrollableFrame(f)
        self.ring_scroll.pack(fill="both", expand=True, padx=6)
        self.ring_box = self.ring_scroll.inner

    def _refresh_ringtones(self):
        for w in self.ring_box.winfo_children():
            w.destroy()
        try:
            ambient.ensure_all()
        except Exception:
            pass
        files = []
        if os.path.isdir(AUDIO_DIR):
            for n in sorted(os.listdir(AUDIO_DIR)):
                if os.path.splitext(n)[1].lower() in (".wav", ".mp3", ".m4a", ".wma", ".ogg"):
                    files.append(os.path.join(AUDIO_DIR, n))
        s = self.app.store.settings
        cur = s.get("default_ringtone", "")
        for path in files:
            self._make_ring_row(path, cur)

    def _make_ring_row(self, path, current):
        row = tk.Frame(self.ring_box, bg=CARD, highlightbackground=BORDER,
                       highlightthickness=1)
        row.pack(fill="x", padx=8, pady=5)
        tk.Label(row, text="♪ " + os.path.basename(path), bg=CARD, fg=TEXT,
                 font=F(11), anchor="w").pack(side="left", padx=14, pady=12)
        is_cur = os.path.abspath(path) == os.path.abspath(current) if current else False
        preview = ttk.Button(row, text=i18n.t("preview"),
                             command=lambda: self._preview(path, preview))
        preview.pack(side="right", padx=6, pady=8)
        ttk.Button(row, text=i18n.t("default_ring"),
                   command=lambda: self._set_default_ring(path)
                   ).pack(side="right", padx=6)
        if is_cur:
            tk.Label(row, text="♥", bg=CARD, fg=PRIMARY, font=F(12, True)
                     ).pack(side="right", padx=4)

    def _preview(self, path, btn):
        if self._preview_btn is not None:
            try:
                self._preview_btn.configure(text=i18n.t("preview"))
            except tk.TclError:
                pass
        self._player.stop()
        if self._player.play(path, loop=False):
            self._preview_btn = btn
            btn.configure(text=i18n.t("stop"))
            self.after(6000, lambda: self._stop_preview(btn))

    def _stop_preview(self, btn):
        self._player.stop()
        try:
            btn.configure(text=i18n.t("preview"))
        except tk.TclError:
            pass

    def _set_default_ring(self, path):
        self._player.stop()
        self.app.store.update_settings(default_ringtone=path)
        self._refresh_ringtones()
        self._toast(i18n.t("market_saved_file"))

    # ---------- 吉祥物 ----------
    def _build_mascot(self, f):
        card = tk.Frame(f, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=16, pady=16)
        self.mascot_cnv = tk.Canvas(card, width=200, height=220, bg=CHIP_BG,
                                    highlightthickness=0)
        self.mascot_cnv.pack(side="left", padx=24, pady=24)
        info = tk.Frame(card, bg=CARD)
        info.pack(side="left", fill="both", expand=True, padx=10, pady=24)
        tk.Label(info, text=i18n.t("tab_mascot"), bg=CARD, fg=TEXT,
                 font=F(14, True), anchor="w").pack(fill="x")
        tk.Label(info, text=i18n.t("market_mascot_hint"), bg=CARD, fg=TEXT_SUB,
                 font=F(10), wraplength=460, justify="left", anchor="w"
                 ).pack(fill="x", pady=10)
        btns = tk.Frame(info, bg=CARD)
        btns.pack(anchor="w")
        ttk.Button(btns, text=i18n.t("market_mascot_pick"),
                   command=self._pick_mascot).pack(side="left", padx=(0, 10))
        ttk.Button(btns, text=i18n.t("market_mascot_reset"),
                   command=self._reset_mascot).pack(side="left")
        ttk.Button(btns, text=i18n.t("market_open_wallpapers"),
                   command=lambda: os.startfile(WALLPAPER_DIR)).pack(side="left", padx=10)

    def _refresh_mascot(self):
        self.mascot_cnv.delete("all")
        try:
            photo, w, h = mascot_photo(150)
            self.mascot_cnv.create_image(100, 110, image=photo)
            self.mascot_cnv._photo = photo
        except Exception:
            pass

    def _pick_mascot(self):
        p = filedialog.askopenfilename(
            title=i18n.t("market_mascot_pick"),
            filetypes=[(i18n.t("image_files"), "*.png *.jpg *.jpeg *.gif *.bmp"),
                       (i18n.t("all_files"), "*.*")])
        if p:
            self._apply_mascot(p, toast=True, copy=True)

    def _reset_mascot(self):
        self.app.store.update_settings(mascot_file="")
        set_mascot("")
        self._refresh_mascot()
        self.app.after_change()
        self._toast(i18n.t("market_mascot_reset"))

    def _apply_mascot(self, path, toast=False, copy=False):
        import shutil
        dest = path
        if copy:
            os.makedirs(MASCOT_DIR, exist_ok=True)
            dest = os.path.join(MASCOT_DIR, os.path.basename(path))
            base, ext = os.path.splitext(dest)
            i = 1
            while os.path.exists(dest):
                dest = "%s_%d%s" % (base, i, ext)
                i += 1
            shutil.copyfile(path, dest)
        self.app.store.update_settings(mascot_file=dest)
        set_mascot(dest)
        self._refresh_mascot()
        self.app.after_change()
        if toast:
            self._toast(i18n.t("market_saved_mascot"))

    # ---------- 链接下载 ----------
    def _build_download(self, f):
        card = tk.Frame(f, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=16, pady=20)
        body = tk.Frame(card, bg=CARD)
        body.pack(fill="x", padx=22, pady=26)
        tk.Label(body, text=i18n.t("tab_download"), bg=CARD, fg=TEXT,
                 font=F(14, True), anchor="w").pack(fill="x")
        self.url_var = tk.StringVar()
        tk.Entry(body, textvariable=self.url_var, font=F(11),
                 relief="solid", bd=1).pack(fill="x", pady=12, ipady=5)
        tk.Label(body, text=i18n.t("market_url_hint"), bg=CARD, fg=TEXT_SUB,
                 font=F(9), anchor="w").pack(fill="x")
        row = tk.Frame(body, bg=CARD)
        row.pack(fill="x", pady=14)
        self.dl_progress = tk.Label(row, text="", bg=CARD, fg=PRIMARY, font=F(10))
        self.dl_progress.pack(side="left")
        ttk.Button(row, text=i18n.t("market_url_go"),
                   command=self._start_url_download).pack(side="right")

    def _start_url_download(self):
        url = self.url_var.get().strip()
        if not url.lower().startswith(("http://", "https://")):
            self.dl_progress.configure(text=i18n.t("market_url_bad"))
            return
        self.dl_progress.configure(text=i18n.t("market_downloading", 0))

        def progress(done, total):
            pct = int(done * 100 / total) if total else 0
            self.dl_progress.configure(text=i18n.t("market_downloading", pct))

        def ok(path, kind):
            self.dl_progress.configure(text="")
            if kind == "audio":
                # 音频统一归入铃声库
                import shutil
                os.makedirs(AUDIO_DIR, exist_ok=True)
                dest = os.path.join(AUDIO_DIR, os.path.basename(path))
                if os.path.abspath(os.path.dirname(path)) != os.path.abspath(AUDIO_DIR):
                    if os.path.exists(dest):
                        dest = net.unique_path(AUDIO_DIR, os.path.basename(path))
                    shutil.move(path, dest)
                    path = dest
                self._toast(i18n.t("market_saved_file"))
                self._switch("ringtone")
            elif kind == "image":
                self.app.store.update_settings(default_image=path)
                self._toast(i18n.t("market_saved_bg"))
            else:
                self._toast(i18n.t("market_saved_file"))

        def err(e):
            self.dl_progress.configure(text=i18n.t("market_url_bad"))

        # 图片先存壁纸目录，音频存铃声目录；具体类型由响应头/扩展名判定
        net.download(self.app.root, url, WALLPAPER_DIR,
                     on_progress=progress, on_ok=ok, on_err=err)

    # ---------- 轻提示 ----------
    def _toast(self, text):
        top = tk.Toplevel(self.app.root)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.configure(bg=PRIMARY)
        lbl = tk.Label(top, text=text, bg=PRIMARY, fg="#FFFFFF", font=F(11, True),
                       padx=22, pady=12)
        lbl.pack()
        self.app.root.update_idletasks()
        x = self.app.root.winfo_rootx() + self.app.root.winfo_width() // 2 - 160
        y = self.app.root.winfo_rooty() + 90
        top.geometry("+%d+%d" % (x, y))
        top.after(1800, top.destroy)
