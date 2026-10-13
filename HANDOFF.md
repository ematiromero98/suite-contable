# HANDOFF — Suite Contable (launcher / ERP del estudio)

> **Leé esto primero** para continuar el proyecto en un chat nuevo. Estado al **11-09-2026,
> v1.29.0**. Los documentos anteriores siguen valiendo por partes: `GUIA.md` (operación paso a
> paso), `ARQUITECTURA.md` (por qué repos separados + cómo se actualiza), `CORE-COMPARTIDO.md`
> (tema/formatos/`release.py` compartidos), `README.md`. Sus **listas de apps quedaron viejas**
> (5, 6 o 9 apps): la lista vigente es la de acá y la de `config.APPS`.

---

## 0. Qué es y estado actual

**Suite Contable** es el **launcher/ERP** de MR & Asociados: una ventana PyQt6 (tema «Panel
Oscuro», sidebar + topbar) que **abre, instala y actualiza** las apps del estudio, trae las
**credenciales**, muestra el **registro de backups**, y explica el ecosistema en el módulo
**🗺 Arquitectura** (pestañas: Apps y proyectos · Bases de datos · Conexiones · Ecosistema 3D ·
Documentación). No toca datos: cada app vive en su repo.

- **Local:** `D:\suite-contable` (checkout de desarrollo y también la instalación de esta PC).
  Configurable con `SUITE_CONTABLE_DIR`.
- **GitHub:** `ematiromero98/suite-contable`, **público a propósito** (se instala sin
  credenciales) → **nunca** un secreto en este repo. Rama `main`.
- **Versión:** `version.py` (`VERSION = "1.29.0"`). Tags `vX.Y.Z` para las versiones grandes;
  **el ERP se auto-actualiza con `git pull` de `main` al abrir** (no necesita release).
- **Tests** (desde la rama `ui/progreso-en-icono`): `python -m pytest -q` en `tests/`
  (avance por etapas sin GUI + `IconoProgreso` offscreen, que se saltea si no hay PyQt6).
  No hay CI en GitHub: correr a mano `pytest` + `pyflakes main.py ui tests`. El resto de
  la UI se sigue verificando a mano (construir `Launcher()` y capturar, ver §6).

**Páginas del sidebar** (`main.py`, `Launcher`): GENERAL → 🗂 Panel (tarjetas de apps: logo,
versión, estado, Abrir/Instalar/Actualizar), 🔄 Actualizaciones, 🗺 Arquitectura (con
pestañas internas), 💾 Registro de Backups · SISTEMA → ⚙ Ajustes. Índices del QStackedWidget:
Panel=0, Actualizaciones=1, Ajustes=2, Arquitectura=3, Backups=4. Topbar: «⟳ Actualizar todo
(N)» y «🔑 Traer credenciales». Marca del sidebar: logo **SC** azul (`assets/suite.png`).

**Apps registradas hoy (`config.APPS`, 13)** — key · monograma/color · carpeta · repo:

| key | App | Logo | Carpeta por defecto | Repo | Versión en |
|---|---|---|---|---|---|
| impuestos | Impuestos (IIBB + IVA) | IMP menta | `D:\PROYECTOS CLAUDE\impuestos` | `impuestos` (privado, **nuevo 11-09**, v1.9.0) | version.py |
| reten | RetencionesPro | RP verde | `D:\RetencionesPro` | `RetencionesPro` | version.py |
| cobranzas | Cobranzas OSECAC | COB ámbar | `D:\PROYECTOS CLAUDE\cobranzas-osecac` | `cobranzas-osecac` | VERSION |
| facturador | Facturador ARCA | FAC teal | `D:\PROYECTOS CLAUDE\facturador-arca` | `facturador-arca` (master) | VERSION |
| employee | Employee Pro | EP violeta | `D:\PROYECTOS CLAUDE\employee-pro` | `employee-pro` | version.py |
| deposito | Depósito Avalos (PySide6) | DA naranja | `D:\PROYECTOS CLAUDE\deposito-avalos` | `deposito-avalos` | version.py |
| uniformes | Depósito Uniformes | DU gris azulado | `D:\PROYECTOS CLAUDE\deposito-uniformes` | `deposito-uniformes` | version.py |
| juicios | Control de Juicios | CJ navy | `D:\control-juicios` | `control-juicios` | VERSION |
| contabilidad | Contabilidad | CTB verde oscuro | `D:\contabilidad` | `contabilidad` | VERSION |
| conciliador | Conciliador Bancario | CB verde | `D:\PROYECTOS CLAUDE\conciliador-bancario` | `conciliador-bancario` | VERSION |
| ausencias | Calendario de Ausencias | CA menta | `D:\PROYECTOS CLAUDE\calendario-ausencias` | `calendario-ausencias` | version.py |
| veps | VEP Autónomos | VEP púrpura | `D:\arca-vep-autonomos` | `arca-vep-autonomos` | VERSION |
| backups | Backups | BK gris pizarra | `D:\PROYECTOS CLAUDE\suite-backups` | `suite-backups` (privado, **nuevo 05-10**, v1.1.0) | `suitebackups\__init__.py` |

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
  **Token tapado (v1.35.1):** `_actualizar_app_core` es un envoltorio que llama a
  `_actualizar_app_core_impl` y pasa TODO detalle (fetch colgado/fallido —`TimeoutExpired`
  repite el comando con la URL—, merge/reset, pip, excepciones) por `_sin_token` ANTES de
  recortarlo: tapa los tokens usados y cualquier `https://usuario:token@…` o `ghp_…`/
  `github_pat_…`. `IconoProgreso.terminar/fallar` además tapan el tooltip
  (`ui.avance.tapar_credenciales`). Tests: `tests/test_sin_token.py`. `ui.avance` se importa
  protegido: si faltara, la Suite abre sin avance por etapas (`SeguidorAvance` mudo).
  Nota: con `QT_QPA_PLATFORM=offscreen` en Windows fallaba
  `test_leyendas_y_pastilla_entran_con_aire` (el plugin offscreen no hallaba las fuentes);
  desde v1.35.2 `tests/conftest.py` fija `QT_QPA_FONTDIR=C:\Windows\Fonts` y pasan todos.
- **Panel con ventana angosta** (v1.35.2): la grilla de tarjetas del Panel es
  `GrillaTarjetas` (`main.py`), ya no un `QGridLayout` fijo de 2 columnas. Escucha el resize
  del viewport del `QScrollArea` (y los `LayoutRequest` de las tarjetas) y pone **2 columnas
  si entran con el ancho mínimo de la tarjeta más ancha, si no 1** — nunca scroll
  horizontal ni tarjetas cortadas (antes, a ~1000 px la 2.ª columna quedaba cortada; desde
  v1.34 la leyenda bajo el ícono las hizo ~40 px más anchas). Con las fuentes de Windows el
  corte a 2 columnas cae en ~1186 px de ventana (tarjeta mínima ~438 px: «Facturador
  Monotributistas vX»). «Actualizaciones» es una lista vertical y no tenía el problema.
  Mínimo de ventana: se deja en **900×600** (el Panel a 1 columna necesita ~750 px;
  Arquitectura a 900 se ve apretada pero sin cortes). Tests: `tests/test_grilla_panel.py`
  (ventana a 1000 px: ninguna tarjeta fuera del viewport; 900/1180/1400/1800; 1↔2 columnas).
- **Actualización en el ícono** (v1.34.0, #082 de Lucian UX/UI Prompt, MIT): el logo de
  cada tarjeta del Panel y de cada fila de «Actualizaciones» es un `ui/icono_progreso.IconoProgreso` (QPainter): mientras la app se instala o
  actualiza, un velo oscuro se retira en sentido horario (`drawPie`) con el % encima; al
  terminar, ✓ menta con rebote (`QPropertyAnimation` OutBack) y la leyenda pasa a
  «actualizada»; ámbar «!» si quedó con aviso; borde/indicador rojo + tooltip con el motivo
  si falló. **El % es DERIVADO POR ETAPAS** (`ui/avance.py`, sin Qt): git/pip no dan un %
  real, así que `_actualizar_app_core` / `_pip_update` / `_instalar_app` reciben un
  `avisar(etapa)` opcional (sólo informa, no cambia la lógica) y cada etapa ocupa un tramo:
  cola 0 · fetch 2-40 · merge 40-50 · venv 50-60 · pip 60-97 · clonar 3-90 · listo 100.
  Dentro del tramo avanza con 1−e^(−t/τ) (nunca llega al techo hasta que la etapa siguiente
  lo confirma) y es monótono. «Actualizar todo» sigue yendo **de a una** (`_UpdateAllWorker`):
  las demás muestran «en cola» con el velo completo. El ancho del ícono sale de la leyenda
  más larga (`LEYENDAS`), así nada queda cortado. Las filas de «Actualizaciones» se
  reconstruyen seguido: `_aplicar_estado` las pone al día con `SeguidorAvance` +
  `_finales`.
- **Instalar** (desde v1.34.0 en segundo plano, la ventana no se congela):
  `_InstallWorker` (mismo esquema de hilo + señales que `_UpdateAllWorker`) corre
  `_instalar_app_core` = clone con token del runtime (o `gh repo clone`) en `app["dir"]` y
  deja el origin sin token. No crea venv ni deps (eso pasa en la primera actualización).
  Devuelve un motivo (`instalada`/`ya_estaba`/`carpeta_ajena`/`sin_credenciales`/
  `clone_fallo`/`excepcion`); `_resultado_instalacion` lo pasa al ícono y
  `_mensaje_instalacion` muestra los mismos avisos de siempre. El token se tapa (`***`) en
  cualquier mensaje. **Abrir** (`_abrir`): primer archivo de `entradas` que exista (`run.bat`, `main.py`…).
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
- **App «Backups»** (`key: backups`, repo privado `ematiromero98/suite-backups`, desde
  v1.32.0): tarjeta en el menú; «Abrir» corre `BACKUP-AHORA.bat` (backup manual completo,
  **pide confirmar S/N** porque tarda 1-2 h). Versión en `suitebackups\__init__.py`. Sin
  updater propio → la Suite lo actualiza con git pull; el token del runtime tiene que cubrir
  ese repo (no lee el `.env` compartido: sus secretos van en `secretos_backup.json` local).
  Necesita su `.venv` y PostgreSQL 17 instalados (ver su INSTALL.md); la tarea programada se
  registra aparte con `PROGRAMAR-AUTOMATICO.bat`.
- **Módulo Arquitectura** (`arquitectura.py` → `ModuloArquitectura`, desde oct-2026 junta lo
  que antes eran 3 entradas del sidebar). Pestañas: **Apps y proyectos** (`PaginaArquitectura`,
  datos en `PROYECTOS`/`BASES`), **Bases de datos** (`bases_datos.py`, `PROYECTOS_SUPA`:
  proyecto → schemas → apps, Edge Functions, buckets, backup y costo), **Conexiones**
  (`conexiones_db.py`, `BASES`: las 5 bases y cómo se conecta cada app: login / SQL directo /
  Edge Fn / REST key), **Ecosistema 3D** (tarjeta de `main.py` que abre
  `assets/ecosistema-3d.html`, arrays `NODES`/`EDGES`) y **Documentación** (los .md del repo
  con `QTextBrowser.setMarkdown`). **Son datos escritos a mano: al cambiar una app o una base
  hay que editarlos** (al día con las 13 apps del menú y las 5 bases de oct-2026; la vista
  general se acomoda sola en filas de 4).
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
| ORDENES DE PAGO – BELGRANO (compartida) | `zpwccecovhjmeibxafkg` | public: RetencionesPro, Impuestos, Contabilidad, Juicios, VEP, Facturador, Factura Mono, comprobantes-cel, suite-backups · schema `conciliador`: Conciliador Bancario · schema `rrhh`: Employee Pro + Calendario de Ausencias · schema `chermisqui`: qb-dashboard (+ /taxes), chermisqui-control-dias · schema `deposito`: Depósito Avalos + Depósito Uniformes (u_*), web del celular (Edge Fn `deposito-comprobante-cel`), bucket `deposito-comprobantes`; bucket público `releases` = canal de update de los .exe del Depósito | secret key / DB_URL (directo), login, Edge Function |
| COBRANZAS OSECAC | `rrarmatjyvmrpohsvfzg` | Cobranzas OSECAC (Impuestos y Contabilidad leen) | login con cuenta compartida (RLS) |
| AME-PAYROLL (us-west-1) | `vswtxuvknxsjfodgviiq` | ame-payroll (public), payroll-platform (schema `app`) — fuera de la Suite | login / directo |
| casamiento-matilara | `nlnzryrwvbqigqzqkqqf` | Portal Clientes (pc_*), app del casamiento — fuera de la Suite | login / Edge Function |

Son **4 proyectos** activos (org Pro: US$25 + ~US$10/mes de cómputo c/u − US$10 de crédito ≈
**US$55/mes**). EMPLOYEE-PRO (`ffcz…`) se dio de baja en oct-2026 (mudado al schema `rrhh`);
el Conciliador ya vivía en el schema `conciliador`. El 12-oct-2026 el Depósito se mudó al
schema `deposito` de la base central: DEPOSITO-AVALOS (`ioycuhefaalpqivhhryb`) quedó
**congelado** (sin permisos, sólo canal de update para .exe viejos) y se borra tras ~2 semanas
de gracia; hasta entonces son 5 (≈ US$65/mes). RLS activo con la cuenta compartida
`estudio@mrasoc.com`; signups cerrados. Backup semanal cifrado + Storage: repo
`suite-backups` (`RESTORE.md` para restaurar). Detalle visual: módulo Arquitectura → pestaña
«Bases de datos».

---

## 4. Tokens y credenciales de GitHub (lo que más confunde)

- **`gh auth login` personal** (cuenta `ematiromero98`, scopes repo): lo que usa esta PC de
  desarrollo. Cubre todo.
- **Token del runtime** (`gh_token.txt`, lo deja el instalador «cero logins»): solo lectura;
  con él la Suite clona/actualiza aunque la PC no tenga `gh` logueado. Debe cubrir todos los
  repos de la suite **y** `suite-secretos`.
- **`GITHUB_TOKEN` del `.env` compartido** (`suite-secretos`): fine-grained
  **«RetencionesPro - clientes»** (id 15397886). Lo usan los actualizadores propios de las apps
  (RetencionesPro `update.bat`, Cobranzas `actualizador.py`). Desde el **11-09-2026 incluye 13
  repos**: RetencionesPro, cobranzas-osecac, impuestos, ddjj-impuestos, contabilidad,
  deposito-avalos, facturador-arca, employee-pro, cm03-convenio-multilateral,
  calendario-ausencias, conciliador-bancario, control-juicios, arca-vep-autonomos. **No
  incluye `suite-secretos`** (a propósito). Los fine-grained no pueden leer un repo privado
  fuera de su lista: el síntoma es 403 «Write access to repository not granted», y antes
  Cobranzas lo tragaba en silencio (arreglado en Cobranzas 2.61.1).
- El otro token fine-grained, **«Instalador Suite»** (todos los repos), es el candidato natural
  para el `gh_token.txt` del instalador.

---

## 5. Pendientes

1. **Docs viejas con listas de apps:** `README.md` (5 apps), `GUIA.md` §1 (6 apps),
   `ARQUITECTURA.md` §1 (9 apps). Este HANDOFF es la referencia; actualizarlas cuando se
   toquen.
2. `assets/apps/ddjj.png` y `cm03.png` quedan sin uso mientras esas apps no estén en el menú.
3. Tests mínimos (sólo avance en el ícono): si crece `main.py`, extraer lo puro
   (`_es_mayor`, `_parse_version_txt`, `_mayor_disponible`) a un módulo testeable.

---

## 6. Cómo trabajar acá

- Cambio → probar → commit + push a `main` (llega a cada PC al reabrir el ERP). Para cambios
  grandes, además bump `version.py` y tag `vX.Y.Z` (el pill de versión del pie lo muestra).
- **Verificar la UI:** `python -c` con `QApplication` + `Launcher()`; en pantalla
  (`w.show()`, `processEvents` unos segundos para que corran los chequeos, `w.grab().save()`)
  se ve con fuentes; `QT_QPA_PLATFORM=offscreen` sirve para lógica y, con
  `QT_QPA_FONTDIR=C:/Windows/Fonts`, también dibuja bien las fuentes. Antes de construir
  `Launcher()` en una prueba, anular `Launcher._auto_update_suite` (hace fetch + `reset
  --hard` del propio repo), `credenciales`, `_Chequeador.correr` y `_BackupsLoader.correr`;
  el avance de los íconos se simula llamando `_on_etapa(key, etapa)` / `_on_una_lista(...)`.
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
