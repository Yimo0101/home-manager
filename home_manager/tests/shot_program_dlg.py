# -*- coding: utf-8 -*-
"""截图：定时打开程序对话框 + BetterGI 一条龙模板（三语）"""
import os
import sys

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from PIL import ImageGrab  # noqa: E402

SHOTS = os.path.join(HERE, "shots_new")
os.makedirs(SHOTS, exist_ok=True)


def grab(widget, name):
    widget.update_idletasks()
    x, y = widget.winfo_rootx(), widget.winfo_rooty()
    ImageGrab.grab(bbox=(x, y, x + widget.winfo_width(),
                         y + widget.winfo_height())).save(
        os.path.join(SHOTS, name))
    print("shot", name)


def main():
    import i18n
    from ui_main import App
    from ui_dialogs import ProgramTaskDialog
    app = App()
    app.root.geometry("1100x760+60+20")

    def step_zh():
        i18n.set_lang("zh")
        dlg = ProgramTaskDialog(app.root)
        dlg._apply_bettergi()

        def shot():
            grab(dlg, "16_program_bettergi_zh.png")
            dlg.destroy()
            app.root.after(200, step_ja)
        dlg.after(350, shot)

    def step_ja():
        i18n.set_lang("ja")
        dlg = ProgramTaskDialog(app.root)
        dlg._apply_bettergi()

        def shot():
            grab(dlg, "17_program_bettergi_ja.png")
            dlg.destroy()
            app.root.after(200, step_en)
        dlg.after(350, shot)

    def step_en():
        i18n.set_lang("en")
        dlg = ProgramTaskDialog(app.root)
        dlg._apply_bettergi()

        def shot():
            grab(dlg, "18_program_bettergi_en.png")
            dlg.destroy()
            app.root.after(200, lambda: os._exit(0))
        dlg.after(350, shot)

    app.root.after(500, step_zh)
    app.root.mainloop()


if __name__ == "__main__":
    main()
