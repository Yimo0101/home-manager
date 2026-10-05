# -*- coding: utf-8 -*-
import os, sys, traceback
os.environ["HM_NO_MUTEX"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repro_lang.log")
logf = open(LOG, "w", encoding="utf-8")

def log(*a):
    logf.write(" ".join(str(x) for x in a) + "\n")
    logf.flush()

def main():
    from ui_main import App
    app = App()
    def cb_exc(exc, val, tb):
        log("CALLBACK_EXCEPTION:", "".join(traceback.format_exception(exc, val, tb)))
    app.root.report_callback_exception = cb_exc
    app.root.deiconify()
    def watchdog():
        log("WATCHDOG TIMEOUT - destroying")
        app.root.destroy()
    app.root.after(12000, watchdog)
    app.root.after(800, lambda: app.show_page("focus"))
    def goja():
        log("-> ja")
        app.change_language("ja")
        log("JA_OK")
        app.root.after(400, lambda: app.show_page("market"))
        def gomenu():
            log("-> ringtone tab")
            app.pages["market"]._switch("ringtone")
            log("RING_OK")
            app.root.after(300, goen)
        app.root.after(400, gomenu)
    def goen():
        log("-> en")
        app.change_language("en")
        log("EN_OK")
        app.root.after(400, finish)
    def finish():
        log("DONE")
        app.root.destroy()
    app.root.after(1200, goja)
    app.root.mainloop()
    log("MAINLOOP EXIT")
    logf.close()

main()
