# -*- coding: utf-8 -*-
"""居家管家 - 全局配置与路径（兼容 PyInstaller 打包：资源只读、用户数据可写）"""
import os
import sys

APP_NAME = "居家管家"
APP_VERSION = "1.1.2"

# GitHub 发布地址（仓库建好后填入 owner/repo，用于检查更新）
GITHUB_REPO = "Yimo0101/home-manager"   # GitHub 仓库，用于 Release 检查更新


def _frozen():
    return getattr(sys, "frozen", False)


# 程序所在目录（打包后是 exe 旁边；开发时是包目录）
if _frozen():
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
    BUNDLE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = APP_DIR

# 可写目录（数据 / 用户下载的资源都放 exe 旁边，解压到哪都能用）
DATA_DIR = os.path.join(APP_DIR, "data")
USER_ASSETS = os.path.join(APP_DIR, "assets")
# 只读的随包资源目录
BUNDLE_ASSETS = os.path.join(BUNDLE_DIR, "assets")

AUDIO_DIR = os.path.join(USER_ASSETS, "audio")
WALLPAPER_DIR = os.path.join(USER_ASSETS, "wallpapers")
MASCOT_DIR = os.path.join(USER_ASSETS, "mascots")

# 缩略图磁盘缓存（集市切分类时秒开，不重复下载原图）
CACHE_DIR = os.path.join(DATA_DIR, "cache")
THUMB_CACHE_DIR = os.path.join(CACHE_DIR, "thumbs")

DATA_FILE = os.path.join(DATA_DIR, "data.json")
LOG_FILE = os.path.join(DATA_DIR, "app.log")


def asset_path(rel):
    """资源文件：优先用户目录（可被市场下载覆盖），其次随包目录"""
    user_p = os.path.join(USER_ASSETS, rel)
    if os.path.exists(user_p):
        return user_p
    bundle_p = os.path.join(BUNDLE_ASSETS, rel)
    if os.path.exists(bundle_p):
        return bundle_p
    return user_p


def ensure_dirs():
    for d in (DATA_DIR, USER_ASSETS, AUDIO_DIR, WALLPAPER_DIR, MASCOT_DIR,
              CACHE_DIR, THUMB_CACHE_DIR, BUNDLE_ASSETS):
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass


ensure_dirs()

# 默认资源
DEFAULT_RINGTONE = asset_path("default_ring.wav")
DEFAULT_IMAGE = asset_path("default_bg.png")
ICON_FILE = asset_path("app.ico")
ICON_PNG = asset_path("app.png")
MASCOT_FILE = asset_path("mascot.png")

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# 单实例互斥量名称
MUTEX_NAME = "Global\\HomeManager_SingleInstance_v1"


def default_settings():
    return {
        "autostart": False,        # 开机自启动
        "wake_enabled": True,      # 睡眠状态下允许唤醒电脑
        "default_ringtone": "",    # 默认铃声（空=程序自带铃声）
        "default_image": "",       # 默认闹钟背景（空=程序自带背景）
        "snooze_minutes": 5,       # 贪睡时长（分钟）
        "wake_ahead_seconds": 20,  # 提前多少秒唤醒电脑
        "language": "zh",          # 界面语言 zh / ja / en
        "morning_enabled": False,  # 一键早安模式
        "morning_apps": [],        # 早安后自动启动的程序路径列表
        "focus_minutes": 25,       # 番茄钟专注时长
        "break_minutes": 5,        # 番茄钟休息时长
        "mascot_file": "",         # 自定义侧边栏吉祥物（空=自带）
    }
