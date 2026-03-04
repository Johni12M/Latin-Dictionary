@echo off
if not exist "%~dp0__pycache__" (
    "%~dp0venv\Scripts\python.exe" -m compileall -q "%~dp0" >nul 2>&1
)
start "" /ABOVENORMAL /d "%~dp0" "%~dp0venv\Scripts\pythonw.exe" -O main.py
