# -*- coding: utf-8 -*-
"""居家管家 - 程序入口"""
import ctypes
import logging
import os
import sys
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import APP_NAME, LOG_FILE, MUTEX_NAME  # noqa: E402


def setup_logging():
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8",
    )


def single_instance():
    if os.environ.get("HM_NO_MUTEX") == "1":
        return True
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        return False
    return True


def main():
    setup_logging()
    log = logging.getLogger("home_manager")
    log.info("居家管家启动")
    if not single_instance():
        r = tk.Tk()
        r.withdraw()
        title, msg = APP_NAME, ""
        try:
            import i18n
            from storage import DataStore
            i18n.init_fonts(r)
            i18n.set_lang(DataStore().settings.get("language", "zh"))
            title, msg = i18n.t("brand"), i18n.t("already_running")
        except Exception:
            msg = "Home Manager is already running (check the tray icon)."
        messagebox.showinfo(title, msg)
        r.destroy()
        return

    import autostart
    from ui_main import App

    app = App()
    # 同步开机启动实际状态
    try:
        app.store.update_settings(autostart=autostart.is_enabled())
    except Exception:
        pass
    app.run()
    log.info("居家管家退出")


if __name__ == "__main__":
    main()
