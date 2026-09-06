"""
Tooltip leggero per Tkinter (non esiste un widget nativo).

Uso:
    from .tooltip import attach
    attach(widget, "Testo d'aiuto mostrato al passaggio del mouse")

Il tooltip compare dopo un breve ritardo e scompare all'uscita del mouse
o al click. Pensato per pulsanti, etichette, campi e "termini tecnici".
"""
import tkinter as tk


class Tooltip:
    """Mostra un piccolo riquadro giallo d'aiuto sopra un widget."""

    BG = "#FFF8E1"
    FG = "#3a2f1a"
    BORDER = "#E0C97F"

    def __init__(self, widget, text, delay=450, wraplength=320):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def set_text(self, text):
        self.text = text

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self._tip is not None or not self.text:
            return
        try:
            x = self.widget.winfo_pointerx() + 14
            y = self.widget.winfo_pointery() + 18
        except tk.TclError:
            return
        self._tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        try:
            tw.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        tw.wm_geometry(f"+{x}+{y}")
        frame = tk.Frame(tw, bg=self.BORDER, bd=0)
        frame.pack()
        tk.Label(frame, text=self.text, justify="left",
                 bg=self.BG, fg=self.FG, font="GiocoHelp",
                 wraplength=self.wraplength, padx=8, pady=5,
                 bd=0).pack(padx=1, pady=1)

    def _hide(self, _event=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


def attach(widget, text, **kwargs):
    """Scorciatoia: collega un Tooltip a un widget e lo restituisce."""
    return Tooltip(widget, text, **kwargs)
