@echo off
echo Building Navigium for Windows...
cd /d "%~dp0"
call venv\Scripts\activate.bat
flet build windows --project Navigium
echo.
echo Done! Executable is in build\windows\
pause
