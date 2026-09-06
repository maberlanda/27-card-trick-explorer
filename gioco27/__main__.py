"""Punto di ingresso: python -m gioco27  [--selftest]"""
import sys


def main():
    from . import __version__
    from .core.log import get_logger
    log = get_logger("main")

    if "--selftest" in sys.argv:
        from .core.gioco_reale import selftest
        print(f"Gioco delle 27 carte v{__version__} — verifica di integrità")
        try:
            for k, v in selftest().items():
                print(f"  {k:28s} {v}")
        except AssertionError as e:
            print(f"  ✗ INCOERENZA: {e}")
            sys.exit(1)
        sys.exit(0)

    log.info("Avvio Gioco delle 27 carte v%s", __version__)
    try:
        from .gui.app import App
        App().mainloop()
    except Exception:
        log.exception("Errore fatale all'avvio")
        raise


# Guard obbligatorio per il multiprocessing su Windows (spawn re-importa il modulo).
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
