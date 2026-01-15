@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "APP_DIR=%~dp0"
set "PYTHON_DIR=%~dp0python-3.12.10-embed-amd64"
set "PYTHONW_EXE=%PYTHON_DIR%\pythonw.exe"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

REM Set MPV_DLL to use libmpv-2.dll
set "MPV_DLL=%APP_DIR%libmpv-2.dll"

REM Add application directory to PATH for DLL loading
set "PATH=%APP_DIR%;%PATH%"

REM Check if Python exists
if not exist "%PYTHONW_EXE%" (
    echo ОШИБКА: Python не найден!
    pause
    exit /b 1
)

REM Check if dependencies are installed
"%PYTHON_EXE%" -c "import PyQt6" >nul 2>&1
if %errorlevel% neq 0 (
    echo Зависимости не установлены. Запустите сначала setup.bat
    pause
    exit /b 1
)

REM Run the application without console window
start "" "%PYTHONW_EXE%" main.py
