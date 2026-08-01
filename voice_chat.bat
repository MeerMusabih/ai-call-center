@echo off
echo ========================================
echo   AI Call Center - Local Voice Chat
echo ========================================
echo.

cd /d "%~dp0"

set SERVER_UP=0
for /f "delims=" %%i in ('curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/health') do set SERVER_UP=%%i

if "%SERVER_UP%"=="200" goto ready

echo [1/2] Starting Ollama...
start /B "" "C:\Users\sirh9\AppData\Local\Programs\Ollama\ollama.exe" serve
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
