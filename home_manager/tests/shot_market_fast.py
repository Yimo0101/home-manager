# -*- coding: utf-8 -*-
import os
import sys
os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from PIL import ImageGrab
SHOTS = os.path.join(HERE, "shots_new")


def main():
    from ui_main import App
    app = App()
    app.change_language("zh")
    app.root.deiconify()
    app.root.attributes("-topmost", True)
    app.root.lift()
    app.root.geometry("1080x700+80+40")
    mp = app.pages["market"]

    def show():
        app.show_page("market")
        mp._switch("wallpaper")   # 首次进入自然触发一次冷加载
        app.root.after(6000, grab1)

    def grab1():
        ImageGrab.grab().save(os.path.join(SHOTS, "13_market_fast_waifu.png"))
        print("shot waifu cold")
        mp._change_category("neko")
        app.root.after(6000, grab2)

    def grab2():
        ImageGrab.grab().save(os.path.join(SHOTS, "14_market_fast_neko.png"))
        print("shot neko cold")
        # 切回 waifu：列表+缩略图全部走缓存，应瞬间铺满
        mp._change_category("waifu")
        app.root.after(1500, grab3)

    def grab3():
        ImageGrab.grab().save(os.path.join(SHOTS, "15_market_cached.png"))
        print("shot waifu cached")
        app.root.destroy()

    app.root.after(600, show)
    app.root.mainloop()
    print("DONE")


main()
