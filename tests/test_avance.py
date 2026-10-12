# -*- coding: utf-8 -*-
"""Avance derivado por etapas (ui/avance.py): sin GUI, con reloj falso."""
import pytest

from ui.avance import (ETAPAS, FINALES, SeguidorAvance, avance_en_etapa, final,
                       leyenda)


class Reloj:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def test_tramos_contiguos_y_ordenados():
    orden = ["fetch", "merge", "venv", "pip"]
    for a, b in zip(orden, orden[1:]):
        assert ETAPAS[a][1] == pytest.approx(ETAPAS[b][0])
    for e in orden + ["clonar"]:
        ini, techo, _l, tau = ETAPAS[e]
        assert 0.0 <= ini < techo < 1.0 and tau > 0
    assert ETAPAS["listo"][0] == ETAPAS["listo"][1] == 1.0


def test_avance_en_etapa_arranca_en_inicio_y_nunca_llega_al_techo():
    for e in ("fetch", "merge", "venv", "pip", "clonar"):
        ini, techo, _l, _tau = ETAPAS[e]
        assert avance_en_etapa(e, 0) == pytest.approx(ini)
        assert avance_en_etapa(e, -5) == pytest.approx(ini)
        previo = ini
        for s in (0.5, 2, 10, 30):
            v = avance_en_etapa(e, s)
            assert previo <= v < techo
            previo = v
        assert avance_en_etapa(e, 600) == pytest.approx(techo, abs=1e-3)


def test_cola_es_cero_y_etapa_desconocida_usa_fetch():
    assert avance_en_etapa("cola", 99) == 0.0
    assert avance_en_etapa("rara", 0) == pytest.approx(ETAPAS["fetch"][0])
    assert leyenda("rara") == leyenda("fetch") == "descargando…"


def test_leyendas_y_finales():
    assert leyenda("cola") == "en cola"
    assert leyenda("pip") == "dependencias…"
    assert final("ok") == ("ok", "actualizada")
    assert final("instalada") == ("ok", "instalada")
    assert final("aviso")[0] == "aviso"
    assert final("error")[0] == "error"
    assert final("saltada")[0] == "error"
    assert final("cualquier-cosa") == FINALES["error"]


def test_seguidor_secuencia_completa_monotona():
    r = Reloj()
    seg = SeguidorAvance(reloj=r)
    seg.etapa("a", "cola")
    seg.etapa("b", "cola")
    assert seg.avance("a") == 0.0
    assert sorted(seg.activas()) == ["a", "b"]

    valores = []
    for etapa, dur in (("fetch", 3), ("merge", 1), ("pip", 20)):
        seg.etapa("a", etapa)
        for _ in range(4):
            r.t += dur / 4
            valores.append(seg.avance("a"))
    assert valores == sorted(valores)            # nunca retrocede
    assert 0.6 < valores[-1] < 0.97
    assert seg.avance("b") == 0.0                # sigue en cola

    seg.terminar("a")
    assert seg.activas() == ["b"]
    assert seg.etapa_de("a") == "listo"


def test_seguidor_no_retrocede_si_la_etapa_nueva_arranca_mas_abajo():
    r = Reloj()
    seg = SeguidorAvance(reloj=r)
    seg.etapa("x", "pip")
    r.t += 30
    alto = seg.avance("x")
    seg.etapa("x", "fetch")                      # (orden raro) no baja
    assert seg.avance("x") == pytest.approx(alto)


def test_seguidor_corrida_nueva_arranca_de_cero():
    r = Reloj()
    seg = SeguidorAvance(reloj=r)
    seg.etapa("x", "pip")
    r.t += 30
    assert seg.avance("x") > 0.6
    seg.terminar("x")
    seg.etapa("x", "fetch")                      # otra actualización después
    assert seg.avance("x") == pytest.approx(ETAPAS["fetch"][0])


def test_seguidor_desconocido_y_olvidar():
    seg = SeguidorAvance(reloj=Reloj())
    assert seg.avance("nada") == 0.0
    assert seg.etapa_de("nada") is None
    seg.terminar("nada")                         # no explota
    seg.olvidar("nada")
    assert seg.activas() == []
