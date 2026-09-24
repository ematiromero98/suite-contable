# -*- coding: utf-8 -*-
"""
conexiones_db.py — Página "Conexiones a base de datos" del launcher.

Organigrama simple de cómo está armado el backend del ERP: qué bases Supabase
hay, qué guarda cada una, qué apps se conectan a cada base y CÓMO (login
autenticado / conexión directa psycopg2 / Edge Function). Se dibuja con el mismo
QGraphicsView nativo del resto de la Suite (reusa los helpers de arquitectura.py).
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QGraphicsScene,
)

from arquitectura import (
    _Vista, _caja, _texto, _linea,
    BG, CARD, CARD2, BORDE, TXT, SUB, MENTA, LINEA,
)

# Colores por TIPO de conexión (leyenda).
C_LOGIN = MENTA        # anon key + login de la cuenta compartida (authenticated)
C_DIRECTO = "#f6b64b"  # psycopg2 directo (rol postgres: omite RLS; apps "admin")
C_EDGE = "#5bb0ff"     # Edge Function (service_role del lado servidor)

# ── Datos del organigrama (bases + apps + tipo de conexión) ─────────────────
#   tipo: "login" | "directo" | "edge"
BASES = [
    {
        "nombre": "ORDENES DE PAGO – BELGRANO", "ref": "zpwcc…", "emoji": "⭐",
        "tablas": "retenciones, órdenes de pago, facturas, DDJJ/IVA/CM03, contabilidad, juicios, padrones, VEP",
        "apps": [
            ("Órdenes de Pago", "directo"), ("Impuestos (IIBB + IVA)", "directo"),
            ("Contabilidad", "directo"), ("VEP Autónomos", "directo"),
            ("Facturador Monotributistas", "login"), ("suite-backups", "directo"),
            ("comprobantes-cel (web)", "edge"),
        ],
    },
    {
        "nombre": "COBRANZAS OSECAC", "ref": "rrarma…", "emoji": "💰",
        "tablas": "cobranzas, retenciones, facturas, usuarios, asientos",
        "apps": [("Cobranzas", "login"), ("Impuestos (lectura)", "login")],
    },
    {
        "nombre": "EMPLOYEE-PRO", "ref": "ffczb…", "emoji": "👥",
        "tablas": "empleados, sueldos, ausencias, qb_*, chcal_*",
        "apps": [
            ("Employee Pro", "login"), ("Calendario Ausencias", "login"),
            ("qb-dashboard (web)", "edge"), ("calendario-cel (web)", "edge"),
            ("chermisqui-control-dias (web)", "edge"),
        ],
    },
    {
        "nombre": "DEPOSITO AVALOS", "ref": "ioycu…", "emoji": "📦",
        "tablas": "productos, stock, inventarios, movimientos",
        "apps": [("Depósito Avalos", "login")],
    },
    {
        "nombre": "CONCILIADOR BANCARIO", "ref": "qaaxe…", "emoji": "🏦",
        "tablas": "movimientos, conciliaciones, asientos",
        "apps": [("Conciliador Bancario", "login")],
    },
]

_TIPO_COLOR = {"login": C_LOGIN, "directo": C_DIRECTO, "edge": C_EDGE}
_TIPO_LABEL = {"login": "login", "directo": "psycopg2", "edge": "Edge Fn"}

# Geometría
_BASE_X, _BASE_W = 40, 340
_APP_X, _APP_W, _APP_H, _APP_GAP = 500, 300, 30, 10
_BAND_GAP = 34


class PaginaConexionesDB(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{BG};")
        self._build()

    def _chip_leyenda(self, root, color, texto):
        c = QFrame()
        c.setFixedSize(14, 14)
        c.setStyleSheet(f"background:{color}; border-radius:4px;")
        root.addWidget(c)
        lbl = QLabel(texto)
        lbl.setStyleSheet(f"color:{SUB}; font-size:11px; margin-right:14px;")
        root.addWidget(lbl)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(6)

        tit = QLabel("🗄️  Conexiones a base de datos")
        tit.setStyleSheet(f"color:{TXT}; font-size:20px; font-weight:700;")
        lay.addWidget(tit)
        sub = QLabel("6 bases Supabase (Postgres, sa-east-1). Cada app se conecta a la suya. "
                     "Todas con RLS activado y auto-registro deshabilitado.")
        sub.setStyleSheet(f"color:{SUB}; font-size:11px;")
        lay.addWidget(sub)

        # Leyenda de tipos de conexión
        leg = QHBoxLayout()
        leg.setContentsMargins(0, 4, 0, 4)
        leg.setSpacing(6)
        self._chip_leyenda(leg, C_LOGIN, "login (anon + cuenta compartida, con RLS)")
        self._chip_leyenda(leg, C_DIRECTO, "psycopg2 directo (app admin, omite RLS)")
        self._chip_leyenda(leg, C_EDGE, "Edge Function (service_role del servidor)")
        leg.addStretch(1)
        lay.addLayout(leg)

        vista = _Vista()
        vista.setStyleSheet(f"border:1px solid {BORDE}; border-radius:12px; background:{CARD2};")
        scene = QGraphicsScene()
        self._dibujar(scene)
        vista.setScene(scene)
        lay.addWidget(vista, 1)

    def _dibujar(self, scene):
        y = 18
        for b in BASES:
            n = len(b["apps"])
            base_h = 108
            band_h = max(base_h, n * (_APP_H + _APP_GAP))
            base_y = y + (band_h - base_h) / 2

            # Tarjeta de la base
            _caja(scene, _BASE_X, base_y, _BASE_W, base_h, MENTA, relleno=CARD)
            _texto(scene, _BASE_X + 16, base_y + 12, f"{b['emoji']}  {b['nombre']}",
                   color=TXT, size=12, bold=True)
            _texto(scene, _BASE_X + 16, base_y + 36, f"Supabase · {b['ref']}",
                   color=SUB, size=9)
            _texto(scene, _BASE_X + 16, base_y + 54, b["tablas"], color=SUB, size=8,
                   w=_BASE_W - 30)
            _texto(scene, _BASE_X + 16, base_y + 84, "🔒 RLS activado · signups off",
                   color=MENTA, size=9, bold=True)

            base_mid = (_BASE_X + _BASE_W, base_y + base_h / 2)

            # Apps conectadas
            ay = y
            for nombre, tipo in b["apps"]:
                color = _TIPO_COLOR[tipo]
                _caja(scene, _APP_X, ay, _APP_W, _APP_H, color, radio=8, relleno=CARD)
                _texto(scene, _APP_X + 12, ay + 8, nombre, color=TXT, size=9, bold=True)
                _linea(scene, base_mid, (_APP_X, ay + _APP_H / 2),
                       color=color, ancho=2, etiqueta=_TIPO_LABEL[tipo])
                ay += _APP_H + _APP_GAP

            y += band_h + _BAND_GAP

        scene.setSceneRect(0, 0, _APP_X + _APP_W + 40, y + 20)
