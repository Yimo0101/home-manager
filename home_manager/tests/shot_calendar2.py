# -*- coding: utf-8 -*-
"""验证：节日不重叠、数字深浅、选中就地动画（不重建格子）、倒计时、三语、缩放"""
import datetime
import os
import sys

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from PIL import ImageGrab  # noqa: E402

SHOTS = os.path.join(HERE, "shots_cal2")
os.makedirs(SHOTS, exist_ok=True)


def grab(name):
    ImageGrab.grab().save(os.path.join(SHOTS, name))


def main():
    import i18n
    from ui_main import App
    app = App()
    steps = []

    def page():
        return app.pages["calendar"]

    def show():
        app.root.deiconify()
        app.root.attributes("-topmost", True)
        app.root.lift()
        app.show_page("calendar")
        app.root.after(500, next)

    def s_oct():
        p = page()
        p.year, p.month = 2026, 10
        p.selected = datetime.date(2026, 10, 18)
        p.refresh()
        app.root.after(300, lambda: grab("oct_chongyang.png"))
        app.root.after(450, next)

    def s_nov():
        p = page()
        p.year, p.month = 2026, 11
        p.selected = datetime.date(2026, 11, 26)
        p.refresh()
        app.root.after(300, lambda: grab("nov_ganen.png"))
        app.root.after(450, next)

    def s_select_anim():
        """点 11/20：断言格子控件没有被重建，并抓动画中间帧"""
        p = page()
        p.year, p.month = 2026, 11
        p.selected = datetime.date(2026, 11, 18)
        p.refresh()
        app.root.update_idletasks()
        before = {d: str(info["frame"]) for d, info in p._cells.items()}
        p.select_day(datetime.date(2026, 11, 20))
        # 动画进行中（约 45ms）抓一帧
        app.root.after(45, lambda: grab("select_midframe.png"))

        def check():
            after = {d: str(info["frame"]) for d, info in p._cells.items()}
            assert before == after, "选中日期导致月历格子被重建！"
            print("SELECT_INPLACE_OK 42格控件全部未重建")
            # 颜色断言：新选中格为 SEL_BG，旧格回到 CARD
            new_bg = p._cells[datetime.date(2026, 11, 20)]["frame"].cget("bg")
            old_bg = p._cells[datetime.date(2026, 11, 18)]["frame"].cget("bg")
            print("new cell bg:", new_bg, " old cell bg:", old_bg)
            assert new_bg.lower() == "#ffeaf1"
            assert old_bg.lower() == "#ffffff"
            grab("select_done.png")
            next()
        app.root.after(400, check)

    def s_countdown():
        p = page()
        print("倒计时：", p.count_lbl.cget("text"), "| fg:", p.count_lbl.cget("fg"))
        assert p.count_lbl.cget("text"), "倒计时为空"
        next()

    def s_resize():
        """快速连续改尺寸，模拟拖动边框，确认无异常且渐变不重画卡顿"""
        for wh in ((980, 620), (1180, 760), (900, 560), (1080, 700)):
            app.root.geometry("%dx%d" % wh)
            app.root.update_idletasks()
        app.root.after(200, lambda: grab("after_resize.png"))
        app.root.after(350, next)

    def s_ja():
        app.change_language("ja")
        p = page()
        p.year, p.month = 2026, 11
        p.selected = datetime.date(2026, 11, 7)
        p.refresh()
        app.root.after(350, lambda: grab("nov_ja.png"))
        app.root.after(500, next)

    def s_en():
        app.change_language("en")
        p = page()
        p.year, p.month = 2026, 11
        p.selected = datetime.date(2026, 11, 26)
        p.refresh()
        app.root.after(350, lambda: grab("nov_en.png"))
        app.root.after(500, next)

    def s_restore():
        app.change_language("zh")
        app.root.after(400, next)

    steps = [show, s_oct, s_nov, s_select_anim, s_countdown, s_resize,
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

    app.root.after(800, next)
    app.root.mainloop()


if __name__ == "__main__":
    main()
