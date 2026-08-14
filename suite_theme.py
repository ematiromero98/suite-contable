# -*- coding: utf-8 -*-
"""
suite_theme — Tema visual compartido de la Suite Contable (MR & Asociados).

Un solo lugar para el look "Panel Oscuro" (dark + acento menta) de TODAS las
apps del estudio. Vive en el repo `suite-contable` (público, ya instalado en
cada PC); las apps lo importan agregando la carpeta de la Suite al `sys.path`
y llamando `suite_theme.apply(app)` en su arranque.

Uso típico en una app::

    import os, sys
    _suite = os.environ.get("SUITE_CONTABLE_DIR", r"D:\\suite-contable")
    if os.path.isdir(_suite):
        sys.path.insert(0, _suite)
    try:
        import suite_theme
    except Exception:
        suite_theme = None
    ...
    app = QApplication(sys.argv)
    if suite_theme:
        suite_theme.apply(app)      # tema global, una línea

No tiene dependencias fuera de PyQt6 (que toda app ya usa). Para los gráficos,
ver `suite_charts` (ese sí necesita PyQt6-QtCharts).
"""
from __future__ import annotations

# ── Tokens de color (la única fuente de verdad del tema) ────────────────────
BG        = "#0f1218"   # fondo de contenido
BG_DEEP   = "#0b0e13"   # fondo más profundo (detrás de tarjetas)
SIDE      = "#12161e"   # sidebar
PANEL     = "#171c26"   # tarjetas / superficies
PANEL2    = "#1d2430"   # superficie elevada
SOFT      = "#1c222e"   # inputs, chips, botón fantasma
TEXT      = "#eef2f8"   # texto principal
MUTED     = "#8a94a6"   # texto secundario / labels
FAINT     = "#5b6472"   # texto terciario / deshabilitado
BORDER    = "#242c39"   # bordes de tarjeta
HAIR      = "#1d2530"   # divisores finos
ACCENT    = "#2ee6a6"   # acento (acciones, activo)
ACCENT_INK = "#04120c"  # texto sobre el acento
ACCENT_2  = "#5cf0bd"   # acento claro (texto sobre fondo tenue)
ACCENT_WEAK = "#12271f"  # fondo tenue del ítem activo
GOOD      = "#2ee6a6"
WARN      = "#f6b64b"
BAD       = "#f6465d"
INFO      = "#5bb0ff"

FONT = '"Segoe UI", "Segoe UI Variable", system-ui, sans-serif'


def qss(base_font_px: int = 12) -> str:
    """Devuelve el QSS global del tema. `base_font_px` deja ajustar la densidad
    por app (Employee Pro usa tablas densas → 11; otras 12/13)."""
    return f"""
* {{ outline: 0; }}
QWidget {{
    background: {BG};
    color: {TEXT};
    font-family: {FONT};
    font-size: {base_font_px}px;
}}
QMainWindow, QDialog {{ background: {BG}; }}
QToolTip {{
    background: {BG_DEEP}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 8px; padding: 6px 9px;
}}

/* ── Texto ── */
QLabel {{ background: transparent; }}
QLabel#screenTitle, QLabel[role="title"] {{ font-size: {base_font_px + 6}px; font-weight: 700; color: {TEXT}; }}
QLabel#helper, QLabel[role="hint"] {{ font-size: {base_font_px - 1}px; color: {MUTED}; }}
QLabel#kpiLabel {{ color: {MUTED}; font-size: {base_font_px - 2}px; font-weight: 700; }}
QLabel#kpiValue {{ color: {TEXT}; font-size: {base_font_px + 14}px; font-weight: 400; }}

/* ── Botones ── */
QPushButton {{
    background: {ACCENT}; color: {ACCENT_INK}; border: none;
    border-radius: 9px; padding: 8px 15px; font-size: {base_font_px}px; font-weight: 700;
}}
QPushButton:hover  {{ background: {ACCENT_2}; }}
QPushButton:disabled {{ background: #232c39; color: {FAINT}; }}
QPushButton#secondary, QPushButton[variant="secondary"] {{
    background: {SOFT}; color: {TEXT}; border: 1px solid {BORDER};
}}
QPushButton#secondary:hover, QPushButton[variant="secondary"]:hover {{ background: {PANEL2}; }}
QPushButton#ghost, QPushButton[variant="ghost"] {{
    background: transparent; color: {WARN}; border: 1px solid #4a3a1e; font-weight: 700;
}}
QPushButton#ghost:hover {{ background: #241d10; }}
QPushButton#danger, QPushButton[variant="danger"] {{ background: {BAD}; color: #fff; }}
QPushButton#danger:hover {{ background: #ff5c6f; }}

/* ── Inputs ── */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QPlainTextEdit, QTextEdit {{
    background: {SOFT}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 8px; padding: 7px 10px;
    selection-background-color: {ACCENT}; selection-color: {ACCENT_INK};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{ border: 1px solid {ACCENT}; }}
QLineEdit:disabled, QComboBox:disabled {{ color: {FAINT}; background: #12151b; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: {PANEL}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 8px;
    selection-background-color: {ACCENT_WEAK}; selection-color: {ACCENT_2};
    outline: 0;
}}

/* ── Checkboxes / radios ── */
QCheckBox, QRadioButton {{ background: transparent; color: {TEXT}; spacing: 7px; }}
QCheckBox::indicator, QRadioButton::indicator {{ width: 16px; height: 16px; }}
QCheckBox::indicator {{ border: 1px solid {BORDER}; border-radius: 4px; background: {SOFT}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QRadioButton::indicator {{ border: 1px solid {BORDER}; border-radius: 8px; background: {SOFT}; }}
QRadioButton::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

/* ── Tablas ── */
QTableView, QTableWidget, QTreeView, QListView {{
    background: {PANEL}; alternate-background-color: #141924;
    color: {TEXT}; gridline-color: {HAIR};
    border: 1px solid {BORDER}; border-radius: 10px;
    selection-background-color: {ACCENT_WEAK}; selection-color: {ACCENT_2};
    font-size: {base_font_px}px;
}}
QTableView::item, QTableWidget::item, QTreeView::item, QListView::item {{ padding: 5px 7px; }}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{
    background: {SOFT}; color: {MUTED};
    padding: 8px 9px; border: none; border-bottom: 1px solid {BORDER};
    font-size: {base_font_px - 1}px; font-weight: 700;
}}
QTableCornerButton::section {{ background: {SOFT}; border: none; }}

/* ── Tabs ── */
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 10px; top: -1px; }}
QTabBar::tab {{
    background: transparent; color: {MUTED};
    padding: 8px 16px; border: none; border-bottom: 2px solid transparent;
    font-size: {base_font_px}px; font-weight: 600;
}}
QTabBar::tab:hover {{ color: {TEXT}; }}
QTabBar::tab:selected {{ color: {ACCENT_2}; border-bottom: 2px solid {ACCENT}; }}

/* ── GroupBox ── */
QGroupBox {{
    background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px;
    margin-top: 14px; padding: 12px; font-weight: 600;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 5px; color: {MUTED}; }}

/* ── ScrollBars ── */
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #2a3340; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #3a4658; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #2a3340; border-radius: 5px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: #3a4658; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ── Menús ── */
QMenuBar {{ background: {SIDE}; color: {TEXT}; }}
QMenuBar::item:selected {{ background: {PANEL2}; }}
QMenu {{ background: {PANEL}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px; }}
QMenu::item {{ padding: 6px 22px; border-radius: 6px; }}
QMenu::item:selected {{ background: {ACCENT_WEAK}; color: {ACCENT_2}; }}
QMenu::separator {{ height: 1px; background: {HAIR}; margin: 4px 8px; }}

/* ── ProgressBar ── */
QProgressBar {{ background: {SOFT}; border: 1px solid {BORDER}; border-radius: 8px; text-align: center; color: {TEXT}; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 7px; }}

/* ── Sidebar (mismos objectNames que ya usan las apps) ── */
QWidget#sidebar {{ background: {SIDE}; border-right: 1px solid {HAIR}; }}
QLabel#brand {{ color: {TEXT}; font-size: 15px; font-weight: 700; }}
QLabel#brandSub {{ color: {MUTED}; font-size: 9px; }}
QLabel#navSection {{ color: {MUTED}; font-size: 9px; font-weight: 700; }}
QPushButton#nav {{
    background: transparent; color: {MUTED};
    border: none; text-align: left; padding: 9px 14px; border-radius: 10px;
    font-size: 13px; font-weight: 500;
}}
QPushButton#nav:hover {{ background: {SOFT}; color: {TEXT}; }}
QPushButton#nav:checked {{ background: {ACCENT_WEAK}; color: {ACCENT_2}; font-weight: 600; }}
QPushButton#navDisabled {{
    background: transparent; color: {FAINT};
    border: none; text-align: left; padding: 9px 14px; font-size: 13px;
}}

/* ── Tarjetas reutilizables ── */
QFrame#card, QFrame#kpi {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 14px; }}
"""


# QSS por defecto (densidad media). Alias `APP_QSS` para compatibilidad con las
# apps que ya importan un `APP_QSS`.
QSS = qss()
APP_QSS = QSS


def dark_palette():
    """QPalette oscura para que las partes nativas (y los QMessageBox) queden
    en tema oscuro además del stylesheet."""
    from PyQt6.QtGui import QPalette, QColor
    from PyQt6.QtCore import Qt
    p = QPalette()
    c = QColor
    p.setColor(QPalette.ColorRole.Window, c(BG))
    p.setColor(QPalette.ColorRole.WindowText, c(TEXT))
    p.setColor(QPalette.ColorRole.Base, c(PANEL))
    p.setColor(QPalette.ColorRole.AlternateBase, c(SOFT))
    p.setColor(QPalette.ColorRole.Text, c(TEXT))
    p.setColor(QPalette.ColorRole.Button, c(SOFT))
    p.setColor(QPalette.ColorRole.ButtonText, c(TEXT))
    p.setColor(QPalette.ColorRole.ToolTipBase, c(BG_DEEP))
    p.setColor(QPalette.ColorRole.ToolTipText, c(TEXT))
    p.setColor(QPalette.ColorRole.Highlight, c(ACCENT))
    p.setColor(QPalette.ColorRole.HighlightedText, c(ACCENT_INK))
    p.setColor(QPalette.ColorRole.PlaceholderText, c(MUTED))
    p.setColor(QPalette.ColorRole.Link, c(ACCENT_2))
    dis = QPalette.ColorGroup.Disabled
    p.setColor(dis, QPalette.ColorRole.Text, c(FAINT))
    p.setColor(dis, QPalette.ColorRole.ButtonText, c(FAINT))
    p.setColor(dis, QPalette.ColorRole.WindowText, c(FAINT))
    return p


def apply(app, base_font_px: int = 12):
    """Aplica el tema completo a una QApplication: estilo Fusion + paleta oscura
    + stylesheet global. Una sola llamada por app, en su arranque."""
    try:
        app.setStyle("Fusion")
    except Exception:                                   # noqa: BLE001
        pass
    try:
        app.setPalette(dark_palette())
    except Exception:                                   # noqa: BLE001
        pass
    app.setStyleSheet(qss(base_font_px))
    return app
