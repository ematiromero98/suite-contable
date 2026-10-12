# -*- coding: utf-8 -*-
"""IconoProgreso offscreen (se saltea si no hay PyQt6) + ganchos de etapa de
main.py con git/pip FALSOS (nunca instala ni actualiza nada de verdad)."""
import types

import pytest

QtWidgets = pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtCore import QEventLoop, QTimer           # noqa: E402
from PyQt6.QtGui import QColor, QImage, QPixmap        # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _esperar(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _logo(lado=44):
    pm = QPixmap(lado * 2, lado * 2)
    pm.fill(QColor("#2ee6a6"))
    pm.setDevicePixelRatio(2)
    return pm


def _render(w):
    img = QImage(w.size(), QImage.Format.Format_ARGB32)
    img.fill(QColor("#171c26"))
    w.render(img)
    return img


def test_estados_y_api(qapp):
    from ui.icono_progreso import IconoProgreso
    w = IconoProgreso(_logo(), lado=44, radio=13)
    assert w.estado == "reposo" and w.texto == ""
    w.en_cola()
    assert w.estado == "cola" and w.texto == "en cola"
    w.avanzar(0.5, "descargando…", animar=False)
    assert w.estado == "progreso" and w.avance == pytest.approx(0.5)
    w.avanzar(2.0, animar=False)
    assert w.avance == 1.0                       # se acota a 0..1
    w.terminar("actualizada")
    assert w.estado == "ok" and w.texto == "actualizada"
    _esperar(600)                                # deja correr el rebote
    assert w.escala == pytest.approx(1.0)
    w.fallar("fatal: repository not found")
    assert w.estado == "error"
    assert "repository not found" in w.toolTip()
    w.reposo()
    assert w.estado == "reposo" and w.toolTip() == ""


def test_velo_conico_cubre_lo_que_falta(qapp):
    """A mitad, la mitad DERECHA (12→6 horario) queda revelada y la izquierda
    con velo: el píxel de la izquierda es más oscuro que el de la derecha."""
    from ui.icono_progreso import IconoProgreso
    w = IconoProgreso(_logo(), lado=44, radio=13, leyenda=False)
    w.avanzar(0.5, animar=False)
    img = _render(w)
    r = w._rect_icono()
    y = int(r.center().y() + 8)                  # debajo del texto del %
    izq = QColor(img.pixel(int(r.left() + 6), y))
    der = QColor(img.pixel(int(r.right() - 6), y))
    assert izq.lightness() < der.lightness() - 40

    w.en_cola()                                  # velo completo
    img = _render(w)
    der2 = QColor(img.pixel(int(r.right() - 6), y))
    assert der2.lightness() < der.lightness() - 40


def test_sin_logo_dibuja_monograma(qapp):
    from ui.icono_progreso import IconoProgreso
    w = IconoProgreso(None, lado=44, color="#8E44AD", mono="EP")
    img = _render(w)
    r = w._rect_icono()
    c = QColor(img.pixel(int(r.left() + 4), int(r.top() + 22)))
    assert abs(c.red() - 0x8E) < 30 and abs(c.blue() - 0xAD) < 30


# ------------------------------------------------------- ganchos en main.py
def _fake_git_ok(dir_, args, timeout=240):
    return types.SimpleNamespace(returncode=0, stdout="", stderr="")


def test_actualizar_app_core_avisa_etapas_en_orden(qapp, tmp_path, monkeypatch):
    import main
    (tmp_path / ".git").mkdir()
    (tmp_path / "requirements.txt").write_text("x\n", encoding="utf-8")
    llamadas = []
    monkeypatch.setattr(main, "_git", _fake_git_ok)

    def fake_run(cmd, **kw):                     # venv y pip: simulados
        llamadas.append(cmd[1:3])
        if "venv" in cmd:
            py = tmp_path / ".venv" / "Scripts"
            py.mkdir(parents=True)
            (py / "python.exe").write_text("", encoding="utf-8")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(main.subprocess, "run", fake_run)
    etapas = []
    estado, _ = main._actualizar_app_core(
        {"dir": str(tmp_path), "repo": "x/y"}, etapas.append)
    assert estado == "ok"
    assert etapas == ["fetch", "merge", "venv", "pip"]
    assert llamadas                               # pasó por el run falso


def test_actualizar_app_core_callback_roto_no_rompe(qapp, tmp_path, monkeypatch):
    import main
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(main, "_git", _fake_git_ok)

    def roto(_e):
        raise RuntimeError("boom")

    estado, _ = main._actualizar_app_core({"dir": str(tmp_path), "repo": "x/y"}, roto)
    assert estado == "ok"                         # sin requirements: ok


def test_actualizar_app_core_error_de_fetch(qapp, tmp_path, monkeypatch):
    import main
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(main, "_git", lambda *a, **k: types.SimpleNamespace(
        returncode=1, stdout="", stderr="fatal: sin red"))
    monkeypatch.setattr(main, "_token_runtime", lambda: None)
    monkeypatch.setattr(main, "_leer_token_env", lambda d: None)
    etapas = []
    estado, det = main._actualizar_app_core(
        {"dir": str(tmp_path), "repo": "x/y"}, etapas.append)
    assert (estado, etapas) == ("error", ["fetch"]) and "sin red" in det


def test_icono_app_usa_widget_de_progreso(qapp):
    import main
    app = dict(main.config.APPS[0])
    w = main._icono_app(app, 44, 13)
    assert hasattr(w, "avanzar")
