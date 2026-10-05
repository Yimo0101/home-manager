# -*- mode: python ; coding: utf-8 -*-
"""居家管家 PyInstaller 打包配置（onedir 便携版）

构建：pyinstaller 居家管家.spec
产物：dist/居家管家/居家管家.exe（双击即用，数据写在程序同目录）
"""
import os

block_cipher = None
HERE = os.path.abspath(".")
ASSETS = os.path.join(HERE, "assets")

# 随包默认资源：排除用户私人铃声与设计源文件、重复图标
SKIP_FILES = {"起床铃声.mp3", "icon_master.png", "icon.ico", "icon.png"}

datas = []
for root, _dirs, files in os.walk(ASSETS):
    for name in files:
        if name in SKIP_FILES:
            continue
        full = os.path.join(root, name)
        rel_dir = os.path.relpath(root, HERE)
        datas.append((full, rel_dir.replace("\\", "/")))

hiddenimports = ["pystray._win32", "PIL._tkinter_finder"]

a = Analysis(
    ["main.pyw"],
    pathex=[HERE],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["numpy", "scipy", "matplotlib", "pytest", "imageio_ffmpeg"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="居家管家",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ASSETS, "app.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="居家管家",
)
