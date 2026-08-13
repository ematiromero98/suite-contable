# -*- coding: utf-8 -*-
"""
config.py — Rutas de las apps de la suite. Lo único que cambia entre máquinas
son estas carpetas; se pueden sobreescribir con variables de entorno.
"""
import os

# Cada app: dónde vive + por qué archivo se abre (en orden de preferencia) +
# de dónde leer su versión para mostrarla.
APPS = [
    {
        "key": "ddjj",
        "nombre": "DDJJ Impuestos",
        "emoji": "📑",
        "desc": "DDJJ de IVA + SIRCREB en ARCA (Portal IVA).",
        "color": "#2E86C1",
        "dir": os.environ.get("DDJJ_IMPUESTOS_DIR", r"D:\ddjj-impuestos"),
        "entradas": ["DDJJ Impuestos.bat", "APP IVA.bat",
                     os.path.join("scripts", "main.py")],
        "version_file": os.path.join("scripts", "version.py"),
    },
    {
        "key": "reten",
        "nombre": "RetencionesPro",
        "emoji": "🧾",
        "desc": "Retenciones, órdenes de pago y conciliación de compras.",
        "color": "#1E8E4E",
        "dir": os.environ.get("RETENCIONESPRO_DIR", r"D:\RetencionesPro"),
        "entradas": ["run.bat", "main.py"],
        "version_file": "version.py",
    },
]
