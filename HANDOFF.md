# HANDOFF — Suite Contable (launcher / ERP del estudio)

> **Leé esto primero** para continuar el proyecto en un chat nuevo. Estado al **11-09-2026,
> v1.28.1**. Los documentos anteriores siguen valiendo por partes: `GUIA.md` (operación paso a
> paso), `ARQUITECTURA.md` (por qué repos separados + cómo se actualiza), `CORE-COMPARTIDO.md`
> (tema/formatos/`release.py` compartidos), `README.md`. Sus **listas de apps quedaron viejas**
> (5, 6 o 9 apps): la lista vigente es la de acá y la de `config.APPS`.

---

## 0. Qué es y estado actual

**Suite Contable** es el **launcher/ERP** de MR & Asociados: una ventana PyQt6 (tema «Panel
Oscuro», sidebar + topbar) que **abre, instala y actualiza** las apps del estudio, trae las
**credenciales**, muestra el **registro de backups**, y dibuja el ecosistema (Arquitectura,
Ecosistema 3D, Conexiones DB). No toca datos: cada app vive en su repo.

- **Local:** `D:\suite-contable` (checkout de desarrollo y también la instalación de esta PC).
  Configurable con `SUITE_CONTABLE_DIR`.
- **GitHub:** `ematiromero98/suite-contable`, **público a propósito** (se instala sin
  credenciales) → **nunca** un secreto en este repo. Rama `main`.
- **Versión:** `version.py` (`VERSION = "1.28.1"`). Tags `vX.Y.Z` para las versiones grandes;
  **el ERP se auto-actualiza con `git pull` de `main` al abrir** (no necesita release).
- **Sin tests automatizados** en este repo (se verifica a mano: construir `Launcher()` en
  pantalla y capturar, ver §6).

**Páginas del sidebar** (`main.py`, `Launcher`): GENERAL → 🗂 Panel (tarjetas de apps: logo,
versión, estado, Abrir/Instalar/Actualizar), 🔄 Actualizaciones, 🗺 Arquitectura, 🌐 Ecosistema
3D, 🗄 Conexiones DB, 💾 Registro de Backups · SISTEMA → ⚙ Ajustes. Topbar: «⟳ Actualizar todo
(N)» y «🔑 Traer credenciales». Marca del sidebar: logo **SC** azul (`assets/suite.png`).

**Apps registradas hoy (`config.APPS`, 11)** — key · monograma/color · carpeta · repo:

| key | App | Logo | Carpeta por defecto | Repo | Versión en |
|---|---|---|---|---|---|
| impuestos | Impuestos (IIBB + IVA) | IMP menta | `D:\PROYECTOS CLAUDE\impuestos` | `impuestos` (privado, **nuevo 11-09**) | version.py |
| reten | RetencionesPro | RP verde | `D:\RetencionesPro` | `RetencionesPro` | version.py |
| cobranzas | Cobranzas OSECAC | COB ámbar | `D:\PROYECTOS CLAUDE\cobranzas-osecac` | `cobranzas-osecac` | VERSION |
| facturador | Facturador ARCA | FAC teal | `D:\PROYECTOS CLAUDE\facturador-arca` | `facturador-arca` (master) | VERSION |
| employee | Employee Pro | EP violeta | `D:\PROYECTOS CLAUDE\employee-pro` | `employee-pro` | version.py |
| deposito | Depósito Avalos (PySide6) | DA naranja | `D:\PROYECTOS CLAUDE\deposito-avalos` | `deposito-avalos` | version.py |
| juicios | Control de Juicios | CJ navy | `D:\control-juicios` | `control-juicios` | VERSION |
| contabilidad | Contabilidad | CTB verde oscuro | `D:\contabilidad` | `contabilidad` | VERSION |
| conciliador | Conciliador Bancario | CB verde | `D:\PROYECTOS CLAUDE\conciliador-bancario` | `conciliador-bancario` | VERSION |
| ausencias | Calendario de Ausencias | CA menta | `D:\PROYECTOS CLAUDE\calendario-ausencias` | `calendario-ausencias` | version.py |
| veps | VEP Autónomos | VEP púrpura | `D:\arca-vep-autonomos` | `arca-vep-autonomos` | VERSION |

**Retiradas del launcher el 11-09-2026** (commit `d0c8f54`): **DDJJ Impuestos** (`ddjj-impuestos`,
master) y **CM03 Convenio Multilateral** (`cm03-convenio-multilateral`); las reemplaza la app
**Impuestos**, que unifica IIBB CM03 + IVA. Sus repos y logos (`assets/apps/ddjj.png`, `cm03.png`)
siguen existiendo por si vuelven.

---

## 1. Reglas fijas / decisiones (no reabrir)

- **Repos separados + launcher, no monolito** (`ARQUITECTURA.md` §2). Lo compartido va al
  **core** de este repo (`suite_theme.py`, `suite_charts.py`, `formatos.py`, `release.py`),
  adoptado de a una app por vez, con `sys.path.append` y fallback.
- **Este repo es público → cero secretos.** Las credenciales viajan por el repo privado
  `ematiromero98/suite-secretos` (modelo «cero logins») o, como camino viejo, por el Google
  Drive del estudio con rclone (versión fija + SHA256).
- **Actualización de apps por GitHub Releases** cuando la app corta release (RetencionesPro,
  DDJJ) **o por la rama por defecto** (v1.20+, `_version_en_rama` lee el archivo de versión
  en la punta de la rama: Cobranzas y las que pushean a `main`). Se toma la **mayor** de ambas.
- **Publicar una app: `python D:\suite-contable\release.py X.Y.Z`** desde la carpeta de la app
  (bump + commit + push + release + chequeo de que el tag y el código coinciden). Evita el bug
  del «ERP tirando para atrás» (release vX con `version.py` en otra versión → update eterno).
- **Logos:** molde común (cuadrado redondeado, degradé del `color` de la app, monograma
  `mono`) generado por `generar_iconos_apps.py` → `assets/apps/<key>.png`. Cada app tiene el
  mismo molde en su `generar_icono.py`. Cambiar color/monograma = tocar `config.py` +
  regenerar acá + regenerar el `.ico` de la app. Ícono propio: `generar_icono.py` (SC).
- **git nunca interactivo** en el launcher (`GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never`,
  `credential.interactive=false`): las updates no abren el diálogo «Select an account»; caen al
  fetch con token.
- **Datos fuera de git.** `reset --hard` al realinear una app es seguro porque `.env`, `.venv`,
  `secretos.json`, `certs/` están gitignored en cada app.
- **Riesgos aceptados por el usuario (no re-proponer):** el `.env` compartido lleva
  `SUPABASE_SECRET_KEY` + `SUPABASE_DB_URL` (apps «admin» con acceso maestro); token de GitHub
  del `.env` rotable; claves fiscales embebidas en Cobranzas; no hay Edge Function
  intermedia. Ver memoria del asistente / `SEGURIDAD` de cada app.

---

## 2. Cómo funciona por dentro (`main.py`)

- **Chequeo de versiones al abrir** (`_Chequeador`, en hilo): por app, `_ultima_release(repo)`
  (gh → API con token del runtime) y `_version_en_rama(repo, version_file)` (contents API de
  la rama por defecto); `_mayor_disponible` vs `_leer_version(app)` → pill «⬆ Nueva versión»
  y contador en «Actualizar todo». `_es_mayor` compara tuplas semver.
- **Actualizar una app** (`_actualizar_app_core`): 1) `git fetch` (credenciales de `gh` si las
  hay) → 2) si falla, fetch con **token del runtime** (`_token_runtime`: archivo del instalador
  `%LOCALAPPDATA%\Suite Contable\gh_token.txt` → `gh auth token`) → 3) último recurso, el
  `GITHUB_TOKEN` del `.env` de la app. Luego `merge --ff-only @{u}`; si divergió, rama
  `backup-local-<ts>` + stash + `reset --hard`. Después `pip install -r requirements.txt` en el
  `.venv` de la app con el **Python real** (`_python_base`, nunca el stub de la Microsoft
  Store). Devuelve ok / aviso / saltada / error con detalle.
- **Instalar** (`_instalar_app`): `gh repo clone` (o con token) en `app["dir"]`, crea venv y
  deps. **Abrir** (`_abrir`): primer archivo de `entradas` que exista (`run.bat`, `main.py`…).
- **Credenciales** (`credenciales.py`): `traer()` → primero `traer_github()` (clona/actualiza
  `suite-secretos` con `gh`/token, copia `.env` a `env_central()` =
  `%LOCALAPPDATA%\Suite Contable\.env`, lo **distribuye** a las apps que lo leen
  (`_APPS_ENV`: reten, ddjj, juicios, contabilidad, veps) y a `OneDrive\Suite Contable\.env`;
  instala los **secretos propios** (`cobranzas.secretos.json` → corre `configurar.py`;
  `employee.secretos.json`) y los **certs de ARCA de Cobranzas** desde `cobranzas.certs/`);
  si no hay gh, cae a rclone + Google Drive (`suite:Suite Contable/.env`, cuenta
  `ematiromero98@gmail.com`). `todo_listo()` decide si el botón queda gris; al abrir, si
  falta el `.env`, lo ofrece solo. `refrescar_token_github()` / `refrescar_secretos_apps()`
  propagan un token nuevo o el login de la cuenta compartida a PCs ya configuradas.
- **Registro de Backups** (`_page_backups`, `_BackupsLoader`): lee `suite_backup_runs` de la
  base compartida (lo escribe `suite-backups`, domingos 22:00) y muestra alerta arriba si el
  último falló o tiene más de 8 días.
- **Arquitectura / Ecosistema 3D / Conexiones DB:** `arquitectura.py` (diagrama con `DATOS`),
  `assets/ecosistema-3d.html` (ciudad isométrica, arrays `NODES`/`EDGES`),
  `conexiones_db.py` (`BASES`: las 5 bases y cómo se conecta cada app: login / directo /
  edge). **Son datos escritos a mano: al cambiar una app hay que editarlos** (ver §5).
- **Bootstrap desde las apps:** cada app trae `bootstrap_suite.py` que clona la Suite si falta
  (`D:\suite-contable`) y crea el acceso directo. Best-effort.
- **Instaladores:** `instalar_suite.ps1` («cero logins»: pegar el token de solo lectura, instala
  Git/Python/gh si faltan, loguea `gh`, clona ERP y apps, trae credenciales, crea acceso
  directo; guarda el token en `gh_token.txt`) + `setup_pc.py`; `instalar_erp.bat` /
  `reparar_erp.bat` (Drive) para el camino viejo; `Suite Contable.bat` y
  `crear_acceso_directo.ps1`.

---

## 3. Bases de datos del estudio (para orientarse)

| Base (Supabase) | Ref | Quién escribe | Cómo |
|---|---|---|---|
| ORDENES DE PAGO – BELGRANO (compartida) | `zpwccecovhjmeibxafkg` | RetencionesPro, Impuestos/DDJJ, CM03, Contabilidad, VEP, Facturador, comprobantes-cel, suite-backups | secret key / DB_URL (directo), login, Edge Function |
| COBRANZAS OSECAC | `rrarmatjyvmrpohsvfzg` | Cobranzas OSECAC (CM03/Impuestos leen) | login con cuenta compartida (RLS) |
| EMPLOYEE-PRO | `ffczbimnuodzcbgsdxbx` | Employee Pro, Calendario de Ausencias, webs (qb-dashboard, calendario-cel, chermisqui) | login / Edge Function |
| DEPOSITO AVALOS | `ioycuhefaalpqivhhryb` | Depósito Avalos | login |
| CONCILIADOR BANCARIO | `qaaxestmwmqmylthnwts` | Conciliador Bancario | login |

RLS activo en las 5 con la cuenta compartida `estudio@mrasoc.com`; signups cerrados. Backup
semanal cifrado de las 5 + Storage: repo `suite-backups` (`RESTORE.md` para restaurar).

---

## 4. Tokens y credenciales de GitHub (lo que más confunde)

- **`gh auth login` personal** (cuenta `ematiromero98`, scopes repo): lo que usa esta PC de
  desarrollo. Cubre todo.
- **Token del runtime** (`gh_token.txt`, lo deja el instalador «cero logins»): solo lectura;
  con él la Suite clona/actualiza aunque la PC no tenga `gh` logueado. Debe cubrir todos los
  repos de la suite **y** `suite-secretos`.
- **`GITHUB_TOKEN` del `.env` compartido** (`suite-secretos`): fine-grained
  **«RetencionesPro - clientes»** (id 15397886). Lo usan los actualizadores propios de las apps
  (RetencionesPro `update.bat`, Cobranzas `actualizador.py`). Desde el **11-09-2026 incluye 12
  repos**: RetencionesPro, cobranzas-osecac, ddjj-impuestos, contabilidad, deposito-avalos,
  facturador-arca, employee-pro, cm03-convenio-multilateral, calendario-ausencias,
  conciliador-bancario, control-juicios, arca-vep-autonomos. **No incluye `impuestos` ni
  `suite-secretos`** (a propósito lo segundo). Los fine-grained no pueden leer un repo privado
  fuera de su lista: el síntoma es 403 «Write access to repository not granted», y antes
  Cobranzas lo tragaba en silencio (arreglado en Cobranzas 2.61.1).
- El otro token fine-grained, **«Instalador Suite»** (todos los repos), es el candidato natural
  para el `gh_token.txt` del instalador.

---

## 5. Pendientes

1. **Agregar `impuestos` al token «RetencionesPro - clientes»** (GitHub → Settings → Developer
   settings → Fine-grained tokens → editar → Repository access) si la app Impuestos usa el
   `GITHUB_TOKEN` del `.env` para actualizarse; si no, verificar cómo se actualiza.
2. **Diagramas internos desactualizados:** `arquitectura.py` (`DATOS`, 9 apps: le faltan
   Impuestos, Calendario de Ausencias, VEP, y sobra DDJJ/CM03 como apps del menú),
   `assets/ecosistema-3d.html` (`NODES`/`EDGES`) y `conexiones_db.py` (`BASES` nombra DDJJ y
   CM03; agregar Impuestos). Son datos a mano.
3. **Docs viejas con listas de apps:** `README.md` (5 apps), `GUIA.md` §1 (6 apps),
   `ARQUITECTURA.md` §1 (9 apps). Este HANDOFF es la referencia; actualizarlas cuando se
   toquen.
4. `assets/apps/ddjj.png` y `cm03.png` quedan sin uso mientras esas apps no estén en el menú.
5. Sin tests: si crece `main.py`, extraer lo puro (`_es_mayor`, `_parse_version_txt`,
   `_mayor_disponible`, `_actualizar_app_core` sin red) a un módulo testeable.

---

## 6. Cómo trabajar acá

- Cambio → probar → commit + push a `main` (llega a cada PC al reabrir el ERP). Para cambios
  grandes, además bump `version.py` y tag `vX.Y.Z` (el pill de versión del pie lo muestra).
- **Verificar la UI:** `python -c` con `QApplication` + `Launcher()`; en pantalla
  (`w.show()`, `processEvents` unos segundos para que corran los chequeos, `w.grab().save()`)
  se ve con fuentes; `QT_QPA_PLATFORM=offscreen` sirve para lógica pero dibuja cuadraditos.
  `w._nav_panel.click()` / `w._nav_upd.click()` cambian de página.
- **Agregar una app:** entrada en `config.APPS` (`key`, `nombre`, `emoji`, `mono`, `desc`,
  `color`, `env_dir`, `dir`, `entradas`, `version_file`, `repo`) → `python
  generar_iconos_apps.py` → editar `arquitectura.py`/`conexiones_db.py`/`ecosistema-3d.html` →
  agregar el repo a los tokens (§4) y, si la app lee el `.env` compartido, a `_APPS_ENV` en
  `credenciales.py` (o a `_APPS_SECRETO` / `_CERTS` si tiene secreto o certs propios).
- El usuario trabaja en paralelo en este repo (hoy: alta de Impuestos y retiro de DDJJ/CM03
  desde otra sesión): `git fetch` + `git status` antes de tocar.

---

## 7. Proyectos relacionados

- **suite-secretos** (privado): `.env` compartido + `cobranzas.secretos.json` +
  `employee.secretos.json` + `cobranzas.certs/`. Fuente de todas las credenciales.
- **suite-backups**: CLI de backup semanal cifrado (AES-256) de las 5 bases + Storage,
  Task Scheduler domingos 22:00; escribe `suite_backup_runs`.
- Cada app tiene su propio HANDOFF: `cobranzas-osecac/HANDOFF.md`,
  `RetencionesPro/docs/HANDOFF_CONTABILIDAD.md`, y en las demás `HANDOFF.md`/`README.md`.
