# -*- coding: utf-8 -*-
import os
import sys
import time

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from ui_main import App  # noqa: E402

app = App()
app.show_page("settings")
def step():
    c = app.pages["settings"].scroll.canvas
    print("scrollregion:", c.cget("scrollregion"))
    print("canvas h:", c.winfo_height(), "inner reqh:", app.pages["settings"].scroll.inner.winfo_reqheight())
    c.yview_moveto(1.0)
    app.root.update_idletasks()
    print("yview after moveto:", c.yview())
    os._exit(0)
app.root.after(1500, step)
app.root.mainloop()
