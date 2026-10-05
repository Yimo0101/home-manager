# -*- coding: utf-8 -*-
"""居家管家 - 电脑唤醒

原理：调用 Windows 可等待定时器（WaitableTimer）并置 fResume=True，
在电脑处于「睡眠 / 休眠」状态时可到点唤醒电脑（需要系统电源选项允许
「允许唤醒定时器」）。电脑若为「完全关机」状态，任何软件都无法开机，
需在主板 BIOS 中设置 RTC 闹钟（见使用说明）。
"""
import ctypes
import datetime
import re
import subprocess
import threading

kernel32 = ctypes.windll.kernel32

# powercfg 别名（不同 Windows 版本的 RTCWAKE 完整 GUID 不同，统一用别名）
SUB_SLEEP = "SUB_SLEEP"
RTCWAKE = "RTCWAKE"


def _utc_filetime(dt_local):
    """本地 datetime -> UTC FILETIME（100ns，自1601-01-01）"""
    dt_utc = dt_local.astimezone(datetime.timezone.utc)
    epoch = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc)
    return int((dt_utc - epoch).total_seconds() * 10_000_000)


class WakeManager:
    def __init__(self):
        self._handle = None
        self._due = None
        self._lock = threading.Lock()
        self._wait_thread = None

    def cancel(self):
        with self._lock:
            if self._handle:
                kernel32.CancelWaitableTimer(self._handle)
                kernel32.CloseHandle(self._handle)
                self._handle = None
            self._due = None

    def schedule(self, dt_local):
        """设置到点唤醒（绝对本地时间）。同一分钟内重复设置会被忽略。"""
        if dt_local is None:
            return False
        with self._lock:
            if self._due and abs((dt_local - self._due).total_seconds()) < 30:
                return True
            self.cancel_locked()
            handle = kernel32.CreateWaitableTimerW(None, True, "HomeManager_WakeTimer")
            if not handle:
                return False
            ft = _utc_filetime(dt_local)
            due = ctypes.c_longlong(ft)
            # fResume=1：唤醒睡眠中的电脑
            ok = kernel32.SetWaitableTimer(
                handle, ctypes.byref(due), 0, None, None, True
            )
            if not ok:
                kernel32.CloseHandle(handle)
                return False
            self._handle = handle
            self._due = dt_local
            return True

    def cancel_locked(self):
        if self._handle:
            kernel32.CancelWaitableTimer(self._handle)
            kernel32.CloseHandle(self._handle)
            self._handle = None
        self._due = None

    @property
    def due(self):
        return self._due


def query_wake_timer_status():
    """查询「允许唤醒定时器」当前电源设置。返回 (ac:bool|None, dc:bool|None, raw:str)"""
    try:
        proc = subprocess.run(
            ["powercfg", "/query", "SCHEME_CURRENT", SUB_SLEEP, RTCWAKE],
            capture_output=True, timeout=10,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
        # 中文 Windows 的 powercfg 输出是 GBK，英文系统为 ASCII（GBK 兼容）
        out = proc.stdout.decode("gbk", errors="ignore")
    except Exception as e:
        return None, None, str(e)
    ac = dc = None
    for line in out.splitlines():
        m = re.search(r"0x([0-9a-fA-F]+)", line)
        if not m:
            continue
        val = int(m.group(1), 16)
        low = line.lower()
        if "ac power setting index" in low or "交流电源设置索引" in low:
            ac = val
        elif "dc power setting index" in low or "直流电源设置索引" in low:
            dc = val
    # 1=启用；2=仅重要唤醒定时器（也算开启，但建议设为 1）
    return (ac in (1, 2)), (dc in (1, 2)), out


def enable_wake_timers_elevated():
    """提权运行 powercfg，开启交流/直流下的唤醒定时器，会弹 UAC。返回是否成功发起。"""
    cmd = (
        '/c powercfg /setacvalueindex SCHEME_CURRENT %s %s 1 & '
        'powercfg /setdcvalueindex SCHEME_CURRENT %s %s 1 & '
        'powercfg /setactive SCHEME_CURRENT'
    ) % (SUB_SLEEP, RTCWAKE, SUB_SLEEP, RTCWAKE)
    try:
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", "cmd.exe", cmd, None, 0  # SW_HIDE
        )
        return rc > 32
    except Exception:
        return False
