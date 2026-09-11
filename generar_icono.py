# -*- coding: utf-8 -*-
"""generar_icono.py — Ícono de Suite Contable (launcher) con el molde común de la Suite Contable:
cuadrado redondeado, degradé diagonal (tinte claro → sombra) del color de la app
en el launcher (#2E86C1) y el monograma «SC» en blanco (Segoe UI Bold).

    python generar_icono.py

Genera: assets/suite.ico, assets/suite.png
El mismo molde (y monograma) lo usa suite-contable/generar_iconos_apps.py para
las tarjetas del launcher: si se cambia acá, cambiarlo allá también.
"""
import os

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
COLOR = "#2E86C1"
MONO = "SC"
SALIDAS = ['assets/suite.ico', 'assets/suite.png']
S, R = 256, 52


def _hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mix(c, to, t):
    return tuple(round(c[i] + (to[i] - c[i]) * t) for i in range(3))


def _paleta(color):
    c = _hex2rgb(color)
    claro = (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) > 150
    top = c if claro else _mix(c, (255, 255, 255), 0.22)
    bottom = _mix(c, (8, 12, 24), 0.62 if claro else 0.5)
    return top, bottom


def _fuente(px):
    for f in ("segoeuib.ttf", "C:/Windows/Fonts/segoeuib.ttf", "arialbd.ttf"):
        try:
            return ImageFont.truetype(f, px)
        except OSError:
            continue
    return ImageFont.load_default()


def icono(mono=MONO, color=COLOR):
    top, bottom = _paleta(color)
    grad = Image.new("RGBA", (S, S))
    px = grad.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = _mix(top, bottom, (x + y) / (2 * (S - 1))) + (255,)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=R, fill=255)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    lineas = mono.split("\n")
    size = ({1: 124, 2: 108, 3: 92}[max(len(l) for l in lineas)]
            if len(lineas) == 1 else 88)
    f = _fuente(size)
    medidas = []
    for l in lineas:
        bb = d.textbbox((0, 0), l, font=f)
        medidas.append((bb, bb[2] - bb[0], bb[3] - bb[1]))
    gap = 6
    y = (S - (sum(h for _, _, h in medidas) + gap * (len(lineas) - 1))) / 2
    for l, (bb, w, h) in zip(lineas, medidas):
        d.text(((S - w) / 2 - bb[0], y - bb[1]), l, font=f, fill=(255, 255, 255))
        y += h + gap
    return img


def main():
    img = icono()
    for rel in SALIDAS:
        out = os.path.join(AQUI, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if out.lower().endswith(".ico"):
            img.save(out, sizes=[(16, 16), (32, 32), (48, 48), (64, 64),
                                 (128, 128), (256, 256)])
        else:
            lado = None
            base = os.path.basename(out)
            for n in ("512", "256", "128"):
                if f"_{n}" in base:
                    lado = int(n)
            (img.resize((lado, lado), Image.LANCZOS) if lado else img).save(out)
        print("Icono generado:", rel)


if __name__ == "__main__":
    main()
