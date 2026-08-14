# -*- coding: utf-8 -*-
"""
release.py — Publica una versión nueva de una app de la suite de forma ATÓMICA
y a prueba del bug que dejaba al ERP "tirando para atrás".

Qué hace, en orden, y frena si algo no cierra:
  1. Detecta el archivo de versión de la app (VERSION | version.py | scripts/version.py).
  2. Verifica: es repo git, remote `origin` oficial de github.com, y árbol limpio
     (o sólo el archivo de versión modificado).
  3. Escribe la versión nueva en ese archivo.
  4. Commit + push a la rama por defecto (con fallback al token de `gh` si el
     origin es de sólo lectura, como RetencionesPro).
  5. Crea el GitHub Release `vX.Y.Z` apuntando a esa rama.
  6. CHEQUEO FINAL: relee la versión del código publicado y la compara con el
     tag del release. Si no coinciden -> avisa fuerte (esa desincronización es
     la que hacía loopear al ERP).

Uso (parado en la carpeta de la app)::

    python D:\\suite-contable\\release.py 1.43.5
    python D:\\suite-contable\\release.py 1.43.5 --dir "D:\\RetencionesPro" --yes
"""
import argparse
import os
import re
import subprocess
import sys

# La consola de Windows (cp1252) no encodea algunos glifos; que nunca crashee.
try:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:  # noqa: BLE001
    pass

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Candidatos de archivo de versión, en orden de preferencia.
_VERSION_FILES = ["VERSION", "version.py", os.path.join("scripts", "version.py")]
_SEMVER = re.compile(r"^\d+\.\d+(\.\d+)?$")


def _run(args, cwd, timeout=60):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout, creationflags=_NO_WINDOW)


def _git(cwd, *args, timeout=120):
    return _run(["git", "-C", cwd, *args], cwd, timeout)


def _fail(msg):
    print(f"\n[ABORTA] {msg}")
    sys.exit(1)


def _detectar_version_file(d):
    for vf in _VERSION_FILES:
        if os.path.isfile(os.path.join(d, vf)):
            return vf
    _fail("No encontré archivo de versión (VERSION / version.py / scripts/version.py).")


def _leer_version(texto):
    m = re.search(r'(?:__version__|VERSION)\s*=\s*["\']([^"\']+)["\']', texto)
    if m:
        return m.group(1)
    linea = (texto.strip().splitlines() or [""])[0].strip()
    return linea.lstrip("vV") if re.match(r"^v?\d+(\.\d+)*$", linea) else None


def _escribir_version(path, nueva):
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    if re.search(r'(?:__version__|VERSION)\s*=', txt):
        nuevo = re.sub(r'((?:__version__|VERSION)\s*=\s*["\'])[^"\']+(["\'])',
                       rf'\g<1>{nueva}\g<2>', txt, count=1)
    else:                                   # archivo VERSION en texto plano
        nuevo = nueva + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(nuevo)


def _rama_actual(d):
    r = _git(d, "rev-parse", "--abbrev-ref", "HEAD")
    return r.stdout.strip()


def _origin_oficial(d):
    r = _git(d, "remote", "get-url", "origin")
    url = (r.stdout or "").strip().lower()
    return "github.com" in url and "ematiromero98/" in url, url


def _gh_token():
    r = _run(["gh", "auth", "token"], os.getcwd())
    return r.stdout.strip() if r.returncode == 0 else None


def _repo_slug(d):
    raw = (_git(d, "remote", "get-url", "origin").stdout or "").strip()
    m = re.search(r"github\.com[:/](ematiromero98/[^/.\s]+?)(?:\.git)?$", raw)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser(description="Publica una versión de una app de la suite.")
    ap.add_argument("version", help="Versión nueva, ej. 1.43.5")
    ap.add_argument("--dir", default=".", help="Carpeta del repo (default: actual)")
    ap.add_argument("--notes", default="", help="Notas del release")
    ap.add_argument("--yes", action="store_true", help="No pedir confirmación")
    a = ap.parse_args()

    d = os.path.abspath(a.dir)
    nueva = a.version.lstrip("vV")
    if not _SEMVER.match(nueva):
        _fail(f"Versión inválida: {a.version} (usá X.Y o X.Y.Z).")
    if not os.path.isdir(os.path.join(d, ".git")):
        _fail(f"{d} no es un repo git.")

    ok, url = _origin_oficial(d)
    if not ok:
        _fail(f"El remote origin no es oficial (github.com/ematiromero98): {url}")
    repo = _repo_slug(d)
    rama = _rama_actual(d)

    vf = _detectar_version_file(d)
    vf_path = os.path.join(d, vf)
    with open(vf_path, encoding="utf-8") as f:
        actual = _leer_version(f.read())

    # árbol limpio (o sólo el archivo de versión tocado)
    est = _git(d, "status", "--porcelain").stdout.strip().splitlines()
    sucios = [l for l in est if l[3:].strip() != vf.replace("\\", "/")]
    if sucios:
        _fail("Hay cambios sin commitear (aparte del archivo de versión):\n  "
              + "\n  ".join(sucios) + "\nCommiteá o limpiá antes de publicar.")

    print(f"Repo:     {repo}  (rama {rama})")
    print(f"Versión:  {actual}  ->  {nueva}   [{vf}]")
    print(f"Release:  v{nueva}")
    if not a.yes:
        if input("\n¿Publicar? Esto pushea y crea el release [s/N]: ").strip().lower() not in ("s", "si", "y"):
            print("Cancelado."); sys.exit(0)

    # 1) escribir versión + commit
    _escribir_version(vf_path, nueva)
    _git(d, "add", vf)
    c = _git(d, "commit", "-m", f"chore: release v{nueva}")
    if c.returncode != 0 and "nothing to commit" not in (c.stdout + c.stderr):
        _fail("No pude commitear:\n" + (c.stderr or c.stdout))

    # 2) push (con fallback a token de gh si el origin es read-only)
    p = _git(d, "push", "origin", rama)
    if p.returncode != 0:
        tok = _gh_token()
        if tok:
            p = _git(d, "push", f"https://x-access-token:{tok}@github.com/{repo}.git", rama)
        if p.returncode != 0:
            _fail("Falló el push:\n" + (p.stderr or p.stdout))
    print("  push OK")

    # 3) crear el release
    notas = a.notes or f"Release v{nueva}."
    r = _run(["gh", "release", "create", f"v{nueva}", "--repo", repo,
              "--target", rama, "--title", f"v{nueva}", "--notes", notas], d)
    if r.returncode != 0:
        _fail("Falló crear el release:\n" + (r.stderr or r.stdout))
    print(f"  release v{nueva} creado")

    # 4) CHEQUEO FINAL: versión publicada == tag (el bug del loop)
    _git(d, "fetch", "--tags", "--quiet")
    show = _git(d, "show", f"v{nueva}:{vf.replace(os.sep, '/')}")
    pub = _leer_version(show.stdout) if show.returncode == 0 else None
    print("\n==== VERIFICACION ====")
    print(f"  codigo publicado (tag v{nueva}) reporta version: {pub}")
    if pub == nueva:
        print("  [OK] Coincide. El ERP va a ver esta app al dia (sin loop).")
    else:
        print(f"  [ERROR] NO coincide (codigo={pub}, tag={nueva}). El ERP va a loopear.")
        print("    Revisa el archivo de version y volve a publicar.")
        sys.exit(2)


if __name__ == "__main__":
    main()
