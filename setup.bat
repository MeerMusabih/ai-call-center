@echo off
setlocal
cd /d "%~dp0"
echo ========================================
echo   AI Call Center - Setup
echo ========================================
echo.
echo This script installs everything needed to run the
echo AI Call Center on a fresh Windows machine.
echo.
echo It will:
echo   1. Install Python 3.12 (if missing)
echo   2. Install FFmpeg (if missing)
echo   3. Install Ollama and pull the LLM model
echo   4. Create a virtual environment and install Python packages
echo   5. Create your .env config file
echo.
echo Downloads require an internet connection (~2GB total).
echo.

choice /C YN /M "Continue with setup"
if errorlevel 2 exit /b 1

REM ---------------------------------------------------------------
REM 1) Python
REM ---------------------------------------------------------------
python --version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
    echo [OK] Python %PYVER% found
) else (
    echo [1] Python not found. Installing Python 3.12...
    curl -sSL -o "%TEMP%\python-setup.exe" "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
    "%TEMP%\python-setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    echo [OK] Python installed. Reopen this terminal, then run setup.bat again.
    pause
    exit /b 0
)

REM ---------------------------------------------------------------
REM 2) FFmpeg
REM ---------------------------------------------------------------
set FFMPEG_DIR=
where ffmpeg >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] FFmpeg found on PATH
) else (
    echo [2] FFmpeg not found. Downloading...
    curl -sSL -o "%TEMP%\ffmpeg.zip" "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    powershell -Command "Expand-Archive -Path '%TEMP%\ffmpeg.zip' -DestinationPath '%LOCALAPPDATA%\ffmpeg' -Force"
    for /d %%d in ("%LOCALAPPDATA%\ffmpeg\ffmpeg-*") do set "FFMPEG_DIR=%%d\bin"
    if not defined FFMPEG_DIR (
        echo [!] FFmpeg extraction failed. Install it manually from https://ffmpeg.org/download.html
        pause
        exit /b 1
    )
)
if defined FFMPEG_DIR (
    echo [OK] FFmpeg installed to %FFMPEG_DIR%
)

REM ---------------------------------------------------------------
REM 3) Ollama + model
REM ---------------------------------------------------------------
where ollama >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Ollama found
) else if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    echo [OK] Ollama found
) else (
    echo [3] Ollama not found. Installing...
    curl -sSL -o "%TEMP%\OllamaSetup.exe" "https://ollama.com/download/OllamaSetup.exe"
    "%TEMP%\OllamaSetup.exe" /S
    echo [OK] Ollama installed
)

echo Pulling LLM model (qwen2.5:1.5b, ~1GB)...
start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
timeout /t 5 /nobreak >nul
"%LOCALAPPDATA%\Programs\Ollama\ollama.exe" pull qwen2.5:1.5b

REM ---------------------------------------------------------------
REM 4) Python packages
REM ---------------------------------------------------------------
echo [4] Creating virtual environment and installing packages...
if not exist ".venv" python -m venv .venv
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [!] Package installation failed. Check the error above.
    pause
    exit /b 1
)

REM ---------------------------------------------------------------
REM 5) .env
REM ---------------------------------------------------------------
if not exist ".env" (
    echo [5] Creating .env from .env.example...
    copy ".env.example" ".env" >nul
)
if defined FFMPEG_DIR (
    echo Setting FFMPEG_PATH in .env...
    powershell -Command "(Get-Content '.env') -replace '^FFMPEG_PATH=.*', 'FFMPEG_PATH=%FFMPEG_DIR%' | Set-Content '.env'"
)
if not exist ".env" (
    echo [!] Failed to create .env
    pause
    exit /b 1
)
echo   Set TWILIO_* values later if you use real phone calls.

echo.
echo ========================================
echo   Setup complete!
echo ========================================
echo.
echo   Run  voice_chat.bat   to test the voice assistant
echo   Run  start.bat        to start the server + dashboard
echo.
pause
