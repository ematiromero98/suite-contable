# -*- coding: utf-8 -*-
"""
arquitectura.py — Módulo "🗺️ Arquitectura" del ERP.

Muestra, DENTRO del launcher, un diagrama navegable y dinámico de:
  • la Suite completa (el ERP + las 8 apps + las bases Supabase + los sistemas
    externos como ARCA, OSECAC y el Drive), y
  • cada proyecto por separado (capas UI / Lógica / Datos / Integraciones), con
    una explicación en lenguaje simple y el flujo del caso de uso principal
    reproducible paso a paso.

Todo se dibuja con QGraphicsView NATIVO (sin dependencias nuevas: el ERP se
auto-actualiza sin pip). Los datos viven en DATOS, abajo — una sola fuente de
verdad para el diagrama y el texto. Si cambia una app, se edita acá.
"""
from PyQt6.QtCore import Qt, QRectF, QTimer, QPointF
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QPainterPath, QPixmap, QIcon,
)
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsPathItem,
    QGraphicsPixmapItem,
    QListWidget, QListWidgetItem, QTextBrowser, QPushButton, QLabel, QFrame,
    QLineEdit,
)

# ----------------------------------------------------------------- paleta
BG = "#0f1218"
CARD = "#1a2130"
CARD2 = "#151b27"
BORDE = "#2a3446"
TXT = "#eef2f8"
SUB = "#8a94a6"
MENTA = "#3ddc97"
LINEA = "#3a4658"

# La fuente base ("Segoe UI") no trae glifos de color: los emojis salían como
# "tofu". Los dibujamos a un QPixmap con la fuente de emoji de Windows.
_EMOJI_FONT = "Segoe UI Emoji"


def _emoji_pixmap(emoji, size):
    """Emoji a color en un QPixmap transparente (size px físicos, sin dpr)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    f = QFont(_EMOJI_FONT)
    f.setPixelSize(int(size * 0.84))
    p.setFont(f)
    p.setPen(QColor("#ffffff"))            # sólo aplica al fallback monocromo
    p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, emoji)
    p.end()
    return pm


def _emoji_item(scene, x, y, emoji, px=18, key=None):
    """Agrega un emoji (como pixmap a color) a la escena en (x, y)."""
    it = QGraphicsPixmapItem(_emoji_pixmap(emoji, px * 2))
    it.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
    it.setScale(0.5)
    it.setPos(x, y)
    if key is not None:
        it.setData(0, key)
    scene.addItem(it)
    return it


def _emoji_icon(emoji, px=18):
    """QIcon con el emoji a color (para los items de la lista de la izquierda)."""
    return QIcon(_emoji_pixmap(emoji, px * 2))


# ================================================================= DATOS
# Colores por app (los mismos del launcher). Cada proyecto trae lo justo para
# dibujar su diagrama de capas y explicarlo.
SUPA_COMPARTIDA = "Supabase «ORDENES DE PAGO» (zpwccecovhjmeibxafkg)"
SUPA_COBRANZAS = "Supabase Cobranzas (rrarmatjyvmrpohsvfzg)"
SUPA_EMPLOYEE = "Supabase Employee (ffczbimnuodzcbgsdxbx)"
SUPA_DEPOSITO = "Supabase Depósito (ioycuhefaalpqivhhryb)"
SUPA_CONCILIADOR = "Supabase Conciliador (qaaxestmwmqmylthnwts)"

PROYECTOS = {
    "erp": {
        "nombre": "Suite Contable (ERP)", "emoji": "🖥️", "color": "#3ddc97",
        "proposito": "Es el «menú de inicio» del estudio: una sola ventana desde "
                     "la que se abren, instalan y actualizan las 8 apps. No toca "
                     "datos; sólo lanza cada programa y lo mantiene al día y con "
                     "sus credenciales puestas.",
        "stack": "Python + PyQt6. Usa git y gh (GitHub CLI) y rclone (Google Drive) "
                 "como procesos externos. Sin base de datos propia.",
        "entrypoint": "Suite Contable.bat → pythonw main.py",
        "datos": "No usa base de datos. Reparte credenciales a las apps.",
        "capas": [
            ("Ventana (PyQt6)", ["main.py — launcher, tarjetas por app, KPIs"]),
            ("Config", ["config.py — registro de las 8 apps (ruta, repo, versión)"]),
            ("Servicios", ["credenciales.py — baja el .env y los secretos del Drive",
                            "release.py — publica versiones", "version.py"]),
            ("Core compartido", ["suite_theme.py — tema visual",
                                   "suite_charts.py — gráficos", "formatos.py — $ y CUIT",
                                   "arquitectura.py — este módulo"]),
        ],
        "integraciones": ["git / gh (auto-update y clone)", "GitHub Releases",
                           "Google Drive vía rclone (credenciales)"],
        "flujo": [
            "El usuario abre el ERP; en segundo plano se auto-actualiza (git pull).",
            "Chequea la última versión de cada app en GitHub y avisa en su tarjeta.",
            "Si falta el .env, ofrece traer las credenciales del Drive (OAuth 1 vez).",
            "El usuario toca «Abrir» y el ERP lanza esa app en su carpeta.",
            "O toca «Actualizar»: git pull + reinstala dependencias en su .venv.",
        ],
    },
    "reten": {
        "nombre": "RetencionesPro", "emoji": "🧾", "color": "#1E8E4E",
        "proposito": "Liquida los pagos a proveedores con sus retenciones "
                     "(Ganancias, IVA, IIBB), genera las Órdenes de Pago con PDF y "
                     "certificados, arma los archivos fiscales (SICORE, ARBA, AGIP) "
                     "y concilia compras contra ARCA.",
        "stack": "Python + PyQt6. Se conecta a Postgres DIRECTO con psycopg2 (pool) "
                 "+ Storage. reportlab (PDF), selenium (SIRE/Tango), keyring.",
        "entrypoint": "run.bat → python main.py",
        "datos": SUPA_COMPARTIDA + " · tablas pagos, facturas, ret_* · bucket pdfs",
        "capas": [
            ("UI (PyQt6)", ["main_window.py", "form_orden.py (Nueva OP)",
                             "reportes_fiscales.py", "conciliacion.py", "pasar_pagos.py (QR)"]),
            ("Lógica", ["calculos.py (retenciones)", "pdf_gen.py", "reportes_fiscales.py",
                         "sire_emision.py (Selenium)", "tango_loader.py"]),
            ("Datos", ["db.py — psycopg2 + pool", "cloud_db.py", "cloud_storage.py (bucket pdfs)"]),
        ],
        "integraciones": ["ARCA · portal SIRE (Selenium)", "Tango (asientos)",
                           "GitHub Releases", "Facturador (RPC)"],
        "flujo": [
            "En «Nueva OP» se elige empresa, tipo, proveedor y mes.",
            "Se cargan las facturas en la grilla.",
            "El motor calcula Ganancias / IVA / IIBB y muestra el neto a pagar.",
            "Se completan los datos del pago (banco / cheque / CBU).",
            "«Procesar»: asigna N° de certificado, genera y sube los PDF.",
            "Guarda cabecera en pagos + detalle en facturas + retenciones.",
        ],
        "rel_datos": SUPA_COMPARTIDA,
    },
    "ddjj": {
        "nombre": "DDJJ Impuestos", "emoji": "📑", "color": "#2E86C1",
        "proposito": "Prepara mes a mes las DDJJ de IVA y las retenciones de IIBB "
                     "(SIRCREB) de los 9 clientes en ARCA. Arma la DDJJ hasta la "
                     "Vista Previa (PDF + Excel) y guarda todo en la nube. Regla de "
                     "oro: NUNCA presenta (eso lo hace una persona después).",
        "stack": "Python + PyQt6. Postgres DIRECTO con psycopg2. Playwright "
                 "(navegador Chromium para ARCA), pandas, openpyxl.",
        "entrypoint": "DDJJ Impuestos.bat → pythonw scripts/main.py",
        "datos": SUPA_COMPARTIDA + " · tablas ddjj_iva, ddjj_sircreb, ddjj_historial",
        "capas": [
            ("UI (PyQt6)", ["scripts/main.py", "main_window.py",
                             "page_ejecutar.py", "page_repositorio.py", "page_conciliacion.py"]),
            ("Motores", ["portal_iva.py (Playwright → DDJJ IVA)",
                          "sircreb.py (SIFERE → retenciones)", "conciliacion.py"]),
            ("Datos", ["supabase_db.py — psycopg2 (historial, IVA, SIRCREB)"]),
        ],
        "integraciones": ["ARCA · Portal IVA + SIFERE (Playwright, login manual)",
                           "RetencionesPro (concilia compras)", "GitHub"],
        "flujo": [
            "Se elige mes, cliente (o «todos») y modo, y se da Iniciar.",
            "Se abre Chromium; Adrián pone CUIT + Clave Fiscal + CAPTCHA una vez.",
            "Por cada cliente abre Nueva DDJJ e importa los libros de ARCA.",
            "Completa aperturas y llega a la Vista Previa.",
            "Guarda el PDF y PARA (no presenta).",
            "Guarda el resultado en Supabase para consultas y comparativos.",
        ],
        "rel_datos": SUPA_COMPARTIDA,
    },
    "cobranzas": {
        "nombre": "Cobranzas OSECAC", "emoji": "💰", "color": "#D68910",
        "proposito": "Descarga las órdenes de pago y retenciones del portal de "
                     "prestadores de OSECAC, parsea los PDF, arma Excel y asientos "
                     "contables, factura en ARCA y cruza facturas contra cobranzas. "
                     "Todo se guarda en su propia nube.",
        "stack": "Python + PyQt6. Supabase por REST (anon key) + Storage. requests + "
                 "BeautifulSoup (OSECAC), Selenium (ARCA), zeep (WSFEV1), bcrypt (login).",
        "entrypoint": "Iniciar Cobranzas.bat → pythonw cobranzas_qt.py",
        "datos": SUPA_COBRANZAS + " · tablas cobranzas, retenciones, facturas · bucket cobranzas",
        "capas": [
            ("UI (PyQt6 · ui/)", ["cobranzas_qt.py + shell.py", "mod_dashboard.py",
                                    "mod_descargar.py", "mod_repositorio.py",
                                    "mod_retenciones.py", "mod_asientos.py", "mod_facturacion.py"]),
            ("Motores", ["osecac_descargar.py (portal OSECAC)", "facturas_arca.py (Selenium)",
                          "parser_retenciones.py", "asientos_contables.py", "exportar_excel.py"]),
            ("Datos", ["supabase_sync.py — REST + Storage", "configurar.py (secretos.json → .env)"]),
        ],
        "integraciones": ["Portal OSECAC (HTTP)", "ARCA · Mis Comprobantes + WSFEV1",
                           "GitHub"],
        "flujo": [
            "Login en la app; se abre el Dashboard.",
            "En «Descargar de OSECAC»: se tilda empresa, rango de fechas y destino.",
            "Entra al portal, parsea los pagos y baja los PDF (saltea lo ya bajado).",
            "Clasifica cada PDF (Cobranza / Ganancias / IVA / IIBB / SUSS) y lo parsea.",
            "Sube los PDF al bucket y la metadata a las tablas.",
            "Genera Excel/asientos y cruza con las facturas de ARCA.",
        ],
        "rel_datos": SUPA_COBRANZAS,
    },
    "facturador": {
        "nombre": "Facturador ARCA", "emoji": "📄", "color": "#16A085",
        "proposito": "Emite facturas electrónicas reales contra los Web Services de "
                     "ARCA (WSFEV1), el mismo backend de Comprobantes en Línea. "
                     "Factura por varios monotributistas y RI a un grupo fijo de "
                     "empresas, individual o por lote mensual.",
        "stack": "Python + PyQt6. Supabase por REST (anon key) + Storage. zeep (SOAP), "
                 "cryptography (firma CMS del WSAA), reportlab + qrcode (PDF).",
        "entrypoint": "python main.py",
        "datos": SUPA_COMPARTIDA + " · tablas facturador_facturas, facturador_token · bucket facturador",
        "capas": [
            ("UI (PyQt6)", ["main.py — MainWindow", "LoteDialog (lote mensual)",
                             "FacturasDialog (emitidas + resumen)", "PadronDialog"]),
            ("Núcleo (src/)", ["wsaa.py — autenticación por certificado",
                                 "wsfev1.py — pide el CAE", "comprobante_pdf.py — PDF con QR",
                                 "nube.py — Supabase REST"]),
            ("Config local", ["nube.json (credenciales)", "certs/ (certificado ARCA)",
                               "datos_local.json (emisores)"]),
        ],
        "integraciones": ["ARCA · WSAA + WSFEV1 (SOAP, certificado)",
                           "RetencionesPro (RPC crear_op_desde_factura)", "GitHub"],
        "flujo": [
            "Se marcan emisores y se carga el cliente y los ítems.",
            "wsaa.py firma el TRA con el certificado y obtiene el Ticket de Acceso.",
            "wsfev1.py pide el CAE a ARCA (elige tipo A/B/C automático).",
            "comprobante_pdf.py genera el PDF con el QR oficial.",
            "nube.py sube el PDF y guarda la factura.",
            "La RPC crea 1 Orden de Pago en RetencionesPro (factura → OP).",
        ],
        "rel_datos": SUPA_COMPARTIDA,
    },
    "employee": {
        "nombre": "Employee Pro", "emoji": "👥", "color": "#8E44AD",
        "proposito": "Gestión de RR.HH. de las empresas clientes: legajos, "
                     "documentación con vencimientos, ausencias, vacaciones, EPP, "
                     "capacitaciones y registro de sueldos. Multiempresa.",
        "stack": "Python + PyQt6. Supabase (SDK oficial) + Storage. reportlab, "
                 "openpyxl, qrcode (captura de fotos por QR).",
        "entrypoint": "python main.py",
        "datos": SUPA_EMPLOYEE + " · tablas empleados, documentos, vacaciones… · bucket legajos",
        "capas": [
            ("UI (PyQt6 · ui/)", ["login.py", "main_window.py", "empleado_form.py",
                                    "documento_form.py", "ficha_dialog.py (Ficha 360)",
                                    "captura_dialog.py (QR)"]),
            ("Servicios", ["faltantes.py (qué falta por empleado)",
                            "control_center.py (alertas)", "cronos_import.py (fichadas)",
                            "analytics.py"]),
            ("Datos / Config", ["db/client.py — SDK Supabase", "config/settings.py (secretos.json)"]),
        ],
        "integraciones": ["ARCA (alta temprana, a nivel de datos)",
                           "Cronos (importa fichadas)", "GitHub"],
        "flujo": [
            "Login eligiendo rol y empresa activa.",
            "Se abre el Padrón; marca en rojo quién «requiere atención».",
            "Se crea/edita un empleado y se cargan sus documentos (al bucket).",
            "Calcula el estado de cada documento y el checklist de incorporación.",
            "Se registran novedades, vacaciones, EPP y capacitaciones.",
            "Se exporta el legajo completo a PDF / Excel.",
        ],
        "rel_datos": SUPA_EMPLOYEE,
    },
    "juicios": {
        "nombre": "Control de Juicios", "emoji": "⚖️", "color": "#1F4E79",
        "proposito": "Controla los juicios y contingencias laborales de las empresas "
                     "clientes: tablero de KPIs (activos, monto en riesgo, provisión, "
                     "ahorro en acuerdos) y alta/edición del listado. Reemplaza el "
                     "Excel con macros por consultas en vivo.",
        "stack": "Python + PyQt6. Supabase por REST (requests / PostgREST, sin SDK). "
                 "openpyxl (export), qrcode; gráfico con QPainter.",
        "entrypoint": "run.bat → python main.py",
        "datos": SUPA_COMPARTIDA + " · tablas juicios_* (base compartida)",
        "capas": [
            ("UI (PyQt6)", ["main.py", "shell.py", "ui_dashboard.py (KPIs)",
                             "ui_listado.py", "ui_form.py", "ui_compartir.py (link + QR)"]),
            ("Datos", ["db.py — JuiciosDB (REST) + carga del .env compartido"]),
            ("Extras", ["estilos.py", "grafico.py (QPainter)"]),
        ],
        "integraciones": ["Formulario público (GitHub Pages) para abogados",
                           "WhatsApp / QR", "GitHub"],
        "flujo": [
            "Al abrir, conecta y detecta cargas nuevas de abogados (badge 🔔).",
            "El Dashboard muestra los KPIs en vivo por empresa.",
            "Se filtra el listado por empresa, categoría, etapa, año.",
            "Se da de alta o edita un juicio (INSERT/UPDATE directo).",
            "Se comparte por WhatsApp/QR el link público de carga.",
            "Se exporta el listado a Excel.",
        ],
        "rel_datos": SUPA_COMPARTIDA,
    },
    "deposito": {
        "nombre": "Depósito Avalos", "emoji": "📦", "color": "#A04000",
        "proposito": "Controla el stock del depósito de artículos de limpieza: "
                     "productos, proveedores, ingresos, egresos y devoluciones, con "
                     "objetivos por producto y 15 informes (cobertura, rotación ABC, "
                     "kardex). La integridad del stock se garantiza con RPC atómicas.",
        "stack": "Python + PySide6 (Qt). Supabase propio (sin RLS) por REST + RPC. "
                 "openpyxl / reportlab (export Excel y PDF).",
        "entrypoint": "ejecutar.bat → python app.py",
        "datos": SUPA_DEPOSITO + " · productos, proveedores, ingresos, egresos, "
                 "inventarios, objetivos · migraciones 0001-0007",
        "capas": [
            ("UI (PySide6 · src/ui/)", ["main_window.py — 11 secciones",
                                          "dashboard_screen.py (KPIs + gráficos)",
                                          "inventarios_screen.py", "ingresos_screen.py",
                                          "devoluciones_screen.py", "informes_screen.py",
                                          "costos_screen.py", "objetivos_screen.py"]),
            ("Servicios / Dominio", ["src/services (stock_service, productos_service)",
                                       "src/domain (reglas)", "src/reports (15 informes)"]),
            ("Datos", ["src/repositories/*_repo.py — acceso por tabla",
                        "db/client.py — Supabase REST + RPC atómicas"]),
        ],
        "integraciones": ["Credenciales por OneDrive (Suite)", "GitHub Releases"],
        "flujo": [
            "Al abrir se elige usuario y puesto (trazabilidad de cada movimiento).",
            "El stock inicial se carga por Planilla de conteo → Inventario General.",
            "Se registran ingresos (por proveedor) y egresos del depósito.",
            "Las devoluciones y ajustes se aplican con RPC atómicas (nunca stock negativo).",
            "El Dashboard muestra cobertura y objetivos por producto.",
            "Se exportan los 15 informes a Excel / PDF (rotación ABC, kardex…).",
        ],
        "rel_datos": SUPA_DEPOSITO,
    },
    "contabilidad": {
        "nombre": "Contabilidad", "emoji": "📚", "color": "#117864",
        "proposito": "Contabilidad paralela del estudio: Libro Diario y Mayor, plan "
                     "de cuentas, estados contables y conciliación contra Tango. "
                     "Devenga las ventas directamente desde el libro IVA de ARCA.",
        "stack": "Python + PyQt6. Usa la MISMA base compartida que el resto de la "
                 "suite (lee asientos/cobranzas de las apps hermanas). openpyxl / PDF.",
        "entrypoint": "run.bat → python main.py",
        "datos": SUPA_COMPARTIDA + " · asientos, plan de cuentas, conciliación",
        "capas": [
            ("UI (PyQt6)", ["main.py + shell.py", "ui_dashboard.py",
                             "ui_diario.py (Libro Diario)", "ui_estados.py (Mayor/estados)",
                             "ui_conciliacion.py", "ui_cobranzas.py", "ui_apertura.py",
                             "ui_cierre.py"]),
            ("Lógica", ["diario.py / asiento_editor.py (asientos)", "plan.py (plan de cuentas)",
                         "conciliacion.py (contra Tango)", "cobranzas_sync.py",
                         "exportar.py / pdf_export.py"]),
            ("Datos", ["db.py — misma Supabase compartida (.env de la Suite)"]),
        ],
        "integraciones": ["Tango (concilia asientos)", "ARCA · libro IVA (devenga ventas)",
                           "Cobranzas OSECAC (importa)", "GitHub"],
        "flujo": [
            "Importa el libro IVA de ARCA y devenga las ventas del período.",
            "Carga/edita los asientos en el Libro Diario.",
            "Concilia los movimientos contra el mayor de Tango.",
            "Arma el Libro Mayor y los estados contables.",
            "Cierra el período (apertura / cierre).",
            "Exporta Diario, Mayor y estados a Excel / PDF.",
        ],
        "rel_datos": SUPA_COMPARTIDA,
    },
    "conciliador": {
        "nombre": "Conciliador Bancario", "emoji": "🏦", "color": "#0F9D78",
        "proposito": "Concilia el Mayor de Tango contra el extracto del banco "
                     "(BBVA, Excel o PDF): cruza los movimientos, propone el asiento "
                     "de gastos bancarios y arma el cuadro de conciliación saldo-a-saldo "
                     "estilo Reconcile de QuickBooks.",
        "stack": "Python + PyQt6. Supabase propio (sin RLS) por REST con anon key "
                 "embebida. pandas / pdfplumber (lee Tango y BBVA) · openpyxl / reportlab "
                 "(export Excel y PDF).",
        "entrypoint": "run.bat → python main.py",
        "datos": SUPA_CONCILIADOR + " · conciliacion, movimiento, asiento, asiento_linea",
        "capas": [
            ("UI (PyQt6 · ui/)", ["main_window.py — solapas (QTabWidget)",
                                    "panel_pendientes.py (4 categorías)",
                                    "reconcile_tab.py (cuadro saldo-a-saldo)",
                                    "asiento_dialog.py / cheque_dialog.py"]),
            ("Lógica (logic/)", ["matching.py (cascada exacto/ref/tolerancia)",
                                   "conceptos.py (15 conceptos del banco)",
                                   "asientos.py (asiento de gastos bancarios)",
                                   "reconcile.py + sesion.py", "exportar.py (Excel/PDF)"]),
            ("Parsers / Datos", ["parsers/ (Tango xlsx, BBVA xls/xlsx/pdf)",
                                   "db/rest.py — Supabase REST", "db/repo.py"]),
        ],
        "integraciones": ["Tango (Mayor Excel)", "BBVA (extracto Excel/PDF)", "GitHub"],
        "flujo": [
            "Carga el Mayor de Tango y el extracto del BBVA (Excel o PDF).",
            "Cruza los movimientos en cascada (importe / fecha / referencia).",
            "Propone el asiento de gastos bancarios (SIRCREB, Ley 25.413, comisiones…).",
            "Clasifica las pendientes en 4 solapas y arma el cuadro Mayor → Banco.",
            "Guarda la conciliación por cuenta y período; exporta a Excel / PDF.",
        ],
        "rel_datos": SUPA_CONCILIADOR,
    },
    # ── Webs companion (front-ends que corren en el celular) ──────────────
    "comprobantes": {
        "nombre": "Comprobantes (Web QR)", "emoji": "📲", "color": "#27AE9A",
        "parent": "reten",
        "proposito": "Es la web que se abre en el CELULAR (con un QR desde "
                     "RetencionesPro) para sacarle la foto al comprobante de un pago "
                     "y subirla, sin instalar nada. Cubre las órdenes de pago a "
                     "proveedores y los pagos de DDJJ de retenciones.",
        "stack": "HTML/CSS/JS estático en GitHub Pages (sin build). Habla con una "
                 "Edge Function de Supabase (Deno) protegida por un PIN; el navegador "
                 "del celular nunca ve las claves de la base.",
        "entrypoint": "ematiromero98.github.io/comprobantes-cel/ (QR desde «Pasar Pagos»)",
        "datos": SUPA_COMPARTIDA + " · Edge Function comprobantes-cel · buckets "
                 "comprobantes / pdfs · tablas bandeja_comprobantes, ddjj_recaudacion_pagos",
        "capas": [
            ("Front (GitHub Pages)", ["index.html — lista de órdenes/DDJJ y cámara del celular",
                                        "Acceso por PIN (no hay login por persona)"]),
            ("Edge Function (Deno)", ["comprobantes-cel/index.ts — API con header x-pin",
                                        "GET /ordenes · GET /ddjj · POST /subir · POST /subir-ddjj"]),
            ("Datos", ["RPC ordenes_para_comprobantes / ddjj_para_comprobantes",
                        "Storage: sube la foto al bucket (comprobantes / pdfs)",
                        "PIN guardado en app_config (clave pin_comprobantes)"]),
        ],
        "integraciones": ["RetencionesPro (Pasar Pagos · QR)", "Supabase Edge Functions",
                           "GitHub Pages"],
        "flujo": [
            "En RetencionesPro, «Pasar Pagos» arma un QR que incluye el PIN.",
            "El celular abre la web y valida el PIN contra app_config.",
            "Lista las órdenes pendientes y las DDJJ que esperan comprobante.",
            "Se elige una y se saca la foto del comprobante de pago.",
            "La Edge Function sube la imagen al bucket con la service-role key.",
            "Marca la orden/DDJJ como comprobada; el escritorio la muestra sin cambios.",
        ],
        "rel_datos": SUPA_COMPARTIDA,
    },
    "juicios_carga": {
        "nombre": "Carga de Juicios (Web)", "emoji": "📝", "color": "#5DADE2",
        "parent": "juicios",
        "proposito": "Es el formulario público (link + QR) que se le pasa a los "
                     "abogados para que carguen o completen un juicio desde el "
                     "celular, sin entrar al sistema. Lo que cargan aparece "
                     "automáticamente en Control de Juicios.",
        "stack": "HTML/CSS/JS estático en GitHub Pages (sin build, sin dependencias). "
                 "Escribe a través de una Edge Function de Supabase (Deno); no expone "
                 "ninguna clave de la base.",
        "entrypoint": "ematiromero98.github.io/juicios-carga/ (link/QR desde Control de Juicios)",
        "datos": SUPA_COMPARTIDA + " · Edge Function juicio-abogado · tablas juicios_*",
        "capas": [
            ("Front (GitHub Pages)", ["index.html — formulario responsive",
                                        "Modo Nuevo (?nuevo=clave) o Editar (?token=…)"]),
            ("Edge Function (Deno)", ["juicio-abogado — GET ?meta (empresas) · GET ?data (juicio)",
                                        "POST — alta o edición del juicio"]),
            ("Datos", ["Escribe en juicios_* (base compartida)",
                        "Valida por token/clave; sin login por persona"]),
        ],
        "integraciones": ["Control de Juicios (recibe las cargas)", "Supabase Edge Functions",
                           "WhatsApp / QR", "GitHub Pages"],
        "flujo": [
            "Desde Control de Juicios se comparte el link/QR (nuevo o para editar uno).",
            "El abogado abre el formulario en el celular.",
            "Elige la empresa (alta) o se le precarga el juicio (edición).",
            "Completa carátula, etapa, montos, juzgado, abogado y notas.",
            "«Enviar»: la Edge Function guarda en juicios_* de la base compartida.",
            "Control de Juicios detecta la carga nueva (badge 🔔) y la revisa.",
        ],
        "rel_datos": SUPA_COMPARTIDA,
    },
}

# Webs companion (front-ends en el celular) → app de escritorio que las usa.
COMPANIONS_ORDEN = ["comprobantes", "juicios_carga"]

# Sistemas externos y bases, para la vista general.
EXTERNOS = {
    "arca": ("🏛️", "ARCA / AFIP", "Portal IVA, SIRE, SIFERE, WSFEV1"),
    "osecac": ("🏥", "Portal OSECAC", "Órdenes de pago de prestadores"),
    "drive": ("☁️", "Google Drive", "Credenciales (.env / secretos)"),
    "tango": ("📚", "Tango", "Asientos contables"),
}
BASES = {
    "compartida": ("🗄️", "Supabase COMPARTIDA", "zpwccecovhjmeibxafkg",
                    ["reten", "ddjj", "facturador", "juicios", "contabilidad"]),
    "cobranzas": ("🗄️", "Supabase Cobranzas", "rrarmatjyvmrpohsvfzg", ["cobranzas"]),
    "employee": ("🗄️", "Supabase Employee", "ffczbimnuodzcbgsdxbx", ["employee"]),
    "deposito": ("🗄️", "Supabase Depósito", "ioycuhefaalpqivhhryb", ["deposito"]),
    "conciliador": ("🗄️", "Supabase Conciliador", "qaaxestmwmqmylthnwts", ["conciliador"]),
}
APPS_ORDEN = ["reten", "ddjj", "cobranzas", "facturador",
              "employee", "juicios", "deposito", "contabilidad", "conciliador"]


# ============================================================ VISTA (Qt)
class _Vista(QGraphicsView):
    """QGraphicsView con zoom por rueda y arrastre para desplazar. Los clics en
    nodos con data(0) llaman a on_nodo(key)."""

    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QColor(BG))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._zoom = 1.0
        self.on_nodo = None

    def wheelEvent(self, e):
        f = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        nz = self._zoom * f
        if 0.35 < nz < 3.0:
            self._zoom = nz
            self.scale(f, f)

    def mousePressEvent(self, e):
        it = self.itemAt(e.pos())
        while it is not None and it.data(0) is None:
            it = it.parentItem()
        if it is not None and it.data(0) and callable(self.on_nodo):
            self.on_nodo(it.data(0))
            return
        super().mousePressEvent(e)


def _texto(scene, x, y, s, color=TXT, size=10, bold=False, w=None):
    t = QGraphicsSimpleTextItem(s)
    f = QFont("Segoe UI", size)
    f.setBold(bold)
    t.setFont(f)
    t.setBrush(QColor(color))
    t.setPos(x, y)
    scene.addItem(t)
    return t


def _caja(scene, x, y, w, h, color, radio=12, relleno=CARD, ancho=2):
    path = QPainterPath()
    path.addRoundedRect(QRectF(x, y, w, h), radio, radio)
    it = QGraphicsPathItem(path)
    it.setPen(QPen(QColor(color), ancho))
    it.setBrush(QBrush(QColor(relleno)))
    scene.addItem(it)
    return it


def _nodo_app(scene, x, y, w, h, key, titulo, emoji, color, sub=""):
    """Tarjeta de app clickeable (data(0)=key)."""
    caja = _caja(scene, x, y, w, h, color, relleno=CARD)
    caja.setData(0, key)
    caja.setCursor(Qt.CursorShape.PointingHandCursor)
    _emoji_item(scene, x + 12, y + 11, emoji, 22, key=key)
    _texto(scene, x + 42, y + 14, titulo, color=TXT, size=11, bold=True).setData(0, key)
    if sub:
        _texto(scene, x + 14, y + 40, sub, color=SUB, size=8).setData(0, key)
    return caja


def _label_ico(scene, x, y, emoji, txt, color=TXT, size=10, bold=False, epx=16):
    """Fila 'ícono + texto' con el emoji dibujado a color (no como fuente)."""
    _emoji_item(scene, x, y - 2, emoji, epx)
    _texto(scene, x + epx + 8, y, txt, color=color, size=size, bold=bold)


def _linea(scene, p1, p2, color=LINEA, ancho=2, etiqueta="", punteada=False):
    path = QPainterPath()
    path.moveTo(p1[0], p1[1])
    path.lineTo(p2[0], p2[1])
    it = QGraphicsPathItem(path)
    pen = QPen(QColor(color), ancho)
    if punteada:
        pen.setStyle(Qt.PenStyle.DashLine)
    it.setPen(pen)
    it.setZValue(-1)
    scene.addItem(it)
    if etiqueta:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        _texto(scene, mx - 4, my - 16, etiqueta, color=SUB, size=8)
    return it


class PaginaArquitectura(QWidget):
    """Página del ERP: lista de vistas + diagrama + explicación."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._flujo_items = []
        self._flujo_timer = QTimer(self)
        self._flujo_timer.timeout.connect(self._flujo_tick)
        self._flujo_i = 0
        self._flujo_key = None
        self._build()
        self.mostrar_general()

    # ------------------------------------------------------------ layout
    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Panel izquierdo: navegación
        izq = QVBoxLayout()
        izq.setContentsMargins(14, 14, 8, 14)
        izq.setSpacing(8)
        tit = QLabel("🗺️  Arquitectura")
        tit.setStyleSheet(f"color:{TXT}; font-size:15px; font-weight:800;")
        izq.addWidget(tit)
        sub = QLabel("Elegí un proyecto para verlo solo")
        sub.setStyleSheet(f"color:{SUB}; font-size:11px;")
        izq.addWidget(sub)
        # Filtro: escribí y la lista se achica a los proyectos que coinciden.
        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("🔎  Filtrar proyecto…")
        self.filtro.setClearButtonEnabled(True)
        self.filtro.setStyleSheet(
            f"QLineEdit{{background:{CARD2}; border:1px solid {BORDE}; border-radius:9px;"
            f"color:{TXT}; font-size:12px; padding:7px 9px;}}"
            f"QLineEdit:focus{{border:1px solid {MENTA};}}")
        self.filtro.textChanged.connect(self._filtrar_lista)
        izq.addWidget(self.filtro)
        self.lista = QListWidget()
        self.lista.setStyleSheet(
            f"QListWidget{{background:{CARD2}; border:1px solid {BORDE};"
            f"border-radius:10px; color:{TXT}; font-size:12px; padding:6px;}}"
            f"QListWidget::item{{padding:9px 8px; border-radius:7px;}}"
            f"QListWidget::item:selected{{background:{MENTA}; color:#0b0f14;}}"
            f"QListWidget::item:hover{{background:#232c39;}}")
        it_gen = QListWidgetItem(_emoji_icon("🌐", 18), "  Vista general del ERP", self.lista)
        it_gen.setData(32, "general")
        for k in APPS_ORDEN:
            p = PROYECTOS[k]
            it = QListWidgetItem(_emoji_icon(p["emoji"], 18), "  " + p["nombre"], self.lista)
            it.setData(32, k)
        # Webs companion (celular), agrupadas al final con un separador visual.
        sep = QListWidgetItem("  webs del estudio (celular)", self.lista)
        sep.setFlags(Qt.ItemFlag.NoItemFlags)
        sep.setForeground(QColor(SUB))
        for k in COMPANIONS_ORDEN:
            p = PROYECTOS[k]
            it = QListWidgetItem(_emoji_icon(p["emoji"], 18), "  " + p["nombre"], self.lista)
            it.setData(32, k)
        self.lista.currentItemChanged.connect(self._on_lista)
        izq.addWidget(self.lista, stretch=1)
        self.btn_flujo = QPushButton("▶  Reproducir flujo")
        self.btn_flujo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_flujo.setStyleSheet(
            f"QPushButton{{background:#20303f; color:{MENTA}; border:1px solid #2e4a3f;"
            f"border-radius:9px; padding:9px; font-size:12px; font-weight:700;}}"
            f"QPushButton:hover{{background:#274a3e;}}"
            f"QPushButton:disabled{{color:{SUB}; background:{CARD2}; border-color:{BORDE};}}")
        self.btn_flujo.clicked.connect(self._reproducir_flujo)
        izq.addWidget(self.btn_flujo)
        cont_izq = QWidget()
        cont_izq.setLayout(izq)
        cont_izq.setFixedWidth(230)
        lay.addWidget(cont_izq)

        # Centro: el diagrama
        self.vista = _Vista()
        self.vista.on_nodo = self._on_nodo
        lay.addWidget(self.vista, stretch=1)

        # Derecha: explicación
        self.info = QTextBrowser()
        self.info.setOpenExternalLinks(False)
        self.info.setStyleSheet(
            f"QTextBrowser{{background:{CARD2}; border:none; border-left:1px solid {BORDE};"
            f"color:{TXT}; font-size:12px; padding:16px;}}")
        self.info.setFixedWidth(330)
        lay.addWidget(self.info)

    # ------------------------------------------------------------ navegación
    def _on_lista(self, cur, _prev):
        if cur is None:
            return
        key = cur.data(32)
        if key == "general":
            self.mostrar_general()
        else:
            self.mostrar_proyecto(key)

    def _filtrar_lista(self, texto):
        """Achica la lista a los proyectos cuyo nombre contiene `texto`."""
        q = (texto or "").strip().lower()
        for i in range(self.lista.count()):
            it = self.lista.item(i)
            es_sep = not (it.flags() & Qt.ItemFlag.ItemIsSelectable)
            if es_sep:                      # el separador "webs del estudio…"
                it.setHidden(bool(q))       # se oculta cuando hay filtro activo
                continue
            it.setHidden(bool(q) and q not in it.text().lower())

    def _on_nodo(self, key):
        # Clic en un nodo del diagrama general → seleccionar en la lista.
        for i in range(self.lista.count()):
            if self.lista.item(i).data(32) == key:
                self.lista.setCurrentRow(i)
                return
        if key in PROYECTOS:
            self.mostrar_proyecto(key)

    def _reset(self):
        self._flujo_timer.stop()
        self._flujo_items = []
        self.vista.setScene(QGraphicsScene())

    def _ajustar(self):
        """Encaja el diagrama actual en la vista (se ve completo de un vistazo)."""
        sc = self.vista.scene()
        if sc is not None:
            self.vista.fitInView(sc.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.vista._zoom = 1.0

    def showEvent(self, e):
        super().showEvent(e)
        self._ajustar()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._ajustar()

    # ------------------------------------------------------------ vista general
    def mostrar_general(self):
        self.btn_flujo.setEnabled(False)
        sc = QGraphicsScene()
        self.vista.setScene(sc)
        W = 1180

        _label_ico(sc, 40, 12, "🌐", "Suite Contable — MR & Asociados",
                   color=TXT, size=15, bold=True, epx=22)
        _texto(sc, 40, 44, "Un ERP que abre 8 apps. Tocá cualquier app para ver su detalle.",
               color=SUB, size=10)

        # ERP arriba, centrado
        erp = PROYECTOS["erp"]
        ex, ew = W / 2 - 130, 260
        _nodo_app(sc, ex, 80, ew, 54, "erp", erp["nombre"], erp["emoji"], erp["color"],
                  "lanza / actualiza / instala")
        erp_bottom = (W / 2, 134)

        # Apps: 9 en 2 filas (5 + 4)
        aw, ah, gx, gy = 176, 64, 18, 16
        cols = 5
        row_w = cols * aw + (cols - 1) * gx
        x0 = (W - row_w) / 2
        ry = [176, 176 + ah + gy]                 # y de cada fila
        centros, bottoms = {}, {}
        for i, k in enumerate(APPS_ORDEN):
            p = PROYECTOS[k]
            col, row = i % cols, i // cols
            x, y = x0 + col * (aw + gx), ry[row]
            _nodo_app(sc, x, y, aw, ah, k, p["nombre"], p["emoji"], p["color"])
            centros[k] = (x + aw / 2, y)
            bottoms[k] = y + ah
            _linea(sc, erp_bottom, (x + aw / 2, y), color="#2e3a4d", ancho=2)

        # Fila de bases (datos)
        by = 352
        base_w = {"compartida": 290, "cobranzas": 200, "employee": 200,
                  "deposito": 210, "conciliador": 210}
        gapb = 22
        total_b = sum(base_w.values()) + gapb * (len(base_w) - 1)
        bx0 = (W - total_b) / 2
        base_pos, cx = {}, bx0
        for bk in ("compartida", "cobranzas", "employee", "deposito", "conciliador"):
            base_pos[bk] = (cx, by, base_w[bk])
            cx += base_w[bk] + gapb
        for bk, (emoji, nombre, ref, apps) in BASES.items():
            bx, byy, bw = base_pos[bk]
            _caja(sc, bx, byy, bw, 54, "#3a4658", relleno="#12202b")
            _label_ico(sc, bx + 12, byy + 11, emoji, nombre, color="#bfe9d5",
                       size=10, bold=True, epx=15)
            _texto(sc, bx + 12, byy + 31, ref, color=SUB, size=8)
            for k in apps:
                if k in centros:
                    _linea(sc, (centros[k][0], bottoms[k]), (bx + bw / 2, byy),
                           color="#2b6b52", ancho=2, punteada=True)

        # Puente factura → OP (Facturador → RetencionesPro)
        if "facturador" in centros and "reten" in centros:
            _linea(sc, centros["facturador"], centros["reten"],
                   color=MENTA, ancho=2, etiqueta="factura → OP (RPC)")

        # Externos (abajo)
        exy = 448
        ext_w, gape = 200, 24
        total_e = len(EXTERNOS) * ext_w + gape * (len(EXTERNOS) - 1)
        exx = (W - total_e) / 2
        for ek, (emoji, nombre, desc) in EXTERNOS.items():
            _caja(sc, exx, exy, ext_w, 50, "#4a3a1e", relleno="#241d10")
            _label_ico(sc, exx + 12, exy + 10, emoji, nombre, color="#f6c66b",
                       size=10, bold=True, epx=15)
            _texto(sc, exx + 12, exy + 30, desc, color=SUB, size=8)
            exx += ext_w + gape

        # Webs companion (celular) — fila clickeable, atadas a su app de escritorio.
        wy = 520
        _texto(sc, 40, wy - 4, "Webs del estudio (celular):", color=SUB, size=9, bold=True)
        cw, gapc = 250, 24
        total_c = len(COMPANIONS_ORDEN) * cw + gapc * (len(COMPANIONS_ORDEN) - 1)
        wx = (W - total_c) / 2
        for ck in COMPANIONS_ORDEN:
            p = PROYECTOS[ck]
            caja = _caja(sc, wx, wy + 14, cw, 50, p["color"], relleno="#101a22")
            caja.setData(0, ck)
            caja.setCursor(Qt.CursorShape.PointingHandCursor)
            _emoji_item(sc, wx + 12, wy + 25, p["emoji"], 18, key=ck)
            _texto(sc, wx + 40, wy + 22, p["nombre"], color=TXT, size=10, bold=True).setData(0, ck)
            _texto(sc, wx + 40, wy + 40, "↳ " + PROYECTOS[p["parent"]]["nombre"],
                   color=SUB, size=8).setData(0, ck)
            wx += cw + gapc

        sc.setSceneRect(0, 0, W, 600)
        self._ajustar()
        self._explicacion_general()

    def _explicacion_general(self):
        # Punto de color por app (en vez de emoji: QTextBrowser usa la fuente base
        # y el emoji saldría como "tofu"; el punto siempre se ve bien).
        filas = "".join(
            f"<tr><td style='padding:3px 8px 3px 0;color:{PROYECTOS[k]['color']};"
            f"font-size:15px'>&#9679;</td>"
            f"<td style='padding:3px 0'><b>{PROYECTOS[k]['nombre']}</b><br>"
            f"<span style='color:{SUB};font-size:11px'>{PROYECTOS[k]['proposito'][:90]}…</span></td></tr>"
            for k in APPS_ORDEN)
        self.info.setHtml(f"""
        <div style='color:{TXT}'>
        <h2 style='color:{MENTA};margin:0 0 6px'>El ERP de un vistazo</h2>
        <p style='color:{SUB};font-size:12px;margin:0 0 12px'>
        La <b>Suite Contable</b> es el programa que abre y mantiene al día las 8 apps
        del estudio. Cada app guarda sus datos en Supabase (la «nube») y se conecta
        con sistemas externos como ARCA u OSECAC.</p>
        <h3 style='color:{TXT};margin:10px 0 4px'>Las bases de datos</h3>
        <ul style='color:{SUB};font-size:12px;margin:0 0 10px;padding-left:18px'>
        <li><b style='color:#bfe9d5'>Compartida</b>: la usan RetencionesPro, DDJJ,
        Facturador, Juicios y Contabilidad (por eso se cruzan datos entre ellas).</li>
        <li><b style='color:#bfe9d5'>Cobranzas</b>, <b style='color:#bfe9d5'>Employee</b>
        y <b style='color:#bfe9d5'>Depósito</b> tienen su propia base, separada.</li></ul>
        <h3 style='color:{TXT};margin:10px 0 4px'>Las apps</h3>
        <table style='font-size:12px'>{filas}</table>
        <h3 style='color:{TXT};margin:12px 0 4px'>Webs del celular</h3>
        <p style='color:{SUB};font-size:12px;margin:0 0 8px'>
        Dos front-ends que corren en el <b>celular</b> (GitHub Pages + una Edge
        Function de Supabase): <b style='color:#27AE9A'>Comprobantes (QR)</b> sube la
        foto del pago para RetencionesPro, y <b style='color:#5DADE2'>Carga de Juicios</b>
        deja que los abogados carguen un juicio para Control de Juicios.</p>
        <p style='color:{SUB};font-size:11px;margin-top:12px'>
        Tocá una app o web (acá o en el diagrama) para ver cómo está hecha por dentro.</p>
        </div>""")

    # ------------------------------------------------------------ vista proyecto
    def mostrar_proyecto(self, key):
        p = PROYECTOS.get(key)
        if not p:
            return
        self._flujo_key = key
        self.btn_flujo.setEnabled(bool(p.get("flujo")))
        sc = QGraphicsScene()
        self.vista.setScene(sc)
        W = 900

        _label_ico(sc, 30, 12, p["emoji"], p["nombre"], color=p["color"],
                   size=16, bold=True, epx=22)
        _texto(sc, 30, 40, p["datos"], color=SUB, size=9)

        # Capas apiladas
        y = 76
        for nombre, items in p["capas"]:
            h = 44 + len(items) * 20
            _caja(sc, 30, y, W - 60, h, p["color"], relleno=CARD)
            _texto(sc, 46, y + 12, nombre, color=TXT, size=12, bold=True)
            for j, it in enumerate(items):
                _texto(sc, 60, y + 38 + j * 20, "• " + it, color=SUB, size=9)
            if y > 76:
                _linea(sc, (W / 2, y - 12), (W / 2, y), color=p["color"], ancho=2)
            y += h + 12

        # Integraciones (chips)
        _texto(sc, 30, y + 2, "Se conecta con:", color=TXT, size=11, bold=True)
        cx = 150
        for ig in p.get("integraciones", []):
            w = 16 + len(ig) * 7
            _caja(sc, cx, y - 4, w, 26, "#4a3a1e", radio=13, relleno="#241d10", ancho=1)
            _texto(sc, cx + 10, y + 2, ig, color="#f6c66b", size=9)
            cx += w + 10
        y += 40

        # Flujo (strip de pasos, se anima)
        self._flujo_items = []
        if p.get("flujo"):
            _texto(sc, 30, y, "Flujo del caso principal:", color=TXT, size=11, bold=True)
            y += 26
            sx = 30
            for i, paso in enumerate(p["flujo"]):
                box = _caja(sc, sx, y, 54, 40, "#2e3a4d", radio=10, relleno=CARD2)
                num = _texto(sc, sx + 22, y + 10, str(i + 1), color=SUB, size=13, bold=True)
                self._flujo_items.append((box, num))
                if i < len(p["flujo"]) - 1:
                    _linea(sc, (sx + 54, y + 20), (sx + 64, y + 20), color=LINEA, ancho=2)
                sx += 64
            y += 56

        sc.setSceneRect(0, 0, W, y + 10)
        self._ajustar()
        self._explicacion_proyecto(key, -1)

    def _explicacion_proyecto(self, key, paso_activo):
        p = PROYECTOS[key]
        pasos = ""
        for i, s in enumerate(p.get("flujo", [])):
            act = i == paso_activo
            col = MENTA if act else SUB
            peso = "font-weight:700;" if act else ""
            marca = "▶ " if act else f"{i+1}. "
            pasos += (f"<li style='color:{col};{peso}margin-bottom:5px'>"
                      f"{marca if act else ''}{'' if act else ''}{s}</li>")
        self.info.setHtml(f"""
        <div style='color:{TXT}'>
        <h2 style='color:{p['color']};margin:0 0 8px'>
        <span style='font-size:15px'>&#9679;</span> {p['nombre']}</h2>
        <p style='font-size:12px;margin:0 0 12px'>{p['proposito']}</p>
        <h3 style='color:{TXT};margin:10px 0 4px'>Tecnología</h3>
        <p style='color:{SUB};font-size:12px;margin:0 0 10px'>{p['stack']}</p>
        <h3 style='color:{TXT};margin:10px 0 4px'>Se abre con</h3>
        <p style='color:{SUB};font-size:12px;margin:0 0 10px'><code>{p['entrypoint']}</code></p>
        <h3 style='color:{TXT};margin:10px 0 4px'>Flujo</h3>
        <ol style='font-size:12px;padding-left:18px;margin:0'>{pasos}</ol>
        <p style='color:{SUB};font-size:11px;margin-top:12px'>
        Tocá «▶ Reproducir flujo» para verlo paso a paso.</p>
        </div>""")

    # ------------------------------------------------------------ animación
    def _reproducir_flujo(self):
        if not self._flujo_items:
            return
        self._flujo_i = 0
        self._flujo_timer.start(1100)
        self._flujo_tick()

    def _flujo_tick(self):
        # apaga todos
        for box, num in self._flujo_items:
            box.setBrush(QBrush(QColor(CARD2)))
            box.setPen(QPen(QColor("#2e3a4d"), 2))
            num.setBrush(QColor(SUB))
        if self._flujo_i >= len(self._flujo_items):
            self._flujo_timer.stop()
            if self._flujo_key:
                self._explicacion_proyecto(self._flujo_key, -1)
            return
        box, num = self._flujo_items[self._flujo_i]
        box.setBrush(QBrush(QColor("#1d3b30")))
        box.setPen(QPen(QColor(MENTA), 3))
        num.setBrush(QColor(MENTA))
        if self._flujo_key:
            self._explicacion_proyecto(self._flujo_key, self._flujo_i)
        self._flujo_i += 1
