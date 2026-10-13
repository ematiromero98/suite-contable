# -*- coding: utf-8 -*-
"""El token de GitHub nunca aparece en avisos, log ni tooltip del camino de
actualización (fetch colgado/fallido, merge/reset, pip). git/pip son FALSOS:
nunca se actualiza ni instala nada de verdad. El token es inventado."""
import os
import subprocess
import sys
import types

import pytest

_QAPP = None
TOK = "ghp_FAKE123"
URL = f"https://x-access-token:{TOK}@github.com/x/y.git"
ENVTOK = "usuario:SECRETOENV987"          # token del .env sin forma ghp_


def _r(rc=0, out="", err=""):
    return types.SimpleNamespace(returncode=rc, stdout=out, stderr=err)


def _limpio(texto):
    return TOK not in texto and "FAKE123" not in texto and "SECRETOENV987" not in texto


@pytest.fixture
def main_mod(monkeypatch):
    pytest.importorskip("PyQt6.QtWidgets")
    import main
    monkeypatch.setattr(main, "_token_runtime", lambda: TOK)
    monkeypatch.setattr(main, "_leer_token_env", lambda d: None)
    # Estos tests miran sólo el token: la copia se da por limpia y en su rama
    # principal (eso se prueba en tests/test_actualizar_rama.py).
    monkeypatch.setattr(main, "_problema_copia_local", lambda d, r: None)
    return main


def _app(tmp_path):
    (tmp_path / ".git").mkdir(exist_ok=True)
    return {"dir": str(tmp_path), "repo": "x/y"}


# ------------------------------------------------------------ _sin_token
def test_sin_token_tapa_url_y_tokens_sueltos(main_mod):
    s = main_mod._sin_token(f"fatal: {URL} y suelto {TOK} y github_pat_ABCdef_123456")
    assert _limpio(s) and "github_pat_" not in s
    assert "https://***@github.com/x/y.git" in s
    assert main_mod._sin_token("clave-rara-zzz", "clave-rara-zzz") == "***"
    assert main_mod._sin_token(None) == ""
    assert main_mod._sin_token("sin nada que tapar") == "sin nada que tapar"


def test_tapar_credenciales_de_ui_avance():
    from ui.avance import tapar_credenciales
    assert _limpio(tapar_credenciales(f"error en {URL}"))
    assert tapar_credenciales(None) == ""


# ---------------------------------------------------- fetch colgado / fallido
def test_fetch_colgado_con_token_no_filtra(main_mod, tmp_path, monkeypatch, capsys):
    llamadas = []

    def fake_git(dir_, args, timeout=240):
        llamadas.append(args)
        if args == ["fetch"]:
            return _r(1, err="fatal: Authentication failed")
        # fetch con el token en la URL: se cuelga -> TimeoutExpired repite el cmd
        raise subprocess.TimeoutExpired(["git", "-C", dir_] + args, timeout)

    monkeypatch.setattr(main_mod, "_git", fake_git)
    estado, det = main_mod._actualizar_app_core(_app(tmp_path))
    assert any(URL in " ".join(a) for a in llamadas)   # sí usó el token
    assert estado == "error" and "timed out" in det
    assert _limpio(det)
    out = capsys.readouterr()
    assert _limpio(out.out + out.err)


def test_fetch_fallido_stderr_con_url_no_filtra(main_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(main_mod, "_leer_token_env", lambda d: ENVTOK)
    relleno = "x" * 280                        # el token cae justo en el corte

    def fake_git(dir_, args, timeout=240):
        return _r(1, err=f"{relleno} fatal: unable to access '{args[-1]}': 403")

    monkeypatch.setattr(main_mod, "_git", fake_git)
    estado, det = main_mod._actualizar_app_core(_app(tmp_path))
    assert estado == "error" and _limpio(det) and len(det) <= 300


def test_reset_fallido_no_filtra(main_mod, tmp_path, monkeypatch):
    def fake_git(dir_, args, timeout=240):
        if args[0] == "fetch":
            return _r(1) if args == ["fetch"] else _r(0)
        if args[0] == "merge":
            return _r(1, err="no ff")
        if args[0] == "reset":
            return _r(1, err=f"fatal: no pude con {URL}")
        return _r(0)

    monkeypatch.setattr(main_mod, "_git", fake_git)
    estado, det = main_mod._actualizar_app_core(_app(tmp_path))
    assert estado == "error" and _limpio(det)


def test_pip_fallido_aviso_no_filtra(main_mod, tmp_path, monkeypatch):
    app = _app(tmp_path)
    (tmp_path / "requirements.txt").write_text("x\n", encoding="utf-8")
    py = tmp_path / ".venv" / "Scripts"
    py.mkdir(parents=True)
    (py / "python.exe").write_text("", encoding="utf-8")
    monkeypatch.setattr(main_mod, "_git", lambda *a, **k: _r(0))
    monkeypatch.setattr(main_mod.subprocess, "run", lambda cmd, **kw: _r(
        1, err=f"ERROR: git+{URL}#egg=algo no se pudo bajar"))
    estado, det = main_mod._actualizar_app_core(app)
    assert estado == "aviso" and _limpio(det)


def test_excepcion_inesperada_no_filtra(main_mod, tmp_path, monkeypatch):
    def roto(*a, **k):
        raise RuntimeError(f"explotó con {URL}")

    monkeypatch.setattr(main_mod, "_actualizar_app_core_impl", roto)
    estado, det = main_mod._actualizar_app_core(_app(tmp_path))
    assert estado == "error" and _limpio(det)


# ------------------------------------------------------------------ tooltip
def test_tooltip_del_icono_no_muestra_token():
    QtWidgets = pytest.importorskip("PyQt6.QtWidgets")
    global _QAPP                               # que no la junte el GC
    _QAPP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    from ui.icono_progreso import IconoProgreso
    w = IconoProgreso(None, lado=44, radio=13)
    w.fallar(f"fatal: {URL} timed out")
    assert _limpio(w.toolTip()) and "Falló" in w.toolTip()
    w.terminar("con aviso", aviso=True, detalle=f"pip: {URL}")
    assert _limpio(w.toolTip())


# ------------------------------------------------- ui.avance ausente (#2)
def test_suite_abre_sin_ui_avance():
    pytest.importorskip("PyQt6.QtWidgets")
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    codigo = (
        "import sys\n"
        "class Bloq:\n"
        "    def find_spec(self, n, p=None, t=None):\n"
        "        if n == 'ui.avance':\n"
        "            raise ImportError('sin ui.avance')\n"
        "sys.meta_path.insert(0, Bloq())\n"
        "import main\n"
        "assert main.IconoProgreso is None\n"
        "s = main.SeguidorAvance()\n"
        "s.etapa('k', 'fetch'); s.terminar('k'); s.olvidar('k')\n"
        "assert s.activas() == [] and s.etapa_de('k') is None\n"
        "assert main._leyenda_etapa('fetch') == ''\n"
        "print('OK')\n")
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=raiz, env=env,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and "OK" in r.stdout, r.stderr
