# -*- coding: utf-8 -*-
"""«Actualizar» una app baja SIEMPRE la rama principal (`origin/<rama>`), por
el camino normal y por el del token por igual; no pisa una copia que está en
otra rama o con cambios locales (queda pendiente con el motivo), y al terminar
vuelve a leer la versión instalada para decidir si sigue pendiente.

git es FALSO (salvo el último test, que usa git real en carpetas temporales):
nunca se actualiza ni instala nada de verdad. El token es inventado."""
import subprocess
import types

import pytest

TOK = "ghp_FAKERAMA42"


def _r(rc=0, out="", err=""):
    return types.SimpleNamespace(returncode=rc, stdout=out, stderr=err)


@pytest.fixture
def main_mod(monkeypatch):
    pytest.importorskip("PyQt6.QtWidgets")
    import main
    monkeypatch.setattr(main, "_token_runtime", lambda: TOK)
    monkeypatch.setattr(main, "_leer_token_env", lambda d: None)
    monkeypatch.setattr(main, "_pip_update", lambda d, avisar=None: (True, "ok"))
    return main


def _app(tmp_path, **extra):
    (tmp_path / ".git").mkdir(exist_ok=True)
    return dict({"dir": str(tmp_path), "repo": "x/y", "version_file": "VERSION"},
                **extra)


class GitFalso:
    """Simula git: rama actual, `status --porcelain`, fetch normal ok/falla."""

    def __init__(self, rama="main", sucio="", fetch_ok=True, ff_ok=True):
        self.rama, self.sucio = rama, sucio
        self.fetch_ok, self.ff_ok = fetch_ok, ff_ok
        self.llamadas = []

    def __call__(self, dir_, args, timeout=240):
        self.llamadas.append(list(args))
        if args[:2] == ["rev-parse", "--abbrev-ref"]:
            return _r(0, self.rama + "\n")
        if args[0] == "status":
            return _r(0, self.sucio)
        if args == ["fetch"]:
            return _r(0) if self.fetch_ok else _r(128, err="Authentication failed")
        if args[0] == "fetch":
            return _r(0)
        if args[0] == "merge":
            return _r(0) if self.ff_ok else _r(1, err="Not possible to fast-forward")
        return _r(0)

    def con(self, sub):
        return [a for a in self.llamadas if a and a[0] == sub]


def _destructivos(g):
    return [a for a in g.llamadas
            if a[0] in ("fetch", "merge", "reset", "stash", "branch")]


# ------------------------------------------------------ rama principal ok
def test_rama_principal_ok_va_contra_origin_main(main_mod, tmp_path, monkeypatch):
    g = GitFalso()
    monkeypatch.setattr(main_mod, "_git", g)
    estado, det = main_mod._actualizar_app_core(_app(tmp_path))
    assert estado == "ok"
    assert g.con("merge") == [["merge", "--ff-only", "origin/main"]]
    assert not any("@{u}" in " ".join(a) or "FETCH_HEAD" in " ".join(a)
                   for a in g.llamadas)


def test_rama_configurada_master(main_mod, tmp_path, monkeypatch):
    g = GitFalso(rama="master")
    monkeypatch.setattr(main_mod, "_git", g)
    estado, _ = main_mod._actualizar_app_core(_app(tmp_path, rama="master"))
    assert estado == "ok"
    assert g.con("merge") == [["merge", "--ff-only", "origin/master"]]


def test_facturador_configurado_en_master():
    pytest.importorskip("PyQt6.QtWidgets")
    import main
    fac = next(a for a in main.config.APPS if a["key"] == "facturador")
    assert main._rama_principal(fac) == "master"
    otras = [a for a in main.config.APPS if a["key"] != "facturador"]
    assert all(main._rama_principal(a) == "main" for a in otras)


# ------------------------------------------------- copia en otra rama
def test_copia_en_otra_rama_no_se_toca(main_mod, tmp_path, monkeypatch):
    g = GitFalso(rama="fix/retpro-con-sesion")
    monkeypatch.setattr(main_mod, "_git", g)
    estado, det = main_mod._actualizar_app_core(_app(tmp_path))
    assert estado == "retenida"
    assert "fix/retpro-con-sesion" in det and "no se actualizó" in det
    assert "pendiente" in det.lower()
    assert _destructivos(g) == []          # ni fetch, ni merge, ni reset


def test_head_suelto_no_se_toca(main_mod, tmp_path, monkeypatch):
    g = GitFalso(rama="HEAD")
    monkeypatch.setattr(main_mod, "_git", g)
    estado, det = main_mod._actualizar_app_core(_app(tmp_path))
    assert estado == "retenida" and "HEAD suelto" in det
    assert _destructivos(g) == []


# ------------------------------------------------------- cambios locales
def test_cambios_locales_no_se_pisan(main_mod, tmp_path, monkeypatch):
    g = GitFalso(sucio=" M main.py\nM  db.py\n")
    monkeypatch.setattr(main_mod, "_git", g)
    estado, det = main_mod._actualizar_app_core(_app(tmp_path))
    assert estado == "retenida"
    assert "2 archivo" in det and "no se actualizó" in det
    assert _destructivos(g) == []
    # Sólo mira archivos versionados (.env/.venv/salidas no cuentan).
    assert ["status", "--porcelain", "--untracked-files=no"] in g.llamadas


# --------------------------------------------------------- camino token
def test_camino_token_misma_rama_que_el_normal(main_mod, tmp_path, monkeypatch):
    g = GitFalso(fetch_ok=False)
    monkeypatch.setattr(main_mod, "_git", g)
    estado, det = main_mod._actualizar_app_core(_app(tmp_path))
    assert estado == "ok"
    fetch_tok = [a for a in g.con("fetch") if a != ["fetch"]]
    assert len(fetch_tok) == 1
    assert fetch_tok[0][-1] == "+refs/heads/main:refs/remotes/origin/main"
    # El merge va al MISMO destino que en el camino normal.
    assert g.con("merge") == [["merge", "--ff-only", "origin/main"]]
    assert TOK not in det


def test_camino_token_diverge_realinea_a_origin_main(main_mod, tmp_path, monkeypatch):
    g = GitFalso(fetch_ok=False, ff_ok=False)
    monkeypatch.setattr(main_mod, "_git", g)
    estado, _ = main_mod._actualizar_app_core(_app(tmp_path))
    assert estado == "ok"
    assert g.con("reset") == [["reset", "--hard", "origin/main"]]
    assert g.con("branch")                 # respaldo antes de realinear


# ---------------------------------- volver a leer la versión instalada
def test_version_instalada_sigue_atras_queda_pendiente(main_mod, tmp_path):
    app = _app(tmp_path)
    (tmp_path / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    estado, det = main_mod._revisar_version_tras_actualizar(app, "ok", "al día", "1.1.0")
    assert estado == "aviso"
    assert "v1.0.0" in det and "v1.1.0" in det and "sigue pendiente" in det
    assert main_mod._sigue_pendiente("1.1.0", "1.0.0")


def test_version_instalada_al_dia_sale_de_pendientes(main_mod, tmp_path):
    app = _app(tmp_path)
    (tmp_path / "VERSION").write_text("1.1.0\n", encoding="utf-8")
    assert main_mod._revisar_version_tras_actualizar(
        app, "ok", "al día", "1.1.0") == ("ok", "al día")
    assert not main_mod._sigue_pendiente("1.1.0", "1.1.0")
    assert not main_mod._sigue_pendiente(None, "1.0.0")      # no estaba pendiente
    assert main_mod._sigue_pendiente("1.1.0", None)          # ilegible: sigue


def test_retenida_y_error_no_se_reinterpretan(main_mod, tmp_path):
    app = _app(tmp_path)
    assert main_mod._revisar_version_tras_actualizar(
        app, "retenida", "x", "9.9.9") == ("retenida", "x")
    assert main_mod._revisar_version_tras_actualizar(
        app, "error", "y", "9.9.9") == ("error", "y")


def test_worker_vuelve_a_leer_la_version(main_mod, tmp_path, monkeypatch):
    app = dict(_app(tmp_path), key="k", nombre="App K")
    (tmp_path / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    monkeypatch.setattr(main_mod, "_actualizar_app_core",
                        lambda a, avisar=None: ("ok", "al día"))

    class HiloEnElActo:
        def __init__(self, target, daemon=None):
            self._t = target

        def start(self):
            self._t()

    monkeypatch.setattr(main_mod.threading, "Thread", HiloEnElActo)
    w = main_mod._UpdateAllWorker()
    got = []
    w.listo.connect(got.append)
    w.start([app], {"k": "1.2.0"})
    (key, _n, estado, det), = got[0]
    assert key == "k" and estado == "aviso" and "sigue pendiente" in det


def test_final_retenida_es_aviso_no_error():
    from ui.avance import final
    tipo, ley = final("retenida")
    assert tipo == "aviso" and ley == "pendiente"


# ------------------------------------------------ git REAL (sin red)
def _git_real(cwd, *args):
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def test_git_real_otra_rama_y_main(main_mod, tmp_path):
    if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
        pytest.skip("sin git")
    origen = tmp_path / "origen"
    origen.mkdir()
    _git_real(origen, "init", "-q", "-b", "main")
    _git_real(origen, "config", "user.email", "t@t")
    _git_real(origen, "config", "user.name", "t")
    (origen / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    _git_real(origen, "add", "VERSION")
    _git_real(origen, "commit", "-qm", "v1.0.0")
    copia = tmp_path / "copia"
    _git_real(tmp_path, "clone", "-q", str(origen), str(copia))
    # Otra sesión en la copia: rama propia, trackeando una rama remota.
    _git_real(origen, "checkout", "-qb", "fix/otra-sesion")
    (origen / "x.txt").write_text("x", encoding="utf-8")
    _git_real(origen, "add", "x.txt")
    _git_real(origen, "commit", "-qm", "wip")
    _git_real(origen, "checkout", "-q", "main")
    (origen / "VERSION").write_text("1.1.0\n", encoding="utf-8")
    _git_real(origen, "commit", "-qam", "v1.1.0")
    _git_real(copia, "fetch", "-q")
    _git_real(copia, "checkout", "-q", "fix/otra-sesion")
    app = {"dir": str(copia), "repo": None, "version_file": "VERSION"}

    estado, det = main_mod._actualizar_app_core(app)
    assert estado == "retenida" and "fix/otra-sesion" in det
    assert _git_real(copia, "rev-parse", "--abbrev-ref", "HEAD") == "fix/otra-sesion"

    # De vuelta en main (como cuando la otra sesión cierra): baja origin/main.
    _git_real(copia, "checkout", "-q", "main")
    estado, det = main_mod._actualizar_app_core(app)
    assert estado == "ok", det
    assert main_mod._leer_version(app) == "1.1.0"
    assert main_mod._revisar_version_tras_actualizar(app, estado, det, "1.1.0")[0] == "ok"
