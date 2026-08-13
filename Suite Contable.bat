@echo off
REM Lanza la Suite Contable sin consola negra.
cd /d "%~dp0"
start "" pythonw "%~dp0main.py"
