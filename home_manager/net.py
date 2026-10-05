# -*- coding: utf-8 -*-
"""居家管家 - 联网下载（纯标准库，后台线程 + Tk 主线程回调）

- fetch_json：取 JSON（集市图源列表）
- download：下载文件到指定目录，带进度回调
所有回调都通过 root.after 投递回主线程，UI 可直接刷新。
"""
import json
import os
import shutil
import threading
import urllib.parse
import urllib.request
import uuid

UA = "HomeManager/1.1 (Windows; desktop assistant)"

# 免费 SFW 图源：nekos.best（无需 key）。静态插画 + 治愈互动 GIF
NEKOS_CATEGORIES = ["waifu", "neko", "kitsune", "husbando",
                    "hug", "pat", "cuddle", "wave", "smile", "blush"]
NEKOS_API = "https://nekos.best/api/v2/%s?amount=%d"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".wma", ".ogg"}


def _ui(root, fn, *args):
    """把回调投递到 Tk 主线程（控件可能已销毁，静默忽略）"""
    def call():
        try:
            fn(*args)
        except Exception:
            pass
    if root is not None:
        try:
            root.after(0, call)
        except Exception:
            pass
    else:
        call()


def fetch_json(root, url, on_ok, on_err):
    def work():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            _ui(root, on_ok, data)
        except Exception as e:
            _ui(root, on_err, str(e))
    threading.Thread(target=work, daemon=True).start()


def fetch_bytes(root, url, on_ok, on_err):
    """下载原始字节（缩略图预览用）"""
    def work():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            _ui(root, on_ok, data)
        except Exception as e:
            _ui(root, on_err, str(e))
    threading.Thread(target=work, daemon=True).start()


def fetch_wallpapers(root, category, amount, on_ok, on_err):
    """返回 [{url, thumb, title}]；nekos.best 自带缩略图字段"""
    def work():
        try:
            req = urllib.request.Request(
                NEKOS_API % (category, max(1, min(20, amount))),
                headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            items = []
            for r in data.get("results", []):
                items.append({
                    "url": r.get("url", ""),
                    "thumb": r.get("url", ""),
                    "title": r.get("anime_name") or r.get("artist_name") or category,
                })
            _ui(root, on_ok, items)
        except Exception as e:
            _ui(root, on_err, str(e))
    threading.Thread(target=work, daemon=True).start()


def guess_kind(url, content_type=""):
    path = urllib.parse.urlparse(url).path.lower()
    ext = os.path.splitext(path)[1]
    ct = (content_type or "").lower()
    if ext in IMAGE_EXTS or "image" in ct:
        return "image", ext or ".jpg"
    if ext in AUDIO_EXTS or "audio" in ct:
        return "audio", ext or ".mp3"
    return "other", ext or ".bin"


def unique_path(folder, filename):
    base, ext = os.path.splitext(filename)
    p = os.path.join(folder, filename)
    if not os.path.exists(p):
        return p
    for i in range(1, 999):
        p = os.path.join(folder, "%s_%d%s" % (base, i, ext))
        if not os.path.exists(p):
            return p
    return os.path.join(folder, uuid.uuid4().hex[:8] + ext)


def download(root, url, folder, filename=None, kind_hint="",
             on_progress=None, on_ok=None, on_err=None):
    """下载文件；on_progress(已下载字节, 总字节或0)，on_ok(路径, kind)"""
    def work():
        try:
            os.makedirs(folder, exist_ok=True)
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                ctype = resp.headers.get("Content-Type", "")
                kind, ext = guess_kind(url, ctype)
                if kind_hint in ("image", "audio"):
                    kind = kind_hint
                    if kind_hint == "image" and ext not in IMAGE_EXTS:
                        ext = ".jpg"
                    if kind_hint == "audio" and ext not in AUDIO_EXTS:
                        ext = ".mp3"
                fname = filename
                if not fname:
                    name = os.path.basename(urllib.parse.urlparse(url).path)
                    if not name or os.path.splitext(name)[1] == "":
                        name = "hm_%s%s" % (uuid.uuid4().hex[:8], ext)
                    fname = urllib.parse.unquote(name)
                elif os.path.splitext(fname)[1] == "":
                    fname = fname + ext
                dest = unique_path(folder, os.path.basename(fname))
                total = int(resp.headers.get("Content-Length", 0) or 0)
                done = 0
                tmp = dest + ".part"
                with open(tmp, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        if on_progress:
                            _ui(root, on_progress, done, total)
                shutil.move(tmp, dest)
            if on_ok:
                _ui(root, on_ok, dest, kind)
        except Exception as e:
            if on_err:
                _ui(root, on_err, str(e))
    threading.Thread(target=work, daemon=True).start()
