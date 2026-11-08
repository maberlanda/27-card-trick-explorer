"""Punto di ingresso: python -m gioco27  [--selftest | <comando batch> …] (vedi cli.py)"""
import sys


def _comandi_cli():
    from .cli import COMANDI
    return COMANDI


def _smoke_gui():
    """Verifica l'avvio Tk e i due export PDF del bundle di rilascio."""
    from pathlib import Path
    from tempfile import TemporaryDirectory

    from pypdf import PdfReader

    from .core import config
    from .core.combinations import generate_pdf_ex_parallel
    from .core.detail_pdf import generate_detail_pdf_parallel
    from .gui.app import App

    with TemporaryDirectory(prefix="gioco27-smoke-") as directory:
        folder = Path(directory)
        config._CONFIG_DIR = folder
        config._CONFIG_FILE = folder / "config.json"
        app = App()
        try:
            app.update()
            if not app.winfo_viewable():
                raise RuntimeError("Finestra principale non visualizzata")
            filters = [dict(p0="SCD_U", p1="SCD_U", p2="SCD_U",
                            j0="I_3", j1="I_3", j2="I_3") for _ in range(3)]
            for name, generate in (("matrix", generate_pdf_ex_parallel),
                                   ("detail", generate_detail_pdf_parallel)):
                path = folder / f"{name}.pdf"
                if generate(path, filters, n_workers=1) != 1 or len(PdfReader(path).pages) != 1:
                    raise RuntimeError(f"Verifica PDF fallita: {name}")
        finally:
            app.destroy()


def main():
    # J: comandi batch senza Tk (python -m gioco27 validate|replay|…|--help)
    if len(sys.argv) > 1 and (sys.argv[1] in _comandi_cli() or sys.argv[1] in ("-h", "--help", "--version")):
        from .cli import main as cli_main
        sys.exit(cli_main(sys.argv[1:]))

    from . import __version__
    from .core.log import get_logger
    log = get_logger("main")

    if sys.argv[1:] == ["--smoke-gui"]:
        try:
            _smoke_gui()
        except Exception:
            log.exception("Verifica dell'avvio GUI e dei PDF fallita")
            sys.exit(1)
        return

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
