@echo off
cd /d "%~dp0"
start "Boersenmailer" ".venv\Scripts\python.exe" app.py
timeout /t 2 /nobreak >nul
start "" "http://localhost:5000"
