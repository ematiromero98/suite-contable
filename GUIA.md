# Guía de operación — Suite Contable

Cómo instalar, usar, actualizar y desarrollar los programas del estudio. Para el
diseño/porqué de la separación en repos, ver [ARQUITECTURA.md](ARQUITECTURA.md).

---

## 1. Los programas y sus repos

| Programa | Repo GitHub | Rama | Privado |
| --- | --- | --- | --- |
| **Suite Contable (ERP / lanzador)** | `ematiromero98/suite-contable` | `main` | **público** |
| DDJJ Impuestos (IVA + SIRCREB) | `ematiromero98/ddjj-impuestos` | `master` | privado |
| RetencionesPro | `ematiromero98/RetencionesPro` | `main` | privado |
| Cobranzas OSECAC | `ematiromero98/cobranzas-osecac` | `main` | privado |
| Facturador ARCA | `ematiromero98/facturador-arca` | `master` | privado |
| Employee Pro | `ematiromero98/employee-pro` | `main` | privado |

Todos comparten la **misma base Supabase**. El ERP es público **a propósito**:
así se instala sin credenciales. Por eso las claves **nunca** van en el código
del ERP.

---

## 2. Poner una PC nueva a funcionar (de cero)

En orden:

1. **Instalar el ERP.** Descargar `instalar_erp_2.bat` del Google Drive del
   estudio y hacerle doble clic. Clona/actualiza el ERP y crea el acceso
   directo **"Suite Contable"** en el Escritorio.
   - Requisito: **Git para Windows** (https://git-scm.com/download/win) y Python.
   - Si el ERP quedó viejo y no se actualiza solo, usar `reparar_erp.bat` (fuerza
     la última versión).

2. **Traer las credenciales (.env).** Abrir el ERP y tocar **🔑 Traer
   credenciales** (o correr `traer_credenciales.bat`). Se abre el navegador y
   pide acceso a Google Drive → **iniciar sesión con la cuenta del estudio
   `ematiromero98@gmail.com`** y "Permitir". Baja el `.env` (privado) y lo deja
   donde las apps lo buscan. Cuando termina, el botón queda gris.

3. **Loguear GitHub CLI (`gh`)** — necesario para instalar/actualizar los
   programas privados:
   ```bash
   winget install --id GitHub.cli -e
   gh auth login
   ```
   Elegir GitHub.com → HTTPS → *Yes* a autenticar git → *Login with a web
   browser* → **cuenta del estudio `ematiromero98`**.

4. **Instalar las apps.** En el ERP, cada app que falte muestra **⬇ Instalar**.
   Tocarla. Después **Abrir**.

---

## 3. Los botones del ERP

- **Abrir** — lanza el programa.
- **⬇ Instalar** — aparece solo si esa app **no está** instalada (la clona con
  `gh`). Requiere `gh` logueado.
- **⟳ Actualizar** (en la tarjeta) — aparece solo si esa app tiene una **versión
  nueva publicada**. Actualiza esa app sola.
- **⟳ Actualizar todo (N)** (arriba) — está **apagado si no hay ninguna
  actualización pendiente**; se prende y muestra cuántas hay cuando alguna app
  tiene versión nueva. Las actualiza todas juntas.
- **🔑 Traer credenciales** — baja el `.env` del Drive. Queda gris si ya están.

Al actualizar (una o todas), la app que queda al día deja de figurar como
pendiente y se le oculta el aviso/botón. Los **datos no se tocan** (viven en
Supabase y en el `.env`/`.venv`, fuera de git).

---

## 4. Desarrollar y publicar cambios

### El ERP (este repo)
Se **auto-actualiza solo**: cada vez que se abre hace `git pull` de `main` (y se
realinea por la fuerza si la copia local divergió). **No hace falta release.**

```bash
git add -A && git commit -m "..."
git push origin main
```
En cada PC llega al **reabrir** el ERP.

### Una app (DDJJ, RetencionesPro, etc.)
El ERP detecta que hay update comparando el **último Release** de GitHub contra
la versión instalada. Por eso, para que un cambio llegue a las PC **hay que
publicar un Release** (solo `push` no alcanza):

```bash
git add -A && git commit -m "..."
git push
# subir version.py / VERSION (semver: MAYOR.MENOR.PARCHE)
gh release create vX.Y.Z --title "..." --notes "..."
```
Después, en cada PC, el ERP muestra el botón **⟳ Actualizar** de esa app.

> **Dependencias:** al actualizar, el ERP crea el `.venv` de la app (con el
> Python real que lo corre) e instala `requirements.txt` solo. Si falla, el
> resumen de "Actualizar" muestra el motivo exacto.

---

## 5. Los `.bat` auxiliares (en el Drive del estudio)

| Archivo | Qué hace |
| --- | --- |
| `instalar_erp_2.bat` | Instala/actualiza el ERP (repo público) y crea el acceso directo. |
| `reparar_erp.bat` | **Fuerza** el ERP a la última versión (`reset --hard`) si quedó trabado. |
| `traer_credenciales.bat` | Baja el `.env` del Drive con rclone (pide acceso a Google). Mismo mecanismo que el botón del ERP. |

---

## 6. Problemas comunes

| Síntoma | Causa | Solución |
| --- | --- | --- |
| "Falta la variable SUPABASE_URL en el .env" | La PC no tiene el `.env`. | **🔑 Traer credenciales** (login con la cuenta del estudio). |
| El ERP abre viejo / no aparece "Actualizar todo" | La copia local del ERP quedó desalineada. | Correr `reparar_erp.bat`, o cerrar y reabrir el ERP. |
| Al actualizar una app: **403 / Write access not granted** | Falta `gh` logueado en esa PC. | `gh auth login` con la cuenta del estudio. |
| "faltan dependencias" al actualizar | El `.venv` se creaba con el Python de la Microsoft Store (roto). Corregido en ERP ≥ v1.8.1. | Actualizar el ERP; el resumen ahora muestra el error real. |
| "No encontré 'gh' para instalar" | GitHub CLI no instalado. | `winget install --id GitHub.cli -e`. |

---

## 7. Seguridad (no romper esto)

- Las **claves nunca** van en el código. El ERP es público: un secreto ahí daría
  acceso a toda la contabilidad. El `.env` viaja **privado** por el Drive del
  estudio.
- El **auto-update** del ERP solo corre si `origin` es el repo oficial.
- La descarga de **rclone** usa versión fija + verificación **SHA256**.
