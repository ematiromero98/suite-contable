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
    QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QIcon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from version import VERSION

_BASE = os.path.dirname(os.path.abspath(__file__))
# Evitar que se abran consolas negras al llamar a gh/.bat en Windows.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _leer_version(app):
    """Lee la versión de una app desde su archivo de versión (soporta
    VERSION = "x" y __version__ = "x")."""
    ruta = os.path.join(app["dir"], app["version_file"])
    try:
        with open(ruta, encoding="utf-8") as f:
            txt = f.read()
        m = re.search(r'(?:__version__|VERSION)\s*=\s*["\']([^"\']+)["\']', txt)
        if m:
            return m.group(1)
    except OSError:
        pass
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


def _actualizar(app, parent):
    script = _script_update(app)
    if not script:
        QMessageBox.warning(
            parent, "Actualizar",
            f"No encontré el actualizador de {app['nombre']} en:\n{app['dir']}")
        return
    try:
        subprocess.Popen(f'"{script}"', cwd=app["dir"], shell=True)
    except Exception as e:                              # noqa: BLE001
        QMessageBox.critical(parent, "Error",
                             f"No pude actualizar {app['nombre']}:\n{e}")
        return
    QMessageBox.information(
        parent, "Actualizando",
        f"Se está actualizando {app['nombre']}.\nCuando termine, se abre solo.")


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Suite Contable — MR & Asociados")
        self.setMinimumWidth(560)
        self._cards = {}
        ico = os.path.join(_BASE, "assets", "suite.ico")
        if os.path.isfile(ico):
            self.setWindowIcon(QIcon(ico))
        self._build()
        # Chequear actualizaciones en segundo plano y avisar en cada tarjeta.
        self._chequeador = _Chequeador()
        self._chequeador.listo.connect(self._on_update)
        self._chequeador.correr(config.APPS)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 24)
        lay.setSpacing(18)

        titulo = QLabel("Suite Contable")
        titulo.setStyleSheet("font-size:26px; font-weight:bold; color:#17375E;")
        lay.addWidget(titulo)
        sub = QLabel("Elegí qué programa abrir.")
        sub.setStyleSheet("color:#5D6D7E; font-size:13px;")
        lay.addWidget(sub)

        for app in config.APPS:
            lay.addWidget(self._tarjeta(app))

        lay.addStretch()
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

        self._cards[app["key"]] = {"lbl": lbl_update, "btn": btn_upd}
        return card

    def _on_update(self, key, latest):
        card = self._cards.get(key)
        if not card or not latest:
            return
        card["lbl"].setText(f"🔔 Hay una versión nueva: v{latest}")
        card["lbl"].setVisible(True)
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
