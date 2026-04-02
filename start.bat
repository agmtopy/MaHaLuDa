@echo off
REM MaHaLuDa 启动脚本 (Windows)
REM 请确保已安装Python和所有依赖

echo ====================================
echo MaHaLuDa 截图工具
echo ====================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM 显示Python版本
echo [信息] Python版本:
python --version
echo.

REM 检查是否在虚拟环境
python -c "import sys; print('[信息] Python路径:', sys.executable)" 2>nul
echo.

REM 检查依赖
echo [检查] 正在检查依赖库...
python -c "import PyQt6; import keyboard; import mss; import PIL; import loguru" 2>nul
if errorlevel 1 (
    echo [警告] 缺少依赖库，正在安装...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo.
    echo [成功] 依赖安装完成
    echo.
)

REM 启动程序
echo [启动] 正在启动MaHaLuDa...
echo [提示] 程序将最小化到系统托盘
echo [提示] 按 Ctrl+Shift+A 进行截图
echo [提示] 按 Ctrl+C 退出程序
echo.
echo ====================================
echo.

python -m src.main

if errorlevel 1 (
    echo.
    echo [错误] 程序异常退出
    pause
)