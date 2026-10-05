# -*- coding: utf-8 -*-
import os
import sys
import time

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from PIL import ImageGrab  # noqa: E402
from ui_main import App  # noqa: E402

app = App()
app.show_page("settings")

def step():
    c = app.pages["settings"].scroll.canvas
    app.root.deiconify()
    app.root.attributes("-topmost", True)
    app.root.lift()
    time.sleep(0.8)
    c.yview_moveto(1.0)
    for _ in range(5):
        c.update()
        time.sleep(0.2)
    print("canvas h:", c.winfo_height(), "region:", c.cget("scrollregion"),
          "yview:", c.yview(), flush=True)
    # 嵌入窗口的实际坐标
    print("inner y:", app.pages["settings"].scroll.inner.winfo_y(), flush=True)
    ImageGrab.grab().save(os.path.join(HERE, "shots_i18n", "debug_scroll2.png"))
    os._exit(0)

app.root.after(1200, step)
app.root.mainloop()
