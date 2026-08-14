# -*- coding: utf-8 -*-
"""
formatos — Formateadores compartidos de la Suite Contable (MR & Asociados).

Fuente de verdad de cómo se muestran importes/porcentajes en TODAS las apps.
Vive en `suite-contable` (ya instalado en cada PC); las apps lo importan igual
que `suite_theme` (append de la carpeta de la Suite al sys.path + fallback).

Sin dependencias (sólo la stdlib).
"""
from __future__ import annotations


def fmt_money(v, simbolo: str = "$ ") -> str:
    """1234567.89 -> '$ 1.234.567,89' (formato AR: punto de miles, coma decimal)."""
    try:
        n = float(v or 0)
    except (TypeError, ValueError):
        return "-"
    s = f"{n:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"{simbolo}{s}"


def fmt_money_corto(v, simbolo: str = "$ ") -> str:
    """Compacto para KPIs: '$ 1,2 MM' / '$ 850 K' / '$ 900'."""
    try:
        n = float(v or 0)
    except (TypeError, ValueError):
        return "-"
    signo = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000:
        return f"{signo}{simbolo}{n/1_000_000:,.1f} MM".replace(",", ".")
    if n >= 1_000:
        return f"{signo}{simbolo}{n/1_000:,.0f} K".replace(",", ".")
    return f"{signo}{simbolo}{n:,.0f}".replace(",", ".")


def fmt_pct(v, decimales: int = 1) -> str:
    """0.1234 -> '12,3%' (recibe fracción)."""
    try:
        n = float(v or 0) * 100
    except (TypeError, ValueError):
        return "-"
    return f"{n:.{decimales}f}%".replace(".", ",")


def fmt_cuit(v) -> str:
    """'20123456789' -> '20-12345678-9'. Deja intacto lo que no tenga 11 dígitos."""
    s = "".join(ch for ch in str(v or "") if ch.isdigit())
    return f"{s[:2]}-{s[2:10]}-{s[10:]}" if len(s) == 11 else str(v or "")
