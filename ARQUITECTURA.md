# Arquitectura de la Suite Contable (ERP) — MR & Asociados

Referencia del ecosistema: cómo se relacionan los programas del estudio, por qué
están separados, y cómo funcionan la **instalación** y la **actualización**.

---

## 1. Los programas

| App | Repo | Rama | Qué hace | Runtime especial |
|---|---|---|---|---|
| **Suite Contable** (este) | `suite-contable` | main | Launcher/ERP: abre, actualiza e instala las demás | — |
| **DDJJ Impuestos** | `ddjj-impuestos` | master | DDJJ de IVA + SIRCREB en ARCA | Playwright |
| **RetencionesPro** | `RetencionesPro` | main | Retenciones, OP, conciliación de compras | — |
| **Cobranzas OSECAC** | `cobranzas-osecac` | main | Cobranzas: retenciones, asientos, facturación | — |
| **Facturador ARCA** | `facturador-arca` | master | Facturación electrónica (WSFEV1) | — |
| **Employee Pro** | `employee-pro` | main | RR.HH.: legajos, ausencias, sueldos | — |
| **Control de Juicios** | `control-juicios` | main | Juicios y contingencias laborales (KPIs) | — |
| **Depósito Avalos** | `deposito-avalos` | main | Control de stock (artículos de limpieza) | **PySide6** |
| **Contabilidad** | `contabilidad` | main | Libro Diario/Mayor, estados, concilia Tango | — |

Son **8 apps** (todas **PyQt6 + Supabase**, salvo **Depósito Avalos**, que usa
**PySide6**). Comparten la **misma base de Supabase** —salvo Cobranzas, Employee
y Depósito, que tienen la suya— y ahí es donde la integración importa: la
conciliación de compras cruza datos de DDJJ y RetencionesPro en la misma base, y
Contabilidad devenga sobre ella.

### Diagrama en vivo

El propio ERP trae el módulo **🗺️ Arquitectura** (`arquitectura.py`): un diagrama
navegable —ERP → 8 apps → bases Supabase → sistemas externos (ARCA/OSECAC/Tango/
Drive)— con el detalle por capas de cada app y su flujo principal animado. Es la
fuente visual de esta misma doc; si cambia una app, se edita `DATOS` en ese
archivo.

---

## 2. Decisión: repos separados + launcher (NO monolito)

Cada programa es su **propio repo/app**; la Suite unifica el **acceso**, no el
código. Por qué:

1. **Riesgos distintos.** RetencionesPro maneja plata (CI, tests, updater
   endurecido). DDJJ es un scraper de ARCA que se rompe cuando ARCA cambia el
   HTML. Separados, el radio de daño es chico.
2. **Dependencias pesadas no compartidas.** Solo DDJJ usa Playwright.
3. **Actualización por app** (GitHub Releases). Un repo único obligaría a
   actualizar todo junto.
4. **Lo importante ya está unificado: la base.** Misma Supabase.
5. **Costo/beneficio.** Fusionar apps maduras es caro para algo que el launcher
   ya resuelve.

**Cuándo SÍ unificar:** producto único para terceros, con equipo, mismo runtime
y una sola cadencia de release. No es el caso hoy.

**Punto intermedio (para cuando duela la duplicación):** extraer una librería
común (`contable-core`: conexión Supabase, estilos, formateadores, motor de
conciliación). NO fusionar apps. No hacerlo hasta que duela.

---

## 3. Distribución: "abro cualquier app → aparece el ERP"

Cada app trae un **`bootstrap_suite.py`** (en RetencionesPro es
`instalar_suite.bat` + `_bootstrap_suite()`) que se llama al arrancar:

```
Abro CUALQUIER app (DDJJ / RetProp / Cobranzas / Facturador / Employee)
        │  bootstrap: ¿está D:\suite-contable ?
        ├── sí  → no-op (sigue abriendo la app)
        └── no  → gh repo clone suite-contable  +  crea acceso directo
```

- Es **best-effort y no bloquea**: si falla (sin `gh`, sin red), la app abre igual.
- En una máquina que ya tiene la Suite, es un **no-op instantáneo**.
- Sirve para el caso real: las apps están instaladas sueltas en muchas PCs; al
  abrir cualquiera, el ERP aparece solo.

RetencionesPro además instala/actualiza la Suite en su `update.bat` (paso [5/5]).

---

## 4. Actualización: el ERP como centro de updates

Al abrir la Suite, chequea (en segundo plano, vía `gh`) el **último GitHub
Release** de cada app y lo compara con la versión instalada:

```
Abro la Suite
   └── por cada app: ¿release > instalada?
          └── sí → "🔔 ACTUALIZACIÓN DISPONIBLE (vX)" + botón ⟳ Actualizar
```

Al tocar **Actualizar**, la Suite:
1. Si la app tiene actualizador propio (`update.bat` / `Actualizar.bat`), lo
   ejecuta (pull + dependencias + relanzar).
2. Si no, hace **`git pull` directo** en la carpeta de la app (usa las
   credenciales de `gh`). *Ojo:* el git pull pelado NO instala dependencias.

Hoy **las apps tienen `update.bat`/`Actualizar.bat` propio**, así que el botón
siempre instala dependencias nuevas.

### Qué hace cada `update.bat`
1. Se **auto-copia a `%TEMP%`** y corre desde ahí (para que el `git pull` pueda
   reescribir el propio `.bat` sin corromperse).
2. Verifica que el **remote `origin`** sea el repo oficial en github.com
   (defensa supply-chain: no pullear de un remote ajeno).
3. `git pull --ff-only`.
4. `pip install -r requirements.txt` (en `.venv` si existe, o python del sistema).
5. Instala la Suite si falta (`bootstrap_suite`).
6. Reabre la app.

RetencionesPro usa además un token del `.env` para el pull; las otras usan las
credenciales de `gh`.

**Divergencia:** si la copia local de una app tiene commits distintos a los de
GitHub (`--ff-only` no puede avanzar), el `update.bat` **respalda** (rama
`backup-local-*` + `stash`) y hace `reset --hard` al código oficial. Es seguro
porque los **datos no están en git** (viven en Supabase y en `.env`/`.venv`,
gitignored): solo se realinea el código. Pasa típicamente en PCs donde se
commiteó algo local o que quedaron con una historia vieja.

---

## 5. Requisitos por máquina

- **`gh` (GitHub CLI) instalado y autenticado** — para clonar/actualizar los
  repos privados sin manejar tokens a mano.
- **Disco `D:`** por defecto (la Suite se instala en `D:\suite-contable`).
  Configurable con la variable de entorno **`SUITE_CONTABLE_DIR`**.
- Rutas de cada app configurables por env: `DDJJ_IMPUESTOS_DIR`,
  `RETENCIONESPRO_DIR`, `COBRANZAS_DIR`, `FACTURADOR_DIR`, `EMPLOYEE_PRO_DIR`.

**Borde conocido:** en una PC con una versión MUY vieja (sin `update.bat`
todavía), el primer update lo hace la Suite con git pull (sin deps); del segundo
en adelante ya usa el `update.bat` y maneja dependencias.

---

## 6. Cómo agregar una app al menú del ERP

En `config.py`, sumar una entrada a `APPS`:

```python
{
    "key": "miapp",
    "nombre": "Mi App",
    "emoji": "🔧",
    "desc": "Qué hace.",
    "color": "#2E86C1",
    "dir": os.environ.get("MIAPP_DIR", r"D:\ruta\a\miapp"),
    "entradas": ["run.bat", "main.py"],   # puntos de entrada, en orden
    "version_file": "version.py",          # o "VERSION" (texto plano)
    "repo": "ematiromero98/miapp",         # para releases + instalar si falta
    "actualizar": ["update.bat"],          # updater propio; [] = git pull directo
}
```

No hace falta tocar el código de esa app: la Suite solo la **lanza / actualiza /
instala**. Para que el aviso "ACTUALIZACIÓN DISPONIBLE" funcione, la app tiene
que tener **GitHub Releases** (aunque sea uno base con la versión actual).

Para que se integre al circuito completo, conviene que la app tenga:
- `bootstrap_suite.py` llamado en su arranque (instala el ERP si falta).
- un `update.bat` propio (pull + deps + relanzar).
