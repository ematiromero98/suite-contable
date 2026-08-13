# -*- coding: utf-8 -*-
"""
Suite Contable — MR & Asociados.
Launcher: una ventana para abrir DDJJ Impuestos o RetencionesPro.

Abrir con doble clic en «Suite Contable.bat» (o: pythonw main.py).
"""
import os
import re
import sys
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from version import VERSION


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


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Suite Contable — MR & Asociados")
        self.setMinimumWidth(560)
        self._build()

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
        h.addLayout(col, stretch=1)

        btn = QPushButton("Abrir")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedWidth(110)
        btn.setStyleSheet(
            f"QPushButton {{ background:{app['color']}; color:white; border:none;"
            "border-radius:8px; padding:10px 0; font-size:14px; font-weight:bold; }}"
            "QPushButton:hover { opacity:.9; }")
        btn.clicked.connect(lambda _, a=app: _abrir(a, self))
        h.addWidget(btn)
        return card


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = Launcher()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
