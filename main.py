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


def _script_update(app):
    """Primer script de actualización existente de la app, o None."""
    for e in app.get("actualizar", []):
        p = os.path.join(app["dir"], e)
        if os.path.isfile(p):
            return p
    return None


def _vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or ""))


def _es_mayor(latest, installed):
    return bool(latest) and bool(installed) and _vtuple(latest) > _vtuple(installed)


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
                hay = latest if _es_mayor(latest, inst) else ""
                self.listo.emit(a["key"], hay)
        threading.Thread(target=_run, daemon=True).start()


def _abrir(app, parent):
    entrada = _entrada(app)
    if not entrada:
        QMessageBox.warning(
            parent, f"{app['nombre']} no encontrado",
            f"No encontré {app['nombre']} en:\n{app['dir']}\n\n"
            f"Fijá la ruta con la variable de entorno correspondiente "
            f"({'DDJJ_IMPUESTOS_DIR' if app['key']=='ddjj' else 'RETENCIONESPRO_DIR'}).")
        return
    try:
        if entrada.lower().endswith(".bat"):
            subprocess.Popen(f'"{entrada}"', cwd=app["dir"], shell=True)
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


def _pip_update(dir_):
    """Instala dependencias (en .venv si existe, o python del sistema). Crea el
    .venv si falta. Devuelve True si quedaron instaladas, False si algo falló."""
    req = os.path.join(dir_, "requirements.txt")
    if not os.path.isfile(req):
        return True
    venv_py = os.path.join(dir_, ".venv", "Scripts", "python.exe")
    if not os.path.isfile(venv_py):
        # Intentar crear el .venv (la app lo usa para correr).
        try:
            subprocess.run(["python", "-m", "venv", os.path.join(dir_, ".venv")],
                           capture_output=True, text=True, timeout=300,
                           creationflags=_NO_WINDOW)
        except Exception:                              # noqa: BLE001
            pass
    py = venv_py if os.path.isfile(venv_py) else "python"
    try:
        subprocess.run([py, "-m", "pip", "install", "--upgrade", "pip"],
                       capture_output=True, text=True, timeout=300,
                       creationflags=_NO_WINDOW)
        r = subprocess.run([py, "-m", "pip", "install", "-r", req],
                           capture_output=True, text=True, timeout=900,
                           creationflags=_NO_WINDOW)
        return r.returncode == 0
    except Exception:                                   # noqa: BLE001
        return False


def _actualizar(app, parent):
    """Actualiza la app entera desde el ERP, sin depender de su .bat ni del CMD:
    baja los cambios, y si la copia local divergió, respalda y realinea con el
    código oficial; después instala dependencias nuevas. Los DATOS no se tocan
    (viven en Supabase y en .env/.venv, fuera de git)."""
    dir_ = app["dir"]
    if not os.path.isdir(os.path.join(dir_, ".git")):
        QMessageBox.warning(
            parent, "Actualizar",
            f"{app['nombre']} no es un repo git en:\n{dir_}")
        return

    parent.setCursor(Qt.CursorShape.WaitCursor)
    try:
        token, repo = _leer_token_env(dir_), app.get("repo")
        if token and repo:
            f = _git(dir_, ["fetch", f"https://{token}@github.com/{repo}.git"])
            target = "FETCH_HEAD"
        else:
            f = _git(dir_, ["fetch"])
            target = "@{u}"                              # rama remota trackeada
        if f.returncode != 0:
            parent.unsetCursor()
            QMessageBox.critical(parent, "Error",
                                 f"No pude traer cambios de {app['nombre']}:\n"
                                 f"{(f.stderr or '')[:400]}")
            return

        # Caso normal: avanzar en línea recta.
        if _git(dir_, ["merge", "--ff-only", target]).returncode != 0:
            # Divergió: respaldar (rama backup + stash) y realinear al oficial.
            import time
            _git(dir_, ["branch", f"backup-local-{int(time.time())}"])
            _git(dir_, ["stash", "push", "-u", "-m", "respaldo-antes-de-actualizar"])
            rs = _git(dir_, ["reset", "--hard", target])
            if rs.returncode != 0:
                parent.unsetCursor()
                QMessageBox.critical(parent, "Error",
                                     f"No pude alinear {app['nombre']}:\n"
                                     f"{(rs.stderr or '')[:400]}")
                return

        deps_ok = _pip_update(dir_)
    except Exception as e:                              # noqa: BLE001
        parent.unsetCursor()
        QMessageBox.critical(parent, "Error",
                             f"No pude actualizar {app['nombre']}:\n{e}")
        return
    parent.unsetCursor()
    if deps_ok:
        QMessageBox.information(
            parent, "Actualizado",
            f"{app['nombre']} quedó al día. Abrila cuando quieras.")
    else:
        QMessageBox.warning(
            parent, "Actualizado con aviso",
            f"{app['nombre']}: el código quedó al día, pero algunas "
            f"dependencias no se instalaron del todo.\n\nSi algo no funciona "
            f"(por ejemplo el QR), corré «setup.bat» en la carpeta de la app, "
            f"o reintentá Actualizar con buena conexión.")


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
        if ok:
            QMessageBox.information(self, "Listo", msg)
        else:
            QMessageBox.warning(self, "No se pudo", msg)

    @staticmethod
    def _auto_update_suite():
        try:
            if os.path.isdir(os.path.join(_BASE, ".git")):
                _git(_BASE, ["pull", "--ff-only"], timeout=60)
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
        self._btn_cred = QPushButton("🔑 Traer credenciales")
        self._btn_cred.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_cred.setToolTip(
            "Baja el archivo .env (credenciales) desde el Google Drive del "
            "estudio a esta PC. Pide acceso a Google una sola vez.")
        self._btn_cred.setStyleSheet(
            "QPushButton { background:#EAF1FB; color:#17375E;"
            "border:1px solid #C7D8EF; border-radius:8px; padding:7px 12px;"
            "font-size:12px; font-weight:bold; }"
            "QPushButton:hover { background:#DCE8F8; }"
            "QPushButton:disabled { color:#9AA5B1; }")
        if credenciales is None:
            self._btn_cred.setEnabled(False)
        self._btn_cred.clicked.connect(lambda: self._traer_credenciales(auto=False))
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

        btn_upd = QPushButton("⟳ Actualizar")
        btn_upd.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_upd.setFixedWidth(120)
        btn_upd.setStyleSheet(
            "QPushButton { background:#F2C14E; color:#5A3E00; border:none;"
            "border-radius:8px; padding:8px 0; font-size:12px; font-weight:bold; }"
            "QPushButton:hover { background:#E6B33E; }")
        btn_upd.setVisible(False)
        btn_upd.clicked.connect(lambda _, a=app: _actualizar(a, self))
        botones.addWidget(btn_upd)
        h.addLayout(botones)

        self._cards[app["key"]] = {"lbl": lbl_update, "btn": btn_upd, "app": app}
        return card

    def _on_update(self, key, latest):
        card = self._cards.get(key)
        if not card or not latest:
            return
        card["lbl"].setText(f"🔔 ACTUALIZACIÓN DISPONIBLE (v{latest})")
        card["lbl"].setVisible(True)
        # Mostrar Actualizar si la app tiene su propio actualizador o si es un
        # repo git (en ese caso el ERP hace el git pull directo).
        app = card["app"]
        if _script_update(app) or os.path.isdir(os.path.join(app["dir"], ".git")):
            card["btn"].setVisible(True)


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
