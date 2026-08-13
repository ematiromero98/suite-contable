# -*- coding: utf-8 -*-
"""
generar_icono.py — Crea assets/suite.ico: cuadrado redondeado con degradé
celeste→navy y las letras "SC" (Suite Contable). Mismo estilo que DDJJ Impuestos.
"""
import os

from PIL import Image, ImageDraw, ImageFont

_BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(_BASE, "assets", "suite.ico")

SIZE = 256
RADIUS = 52
TOP = (93, 173, 226)     # celeste
BOTTOM = (23, 55, 94)    # navy


def _degrade(size, top, bottom):
    img = Image.new("RGB", (size, size), top)
    px = img.load()
    for y in range(size):
        t = y / (size - 1)
        px_row = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(size):
            px[x, y] = px_row
    return img


def _rounded_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def _fuente(px):
    for nombre in ("segoeuib.ttf", "arialbd.ttf", "seguisb.ttf"):
        try:
            return ImageFont.truetype(nombre, px)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    base = _degrade(SIZE, TOP, BOTTOM)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    img.paste(base, (0, 0), _rounded_mask(SIZE, RADIUS))

    d = ImageDraw.Draw(img)
    texto = "SC"
    font = _fuente(120)
    box = d.textbbox((0, 0), texto, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((SIZE - w) / 2 - box[0], (SIZE - h) / 2 - box[1] - 6),
           texto, font=font, fill=(255, 255, 255))

    img.save(OUT, sizes=[(16, 16), (32, 32), (48, 48), (64, 64),
                         (128, 128), (256, 256)])
    print("Icono creado:", OUT)


if __name__ == "__main__":
    main()
