@echo off
title AUTOSAR HLD Assistant - Starting Services
color 0A

echo ============================================================
echo   AUTOSAR HLD Document Analysis Assistant
echo   Starting all services (Frontend, Backend, and LLM)...
echo ============================================================
echo.

:: Move to script root directory
cd /d "%~dp0"

:: 1. Verify Python availability
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERROR] Python was not found in your PATH!
    echo Please install Python 3.10+ and add it to your PATH.
    pause
    exit /b 1
)

:: 2. Check and Start Ollama LLM Service
echo [1/3] Checking Ollama LLM service...
powershell -NoProfile -Command "try { $res = Invoke-WebRequest -Uri 'http://localhost:11434' -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>&1

if %ERRORLEVEL% equ 0 (
    echo       Ollama is already running at http://localhost:11434.
) else (
    echo       Starting Ollama background server...
    start "" /B ollama serve >nul 2>&1
    :: Wait up to 10 seconds for Ollama to become ready
    powershell -NoProfile -Command "$ready = $false; for ($i=0; $i -lt 10; $i++) { try { $res = Invoke-WebRequest -Uri 'http://localhost:11434' -UseBasicParsing -TimeoutSec 1; $ready = $true; break } catch { Start-Sleep -Seconds 1 } }; if (-not $ready) { exit 1 }"
    if %ERRORLEVEL% equ 0 (
        echo       Ollama successfully started.
    ) else (
        echo       [WARNING] Could not start Ollama automatically.
        echo       If you want to use local models, please start Ollama manually.
    )
)

:: 3. Configure UTF-8 encoding for Windows console
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

:: 4. Stop any stale process on port 8501 before launching
echo.
echo [2/3] Checking port 8501...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

:: 5. Launch Streamlit Application
echo.
echo [3/3] Launching Streamlit Application at http://localhost:8501 ...
echo.
echo ============================================================
echo   Application is now starting!
echo   Browser will open automatically.
echo   To STOP the application, run 'stop_app.bat' or press Ctrl+C.
echo ============================================================
echo.

start "" "http://localhost:8501"
python -m streamlit run app.py --server.port 8501 --server.headless false

pause
