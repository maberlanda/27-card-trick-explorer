"""Adattatore di compatibilita': il catalogo i18n vive in `gioco27.i18n`.

Dalla chiusura del compartimento A (A2) il servizio di localizzazione non
appartiene piu' al package GUI: il dominio (`gioco27.core`) deve poterlo usare
senza dipendere da `gioco27.gui`.  Il proprietario e' `gioco27/i18n.py`.

Questo modulo resta come re-export, cosi' che la GUI e i test continuino a
funzionare con `from .i18n import tr` e con `from gioco27.gui.i18n import
CATALOGS, set_language`.  Nessun catalogo e' duplicato: qui non ci sono dati,
soltanto rimandi agli oggetti del proprietario (stessi dizionari, stesse
funzioni, stesso stato di lingua).
"""
from __future__ import annotations

from .. import i18n as _i18n
from ..i18n import CATALOGS, format_integer, get_language, set_language, tr

__all__ = ["CATALOGS", "format_integer", "get_language", "set_language", "tr"]


def __getattr__(name: str):
    """Espone ogni altro nome del proprietario, stato interno compreso."""
    return getattr(_i18n, name)


def __dir__():
    return sorted(set(__all__) | set(dir(_i18n)))
