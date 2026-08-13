# -*- coding: utf-8 -*-
"""
Suite Contable — MR & Asociados.
Launcher: una ventana para abrir DDJJ Impuestos o RetencionesPro.

Abrir con doble clic en «Suite Contable.bat» (o: pythonw main.py).
"""
import os
import re
import sys
import threading
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QScrollArea,
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon

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

_BASE = os.path.dirname(os.path.abspath(__file__))
# Evitar que se abran consolas negras al llamar a gh/.bat en Windows.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


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
    """Último release publicado en GitHub, vía el CLI `gh` (ya autenticado en la
    máquina; sirve para repos privados sin manejar tokens). None si no se pudo."""
    if not repo:
        return None
    try:
        r = subprocess.run(
            ["gh", "release", "view", "--repo", repo, "--json", "tagName",
             "-q", ".tagName"],
            capture_output=True, text=True, timeout=10,
            creationflags=_NO_WINDOW)
        if r.returncode == 0:
            return r.stdout.strip().lstrip("vV")
    except Exception:                                   # noqa: BLE001
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
    """Clona una app que falta (vía gh, ya autenticado). Bloquea un momento."""
    import shutil
    repo, dest = app.get("repo"), app["dir"]
    if not repo:
        return
    if shutil.which("gh") is None:
        QMessageBox.warning(
            parent, "Instalar",
            f"No encontré 'gh' para instalar {app['nombre']}.\n"
            f"Instalalo una vez a mano:\n  gh repo clone {repo} \"{dest}\"")
        return
    parent.setCursor(Qt.CursorShape.WaitCursor)
    try:
        r = subprocess.run(["gh", "repo", "clone", repo, dest],
                           capture_output=True, text=True, timeout=300,
                           creationflags=_NO_WINDOW)
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
        # 2) Si falla, usar el token del `gh` logueado (cubre TODOS los repos
        #    privados del estudio) aunque no se haya corrido setup-git. Esto
        #    evita el 403 típico en una PC recién configurada.
        if f.returncode != 0 and repo:
            ght = _gh_token()
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
    listo = pyqtSignal(list)            # [(nombre, estado, detalle), ...]

    def start(self, apps):
        def _run():
            resultados = []
            for a in apps:
                self.progreso.emit(a["nombre"])
                estado, detalle = _actualizar_app_core(a)
                resultados.append((a["nombre"], estado, detalle))
            self.listo.emit(resultados)
        threading.Thread(target=_run, daemon=True).start()


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Suite Contable — MR & Asociados")
        self.setMinimumSize(580, 640)
        self._cards = {}
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
        if credenciales is not None and not credenciales.env_presente():
            QTimer.singleShot(700, lambda: self._traer_credenciales(auto=True))

    def _refrescar_boton_cred(self):
        """Estilo del botón según si las credenciales ya están en esta PC:
        apagado/gris cuando ya están, llamativo (ámbar) cuando faltan."""
        if credenciales is None:
            self._btn_cred.setEnabled(False)
            self._btn_cred.setStyleSheet(
                "QPushButton { background:#F1F3F5; color:#B0B8C1;"
                "border:1px solid #E5E9F0; border-radius:8px;"
                "padding:7px 12px; font-size:12px; }")
            return
        if credenciales.env_presente():
            # Ya están: sin color, discreto (pero clickeable por si querés
            # volver a bajarlas).
            self._btn_cred.setToolTip(
                "Las credenciales ya están en esta PC. Tocá sólo si querés "
                "volver a bajarlas del Drive.")
            self._btn_cred.setStyleSheet(
                "QPushButton { background:#F1F3F5; color:#9AA5B1;"
                "border:1px solid #E5E9F0; border-radius:8px;"
                "padding:7px 12px; font-size:12px; }"
                "QPushButton:hover { background:#E9ECEF; color:#6B7580; }")
        else:
            # Faltan: llamativo para que se note que hay que tocarlo.
            self._btn_cred.setToolTip(
                "Baja el archivo .env (credenciales) desde el Google Drive "
                "del estudio a esta PC. Pide acceso a Google una sola vez.")
            self._btn_cred.setStyleSheet(
                "QPushButton { background:#F2C14E; color:#5A3E00;"
                "border:none; border-radius:8px; padding:7px 12px;"
                "font-size:12px; font-weight:bold; }"
                "QPushButton:hover { background:#E6B33E; }")

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

    def _actualizar_todo(self):
        """Actualiza de una sola vez todos los programas instalados en la PC."""
        apps = [a for a in config.APPS
                if os.path.isdir(os.path.join(a["dir"], ".git"))]
        if not apps:
            QMessageBox.information(
                self, "Actualizar todo",
                "No hay programas instalados para actualizar en esta PC.\n\n"
                "Instalá los que falten con su botón «⬇ Instalar».")
            return
        self._btn_upd_all.setEnabled(False)
        self._btn_upd_all.setText("Actualizando…")
        self.setCursor(Qt.CursorShape.WaitCursor)
        self._upd_worker = _UpdateAllWorker()
        self._upd_worker.progreso.connect(self._update_all_progreso)
        self._upd_worker.listo.connect(self._update_all_done)
        self._upd_worker.start(apps)

    def _update_all_progreso(self, nombre):
        self._btn_upd_all.setText(f"Actualizando {nombre}…")

    def _update_all_done(self, resultados):
        self.unsetCursor()
        self._btn_upd_all.setEnabled(True)
        self._btn_upd_all.setText("⟳ Actualizar todo")
        # Refrescar la versión que muestra cada tarjeta y limpiar los avisos.
        for card in self._cards.values():
            app = card["app"]
            ver = _leer_version(app)
            card["nombre"].setText(app["nombre"] + (f"   v{ver}" if ver else ""))
            card["lbl"].setVisible(False)
        iconos = {"ok": "✅", "aviso": "⚠️", "saltada": "•", "error": "❌"}
        cuerpo = "\n".join(f"{iconos.get(e, '•')} {n}: {d}"
                           for n, e, d in resultados)
        if any(e == "error" for _n, e, _d in resultados):
            QMessageBox.warning(self, "Actualizar todo", "Resultado:\n\n" + cuerpo)
        elif any(e == "aviso" for _n, e, _d in resultados):
            QMessageBox.warning(self, "Actualizar todo",
                                "Actualizado, con algún aviso:\n\n" + cuerpo)
        else:
            QMessageBox.information(self, "Actualizar todo",
                                    "Todo quedó al día:\n\n" + cuerpo)

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
            if _git(_BASE, ["fetch"], timeout=60).returncode != 0:
                return
            if _git(_BASE, ["merge", "--ff-only", "@{u}"], timeout=30).returncode != 0:
                _git(_BASE, ["reset", "--hard", "@{u}"], timeout=30)
        except Exception:                              # noqa: BLE001
            pass

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 24)
        lay.setSpacing(18)

        titulo = QLabel("Suite Contable")
        titulo.setStyleSheet("font-size:26px; font-weight:bold; color:#17375E;")
        lay.addWidget(titulo)
        fila = QHBoxLayout()
        sub = QLabel("Elegí qué programa abrir.")
        sub.setStyleSheet("color:#5D6D7E; font-size:13px;")
        fila.addWidget(sub)
        fila.addStretch()
        self._btn_upd_all = QPushButton("⟳ Actualizar todo")
        self._btn_upd_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_upd_all.setToolTip(
            "Baja la última versión de todos los programas instalados en esta "
            "PC y reinstala dependencias. Los datos no se tocan.")
        self._btn_upd_all.setStyleSheet(
            "QPushButton { background:#1E8E4E; color:white; border:none;"
            "border-radius:8px; padding:7px 14px; font-size:12px;"
            "font-weight:bold; } QPushButton:hover { background:#1B7E45; }"
            "QPushButton:disabled { background:#B7C4CE; }")
        self._btn_upd_all.clicked.connect(self._actualizar_todo)
        fila.addWidget(self._btn_upd_all)
        self._btn_cred = QPushButton("🔑 Traer credenciales")
        self._btn_cred.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_cred.clicked.connect(lambda: self._traer_credenciales(auto=False))
        self._refrescar_boton_cred()
        fila.addWidget(self._btn_cred)
        lay.addLayout(fila)

        # Tarjetas dentro de un área con scroll (por si crece la lista de apps).
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        cont = QWidget()
        cl = QVBoxLayout(cont)
        cl.setContentsMargins(0, 0, 8, 0)
        cl.setSpacing(12)
        for app in config.APPS:
            cl.addWidget(self._tarjeta(app))
        cl.addStretch()
        scroll.setWidget(cont)
        lay.addWidget(scroll, stretch=1)

        pie = QLabel(f"Suite Contable v{VERSION}")
        pie.setStyleSheet("color:#9AA5B1; font-size:11px;")
        pie.setAlignment(Qt.AlignmentFlag.AlignRight)
        lay.addWidget(pie)

    def _tarjeta(self, app):
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background:#FFFFFF; border:1px solid #E5E9F0;"
            f"border-left:5px solid {app['color']}; border-radius:10px; }}")
        h = QHBoxLayout(card)
        h.setContentsMargins(18, 16, 18, 16)
        h.setSpacing(16)

        emoji = QLabel(app["emoji"])
        emoji.setStyleSheet("font-size:34px;")
        h.addWidget(emoji)

        col = QVBoxLayout()
        col.setSpacing(2)
        ver = _leer_version(app)
        nombre = QLabel(app["nombre"] + (f"   v{ver}" if ver else ""))
        nombre.setStyleSheet("font-size:17px; font-weight:bold; color:#1F2A37;")
        col.addWidget(nombre)
        desc = QLabel(app["desc"])
        desc.setStyleSheet("color:#5D6D7E; font-size:12px;")
        col.addWidget(desc)
        if not os.path.isdir(app["dir"]):
            aviso = QLabel("⚠ no encontrado en " + app["dir"])
            aviso.setStyleSheet("color:#C0392B; font-size:11px;")
            col.addWidget(aviso)
        lbl_update = QLabel("")
        lbl_update.setStyleSheet("color:#B9770E; font-size:11px; font-weight:bold;")
        lbl_update.setVisible(False)
        col.addWidget(lbl_update)
        h.addLayout(col, stretch=1)

        botones = QVBoxLayout()
        botones.setSpacing(6)
        falta = not os.path.isdir(app["dir"])
        btn = QPushButton("Abrir")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedWidth(120)
        btn.setStyleSheet(
            f"QPushButton {{ background:{app['color']}; color:white; border:none;"
            "border-radius:8px; padding:10px 0; font-size:14px; font-weight:bold; }}"
            "QPushButton:hover { opacity:.9; }"
            "QPushButton:disabled { background:#C4CDD5; }")
        btn.clicked.connect(lambda _, a=app: _abrir(a, self))
        btn.setEnabled(not falta)
        botones.addWidget(btn)

        if falta:
            btn_inst = QPushButton("⬇ Instalar")
            btn_inst.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_inst.setFixedWidth(120)
            btn_inst.setStyleSheet(
                "QPushButton { background:#F2C14E; color:#5A3E00; border:none;"
                "border-radius:8px; padding:8px 0; font-size:12px; font-weight:bold; }"
                "QPushButton:hover { background:#E6B33E; }")
            btn_inst.clicked.connect(lambda _, a=app: _instalar_app(a, self))
            botones.addWidget(btn_inst)

        h.addLayout(botones)

        # La actualización se hace desde el botón "Actualizar todo" de arriba;
        # cada tarjeta sólo muestra el aviso de que hay versión nueva.
        self._cards[app["key"]] = {"lbl": lbl_update, "nombre": nombre, "app": app}
        return card

    def _on_update(self, key, latest):
        card = self._cards.get(key)
        if not card or not latest:
            return
        card["lbl"].setText(f"🔔 ACTUALIZACIÓN DISPONIBLE (v{latest}) — usá «Actualizar todo»")
        card["lbl"].setVisible(True)


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
