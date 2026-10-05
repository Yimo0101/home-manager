# -*- coding: utf-8 -*-
"""居家管家 - 定时动作：打开程序 + 窗口识别 + 自动点击

支持两种点击坐标：
  1. 窗口相对坐标 rx/ry（0~1 的比例）：执行时按目标窗口实时位置换算，
     窗口移动、换分辨率都不会点偏（推荐）；
  2. 绝对屏幕坐标 x/y：找不到目标窗口时兜底使用。
"""
import ctypes
import ctypes.wintypes
import os
import subprocess
import threading
import time

user32 = ctypes.windll.user32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

SW_RESTORE = 9
INVALID_HANDLE = -1


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


# ---------- 窗口识别与激活 ----------

def _enum_windows():
    result = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND,
                       ctypes.wintypes.LPARAM)
    def cb(hwnd, _lparam):
        result.append(hwnd)
        return True

    user32.EnumWindows(cb, 0)
    return result


def _window_title(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value or ""


def find_window(title_sub):
    """按标题包含（不区分大小写）查找可见顶层窗口，返回 hwnd 或 None。

    多个候选标题用 "|" 分隔，任一命中即可，例如 "BetterGI|更好的原神"。
    """
    if not title_sub:
        return None
    needles = [s.strip().lower() for s in str(title_sub).split("|") if s.strip()]
    if not needles:
        return None
    for hwnd in _enum_windows():
        if not user32.IsWindowVisible(hwnd):
            continue
        title = _window_title(hwnd)
        if not title:
            continue
        low = title.lower()
        if any(n in low for n in needles):
            return hwnd
    return None


def wait_for_window(title_sub, timeout=30, interval=0.6):
    """轮询等待窗口出现，返回 hwnd；超时返回 None"""
    deadline = time.time() + max(1, int(timeout))
    while time.time() < deadline:
        hwnd = find_window(title_sub)
        if hwnd:
            return hwnd
        time.sleep(interval)
    return None


def window_rect(hwnd):
    rc = ctypes.wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rc)):
        return None
    return rc.left, rc.top, rc.right, rc.bottom


def focus_window(hwnd):
    """把窗口恢复（最小化时）并提到前台"""
    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
            time.sleep(0.3)
        # AttachThreadInput 技巧绕过 SetForegroundWindow 的前台锁定
        fg = user32.GetForegroundWindow()
        cur_tid = ctypes.windll.kernel32.GetCurrentThreadId()
        fg_tid = user32.GetWindowThreadProcessId(fg, None)
        tgt_tid = user32.GetWindowThreadProcessId(hwnd, None)
        if fg_tid != cur_tid:
            user32.AttachThreadInput(cur_tid, fg_tid, True)
        if tgt_tid != cur_tid and tgt_tid != fg_tid:
            user32.AttachThreadInput(cur_tid, tgt_tid, True)
        user32.ShowWindow(hwnd, 5)  # SW_SHOW
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
        if fg_tid != cur_tid:
            user32.AttachThreadInput(cur_tid, fg_tid, False)
        if tgt_tid != cur_tid and tgt_tid != fg_tid:
            user32.AttachThreadInput(cur_tid, tgt_tid, False)
        time.sleep(0.4)
        return True
    except Exception:
        return False


def resolve_point(step, hwnd):
    """把一步点击换算成屏幕绝对坐标。优先窗口相对比例，失败回退绝对坐标。"""
    rx = step.get("rx")
    ry = step.get("ry")
    if hwnd is not None and rx is not None and ry is not None:
        rc = window_rect(hwnd)
        if rc:
            l, t, r, b = rc
            return int(l + float(rx) * (r - l)), int(t + float(ry) * (b - t))
    return int(step.get("x", 0)), int(step.get("y", 0))


def _run_steps(task):
    title = (task.get("window_title") or "").strip()
    wait_s = task.get("wait_window", 30)
    steps = task.get("clicks", [])

    hwnd = None
    if title:
        hwnd = wait_for_window(title, wait_s)
        if hwnd:
            focus_window(hwnd)

    for step in steps:
        try:
            delay = float(step.get("delay", 2))
        except (TypeError, ValueError):
            delay = 2
        time.sleep(max(0, delay))
        try:
            if title:
                cur = find_window(title)
                if cur:
                    if cur != hwnd:
                        hwnd = cur
                    focus_window(hwnd)
            x, y = resolve_point(step, hwnd)
            click(x, y, bool(step.get("double")))
        except Exception:
            continue


def find_bettergi():
    """自动探测 BetterGI.exe 常见安装位置，找不到返回空字符串"""
    candidates = [
        r"C:\Program Files\BetterGI\BetterGI.exe",
        r"C:\Program Files (x86)\BetterGI\BetterGI.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     "Programs", "BetterGI", "BetterGI.exe"),
    ]
    home = os.environ.get("USERPROFILE", "")
    search_roots = [os.path.join(home, "Desktop"),
                    os.path.join(home, "Downloads")]
    for root in search_roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            depth = os.path.relpath(dirpath, root).count(os.sep)
            if depth >= 2:
                dirnames[:] = []
                continue
            for fn in filenames:
                low = fn.lower()
                if low.endswith(".exe") and "bettergi" in low \
                        and "update" not in low:
                    candidates.append(os.path.join(dirpath, fn))
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return ""


def launch_task(task):
    """打开程序并按配置执行点击。抛异常代表启动失败。

    若配置了窗口标题且该窗口已经存在（程序已在运行），则不重复启动，
    直接激活窗口并执行点击——任务重复触发也安全。
    """
    exe = task.get("exe", "").strip().strip('"')
    title = (task.get("window_title") or "").strip()
    proc = None

    already = find_window(title) if title else None
    if already:
        focus_window(already)
    else:
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
        t = threading.Thread(target=_run_steps, args=(task,), daemon=True)
        t.start()
    return proc
