@echo off
setlocal
cd /d "%~dp0"
where python.exe >nul 2>nul
if errorlevel 1 (
  echo Python was not found in PATH. Install Python 3.11 with Tkinter or run backup_gui.py with your Python executable.
  pause
  exit /b 1
)
python.exe backup_gui.py
if errorlevel 1 pause
