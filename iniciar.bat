@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Primero instala el proyecto siguiendo README.md.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m mc_finder
if errorlevel 1 pause
