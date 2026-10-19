@echo off
title AUTOSAR HLD Assistant - Stopping Services
color 0E

echo ============================================================
echo   AUTOSAR HLD Document Analysis Assistant
echo   Stopping all services (Frontend, Backend, and LLM)...
echo ============================================================
echo.

:: 1. Stop Streamlit application running on port 8501
echo [1/2] Stopping Streamlit Frontend and Backend (Port 8501)...
powershell -NoProfile -Command "$conns = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue; if ($conns) { $conns | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }; Write-Host '      Streamlit process stopped successfully.' } else { Write-Host '      No active process found on port 8501.' }"

:: 2. Stop Ollama LLM Service
echo.
echo [2/2] Stopping Ollama LLM Service...
powershell -NoProfile -Command "Get-Process -Name 'ollama', 'ollama_app' -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }; Write-Host '      Ollama service processes stopped.'"

echo.
color 0A
echo ============================================================
echo   All services have been stopped successfully!
echo ============================================================
echo.
ping 127.0.0.1 -n 3 >nul
