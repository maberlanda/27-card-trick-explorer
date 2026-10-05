"""Scelte esplicite per reset e abbandono dell'esperimento (UX-1)."""
import tkinter as tk
from tkinter import ttk

from .common import prepara_dialogo
from .i18n import tr


def _scegli(parent, titolo, testo, scelte):
    dlg = tk.Toplevel(parent)
    dlg.title(titolo)
    dlg.resizable(False, False)
    dlg.transient(parent)
    risultato = None

    def termina(valore=None):
        nonlocal risultato
        risultato = valore
        dlg.destroy()

    ttk.Label(dlg, text=testo, wraplength=520, justify="left",
              padding=16).pack(fill="x")
    riga = ttk.Frame(dlg, padding=(16, 0, 16, 16))
    riga.pack(fill="x")
    for valore, chiave in scelte:
        bottone = ttk.Button(riga, text=tr(chiave),
                             command=lambda v=valore: termina(v))
        bottone.pack(side="left", padx=4)
    dlg.protocol("WM_DELETE_WINDOW", termina)
    dlg.bind("<Escape>", lambda e: termina())
    dlg.grab_set()
    prepara_dialogo(dlg, bottone)  # Annulla è sempre l'ultima scelta.
    parent.wait_window(dlg)
    return risultato


def conferma_reset(parent):
    return _scegli(parent, tr("workspace.reset.title"), tr("workspace.reset.confirm"),
                   ((True, "workspace.reset.action"), (None, "button.cancel"))) is True


def conferma_abbandono(parent):
    return _scegli(parent, tr("session.confirm.title"), tr("session.confirm.abandon"),
                   (("save", "button.save"), ("discard", "session.discard"),
                    (None, "button.cancel")))
