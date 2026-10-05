# -*- coding: utf-8 -*-
"""单独截一张设置页最底部（关于卡片）"""
import os
import sys
import time

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from PIL import ImageGrab  # noqa: E402


def main():
    from ui_main import App
    app = App()

    def do():
        app.show_page("settings")

        def scroll_and_shoot():
            c = app.pages["settings"].scroll.canvas
            app.root.deiconify()
            app.root.attributes("-topmost", True)
            app.root.lift()
            time.sleep(0.6)
            for frac in (0.8, 0.9, 1.0, 1.0):
                c.yview_moveto(frac)
                app.root.update_idletasks()
                time.sleep(0.3)
            print("yview:", c.yview(), flush=True)
            time.sleep(0.4)
            ImageGrab.grab().save(os.path.join(HERE, "shots_i18n", "zh_9_about.png"))
            print("done", flush=True)
            app.root.attributes("-topmost", False)
            if app._tray:
                app._tray.stop()
            app.scheduler.stop()
            app.wake.cancel()
            app.root.destroy()
            os._exit(0)

        app.root.after(900, scroll_and_shoot)

    app.root.after(800, do)
    app.root.mainloop()


if __name__ == "__main__":
    main()
