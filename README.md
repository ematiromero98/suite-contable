# Suite Contable — MR & Asociados

Launcher único para abrir los programas del estudio desde un solo lugar:

- **📑 DDJJ Impuestos** — DDJJ de IVA + SIRCREB en ARCA.
- **🧾 RetencionesPro** — retenciones, órdenes de pago y conciliación de compras.

Es solo un lanzador: no toca datos ni bases. Cada programa sigue viviendo en su
propio proyecto; esta app solamente los abre.

## Uso

Doble clic en **`Suite Contable.bat`** (o `pythonw main.py`). Aparece una
ventana con las dos apps; tocás **Abrir** en la que quieras.

## Instalación

```bash
pip install -r requirements.txt
```

## Rutas de las apps

Por defecto busca:

- DDJJ Impuestos en `D:\ddjj-impuestos`
- RetencionesPro en `D:\RetencionesPro`

Si están en otro lado, fijá las variables de entorno **`DDJJ_IMPUESTOS_DIR`** y
**`RETENCIONESPRO_DIR`** (o editá `config.py`). La ventana avisa en rojo si no
encuentra alguna.

## Acceso directo en el Escritorio

```powershell
powershell -ExecutionPolicy Bypass -File crear_acceso_directo.ps1
```
