@echo off
setlocal

set "WORKDIR=%~dp0"
cd /d "%WORKDIR%"

set "PYTHON_EXE="
set "PYTHON_ARGS="

where python >nul 2>nul
if not errorlevel 1 set "PYTHON_EXE=python"

if not defined PYTHON_EXE (
  where py >nul 2>nul
  if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARGS=-3"
  )
)

if not defined PYTHON_EXE (
  set "BUNDLED_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  if exist "%BUNDLED_PYTHON%" set "PYTHON_EXE=%BUNDLED_PYTHON%"
)

if not defined PYTHON_EXE (
  echo [project_04] Python not found. Please install Python 3 or add it to PATH.
  pause
  exit /b 1
)

echo [project_04] Using %PYTHON_EXE% %PYTHON_ARGS%
echo [project_04] Checking dependencies...
call "%PYTHON_EXE%" %PYTHON_ARGS% -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo [project_04] Dependency installation failed.
  pause
  exit /b 1
)

echo [project_04] Verifying runtime imports...
call "%PYTHON_EXE%" %PYTHON_ARGS% -c "import fastapi, uvicorn, docx, pdfplumber"
if errorlevel 1 (
  echo [project_04] Required packages are still unavailable.
  pause
  exit /b 1
)

echo [project_04] Starting...
start "" /B "%PYTHON_EXE%" %PYTHON_ARGS% main.py
if errorlevel 1 (
  echo [project_04] Startup command failed.
  pause
  exit /b 1
)

echo [project_04] Started.
echo Default URL: http://127.0.0.1:28200/
echo If port 28200 is busy, the program will use the next free port in the same range.
echo.
echo Press any key to close this window. The program keeps running in background.
pause >nul
endlocal
