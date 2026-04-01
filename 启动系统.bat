@echo off
chcp 65001 >nul
title 亚马逊广告智能追踪系统
echo ====================================================
echo   亚马逊广告智能追踪系统
echo   启动中...  浏览器将自动打开
echo   关闭此窗口将停止系统
echo ====================================================
echo.
cd /d "%~dp0"
python run.py
if %errorlevel% neq 0 (
    echo.
    echo 启动失败！请确认已安装 Python 和依赖包。
    echo 运行: pip install -r requirements.txt
    pause
)
