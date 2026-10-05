# -*- coding: utf-8 -*-
"""居家管家 - 铃声播放（Windows MCI，支持 wav/mp3 循环）与背景图处理"""
import ctypes
import os
import threading
import time

from config import DEFAULT_IMAGE, DEFAULT_RINGTONE

_winmm = ctypes.windll.winmm
_kernel32 = ctypes.windll.kernel32

_mci_send = _winmm.mciSendStringW
_mci_send.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
_mci_send.restype = ctypes.c_long


def _mci(command):
    """执行 MCI 命令，返回错误码（0 为成功）"""
    return _mci_send(command, None, 0, None)


class SoundPlayer:
    """通过 MCI 播放铃声，自带循环；stop 彻底释放"""

    def __init__(self):
        self._alias = "hm_ring_%d" % id(self)
        self._opened = False
        self._want_loop = False
        self._thread = None
        self._stop_evt = threading.Event()

    def play(self, path, loop=True):
        self.stop()
        path = os.path.abspath(path)
        ext = os.path.splitext(path)[1].lower()
        # wav 用 waveaudio，mp3 等用 mpegvideo
        dev = "waveaudio" if ext == ".wav" else "mpegvideo"
        cmd = 'open "%s" type %s alias %s' % (path, dev, self._alias)
        if _mci(cmd) != 0:
            # 再试不指定设备类型
            if _mci('open "%s" alias %s' % (path, self._alias)) != 0:
                return False
        self._opened = True
        self._want_loop = loop
        self._stop_evt.clear()
        _mci("play %s from 0" % self._alias)
        if loop:
            self._thread = threading.Thread(target=self._loop_watch, daemon=True)
            self._thread.start()
        return True

    def _loop_watch(self):
        """MCI repeat 兼容性不一，自行轮询实现循环"""
        buf = ctypes.create_unicode_buffer(64)
        while not self._stop_evt.is_set():
            time.sleep(0.4)
            if not self._opened:
                break
            _winmm.mciSendStringW("status %s mode" % self._alias, buf, 64, None)
            if buf.value == "stopped":
                _mci("seek %s to start" % self._alias)
                _mci("play %s" % self._alias)

    def stop(self):
        self._stop_evt.set()
        self._want_loop = False
        if self._opened:
            _mci("stop %s" % self._alias)
            _mci("close %s" % self._alias)
            self._opened = False

    def __del__(self):
        try:
            self.stop()
        except Exception:
            pass


def resolve_ringtone(settings, item_path=""):
    """铃声路径优先级：任务自定义 -> 设置默认 -> 程序自带"""
    for p in (item_path, settings.get("default_ringtone", ""), DEFAULT_RINGTONE):
        if p and os.path.exists(p):
            return p
    return ""


def resolve_image(settings, item_path=""):
    for p in (item_path, settings.get("default_image", ""), DEFAULT_IMAGE):
        if p and os.path.exists(p):
            return p
    return ""


_cover_cache = {}
_cover_lock = threading.Lock()


def cover_image(path, w, h, dim=0.72):
    """生成覆盖全屏的背景（cover 裁剪 + 压暗，便于文字阅读），带缓存"""
    key = (path, w, h, dim)
    with _cover_lock:
        if key in _cover_cache:
            return _cover_cache[key]
    try:
        from PIL import Image, ImageEnhance
        img = Image.open(path).convert("RGB")
        iw, ih = img.size
        scale = max(w / iw, h / ih)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        img = img.resize((nw, nh), Image.LANCZOS)
        left, top = (nw - w) // 2, (nh - h) // 2
        img = img.crop((left, top, left + w, top + h))
        if dim < 1:
            img = ImageEnhance.Brightness(img).enhance(dim)
    except Exception:
        from PIL import Image
        img = Image.new("RGB", (w, h), (30, 41, 59))
    with _cover_lock:
        if len(_cover_cache) > 12:
            _cover_cache.clear()
        _cover_cache[key] = img
    return img
