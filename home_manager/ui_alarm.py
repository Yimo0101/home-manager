# -*- coding: utf-8 -*-
"""居家管家 - 全屏闹钟 / 提醒弹窗（自定义背景图 + 铃声循环 + 贪睡，三语粉桃风）"""
import datetime
import os
import tkinter as tk

from PIL import Image, ImageDraw, ImageTk

import i18n
from media import SoundPlayer, cover_image
from ui_style import mascot_path, PRIMARY


def _wrap(draw, text, font, max_width):
    lines = []
    for raw in str(text).split("\n"):
        cur = ""
        for ch in raw:
            if draw.textlength(cur + ch, font=font) <= max_width:
                cur += ch
            else:
                lines.append(cur)
                cur = ch
        lines.append(cur)
    return lines


def _rounded_btn(draw, box, radius, fill):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=radius, fill=fill)


class AlarmWindow:
    """非阻塞式全屏弹窗，由主线程创建。"""

    def __init__(self, root, payload, on_snooze=None, on_close=None):
        self.root = root
        self.payload = payload
        self.on_snooze = on_snooze
        self.on_close = on_close
        self.player = SoundPlayer()
        self._closed = False
        self._snoozed = False

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.w = self.win.winfo_screenwidth()
        self.h = self.win.winfo_screenheight()
        self.win.geometry("%dx%d+0+0" % (self.w, self.h))
        self.win.configure(bg="#2A1620")

        bg = cover_image(payload.get("image"), self.w, self.h, dim=0.58).copy()
        # 取按钮位置的背景色，让按钮栏底色与背景图融合
        btn_y = int(self.h * 0.86) + 26
        pr, pg, pb = bg.getpixel((self.w // 2, min(self.h - 1, btn_y)))
        self.btn_bg = "#%02x%02x%02x" % (pr, pg, pb)
        photo = self._compose(bg, payload)
        self._photo = ImageTk.PhotoImage(photo)
        lbl = tk.Label(self.win, image=self._photo, bd=0, highlightthickness=0)
        lbl.place(x=0, y=0, width=self.w, height=self.h)

        is_alarm = payload.get("kind") == "alarm"
        btn_frame = tk.Frame(self.win, bg=self.btn_bg)
        btn_frame.place(relx=0.5, rely=0.86, anchor="center")
        snooze_text = i18n.t("snooze_btn", payload.get("snooze_minutes", 5))
        btn_snooze = tk.Button(btn_frame, text=snooze_text, font=i18n.F(14),
                               fg=PRIMARY, bg="#FFFFFF", activebackground="#FFE3EC",
                               bd=0, padx=34, pady=12, cursor="hand2",
                               command=self._snooze)
        btn_snooze.pack(side="left", padx=14)
        btn_stop = tk.Button(btn_frame,
                             text=i18n.t("stop_alarm") if is_alarm else i18n.t("got_it"),
                             font=i18n.F(14, True),
                             fg="#FFFFFF", bg=PRIMARY, activebackground="#DE5B8A",
                             activeforeground="#FFFFFF", bd=0, padx=46, pady=12,
                             cursor="hand2", command=self._stop)
        btn_stop.pack(side="left", padx=14)

        self.win.bind("<Return>", lambda e: self._stop())
        self.win.bind("<Escape>", lambda e: self._stop())
        self.win.bind("<space>", lambda e: self._snooze())
        self.win.focus_force()
        self.win.lift()

        ring = payload.get("ringtone")
        if ring and os.path.exists(ring):
            self.player.play(ring, loop=True)

    def _compose(self, img, payload):
        draw = ImageDraw.Draw(img)
        W, H = img.size
        center_x = W // 2
        white = (255, 255, 255, 255)

        now = datetime.datetime.now()
        top_text = (i18n.t("popup_alarm_top") if payload.get("kind") == "alarm"
                    else i18n.t("popup_reminder_top"))
        f_top = i18n.pil_font(30, False)
        tw = draw.textlength(top_text, font=f_top)
        draw.text((center_x - tw / 2, 90), top_text, font=f_top,
                  fill=(255, 255, 255, 215))

        f_clock = i18n.pil_font(132, True)
        clock = now.strftime("%H:%M")
        tw = draw.textlength(clock, font=f_clock)
        draw.text((center_x - tw / 2, H * 0.20), clock, font=f_clock, fill=white)

        f_date = i18n.pil_font(34, False)
        date_text = i18n.popup_date(now)
        tw = draw.textlength(date_text, font=f_date)
        draw.text((center_x - tw / 2, H * 0.20 + 165), date_text,
                  font=f_date, fill=(255, 255, 255, 225))

        f_title = i18n.pil_font(64, True)
        title = str(payload.get("title", i18n.t("tip")))
        lines = _wrap(draw, title, f_title, W * 0.8)
        y = H * 0.47
        for line in lines:
            tw = draw.textlength(line, font=f_title)
            draw.text((center_x - tw / 2, y), line, font=f_title, fill=white)
            y += 84

        line2 = payload.get("line2", "")
        if line2:
            f_body = i18n.pil_font(32, False)
            body_lines = _wrap(draw, line2, f_body, W * 0.7)
            y += 10
            for line in body_lines[:4]:
                tw = draw.textlength(line, font=f_body)
                draw.text((center_x - tw / 2, y), line, font=f_body,
                          fill=(255, 255, 255, 225))
                y += 48

        if payload.get("snoozed"):
            f_note = i18n.pil_font(26, False)
            note = i18n.t("snoozed_note")
            tw = draw.textlength(note, font=f_note)
            draw.text((center_x - tw / 2, H * 0.78), note, font=f_note,
                      fill=(255, 255, 255, 190))

        # 右下角吉祥物贴纸
        try:
            mascot = Image.open(mascot_path()).convert("RGBA")
            mh = int(H * 0.30)
            mw = int(mascot.width * mh / mascot.height)
            mascot = mascot.resize((mw, mh), Image.LANCZOS)
            img.paste(mascot, (W - mw - 30, H - mh - 20), mascot)
        except Exception:
            pass
        return img

    def _snooze(self):
        if self._closed:
            return
        self._snoozed = True
        if self.on_snooze:
            self.on_snooze(self.payload)
        self._close()

    def _stop(self):
        self._close()

    def _close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self.player.stop()
        except Exception:
            pass
        try:
            self.win.destroy()
        except Exception:
            pass
        if self.on_close:
            self.on_close(self)
