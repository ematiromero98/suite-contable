# -*- coding: utf-8 -*-
"""
bases_datos.py — Pestaña «Bases de datos» del módulo 🗺 Arquitectura.

Dibuja cada proyecto Supabase como un bloque grande; adentro, sus schemas como
sub-cajas y, en cada schema, las apps que lo usan (chips clickeables). Abajo de
cada bloque van sus Edge Functions y buckets de Storage, y arriba la región, el
tamaño aproximado, si entra al backup semanal y lo que cuesta.

A la derecha, una explicación en lenguaje simple (qué es un proyecto, qué es un
schema, cómo se controla el acceso, cómo son los backups y cuánto cuesta). Al
tocar un proyecto, la explicación pasa a describir ese proyecto.

Mismo QGraphicsView nativo que el resto de la Suite (helpers de arquitectura.py):
sin dependencias nuevas, porque el ERP se auto-actualiza sin pip.

Estado relevado: oct-2026 (EMPLOYEE-PRO dado de baja y mudado al schema rrhh de la
base compartida; Chermisqui en el schema chermisqui). Si cambia algo, se edita
PROYECTOS_SUPA acá abajo.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QFontMetricsF, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QGraphicsScene, QTextBrowser,
)

from arquitectura import (
    _Vista, _caja, _texto, _parrafo, _label_ico, _emoji_item,
    BG, CARD, CARD2, BORDE, TXT, SUB, MENTA,
)

# ── Costos (org Pro de Supabase) ────────────────────────────────────────────
PLAN_PRO = 25          # US$/mes, plan de la organización
COMPUTO_PROY = 10      # US$/mes aprox. de cómputo por proyecto (instancia Micro)
CREDITO = 10           # US$/mes de crédito de cómputo incluido en el plan

# ── Datos ───────────────────────────────────────────────────────────────────
# Cada schema: (nombre, cantidad de tablas, qué guarda, [apps que lo usan]).
PROYECTOS_SUPA = [
    {
        "key": "compartida", "emoji": "⭐", "color": MENTA,
        "nombre": "ORDENES DE PAGO – BELGRANO", "apodo": "la base compartida",
        "ref": "zpwccecovhjmeibxafkg", "region": "sa-east-1 (São Paulo)",
        "tam": "~608 MB", "backup": "semanal · prioridad alta",
        "schemas": [
            ("public", 89,
             "Órdenes de Pago (pagos, facturas, ret_*, op_pagos, padrones) · Impuestos "
             "(cm03_*, iva_*, ddjj_*) · Contabilidad (cont_*) · Juicios (juicios_*) · "
             "VEP (arca_veps_*) · Facturador (facturador_*) · Factura Mono (fm_*) · "
             "bandejas de comprobantes-cel · suite_backup_runs · ia_uso",
             ["Órdenes de Pago", "Impuestos", "Contabilidad", "Control de Juicios",
              "VEP Autónomos", "Facturador", "Factura Mono (web)", "Comprobantes (web)",
              "Carga de Juicios (web)", "Backups (registro)"]),
            ("conciliador", 7, "Conciliaciones, movimientos y asientos del banco",
             ["Conciliador Bancario"]),
            ("rrhh", 26,
             "Employee Pro (empleados, legajos, datos salariales, objetivos, "
             "documentos…) + Calendario de Ausencias (cal_*)",
             ["Employee Pro", "Calendario de Ausencias", "Ausencias (web)"]),
            ("chermisqui", 17,
             "Webs de Chermisqui & Associates: QB Dashboard (qb_*), Taxes por "
             "trimestre (tx_*) y Control de días (chcal_*)",
             ["QB Dashboard (web)", "Taxes (web)", "Control de días (web)"]),
        ],
        "edge": ["comprobantes-cel", "juicio-abogado", "cal-ausencias", "qb-api",
                 "tx-api", "chcal-api"],
        "buckets": ["pdfs", "facturador", "contabilidad-adjuntos", "comprobantes",
                    "legajos", "cm03-ddjj", "cm03-insumos", "ddjj-salidas"],
        "texto": "Es el corazón del estudio. Acá viven casi todas las apps de la Suite "
                 "en el schema <i>public</i>, y por eso pueden cruzar datos entre ellas "
                 "(Impuestos concilia compras contra Órdenes de Pago, Contabilidad "
                 "devenga sobre lo mismo, el Facturador crea OP con una RPC). Desde "
                 "oct-2026 también aloja, en schemas propios, al Conciliador Bancario, "
                 "a RR.HH. (Employee Pro + Calendario de Ausencias, antes en el "
                 "proyecto EMPLOYEE-PRO, ya dado de baja) y a las webs de Chermisqui.",
    },
    {
        "key": "cobranzas", "emoji": "💰", "color": "#D68910",
        "nombre": "COBRANZAS OSECAC", "apodo": "la base de Cobranzas",
        "ref": "rrarmatjyvmrpohsvfzg", "region": "sa-east-1 (São Paulo)",
        "tam": "~20 MB", "backup": "semanal · prioridad alta",
        "schemas": [
            ("public", 9, "Cobranzas, retenciones sufridas, facturas, usuarios, asientos",
             ["Cobranzas", "Impuestos (lee)", "Contabilidad (lee)"]),
        ],
        "edge": [],
        "buckets": ["cobranzas"],
        "texto": "La usa Cobranzas (OSECAC), que guarda acá lo que baja del portal de "
                 "prestadores: cobranzas, retenciones y los PDF. Impuestos lee las "
                 "retenciones de IVA sufridas y Contabilidad importa las cobranzas, "
                 "pero sólo leen. Sigue separada de la compartida (la mudanza quedó "
                 "postergada).",
    },
    {
        "key": "deposito", "emoji": "📦", "color": "#A04000",
        "nombre": "DEPOSITO-AVALOS", "apodo": "la base del Depósito",
        "ref": "ioycuhefaalpqivhhryb", "region": "sa-east-1 (São Paulo)",
        "tam": "~17 MB", "backup": "semanal · prioridad media",
        "schemas": [
            ("public", 44,
             "Depósito Avalos (productos, stock, ingresos, egresos, inventarios, "
             "objetivos) + tablas u_* de Depósito Uniformes",
             ["Depósito Avalos", "Depósito Uniformes", "Depósito (web)"]),
        ],
        "edge": ["comprobante-cel"],
        "buckets": ["releases", "comprobantes"],
        "texto": "Base de los dos depósitos: Avalos (artículos de limpieza) y Uniformes "
                 "(tablas u_*). El stock se mueve sólo con RPC atómicas para que nunca "
                 "quede negativo. El bucket <i>releases</i> guarda los instaladores .exe "
                 "que usa el auto-update de Suite Depósitos.",
    },
    {
        "key": "payroll", "emoji": "🌎", "color": "#5bb0ff",
        "nombre": "AME-PAYROLL", "apodo": "Payroll US",
        "ref": "vswtxuvknxsjfodgviiq", "region": "us-west-1 (California)",
        "tam": "~14 MB", "backup": "semanal · prioridad alta (rol suite_backup)",
        "schemas": [
            ("public", 20, "ame-payroll: payroll de EE.UU. federal + California",
             ["ame-payroll"]),
            ("app", 17, "payroll-platform (Datatech de Chermisqui)",
             ["payroll-platform"]),
        ],
        "edge": [],
        "buckets": ["releases", "releases-archivo"],
        "texto": "Proyecto aparte, fuera de las 13 apps de la Suite: el payroll de "
                 "Estados Unidos. Está en us-west-1 porque los datos y los clientes son "
                 "de California. ame-payroll (escritorio) usa el schema public; "
                 "payroll-platform (API + web) usa su propio schema <i>app</i>.",
    },
    {
        "key": "casamiento", "emoji": "💍", "color": "#e58fb0",
        "nombre": "casamiento-matilara", "apodo": "Portal Clientes + casamiento",
        "ref": "nlnzryrwvbqigqzqkqqf", "region": "sa-east-1 (São Paulo)",
        "tam": "~23 MB", "backup": "semanal · opcional (prioridad baja)",
        "schemas": [
            ("public", 64, "App del casamiento + Portal Clientes (pc_*) y leads",
             ["Portal Clientes (web)", "casamiento-app"]),
        ],
        "edge": ["pc-* (~10, Portal Clientes)", "entregables-subir"],
        "buckets": ["casamiento", "portal-clientes", "entregables"],
        "texto": "Proyecto aparte, fuera de la Suite. Nació para la app del casamiento "
                 "y hoy también aloja el Portal Clientes (tablas pc_*, sus Edge "
                 "Functions pc-* y el bucket de entregables). No se borra hasta después "
                 "del casamiento.",
    },
]

# Geometría del diagrama
_W = 1000               # ancho de la escena
_M = 24                 # margen izquierdo
_PAD = 16               # padding interno de cada bloque


def costo_total(n_proyectos):
    return PLAN_PRO + COMPUTO_PROY * n_proyectos - CREDITO


def _ancho_texto(s, size=9, bold=False):
    f = QFont("Segoe UI", size)
    f.setBold(bold)
    return QFontMetricsF(f).horizontalAdvance(s)


class PaginaBasesDatos(QWidget):
    """Diagrama de proyectos Supabase → schemas → apps + explicación al costado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{BG};")
        self._build()
        self._dibujar()
        self._explicacion_general()

    # ------------------------------------------------------------ layout
    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.vista = _Vista()
        self.vista.on_nodo = self._on_nodo
        self.vista.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self.vista, stretch=1)
        self.info = QTextBrowser()
        self.info.setOpenExternalLinks(False)
        self.info.setStyleSheet(
            f"QTextBrowser{{background:{CARD2}; border:none; border-left:1px solid {BORDE};"
            f"color:{TXT}; font-size:12px; padding:16px;}}")
        self.info.setFixedWidth(360)
        lay.addWidget(self.info)

    def _ajustar(self):
        """Encaja el ANCHO del diagrama en la vista (el alto se recorre con scroll)."""
        sc = self.vista.scene()
        if sc is None:
            return
        vw = self.vista.viewport().width()
        if vw <= 0:
            return
        f = max(0.4, min(1.15, (vw - 4) / sc.sceneRect().width()))
        self.vista.resetTransform()
        self.vista.scale(f, f)
        self.vista._zoom = 1.0
        self.vista.verticalScrollBar().setValue(0)      # arrancar arriba

    def showEvent(self, e):
        super().showEvent(e)
        self._ajustar()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._ajustar()

    # ------------------------------------------------------------ diagrama
    def _chips(self, sc, x0, y0, ancho, etiquetas, color, key_fn, size=9,
               relleno="#101a22"):
        """Chips en flujo (saltan de línea al llegar a `ancho`). Devuelve el alto."""
        x, y, alto = x0, y0, 24
        for et in etiquetas:
            w = _ancho_texto(et, size) + 20
            if x > x0 and x + w > x0 + ancho:
                x = x0
                y += alto + 6
            caja = _caja(sc, x, y, w, alto, color, radio=12, relleno=relleno, ancho=1)
            k = key_fn(et)
            if k:
                caja.setData(0, k)
                caja.setCursor(Qt.CursorShape.PointingHandCursor)
            t = _texto(sc, x + 10, y + 4, et, color=TXT, size=size)
            if k:
                t.setData(0, k)
            x += w + 6
        return (y + alto) - y0

    def _dibujar(self):
        sc = QGraphicsScene()
        self.vista.setScene(sc)
        n = len(PROYECTOS_SUPA)

        _label_ico(sc, _M, 12, "🗄️", "Bases de datos — proyectos Supabase",
                   color=TXT, size=15, bold=True, epx=22)
        _texto(sc, _M, 44, "Proyecto → schemas → apps. Tocá un proyecto (o una app) "
               "para ver su explicación a la derecha.", color=SUB, size=10)

        # Resumen de costo
        cy = 72
        _caja(sc, _M, cy, _W - 2 * _M, 56, "#2b6b52", radio=10, relleno="#12202b")
        _texto(sc, _M + 16, cy + 9,
               f"Costo: plan Pro US${PLAN_PRO} + ~US${COMPUTO_PROY}/mes de cómputo por "
               f"proyecto − US${CREDITO} de crédito incluido  →  {n} proyectos ≈ "
               f"US${costo_total(n)}/mes", color="#bfe9d5", size=11, bold=True)
        _texto(sc, _M + 16, cy + 33,
               f"Antes eran 6 (≈ US${costo_total(6)}/mes) y en sep-2026 eran 8 "
               f"(≈ US${costo_total(8)}/mes). Cada proyecto que se une a otro ahorra "
               f"~US${COMPUTO_PROY}/mes.", color=SUB, size=9)

        y = cy + 56 + 22
        ancho_bloque = _W - 2 * _M
        for p in PROYECTOS_SUPA:
            y = self._dibujar_proyecto(sc, p, _M, y, ancho_bloque) + 20

        sc.setSceneRect(0, 0, _W, y)

    def _dibujar_proyecto(self, sc, p, x, y, ancho):
        key = "proj:" + p["key"]
        col = p["color"]
        items_bloque = []

        # Encabezado
        hdr = []
        hdr.append(_texto(sc, x + 50, y + 12, p["nombre"], color=TXT, size=13, bold=True))
        hdr.append(_texto(sc, x + 50, y + 34, f"{p['ref']}  ·  {p['apodo']}",
                          color=SUB, size=9))
        hdr.append(_emoji_item(sc, x + 14, y + 14, p["emoji"], 26, key=key))
        # Sin emojis en el texto de la escena: la fuente base no trae glifos de
        # color (saldrían como «tofu»); los emojis van como pixmap (_emoji_item).
        meta = (f"Región {p['region']}   ·   {p['tam']}   ·   backup {p['backup']}   ·   "
                f"~US${COMPUTO_PROY}/mes")
        hdr.append(_texto(sc, x + 16, y + 58, meta, color="#bfe9d5", size=9))
        items_bloque += hdr

        # Schemas: en filas. Un schema con muchas apps (≥ 5) ocupa una fila entera
        # (si no, sus chips quedarían en una columna angosta y muy alta); el
        # resto se reparte hasta 3 por fila.
        filas, actual = [], []
        for sch in p["schemas"]:
            if len(sch[3]) >= 5:
                if actual:
                    filas.append(actual)
                    actual = []
                filas.append([sch])
            else:
                actual.append(sch)
                if len(actual) == 3:
                    filas.append(actual)
                    actual = []
        if actual:
            filas.append(actual)

        gap = 12
        fila_y = y + 84
        for fila in filas:
            cols = len(fila)
            sw = (ancho - 2 * _PAD - gap * (cols - 1)) / cols
            fila_h = 0
            cajas = []
            for c, (nom, n_tab, desc, apps) in enumerate(fila):
                sx = x + _PAD + c * (sw + gap)
                t1 = _texto(sc, sx + 12, fila_y + 10, f"schema {nom}", color=col,
                            size=11, bold=True)
                t2 = _texto(sc, sx + 12 + _ancho_texto(f"schema {nom}", 11, True) + 10,
                            fila_y + 13, f"{n_tab} tablas", color=SUB, size=9)
                par = _parrafo(sc, sx + 8, fila_y + 32, desc, sw - 16, color=SUB, size=8)
                ph = par.boundingRect().height()
                ch = self._chips(sc, sx + 12, fila_y + 38 + ph, sw - 24, apps, col,
                                 lambda et, pk=p["key"]: f"app:{pk}:{et}", size=9)
                h = 38 + ph + ch + 12
                caja = _caja(sc, sx, fila_y, sw, h, "#2e3a4d", radio=10, relleno=CARD2,
                             ancho=1)
                caja.setZValue(-0.5)
                for it in (t1, t2, par, caja):
                    it.setData(0, key)
                cajas.append(caja)
                fila_h = max(fila_h, h)
            for caja in cajas:                 # mismo alto para toda la fila
                self._alto_caja(caja, fila_h)
            fila_y += fila_h + gap
        fila_y -= gap
        fila_h = 0
        yy = fila_y + fila_h + 14

        # Edge Functions y buckets
        for etiqueta, lista, color in (("Edge Functions", p["edge"], "#5bb0ff"),
                                       ("Buckets de Storage", p["buckets"], "#f6c66b")):
            lbl = _texto(sc, x + _PAD, yy + 4, etiqueta + ":", color=TXT, size=9, bold=True)
            lbl.setData(0, key)
            if lista:
                h = self._chips(sc, x + _PAD + 150, yy, ancho - 2 * _PAD - 150, lista,
                                color, lambda et: key, size=8, relleno="#141a24")
            else:
                _texto(sc, x + _PAD + 150, yy + 4, "— ninguna —", color=SUB, size=9)
                h = 24
            yy += h + 8

        alto = yy - y + 6
        bloque = _caja(sc, x, y, ancho, alto, col, radio=14, relleno=CARD, ancho=2)
        bloque.setZValue(-1)
        bloque.setData(0, key)
        bloque.setCursor(Qt.CursorShape.PointingHandCursor)
        for it in items_bloque:
            it.setData(0, key)
        return y + alto

    @staticmethod
    def _alto_caja(caja, h):
        """Re-dibuja la sub-caja del schema con el alto final de la fila."""
        r = caja.path().boundingRect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(r.x(), r.y(), r.width(), h), 10, 10)
        caja.setPath(path)

    # ------------------------------------------------------------ interacción
    def _on_nodo(self, key):
        if not isinstance(key, str):
            return
        if key.startswith("proj:"):
            self.mostrar_proyecto(key[5:])
        elif key.startswith("app:"):
            _, pk, app = key.split(":", 2)
            self.mostrar_proyecto(pk, app)

    def mostrar_proyecto(self, pk, app=None):
        p = next((x for x in PROYECTOS_SUPA if x["key"] == pk), None)
        if p is None:
            return
        sch = ""
        for nom, n_tab, desc, apps in p["schemas"]:
            marca = ""
            if app and app in apps:
                marca = (f"<br><span style='color:{MENTA}'>▶ {app} usa este schema</span>")
            sch += (f"<li style='margin-bottom:6px'><b style='color:{p['color']}'>{nom}</b> "
                    f"<span style='color:{SUB}'>({n_tab} tablas)</span><br>"
                    f"<span style='color:{SUB};font-size:11px'>{desc}</span><br>"
                    f"<span style='font-size:11px'>Apps: {', '.join(apps)}</span>{marca}</li>")
        edge = ", ".join(p["edge"]) or "ninguna"
        buckets = ", ".join(p["buckets"]) or "ninguno"
        sel = (f"<p style='background:#1d3b30;color:{MENTA};padding:6px;font-size:12px'>"
               f"Seleccionaste <b>{app}</b>.</p>") if app else ""
        self.info.setHtml(f"""
        <div style='color:{TXT}'>
        <h2 style='color:{p['color']};margin:0 0 4px'>
        <span style='font-size:15px'>&#9679;</span> {p['nombre']}</h2>
        <p style='color:{SUB};font-size:11px;margin:0 0 10px'>ref {p['ref']}</p>
        {sel}
        <p style='font-size:12px;margin:0 0 10px'>{p['texto']}</p>
        <table style='font-size:12px;color:{SUB}' cellspacing='0' cellpadding='2'>
        <tr><td>Región</td><td style='color:{TXT}'>{p['region']}</td></tr>
        <tr><td>Tamaño</td><td style='color:{TXT}'>{p['tam']}</td></tr>
        <tr><td>Backup</td><td style='color:{TXT}'>{p['backup']}</td></tr>
        <tr><td>Costo</td><td style='color:{TXT}'>~US${COMPUTO_PROY}/mes de cómputo</td></tr>
        </table>
        <h3 style='color:{TXT};margin:12px 0 4px'>Schemas</h3>
        <ul style='font-size:12px;padding-left:16px;margin:0'>{sch}</ul>
        <h3 style='color:{TXT};margin:12px 0 4px'>Edge Functions</h3>
        <p style='color:{SUB};font-size:12px;margin:0'>{edge}</p>
        <h3 style='color:{TXT};margin:12px 0 4px'>Buckets de Storage</h3>
        <p style='color:{SUB};font-size:12px;margin:0'>{buckets}</p>
        <p style='font-size:11px;margin-top:14px'>
        <a href='#general' style='color:{MENTA}'>← Volver a la explicación general</a></p>
        </div>""")

    def _on_link(self, url):
        if url.toString().endswith("#general"):
            self._explicacion_general()

    def _explicacion_general(self):
        if not getattr(self, "_link_ok", False):
            self.info.setOpenLinks(False)
            self.info.anchorClicked.connect(self._on_link)
            self._link_ok = True
        n = len(PROYECTOS_SUPA)
        filas = "".join(
            f"<tr><td style='padding:2px 8px 2px 0;color:{p['color']};font-size:14px'>&#9679;</td>"
            f"<td style='padding:2px 0'><b>{p['nombre']}</b> "
            f"<span style='color:{SUB};font-size:11px'>· {p['tam']} · {p['region'].split(' ')[0]}"
            f"</span></td></tr>"
            for p in PROYECTOS_SUPA)
        self.info.setHtml(f"""
        <div style='color:{TXT}'>
        <h2 style='color:{MENTA};margin:0 0 6px'>Cómo se guardan los datos</h2>
        <table style='font-size:12px'>{filas}</table>

        <h3 style='color:{TXT};margin:12px 0 4px'>¿Qué es un proyecto Supabase?</h3>
        <p style='color:{SUB};font-size:12px;margin:0'>
        Es una base de datos Postgres en la nube, con su propia dirección, sus
        usuarios, su almacenamiento de archivos (Storage) y sus funciones del lado
        del servidor (Edge Functions). Cada proyecto corre en su propia máquina y
        por eso cuesta aparte.</p>

        <h3 style='color:{TXT};margin:12px 0 4px'>¿Qué es un schema?</h3>
        <p style='color:{SUB};font-size:12px;margin:0'>
        Es una «carpeta» de tablas dentro de la misma base. Cada app grande tiene el
        suyo (<i>conciliador</i>, <i>rrhh</i>, <i>chermisqui</i>, <i>app</i>) para que
        no choquen nombres de tabla (dos apps pueden tener una tabla
        «empleados» sin pisarse) y para que quede ordenado qué es de quién. Así
        varias apps comparten un proyecto —y su costo— sin mezclarse.</p>

        <h3 style='color:{TXT};margin:12px 0 4px'>¿Cómo se controla el acceso?</h3>
        <ul style='color:{SUB};font-size:12px;margin:0;padding-left:16px'>
        <li><b style='color:{TXT}'>RLS + login</b>: todas las tablas tienen RLS
        (seguridad por fila). Las apps entran con la clave pública y el login de la
        cuenta compartida del estudio; sin login no ven nada. El auto-registro está
        apagado.</li>
        <li><b style='color:{TXT}'>Conexión directa</b>: las apps «admin»
        (Órdenes de Pago, Impuestos, Contabilidad, VEP) y los backups se conectan a
        Postgres con psycopg2/pg_dump usando credenciales que viven en el .env, nunca
        en el código.</li>
        <li><b style='color:{TXT}'>Edge Functions</b>: las webs del celular (GitHub
        Pages) no tienen ninguna clave; le hablan a una función del servidor
        protegida por PIN, y es esa función la que usa la clave service_role.</li>
        </ul>

        <h3 style='color:{TXT};margin:12px 0 4px'>Backups</h3>
        <p style='color:{SUB};font-size:12px;margin:0'>
        Todos los domingos 22:00 la app <b>Backups</b> (suite-backups) hace un
        pg_dump de cada proyecto + baja sus archivos de Storage, lo empaqueta en un
        ZIP cifrado (AES-256), lo copia a OneDrive y guarda 8 semanas. Cada corrida
        queda en <i>suite_backup_runs</i> y se ve en «Registro de Backups».</p>

        <h3 style='color:{TXT};margin:12px 0 4px'>Costo</h3>
        <p style='color:{SUB};font-size:12px;margin:0'>
        Plan Pro US${PLAN_PRO}/mes + ~US${COMPUTO_PROY}/mes de cómputo por proyecto,
        con US${CREDITO} de crédito incluido: <b style='color:{TXT}'>{n} proyectos ≈
        US${costo_total(n)}/mes</b>. Antes eran 6 (≈ US${costo_total(6)}) y en
        sep-2026 eran 8 (≈ US${costo_total(8)}). Por eso se unen proyectos en schemas.</p>

        <p style='color:{SUB};font-size:11px;margin-top:12px'>
        Tocá un proyecto del diagrama para ver su detalle.</p>
        </div>""")
