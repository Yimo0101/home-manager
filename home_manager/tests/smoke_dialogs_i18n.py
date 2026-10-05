# -*- coding: utf-8 -*-
"""居家管家 - 三语对话框 + 设置页底部截图（不保存数据、不发声）"""
import datetime
import os
import sys
import time

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import ui_dialogs  # noqa: E402

OUT = os.path.join(HERE, "shots_i18n")
os.makedirs(OUT, exist_ok=True)
LANGS = ["zh", "ja", "en"]


def grab(name, dlg=None):
    from PIL import ImageGrab
    if dlg is not None:
        dlg.attributes("-topmost", True)
        dlg.lift()
        dlg.focus_force()
        for _ in range(60):
            dlg.update()
            if dlg.body.winfo_ismapped():
                break
            time.sleep(0.1)
    time.sleep(0.7)
    p = os.path.join(OUT, name)
    ImageGrab.grab().save(p)
    print("截图:", p, flush=True)
    if dlg is not None:
        dlg.attributes("-topmost", False)


def main():
    from ui_main import App
    app = App()
    state = {"li": 0}

    def run_lang():
        li = state["li"]
        if li >= len(LANGS):
            finish()
            return
        lang = LANGS[li]
        app.change_language(lang)

        def shot_alarm():
            dlg = ui_dialogs.AlarmDialog(app.root)
            grab("%s_6_dlg_alarm.png" % lang, dlg)
            dlg.destroy()
            app.root.after(400, shot_program)

        def shot_program():
            dlg = ui_dialogs.ProgramTaskDialog(app.root)
            dlg.steps.append({"delay": 3, "x": 960, "y": 540, "double": False})
            dlg._refresh_tree()
            grab("%s_7_dlg_program.png" % lang, dlg)
            dlg.destroy()
            app.root.after(400, shot_event)

        def shot_event():
            today = datetime.date.today().strftime("%Y-%m-%d")
            dlg = ui_dialogs.EventDialog(app.root, today)
            grab("%s_8_dlg_event.png" % lang, dlg)
            dlg.destroy()
            app.root.after(400, shot_about)

        def shot_about():
            app.show_page("settings")
            page = app.pages["settings"]

            def do():
                page.scroll.canvas.yview_moveto(1.0)
                app.root.deiconify()
                app.root.attributes("-topmost", True)
                app.root.lift()
                app.root.update_idletasks()
                time.sleep(0.5)
                grab("%s_9_about.png" % lang)
                app.root.attributes("-topmost", False)
                state["li"] = li + 1
                app.root.after(400, run_lang)
            app.root.after(700, do)

        app.root.after(700, shot_alarm)

    def finish():
        if app._tray:
            app._tray.stop()
        app.scheduler.stop()
        app.wake.cancel()
        app.root.destroy()
        os._exit(0)

    app.root.after(900, run_lang)
    app.root.mainloop()


if __name__ == "__main__":
    main()
