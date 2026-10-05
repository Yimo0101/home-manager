# -*- coding: utf-8 -*-
"""Windows 交互缩放/移动平滑化

Tk 在拖动窗口边框时，每收到一个 WM_SIZE 都会同步重排全部控件；
控件一多（设置页/日历页）就会一卡一卡、内容撕裂。

做法（Win32 标准手法）：
- WM_ENTERSIZEMOVE：进入拖拽/缩放模态循环时，LockWindowUpdate 锁定窗口绘制
  并发送 WM_SETREDRAW=FALSE。期间 Tk 照常更新内部几何，但画面保持上一帧，
  由桌面窗口管理器（DWM）对位图做平滑拉伸，绝不撕裂、不逐帧重排闪烁。
- WM_EXITSIZEMOVE：松手时解锁、恢复重绘并强制整窗一次性刷新，控件一次成型。
"""
import sys


def install(root):
    """在主窗口上安装平滑缩放钩子（仅 Windows；其他系统为空操作）"""
    if sys.platform != "win32":
        return False

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    WM_SETREDRAW = 0x000B
    WM_ENTERSIZEMOVE = 0x0231
    WM_EXITSIZEMOVE = 0x0232
    RDW_INVALIDATE = 0x0001
    RDW_ERASE = 0x0004
    RDW_UPDATENOW = 0x0100
    RDW_ALLCHILDREN = 0x0080
    GWL_WNDPROC = -4

    WNDPROCTYPE = ctypes.WINFUNCTYPE(
        ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
        wintypes.LPARAM)

    try:
        set_window_long = user32.SetWindowLongPtrW
        get_window_long = user32.GetWindowLongPtrW
    except AttributeError:
        set_window_long = user32.SetWindowLongW
        get_window_long = user32.GetWindowLongW
    set_window_long.restype = ctypes.c_void_p
    get_window_long.restype = ctypes.c_void_p
    set_window_long.argtypes = [wintypes.HWND, ctypes.c_int,
                                ctypes.c_void_p]
    get_window_long.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.CallWindowProcW.restype = ctypes.c_long
    user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND,
                                       wintypes.UINT, wintypes.WPARAM,
                                       wintypes.LPARAM]
    user32.LockWindowUpdate.argtypes = [wintypes.HWND]
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
                                    wintypes.WPARAM, wintypes.LPARAM]

    state = {"locked": False}

    def force_refresh(hwnd):
        user32.SendMessageW(hwnd, WM_SETREDRAW, 1, 0)
        user32.RedrawWindow(hwnd, None, None,
                            RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN
                            | RDW_UPDATENOW)

    def make_proc(old_ptr):
        def py_wndproc(hwnd, msg, wparam, lparam):
            if msg == WM_ENTERSIZEMOVE:
                state["locked"] = True
                user32.SendMessageW(hwnd, WM_SETREDRAW, 0, 0)
                user32.LockWindowUpdate(hwnd)
                return user32.CallWindowProcW(old_ptr, hwnd, msg, wparam,
                                              lparam)
            if msg == WM_EXITSIZEMOVE and state["locked"]:
                state["locked"] = False
                ret = user32.CallWindowProcW(old_ptr, hwnd, msg, wparam,
                                             lparam)
                # 松手后让 Tk 完成一次几何重排，再解锁整窗刷新
                try:
                    root.update_idletasks()
                except Exception:
                    pass
                user32.LockWindowUpdate(0)
                root.after_idle(lambda: force_refresh(hwnd))
                return ret
            return user32.CallWindowProcW(old_ptr, hwnd, msg, wparam, lparam)
        return WNDPROCTYPE(py_wndproc)

    def arm():
        try:
            hwnd = root.winfo_id()
        except Exception:
            return
        old = get_window_long(hwnd, GWL_WNDPROC)
        if not old:
            return
        cb = make_proc(old)
        set_window_long(hwnd, GWL_WNDPROC, ctypes.cast(cb, ctypes.c_void_p))
        # 保持回调与 HWND 引用，防止被 GC
        root._hm_resize_cb = cb
        root._hm_hwnd = hwnd

    root.after(300, arm)
    return True
