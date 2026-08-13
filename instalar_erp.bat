@echo off
REM ════════════════════════════════════════════════════════════════════════
REM   instalar_erp.bat — Instala la Suite Contable (ERP) en esta PC, de un
REM   solo clic. El repo es PÚBLICO, así que no necesita token, ni gh, ni tocar
REM   RetencionesPro. Descargá este archivo y hacele doble clic donde sea.
REM ════════════════════════════════════════════════════════════════════════
title Instalar Suite Contable (ERP)

set "SUITE_DIR=%SUITE_CONTABLE_DIR%"
if "%SUITE_DIR%"=="" (
    if exist "D:\" ( set "SUITE_DIR=D:\suite-contable" ) else ( set "SUITE_DIR=%USERPROFILE%\suite-contable" )
)

echo.
echo Instalando la Suite Contable (ERP) en:
echo   %SUITE_DIR%
echo.

where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: no encontre 'git' en esta PC.
    echo Instala "Git para Windows" ^(https://git-scm.com/download/win^) y reintenta.
    pause
    exit /b 1
)

if exist "%SUITE_DIR%\.git" (
    echo Ya estaba: actualizo a la ultima version...
    pushd "%SUITE_DIR%"
    git pull --ff-only
    popd
) else (
    git clone https://github.com/ematiromero98/suite-contable.git "%SUITE_DIR%"
)

if not exist "%SUITE_DIR%\main.py" (
    echo ERROR: no se pudo instalar la Suite. Revisa tu conexion a internet.
    pause
    exit /b 1
)

REM Acceso directo en el Escritorio (con su icono).
if exist "%SUITE_DIR%\crear_acceso_directo.ps1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%SUITE_DIR%\crear_acceso_directo.ps1" >nul 2>&1
)

echo.
echo ===============================================================
echo   Listo. Se creo "Suite Contable" en el Escritorio. La abro.
echo ===============================================================
timeout /t 2 /nobreak >nul
start "" "%SUITE_DIR%\Suite Contable.bat"
exit /b 0
