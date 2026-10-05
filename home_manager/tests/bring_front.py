# -*- coding: utf-8 -*-
import ctypes
import time

import ctypes.wintypes as wt

user32 = ctypes.windll.user32
found = []

EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
IsWindowVisible = user32.IsWindowVisible


def cb(hwnd, lparam):
    if IsWindowVisible(hwnd):
        n = GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        GetWindowTextW(hwnd, buf, n + 1)
        if buf.value and ("居家管家" in buf.value or "Home Manager" in buf.value):
            found.append((hwnd, buf.value))
    return True


EnumWindows(EnumWindowsProc(cb), 0)
print("windows:", found)
for hwnd, title in found:
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
time.sleep(1.5)
from PIL import ImageGrab  # noqa: E402
ImageGrab.grab().save(r"C:\Users\HP\Desktop\居家管家\home_manager\tests\shots_i18n\final_live.png")
print("captured")
