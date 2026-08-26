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
    QStackedBarSeries, QBarCategoryAxis, QValueAxis, QCategoryAxis,
    QLineSeries, QAreaSeries, QPieSeries,
)
from PyQt6.QtCore import Qt, QMargins, QPointF, QRectF
from PyQt6.QtGui import (QColor, QPainter, QLinearGradient, QBrush, QPen, QFont,
                         QPainterPath)
from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
                             QSizePolicy)

from suite_theme import (TEXT, MUTED, HAIR, BORDER, PANEL, ACCENT,
                         BG_DEEP, ACCENT_INK, GOOD, WARN, BAD)
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
    # Relleno con degradé sutil (look boardui) en vez de color plano.
    _grad = QLinearGradient(0, 0, (1 if horizontal else 0), (0 if horizontal else 1))
    _grad.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
    _c1 = QColor(color); _c2 = QColor(color); _c2.setAlpha(140)
    _grad.setColorAt(0, _c1); _grad.setColorAt(1, _c2)
    bset.setBrush(QBrush(_grad))
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


# ════════════════════════════════════════════════════════════════════════════
#  Componentes "boardui": KPI card, sparkline, gauge y funnel (pintados a mano,
#  sin depender de QtCharts, así funcionan aun sin PyQt6-Charts).
# ════════════════════════════════════════════════════════════════════════════
_CARD_INNER = BG_DEEP        # pista / fondo interno


class Sparkline(QWidget):
    """Mini línea + área con degradé para meter dentro de una KPI card."""

    def __init__(self, valores, color=ACCENT, parent=None):
        super().__init__(parent)
        self._v = [float(x or 0) for x in (valores or [])]
        self._c = QColor(color)
        self.setFixedSize(104, 32)

    def set_valores(self, valores):
        self._v = [float(x or 0) for x in (valores or [])]
        self.update()

    def paintEvent(self, _e):
        if len(self._v) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h, pad = self.width(), self.height(), 3
        lo, hi = min(self._v), max(self._v)
        rng = (hi - lo) or 1
        n = len(self._v)
        pts = [QPointF(pad + i * (w - 2 * pad) / (n - 1),
                       h - pad - (v - lo) / rng * (h - 2 * pad))
               for i, v in enumerate(self._v)]
        grad = QLinearGradient(0, 0, 0, h)
        c1 = QColor(self._c); c1.setAlpha(90)
        c2 = QColor(self._c); c2.setAlpha(0)
        grad.setColorAt(0, c1); grad.setColorAt(1, c2)
        area = QPainterPath(); area.moveTo(pts[0].x(), h)
        for pt in pts:
            area.lineTo(pt)
        area.lineTo(pts[-1].x(), h); area.closeSubpath()
        p.fillPath(area, QBrush(grad))
        p.setPen(QPen(self._c, 1.7, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        path = QPainterPath(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        p.drawPath(path)
        p.setBrush(QBrush(self._c)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(pts[-1], 2.4, 2.4)
        p.end()


class KpiCard(QFrame):
    """Tarjeta de métrica: etiqueta + valor grande + (badge de variación o
    subtítulo) + sparkline opcional. `delta` es un texto ya formateado."""

    def __init__(self, titulo: str, valor: str, *, delta: str = None,
                 delta_up: bool = True, sub: str = None, color: str = ACCENT,
                 spark=None, parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        self.setStyleSheet(
            f"QFrame#kpiCard{{background:{PANEL};border:1px solid {BORDER};"
            f"border-radius:14px;}}")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay = QVBoxLayout(self); lay.setContentsMargins(15, 13, 15, 13); lay.setSpacing(7)

        top = QHBoxLayout(); top.setSpacing(8)
        punto = QLabel(); punto.setFixedSize(9, 9)
        punto.setStyleSheet(f"background:{color};border-radius:4px;")
        lb = QLabel(titulo); lb.setStyleSheet(f"color:{MUTED};font-size:12px;background:transparent;")
        top.addWidget(punto); top.addWidget(lb); top.addStretch()
        lay.addLayout(top)

        val = QLabel(valor)
        val.setStyleSheet(f"color:{TEXT};font-size:23px;font-weight:700;background:transparent;")
        lay.addWidget(val)

        row = QHBoxLayout(); row.setSpacing(10)
        if delta is not None:
            col = GOOD if delta_up else BAD
            arrow = "▲" if delta_up else "▼"
            bg = "rgba(46,230,166,.12)" if delta_up else "rgba(246,70,93,.12)"
            badge = QLabel(f"{arrow} {delta}")
            badge.setStyleSheet(
                f"color:{col};background:{bg};border-radius:6px;"
                f"padding:2px 8px;font-size:11px;font-weight:600;")
            row.addWidget(badge)
        elif sub:
            s = QLabel(sub); s.setStyleSheet(f"color:{MUTED};font-size:11px;background:transparent;")
            row.addWidget(s)
        row.addStretch()
        if spark is not None and len(spark) >= 2:
            row.addWidget(Sparkline(spark, color))
        lay.addLayout(row)


class GaugeWidget(QWidget):
    """Semicírculo con % al centro."""

    def __init__(self, pct: float, titulo: str = "", color=ACCENT, parent=None):
        super().__init__(parent)
        self._pct = max(0.0, min(100.0, float(pct or 0)))
        self._titulo = titulo
        self._c = QColor(color)
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_pct(self, pct):
        self._pct = max(0.0, min(100.0, float(pct or 0)))
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        margen = 22
        lado = min(w - 2 * margen, (h - 26) * 2)
        r = lado / 2
        cx = w / 2
        cy = h - 30
        rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        p.setPen(QPen(QColor(_CARD_INNER), 17, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(rect, 180 * 16, -180 * 16)
        p.setPen(QPen(self._c, 17, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(rect, 180 * 16, -int(180 * 16 * self._pct / 100))
        p.setPen(QColor(TEXT))
        f = QFont("Segoe UI", 21); f.setBold(True); p.setFont(f)
        p.drawText(QRectF(cx - r, cy - r * 0.7, 2 * r, r * 0.7),
                   Qt.AlignmentFlag.AlignCenter, f"{self._pct:.0f}%")
        if self._titulo:
            p.setPen(QColor(MUTED)); p.setFont(QFont("Segoe UI", 10))
            p.drawText(QRectF(cx - r, cy - r * 0.12, 2 * r, 20),
                       Qt.AlignmentFlag.AlignCenter, self._titulo)
        p.end()


class FunnelWidget(QWidget):
    """Barras horizontales decrecientes con etiqueta y valor. `pasos` =
    [(label, valor), ...] de mayor a menor."""

    def __init__(self, pasos, fmt=None, parent=None):
        super().__init__(parent)
        self._pasos = [(str(l), float(v or 0)) for l, v in (pasos or [])]
        self._fmt = fmt or (lambda v: f"{int(v):,}".replace(",", "."))
        self.setMinimumHeight(max(120, 46 * len(self._pasos)))

    def paintEvent(self, _e):
        if not self._pasos:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        n = len(self._pasos); gap = 10
        bh = min(34, (h - gap * (n - 1)) / n)
        base = max((v for _, v in self._pasos), default=1) or 1
        meta_w = 160
        avail = max(w - meta_w, 40)
        y = (h - (bh * n + gap * (n - 1))) / 2
        for i, (label, val) in enumerate(self._pasos):
            frac = (val / base) if base else 0
            bw = max(avail * frac, 6)
            col = QColor(PALETTE[i % len(PALETTE)])
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(_CARD_INNER))
            p.drawRoundedRect(QRectF(0, y, avail, bh), 8, 8)
            grad = QLinearGradient(0, 0, bw, 0)
            c2 = QColor(col); c2.setAlpha(200)
            grad.setColorAt(0, col); grad.setColorAt(1, c2)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(QRectF(0, y, bw, bh), 8, 8)
            p.setPen(QColor(ACCENT_INK))
            f = QFont("Segoe UI", 9); f.setBold(True); p.setFont(f)
            p.drawText(QRectF(12, y, bw - 12, bh),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)
            p.setPen(QColor(MUTED)); p.setFont(QFont("Segoe UI", 9))
            p.drawText(QRectF(avail + 10, y, meta_w - 10, bh),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                       f"{self._fmt(val)}  ·  {round(frac*100)}%")
            y += bh + gap
        p.end()


def stacked(cats, series_defs, titulo: str = "") -> QChartView:
    """Barras apiladas. `series_defs` = [(label, [valores], color), ...]."""
    chart = QChart()
    if titulo:
        chart.setTitle(titulo)
    series = QStackedBarSeries()
    for label, valores, color in series_defs:
        bs = QBarSet(label)
        for v in valores:
            bs.append(float(v or 0))
        bs.setColor(QColor(color))
        bs.setBorderColor(QColor(PANEL))
        series.append(bs)
    chart.addSeries(series)
    ax = QBarCategoryAxis(); ax.append([str(c) for c in cats])
    chart.addAxis(ax, Qt.AlignmentFlag.AlignBottom); series.attachAxis(ax)
    tope = 1.0
    for i in range(len(cats)):
        tope = max(tope, sum(float(v[i] or 0) for _, v, _ in series_defs))
    ay = QValueAxis(); ay.setRange(0, tope * 1.15)
    chart.addAxis(ay, Qt.AlignmentFlag.AlignLeft); series.attachAxis(ay)
    chart.legend().setVisible(True)
    chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
    theme_chart(chart, recolor=False)
    return theme_view(QChartView(chart))


def bars_trend(items, linea, color: str = ACCENT, linea_label: str = "Tendencia",
               titulo: str = "") -> QChartView:
    """Barras (degradé) + línea en un eje secundario propio (así las barras no
    se aplastan cuando la línea es un acumulado mucho mayor). `items` =
    [(label, value), ...]; `linea` = [y, ...] del mismo largo."""
    chart = QChart()
    if titulo:
        chart.setTitle(titulo)
    labels = [str(l) for l, _ in items]
    vals = [float(v or 0) for _, v in items]
    bset = QBarSet("")
    for v in vals:
        bset.append(v)
    g = QLinearGradient(0, 0, 0, 1)
    g.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
    c1 = QColor(color); c2 = QColor(color); c2.setAlpha(140)
    g.setColorAt(0, c1); g.setColorAt(1, c2)
    bset.setBrush(QBrush(g)); bset.setColor(QColor(color)); bset.setBorderColor(QColor(PANEL))
    series = QBarSeries(); series.append(bset)
    chart.addSeries(series)
    ax = QBarCategoryAxis(); ax.append(labels)
    chart.addAxis(ax, Qt.AlignmentFlag.AlignBottom); series.attachAxis(ax)
    ay = QValueAxis(); ay.setRange(0, (max(vals) if vals else 1) * 1.15)
    chart.addAxis(ay, Qt.AlignmentFlag.AlignLeft); series.attachAxis(ay)

    ls = QLineSeries(); ls.setName(linea_label)
    for i, v in enumerate(linea):
        ls.append(i, float(v or 0))
    lp = QPen(QColor("#5bb0ff")); lp.setWidthF(2.4); lp.setCapStyle(Qt.PenCapStyle.RoundCap)
    ls.setPen(lp)
    chart.addSeries(ls)
    axx = QValueAxis(); axx.setRange(-0.5, len(labels) - 0.5); axx.setVisible(False)
    chart.addAxis(axx, Qt.AlignmentFlag.AlignBottom); ls.attachAxis(axx)
    ay2 = QValueAxis(); ay2.setRange(0, (max([float(v or 0) for v in linea]) or 1) * 1.10)
    chart.addAxis(ay2, Qt.AlignmentFlag.AlignRight); ls.attachAxis(ay2)
    ay2.setLabelsColor(QColor("#5bb0ff"))

    chart.legend().setVisible(True)
    chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
    theme_chart(chart, recolor=False)
    return theme_view(QChartView(chart))


# ════════════════════════════════════════════════════════════════════════════
#  WaterfallChart — cascada del resultado (pintada a mano, sin QtCharts)
# ════════════════════════════════════════════════════════════════════════════
class WaterfallChart(QWidget):
    """Cascada Ingresos → (egresos, restando) → Resultado. Pintada a mano.
    `egresos` = [(label, monto), ...] (montos positivos, se restan)."""

    def __init__(self, ingresos=0.0, egresos=None, resultado=None, parent=None):
        super().__init__(parent)
        self._pasos = []
        self.setMinimumHeight(240)
        self.set_datos(ingresos, egresos, resultado)

    def _fmt(self, v):
        a = abs(float(v or 0))
        s = "-" if v < 0 else ""
        if a >= 1e6:
            return f"{s}${a/1e6:.1f}".replace(".", ",") + "M"
        if a >= 1e3:
            return f"{s}${a/1e3:.0f}k"
        return f"{s}${a:.0f}"

    def set_datos(self, ingresos, egresos=None, resultado=None):
        ing = float(ingresos or 0)
        egr = [(str(l), float(m or 0)) for l, m in (egresos or []) if float(m or 0) > 0]
        if resultado is None:
            resultado = ing - sum(m for _, m in egr)
        pasos = [("Ingresos", 0.0, ing, ACCENT, ing)]   # (label, y0, y1, color, valor)
        run = ing
        for lbl, m in egr:
            pasos.append((lbl, run - m, run, WARN, -m))
            run -= m
        col = GOOD if resultado >= 0 else BAD
        pasos.append(("Resultado", 0.0, float(resultado), col, float(resultado)))
        self._pasos = pasos
        self.update()

    def paintEvent(self, _e):
        if not self._pasos:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        top_m, bot_m = 22, 40
        plot_h = h - top_m - bot_m
        vmax = max([max(abs(y0), abs(y1)) for _, y0, y1, _, _ in self._pasos] + [1])
        n = len(self._pasos)
        step = w / n
        bw = min(46, step * 0.6)

        def Y(v):
            return top_m + plot_h - (v / vmax) * plot_h

        prev_x = prev_y = None
        for i, (label, y0, y1, color, valor) in enumerate(self._pasos):
            cx = step * (i + 0.5)
            x = cx - bw / 2
            yt, yb = Y(max(y0, y1)), Y(min(y0, y1))
            # conector con la barra anterior (línea de nivel)
            if prev_x is not None:
                p.setPen(QPen(QColor(BORDER), 1, Qt.PenStyle.DashLine))
                p.drawLine(int(prev_x), int(prev_y), int(x), int(prev_y))
            col = QColor(color)
            grad = QLinearGradient(0, yt, 0, yb)
            c2 = QColor(col); c2.setAlpha(150)
            grad.setColorAt(0, col); grad.setColorAt(1, c2)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(grad))
            p.drawRoundedRect(QRectF(x, yt, bw, max(yb - yt, 2)), 4, 4)
            # valor arriba
            p.setPen(QColor(TEXT)); f = _font(8, bold=True); p.setFont(f)
            p.drawText(QRectF(cx - step / 2, yt - 16, step, 14),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                       self._fmt(valor))
            # etiqueta abajo
            p.setPen(QColor(MUTED)); p.setFont(_font(8))
            et = label if len(label) <= 12 else label[:11] + "…"
            p.drawText(QRectF(cx - step / 2, h - bot_m + 4, step, bot_m - 6),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, et)
            prev_x, prev_y = x + bw, Y(y1)
        p.end()
