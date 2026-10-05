# -*- coding: utf-8 -*-
"""居家管家 - 定时动作：打开程序 + 自动点击"""
import ctypes
import ctypes.wintypes
import os
import subprocess
import threading
import time

user32 = ctypes.windll.user32

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010


def get_cursor_pos():
    pt = ctypes.wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def click(x, y, double=False, right=False):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.15)
    if right:
        down, up = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
    else:
        down, up = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
    user32.mouse_event(down, 0, 0, 0, 0)
    time.sleep(0.06)
    user32.mouse_event(up, 0, 0, 0, 0)
    if double:
        time.sleep(0.12)
        user32.mouse_event(down, 0, 0, 0, 0)
        time.sleep(0.06)
        user32.mouse_event(up, 0, 0, 0, 0)


def _run_clicks_safely(steps):
    """steps: [{"delay": 秒, "x": int, "y": int, "double": bool}]"""
    for step in steps:
        try:
            delay = float(step.get("delay", 2))
        except (TypeError, ValueError):
            delay = 2
        time.sleep(max(0, delay))
        try:
            click(int(step["x"]), int(step["y"]), bool(step.get("double")))
        except Exception:
            continue


def launch_task(task):
    """打开程序并按配置执行点击。抛异常代表失败。"""
    exe = task.get("exe", "").strip().strip('"')
    if not exe or not os.path.exists(exe):
        raise FileNotFoundError("程序路径不存在：%s" % exe)
    args = task.get("args", "").strip()
    workdir = os.path.dirname(exe)
    if args:
        cmd = '"%s" %s' % (exe, args)
        proc = subprocess.Popen(cmd, cwd=workdir, close_fds=True)
    else:
        proc = subprocess.Popen([exe], cwd=workdir, close_fds=True)
    steps = task.get("clicks", [])
    if steps:
        t = threading.Thread(target=_run_clicks_safely, args=(steps,), daemon=True)
        t.start()
    return proc
