"""
Font con nome per i testi di aiuto / note, scalabili dall'utente.

I widget di aiuto (tooltip, banner, glossario, pannelli esplicativi, stati
vuoti) usano questi font *con nome* invece di tuple fisse: così basta
riconfigurarli una volta per ingrandire tutto il testo d'aiuto, comodo sui
monitor 4K. La scala è salvata in config ("help_font_scale") e regolabile da
Impostazioni → "Dimensione testo aiuti".
"""
import tkinter as tk
import tkinter.font as tkfont

# nome -> (famiglia, size_base@100%, weight, slant, underline)
_BASE = {
    "GiocoHelp":         ("Segoe UI", 10, "normal", "roman",  0),
    "GiocoHelpBold":     ("Segoe UI", 10, "bold",   "roman",  0),
    "GiocoHelpItalic":   ("Segoe UI", 10, "normal", "italic", 0),
    "GiocoHelpLink":     ("Segoe UI",  9, "normal", "roman",  1),
    "GiocoHelpMono":     ("Consolas", 10, "normal", "roman",  0),
    "GiocoHelpMonoBold": ("Consolas", 10, "bold",   "roman",  0),
}

_scale = 1.0
# Riferimenti persistenti ai Font: senza, l'oggetto Font verrebbe raccolto dal
# garbage collector e il suo __del__ cancellerebbe il font con nome in Tcl.
_fonts: dict = {}


def apply_scale(scale, root=None):
    """Crea/riconfigura i font con nome alla scala data (1.0 = 100%)."""
    global _scale
    try:
        _scale = max(0.7, min(3.0, float(scale)))
    except (TypeError, ValueError):
        _scale = 1.0
    for name, (fam, size, weight, slant, under) in _BASE.items():
        f = _fonts.get(name)
        if f is None:
            try:
                f = tkfont.nametofont(name)
            except tk.TclError:
                f = tkfont.Font(name=name, root=root)
            _fonts[name] = f   # mantieni vivo il riferimento
        f.configure(family=fam, size=max(7, round(size * _scale)),
                    weight=weight, slant=slant, underline=under)


def get_scale():
    return _scale
