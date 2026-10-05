# -*- coding: utf-8 -*-
"""居家管家 - 在线更新（GitHub Releases，免登录公开接口）

- check_latest：查询最新版本号与下载地址（后台线程）
- apply_update：下载便携版 zip，生成 update.bat 替换文件并自动重启（仅打包版）
"""
import json
import os
import sys
import threading
import urllib.request
import webbrowser

from config import APP_DIR, APP_VERSION, GITHUB_REPO

API = "https://api.github.com/repos/%s/releases/latest"
UA = "HomeManager-Updater/1.0"


def _ver_tuple(s):
    parts = []
    for x in str(s).lstrip("vV").split("."):
        num = ""
        for ch in x:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num or 0))
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(latest, current=APP_VERSION):
    try:
        return _ver_tuple(latest) > _ver_tuple(current)
    except Exception:
        return False


def check_latest(root, on_ok, on_err):
    """on_ok(version, notes, page_url, zip_url)"""
    if not GITHUB_REPO:
        def none():
            on_ok("", "", "", "")
        if root is not None:
            root.after(0, none)
        else:
            none()
        return

    def work():
        try:
            req = urllib.request.Request(API % GITHUB_REPO,
                                         headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            version = str(data.get("tag_name", "")).lstrip("vV")
            notes = data.get("body", "") or ""
            page = data.get("html_url", "")
            zip_url = ""
            for a in data.get("assets", []):
                name = a.get("name", "").lower()
                if name.endswith(".zip"):
                    zip_url = a.get("browser_download_url", "")
                    break
            cb = lambda: on_ok(version, notes, page, zip_url)
            if root is not None:
                root.after(0, cb)
            else:
                cb()
        except Exception as e:
            cb = lambda: on_err(str(e))
            if root is not None:
                root.after(0, cb)
            else:
                cb()

    threading.Thread(target=work, daemon=True).start()


def open_page(url):
    if url:
        webbrowser.open(url)


def apply_update(root, zip_url, page_url, on_status, on_done):
    """打包版：下载 zip -> update.bat 静默替换重启；开发版：打开下载页。"""
    if not getattr(sys, "frozen", False):
        open_page(page_url)
        on_done("browser")
        return
    if not zip_url:
        open_page(page_url)
        on_done("browser")
        return

    import tempfile
    tmp_zip = os.path.join(tempfile.gettempdir(), "home_manager_update.zip")
    bat = os.path.join(APP_DIR, "update.bat")
    exe_path = sys.executable
    app_dir = APP_DIR

    def work():
        try:
            on_status("download")
            req = urllib.request.Request(zip_url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as resp, \
                    open(tmp_zip, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
            on_status("install")
            # 解压到临时目录
            extract = os.path.join(tempfile.gettempdir(), "hm_update_extract")
            import shutil
            shutil.rmtree(extract, ignore_errors=True)
            os.makedirs(extract, exist_ok=True)
            shutil.unpack_archive(tmp_zip, extract, "zip")
            # 找到压缩包内的程序根（含 exe 的那一层）
            src = extract
            for _ in range(3):
                exes = [n for n in os.listdir(src) if n.lower().endswith(".exe")]
                if exes:
                    break
                subs = [os.path.join(src, n) for n in os.listdir(src)
                        if os.path.isdir(os.path.join(src, n))]
                if len(subs) == 1:
                    src = subs[0]
                else:
                    break
            bat_text = (
                "@echo off\r\n"
                "ping 127.0.0.1 -n 4 > nul\r\n"
                "xcopy /e /y /i \"%s\\*\" \"%s\\\" > nul\r\n"
                "del /q \"%s\"\r\n"
                "start \"\" \"%s\"\r\n"
                "del \"%%~f0\"\r\n"
            ) % (src, app_dir, tmp_zip, exe_path)
            with open(bat, "w", encoding="gbk", errors="ignore") as f:
                f.write(bat_text)
            os.startfile(bat)
            on_done("restart")
        except Exception as e:
            on_done("error:" + str(e))

    threading.Thread(target=work, daemon=True).start()
