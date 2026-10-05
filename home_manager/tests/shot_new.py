# -*- coding: utf-8 -*-
"""新功能界面回归：纪念日、番茄钟、集市（铃声/壁纸）、早安简报、设置新卡片、三语"""
import datetime
import os
import sys

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from PIL import ImageGrab  # noqa: E402

SHOTS = os.path.join(HERE, "shots_new")
os.makedirs(SHOTS, exist_ok=True)


def grab(name):
    ImageGrab.grab().save(os.path.join(SHOTS, name))
    print("shot", name)


def main():
    import i18n
    from ui_main import App
    app = App()

    # 准备两个纪念日：农历重阳 + 公历倒数
    store = app.store
    store.data["anniversaries"] = [
        {"id": "ann1", "title": "重阳节（农历）", "date": "2026-09-09",
         "calendar": "lunar", "yearly": True},
        {"id": "ann2", "title": "期末考试", "date": "2026-12-20",
         "calendar": "solar", "yearly": False},
    ]
    store.save()

    def raise_root():
        app.root.deiconify()
        app.root.attributes("-topmost", True)
        app.root.lift()
        app.root.geometry("1080x700+80+40")
        app.root.after(400, next)

    def s_alarms():
        app.show_page("alarms")
        app.root.after(350, lambda: grab("01_alarms_word.png"))
        app.root.after(500, next)

    def s_calendar():
        p = app.pages["calendar"]
        p.year, p.month = 2026, 10
        p.selected = datetime.date(2026, 10, 5)
        app.show_page("calendar")
        app.root.after(400, lambda: grab("02_calendar_ann.png"))
        app.root.after(550, next)

    def s_focus():
        app.show_page("focus")
        app.root.after(400, lambda: grab("03_focus.png"))
        app.root.after(550, next)

    def s_market_ring():
        app.show_page("market")
        mp = app.pages["market"]
        mp._switch("ringtone")
        app.root.after(600, lambda: grab("04_market_ring.png"))
        app.root.after(800, next)

    def s_market_wp():
        mp = app.pages["market"]
        mp._switch("wallpaper")
        mp._load_wallpapers()
        app.root.after(9000, lambda: grab("05_market_wallpaper.png"))
        app.root.after(9200, next)

    def s_market_dl():
        mp = app.pages["market"]
        mp._switch("download")
        app.root.after(300, lambda: grab("06_market_download.png"))
        app.root.after(450, next)

    def s_settings():
        app.show_page("settings")
        app.root.after(500, lambda: grab("07_settings.png"))
        app.root.after(650, next)

    def s_morning():
        from ui_morning import MorningWindow
        w = MorningWindow(app.root, app)
        app.root.after(500, lambda: grab("08_morning.png"))
        app.root.after(700, w.destroy)
        app.root.after(900, next)

    def s_ja():
        app.change_language("ja")
        app.show_page("focus")
        app.root.after(500, lambda: grab("09_focus_ja.png"))
        app.root.after(650, next)

    def s_en():
        app.change_language("en")
        app.show_page("calendar")
        app.root.after(500, lambda: grab("10_calendar_en.png"))
        app.root.after(650, next)

    def finish():
        # 还原数据，避免测试纪念日污染用户文件
        store.data["anniversaries"] = []
        store.save()
        app.root.destroy()

    steps = [raise_root, s_alarms, s_calendar, s_focus, s_market_ring,
             s_market_wp, s_market_dl, s_settings, s_morning, s_ja, s_en,
             finish]
    idx = {"i": 0}

    def next():
        if idx["i"] >= len(steps):
            return
        fn = steps[idx["i"]]
        idx["i"] += 1
        fn()

    app.root.after(300, next)
    app.root.mainloop()
    print("SHOTS DONE")


if __name__ == "__main__":
    main()
