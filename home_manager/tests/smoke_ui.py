# -*- coding: utf-8 -*-
"""居家管家 - 界面冒烟测试：逐页截图 + 全屏闹钟弹窗截图（不发声）"""
import datetime
import os
import shutil
import sys

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import ui_alarm  # noqa: E402
from config import DATA_FILE  # noqa: E402


class QuietPlayer(ui_alarm.SoundPlayer):
    def play(self, *a, **k):
        return True


ui_alarm.SoundPlayer = QuietPlayer  # 测试不发声

OUT = os.path.join(HERE, "shots")
os.makedirs(OUT, exist_ok=True)


def do_grab(app, name, lift_root=True):
    import time
    from PIL import ImageGrab
    if lift_root:
        app.root.deiconify()
        app.root.attributes("-topmost", True)
        app.root.lift()
        app.root.focus_force()
    app.root.update_idletasks()
    time.sleep(0.5)
    p = os.path.join(OUT, name)
    ImageGrab.grab().save(p)
    print("截图:", p, flush=True)
    if lift_root:
        app.root.attributes("-topmost", False)


def main():
    # 备份真实数据，测试结束恢复
    bak = DATA_FILE + ".smokebak"
    if os.path.exists(DATA_FILE):
        shutil.copy2(DATA_FILE, bak)

    from ui_main import App
    app = App()
    added = []

    def grab(name, lift_root=True):
        do_grab(app, name, lift_root)

    try:
        def step1():
            grab("1_alarms.png")
            app.show_page("tasks")
            app.root.after(1300, step2)

        def step2():
            grab("2_tasks.png")
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
            app.show_page("calendar")
            app.root.after(1300, step3)

        def step3():
            grab("3_calendar.png")
            app.show_page("settings")
            app.root.after(1300, step4)

        def step4():
            grab("4_settings.png")
            app.test_alarm()
            app.root.after(1400, step5)

        def step5():
            grab("5_alarm_popup.png", lift_root=False)
            for w in list(app._popups):
                w._close()
            app.root.after(1300, finish)

        def finish():
            grab("6_after_close.png")
            if app._tray:
                app._tray.stop()
            app.scheduler.stop()
            app.wake.cancel()
            app.root.destroy()
            # os._exit 不会执行 finally，需先手动恢复真实数据
            if os.path.exists(bak):
                shutil.copy2(bak, DATA_FILE)
                os.remove(bak)
            sys.stdout.flush()
            os._exit(0)

        def chain():
            step1()

        app.root.after(900, chain)
        app.root.mainloop()
    finally:
        # 恢复真实数据
        if os.path.exists(bak):
            shutil.copy2(bak, DATA_FILE)
            os.remove(bak)
        else:
            for i in added:
                try:
                    app.store.delete_event(i)
                except Exception:
                    pass
    print("冒烟测试完成")


if __name__ == "__main__":
    main()
