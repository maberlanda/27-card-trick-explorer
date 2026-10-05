"""
Tooltip leggero per Tkinter (non esiste un widget nativo).

Uso:
    from .tooltip import attach
    attach(widget, "Testo d'aiuto mostrato al passaggio del mouse")

Il tooltip compare dopo un breve ritardo e scompare all'uscita del mouse
o al click. Pensato per pulsanti, etichette, campi e "termini tecnici".

Compartimento H2: compare anche quando il widget riceve il focus da tastiera.
Prima era un'informazione che esisteva solo per chi usa il mouse; ora chi
arriva con Tab legge le stesse cose. Il riquadro si posiziona accanto al
widget quando arriva dal focus (il puntatore potrebbe essere altrove) e
accanto al puntatore quando arriva dal passaggio del mouse.
"""
import tkinter as tk


def posizione_tooltip(x, y, width, height, screen_width, screen_height,
                      control_top=None):
    """Keep the help visible; prefer above the control at the bottom edge."""
    margin = 4
    if y + height > screen_height - margin and control_top is not None:
        y = control_top - height - margin
    return (max(margin, min(x, screen_width - width - margin)),
            max(margin, min(y, screen_height - height - margin)))


class Tooltip:
    """Mostra un piccolo riquadro giallo d'aiuto sopra un widget."""

    BG = "#FFF8E1"
    FG = "#3a2f1a"
    BORDER = "#E0C97F"
    #: Ritardo prima di mostrare il riquadro. Attributo di classe perché è
    #: anche il tempo che un test deve aspettare per vederlo comparire.
    RITARDO = 450

    def __init__(self, widget, text, delay=None, wraplength=320):
        self.widget = widget
        self.text = text
        self.delay = self.RITARDO if delay is None else delay
        self.wraplength = wraplength
        self._after_id = None
        self._tip = None
        self._dal_focus = False
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")
        # H2: la stessa informazione, per chi non usa il mouse.
        widget.bind("<FocusIn>", self._schedule_dal_focus, add="+")
        widget.bind("<FocusOut>", self._hide, add="+")
        widget.bind("<Escape>", self._hide, add="+")
        widget.bind("<Destroy>", self._hide, add="+")
        widget._tooltip = self

    def set_text(self, text):
        self.text = text
        if self._tip is not None:
            self._hide()
            self._after_id = self.widget.after(self.delay, self._show)

    def _schedule(self, _event=None):
        self._claim()
        self._dal_focus = False
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _schedule_dal_focus(self, _event=None):
        self._claim()
        self._dal_focus = True
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _claim(self):
        root = self.widget._root()
        previous = getattr(root, "_active_tooltip", None)
        if previous is not None and previous is not self:
            previous._hide()
        root._active_tooltip = self

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        self._after_id = None
        if self._tip is not None or not self.text:
            return
        try:
            text = self.text() if callable(self.text) else self.text
            if not text:
                return
            if self._dal_focus:
                # Il puntatore potrebbe essere dall'altra parte dello schermo:
                # accanto al widget, non accanto al mouse.
                x = self.widget.winfo_rootx() + 12
                y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
            else:
                x = self.widget.winfo_pointerx() + 14
                y = self.widget.winfo_pointery() + 18
        except tk.TclError:
            return
        self._claim()
        self._tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        try:
            tw.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        tw.withdraw()
        frame = tk.Frame(tw, bg=self.BORDER, bd=0)
        frame.pack()
        label = tk.Label(frame, text=text, justify="left",
                 bg=self.BG, fg=self.FG, font="GiocoHelp",
                 wraplength=min(self.wraplength, self.widget.winfo_screenwidth() - 28), padx=8, pady=5,
                 bd=0)
        label.pack(padx=1, pady=1)
        tw.update_idletasks()
        while (tw.winfo_reqheight() > self.widget.winfo_screenheight() - 16
               and int(label.cget("wraplength")) < self.widget.winfo_screenwidth() - 28):
            label.configure(wraplength=min(int(label.cget("wraplength")) * 2,
                                           self.widget.winfo_screenwidth() - 28))
            tw.update_idletasks()
        x, y = posizione_tooltip(x, y, tw.winfo_reqwidth(), tw.winfo_reqheight(),
                                 self.widget.winfo_screenwidth(),
                                 self.widget.winfo_screenheight(),
                                 self.widget.winfo_rooty())
        tw.wm_geometry(f"+{x}+{y}")
        tw.deiconify()

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
    existing = getattr(widget, "_tooltip", None)
    if existing is not None:
        existing.set_text(text)
        return existing
    return Tooltip(widget, text, **kwargs)
