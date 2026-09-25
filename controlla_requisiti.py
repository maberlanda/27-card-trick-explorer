#!/usr/bin/env python3
"""
Controlla che le dipendenze di «Gioco delle 27 carte» siano installate.

Uso:
    python controlla_requisiti.py          # uso del programma
    python controlla_requisiti.py --dev    # anche test, analisi statica e build

Mostra per gruppi (Python, interfaccia grafica, runtime, export facoltativi e,
con --dev, test/build) che cosa e' presente e che cosa manca, e in fondo il
comando pip per installarlo.

Codice di uscita 1 solo se manca qualcosa di OBBLIGATORIO per avviare il
programma (Python troppo vecchio, numpy, tkinter); le librerie facoltative e
quelle di sviluppo non sono mai un errore fatale. Senza tkinter la CLI batch
(`python -m gioco27 --help`) funziona comunque.
"""
import importlib
import sys

#: requires-python di pyproject.toml (un test ne verifica la coerenza).
PYTHON_MINIMO = (3, 10)

# (modulo_da_importare, nome_pip, obbligatorio, descrizione)
DEPS = [
    ("tkinter",   None,        True,  "interfaccia grafica (inclusa in Python / pacchetto di sistema)"),
    ("numpy",     "numpy",     True,  "calcolo matriciale (runtime)"),
    ("reportlab", "reportlab", False, "export PDF (extra export)"),
    ("openpyxl",  "openpyxl",  False, "export Excel .xlsx (extra export)"),
    ("pypdf",     "pypdf",     False, "unione PDF nell'export parallelo (extra export)"),
    ("pikepdf",   "pikepdf",   False, "deduplica risorse nei PDF uniti (extra export)"),
]

# Solo con --dev: non servono per usare il programma.
DEV_DEPS = [
    ("pytest",      "pytest",      "test (extra test)"),
    ("pyflakes",    "pyflakes",    "analisi statica (extra test)"),
    ("pypdfium2",   "pypdfium2",   "rasterizzazione PDF in un test (extra test)"),
    ("PIL",         "pillow",      "immagini per pypdfium2 (extra test)"),
    ("build",       "build",       "sdist e wheel (extra build)"),
    ("PyInstaller", "pyinstaller", "eseguibile desktop (extra build)"),
]


def _version(mod):
    for attr in ("__version__", "Version", "VERSION", "version"):
        v = getattr(mod, attr, None)
        if v and isinstance(v, str):
            return v
    if getattr(mod, "__name__", "") == "tkinter":
        return str(getattr(mod, "TkVersion", "?"))
    return "?"


def _prova(imp):
    try:
        mod = importlib.import_module(imp)
    except Exception:
        return None
    # Una cartella omonima nella directory corrente (es. `build/`) si importa
    # come namespace package vuoto: non e' la libreria.
    if getattr(mod, "__file__", None) is None and imp not in sys.builtin_module_names:
        return None
    return mod


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    dev = "--dev" in argv
    fatali = []

    versione = sys.version_info[:2]
    ok_py = versione >= PYTHON_MINIMO
    print(f"Python {sys.version.split()[0]}  "
          f"({'OK' if ok_py else 'TROPPO VECCHIO'}: serve {'.'.join(map(str, PYTHON_MINIMO))} o superiore)")
    if not ok_py:
        fatali.append("python")
    print("\nDipendenze di Gioco delle 27 carte:\n")

    da_installare = []
    tkinter_mancante = False
    for imp, pip_name, required, desc in DEPS:
        mod = _prova(imp)
        if mod is not None:
            print(f"  [ OK ]  {imp:11} {_version(mod):>10}   {desc}")
            continue
        etich = "MANCA!" if required else "manca "
        print(f"  [{etich}] {imp:11} {'':>10}   {desc}")
        if required:
            fatali.append(imp)
        if imp == "tkinter":
            tkinter_mancante = True
        elif pip_name:
            da_installare.append(pip_name)

    if dev:
        print("\nSviluppo, test e build (--dev, mai obbligatorie):\n")
        for imp, pip_name, desc in DEV_DEPS:
            mod = _prova(imp)
            if mod is not None:
                print(f"  [ OK ]  {imp:11} {_version(mod):>10}   {desc}")
            else:
                print(f"  [manca ] {imp:11} {'':>10}   {desc}")
                da_installare.append(pip_name)

    print()
    if da_installare:
        print("Per installare le librerie mancanti:")
        print("    pip install " + " ".join(dict.fromkeys(da_installare)))
        print("(tutto per l'uso: pip install -r requirements.txt; "
              "per lo sviluppo: pip install -r requirements-dev.txt)")
    if tkinter_mancante:
        print("tkinter non si installa con pip:")
        print("  • Windows/macOS: reinstalla Python da python.org lasciando spuntato 'tcl/tk'")
        print("  • Linux:         sudo apt install python3-tk")
        print("  Senza tkinter funziona solo la CLI batch:  python -m gioco27 --help")
    if not da_installare and not tkinter_mancante and ok_py:
        print("Tutto a posto: nessuna dipendenza mancante.")

    # 1 solo se manca qualcosa di OBBLIGATORIO (Python, numpy, tkinter).
    return 1 if fatali else 0


if __name__ == "__main__":
    sys.exit(main())
