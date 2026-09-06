#!/usr/bin/env python3
"""
Controlla che le dipendenze di «Gioco delle 27 carte» siano installate.

Uso:
    python controlla_requisiti.py

Mostra per ogni libreria se è presente (con la versione) o mancante, e in fondo
il comando pip per installare ciò che serve. Codice di uscita 1 se manca una
dipendenza OBBLIGATORIA, altrimenti 0.
"""
import importlib
import sys

# (modulo_da_importare, nome_pip, obbligatorio, descrizione)
DEPS = [
    ("numpy",     "numpy",     True,  "calcolo matriciale (richiesto)"),
    ("tkinter",   None,        True,  "interfaccia grafica (richiesto)"),
    ("reportlab", "reportlab", False, "export PDF"),
    ("openpyxl",  "openpyxl",  False, "export Excel (.xlsx)"),
    ("pypdf",     "pypdf",     False, "unione PDF nell'export parallelo"),
    ("pikepdf",   "pikepdf",   False, "deduplica risorse nei PDF uniti"),
]


def _version(mod):
    for attr in ("__version__", "Version", "VERSION", "version"):
        v = getattr(mod, attr, None)
        if v:
            return str(v)
    return "?"


def main():
    print(f"Python {sys.version.split()[0]}")
    print("Dipendenze di Gioco delle 27 carte:\n")

    da_installare = []
    tkinter_mancante = False

    for imp, pip_name, required, desc in DEPS:
        try:
            mod = importlib.import_module(imp)
            print(f"  [ OK ]  {imp:10} {_version(mod):>10}   {desc}")
        except Exception:
            etich = "MANCA!" if required else "manca "
            print(f"  [{etich}] {imp:10} {'':>10}   {desc}")
            if imp == "tkinter":
                tkinter_mancante = True
            elif pip_name:
                da_installare.append(pip_name)

    print()
    if da_installare:
        print("Per installare le librerie mancanti:")
        print("    pip install " + " ".join(dict.fromkeys(da_installare)))
    if tkinter_mancante:
        print("tkinter non si installa con pip:")
        print("  • Windows: reinstalla Python da python.org lasciando spuntato 'tcl/tk'")
        print("  • Linux:   sudo apt install python3-tk")
    if not da_installare and not tkinter_mancante:
        print("Tutto a posto: nessuna dipendenza mancante.")

    # Esce con 1 solo se manca qualcosa di OBBLIGATORIO (numpy o tkinter)
    obbligatorie_mancanti = tkinter_mancante or ("numpy" in da_installare)
    return 1 if obbligatorie_mancanti else 0


if __name__ == "__main__":
    sys.exit(main())
