@echo off
chcp 65001 > nul
setlocal

set PYTHON=C:\Users\1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
set WORKDIR=%~dp0

cd /d "%WORKDIR%"

echo [思政教学程序] 检查依赖...
"%PYTHON%" -m pip install fastapi uvicorn -q 2>nul

echo [思政教学程序] 启动中...
start "" /B "%PYTHON%" main.py

echo [思政教学程序] 已启动！
echo 访问地址: http://127.0.0.1:28200/
echo.
echo 按任意键关闭本窗口（程序仍在后台运行）...
pause >nul
endlocal
