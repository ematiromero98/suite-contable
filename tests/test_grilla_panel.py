# -*- coding: utf-8 -*-
"""Panel con ventana angosta: la grilla de tarjetas se adapta al ancho del
viewport (2 columnas si entran, si no 1) y ninguna tarjeta queda cortada a la
derecha. Offscreen; chequeos/backups/credenciales parcheados (no instala ni
actualiza nada)."""
import pytest

QtWidgets = pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtCore import QEventLoop, QPoint, QTimer      # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _esperar(ms=60):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


@pytest.fixture
def ventana(qapp, monkeypatch):
    import main
    monkeypatch.setattr(main.Launcher, "_auto_update_suite", staticmethod(lambda: None))
    monkeypatch.setattr(main, "credenciales", None)
    monkeypatch.setattr(main._Chequeador, "correr", lambda self, apps: None)
    monkeypatch.setattr(main._BackupsLoader, "correr", lambda self, limit=200: None)
    w = main.Launcher()
    # Peor caso: tarjetas con «Nueva versión disponible» + botón Actualizar.
    for app in main.config.APPS[:3]:
        w._on_update(app["key"], "9.9.9")
        w._cards[app["key"]]["btn"].setVisible(True)
    w._stack.setCurrentIndex(0)
    w.show()
    yield w
    w.close()


def _ajustar(w, ancho):
    w.resize(ancho, 680)
    for _ in range(4):
        _esperar()


def _fuera_de_vista(w):
    """Tarjetas cuyo borde izq./der. cae fuera del viewport del Panel."""
    vp = w._scroll_panel.viewport()
    fuera = []
    for c in w._cards.values():
        card = c["nombre"].parentWidget()
        izq = card.mapTo(vp, QPoint(0, 0)).x()
        der = izq + card.width()
        if izq < 0 or der > vp.width():
            fuera.append((c["app"]["key"], izq, der, vp.width()))
    return fuera


def test_ventana_1000_ninguna_tarjeta_cortada(ventana):
    _ajustar(ventana, 1000)
    assert ventana.width() == 1000
    assert _fuera_de_vista(ventana) == []
    # El contenido nunca es más ancho que el viewport (no hay scroll horizontal).
    assert ventana._grilla_panel.width() <= ventana._scroll_panel.viewport().width()


@pytest.mark.parametrize("ancho", [900, 1180, 1400, 1800])
def test_otros_anchos_tampoco_cortan(ventana, ancho):
    _ajustar(ventana, ancho)
    assert _fuera_de_vista(ventana) == []


def test_columnas_segun_ancho(ventana):
    g = ventana._grilla_panel
    minimo = g.ancho_minimo_tarjeta()
    assert minimo > 0
    assert g.columnas_para(minimo) == 1
    assert g.columnas_para(2 * minimo + 14 + 8) == 2
    assert g.columnas_para(2 * minimo + 14 + 7) == 1
    assert g.columnas_para(10_000) == 2           # tope: 2 columnas
    _ajustar(ventana, 900)
    assert g.columnas() == 1
    _ajustar(ventana, 2400)
    assert g.columnas() == 2
    _ajustar(ventana, 1000)                       # y vuelve a 1 al achicar
    assert g.columnas() == 1


def test_minimo_de_ventana_alcanza_para_el_panel(ventana):
    """El mínimo de la ventana deja al Panel su ancho mínimo (1 columna)."""
    _ajustar(ventana, 400)                        # se frena en el mínimo
    assert ventana.width() == ventana.minimumWidth() >= 900
    assert _fuera_de_vista(ventana) == []
