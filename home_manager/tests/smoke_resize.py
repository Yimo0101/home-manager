# -*- coding: utf-8 -*-
"""验证平滑缩放钩子安装、拖拽消息往返、松手后几何正确"""
import os
import sys

os.environ["HM_NO_MUTEX"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import ctypes  # noqa: E402


def main():
    from ui_main import App
    app = App()
    app.root.deiconify()
    app.root.update_idletasks()

    def work():
        assert hasattr(app.root, "_hm_resize_cb"), "钩子未安装"
        hwnd = app.root._hm_hwnd
        u32 = ctypes.windll.user32
        # 模拟进入缩放 -> 改尺寸 -> 退出缩放
        u32.SendMessageW(hwnd, 0x0231, 0, 0)
        app.root.geometry("1200x800")
        for _ in range(5):
            app.root.update()
        u32.SendMessageW(hwnd, 0x0232, 0, 0)
        for _ in range(8):
            app.root.update()
        w = app.root.winfo_width()
        print("HOOK_OK final width:", w)
        assert w >= 1100, "松手后窗口宽度未更新: %s" % w
        # 再改一次确认后续正常缩放仍然生效
        app.root.geometry("1000x700")
        app.root.update_idletasks()
        for _ in range(5):
            app.root.update()
        print("second width:", app.root.winfo_width())
        if app._tray:
            app._tray.stop()
        app.scheduler.stop()
        app.wake.cancel()
        app.root.destroy()
        os._exit(0)

    app.root.after(600, work)
    app.root.mainloop()


if __name__ == "__main__":
    main()
