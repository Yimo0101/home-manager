# -*- coding: utf-8 -*-
# 居家管家 - 一键构建便携版并打 zip
# 用法：powershell -ExecutionPolicy Bypass -File .\build_release.ps1
param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$App = Join-Path $Root "home_manager"

Write-Host "==> 使用解释器：$Python"
& $Python --version
if ($LASTEXITCODE -ne 0) { throw "找不到 Python，请用 -Python 指定 python.exe 完整路径" }

Write-Host "==> 安装/检查 PyInstaller"
& $Python -m pip install --upgrade pyinstaller pillow pystray | Out-Null

Push-Location $App
try {
    Write-Host "==> 清理旧构建"
    if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
    if (Test-Path "dist")  { Remove-Item "dist" -Recurse -Force }

    Write-Host "==> PyInstaller 打包（onedir 便携版）"
    & $Python -m PyInstaller --noconfirm --clean "居家管家.spec"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller 打包失败" }

    $OutDir = Join-Path $App "dist\居家管家"
    if (-not (Test-Path (Join-Path $OutDir "居家管家.exe"))) {
        throw "未找到产物 exe：$OutDir"
    }

    # 附上使用说明
    $Readme = Join-Path $Root "使用说明.md"
    if (Test-Path $Readme) { Copy-Item $Readme (Join-Path $OutDir "使用说明.md") -Force }

    # 版本号
    $ver = (& $Python -c "import sys; sys.path.insert(0,'.'); import config; print(config.APP_VERSION)").Trim()
    $Zip = Join-Path $App ("dist\HomeManager-v{0}-portable.zip" -f $ver)
    if (Test-Path $Zip) { Remove-Item $Zip -Force }
    Write-Host "==> 压缩 zip：$Zip"
    Compress-Archive -Path (Join-Path $App "dist\居家管家") -DestinationPath $Zip -CompressionLevel Optimal

    Write-Host ""
    Write-Host "构建完成："
    Write-Host "  文件夹：$OutDir"
    Write-Host "  压缩包：$Zip"
}
finally {
    Pop-Location
}
