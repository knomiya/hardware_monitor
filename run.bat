@echo off
REM 硬件温度监控启动脚本
chcp 65001 > nul
title 硬件温度监控

conda run -n hardware-monitor python main.py

if not exist logs mkdir logs
if not exist data mkdir data

echo 正在启动硬件温度监控...
python main.py

if errorlevel 1 (
    echo 启动失败，请确保已安装所有依赖
    echo 错误代码: %errorlevel%
    pause
    exit /b %errorlevel%
)