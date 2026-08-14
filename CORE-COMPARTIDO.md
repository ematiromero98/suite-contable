# Core compartido de la Suite Contable

`suite-contable` (ya instalado en cada PC, en `D:\suite-contable`) es también el
**hogar del código compartido**. En vez de duplicar tema/formatos/tooling en
cada app, las apps lo importan de acá. Así un cambio se hace **una vez** y vale
para todas (el dolor que motivó esto: el tema hubo que arreglarlo 6 veces).

## Qué hay hoy

| Módulo | Qué es | Ya lo usa |
|---|---|---|
| `suite_theme.py` | Tema "Panel Oscuro": tokens de color, `qss()`, `apply(app)` | Employee, Control de Juicios |
| `suite_charts.py` | Gráficos (necesita PyQt6-QtCharts) | Employee |
| `formatos.py` | `fmt_money`, `fmt_money_corto`, `fmt_pct`, `fmt_cuit` | Control de Juicios |
| `release.py` | Publica una versión (bump+commit+tag+release) sin desincronizar | — (tooling) |

## Cómo una app adopta el core (patrón)

Al inicio del módulo de estilos (o del `main`), agregar la carpeta de la Suite
al `sys.path` con **append** (no `insert(0)`, para no pisar `version.py`/`config.py`
propios de la app) y con **fallback** si la Suite no estuviera:

```python
import os, sys
_suite = os.environ.get("SUITE_CONTABLE_DIR", r"D:\\suite-contable")
if os.path.isdir(_suite) and _suite not in sys.path:
    sys.path.append(_suite)
try:
    import suite_theme as _t
except Exception:
    _t = None

FONDO = _t.BG if _t else "#0f1218"     # etc. — mapear las constantes de la app
```

- **Tema completo (recomendado para apps nuevas):** `suite_theme.apply(app)` en el
  arranque. Requiere que la app use los objectNames del tema (`#sidebar`, `#nav`,
  `#card`, `#kpi`, `role="title"`…).
- **Sólo paleta (apps con QSS propio):** importar los *tokens* (`_t.BG`, `_t.PANEL`,
  `_t.TEXT`, `_t.ACCENT`…) y usarlos en el QSS de la app. Es lo que hace Control
  de Juicios: mantiene su QSS pero los colores salen del core.
- **Formatos:** `from formatos import fmt_money, fmt_money_corto` (con el mismo
  fallback).

## Migración incremental (NO big-bang)

Las 5 apps de producción tienen su `estilos.py` propio. Migrarlas **de a una**,
verificando con un render antes de publicar. Nunca las 6 juntas: si el core
rompe algo, se lleva puesta toda la suite. Orden sugerido por riesgo: primero
las que ya usan tema compartido o QSS chico.

## Publicar una versión (usar SIEMPRE esto)

Desde la carpeta de la app:

```bash
python D:\suite-contable\release.py 1.43.5
```

Hace bump del archivo de versión + commit + push + GitHub Release y **verifica
que la versión del código publicado coincida con el tag**. Esa verificación es
la que evita el bug del "ERP tirando para atrás" (release vX pero `version.py`
en otra versión → el ERP ofrece update para siempre).
