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

# Carpetas de las apps: por defecto en D:\ (oficina). Si esta PC usa otro disco
# (p. ej. una de casa sin D:), las redirigimos a ese disco — persistente con setx
# (para cuando se abra el ERP) y en esta sesión (para el setup_pc.py de abajo).
$AppDirs = [ordered]@{
    "SUITE_CONTABLE_DIR" = "\suite-contable"
    "DDJJ_IMPUESTOS_DIR" = "\ddjj-impuestos"
    "RETENCIONESPRO_DIR" = "\RetencionesPro"
    "COBRANZAS_DIR"      = "\PROYECTOS CLAUDE\cobranzas-osecac"
    "FACTURADOR_DIR"     = "\PROYECTOS CLAUDE\facturador-arca"
    "EMPLOYEE_PRO_DIR"   = "\PROYECTOS CLAUDE\employee-pro"
    "JUICIOS_DIR"        = "\control-juicios"
    "CONTABILIDAD_DIR"   = "\contabilidad"
}
if ($Drive -ne "D:") {
    Write-Host "Esta PC no tiene disco D:, uso $Drive y redirijo las carpetas." -ForegroundColor Yellow
    foreach ($k in $AppDirs.Keys) {
        $val = "$Drive$($AppDirs[$k])"
        setx $k "$val" | Out-Null                 # persistente (futuras sesiones)
        Set-Item -Path "Env:$k" -Value $val       # esta sesión (setup_pc.py)
    }
}

# ----------------------------------------------------------------------------
$ErrorActionPreference = "Stop"
function Existe($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
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

# 1) Requisitos: git, gh y python (se instalan solos con winget si faltan).
$reqs = @(
    @{ cmd = "git";    id = "Git.Git" },
    @{ cmd = "gh";     id = "GitHub.cli" },
    @{ cmd = "python"; id = "Python.Python.3.12" }
)
foreach ($r in $reqs) {
    if (-not (Existe $r.cmd)) {
        Write-Host "Instalando $($r.cmd)..." -ForegroundColor Yellow
        winget install --id $r.id -e --silent --accept-package-agreements --accept-source-agreements
        Refrescar-Path
    }
}
if (-not (Existe "git") -or -not (Existe "gh") -or -not (Existe "python")) {
    Write-Host "No pude instalar git/gh/python automaticamente." -ForegroundColor Red
    Write-Host "Instalalos a mano (winget install Git.Git GitHub.cli Python.Python.3.12) y volve a correr." -ForegroundColor Red
    Read-Host "Enter para salir"; exit 1
}

# 2) Autenticar gh con el token (sin navegador, sin login).
Write-Host "Autenticando con GitHub (token de solo lectura)..." -ForegroundColor Yellow
$TOKEN | gh auth login --with-token
gh auth setup-git

# 3) ERP: clonar o actualizar.
if (Test-Path "$SUITE\.git") {
    Write-Host "Actualizando el ERP..." -ForegroundColor Yellow
    git -C $SUITE pull --ff-only
} else {
    Write-Host "Bajando el ERP a $SUITE ..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path (Split-Path $SUITE) | Out-Null
    gh repo clone ematiromero98/suite-contable $SUITE
}

# 4) Dejar la PC lista: apps + dependencias + credenciales + acceso directo.
Write-Host "Preparando apps y credenciales (puede tardar unos minutos)..." -ForegroundColor Yellow
python "$SUITE\setup_pc.py"

Write-Host ""
Write-Host "==  LISTO. Abri 'Suite Contable' desde el Escritorio.  ==" -ForegroundColor Green
Read-Host "Enter para salir"
