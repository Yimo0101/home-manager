# -*- coding: utf-8 -*-
"""居家管家 - 对话框截图测试（不保存数据、不发声）"""
import os
import sys
import time

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import ui_dialogs  # noqa: E402

OUT = os.path.join(HERE, "shots")
os.makedirs(OUT, exist_ok=True)


def grab(name, dlg):
    from PIL import ImageGrab
    dlg.attributes("-topmost", True)
    dlg.lift()
    dlg.focus_force()
    # 等待对话框真正映射可见（全屏游戏可能延迟新窗口绘制）
    mapped = False
    for _ in range(60):
        dlg.update()
        if dlg.body.winfo_ismapped():
            mapped = True
            break
        time.sleep(0.1)
    print("  body mapped:", mapped, flush=True)
    time.sleep(0.8)
    ImageGrab.grab().save(os.path.join(OUT, name))
    print("截图:", name, flush=True)
    dlg.attributes("-topmost", False)


def main():
    from ui_main import App
    app = App()

    def shot_alarm():
        dlg = ui_dialogs.AlarmDialog(app.root)
        grab("7_dialog_alarm.png", dlg)
        dlg.destroy()
        app.root.after(500, shot_program)

    def shot_program():
        dlg = ui_dialogs.ProgramTaskDialog(app.root)
        dlg.steps.append({"delay": 3, "x": 960, "y": 540, "double": False})
        dlg._refresh_tree()
        grab("8_dialog_program.png", dlg)
        dlg.destroy()
        app.root.after(500, shot_event)

    def shot_event():
        import datetime
        today = datetime.date.today().strftime("%Y-%m-%d")
        dlg = ui_dialogs.EventDialog(app.root, today)
        grab("9_dialog_event.png", dlg)
        dlg.destroy()
        app.root.after(500, finish)

    def finish():
        if app._tray:
            app._tray.stop()
        app.scheduler.stop()
        app.wake.cancel()
        app.root.destroy()
        os._exit(0)

    app.root.after(900, shot_alarm)
    app.root.mainloop()


if __name__ == "__main__":
    main()
