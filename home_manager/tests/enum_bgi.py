# -*- coding: utf-8 -*-
import ctypes
import ctypes.wintypes
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..")
u = ctypes.windll.user32
PID = 27816

@ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
def cb(hwnd, lp):
    pid = ctypes.wintypes.DWORD()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == PID:
        n = u.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(hwnd, buf, n + 1)
        rc = ctypes.wintypes.RECT()
        u.GetWindowRect(hwnd, ctypes.byref(rc))
        print("hwnd=%s visible=%s title=%r rect=(%d,%d,%d,%d)" % (
            hwnd, bool(u.IsWindowVisible(hwnd)), buf.value,
            rc.left, rc.top, rc.right, rc.bottom))
    return True

u.EnumWindows(cb, 0)
