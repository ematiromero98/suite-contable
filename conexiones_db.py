# -*- coding: utf-8 -*-
"""
conexiones_db.py — Página "Conexiones a base de datos" del launcher.

Organigrama simple de cómo está armado el backend del ERP: qué bases Supabase
hay, qué guarda cada una, qué apps se conectan a cada base y CÓMO (login
autenticado / conexión directa psycopg2 / Edge Function). Se dibuja con el mismo
QGraphicsView nativo del resto de la Suite (reusa los helpers de arquitectura.py).
"""
from __future__ import annotations

from PyQt6.QtGui import QFont, QFontMetricsF
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QGraphicsScene,
)

from arquitectura import (
    _Vista, _caja, _texto, _linea, _parrafo,
    BG, CARD, CARD2, BORDE, TXT, SUB, MENTA,
)

# Colores por TIPO de conexión (leyenda).
C_LOGIN = MENTA        # anon key + login de la cuenta compartida (authenticated)
C_DIRECTO = "#f6b64b"  # psycopg2 directo (rol postgres: omite RLS; apps "admin")
C_EDGE = "#5bb0ff"     # Edge Function (service_role del lado servidor)
C_REST = "#c39bff"     # REST con una API key, sin login de usuario

# ── Datos del organigrama (bases + apps + tipo de conexión) ─────────────────
#   tipo: "login" | "directo" | "edge" | "rest"
#   Estado 12-oct-2026: EMPLOYEE-PRO se dio de baja y DEPOSITO-AVALOS quedó
#   congelado; RR.HH., Chermisqui y el Depósito viven en la base compartida, cada
#   uno en su schema (rrhh / chermisqui / deposito).
BASES = [
    {
        "nombre": "ORDENES DE PAGO – BELGRANO", "ref": "zpwcc…", "emoji": "⭐",
        "tablas": "public: OP, retenciones, DDJJ/IVA/CM03, contabilidad, juicios, VEP, facturador · "
                  "schemas conciliador, rrhh, chermisqui y deposito (Avalos + u_* de Uniformes)",
        "apps": [
            ("Órdenes de Pago", "directo"), ("Impuestos (IIBB + IVA)", "directo"),
            ("Contabilidad", "directo"), ("VEP Autónomos", "directo"),
            ("Facturador Monotributistas", "login"), ("Conciliador Bancario", "login"),
            ("Employee Pro (schema rrhh)", "login"),
            ("Calendario Ausencias (schema rrhh)", "login"),
            ("Depósito Avalos (schema deposito)", "login"),
            ("Depósito Uniformes (schema deposito)", "login"),
            ("comprobantes-cel (web)", "edge"), ("juicios-carga (web)", "edge"),
            ("calendario-cel (web)", "edge"),
            ("deposito-comprobantes (web)", "edge"),
            ("qb-dashboard + /taxes (web)", "edge"),
            ("chermisqui-control-dias (web)", "edge"),
            ("suite-backups (pg_dump)", "directo"),
        ],
    },
    {
        "nombre": "COBRANZAS OSECAC", "ref": "rrarma…", "emoji": "💰",
        "tablas": "cobranzas, retenciones, facturas, usuarios, asientos",
        "apps": [("Cobranzas", "login"), ("Impuestos (lectura)", "login"),
                 ("Contabilidad (lectura)", "rest"), ("suite-backups (pg_dump)", "directo")],
    },
    {
        "nombre": "AME-PAYROLL (US)", "ref": "vswtx…", "emoji": "🌎",
        "tablas": "public: ame-payroll (payroll federal + CA) · schema app: payroll-platform",
        "apps": [("ame-payroll (escritorio)", "login"),
                 ("payroll-platform (API)", "directo"),
                 ("payroll-platform (web, sólo auth)", "login"),
                 ("suite-backups (rol suite_backup)", "directo")],
    },
    {
        "nombre": "casamiento-matilara", "ref": "nlnzr…", "emoji": "💍",
        "tablas": "app del casamiento + Portal Clientes (pc_*, leads)",
        "apps": [("Portal Clientes (web)", "login"), ("Portal Clientes (pc-* Edge)", "edge"),
                 ("casamiento-app (fotos/tesoro)", "rest"),
                 ("suite-backups (opcional)", "directo")],
    },
]

_TIPO_COLOR = {"login": C_LOGIN, "directo": C_DIRECTO, "edge": C_EDGE, "rest": C_REST}
_TIPO_LABEL = {"login": "login", "directo": "SQL directo", "edge": "Edge Fn", "rest": "REST key"}

# Geometría
_BASE_X, _BASE_W = 40, 380
_APP_X, _APP_W, _APP_H, _APP_GAP = 560, 360, 30, 10
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
        sub = QLabel(f"{len(BASES)} bases Supabase (Postgres; {len(BASES) - 1} en sa-east-1 y "
                     "Payroll US en us-west-1). Cada app se conecta a la suya. Todas con RLS "
                     "activado y auto-registro deshabilitado. (DEPOSITO-AVALOS, ioycu…, quedó "
                     "congelado tras mudarse al schema deposito y se borra tras la gracia.)")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color:{SUB}; font-size:11px;")
        lay.addWidget(sub)

        # Leyenda de tipos de conexión
        leg = QHBoxLayout()
        leg.setContentsMargins(0, 4, 0, 4)
        leg.setSpacing(6)
        self._chip_leyenda(leg, C_LOGIN, "login (anon + cuenta compartida, con RLS)")
        self._chip_leyenda(leg, C_DIRECTO, "SQL directo (psycopg2 / pg_dump; app admin, omite RLS)")
        self._chip_leyenda(leg, C_EDGE, "Edge Function (service_role del servidor)")
        self._chip_leyenda(leg, C_REST, "REST con API key (sin login)")
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
            # Primero el párrafo de tablas (puede ocupar 1-3 líneas) para saber
            # cuánto mide la tarjeta de la base.
            par = _parrafo(scene, 0, 0, b["tablas"], _BASE_W - 24, color=SUB, size=8)
            par_h = par.boundingRect().height()
            base_h = 50 + par_h + 30
            band_h = max(base_h, n * (_APP_H + _APP_GAP) - _APP_GAP)
            base_y = y + (band_h - base_h) / 2
            par.setPos(_BASE_X + 12, base_y + 48)
            par.setZValue(1)

            # Tarjeta de la base
            _caja(scene, _BASE_X, base_y, _BASE_W, base_h, MENTA, relleno=CARD)
            _texto(scene, _BASE_X + 16, base_y + 12, f"{b['emoji']}  {b['nombre']}",
                   color=TXT, size=12, bold=True)
            _texto(scene, _BASE_X + 16, base_y + 34, f"Supabase · {b['ref']}",
                   color=SUB, size=9)
            _texto(scene, _BASE_X + 16, base_y + base_h - 26, "🔒 RLS activado · signups off",
                   color=MENTA, size=9, bold=True)

            base_mid = (_BASE_X + _BASE_W, base_y + base_h / 2)

            # Apps conectadas
            ay = y + (band_h - (n * (_APP_H + _APP_GAP) - _APP_GAP)) / 2
            for nombre, tipo in b["apps"]:
                color = _TIPO_COLOR[tipo]
                _caja(scene, _APP_X, ay, _APP_W, _APP_H, color, radio=8, relleno=CARD)
                _texto(scene, _APP_X + 12, ay + 8, nombre, color=TXT, size=9, bold=True)
                # El tipo de conexión va adentro de la caja, a la derecha (en el
                # medio de la línea se amontonaba con muchas apps).
                et = _TIPO_LABEL[tipo]
                ew = QFontMetricsF(QFont("Segoe UI", 8)).horizontalAdvance(et)
                _texto(scene, _APP_X + _APP_W - ew - 12, ay + 9, et, color=color, size=8)
                _linea(scene, base_mid, (_APP_X, ay + _APP_H / 2), color=color, ancho=2)
                ay += _APP_H + _APP_GAP

            y += band_h + _BAND_GAP

        scene.setSceneRect(0, 0, _APP_X + _APP_W + 40, y + 20)
