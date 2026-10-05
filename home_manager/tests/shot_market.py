# -*- coding: utf-8 -*-
import os, sys
os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from PIL import ImageGrab
SHOTS = os.path.join(HERE, "shots_new")

def main():
    import i18n
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
        mp._switch("wallpaper")
        mp._load_wallpapers()
        app.root.after(18000, grab1)

    def grab1():
        ImageGrab.grab().save(os.path.join(SHOTS, "05_market_wallpaper.png"))
        print("shot wallpaper zh")
        mp._change_category("hug")
        app.root.after(12000, grab2)

    def grab2():
        ImageGrab.grab().save(os.path.join(SHOTS, "11_market_hug.png"))
        print("shot hug gif")
        app.store.update_settings(language="zh")
        app.root.destroy()

    app.root.after(600, show)
    app.root.mainloop()
    print("DONE")

main()
