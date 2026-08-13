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
        "repo": "ematiromero98/ddjj-impuestos",
        "actualizar": ["Actualizar.bat"],
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
        "repo": "ematiromero98/RetencionesPro",
        "actualizar": ["update.bat"],
    },
    {
        "key": "cobranzas",
        "nombre": "Cobranzas OSECAC",
        "emoji": "💰",
        "desc": "Cobranzas OSECAC: retenciones, asientos y facturación.",
        "color": "#D68910",
        "dir": os.environ.get("COBRANZAS_DIR", r"D:\PROYECTOS CLAUDE\cobranzas-osecac"),
        "entradas": ["Iniciar Cobranzas.bat", "cobranzas_qt.py"],
        "version_file": "VERSION",
        "repo": "ematiromero98/cobranzas-osecac",
        "actualizar": ["update.bat"],
    },
    {
        "key": "facturador",
        "nombre": "Facturador ARCA",
        "emoji": "📄",
        "desc": "Facturación electrónica ARCA (WSFEV1).",
        "color": "#16A085",
        "dir": os.environ.get("FACTURADOR_DIR", r"D:\PROYECTOS CLAUDE\facturador-arca"),
        "entradas": ["main.py"],
        "version_file": "VERSION",
        "repo": "ematiromero98/facturador-arca",
        "actualizar": ["update.bat"],
    },
    {
        "key": "employee",
        "nombre": "Employee Pro",
        "emoji": "👥",
        "desc": "Gestión de RR.HH.: legajos, ausencias, sueldos. Multiempresa.",
        "color": "#8E44AD",
        "dir": os.environ.get("EMPLOYEE_PRO_DIR", r"D:\PROYECTOS CLAUDE\employee-pro"),
        "entradas": ["main.py"],
        "version_file": "version.py",
        "repo": "ematiromero98/employee-pro",
        "actualizar": ["update.bat"],
    },
]
