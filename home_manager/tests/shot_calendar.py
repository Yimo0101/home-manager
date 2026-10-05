# -*- coding: utf-8 -*-
"""验证：日历农历/节气/节日显示、三语、开关就地刷新不重建"""
import datetime
import os
import sys

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from PIL import ImageGrab  # noqa: E402

SHOTS = os.path.join(HERE, "shots_cal")
os.makedirs(SHOTS, exist_ok=True)


def grab(name):
    ImageGrab.grab().save(os.path.join(SHOTS, name))


def find_switches(widget, out):
    if hasattr(widget, "on_toggle"):
        out.append(widget)
    for ch in widget.winfo_children():
        find_switches(ch, out)


def main():
    import i18n
    from ui_main import App
    app = App()
    page = app.pages["calendar"]
    steps = []

    def cal_page():
        return app.pages["calendar"]

    def s_cal_oct_guoqing():
        app.root.deiconify()
        app.root.attributes("-topmost", True)
        app.root.lift()
        app.show_page("calendar")
        p = cal_page()
        p.year, p.month = 2026, 10
        p.select_day(datetime.date(2026, 10, 1))
        app.root.after(450, lambda: grab("cal_10_guoqing.png"))
        app.root.after(600, next)

    def s_cal_oct_hanlu():
        p = cal_page()
        p.select_day(datetime.date(2026, 10, 8))
        app.root.after(350, lambda: grab("cal_10_hanlu.png"))
        app.root.after(500, next)

    def s_cal_feb():
        p = cal_page()
        p.year, p.month = 2026, 2
        p.selected = datetime.date(2026, 2, 17)
        p.refresh()
        app.root.after(350, lambda: grab("cal_02_chunjie.png"))
        app.root.after(500, next)

    def s_toggle():
        app.show_page("alarms")

        def work():
            grab("alarms_before.png")
            ap = app.pages["alarms"]
            sws = []
            find_switches(ap.box, sws)
            assert sws, "未找到开关"
            alarm_id = list(ap.rows.keys())[0]
            lbl_before = ap.rows[alarm_id]["time"]
            before_id = str(lbl_before)
            before_fg = lbl_before.cget("fg")
            sws[0]._click()  # 模拟点击开关

            def after_anim():
                lbl_after = ap.rows[alarm_id]["time"]
                assert str(lbl_after) == before_id, "开关导致整行重建！"
                assert lbl_after.cget("fg") != before_fg, "时间颜色未变化"
                grab("alarms_after_toggle.png")
                print("TOGGLE_INPLACE_OK fg:", before_fg, "->", lbl_after.cget("fg"))
                # 还原状态
                sws[0]._click()
                app.root.after(300, next)
            app.root.after(350, after_anim)
        app.root.after(500, work)

    def s_ja():
        app.change_language("ja")
        app.show_page("calendar")
        p = cal_page()
        p.year, p.month = 2026, 10
        p.select_day(datetime.date(2026, 10, 8))
        app.root.after(450, lambda: grab("cal_ja.png"))
        app.root.after(600, next)

    def s_en():
        app.change_language("en")
        app.show_page("calendar")
        p = cal_page()
        p.year, p.month = 2026, 10
        p.select_day(datetime.date(2026, 10, 8))
        app.root.after(450, lambda: grab("cal_en.png"))
        app.root.after(600, next)

    def s_restore():
        app.change_language("zh")
        app.root.after(400, next)

    steps = [s_cal_oct_guoqing, s_cal_oct_hanlu, s_cal_feb, s_toggle,
             s_ja, s_en, s_restore]

    def next():
        if steps:
            steps.pop(0)()
        else:
            app.root.attributes("-topmost", False)
            if app._tray:
                app._tray.stop()
            app.scheduler.stop()
            app.wake.cancel()
            app.root.destroy()
            os._exit(0)

    app.root.after(900, next)
    app.root.mainloop()


if __name__ == "__main__":
    main()
