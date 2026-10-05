# -*- coding: utf-8 -*-
import os
import sys
import time

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import tkinter as tk
import net

# 让回调异常不再被吞掉
_orig_ui = net._ui
def loud_ui(root, fn, *args):
    def call():
        try:
            fn(*args)
        except Exception as e:
            import traceback
            print("CALLBACK ERROR:", e)
            traceback.print_exc()
    if root is not None:
        root.after(0, call)
    else:
        call()
net._ui = loud_ui

root = tk.Tk()
root.withdraw()

items1 = []
net.fetch_wallpapers(root, "waifu", 9, lambda it: items1.extend(it),
                     lambda e: print("list err", e), force=True)


def step1():
    print("list1 items:", len(items1))
    filled = [0]
    labels = []
    for it in items1:
        lab = tk.Label(root, text="…")
        lab.pack()
        labels.append(lab)

        def mk(l):
            def show(data):
                from PIL import Image, ImageTk
                import io
                img = Image.open(io.BytesIO(data))
                ph = ImageTk.PhotoImage(img)
                l.configure(image=ph, text="")
                l.image = ph
                filled[0] += 1
            return show
        net.fetch_thumb(root, it["thumb"], mk(lab), lambda e: print("thumb err", e),
                        resize=it.get("resize", False),
                        remember=it.get("remember", False))

    def step2():
        print("after cold fill, filled =", filled[0])
        # 模拟切回缓存：全部重建
        filled2 = [0]
        labels2 = []
        for it in items1:
            lab = tk.Label(root, text="…")
            lab.pack()
            labels2.append(lab)

            def mk(l):
                def show(data):
                    from PIL import Image, ImageTk
                    import io
                    img = Image.open(io.BytesIO(data))
                    ph = ImageTk.PhotoImage(img)
                    l.configure(image=ph, text="")
                    l.image = ph
                    filled2[0] += 1
                return show
            net.fetch_thumb(root, it["thumb"], mk(lab),
                            lambda e: print("thumb err2", e),
                            resize=it.get("resize", False),
                            remember=it.get("remember", False))

        def report():
            print("after cached fill, filled2 =", filled2[0])
            root.destroy()
        root.after(800, report)

    root.after(8000, step2)


root.after(3000, step1)
root.mainloop()
print("DONE")
