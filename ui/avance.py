# -*- coding: utf-8 -*-
"""
ui/avance.py — Avance DERIVADO POR ETAPAS de una instalación/actualización.

Ni `git fetch`/`git clone` (con `capture_output`) ni `pip install` dan un % real
que podamos leer sin cambiar cómo se actualiza. Lo que sí sabemos es en qué
ETAPA está cada app, porque `_actualizar_app_core` / `_pip_update` /
`_instalar_app` avisan al entrar en cada una. A cada etapa le corresponde un
tramo del 0-100 %:

    cola     0 %          (esperando su turno: el worker actualiza de a una)
    fetch    2 → 40 %     bajar el código (git fetch)          «descargando…»
    merge   40 → 50 %     aplicarlo (merge --ff-only / reset)  «aplicando…»
    venv    50 → 60 %     crear el .venv si falta              «preparando…»
    pip     60 → 97 %     pip install -r requirements.txt      «dependencias…»
    clonar   3 → 90 %     instalar: git clone                  «descargando…»
    listo  100 %          terminó (ok / aviso / instalada)     «actualizada»

Dentro de un tramo el avance se acerca al techo con una curva asintótica
(1 − e^(−t/τ)): se mueve siempre, desacelera y NUNCA llega al techo hasta que
la etapa siguiente lo confirma, así la barra no «miente» un 100 % ni queda
congelada mientras pip trabaja. El avance es monótono (no retrocede nunca).

Sin Qt: lo usan los tests sin GUI y el launcher (que sólo le pide números).
"""
import math
import time

# etapa -> (inicio, techo, leyenda, tau_segundos)
ETAPAS = {
    "cola":   (0.00, 0.00, "en cola", 1.0),
    "fetch":  (0.02, 0.40, "descargando…", 4.0),
    "merge":  (0.40, 0.50, "aplicando…", 1.5),
    "venv":   (0.50, 0.60, "preparando…", 8.0),
    "pip":    (0.60, 0.97, "dependencias…", 12.0),
    "clonar": (0.03, 0.90, "descargando…", 10.0),
    "listo":  (1.00, 1.00, "actualizada", 1.0),
}

# Estado final (lo que devuelve `_actualizar_app_core` / `_instalar_app`) ->
# (tipo visual, leyenda debajo del ícono).
FINALES = {
    "ok":        ("ok", "actualizada"),
    "instalada": ("ok", "instalada"),
    "aviso":     ("aviso", "con aviso"),
    "saltada":   ("error", "no instalada"),
    "error":     ("error", "error"),
}


def leyenda(etapa):
    """Texto corto que va debajo del ícono para una etapa."""
    return ETAPAS.get(etapa, ETAPAS["fetch"])[2]


def avance_en_etapa(etapa, segundos):
    """Fracción 0..1 estimada tras `segundos` dentro de `etapa`. Asintótica:
    arranca en el inicio del tramo y tiende al techo sin alcanzarlo."""
    ini, techo, _ley, tau = ETAPAS.get(etapa, ETAPAS["fetch"])
    if techo <= ini:
        return ini
    s = max(0.0, float(segundos))
    return ini + (techo - ini) * (1.0 - math.exp(-s / tau))


def final(estado):
    """(tipo, leyenda) para un estado final; desconocido = error."""
    return FINALES.get(estado, FINALES["error"])


class SeguidorAvance:
    """Lleva la etapa y el avance de varias apps a la vez (por `key`).

    El reloj es inyectable (`reloj`) para testear sin esperar."""

    def __init__(self, reloj=time.monotonic):
        self._reloj = reloj
        self._apps = {}     # key -> {"etapa", "t0", "max"}

    def etapa(self, key, etapa):
        """Marca que `key` entró en `etapa` (reinicia el reloj del tramo)."""
        d = self._apps.get(key)
        # Una corrida nueva (entra en cola, o venía de 'listo') arranca de 0;
        # dentro de la misma corrida el avance nunca retrocede.
        nueva = d is None or d["etapa"] == "listo" or etapa == "cola"
        prev = 0.0 if nueva else d["max"]
        self._apps[key] = {"etapa": etapa, "t0": self._reloj(), "max": prev}

    def activas(self):
        """Keys en curso (con etapa distinta de 'listo')."""
        return [k for k, d in self._apps.items() if d["etapa"] != "listo"]

    def etapa_de(self, key):
        d = self._apps.get(key)
        return d["etapa"] if d else None

    def avance(self, key):
        """Fracción 0..1 actual de `key` (monótona). 0 si no se conoce."""
        d = self._apps.get(key)
        if not d:
            return 0.0
        a = avance_en_etapa(d["etapa"], self._reloj() - d["t0"])
        if d["etapa"] == "cola":
            a = 0.0
        d["max"] = max(d["max"], a)
        return d["max"]

    def terminar(self, key):
        """La app terminó (bien o mal): sale de las activas."""
        d = self._apps.setdefault(key, {"etapa": "listo", "t0": 0.0, "max": 0.0})
        d["etapa"] = "listo"

    def olvidar(self, key):
        self._apps.pop(key, None)
