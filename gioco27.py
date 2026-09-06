#!/usr/bin/env python3
"""Launcher: avvia l'applicazione Gioco delle 27 Carte.

Uso:
    python gioco27.py               # avvia la GUI
    python gioco27.py --selftest    # verifica di integrità
oppure (con il package):
    python -m gioco27
"""
import sys, os

# Assicura che la directory del launcher sia nel path
here = os.path.dirname(os.path.abspath(__file__))
if here not in sys.path:
    sys.path.insert(0, here)


def main():
    # Delega a gioco27.__main__.main: cosi' `python gioco27.py --selftest`
    # funziona esattamente come `python -m gioco27 --selftest`, invece di
    # ignorare l'argomento e aprire la GUI.
    from gioco27.__main__ import main as _main
    _main()


# Il guard __main__ è OBBLIGATORIO: su Windows il multiprocessing usa "spawn",
# che re-importa questo modulo in ogni processo figlio. Senza il guard, ogni
# worker rilancerebbe l'intera GUI. freeze_support() serve se si crea un .exe.
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
