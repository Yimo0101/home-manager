# -*- coding: utf-8 -*-
"""验证页面切换动画：抓中间帧（滑入中）与完成帧"""
import os
import sys
import time

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from PIL import ImageGrab  # noqa: E402

SHOTS = os.path.join(HERE, "shots_i18n")


def grab(name):
    ImageGrab.grab().save(os.path.join(SHOTS, name))


def main():
    from ui_main import App
    app = App()

    seq = []

    def switch(key, mid_name, fin_name):
        def s():
            app.root.deiconify()
            app.root.attributes("-topmost", True)
            app.root.lift()
            app.root.update()
            app.show_page(key)          # 启动 150ms 滑入动画
            app.root.after(45, lambda: grab(mid_name))   # 动画中间
            app.root.after(400, lambda: grab(fin_name))  # 动画结束
            app.root.after(550, next)
        seq.append(s)

    switch("tasks", "trans_1_mid.png", "trans_1_end.png")
    switch("calendar", "trans_2_mid.png", "trans_2_end.png")
    switch("settings", "trans_3_mid.png", "trans_3_end.png")
    switch("alarms", "trans_4_mid.png", "trans_4_end.png")

    def next():
        if seq:
            seq.pop(0)()
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
