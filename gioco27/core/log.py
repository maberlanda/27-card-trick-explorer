"""
Logging centralizzato su ~/.gioco27/gioco27.log.

Uso:
    from ..core.log import get_logger
    log = get_logger(__name__)
    log.warning("...")
    log.exception("...")   # dentro un except: registra anche il traceback

Il file ruota automaticamente (max ~512 KB x 3 backup). Se il file di log
non e' scrivibile, il logging degrada silenziosamente a NullHandler:
il programma non deve mai fallire a causa del logging.
"""
import logging
import logging.handlers
import pathlib

_LOG_DIR  = pathlib.Path.home() / ".gioco27"
_LOG_FILE = _LOG_DIR / "gioco27.log"

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    _configured = True
    root = logging.getLogger("gioco27")
    root.setLevel(logging.INFO)
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            _LOG_FILE, maxBytes=512 * 1024, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s  %(levelname)-7s %(name)s: %(message)s"))
        root.addHandler(handler)
    except Exception:
        root.addHandler(logging.NullHandler())


def get_logger(name: str = "gioco27") -> logging.Logger:
    """Restituisce un logger figlio di 'gioco27' (configura al primo uso)."""
    _configure()
    if not name.startswith("gioco27"):
        name = f"gioco27.{name}"
    return logging.getLogger(name)
