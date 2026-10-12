# -*- coding: utf-8 -*-
"""Tests de la Suite: raíz del repo en sys.path y Qt sin pantalla."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
