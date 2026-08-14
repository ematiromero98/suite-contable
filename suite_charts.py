# -*- coding: utf-8 -*-
"""
suite_charts — Gráficos themeados de la Suite Contable (dark + acento menta).

Motor de gráficos compartido sobre **QtCharts**, con la "vuelta de tuerca":
fondo transparente, grilla tenue, paleta categórica **validada CVD**, etiquetas
de valor y dona con total al centro. Vive en `suite-contable`; las apps que
grafican lo importan (necesita `PyQt6-QtCharts`, que ya tienen Employee Pro y
RetencionesPro; el resto lo agrega a su requirements si suma gráficos).

API principal:
    theme_chart(chart)                 -> re-tinta un QChart existente (retrofit)
    theme_view(view)                   -> ajusta un QChartView (antialias, fondo)
    area(points, ...)                  -> QChartView de evolución (área + degradé)
    bars(items, ...) / hbars(items,..) -> QChartView de barras (vert/horiz)
    donut(items, ...)                  -> QWidget con dona + total al centro

`items` = [(etiqueta, valor), ...]. `points` = [(x_label, y), ...].
"""
from __future__ import annotations

from PyQt6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet, QHorizontalBarSeries,
    QBarCategoryAxis, QValueAxis, QCategoryAxis, QLineSeries, QAreaSeries, QPieSeries,
)
from PyQt6.QtCore import Qt, QMargins, QPointF
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QBrush, QPen, QFont

from suite_theme import TEXT, MUTED, HAIR, BORDER, PANEL, ACCENT
# Paleta categórica validada (ver dataviz): menta·azul·ámbar·rosa. Distinción
# CVD ΔE >= 8 en oscuro. A partir del 5º color hace falta encoding secundario.
PALETTE = ["#2ee6a6", "#5bb0ff", "#f6b64b", "#e879c7", "#a0aec0", "#f6465d"]

_GRID = QColor(HAIR)
_AXIS = QColor(MUTED)
_INK = QColor(TEXT)


def _font(px=10, bold=False):
    f = QFont("Segoe UI", px)
    f.setBold(bold)
    return f


def theme_view(view: QChartView) -> QChartView:
    """Ajustes de render de un QChartView (antialias + fondo transparente)."""
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.setStyleSheet("background: transparent; border: none;")
    view.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
    return view


def theme_chart(chart: QChart, recolor: bool = True) -> QChart:
    """Aplica el tema oscuro a un QChart YA construido (retrofit de gráficos que
    la app arma por su cuenta). Fondo transparente, grilla tenue, textos claros
    y, si `recolor`, re-tinta las series con la paleta de la Suite."""
    chart.setBackgroundVisible(False)
    chart.setPlotAreaBackgroundVisible(False)
    chart.setMargins(QMargins(0, 0, 0, 0))
    chart.setBackgroundRoundness(0)
    # NB: NO habilitar animaciones acá. `setAnimationOptions` sobre un
    # QAreaSeries con QCategoryAxis segfaultea QtCharts (acceso inválido al
    # calcular la geometría animada). El tema no las necesita.
    chart.setTitleBrush(QBrush(_INK))
    chart.setTitleFont(_font(11, bold=True))

    leg = chart.legend()
    leg.setLabelColor(_INK)
    leg.setFont(_font(9))
    try:
        leg.setMarkerShape(leg.MarkerShape.MarkerShapeCircle)
    except Exception:                                   # noqa: BLE001
        pass

    for ax in chart.axes():
        ax.setLabelsColor(_AXIS)
        ax.setTitleBrush(QBrush(_AXIS))
        ax.setLabelsFont(_font(9))
        gp = QPen(_GRID); gp.setWidthF(1.0)
        ax.setGridLinePen(gp)
        lp = QPen(QColor(BORDER)); lp.setWidthF(1.0)
        ax.setLinePen(lp)
        try:
            ax.setMinorGridLineVisible(False)
        except Exception:                               # noqa: BLE001
            pass

    if recolor:
        _recolor(chart)
    return chart


def _recolor(chart: QChart):
    """Re-tinta series conocidas con la paleta (best-effort)."""
    for s in chart.series():
        try:
            if isinstance(s, (QBarSeries, QHorizontalBarSeries)):
                for i in range(s.count()):
                    bs = s.barSets()[i]
                    bs.setColor(QColor(PALETTE[i % len(PALETTE)]))
                    bs.setBorderColor(QColor(PANEL))
            elif isinstance(s, QPieSeries):
                for i, sl in enumerate(s.slices()):
                    sl.setColor(QColor(PALETTE[i % len(PALETTE)]))
                    sl.setBorderColor(QColor(PANEL))
                    sl.setBorderWidth(2)
                    sl.setLabelColor(_INK)
            elif isinstance(s, QLineSeries):
                p = QPen(QColor(ACCENT)); p.setWidthF(2.4)
                s.setPen(p)
        except Exception:                               # noqa: BLE001
            pass


def _axes(chart, cats, vmax):
    ax = QBarCategoryAxis()
    ax.append([str(c) for c in cats])
    chart.addAxis(ax, Qt.AlignmentFlag.AlignBottom)
    ay = QValueAxis()
    ay.setRange(0, vmax * 1.12 if vmax else 1)
    ay.setLabelFormat("%d")
    chart.addAxis(ay, Qt.AlignmentFlag.AlignLeft)
    return ax, ay


def bars(items, color: str = ACCENT, titulo: str = "", horizontal: bool = False) -> QChartView:
    """Barras de una serie. `items` = [(label, value), ...]."""
    chart = QChart()
    if titulo:
        chart.setTitle(titulo)
    labels = [str(l) for l, _ in items]
    vals = [float(v or 0) for _, v in items]
    bset = QBarSet("")
    for v in vals:
        bset.append(v)
    bset.setColor(QColor(color))
    bset.setBorderColor(QColor(PANEL))
    series = QHorizontalBarSeries() if horizontal else QBarSeries()
    series.setLabelsVisible(True)
    try:
        series.setLabelsPosition(series.LabelsPosition.LabelsOutsideEnd)
    except Exception:                                   # noqa: BLE001
        pass
    series.append(bset)
    chart.addSeries(series)
    vmax = max(vals) if vals else 1
    ax = QBarCategoryAxis(); ax.append(labels)
    ay = QValueAxis(); ay.setRange(0, vmax * 1.15)
    if horizontal:
        chart.addAxis(ay, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(ax, Qt.AlignmentFlag.AlignLeft)
    else:
        chart.addAxis(ax, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(ay, Qt.AlignmentFlag.AlignLeft)
    series.attachAxis(ax); series.attachAxis(ay)
    chart.legend().setVisible(False)
    theme_chart(chart, recolor=False)
    v = QChartView(chart)
    return theme_view(v)


def hbars(items, color: str = ACCENT, titulo: str = "") -> QChartView:
    return bars(items, color=color, titulo=titulo, horizontal=True)


def area(points, color: str = ACCENT, titulo: str = "") -> QChartView:
    """Evolución con área + degradé (la 'vuelta de tuerca'). `points` =
    [(x_label, y), ...] — el eje X toma las etiquetas en orden."""
    chart = QChart()
    if titulo:
        chart.setTitle(titulo)
    labels = [str(l) for l, _ in points]
    vals = [float(v or 0) for _, v in points]
    # OJO: la QLineSeries del área NO se agrega también al chart (el QAreaSeries
    # ya la posee; agregarla de nuevo corrompe el chart y segfaultea). El trazo
    # visible es una línea SEPARATE con los mismos puntos.
    upper = QLineSeries()
    for i, v in enumerate(vals):
        upper.append(float(i), v)
    a = QAreaSeries(upper)
    grad = QLinearGradient(QPointF(0, 0), QPointF(0, 1))
    grad.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
    cc = QColor(color); cc.setAlphaF(0.34)
    grad.setColorAt(0.0, cc)
    c2 = QColor(color); c2.setAlphaF(0.0)
    grad.setColorAt(1.0, c2)
    a.setBrush(QBrush(grad))
    a.setPen(QPen(Qt.GlobalColor.transparent))

    line = QLineSeries()
    for i, v in enumerate(vals):
        line.append(float(i), v)
    lp = QPen(QColor(color)); lp.setWidthF(2.4)
    lp.setCapStyle(Qt.PenCapStyle.RoundCap); lp.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    line.setPen(lp)

    chart.addSeries(a)
    chart.addSeries(line)

    n = len(vals)
    # Eje X de categorías POSICIONADAS (QCategoryAxis): un solo eje, las
    # etiquetas caen sobre el índice de cada punto. Evita el doble eje frágil.
    axx = QCategoryAxis()
    axx.setRange(0, n - 1 if n > 1 else 1)
    for i, lab in enumerate(labels):
        axx.append(lab, i)
    try:
        axx.setLabelsPosition(QCategoryAxis.AxisLabelsPosition.AxisLabelsPositionOnValue)
    except Exception:                                   # noqa: BLE001
        pass
    axy = QValueAxis()
    axy.setRange(0, (max(vals) if vals else 1) * 1.15)
    axy.setLabelFormat("%d")
    chart.addAxis(axx, Qt.AlignmentFlag.AlignBottom)
    chart.addAxis(axy, Qt.AlignmentFlag.AlignLeft)
    for s in (a, line):
        s.attachAxis(axx)
        s.attachAxis(axy)
    chart.legend().setVisible(False)
    theme_chart(chart, recolor=False)
    v = QChartView(chart)
    return theme_view(v)


def donut(items, center_top: str = "", center_bottom: str = "TOTAL", hole: float = 0.62):
    """Dona con total al centro. Devuelve un QWidget contenedor (dona + overlay
    con el texto central). `items` = [(label, value), ...]."""
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout

    chart = QChart()
    chart.legend().setVisible(False)
    serie = QPieSeries()
    serie.setHoleSize(hole)
    serie.setPieSize(0.98)
    for i, (lab, val) in enumerate(items):
        sl = serie.append(str(lab), float(val or 0))
        sl.setColor(QColor(PALETTE[i % len(PALETTE)]))
        sl.setBorderColor(QColor(PANEL))
        sl.setBorderWidth(3)
        sl.setLabelVisible(False)
    chart.addSeries(serie)
    theme_chart(chart, recolor=False)
    view = theme_view(QChartView(chart))

    cont = QWidget()
    grid = QGridLayout(cont)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.addWidget(view, 0, 0)
    overlay = QWidget()
    overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    # El overlay va ARRIBA de la dona: si pintara su fondo (del tema global) la
    # taparía. Forzarlo transparente.
    overlay.setStyleSheet("background: transparent;")
    ov = QVBoxLayout(overlay)
    ov.setContentsMargins(0, 0, 0, 0)
    ov.setSpacing(0)
    top = QLabel(center_top)
    top.setAlignment(Qt.AlignmentFlag.AlignCenter)
    top.setStyleSheet(f"background:transparent; color:{TEXT}; font-size:17px; font-weight:600;")
    bot = QLabel(center_bottom)
    bot.setAlignment(Qt.AlignmentFlag.AlignCenter)
    bot.setStyleSheet(f"background:transparent; color:{MUTED}; font-size:9px; font-weight:700;")
    ov.addStretch(); ov.addWidget(top); ov.addWidget(bot); ov.addStretch()
    grid.addWidget(overlay, 0, 0)
    return cont
