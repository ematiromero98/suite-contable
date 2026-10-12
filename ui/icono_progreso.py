# -*- coding: utf-8 -*-
# Basado en Lucian UX/UI Prompt #082 · MIT (c) 2026 Seokwoooo
"""
ui/icono_progreso.py — «Actualización en el ícono».

Ícono de una app (su logo) que muestra en sí mismo cómo va su instalación o
actualización:

* **en curso**: un velo oscuro cubre el ícono y se retira en sentido horario
  desde las 12 (barrido cónico, `QPainter.drawPie`) según el avance, con el %
  encima;
* **en cola**: velo completo, sin %;
* **terminado**: aparece con rebote (`QPropertyAnimation`, curva OutBack) un ✓
  menta en la esquina; la leyenda de abajo pasa a «actualizada»;
* **error**: borde e indicador rojos; el motivo queda en el tooltip.

Pintado a mano con QPainter (sin imágenes ni QSS): reutilizable en cualquier
app de la Suite. El avance lo decide quien lo usa (ver `ui/avance.py`).
"""
from PyQt6.QtCore import (Qt, QRectF, QPointF, QPropertyAnimation,
                          QEasingCurve, pyqtProperty)
from PyQt6.QtGui import (QPainter, QPainterPath, QColor, QFont, QPen,
                         QFontMetrics, QPixmap)
from PyQt6.QtWidgets import QWidget

from ui.avance import ETAPAS, FINALES

# Todas las leyendas posibles: el ancho del widget se calcula con la más larga,
# así ninguna queda cortada ni justa.
LEYENDAS = tuple({e[2] for e in ETAPAS.values()} | {f[1] for f in FINALES.values()})

# Paleta del launcher (Panel Oscuro + menta).
_BG = "#0f1218"
_PANEL = "#171c26"
_TEXT = "#eef2f8"
_MUTED = "#8a94a6"
_MENTA = "#2ee6a6"
_MENTA_INK = "#04120c"
_WARN = "#f6b64b"
_BAD = "#f6465d"

REPOSO, COLA, PROGRESO, OK, AVISO, ERROR = (
    "reposo", "cola", "progreso", "ok", "aviso", "error")

_VELO = QColor(15, 18, 24, 184)       # rgba(15,18,24,.72), como la referencia


class IconoProgreso(QWidget):
    """Logo de app con progreso de instalación/actualización pintado encima.

    pixmap   logo de la app (si es None/nulo se dibuja un cuadrado del `color`
             con el monograma `mono`).
    lado     lado del ícono en px; radio = esquinas redondeadas.
    leyenda  si True, reserva una línea de texto debajo del ícono."""

    def __init__(self, pixmap=None, lado=44, radio=13, color=_MENTA, mono="",
                 leyenda=True, leyendas=LEYENDAS, parent=None):
        super().__init__(parent)
        self._pm = pixmap if (pixmap is not None and not pixmap.isNull()) else None
        self._lado = int(lado)
        self._radio = float(radio)
        self._color = QColor(color)
        self._mono = mono or ""
        self._con_leyenda = bool(leyenda)
        self._estado = REPOSO
        self._avance = 0.0
        self._escala = 0.0
        self._texto = ""
        self._detalle = ""

        self._anim_avance = QPropertyAnimation(self, b"avance", self)
        self._anim_avance.setDuration(220)
        self._anim_avance.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_check = QPropertyAnimation(self, b"escala", self)
        self._anim_check.setDuration(460)
        self._anim_check.setEasingCurve(QEasingCurve.Type.OutBack)

        # Ancho = el del ícono o el de la leyenda más larga (en negrita, la
        # variante más ancha) + aire a los costados, lo que sea mayor.
        fm_ley = QFontMetrics(self._fuente_leyenda(negrita=True))
        ancho = self._lado + 12
        alto = self._lado + 8
        if self._con_leyenda:
            ancho = max(ancho, max((fm_ley.horizontalAdvance(t) for t in leyendas),
                                   default=0) + 24)
            alto += fm_ley.height() + 6
        self.setFixedSize(int(ancho), int(alto))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    # ------------------------------------------------------------ propiedades
    def _get_avance(self):
        return self._avance

    def _set_avance(self, v):
        self._avance = max(0.0, min(1.0, float(v)))
        self.update()

    avance = pyqtProperty(float, _get_avance, _set_avance)

    def _get_escala(self):
        return self._escala

    def _set_escala(self, v):
        self._escala = float(v)
        self.update()

    escala = pyqtProperty(float, _get_escala, _set_escala)

    @property
    def estado(self):
        return self._estado

    @property
    def texto(self):
        return self._texto

    @property
    def detalle(self):
        return self._detalle

    # ------------------------------------------------------------- API pública
    def reposo(self, texto=""):
        """Sin velo ni indicadores (estado normal de la tarjeta)."""
        self._anim_avance.stop()
        self._anim_check.stop()
        self._estado, self._avance, self._escala = REPOSO, 0.0, 0.0
        self._texto, self._detalle = texto, ""
        self.setToolTip("")
        self.update()

    def en_cola(self, texto="en cola"):
        """Velo completo: espera su turno."""
        self._anim_avance.stop()
        self._anim_check.stop()
        self._estado, self._avance, self._escala = COLA, 0.0, 0.0
        self._texto, self._detalle = texto, ""
        self.setToolTip("En cola: se actualiza cuando termine la anterior.")
        self.update()

    def avanzar(self, fraccion, texto=None, animar=True):
        """Fija el avance (0..1). Saltos grandes se animan; los chicos (los del
        temporizador) se aplican directo para no encolar animaciones."""
        if self._estado != PROGRESO:
            self._anim_check.stop()
            self._estado, self._escala, self._detalle = PROGRESO, 0.0, ""
            self.setToolTip("")
        if texto is not None:
            self._texto = texto
        f = max(0.0, min(1.0, float(fraccion)))
        if animar and abs(f - self._avance) > 0.04:
            self._anim_avance.stop()
            self._anim_avance.setStartValue(self._avance)
            self._anim_avance.setEndValue(f)
            self._anim_avance.start()
        elif self._anim_avance.state() != QPropertyAnimation.State.Running:
            self._set_avance(f)
        else:
            self._anim_avance.setEndValue(f)
        self.update()

    def terminar(self, texto="actualizada", aviso=False, detalle=""):
        """Velo fuera + ✓ con rebote (menta; ámbar «!» si `aviso`)."""
        self._anim_avance.stop()
        self._avance = 1.0
        self._estado = AVISO if aviso else OK
        self._texto, self._detalle = texto, detalle or ""
        self.setToolTip(self._detalle)
        self._rebotar()

    def fallar(self, detalle, texto="error"):
        """Borde e indicador rojos; el motivo va al tooltip."""
        self._anim_avance.stop()
        self._estado, self._avance = ERROR, 1.0
        self._texto, self._detalle = texto, (detalle or "").strip()
        self.setToolTip("Falló: " + (self._detalle or "error desconocido"))
        self._rebotar()

    def _rebotar(self):
        self._anim_check.stop()
        self._anim_check.setStartValue(0.0)
        self._anim_check.setEndValue(1.0)
        self._anim_check.start()
        self.update()

    # ------------------------------------------------------------------ fuentes
    def _fuente_pct(self):
        f = QFont("Segoe UI")
        f.setPixelSize(max(9, min(12, int(self._lado * 0.23))))
        f.setWeight(QFont.Weight.DemiBold)
        return f

    @staticmethod
    def _fuente_leyenda(negrita=False):
        f = QFont("Segoe UI")
        f.setPixelSize(10)
        f.setWeight(QFont.Weight.DemiBold if negrita else QFont.Weight.Normal)
        return f

    def rect_pastilla(self):
        """Rectángulo de la pastilla del %: ancho fijo (el de «100%») para que
        no salte al cambiar de cifra; nunca más ancho que el ícono."""
        fm = QFontMetrics(self._fuente_pct())
        r = self._rect_icono()
        pw = min(fm.horizontalAdvance("100%") + 12, r.width() - 4)
        ph = fm.height() + 4
        return QRectF(r.center().x() - pw / 2, r.center().y() - ph / 2, pw, ph)

    # --------------------------------------------------------------- geometría
    def _rect_icono(self):
        x = (self.width() - self._lado) / 2.0
        return QRectF(x, 4.0, self._lado, self._lado)

    # ------------------------------------------------------------------ pintar
    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = self._rect_icono()
        forma = QPainterPath()
        forma.addRoundedRect(r, self._radio, self._radio)

        # 1) Logo (o cuadrado de color + monograma si no hay PNG).
        p.save()
        p.setClipPath(forma)
        if self._pm is not None:
            p.drawPixmap(r, self._pm, QRectF(self._pm.rect()))
        else:
            p.fillPath(forma, self._color)
            f = QFont("Segoe UI")
            f.setPixelSize(max(9, int(self._lado * 0.30)))
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor("#ffffff"))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, self._mono)

        # 2) Velo cónico: cubre desde el ángulo del avance hasta las 12, en
        #    sentido horario. Qt mide en 1/16 de grado, positivo = antihorario
        #    y 0 = las 3: el borde «revelado» arranca en 90° y gira -360·k.
        if self._estado in (COLA, PROGRESO):
            k = 0.0 if self._estado == COLA else self._avance
            if k < 1.0:
                lado2 = self._lado * 1.5          # que cubra las esquinas
                pie = QRectF(r.center().x() - lado2 / 2,
                             r.center().y() - lado2 / 2, lado2, lado2)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(_VELO)
                inicio = int(round((90.0 - 360.0 * k) * 16))
                barrido = -int(round(360.0 * (1.0 - k) * 16))
                p.drawPie(pie, inicio, barrido)
        p.restore()

        # 3) % encima del ícono.
        if self._estado == PROGRESO:
            p.setFont(self._fuente_pct())
            txt = f"{int(round(self._avance * 100))}%"
            # Pastilla oscura detrás del %: el logo trae su monograma y sin
            # esto los dos textos se pisan en la parte ya revelada.
            pastilla = self.rect_pastilla()
            ph = pastilla.height()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(15, 18, 24, 215))
            p.drawRoundedRect(pastilla, ph / 2, ph / 2)
            p.setPen(QColor(_TEXT))
            p.drawText(pastilla, Qt.AlignmentFlag.AlignCenter, txt)

        # 4) Borde rojo si falló.
        if self._estado == ERROR:
            pen = QPen(QColor(_BAD))
            pen.setWidthF(2.0)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1),
                              self._radio - 1, self._radio - 1)

        # 5) Indicador de la esquina (✓ / ! ) con rebote.
        if self._estado in (OK, AVISO, ERROR) and self._escala > 0.01:
            self._pintar_insignia(p, r)

        # 6) Leyenda debajo.
        if self._con_leyenda and self._texto:
            colores = {OK: _MENTA, AVISO: _WARN, ERROR: _BAD}
            f = self._fuente_leyenda(negrita=self._estado in colores)
            p.setFont(f)
            p.setPen(QColor(colores.get(self._estado, _MUTED)))
            caja = QRectF(0, r.bottom() + 5, self.width(),
                          QFontMetrics(f).height() + 2)
            txt = QFontMetrics(f).elidedText(self._texto,
                                             Qt.TextElideMode.ElideRight,
                                             self.width())
            p.drawText(caja, Qt.AlignmentFlag.AlignHCenter
                       | Qt.AlignmentFlag.AlignTop, txt)
        p.end()

    def _pintar_insignia(self, p, r):
        d = max(14.0, self._lado * 0.40)
        c = QPointF(r.right() - d * 0.22, r.bottom() - d * 0.22)
        p.save()
        p.translate(c)
        p.scale(self._escala, self._escala)
        fondo = {OK: _MENTA, AVISO: _WARN, ERROR: _BAD}[self._estado]
        aro = QPen(QColor(_PANEL))
        aro.setWidthF(2.0)
        p.setPen(aro)
        p.setBrush(QColor(fondo))
        p.drawEllipse(QPointF(0, 0), d / 2, d / 2)
        tinta = QPen(QColor(_MENTA_INK if self._estado == OK else _BG))
        tinta.setWidthF(max(1.6, d * 0.13))
        tinta.setCapStyle(Qt.PenCapStyle.RoundCap)
        tinta.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(tinta)
        p.setBrush(Qt.BrushStyle.NoBrush)
        u = d / 2
        if self._estado == OK:
            check = QPainterPath(QPointF(-0.42 * u, 0.02 * u))
            check.lineTo(QPointF(-0.12 * u, 0.32 * u))
            check.lineTo(QPointF(0.44 * u, -0.30 * u))
            p.drawPath(check)
        else:                                   # «!»
            p.drawLine(QPointF(0, -0.42 * u), QPointF(0, 0.10 * u))
            p.drawPoint(QPointF(0, 0.40 * u))
        p.restore()


def pixmap_logo(ruta, lado, dpr=2):
    """Carga y escala nítido (hi-DPI) el PNG de un logo; QPixmap nulo si falta."""
    pm = QPixmap(ruta)
    if pm.isNull():
        return pm
    pm = pm.scaled(int(lado * dpr), int(lado * dpr),
                   Qt.AspectRatioMode.KeepAspectRatio,
                   Qt.TransformationMode.SmoothTransformation)
    pm.setDevicePixelRatio(dpr)
    return pm
