# Suite Contable — MR & Asociados

Launcher único para abrir los programas del estudio desde un solo lugar:

- **📑 DDJJ Impuestos** — DDJJ de IVA + SIRCREB en ARCA.
- **🧾 RetencionesPro** — retenciones, órdenes de pago y conciliación de compras.
- **💰 Cobranzas OSECAC** — cobranzas: retenciones, asientos y facturación.
- **📄 Facturador ARCA** — facturación electrónica (WSFEV1).
- **👥 Employee Pro** — gestión de RR.HH. (legajos, ausencias, sueldos).

Es solo un lanzador: no toca datos ni bases. Cada programa sigue viviendo en su
propio proyecto; esta app solamente los **abre, actualiza e instala**.

- **[GUIA.md](GUIA.md)** — cómo instalar, usar, actualizar y **desarrollar/publicar
  cambios** (credenciales por Drive, login de `gh`, flujo commit → release,
  dependencias, problemas comunes). Empezá por acá.
- [ARQUITECTURA.md](ARQUITECTURA.md) — el porqué de mantener los repos separados.

Para sumar una app nueva al menú, agregá una entrada en `config.py` (`APPS`).

## Uso

Doble clic en **`Suite Contable.bat`** (o `pythonw main.py`). Aparece una
ventana con las dos apps; tocás **Abrir** en la que quieras.

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
| DDJJ Impuestos | `D:\ddjj-impuestos` | `DDJJ_IMPUESTOS_DIR` |
| RetencionesPro | `D:\RetencionesPro` | `RETENCIONESPRO_DIR` |
| Cobranzas OSECAC | `D:\PROYECTOS CLAUDE\cobranzas-osecac` | `COBRANZAS_DIR` |
| Facturador ARCA | `D:\PROYECTOS CLAUDE\facturador-arca` | `FACTURADOR_DIR` |
| Employee Pro | `D:\PROYECTOS CLAUDE\employee-pro` | `EMPLOYEE_PRO_DIR` |

## Seguridad

- El **auto-update** de la propia Suite sólo corre si el remote `origin` apunta
  al repo oficial (`ematiromero98/suite-contable`); si no, se omite y avisa.
- La descarga de **rclone** (para traer el `.env`) usa una versión fija y se
  valida su **SHA256** antes de ejecutarla.

## Acceso directo en el Escritorio

```powershell
powershell -ExecutionPolicy Bypass -File crear_acceso_directo.ps1
```
