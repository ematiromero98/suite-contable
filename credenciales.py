# -*- coding: utf-8 -*-
"""
credenciales.py — Trae el `.env` de la Suite (credenciales de Supabase + token
de GitHub) desde el Google Drive del estudio a ESTA PC.

Por qué existe: el `.env` NO se sube a git (tiene secretos) y este repo es
PÚBLICO. Entonces un clon nuevo no lo trae y las apps fallan con
"Falta SUPABASE_URL". Este módulo lo baja de forma segura:

  - Usa `rclone` (herramienta portable open-source, se descarga sola una vez).
  - Pide ACCESO a Google Drive: abre el navegador para que el usuario inicie
    sesión con la CUENTA DEL ESTUDIO y apruebe (OAuth). El `.env` vive PRIVADO
    en esa cuenta (sin links públicos), así que sólo quien tenga esa sesión
    puede bajarlo.
  - Deja el `.env` donde las apps lo buscan y fija SUITE_ENV.

IMPORTANTE: acá NO hay ninguna credencial. Sólo la lógica que pide el acceso.
Los secretos viven en el Drive privado del estudio y en Supabase.
"""
import hashlib
import os
import shutil
import subprocess
import tempfile

import config

# rclone oficial (open-source). VERSIÓN FIJA + hash SHA256 verificado antes de
# extraer/ejecutar el binario (defensa supply-chain: no correr un ejecutable
# bajado sin validar su integridad). Antes se bajaba "rclone-current-...zip",
# que apunta a un binario que cambia sin aviso y no se podía verificar.
# El hash sale del SHA256SUMS oficial: downloads.rclone.org/<version>/SHA256SUMS
RCLONE_VERSION = "v1.68.2"
RCLONE_ZIP = f"rclone-{RCLONE_VERSION}-windows-amd64.zip"
RCLONE_URL = f"https://downloads.rclone.org/{RCLONE_VERSION}/{RCLONE_ZIP}"
RCLONE_SHA256 = "812bf76cc02c04cf6327f3683f3d5a88e47d36c39db84c1a745777496be7d993"

# Remoto de rclone y ruta del archivo dentro del Drive del estudio.
REMOTO = "suite"
DRIVE_PATH = "suite:Suite Contable/.env"

# Cuenta del estudio (la que tiene el .env). Se le muestra al usuario para que
# elija ESA cuenta en la pantalla de permiso de Google, no la personal de la PC.
CUENTA_ESTUDIO = "ematiromero98@gmail.com"

# Apps que leen un `.env` local con las credenciales COMPARTIDAS de la Suite
# (mismo proyecto Supabase): RetencionesPro, DDJJ Impuestos y Control de Juicios.
_APPS_ENV = ("reten", "ddjj", "juicios", "contabilidad")

# Apps con secreto PROPIO (no usan el `.env` compartido). Cada una guarda sus
# credenciales en un archivo aparte, gitignored, que vive PRIVADO en la carpeta
# "Suite Contable" del Drive del estudio. Se bajan con el MISMO remoto rclone.
#   key        : key de la app en config.APPS
#   drive      : nombre del archivo dentro de "Suite Contable/" en el Drive
#   local      : nombre del archivo dentro de la carpeta de la app
#   marca      : archivo cuya existencia = "ya configurada" (para no re-bajar)
#   configurar : correr configurar.py tras bajar el secreto (Cobranzas genera
#                .env + config.json desde secretos.json; Employee lo lee directo)
# Facturador ARCA NO va acá: versiona su `nube.json` + `certs/` en su repo
# PRIVADO, así que el `gh repo clone` ya se los trae a cada PC.
_APPS_SECRETO = (
    {"key": "cobranzas", "drive": "cobranzas.secretos.json", "local": "secretos.json",
     "marca": ".env", "configurar": True},
    {"key": "employee", "drive": "employee.secretos.json", "local": "secretos.json",
     "marca": "secretos.json", "configurar": False},
)

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def base_dir():
    """Carpeta local de trabajo de la Suite en esta PC."""
    root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(root, "Suite Contable")


def env_central():
    """Ruta central donde queda el `.env` bajado (fuente para las copias)."""
    return os.path.join(base_dir(), ".env")


def _candidatos_env():
    """Todos los lugares donde una app podría encontrar el `.env`."""
    rutas = []
    se = os.environ.get("SUITE_ENV", "").strip()
    if se:
        rutas.append(se)
    od = os.environ.get("OneDrive", "").strip()
    if od:
        rutas.append(os.path.join(od, "Suite Contable", ".env"))
    rutas.append(env_central())
    for a in config.APPS:
        if a["key"] in _APPS_ENV:
            rutas.append(os.path.join(a["dir"], ".env"))
    return rutas


def env_presente():
    """True si esta PC ya tiene el `.env` en algún lugar válido."""
    return any(os.path.isfile(p) for p in _candidatos_env())


def _rclone_exe():
    return os.path.join(base_dir(), "rclone", "rclone.exe")


def _ensure_rclone():
    """Devuelve la ruta a rclone.exe, descargándolo la primera vez."""
    rc = _rclone_exe()
    if os.path.isfile(rc):
        return rc
    os.makedirs(os.path.dirname(rc), exist_ok=True)
    import urllib.request
    import zipfile
    tmpzip = os.path.join(tempfile.gettempdir(), "rclone_dl.zip")
    urllib.request.urlretrieve(RCLONE_URL, tmpzip)
    # Verificar la integridad del ZIP ANTES de abrirlo/extraerlo/ejecutarlo.
    h = hashlib.sha256()
    with open(tmpzip, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    digest = h.hexdigest()
    if digest.lower() != RCLONE_SHA256.lower():
        try:
            os.remove(tmpzip)
        except OSError:
            pass
        raise RuntimeError(
            "El ZIP de rclone descargado NO coincide con el hash SHA256 "
            f"esperado ({RCLONE_VERSION}); se aborta por seguridad.\n"
            f"  esperado: {RCLONE_SHA256}\n  obtenido: {digest}")
    tmpdir = tempfile.mkdtemp(prefix="rclone_")
    try:
        with zipfile.ZipFile(tmpzip) as z:
            z.extractall(tmpdir)
        origen = None
        for root, _dirs, files in os.walk(tmpdir):
            if "rclone.exe" in files:
                origen = os.path.join(root, "rclone.exe")
                break
        if not origen:
            raise RuntimeError("el zip de rclone no tenía rclone.exe")
        shutil.copy2(origen, rc)
    finally:
        try:
            os.remove(tmpzip)
        except OSError:
            pass
        shutil.rmtree(tmpdir, ignore_errors=True)
    if not os.path.isfile(rc):
        raise RuntimeError("no se pudo preparar rclone")
    return rc


def _rclone(rc, *args, timeout=120):
    return subprocess.run([rc, *args], capture_output=True, text=True,
                          timeout=timeout, creationflags=_NO_WINDOW)


def _bajar_env(rc):
    """Baja el `.env` a `env_central()`. Si el remoto no está configurado, lanza
    el OAuth (abre el navegador) y reintenta. Devuelve True si quedó el archivo."""
    destino = env_central()
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    # 1) Intento directo: si el remoto ya existe (de una corrida previa o del
    #    .bat), baja sin volver a pedir acceso.
    try:
        _rclone(rc, "copyto", DRIVE_PATH, destino, timeout=90)
    except Exception:                                       # noqa: BLE001
        pass
    if os.path.isfile(destino):
        return True
    # 2) Falta el acceso: crear el remoto dispara el OAuth (navegador).
    _rclone(rc, "config", "create", REMOTO, "drive",
            "scope=drive.readonly", timeout=300)
    try:
        _rclone(rc, "copyto", DRIVE_PATH, destino, timeout=90)
    except Exception:                                       # noqa: BLE001
        pass
    return os.path.isfile(destino)


def _distribuir_env():
    """Copia el `.env` central a donde las apps lo buscan y fija SUITE_ENV.
    Devuelve la lista de lugares donde quedó."""
    central = env_central()
    puestos = []
    for a in config.APPS:
        if a["key"] in _APPS_ENV and os.path.isdir(a["dir"]):
            try:
                shutil.copy2(central, os.path.join(a["dir"], ".env"))
                puestos.append(a["dir"])
            except OSError:
                pass
    # OneDrive (si está logueado): lo detectan RetencionesPro 1.42.4+ / DDJJ 2.2.4+
    od = os.environ.get("OneDrive", "").strip()
    if od and os.path.isdir(od):
        try:
            dst = os.path.join(od, "Suite Contable")
            os.makedirs(dst, exist_ok=True)
            shutil.copy2(central, os.path.join(dst, ".env"))
            puestos.append(dst)
        except OSError:
            pass
    # Variable persistente (SUITE_ENV) apuntando al central.
    try:
        subprocess.run(["setx", "SUITE_ENV", central], capture_output=True,
                       text=True, timeout=15, creationflags=_NO_WINDOW)
    except Exception:                                       # noqa: BLE001
        pass
    return puestos


def _dir_app(key):
    """Carpeta de una app de la suite en esta PC (None si no está en la config)."""
    for a in config.APPS:
        if a["key"] == key:
            return a["dir"]
    return None


def _secreto_pendiente(spec):
    """True si esa app está instalada pero le falta su secreto/config (según la
    'marca'). False si no está instalada o ya está configurada."""
    d = _dir_app(spec["key"])
    if not d or not os.path.isdir(d):
        return False
    return not os.path.isfile(os.path.join(d, spec["marca"]))


def secretos_pendientes():
    """Apps con secreto propio instaladas y todavía sin configurar."""
    return [s for s in _APPS_SECRETO if _secreto_pendiente(s)]


def _python_de(dir_):
    """Python para correr el configurar.py de una app: el de su `.venv` si existe,
    si no el del proceso actual. configurar.py sólo usa la stdlib."""
    venv = os.path.join(dir_, ".venv", "Scripts", "python.exe")
    if os.path.isfile(venv):
        return venv
    import sys
    return sys.executable or "python"


def _traer_secreto(rc, spec):
    """Baja el secreto propio de una app del Drive y, si corresponde, corre su
    `configurar.py` (sin pisar lo que ya exista). Best-effort: nunca lanza.
    Devuelve True/False, o None si no aplica (no instalada o ya configurada)."""
    d = _dir_app(spec["key"])
    if not d or not os.path.isdir(d):
        return None
    if os.path.isfile(os.path.join(d, spec["marca"])):
        return None
    local = os.path.join(d, spec["local"])
    if not os.path.isfile(local):
        try:
            _rclone(rc, "copyto", f"{REMOTO}:Suite Contable/{spec['drive']}",
                    local, timeout=90)
        except Exception:                                   # noqa: BLE001
            pass
    if not os.path.isfile(local):
        return False
    if spec["configurar"]:
        try:
            subprocess.run([_python_de(d), "configurar.py"], cwd=d,
                           capture_output=True, text=True, timeout=90,
                           creationflags=_NO_WINDOW)
        except Exception:                                   # noqa: BLE001
            pass
    return os.path.isfile(os.path.join(d, spec["marca"]))


def todo_listo():
    """True si esta PC tiene TODO: el `.env` compartido y, para cada app con
    secreto propio instalada, su configuración."""
    return env_presente() and not secretos_pendientes()


def tiene_secreto_propio(key):
    """True si esa app usa un secreto propio distribuido por este módulo."""
    return any(s["key"] == key for s in _APPS_SECRETO)


def asegurar_secreto(key):
    """Al abrir una app con secreto propio: si le falta, intenta bajarlo del Drive
    con el remoto que YA exista (no dispara OAuth; si no hay remoto, queda para el
    botón "Traer credenciales"). Silencioso. True/False, o None si no aplica."""
    spec = next((s for s in _APPS_SECRETO if s["key"] == key), None)
    if spec is None or not _secreto_pendiente(spec):
        return None
    try:
        rc = _rclone_exe()
        if not os.path.isfile(rc):
            return False        # rclone aún no está en esta PC
        return _traer_secreto(rc, spec)
    except Exception:                                       # noqa: BLE001
        return False


def traer():
    """Trae el `.env` y lo distribuye. Devuelve (ok: bool, mensaje: str)."""
    try:
        rc = _ensure_rclone()
    except Exception as e:                                  # noqa: BLE001
        return False, ("No pude preparar rclone (revisá la conexión a "
                       f"internet).\n\n{e}")
    try:
        if not _bajar_env(rc):
            return False, ("No se pudo bajar el .env. Verificá que en la "
                           "pantalla de Google hayas iniciado sesión con la "
                           f"cuenta del estudio ({CUENTA_ESTUDIO}) y que "
                           "aprobaste el acceso.")
    except subprocess.TimeoutExpired:
        return False, ("Se agotó el tiempo esperando el acceso a Google. "
                       "Volvé a intentar y completá el permiso en el navegador.")
    except Exception as e:                                  # noqa: BLE001
        return False, f"Falló la descarga del .env:\n{e}"
    puestos = _distribuir_env()
    detalle = "\n".join(f"  • {p}" for p in puestos) or "  • (carpeta central)"
    # Apps con secreto propio (Cobranzas, Employee): su config vive aparte en el
    # Drive. Se bajan con el mismo remoto rclone.
    for spec in _APPS_SECRETO:
        r = _traer_secreto(rc, spec)
        nombre = next((a["nombre"] for a in config.APPS
                       if a["key"] == spec["key"]), spec["key"])
        if r is True:
            detalle += f"\n  • {nombre} (config propia)"
        elif r is False:
            detalle += (f"\n  • {nombre}: NO pude bajar su secreto "
                        f"({spec['drive']}) del Drive.")
    return True, ("Credenciales instaladas en esta PC. Ya podés abrir las "
                  "apps.\n\nQuedó en:\n" + detalle)
