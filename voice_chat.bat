@echo off
echo ========================================
echo   AI Call Center - Local Voice Chat
echo ========================================
echo.

cd /d "%~dp0"

set SERVER_UP=0
for /f "delims=" %%i in ('curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/health') do set SERVER_UP=%%i

if "%SERVER_UP%"=="200" goto ready

REM Locate Ollama
set OLLAMA_EXE=ollama
where ollama >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set OLLAMA_EXE=ollama
) else if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    set OLLAMA_EXE="%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
) else (
    echo [!] Ollama not found. Install it from https://ollama.com/download or run setup.bat
    exit /b 1
)

echo [1/2] Starting Ollama...
start /B "" %OLLAMA_EXE% serve
timeout /t 3 /nobreak >nul

echo [2/2] Starting FastAPI server...
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0run_server.py"
timeout /t 90 /nobreak >nul

:ready
echo [OK] Server ready, starting voice chat...
echo.
echo   Mic: press ENTER then speak (5 sec recording)
echo   Exit: type q
echo.
"%~dp0.venv\Scripts\python.exe" "%~dp0voice_chat.py"
pause
