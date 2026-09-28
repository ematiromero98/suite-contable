# ============================================================================
#  INSTALADOR "CERO LOGINS" — Suite Contable (MR & Asociados)
# ----------------------------------------------------------------------------
#  Deja una PC nueva 100% lista SIN entrar a GitHub ni a Google Drive:
#  instala lo necesario, se autentica con un token de SÓLO LECTURA, baja el ERP
#  y todas las apps, trae las credenciales y crea el acceso directo. De ahí en
#  más el ERP se auto-actualiza solo.
#
#  USO (una vez por PC):
#    1) Pegá el token en la variable  $TOKEN  de acá abajo.
#    2) Clic derecho sobre este archivo  >  "Ejecutar con PowerShell".
#       (Si Windows lo bloquea: abrí PowerShell y corré
#         powershell -ExecutionPolicy Bypass -File .\instalar_suite.ps1 )
#
#  El token se crea UNA sola vez en GitHub (Settings > Developer settings >
#  Fine-grained tokens): permiso "Contents: Read-only" sobre los repos del
#  estudio, incluido  suite-secretos.  Es de sólo lectura: no puede modificar
#  nada. El mismo token/instalador sirve para todas las PCs.
# ============================================================================

$TOKEN = "PEGA_TU_TOKEN_ACA"          # <-- token fino de GitHub, SÓLO LECTURA

# Carpeta del ERP. Usa D:\ si existe (como en la oficina), si no C:\.
$Drive = if (Test-Path "D:\") { "D:" } else { "C:" }
$SUITE = "$Drive\suite-contable"

# ----------------------------------------------------------------------------
$ErrorActionPreference = "Stop"
function Existe($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
# Python REAL (el "python" de la Microsoft Store es un stub que no corre nada).
function Python-Real {
    $cands = @("$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
               "$env:ProgramFiles\Python312\python.exe")
    foreach ($c in $cands) { if (Test-Path $c) { return $c } }
    foreach ($c in @("py", "python")) {
        if (Existe $c) {
            try {
                $exe = & $c -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $exe -and (Test-Path $exe.Trim())) { return $exe.Trim() }
            } catch {}
        }
    }
    return $null
}
function Refrescar-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

Write-Host ""
Write-Host "==  Instalador Suite Contable  ==" -ForegroundColor Green

if ([string]::IsNullOrWhiteSpace($TOKEN) -or $TOKEN -eq "PEGA_TU_TOKEN_ACA") {
    Write-Host "FALTA pegar el token arriba, en la variable TOKEN." -ForegroundColor Red
    Read-Host "Enter para salir"; exit 1
}

# 1) Requisitos: git y python (se instalan solos con winget si faltan).
#    OJO: NO tocamos `gh auth`. El token va a un archivo aparte (paso 2), así el
#    login personal de quien administre queda intacto y cualquier PC puede ser
#    administradora sin conflicto.
if (-not (Existe "git")) {
    Write-Host "Instalando git..." -ForegroundColor Yellow
    winget install --id Git.Git -e --source winget --silent --accept-package-agreements --accept-source-agreements
    Refrescar-Path
    if (-not (Existe "git") -and (Test-Path "$env:ProgramFiles\Git\cmd")) { $env:Path += ";$env:ProgramFiles\Git\cmd" }
}
$PY = Python-Real
if (-not $PY) {
    Write-Host "Instalando Python 3.12..." -ForegroundColor Yellow
    winget install --id Python.Python.3.12 -e --source winget --silent --accept-package-agreements --accept-source-agreements
    Refrescar-Path
    $PY = Python-Real
}
if (-not (Existe "git") -or -not $PY) {
    Write-Host "No pude instalar git/python automaticamente." -ForegroundColor Red
    Write-Host "Instalalos a mano (winget install Git.Git Python.Python.3.12) y volve a correr." -ForegroundColor Red
    Read-Host "Enter para salir"; exit 1
}
Write-Host "Python: $PY" -ForegroundColor DarkGray

# 2) Guardar el token del runtime en un archivo (NO en el gh personal).
$SuiteData = "$env:LOCALAPPDATA\Suite Contable"
New-Item -ItemType Directory -Force -Path $SuiteData | Out-Null
Set-Content -Path "$SuiteData\gh_token.txt" -Value $TOKEN -NoNewline -Encoding ascii
Write-Host "Token de solo-lectura guardado (sin tocar tu login de GitHub)." -ForegroundColor Yellow

# 3) ERP: clonar o actualizar con el token (git directo, sin gh).
$AuthUrl  = "https://x-access-token:$TOKEN@github.com/ematiromero98/suite-contable.git"
$CleanUrl = "https://github.com/ematiromero98/suite-contable.git"
if (Test-Path "$SUITE\.git") {
    Write-Host "Actualizando el ERP..." -ForegroundColor Yellow
    git -C $SUITE remote set-url origin $AuthUrl
    git -C $SUITE pull --ff-only
    git -C $SUITE remote set-url origin $CleanUrl
} else {
    Write-Host "Bajando el ERP a $SUITE ..." -ForegroundColor Yellow
    $__parent = Split-Path $SUITE
    if ($__parent -and -not (Test-Path $__parent)) { New-Item -ItemType Directory -Force -Path $__parent | Out-Null }
    git clone $AuthUrl $SUITE
    if (Test-Path "$SUITE\.git") { git -C $SUITE remote set-url origin $CleanUrl }
}

# 4) Si esta PC no tiene D:, redirigir las carpetas de TODAS las apps al disco
#    elegido. La lista sale de config.APPS del ERP recién bajado (así nunca queda
#    desfasada cuando se suma o renombra una app). Persistente con setx (para el
#    ERP) y en esta sesión (para el setup_pc.py de abajo).
if ($Drive -ne "D:") {
    Write-Host "Esta PC no tiene disco D:, uso $Drive y redirijo las carpetas." -ForegroundColor Yellow
    $pares = @("SUITE_CONTABLE_DIR=D:\suite-contable")
    $pares += & $PY -c "import sys; sys.path.insert(0, sys.argv[1]); import config; [print(a['env_dir'] + '=' + a['dir']) for a in config.APPS if a.get('env_dir')]" $SUITE
    foreach ($p in $pares) {
        $k, $v = $p -split "=", 2
        if (-not $k -or -not $v) { continue }
        $v = $v.Trim() -replace '^[Dd]:', $Drive
        setx $k "$v" | Out-Null
        Set-Item -Path "Env:$k" -Value $v
    }
}

# 5) Dependencias del propio ERP (PyQt6) en ese Python, y dejar anotado qué
#    pythonw usar: el acceso directo lo lee, así no depende de que Python haya
#    quedado en el PATH (winget no siempre lo agrega).
Write-Host "Instalando dependencias del ERP (PyQt6)..." -ForegroundColor Yellow
& $PY -m pip install -q --upgrade pip
& $PY -m pip install -q -r "$SUITE\requirements.txt"
$PYW = Join-Path (Split-Path $PY) "pythonw.exe"
if (Test-Path $PYW) { Set-Content -Path "$SuiteData\pythonw.txt" -Value $PYW -NoNewline -Encoding ascii }

# 6) Dejar la PC lista: apps + dependencias + credenciales + acceso directo.
Write-Host "Preparando apps y credenciales (puede tardar unos minutos)..." -ForegroundColor Yellow
& $PY "$SUITE\setup_pc.py"

Write-Host ""
Write-Host "==  LISTO. Abri 'Suite Contable' desde el Escritorio.  ==" -ForegroundColor Green
Read-Host "Enter para salir"
