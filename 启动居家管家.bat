@echo off
chcp 65001 >nul
title Home Manager Launcher
rem ============================================
rem 居家管家 - 双击启动器（无控制台窗口）
rem ============================================
set "APPDIR=%~dp0home_manager"
set "MAIN=%APPDIR%\main.pyw"
set "PYW=C:\Users\HP\AppData\Local\Doubao\User Data\sandbox_runtime\bases\c98c5042338ed152c6f10ecd8591889f\python\pythonw.exe"

if not exist "%MAIN%" (
    msg * "%MAIN% not found. Please keep the home_manager folder next to this launcher."
    exit /b 1
)

if exist "%PYW%" (
    start "" "%PYW%" "%MAIN%"
    exit /b 0
)

where pyw >nul 2>&1
if %errorlevel%==0 (
    start "" pyw -3 "%MAIN%"
    exit /b 0
)

start "" pythonw "%MAIN%"
exit /b 0
