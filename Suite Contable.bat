@echo off
REM Lanza la Suite Contable sin consola negra.
cd /d "%~dp0"
REM El instalador anota que pythonw tiene PyQt6 (por si Python no esta en el PATH).
set "PYW=pythonw"
if exist "%LOCALAPPDATA%\Suite Contable\pythonw.txt" set /p PYW=<"%LOCALAPPDATA%\Suite Contable\pythonw.txt"
if not "%PYW%"=="pythonw" if not exist "%PYW%" set "PYW=pythonw"
start "" "%PYW%" "%~dp0main.py"
