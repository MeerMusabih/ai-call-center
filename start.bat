@echo off
echo ========================================
echo   AI Call Center - Start
echo ========================================
echo.

cd /d "%~dp0"

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

REM Start Ollama
echo [1/2] Starting Ollama...
start /B "" %OLLAMA_EXE% serve
timeout /t 3 /nobreak >nul

REM Check Ollama
curl -s http://localhost:11434 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Ollama not responding, waiting...
    timeout /t 5 /nobreak >nul
)
echo [OK] Ollama running

REM Start FastAPI (pythonw wrapper keeps it alive)
echo [2/2] Starting FastAPI server...
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0run_server.py"
timeout /t 90 /nobreak >nul

REM Check server
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Server running on http://localhost:8000
    echo [OK] Dashboard: http://localhost:8000/dashboard/
) else (
    echo [!] Server may still be loading models...
)

echo.
echo   Dashboard:  http://localhost:8000/dashboard/
echo   Health:     http://localhost:8000/health
echo   API Docs:   http://localhost:8000/docs
echo.
echo To connect Twilio, run: ngrok http 8000
echo Then update TWILIO_WEBHOOK_URL in .env
echo.
pause
