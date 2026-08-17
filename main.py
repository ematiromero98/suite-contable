# -*- coding: utf-8 -*-
"""
Suite Contable — MR & Asociados.
Launcher/ERP: una ventana (Panel Oscuro) para abrir, actualizar e instalar los
programas del estudio.

Abrir con doble clic en «Suite Contable.bat» (o: pythonw main.py).
"""
import os
import re
import sys
import threading
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QMessageBox, QScrollArea, QStackedWidget, QButtonGroup,
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QTimer, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QFont, QColor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from version import VERSION

# Comparación de versiones robusta si está `packaging`; si no, fallback numérico.
try:
    from packaging.version import Version as _Version
except Exception:                                          # noqa: BLE001
    _Version = None

# Repo oficial esperado de la Suite (defensa supply-chain del auto-update).
_REPO_OFICIAL = "ematiromero98/suite-contable"

# Traída de credenciales (.env) desde el Drive del estudio. Import defensivo:
# si algo faltara, el ERP igual abre (sólo se desactiva ese botón).
try:
    import credenciales
except Exception:                                          # noqa: BLE001
    credenciales = None

# Módulo "Arquitectura" (diagramas del ERP). Import defensivo: si fallara, el
# ERP abre igual y sólo se omite esa página.
try:
    from arquitectura import PaginaArquitectura
except Exception:                                          # noqa: BLE001
    PaginaArquitectura = None

_BASE = os.path.dirname(os.path.abspath(__file__))
# Evitar que se abran consolas negras al llamar a gh/.bat en Windows.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# ==========================================================================
#  Paleta e identidad visual — Panel Oscuro (acento menta). Un solo lugar para
#  tocar el tema. Se aplica por QSS (hojas de estilo de Qt), sin dependencias
#  nuevas (importante: la Suite se auto-actualiza por git pull, sin pip).
# ==========================================================================
BG       = "#0f1218"
SIDE     = "#12161e"
PANEL    = "#171c26"
PANEL2   = "#1d2430"
SOFT     = "#1c222e"
TEXT     = "#eef2f8"
MUTED    = "#8a94a6"
BORDER   = "#242c39"
HAIR     = "#1d2530"
ACCENT   = "#2ee6a6"
ACCENT_INK = "#04120c"
ACCENT_2 = "#5cf0bd"
WARN     = "#f6b64b"
BAD      = "#f6465d"

QSS = """
Launcher { background: #0f1218; }
QWidget { color: #eef2f8; font-family: "Segoe UI", "Segoe UI Variable", sans-serif; font-size: 13px; }
QToolTip { background:#1d2430; color:#eef2f8; border:1px solid #242c39; padding:5px 7px; }

#sidebar { background:#12161e; border-right:1px solid #1d2530; }
#brandMark { background:#2ee6a6; color:#04120c; border-radius:9px; font-size:13px; font-weight:800; }
#brandName { font-size:15px; font-weight:600; color:#eef2f8; }
#brandSub  { font-size:9px; color:#8a94a6; }
#navLabel  { color:#8a94a6; font-size:9px; font-weight:700; }
QPushButton#nav { text-align:left; padding:9px 12px; border:none; border-radius:10px;
    background:transparent; color:#8a94a6; font-size:13px; font-weight:500; }
QPushButton#nav:hover   { background:#1c222e; color:#eef2f8; }
QPushButton#nav:checked { background:#12271f; color:#5cf0bd; font-weight:600; }
#userMark { background:#12271f; color:#5cf0bd; border-radius:8px; font-weight:700; font-size:12px; }
#userName { font-size:12px; font-weight:600; color:#eef2f8; }
#userHandle { font-size:10px; color:#8a94a6; }
#footVer { color:#5b6472; font-size:10px; }

#content { background:#0f1218; }
QStackedWidget { background:#0f1218; }
#scrollbody { background:transparent; }

#topbar { border-bottom:1px solid #1d2530; }
#greet    { font-size:18px; font-weight:600; color:#eef2f8; }
#greetSub { font-size:12px; color:#8a94a6; }

#kpi { background:#171c26; border:1px solid #242c39; border-radius:14px; }
#kpiLabel { color:#8a94a6; font-size:10px; font-weight:700; }
#kpiValue { color:#eef2f8; font-size:26px; font-weight:400; }
#kpiHint  { color:#8a94a6; font-size:10px; }

#secTitle { font-size:12px; font-weight:700; color:#eef2f8; }
#secCount { color:#8a94a6; font-size:12px; }

#card { background:#171c26; border:1px solid #242c39; border-radius:16px; }
#cardTitle { font-size:15px; font-weight:600; color:#eef2f8; }
#cardDesc  { color:#8a94a6; font-size:11px; }
#cardWarn  { color:#f6465d; font-size:11px; }
#cardUpd   { color:#f6b64b; font-size:11px; font-weight:600; }

QPushButton#abrir { background:#2ee6a6; color:#04120c; border:none; border-radius:10px;
    padding:9px 16px; font-size:13px; font-weight:700; }
QPushButton#abrir:hover    { background:#4fecb8; }
QPushButton#abrir:disabled { background:#232c39; color:#5b6472; }
QPushButton#ghost { background:transparent; color:#f6b64b; border:1px solid #4a3a1e;
    border-radius:10px; padding:9px 14px; font-size:12px; font-weight:700; }
QPushButton#ghost:hover    { background:#241d10; }
QPushButton#ghost:disabled { color:#5b6472; border-color:#242c39; }

#banner { background:#1d2430; border:1px solid #3a3320; border-radius:14px; }
#bannerTitle { font-size:14px; font-weight:600; color:#eef2f8; }
#bannerSub   { color:#8a94a6; font-size:12px; }
#urow { background:#171c26; border:1px solid #242c39; border-radius:12px; }
#uName { font-size:14px; font-weight:600; color:#eef2f8; }
#uJump { color:#8a94a6; font-size:11px; }
#emptyMsg { color:#8a94a6; font-size:14px; }

#setRow { background:#171c26; border:1px solid #242c39; border-radius:12px; }
#setName { font-size:13px; font-weight:600; color:#eef2f8; }
#setPath { color:#8a94a6; font-size:11px; }
QPushButton#action { background:#1c222e; color:#eef2f8; border:1px solid #242c39;
    border-radius:10px; padding:8px 14px; font-size:12px; font-weight:600; }
QPushButton#action:hover { border-color:#2ee6a6; color:#5cf0bd; }

QScrollArea { background:transparent; border:none; }
QScrollBar:vertical { background:transparent; width:10px; margin:2px; }
QScrollBar::handle:vertical { background:#2a3340; border-radius:5px; min-height:30px; }
QScrollBar::handle:vertical:hover { background:#3a4658; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:transparent; }
QScrollBar:horizontal { height:0px; }
"""


def _hex_rgba(h, pct):
    """'#rrggbb' -> 'rgba(r,g,b,PCT%)' para tintes en QSS."""
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{pct})"


# La fuente base ("Segoe UI", del QSS global) NO trae glifos de color: los emojis
# de las tarjetas salían como cuadraditos/"tofu". Los dibujamos a un QPixmap con
# la fuente de emoji de Windows ("Segoe UI Emoji"), que sí los renderiza a color.
_EMOJI_FONT = "Segoe UI Emoji"


def _emoji_pixmap(emoji, px=24):
    """Emoji a color en un QPixmap transparente (nítido en hi-DPI)."""
    dpr = 2
    pm = QPixmap(px * dpr, px * dpr)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    f = QFont(_EMOJI_FONT)
    f.setPixelSize(int(px * 0.82))
    p.setFont(f)
    p.setPen(QColor("#ffffff"))            # sólo aplica al fallback monocromo
    p.drawText(QRectF(0, 0, px, px), Qt.AlignmentFlag.AlignCenter, emoji)
    p.end()
    return pm


def _tile_emoji(emoji, lado, color, radio, emoji_px):
    """Crea el 'tile' cuadrado con el ícono de la app: fondo tintado + emoji a
    color dibujado como pixmap (no como texto, para que no dependa de la fuente
    base)."""
    tile = QLabel()
    tile.setFixedSize(lado, lado)
    tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
    tile.setStyleSheet(
        f"background:{_hex_rgba(color, '16%')};"
        f"border:1px solid {_hex_rgba(color, '26%')};"
        f"border-radius:{radio}px;")
    tile.setPixmap(_emoji_pixmap(emoji, emoji_px))
    return tile


def _leer_version(app):
    """Lee la versión de una app: soporta `__version__ = "x"` / `VERSION = "x"`
    en un .py, o un archivo VERSION con la versión en texto plano."""
    ruta = os.path.join(app["dir"], app["version_file"])
    try:
        with open(ruta, encoding="utf-8") as f:
            txt = f.read()
    except OSError:
        return None
    m = re.search(r'(?:__version__|VERSION)\s*=\s*["\']([^"\']+)["\']', txt)
    if m:
        return m.group(1)
    # Archivo VERSION plano (ej. "2.0.9").
    linea = txt.strip().splitlines()[0].strip() if txt.strip() else ""
    if re.match(r"^v?\d+(\.\d+)*$", linea):
        return linea.lstrip("vV")
    return None


def _entrada(app):
    """Primer punto de entrada existente de la app, o None."""
    for e in app["entradas"]:
        p = os.path.join(app["dir"], e)
        if os.path.isfile(p):
            return p
    return None


def _vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or ""))


def _es_mayor(latest, installed):
    """True si `latest` es una versión posterior a `installed`. Normaliza a
    longitud fija (rellenando con ceros) para que "1.2" y "1.2.0" se consideren
    iguales y no se disparen updates fantasma. Usa `packaging.version` si está
    disponible."""
    if not latest or not installed:
        return False
    if _Version is not None:
        try:
            return _Version(latest) > _Version(installed)
        except Exception:                                   # noqa: BLE001
            pass                                            # fallback numérico
    a, b = _vtuple(latest), _vtuple(installed)
    n = max(len(a), len(b))
    a += (0,) * (n - len(a))
    b += (0,) * (n - len(b))
    return a > b


def _ultima_release(repo):
    """Último release publicado en GitHub. Primero prueba el CLI `gh` (si hay un
    login personal); si no, la API con el token del runtime (así el aviso de
    "hay actualización" anda también sin `gh`). None si no se pudo."""
    if not repo:
        return None
    # 1) gh (si esta PC tiene un login personal)
    try:
        r = subprocess.run(
            ["gh", "release", "view", "--repo", repo, "--json", "tagName",
             "-q", ".tagName"],
            capture_output=True, text=True, timeout=10,
            creationflags=_NO_WINDOW)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().lstrip("vV")
    except Exception:                                   # noqa: BLE001
        pass
    # 2) API de GitHub con el token del runtime (sin gh)
    tok = _token_runtime()
    if tok:
        try:
            import json
            import urllib.request
            req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/releases/latest",
                headers={"Authorization": f"token {tok}",
                         "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                tag = json.load(resp).get("tag_name")
            if tag:
                return tag.lstrip("vV")
        except Exception:                               # noqa: BLE001
            pass
    return None


class _CredWorker(QObject):
    """Trae el `.env` en segundo plano (la parte del OAuth abre el navegador y
    bloquea, por eso no puede correr en el hilo de la interfaz)."""
    done = pyqtSignal(bool, str)

    def start(self):
        def _run():
            try:
                ok, msg = credenciales.traer()
            except Exception as e:                          # noqa: BLE001
                ok, msg = False, f"Error inesperado:\n{e}"
            self.done.emit(ok, msg)
        threading.Thread(target=_run, daemon=True).start()


class _Chequeador(QObject):
    """Chequea en segundo plano si cada app tiene una versión más nueva."""
    listo = pyqtSignal(str, str)   # (key, versión nueva o "" si está al día)

    def correr(self, apps):
        def _run():
            for a in apps:
                latest = _ultima_release(a.get("repo"))
                inst = _leer_version(a)
                if latest and inst is None:
                    # Versión instalada ilegible: igual avisamos que hay release
                    # publicado (en vez de callar y no ofrecer la actualización).
                    hay = latest
                elif _es_mayor(latest, inst):
                    hay = latest
                else:
                    hay = ""
                self.listo.emit(a["key"], hay)
        threading.Thread(target=_run, daemon=True).start()


def _abrir(app, parent):
    # Cobranzas y Employee usan su propio secreto (no el `.env` compartido). Si se
    # está abriendo una y le falta, intentamos bajarlo del Drive con el remoto ya
    # configurado (silencioso; si no hay remoto, queda para "Traer credenciales").
    if credenciales is not None and credenciales.tiene_secreto_propio(app.get("key")):
        try:
            credenciales.asegurar_secreto(app["key"])
        except Exception:                                   # noqa: BLE001
            pass
    entrada = _entrada(app)
    if not entrada:
        env = app.get("env_dir")
        sugerencia = (f"Fijá la ruta con la variable de entorno {env}."
                      if env else
                      "Fijá la ruta con la variable de entorno correspondiente.")
        QMessageBox.warning(
            parent, f"{app['nombre']} no encontrado",
            f"No encontré {app['nombre']} en:\n{app['dir']}\n\n{sugerencia}")
        return
    try:
        if entrada.lower().endswith(".bat"):
            # Sin shell=True (evita inyección vía la ruta). os.startfile lo lanza
            # como si se hiciera doble clic: el directorio de trabajo queda en la
            # carpeta del .bat (= app["dir"]), igual que antes.
            os.startfile(entrada)                          # noqa: S606 (Windows)
        else:
            exe = sys.executable or "python"
            pyw = exe.replace("python.exe", "pythonw.exe")
            exe = pyw if os.path.isfile(pyw) else exe
            subprocess.Popen([exe, entrada], cwd=app["dir"])
    except Exception as e:                              # noqa: BLE001
        QMessageBox.critical(parent, "Error",
                             f"No pude abrir {app['nombre']}:\n{e}")


def _instalar_app(app, parent):
    """Clona una app que falta usando el token del runtime (sin depender de `gh`).
    Bloquea un momento."""
    import shutil
    repo, dest = app.get("repo"), app["dir"]
    if not repo:
        return
    tok = _token_runtime()
    parent.setCursor(Qt.CursorShape.WaitCursor)
    try:
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        if tok:
            url = f"https://x-access-token:{tok}@github.com/{repo}.git"
            r = subprocess.run(["git", "clone", url, dest],
                               capture_output=True, text=True, timeout=300,
                               creationflags=_NO_WINDOW)
            # Dejar el origin SIN el token embebido (las updates lo inyectan solas).
            if r.returncode == 0:
                _git(dest, ["remote", "set-url", "origin",
                            f"https://github.com/{repo}.git"], timeout=15)
        elif shutil.which("gh") is not None:
            r = subprocess.run(["gh", "repo", "clone", repo, dest],
                               capture_output=True, text=True, timeout=300,
                               creationflags=_NO_WINDOW)
        else:
            parent.unsetCursor()
            QMessageBox.warning(
                parent, "Instalar",
                f"No hay credenciales para bajar {app['nombre']}.\n"
                "Corré el instalador del estudio (instalar_suite.ps1) en esta PC.")
            return
    except Exception as e:                              # noqa: BLE001
        parent.unsetCursor()
        QMessageBox.critical(parent, "Error",
                             f"No pude instalar {app['nombre']}:\n{e}")
        return
    parent.unsetCursor()
    if r.returncode != 0:
        QMessageBox.critical(parent, "Error",
                             f"No pude clonar {app['nombre']}:\n{(r.stderr or '')[:400]}")
        return
    QMessageBox.information(
        parent, "Instalado",
        f"{app['nombre']} se instaló en:\n{dest}\n\nReabrí la Suite para usarla.")


def _leer_token_env(dir_):
    """Lee GITHUB_TOKEN del .env de la app (RetencionesPro lo usa para el pull
    porque su remote no lleva credenciales). None si no hay."""
    try:
        with open(os.path.join(dir_, ".env"), encoding="utf-8") as f:
            for linea in f:
                if linea.strip().startswith("GITHUB_TOKEN="):
                    t = linea.split("=", 1)[1].strip().strip('"').strip("'")
                    if t and "REEMPLAZAR" not in t:
                        return t
    except OSError:
        pass
    return None


def _git(dir_, args, timeout=240):
    return subprocess.run(["git", "-C", dir_] + args, capture_output=True,
                          text=True, timeout=timeout, creationflags=_NO_WINDOW)


def _remote_oficial(dir_, repo):
    """True si el remote `origin` de `dir_` apunta al repo oficial esperado
    (`owner/repo` en github.com). Defensa supply-chain: si alguien cambió el
    remote de esta instalación a otro host/repo, un `git pull` ejecutaría código
    ajeno en el próximo arranque. Contempla URLs con o sin `.git`, credential
    helpers embebidos (`x-access-token:...@`) y formato SSH. Espeja la
    validación que ya usan los `update.bat` de las apps hijas."""
    try:
        r = _git(dir_, ["remote", "get-url", "origin"], timeout=10)
    except Exception:                                       # noqa: BLE001
        return False
    if r.returncode != 0:
        return False
    url = (r.stdout or "").strip().lower()
    owner, name = repo.lower().split("/", 1)
    return bool(url) and "github.com" in url and f"{owner}/{name}" in url


def _gh_token():
    """Token del `gh` logueado en esta PC (cubre TODOS los repos privados del
    estudio). None si `gh` no está instalado o no hay sesión. Sirve para bajar
    los repos aunque no se haya corrido `gh auth setup-git`."""
    try:
        r = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=10, creationflags=_NO_WINDOW)
        if r.returncode == 0:
            t = r.stdout.strip()
            return t or None
    except Exception:                                       # noqa: BLE001
        pass
    return None


def _token_runtime():
    """Token de SOLO-LECTURA del runtime (archivo del instalador → gh), para bajar
    y actualizar código sin depender del `gh` personal. Así el ERP se actualiza
    solo aunque esta PC no tenga `gh` logueado, y quien administre puede loguear su
    cuenta con escritura SIN que se pisen entre sí. None si no hay ninguno."""
    if credenciales is not None:
        try:
            return credenciales.token_runtime()
        except Exception:                                   # noqa: BLE001
            pass
    return _gh_token()


def _python_base():
    """Python REAL para crear venvs: el mismo intérprete que corre el ERP
    (`sys.executable`), priorizando python.exe sobre pythonw.exe. NUNCA usar
    'python' pelado: en muchas PC es el stub de la Microsoft Store, que crea
    venvs rotos y hace fallar el pip install (por eso las deps no se instalaban
    en algunas máquinas)."""
    base = sys.executable or "python"
    consola = base.replace("pythonw.exe", "python.exe")
    return consola if os.path.isfile(consola) else base


def _pip_update(dir_):
    """Instala/actualiza las dependencias de la app en su `.venv` (lo crea si
    falta). Devuelve (ok: bool, detalle: str) para poder mostrar el motivo real
    si algo falla."""
    req = os.path.join(dir_, "requirements.txt")
    if not os.path.isfile(req):
        return True, "sin requirements.txt"
    venv_py = os.path.join(dir_, ".venv", "Scripts", "python.exe")
    if not os.path.isfile(venv_py):
        # Crear el .venv con el Python real que corre el ERP (no 'python' pelado).
        try:
            cv = subprocess.run([_python_base(), "-m", "venv",
                                 os.path.join(dir_, ".venv")],
                                capture_output=True, text=True, timeout=300,
                                creationflags=_NO_WINDOW)
            if cv.returncode != 0:
                return False, ("no pude crear el entorno .venv: "
                               + (cv.stderr or cv.stdout or "").strip()[-200:])
        except Exception as e:                          # noqa: BLE001
            return False, f"no pude crear el entorno .venv: {e}"
    if not os.path.isfile(venv_py):
        return False, ("no quedó el .venv de la app; revisá que Python esté "
                       "instalado (no sólo el atajo de la Microsoft Store).")
    try:
        subprocess.run([venv_py, "-m", "pip", "install", "--upgrade", "pip"],
                       capture_output=True, text=True, timeout=300,
                       creationflags=_NO_WINDOW)
        r = subprocess.run([venv_py, "-m", "pip", "install", "-r", req],
                           capture_output=True, text=True, timeout=1200,
                           creationflags=_NO_WINDOW)
        if r.returncode == 0:
            return True, "dependencias al día"
        return False, (r.stderr or r.stdout or "").strip()[-250:]
    except subprocess.TimeoutExpired:
        return False, "se agotó el tiempo instalando dependencias (conexión lenta)"
    except Exception as e:                              # noqa: BLE001
        return False, str(e)[:200]


def _actualizar_app_core(app):
    """Actualiza una app (sin interfaz). Baja los cambios y, si la copia local
    divergió, respalda y realinea con el código oficial; después instala
    dependencias. Los DATOS no se tocan (viven en Supabase y en .env/.venv).

    Devuelve (estado, detalle):
      'ok'       — quedó al día
      'aviso'    — código al día pero deps con problemas
      'saltada'  — no está instalada (no hay repo git)
      'error'    — falló (detalle = motivo)"""
    dir_ = app["dir"]
    if not os.path.isdir(os.path.join(dir_, ".git")):
        return "saltada", "no está instalada en esta PC"
    try:
        repo = app.get("repo")
        # 1) git normal: usa el credential helper si está configurado
        #    (`gh auth setup-git`). Sirve para todos los repos si está bien.
        f = _git(dir_, ["fetch"])
        target = "@{u}"                                  # rama remota trackeada
        # 2) Si falla, usar el token del RUNTIME (archivo del instalador o gh).
        #    Cubre los repos privados sin depender del `gh` personal.
        if f.returncode != 0 and repo:
            ght = _token_runtime()
            if ght:
                f = _git(dir_, ["fetch",
                                f"https://x-access-token:{ght}@github.com/{repo}.git"])
                target = "FETCH_HEAD"
        # 3) Último recurso: token del .env (rescata RetencionesPro, cuyo origin
        #    es de sólo lectura). Ese token sólo cubre RetencionesPro.
        if f.returncode != 0 and repo:
            envtok = _leer_token_env(dir_)
            if envtok:
                f = _git(dir_, ["fetch",
                                f"https://{envtok}@github.com/{repo}.git"])
                target = "FETCH_HEAD"
        if f.returncode != 0:
            return "error", (f.stderr or "").strip()[:300]

        # Caso normal: avanzar en línea recta.
        if _git(dir_, ["merge", "--ff-only", target]).returncode != 0:
            # Divergió: respaldar (rama backup + stash) y realinear al oficial.
            import time
            _git(dir_, ["branch", f"backup-local-{int(time.time())}"])
            _git(dir_, ["stash", "push", "-u", "-m", "respaldo-antes-de-actualizar"])
            rs = _git(dir_, ["reset", "--hard", target])
            if rs.returncode != 0:
                return "error", (rs.stderr or "").strip()[:300]

        deps_ok, deps_detalle = _pip_update(dir_)
    except Exception as e:                              # noqa: BLE001
        return "error", str(e)[:300]
    if deps_ok:
        return "ok", "al día"
    return "aviso", "código al día, pero fallaron las dependencias:\n" + deps_detalle


class _UpdateAllWorker(QObject):
    """Actualiza TODAS las apps instaladas en segundo plano (los pull/pip
    bloquean, no pueden correr en el hilo de la interfaz)."""
    progreso = pyqtSignal(str)          # nombre de la app que se está tocando
    listo = pyqtSignal(list)            # [(key, nombre, estado, detalle), ...]

    def start(self, apps):
        def _run():
            resultados = []
            for a in apps:
                self.progreso.emit(a["nombre"])
                estado, detalle = _actualizar_app_core(a)
                resultados.append((a["key"], a["nombre"], estado, detalle))
            self.listo.emit(resultados)
        threading.Thread(target=_run, daemon=True).start()


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Suite Contable — MR & Asociados")
        self.setMinimumSize(900, 600)
        self.resize(1000, 680)
        self._cards = {}
        self._pendientes = {}   # key -> versión nueva disponible (apps instaladas)
        self._kpi = {}          # key -> QLabel del valor (para refrescar)
        self._nav_buttons = []
        ico = os.path.join(_BASE, "assets", "suite.ico")
        if os.path.isfile(ico):
            self.setWindowIcon(QIcon(ico))
        self._build()
        # Auto-actualizar la propia Suite (git pull) en segundo plano, para que
        # el ERP quede siempre al día en cualquier PC. Best-effort.
        threading.Thread(target=self._auto_update_suite, daemon=True).start()
        # Chequear actualizaciones de las apps y avisar en cada tarjeta.
        self._chequeador = _Chequeador()
        self._chequeador.listo.connect(self._on_update)
        self._chequeador.correr(config.APPS)
        # Si esta PC no tiene el .env, ofrecer traerlo apenas abre la ventana.
        if credenciales is not None and not credenciales.todo_listo():
            QTimer.singleShot(700, lambda: self._traer_credenciales(auto=True))

    # ---------------------------------------------------------------- construcción
    def _build(self):
        self.setStyleSheet(QSS)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())

        right = QWidget()
        right.setObjectName("content")
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)
        rv.addWidget(self._build_topbar())
        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_panel())      # 0
        self._stack.addWidget(self._page_updates())    # 1
        self._stack.addWidget(self._page_settings())   # 2
        self._stack.addWidget(self._page_arquitectura())  # 3
        self._stack.currentChanged.connect(self._on_page_change)
        rv.addWidget(self._stack, stretch=1)
        root.addWidget(right, stretch=1)

        # Ahora que existen los widgets, refrescar estados iniciales.
        self._refrescar_boton_todo()
        self._refrescar_boton_cred()
        self._refrescar_kpis()
        self._nav_buttons[0].setChecked(True)
        self._stack.setCurrentIndex(0)

    def _build_sidebar(self):
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(230)
        v = QVBoxLayout(side)
        v.setContentsMargins(15, 20, 15, 15)
        v.setSpacing(4)

        # Marca
        brand = QHBoxLayout()
        brand.setSpacing(11)
        mark = QLabel("MR")
        mark.setObjectName("brandMark")
        mark.setFixedSize(34, 34)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.addWidget(mark)
        bc = QVBoxLayout()
        bc.setSpacing(1)
        bn = QLabel("Suite Contable")
        bn.setObjectName("brandName")
        bs = QLabel("ESTUDIO")
        bs.setObjectName("brandSub")
        bc.addWidget(bn)
        bc.addWidget(bs)
        brand.addLayout(bc)
        brand.addStretch()
        v.addLayout(brand)
        v.addSpacing(14)

        # Navegación
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        lbl_g = QLabel("GENERAL")
        lbl_g.setObjectName("navLabel")
        v.addWidget(lbl_g)
        self._nav_panel = self._nav_item("🗂   Panel", 0)
        v.addWidget(self._nav_panel)
        self._nav_upd = self._nav_item("🔄   Actualizaciones", 1)
        v.addWidget(self._nav_upd)
        self._nav_arq = self._nav_item("🗺   Arquitectura", 3)
        v.addWidget(self._nav_arq)
        v.addSpacing(8)
        lbl_s = QLabel("SISTEMA")
        lbl_s.setObjectName("navLabel")
        v.addWidget(lbl_s)
        v.addWidget(self._nav_item("⚙   Ajustes", 2))

        v.addStretch()

        # Usuario + versión
        user = QHBoxLayout()
        user.setSpacing(10)
        um = QLabel("M")
        um.setObjectName("userMark")
        um.setFixedSize(30, 30)
        um.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user.addWidget(um)
        uc = QVBoxLayout()
        uc.setSpacing(0)
        un = QLabel("Matías R.")
        un.setObjectName("userName")
        uh = QLabel("ematiromero98")
        uh.setObjectName("userHandle")
        uc.addWidget(un)
        uc.addWidget(uh)
        user.addLayout(uc)
        user.addStretch()
        v.addLayout(user)
        pie = QLabel(f"v{VERSION}")
        pie.setObjectName("footVer")
        pie.setAlignment(Qt.AlignmentFlag.AlignRight)
        v.addWidget(pie)
        return side

    def _nav_item(self, texto, index):
        b = QPushButton(texto)
        b.setObjectName("nav")
        b.setCheckable(True)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(lambda _, i=index: self._stack.setCurrentIndex(i))
        self._nav_group.addButton(b, index)
        self._nav_buttons.append(b)
        return b

    def _build_topbar(self):
        top = QWidget()
        top.setObjectName("topbar")
        h = QHBoxLayout(top)
        h.setContentsMargins(24, 18, 24, 18)
        h.setSpacing(14)
        col = QVBoxLayout()
        col.setSpacing(2)
        g = QLabel("Buen día, Matías")
        g.setObjectName("greet")
        col.addWidget(g)
        self._greet_sub = QLabel("Cargando aplicaciones…")
        self._greet_sub.setObjectName("greetSub")
        col.addWidget(self._greet_sub)
        h.addLayout(col)
        h.addStretch()

        self._btn_upd_all = QPushButton("⟳ Actualizar todo")
        self._btn_upd_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_upd_all.setToolTip(
            "Baja la última versión de todos los programas instalados en esta "
            "PC y reinstala dependencias. Los datos no se tocan.")
        self._btn_upd_all.clicked.connect(self._actualizar_todo)
        h.addWidget(self._btn_upd_all)

        self._btn_cred = QPushButton("🔑 Traer credenciales")
        self._btn_cred.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_cred.clicked.connect(lambda: self._traer_credenciales(auto=False))
        h.addWidget(self._btn_cred)
        return top

    def _kpi_card(self, label, key, hint=""):
        f = QFrame()
        f.setObjectName("kpi")
        v = QVBoxLayout(f)
        v.setContentsMargins(17, 15, 17, 15)
        v.setSpacing(4)
        lb = QLabel(label.upper())
        lb.setObjectName("kpiLabel")
        v.addWidget(lb)
        val = QLabel("—")
        val.setObjectName("kpiValue")
        v.addWidget(val)
        self._kpi[key] = val
        if hint:
            ht = QLabel(hint)
            ht.setObjectName("kpiHint")
            v.addWidget(ht)
        return f

    def _page_panel(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 22, 24, 18)
        v.setSpacing(20)

        # KPIs
        row = QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(self._kpi_card("Aplicaciones", "total", "en la suite"))
        row.addWidget(self._kpi_card("Instaladas", "inst", "en esta PC"))
        row.addWidget(self._kpi_card("Actualizaciones", "pend", "pendientes"))
        row.addWidget(self._kpi_card("Al día", "ok", "última versión"))
        v.addLayout(row)

        # Sección
        sh = QHBoxLayout()
        st = QLabel("APLICACIONES")
        st.setObjectName("secTitle")
        sh.addWidget(st)
        sh.addStretch()
        sc = QLabel(f"{len(config.APPS)} en total")
        sc.setObjectName("secCount")
        sh.addWidget(sc)
        v.addLayout(sh)

        # Grilla de tarjetas (2 columnas) con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cont = QWidget()
        cont.setObjectName("scrollbody")
        grid = QGridLayout(cont)
        grid.setContentsMargins(0, 0, 8, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        for i, app in enumerate(config.APPS):
            grid.addWidget(self._tarjeta(app), i // 2, i % 2)
        grid.setRowStretch((len(config.APPS) + 1) // 2, 1)
        scroll.setWidget(cont)
        v.addWidget(scroll, stretch=1)
        return page

    def _set_pill(self, pill, kind, text):
        colores = {"ok": (ACCENT, _hex_rgba(ACCENT, "13%")),
                   "up": (WARN, _hex_rgba(WARN, "15%")),
                   "bad": (BAD, _hex_rgba(BAD, "14%"))}
        c, bg = colores[kind]
        pill.setText(text)
        pill.setStyleSheet(
            f"color:{c}; background:{bg}; border-radius:9px; padding:3px 9px;"
            "font-size:10px; font-weight:700;")

    def _tarjeta(self, app):
        card = QFrame()
        card.setObjectName("card")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(13)

        # Fila 1: ícono + nombre/desc + pill
        r1 = QHBoxLayout()
        r1.setSpacing(12)
        tile = _tile_emoji(app["emoji"], 44, app["color"], 13, 24)
        r1.addWidget(tile, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(3)
        ver = _leer_version(app)
        nombre = QLabel(app["nombre"] + (f"   v{ver}" if ver else ""))
        nombre.setObjectName("cardTitle")
        col.addWidget(nombre)
        desc = QLabel(app["desc"])
        desc.setObjectName("cardDesc")
        desc.setWordWrap(True)
        col.addWidget(desc)
        falta = not os.path.isdir(app["dir"])
        if falta:
            warn = QLabel("No encontrada en " + app["dir"])
            warn.setObjectName("cardWarn")
            warn.setWordWrap(True)
            col.addWidget(warn)
        lbl_update = QLabel("")
        lbl_update.setObjectName("cardUpd")
        lbl_update.setWordWrap(True)
        lbl_update.setVisible(False)
        col.addWidget(lbl_update)
        r1.addLayout(col, stretch=1)

        pill = QLabel()
        if falta:
            self._set_pill(pill, "bad", "No instalada")
        else:
            self._set_pill(pill, "ok", "Al día")
        r1.addWidget(pill, 0, Qt.AlignmentFlag.AlignTop)
        outer.addLayout(r1)

        # Fila 2: acciones
        r2 = QHBoxLayout()
        r2.setSpacing(10)
        btn = QPushButton("▶  Abrir")
        btn.setObjectName("abrir")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda _, a=app: _abrir(a, self))
        btn.setEnabled(not falta)
        r2.addWidget(btn, stretch=1)

        if falta:
            btn_inst = QPushButton("⬇  Instalar")
            btn_inst.setObjectName("ghost")
            btn_inst.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_inst.clicked.connect(lambda _, a=app: _instalar_app(a, self))
            r2.addWidget(btn_inst)

        # Botón de actualizar SÓLO esta app. Oculto hasta detectar versión nueva.
        btn_upd = QPushButton("⟳  Actualizar")
        btn_upd.setObjectName("ghost")
        btn_upd.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_upd.setVisible(False)
        btn_upd.clicked.connect(lambda _, a=app: self._actualizar_uno(a))
        r2.addWidget(btn_upd)
        outer.addLayout(r2)

        self._cards[app["key"]] = {"lbl": lbl_update, "nombre": nombre,
                                   "btn": btn_upd, "app": app, "pill": pill}
        return card

    # ---------------------------------------------------------------- pág. updates
    def _page_updates(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 22, 24, 18)
        v.setSpacing(16)
        st = QLabel("ACTUALIZACIONES")
        st.setObjectName("secTitle")
        v.addWidget(st)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cont = QWidget()
        cont.setObjectName("scrollbody")
        self._upd_layout = QVBoxLayout(cont)
        self._upd_layout.setContentsMargins(0, 0, 8, 0)
        self._upd_layout.setSpacing(10)
        scroll.setWidget(cont)
        v.addWidget(scroll, stretch=1)
        return page

    def _clear_layout(self, lay):
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _rebuild_updates_page(self):
        self._clear_layout(self._upd_layout)
        pend = [a for a in config.APPS if a["key"] in self._pendientes]
        if not pend:
            msg = QLabel("✓  Todo al día. No hay actualizaciones pendientes.")
            msg.setObjectName("emptyMsg")
            self._upd_layout.addWidget(msg)
            self._upd_layout.addStretch()
            return

        banner = QFrame()
        banner.setObjectName("banner")
        bh = QHBoxLayout(banner)
        bh.setContentsMargins(18, 16, 18, 16)
        bh.setSpacing(14)
        bc = QVBoxLayout()
        bc.setSpacing(2)
        bt = QLabel(f"{len(pend)} actualización(es) disponible(s)")
        bt.setObjectName("bannerTitle")
        bs = QLabel("Baja el código, respalda si hace falta y actualiza "
                    "dependencias. Tus datos no se tocan.")
        bs.setObjectName("bannerSub")
        bs.setWordWrap(True)
        bc.addWidget(bt)
        bc.addWidget(bs)
        bh.addLayout(bc, stretch=1)
        bbtn = QPushButton("⟳  Actualizar todo")
        bbtn.setObjectName("abrir")
        bbtn.setCursor(Qt.CursorShape.PointingHandCursor)
        bbtn.clicked.connect(self._actualizar_todo)
        bh.addWidget(bbtn, 0, Qt.AlignmentFlag.AlignVCenter)
        self._upd_layout.addWidget(banner)

        for app in pend:
            row = QFrame()
            row.setObjectName("urow")
            rh = QHBoxLayout(row)
            rh.setContentsMargins(14, 12, 14, 12)
            rh.setSpacing(13)
            tile = _tile_emoji(app["emoji"], 40, app["color"], 11, 22)
            rh.addWidget(tile)
            col = QVBoxLayout()
            col.setSpacing(2)
            nm = QLabel(app["nombre"])
            nm.setObjectName("uName")
            col.addWidget(nm)
            inst = _leer_version(app) or "—"
            jump = QLabel(f"v{inst}  →  v{self._pendientes[app['key']]}")
            jump.setObjectName("uJump")
            col.addWidget(jump)
            rh.addLayout(col, stretch=1)
            b = QPushButton("⟳  Actualizar")
            b.setObjectName("ghost")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _, a=app: self._actualizar_uno(a))
            rh.addWidget(b)
            self._upd_layout.addWidget(row)
        self._upd_layout.addStretch()

    def _on_page_change(self, idx):
        if idx == 1:
            self._rebuild_updates_page()

    # ------------------------------------------------------------ pág. arquitectura
    def _page_arquitectura(self):
        """Página con el diagrama de arquitectura del ERP y de cada app."""
        if PaginaArquitectura is None:
            ph = QWidget()
            v = QVBoxLayout(ph)
            v.setContentsMargins(24, 22, 24, 18)
            lbl = QLabel("El módulo de arquitectura no está disponible en esta versión.")
            lbl.setStyleSheet("color:#8a94a6; font-size:13px;")
            v.addWidget(lbl)
            v.addStretch()
            return ph
        return PaginaArquitectura(self)

    # ---------------------------------------------------------------- pág. ajustes
    def _page_settings(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 22, 24, 18)
        v.setSpacing(12)
        st = QLabel("AJUSTES")
        st.setObjectName("secTitle")
        v.addWidget(st)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cont = QWidget()
        cont.setObjectName("scrollbody")
        cv = QVBoxLayout(cont)
        cv.setContentsMargins(0, 0, 8, 0)
        cv.setSpacing(10)
        for app in config.APPS:
            row = QFrame()
            row.setObjectName("setRow")
            rh = QHBoxLayout(row)
            rh.setContentsMargins(15, 12, 15, 12)
            rh.setSpacing(12)
            col = QVBoxLayout()
            col.setSpacing(2)
            nm = QLabel(app["nombre"])
            nm.setObjectName("setName")
            col.addWidget(nm)
            pt = QLabel(app["dir"])
            pt.setObjectName("setPath")
            pt.setWordWrap(True)
            col.addWidget(pt)
            rh.addLayout(col, stretch=1)
            existe = os.path.isdir(app["dir"])
            estado = QLabel("● Encontrada" if existe else "● No encontrada")
            estado.setStyleSheet(
                f"color:{ACCENT if existe else BAD}; font-size:11px; font-weight:700;")
            rh.addWidget(estado, 0, Qt.AlignmentFlag.AlignVCenter)
            cv.addWidget(row)
        cv.addStretch()
        scroll.setWidget(cont)
        v.addWidget(scroll, stretch=1)

        fila = QHBoxLayout()
        btn = QPushButton("⟳  Chequear de nuevo")
        btn.setObjectName("action")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._chequeador.correr(config.APPS))
        fila.addWidget(btn)
        fila.addStretch()
        info = QLabel(f"Suite Contable v{VERSION}")
        info.setObjectName("footVer")
        fila.addWidget(info)
        v.addLayout(fila)
        return page

    # ---------------------------------------------------------------- refrescos
    def _refrescar_kpis(self):
        total = len(config.APPS)
        inst = sum(1 for a in config.APPS if os.path.isdir(a["dir"]))
        pend = len(self._pendientes)
        al_dia = max(0, inst - pend)
        if "total" in self._kpi:
            self._kpi["total"].setText(str(total))
            self._kpi["inst"].setText(str(inst))
            self._kpi["pend"].setText(str(pend))
            self._kpi["ok"].setText(str(al_dia))
        if hasattr(self, "_greet_sub"):
            if pend:
                self._greet_sub.setText(
                    f"{total} aplicaciones · {pend} con actualización pendiente")
            else:
                self._greet_sub.setText(f"{total} aplicaciones · todo al día")

    def _refrescar_boton_cred(self):
        """Estilo del botón según si las credenciales ya están en esta PC:
        apagado/discreto cuando ya están, llamativo (ámbar) cuando faltan."""
        if credenciales is None:
            self._btn_cred.setEnabled(False)
            self._btn_cred.setStyleSheet(
                "QPushButton { background:#1c222e; color:#5b6472;"
                "border:1px solid #242c39; border-radius:10px;"
                "padding:8px 14px; font-size:12px; }")
            return
        if credenciales.todo_listo():
            self._btn_cred.setToolTip(
                "Las credenciales ya están en esta PC. Tocá sólo si querés "
                "volver a bajarlas del Drive.")
            self._btn_cred.setStyleSheet(
                "QPushButton { background:#1c222e; color:#8a94a6;"
                "border:1px solid #242c39; border-radius:10px;"
                "padding:8px 14px; font-size:12px; }"
                "QPushButton:hover { background:#232c39; color:#eef2f8; }")
        else:
            self._btn_cred.setToolTip(
                "Baja el archivo .env (credenciales) desde el Google Drive "
                "del estudio a esta PC. Pide acceso a Google una sola vez.")
            self._btn_cred.setStyleSheet(
                "QPushButton { background:#2a2410; color:#f6b64b;"
                "border:1px solid #4a3a1e; border-radius:10px;"
                "padding:8px 14px; font-size:12px; font-weight:700; }"
                "QPushButton:hover { background:#332b12; }")

    def _traer_credenciales(self, auto=False):
        """Ofrece/ejecuta la traída del `.env` desde el Drive del estudio."""
        if credenciales is None:
            return
        cuenta = credenciales.CUENTA_ESTUDIO
        if auto:
            texto = ("Esta PC no tiene el archivo de credenciales (.env), por "
                     "eso las apps no abren.\n\n¿Traerlas ahora desde Google "
                     "Drive?\n\nSe va a abrir el navegador: iniciá sesión con "
                     f"la cuenta del estudio\n{cuenta}\ny tocá \"Permitir\".")
            titulo = "Faltan las credenciales"
        else:
            texto = ("Se va a traer el archivo .env desde el Google Drive del "
                     "estudio.\n\nSe abrirá el navegador: iniciá sesión con la "
                     f"cuenta del estudio\n{cuenta}\ny tocá \"Permitir\".\n\n"
                     "¿Continuar?")
            titulo = "Traer credenciales"
        r = QMessageBox.question(
            self, titulo, texto,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r != QMessageBox.StandardButton.Yes:
            return
        self._btn_cred.setEnabled(False)
        self._btn_cred.setText("Trayendo…")
        self.setCursor(Qt.CursorShape.WaitCursor)
        self._cred_worker = _CredWorker()
        self._cred_worker.done.connect(self._cred_done)
        self._cred_worker.start()

    def _cred_done(self, ok, msg):
        self.unsetCursor()
        self._btn_cred.setEnabled(True)
        self._btn_cred.setText("🔑 Traer credenciales")
        self._refrescar_boton_cred()
        if ok:
            QMessageBox.information(self, "Listo", msg)
        else:
            QMessageBox.warning(self, "No se pudo", msg)

    def _refrescar_boton_todo(self):
        """Prende «Actualizar todo» sólo si hay actualizaciones pendientes; si no,
        queda apagado. Muestra cuántas hay, y actualiza el contador del menú."""
        n = len(self._pendientes)
        self._btn_upd_all.setEnabled(n > 0)
        if n > 0:
            self._btn_upd_all.setText(f"⟳ Actualizar todo ({n})")
            self._btn_upd_all.setToolTip(
                f"Hay {n} programa(s) con versión nueva. Los actualiza y "
                "reinstala dependencias. Los datos no se tocan.")
        else:
            self._btn_upd_all.setText("⟳ Actualizar todo")
            self._btn_upd_all.setToolTip("No hay actualizaciones pendientes.")
        self._btn_upd_all.setStyleSheet(
            "QPushButton { background:#2ee6a6; color:#04120c; border:none;"
            "border-radius:10px; padding:8px 14px; font-size:12px;"
            "font-weight:700; } QPushButton:hover { background:#4fecb8; }"
            "QPushButton:disabled { background:#1c222e; color:#5b6472; }")
        if hasattr(self, "_nav_upd"):
            self._nav_upd.setText(
                "🔄   Actualizaciones" + (f"   ({n})" if n > 0 else ""))

    def _actualizar_todo(self):
        """Actualiza las apps que tienen una versión nueva pendiente."""
        apps = [a for a in config.APPS if a["key"] in self._pendientes
                and os.path.isdir(os.path.join(a["dir"], ".git"))]
        if apps:
            self._iniciar_update(apps)

    def _actualizar_uno(self, app):
        """Actualiza una sola app (botón de su tarjeta)."""
        if os.path.isdir(os.path.join(app["dir"], ".git")):
            self._iniciar_update([app])

    def _iniciar_update(self, apps):
        self._btn_upd_all.setEnabled(False)
        self._btn_upd_all.setText("Actualizando…")
        for c in self._cards.values():
            c["btn"].setEnabled(False)
        self.setCursor(Qt.CursorShape.WaitCursor)
        self._upd_worker = _UpdateAllWorker()
        self._upd_worker.progreso.connect(self._update_all_progreso)
        self._upd_worker.listo.connect(self._update_all_done)
        self._upd_worker.start(apps)

    def _update_all_progreso(self, nombre):
        self._btn_upd_all.setText(f"Actualizando {nombre}…")

    def _update_all_done(self, resultados):
        self.unsetCursor()
        for key, _nombre, estado, _detalle in resultados:
            card = self._cards.get(key)
            if not card:
                continue
            app = card["app"]
            ver = _leer_version(app)
            card["nombre"].setText(app["nombre"] + (f"   v{ver}" if ver else ""))
            if estado in ("ok", "aviso"):
                # Quedó al día: sale de pendientes, se oculta su aviso/botón y la
                # pill vuelve a "Al día".
                self._pendientes.pop(key, None)
                card["lbl"].setVisible(False)
                card["btn"].setVisible(False)
                self._set_pill(card["pill"], "ok", "Al día")
            # Si hubo error, la app sigue pendiente (aviso y botón quedan).
        for c in self._cards.values():
            c["btn"].setEnabled(True)
        self._refrescar_boton_todo()
        self._refrescar_kpis()
        if self._stack.currentIndex() == 1:
            self._rebuild_updates_page()
        iconos = {"ok": "✅", "aviso": "⚠️", "saltada": "•", "error": "❌"}
        cuerpo = "\n".join(f"{iconos.get(e, '•')} {n}: {d}"
                           for _k, n, e, d in resultados)
        if any(e == "error" for _k, _n, e, _d in resultados):
            QMessageBox.warning(self, "Actualizar", "Resultado:\n\n" + cuerpo)
        elif any(e == "aviso" for _k, _n, e, _d in resultados):
            QMessageBox.warning(self, "Actualizar",
                                "Actualizado, con algún aviso:\n\n" + cuerpo)
        else:
            QMessageBox.information(self, "Actualizar",
                                    "Listo, quedó al día:\n\n" + cuerpo)

    @staticmethod
    def _auto_update_suite():
        """Deja el propio ERP al día en cada arranque. Si la copia local divergió
        (por eso a veces quedaba trabada sin actualizar), se realinea al oficial
        por la fuerza — es seguro: el ERP es sólo código, sin datos. El cambio
        recién se ve al reabrir la ventana."""
        try:
            if not os.path.isdir(os.path.join(_BASE, ".git")):
                return
            # Validar que `origin` sea el repo oficial ANTES de traer/aplicar
            # nada: sin este chequeo, un remote adulterado haría que el fetch +
            # `reset --hard` de abajo ejecute código ajeno al reabrir el ERP.
            if not _remote_oficial(_BASE, _REPO_OFICIAL):
                print("[Suite] auto-update OMITIDO: el remote 'origin' no apunta "
                      f"al repo oficial ({_REPO_OFICIAL}). No se actualiza por "
                      "seguridad.", file=sys.stderr)
                return
            # Fetch en 3 niveles, igual que las apps hijas, para que ande también
            # si el repo del ERP pasa a PRIVADO:
            #  1) git normal (credential helper, si se corrió `gh auth setup-git`)
            #  2) token del `gh` logueado (cubre los repos privados del estudio)
            #  3) token del `.env` (GITHUB_TOKEN), último recurso
            f = _git(_BASE, ["fetch"], timeout=60)
            target = "@{u}"
            if f.returncode != 0:
                ght = _token_runtime()
                if ght:
                    f = _git(_BASE, ["fetch",
                                     f"https://x-access-token:{ght}@github.com/"
                                     f"{_REPO_OFICIAL}.git"], timeout=60)
                    target = "FETCH_HEAD"
            if f.returncode != 0:
                envtok = _leer_token_env(_BASE)
                if envtok:
                    f = _git(_BASE, ["fetch",
                                     f"https://{envtok}@github.com/{_REPO_OFICIAL}.git"],
                             timeout=60)
                    target = "FETCH_HEAD"
            if f.returncode != 0:
                return
            if _git(_BASE, ["merge", "--ff-only", target], timeout=30).returncode != 0:
                _git(_BASE, ["reset", "--hard", target], timeout=30)
        except Exception:                              # noqa: BLE001
            pass

    def _on_update(self, key, latest):
        """Llega desde el chequeo en segundo plano: `latest` = versión nueva o ''."""
        card = self._cards.get(key)
        if card and latest:
            app = card["app"]
            card["lbl"].setText(f"Nueva versión disponible · v{latest}")
            card["lbl"].setVisible(True)
            self._set_pill(card["pill"], "up", "Actualizar")
            # Sólo se puede actualizar si está instalada (hay repo git). Si no, se
            # usa «⬇ Instalar». Marcar pendiente y mostrar su botón.
            if os.path.isdir(os.path.join(app["dir"], ".git")):
                self._pendientes[key] = latest
                card["btn"].setVisible(True)
        self._refrescar_boton_todo()
        self._refrescar_kpis()
        if self._stack.currentIndex() == 1:
            self._rebuild_updates_page()


def main():
    # En Windows, para que la barra de tareas muestre el ícono propio (y no el
    # de python/pythonw) hay que declarar un AppUserModelID antes de crear la
    # ventana.
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "mrasoc.suitecontable")
        except Exception:                              # noqa: BLE001
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ico = os.path.join(_BASE, "assets", "suite.ico")
    if os.path.isfile(ico):
        app.setWindowIcon(QIcon(ico))
    w = Launcher()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
