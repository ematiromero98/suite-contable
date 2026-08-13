# Crea un acceso directo "Suite Contable" en el Escritorio, apuntando al .bat.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$bat  = Join-Path $here "Suite Contable.bat"
$desktop = [Environment]::GetFolderPath("Desktop")
$lnk = Join-Path $desktop "Suite Contable.lnk"

# Icono propio de la Suite (con fallback al del estudio).
$ico = Join-Path $here "assets\suite.ico"
if (-not (Test-Path $ico)) { $ico = "D:\ddjj-impuestos\assets\mrasoc.ico" }

$sh = New-Object -ComObject WScript.Shell
$s  = $sh.CreateShortcut($lnk)
$s.TargetPath       = $bat
$s.WorkingDirectory = $here
if (Test-Path $ico) { $s.IconLocation = $ico }
$s.Description = "Suite Contable - MR & Asociados"
$s.Save()
Write-Host "Acceso directo creado en: $lnk"
