@echo off
chcp 65001 >nul
title 合同审计聊天系统 - Contract Audit Chat

echo.
echo ========================================
echo    合同审计聊天系统启动中...
echo    Contract Audit Chat Starting...
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python
    echo Error: Python not found, please install Python first
    pause
    exit /b 1
)

REM 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo ✅ 检测到虚拟环境，正在激活...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  未检测到虚拟环境，使用系统Python
)

REM 检查依赖
echo 🔍 检查依赖...
python -c "import langchain_core" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  检测到依赖缺失，正在安装...
    pip install -r requirements.txt
)

REM 启动聊天系统 (企业级版本)
echo 🚀 启动聊天系统 (企业级版本)...
python chat.py

echo.
echo ========================================
echo    聊天系统已退出
echo    Chat system exited
echo ========================================
pause 