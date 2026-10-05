# -*- coding: utf-8 -*-
"""居家管家 - 开机自启动（注册表 HKCU Run 项，无需管理员）"""
import os
import sys
import winreg

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "HomeManager"


def _pythonw_path():
    """优先用 pythonw.exe（无控制台黑窗）"""
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        candidate = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.exists(candidate):
            return candidate
    return exe


def launch_command():
    here = os.path.dirname(os.path.abspath(__file__))
    main_pyw = os.path.join(here, "main.pyw")
    return '"%s" "%s"' % (_pythonw_path(), main_pyw)


def is_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            val, _ = winreg.QueryValueEx(key, VALUE_NAME)
            return bool(val)
    except OSError:
        return False


def enable():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, launch_command())


def disable():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, VALUE_NAME)
    except OSError:
        pass


def set_enabled(on):
    if on:
        enable()
    else:
        disable()
