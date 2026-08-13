# Arquitectura y decisión: repos separados + launcher (no monolito)

**Decisión (ago-2026):** mantener cada programa del estudio como un **repo/app
separado**, y usar la **Suite Contable** (este proyecto) como **capa de
unificación del acceso** — un único menú para abrir, actualizar e instalar. NO
se fusionan los códigos en un solo programa.

## Por qué separados (y no un solo ERP monolítico)

1. **Perfiles de riesgo distintos.** RetencionesPro maneja **plata**
   (retenciones, órdenes de pago) con CI, tests y un updater endurecido. DDJJ
   Impuestos es un **scraper de ARCA** que se rompe cuando ARCA cambia su HTML.
   Juntarlos hace que un arreglo del scraper obligue a redeployar la app de
   plata, y un bug pueda voltear las dos. Separados, el radio de daño es chico.

2. **Dependencias pesadas no compartidas.** DDJJ arrastra **Playwright** (un
   navegador). Un monolito lo cargaría siempre, aunque el usuario solo quiera
   retenciones.

3. **Modelo de actualización por app.** Cada app se actualiza sola por su
   **GitHub Release** (botón ACTUALIZAR). Un repo único obligaría a actualizar
   todo junto: más frágil y pesado.

4. **Lo que importa ya está unificado: la base.** Todas escriben en la **misma
   Supabase**. La conciliación cruza datos de DDJJ y RetencionesPro ahí mismo.
   Ese es el 90% del valor "integrado" sin fusionar una línea.

5. **Costo/beneficio.** Fusionar apps grandes y maduras (p. ej. `form_orden` de
   RetencionesPro son 113 KB) es un refactor caro y riesgoso, para algo que el
   **launcher ya resuelve** a nivel de uso.

## Cuándo SÍ convendría unificar

Si esto se volviera un **producto único** para terceros, con un **equipo**
manteniéndolo, **mismo runtime** (sin el corte Playwright / no-Playwright) y una
**sola cadencia de release**. No es el caso hoy (un solo mantenedor, apps con
propósitos y riesgos distintos).

## El punto intermedio (para cuando duela la duplicación)

Lo único real a favor de unificar es el **código repetido** entre apps
(conexión a Supabase, estilos de UI, formateadores de importes, el motor de
conciliación). Si eso empieza a costar de mantener, la jugada **no** es
fusionar todo: es extraer una **librería común** chica (`contable-core`) que
cada app importe. Apps separadas, sin duplicar. **No hacerlo hasta que duela.**

## Cómo agrego una app al menú del ERP

En `config.py`, sumar una entrada a `APPS` con: `dir` (carpeta local),
`entradas` (puntos de entrada en orden de preferencia, ej. `run.bat`/`main.py`),
`version_file` (`version.py` o un `VERSION` plano), `repo` (para chequear
releases y para instalarla si falta) y `actualizar` (script de update, si tiene).
No hace falta tocar nada del código de esa app: la Suite solo la **lanza**.
