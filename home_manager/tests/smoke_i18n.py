# -*- coding: utf-8 -*-
"""居家管家 - 三语界面冒烟测试：zh / ja / en 逐页截图 + 全屏弹窗截图（不发声）"""
import datetime
import os
import shutil
import sys
import time

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import ui_alarm  # noqa: E402
from config import DATA_FILE  # noqa: E402


class QuietPlayer(ui_alarm.SoundPlayer):
    def play(self, *a, **k):
        return True


ui_alarm.SoundPlayer = QuietPlayer

OUT = os.path.join(HERE, "shots_i18n")
os.makedirs(OUT, exist_ok=True)
LANGS = ["zh", "ja", "en"]
PAGES = ["alarms", "tasks", "calendar", "settings"]


def grab(app, name, lift_root=True):
    from PIL import ImageGrab
    if lift_root:
        app.root.deiconify()
        app.root.attributes("-topmost", True)
        app.root.lift()
        app.root.focus_force()
    app.root.update_idletasks()
    time.sleep(0.45)
    p = os.path.join(OUT, name)
    ImageGrab.grab().save(p)
    print("截图:", p, flush=True)
    if lift_root:
        app.root.attributes("-topmost", False)


def main():
    bak = DATA_FILE + ".smokebak"
    if os.path.exists(DATA_FILE):
        shutil.copy2(DATA_FILE, bak)

    from ui_main import App
    app = App()
    added = []

    try:
        today = datetime.date.today()
        demo = [
            {"title": "去社区医院复诊", "date": today.strftime("%Y-%m-%d"),
             "all_day": False, "time": "09:30", "end_time": "10:30",
             "remind_minutes": 30, "note": "带医保卡", "reminded": True},
            {"title": "交水电费", "date": today.strftime("%Y-%m-%d"),
             "all_day": True, "time": "", "end_time": "",
             "remind_minutes": -1, "note": "", "reminded": True},
            {"title": "和朋友打球",
             "date": (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
             "all_day": False, "time": "14:00", "end_time": "",
             "remind_minutes": 15, "note": "", "reminded": True},
        ]
        for e in demo:
            added.append(app.store.upsert_event(e)["id"])

        state = {"li": 0, "pi": 0}

        def next_step():
            li, pi = state["li"], state["pi"]
            if li >= len(LANGS):
                finish()
                return
            lang = LANGS[li]
            if pi == 0:
                app.change_language(lang)
            page = PAGES[pi]
            app.show_page(page)
            app.root.after(900, lambda: shoot_page(li, pi))

        def shoot_page(li, pi):
            lang, page = LANGS[li], PAGES[pi]
            grab(app, "%s_%d_%s.png" % (lang, pi + 1, page))
            if pi < len(PAGES) - 1:
                state["pi"] = pi + 1
                app.root.after(400, next_step)
            else:
                app.test_alarm()
                app.root.after(1200, lambda: shoot_popup(li))

        def shoot_popup(li):
            grab(app, "%s_5_popup.png" % LANGS[li], lift_root=False)
            for w in list(app._popups):
                w._close()
            state["li"] = li + 1
            state["pi"] = 0
            app.root.after(700, next_step)

        def finish():
            if app._tray:
                app._tray.stop()
            app.scheduler.stop()
            app.wake.cancel()
            app.root.destroy()
            if os.path.exists(bak):
                shutil.copy2(bak, DATA_FILE)
                os.remove(bak)
            sys.stdout.flush()
            os._exit(0)

        app.root.after(900, next_step)
        app.root.mainloop()
    finally:
        if os.path.exists(bak):
            shutil.copy2(bak, DATA_FILE)
            os.remove(bak)


if __name__ == "__main__":
    main()
