@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   Настройка Video Trimmer
echo ========================================
echo.

cd /d "%~dp0"
set "PYTHON_DIR=%~dp0python-3.12.10-embed-amd64"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

echo Проверка Python...
if not exist "%PYTHON_EXE%" (
    echo ОШИБКА: Python не найден в папке python-3.12.10-embed-amd64
    pause
    exit /b 1
)

echo Python найден: %PYTHON_EXE%
echo.

REM Check if pip exists
"%PYTHON_EXE%" -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Установка pip...
    
    REM Download get-pip.py
    if not exist "%PYTHON_DIR%\get-pip.py" (
        echo Скачивание get-pip.py...
        
        REM Try curl first (available in Windows 10+)
        curl -L -o "%PYTHON_DIR%\get-pip.py" https://bootstrap.pypa.io/get-pip.py 2>nul
        if not exist "%PYTHON_DIR%\get-pip.py" (
            REM Fallback to certutil
            echo Curl не сработал, пробуем certutil...
            certutil -urlcache -split -f "https://bootstrap.pypa.io/get-pip.py" "%PYTHON_DIR%\get-pip.py" >nul 2>&1
        )
        if not exist "%PYTHON_DIR%\get-pip.py" (
            REM Fallback to PowerShell with TLS fix
            echo Пробуем PowerShell...
            powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%PYTHON_DIR%\get-pip.py'"
        )
        if not exist "%PYTHON_DIR%\get-pip.py" (
            echo ОШИБКА: Не удалось скачать get-pip.py
            echo Скачайте вручную: https://bootstrap.pypa.io/get-pip.py
            echo и поместите в папку: %PYTHON_DIR%
            pause
            exit /b 1
        )
    )
    
    REM Create Lib/site-packages directory
    if not exist "%PYTHON_DIR%\Lib\site-packages" (
        mkdir "%PYTHON_DIR%\Lib\site-packages"
    )
    
    REM Install pip
    "%PYTHON_EXE%" "%PYTHON_DIR%\get-pip.py" --no-warn-script-location
    
    REM Verify pip works now
    "%PYTHON_EXE%" -m pip --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ОШИБКА: Не удалось установить pip
        pause
        exit /b 1
    )
    echo Pip установлен успешно!
    echo.
) else (
    echo Pip уже установлен.
    echo.
)

echo Установка зависимостей из requirements.txt...
"%PYTHON_EXE%" -m pip install --no-warn-script-location -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось установить зависимости
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Настройка завершена успешно!
echo ========================================
echo.
echo Теперь вы можете запускать приложение
echo с помощью файла run.bat
echo.
pause
