# -*- coding: utf-8 -*-
"""Tests de la Suite: raíz del repo en sys.path y Qt sin pantalla."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# El plugin offscreen en Windows no encuentra las fuentes del sistema por su
# cuenta: sin esto mide el texto con métricas de reemplazo (tarjetas y leyendas
# más anchas de lo real) y los tests de ancho dan falsos fallos.
if sys.platform == "win32" and os.path.isdir(r"C:\Windows\Fonts"):
    os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
