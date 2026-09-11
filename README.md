# Suite Contable — MR & Asociados

Launcher único para abrir las **11 apps** del estudio desde un solo lugar:

- **🧮 Impuestos (IIBB + IVA)** — Ingresos Brutos (CM03) + IVA de las 9 empresas.
- **🧾 RetencionesPro** — retenciones, órdenes de pago y conciliación de compras.
- **💰 Cobranzas OSECAC** — cobranzas: retenciones, asientos y facturación.
- **📄 Facturador ARCA** — facturación electrónica (WSFEV1).
- **👥 Employee Pro** — gestión de RR.HH. (legajos, ausencias, sueldos).
- **📦 Depósito Avalos** — control de stock del depósito (PySide6).
- **⚖️ Control de Juicios** — juicios y contingencias laborales.
- **📚 Contabilidad** — Libro Diario/Mayor y estados; concilia contra Tango.
- **🏦 Conciliador Bancario** — Mayor de Tango vs. extracto del banco (BBVA).
- **📅 Calendario de Ausencias** — vacaciones y licencias del equipo.
- **🏛️ VEP Autónomos** — genera los VEP de Autónomos en tanda (ARCA).

Es solo un lanzador: no toca datos ni bases. Cada programa sigue viviendo en su
propio proyecto; esta app solamente los **abre, actualiza e instala**.

- **[GUIA.md](GUIA.md)** — cómo instalar, usar, actualizar y **desarrollar/publicar
  cambios** (credenciales por Drive, login de `gh`, flujo commit → release,
  dependencias, problemas comunes). Empezá por acá.
- [ARQUITECTURA.md](ARQUITECTURA.md) — el porqué de mantener los repos separados.

Para sumar una app nueva al menú, agregá una entrada en `config.py` (`APPS`).

## Uso

Doble clic en **`Suite Contable.bat`** (o `pythonw main.py`). Aparece una
ventana con las apps; tocás **Abrir** en la que quieras.

## Instalación

```bash
pip install -r requirements.txt
```

## Rutas de las apps

Por defecto busca cada app en su carpeta. Si están en otro lado, fijá la
variable de entorno correspondiente (o editá `config.py`). La ventana avisa en
rojo si no encuentra alguna.

| App | Ruta por defecto | Variable de entorno |
| --- | --- | --- |
| Impuestos (IIBB + IVA) | `D:\PROYECTOS CLAUDE\impuestos` | `IMPUESTOS_DIR` |
| RetencionesPro | `D:\RetencionesPro` | `RETENCIONESPRO_DIR` |
| Cobranzas OSECAC | `D:\PROYECTOS CLAUDE\cobranzas-osecac` | `COBRANZAS_DIR` |
| Facturador ARCA | `D:\PROYECTOS CLAUDE\facturador-arca` | `FACTURADOR_DIR` |
| Employee Pro | `D:\PROYECTOS CLAUDE\employee-pro` | `EMPLOYEE_PRO_DIR` |
| Depósito Avalos | `D:\PROYECTOS CLAUDE\deposito-avalos` | `DEPOSITO_AVALOS_DIR` |
| Control de Juicios | `D:\control-juicios` | `JUICIOS_DIR` |
| Contabilidad | `D:\contabilidad` | `CONTABILIDAD_DIR` |
| Conciliador Bancario | `D:\PROYECTOS CLAUDE\conciliador-bancario` | `CONCILIADOR_DIR` |
| Calendario de Ausencias | `D:\PROYECTOS CLAUDE\calendario-ausencias` | `CALENDARIO_AUSENCIAS_DIR` |
| VEP Autónomos | `D:\arca-vep-autonomos` | `VEP_AUTONOMOS_DIR` |

## Seguridad

- El **auto-update** de la propia Suite sólo corre si el remote `origin` apunta
  al repo oficial (`ematiromero98/suite-contable`); si no, se omite y avisa.
- La descarga de **rclone** (para traer el `.env`) usa una versión fija y se
  valida su **SHA256** antes de ejecutarla.

## Acceso directo en el Escritorio

```powershell
powershell -ExecutionPolicy Bypass -File crear_acceso_directo.ps1
```
