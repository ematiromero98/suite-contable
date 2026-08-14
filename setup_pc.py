# -*- coding: utf-8 -*-
"""
setup_pc.py — Deja una PC lista para el estudio, SIN pedir ningún login.

Lo corre el instalador (instalar_suite.ps1) DESPUÉS de loguear `gh` con el token
de sólo-lectura. Para esta PC:
  1. Clona (o actualiza) todas las apps del estudio desde GitHub.
  2. Instala las dependencias de cada app en su .venv.
  3. Trae las credenciales desde el repo privado suite-secretos (sin Drive).
  4. Crea el acceso directo del ERP en el Escritorio.

Es idempotente: se puede volver a correr cuando sea y sólo repara lo que falte.
No importa PyQt6 (usa sólo config + credenciales), así que corre con el Python
del sistema recién instalado.
"""
import os
import subprocess
import sys

import config

try:
    import credenciales
except Exception:                                          # noqa: BLE001
    credenciales = None

AQUI = os.path.dirname(os.path.abspath(__file__))
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _log(msg):
    print(msg, flush=True)


def _python_base():
    """Python real para crear los .venv (nunca el stub de la Microsoft Store)."""
    base = sys.executable or "python"
    consola = base.replace("pythonw.exe", "python.exe")
    return consola if os.path.isfile(consola) else base


def _clonar_app(app):
    d, repo = app["dir"], app.get("repo")
    if not repo:
        return
    if os.path.isdir(os.path.join(d, ".git")):
        _log(f"  [=] {app['nombre']}: actualizando")
        subprocess.run(["git", "-C", d, "pull", "--ff-only"], creationflags=_NO_WINDOW)
        return
    os.makedirs(os.path.dirname(d) or ".", exist_ok=True)
    _log(f"  [..] clonando {app['nombre']}")
    r = subprocess.run(["gh", "repo", "clone", repo, d], creationflags=_NO_WINDOW)
    _log("      OK" if r.returncode == 0
         else "      FALLÓ (¿el token tiene acceso a ese repo?)")


def _deps_app(app):
    d = app["dir"]
    req = os.path.join(d, "requirements.txt")
    if not os.path.isfile(req):
        return
    venv_py = os.path.join(d, ".venv", "Scripts", "python.exe")
    if not os.path.isfile(venv_py):
        subprocess.run([_python_base(), "-m", "venv", os.path.join(d, ".venv")],
                       creationflags=_NO_WINDOW)
    if os.path.isfile(venv_py):
        _log(f"  [..] dependencias de {app['nombre']}")
        subprocess.run([venv_py, "-m", "pip", "install", "-q", "--upgrade", "pip"],
                       creationflags=_NO_WINDOW)
        subprocess.run([venv_py, "-m", "pip", "install", "-q", "-r", req],
                       creationflags=_NO_WINDOW)


def _acceso_directo():
    ps1 = os.path.join(AQUI, "crear_acceso_directo.ps1")
    if os.path.isfile(ps1):
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", ps1], creationflags=_NO_WINDOW)


def main():
    _log("== Preparando esta PC para el estudio ==")
    _log("1) Bajando las apps del estudio…")
    for app in config.APPS:
        _clonar_app(app)
    _log("2) Instalando dependencias (puede tardar la primera vez)…")
    for app in config.APPS:
        _deps_app(app)
    _log("3) Trayendo credenciales desde GitHub…")
    if credenciales is not None:
        try:
            _ok, msg = credenciales.traer()
            _log(msg)
        except Exception as e:                              # noqa: BLE001
            _log(f"  No pude traer credenciales: {e}")
    _log("4) Creando el acceso directo…")
    _acceso_directo()
    _log("== Listo. Abrí «Suite Contable» desde el Escritorio. ==")


if __name__ == "__main__":
    main()
