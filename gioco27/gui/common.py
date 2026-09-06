"""Widget e tag tkinter condivisi tra tutti i moduli GUI."""
import threading
import tkinter as tk
import time
from collections import deque
from tkinter import messagebox

from ..core.constants import PERM3_COLORS
from ..core.log import get_logger
from ..core.permutations import _compile_perm3_pat

_log = get_logger(__name__)


def run_in_thread(widget, job, error_title="Errore", on_error=None):
    """
    Esegue `job()` in un thread demone, con gestione errori standard.

    In caso di eccezione: registra il traceback nel log e mostra un
    messagebox di errore (marshallato sul thread Tk con widget.after).
    Se `on_error` e' fornita, viene chiamata (sul thread Tk) dopo il
    messagebox, con l'eccezione come argomento — utile per ripristinare
    lo stato della GUI.

    Il job resta responsabile di marshallare i propri aggiornamenti GUI
    con widget.after(0, ...): Tk non e' thread-safe.
    """
    def runner():
        try:
            job()
        except Exception as e:
            _log.exception("Errore nel thread di lavoro (%s)", error_title)
            def report(e=e):
                messagebox.showerror(error_title, str(e))
                if on_error is not None:
                    on_error(e)
            widget.after(0, report)
    t = threading.Thread(target=runner, daemon=True)
    t.start()
    return t


def ui_call(widget, fn):
    """
    Esegue `fn` sul thread Tk, senza esplodere se il widget e' stato distrutto.

    `widget.after(0, ...)` da un thread di lavoro solleva TclError se la
    finestra e' stata chiusa nel frattempo: e' il caso normale quando l'utente
    chiude un dialogo mentre il calcolo e' ancora in corso, e non deve
    produrre un traceback.
    """
    try:
        if widget.winfo_exists():
            widget.after(0, fn)
    except tk.TclError:
        pass


def fmt_duration(seconds):
    """Formatta una durata (secondi) come stringa breve: '45s', '1m 20s', '1h 05m'."""
    seconds = max(0, int(round(seconds)))
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m {s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m"


class EtaEstimator:
    """
    Stima del tempo rimanente robusta, basata sulla velocita' recente.

    Due accorgimenti contro il rumore (l'ETA che "balla"):
      1. Campionamento distribuito nel tempo: si registra un campione al massimo
         ogni `min_interval` secondi, cosi' la finestra copre sempre alcuni
         secondi reali anche quando i callback arrivano fittissimi (altrimenti
         pochi millisecondi di dati darebbero una pendenza ballerina).
      2. Regressione ai minimi quadrati su TUTTI i punti della finestra (non
         solo primo-vs-ultimo): usa l'informazione di tutti i campioni ed e'
         molto meno sensibile al jitter dei tempi.

    La velocita' di avvio non entra nel calcolo: misurando la pendenza tra
    campioni (che arrivano dopo l'avvio), il costo iniziale viene ignorato.
    """

    def __init__(self, window=60, min_interval=0.5, min_span=1.0, min_samples=5):
        self._samples = deque(maxlen=window)   # coppie (t, fatti)
        self._min_interval = min_interval
        self._min_span = min_span
        self._min_samples = min_samples

    def text(self, done, total):
        now = time.time()
        if done <= 0 or total <= 0 or done >= total:
            return ""
        # Registra un nuovo campione solo se e' passato abbastanza tempo,
        # cosi' la finestra copre secondi reali e non millisecondi.
        if not self._samples or (now - self._samples[-1][0]) >= self._min_interval:
            self._samples.append((now, done))
        n = len(self._samples)
        if n < self._min_samples:
            return ""
        xs = [t for t, _ in self._samples]
        ys = [d for _, d in self._samples]
        span = xs[-1] - xs[0]
        if span < self._min_span:
            return ""
        # Pendenza (item/s) per regressione lineare ai minimi quadrati.
        mx = sum(xs) / n
        my = sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        if sxx <= 0:
            return ""
        rate = sxy / sxx
        if rate <= 0:
            return ""
        remaining = (total - done) / rate
        return f"  -  ~{fmt_duration(remaining)} rimanenti"
def configure_matrix_tags(txt_widget, base_font=("Courier New", 9)):
    """Configura tag-colore bold per tutti i nomi di matrice su un tk.Text."""
    for name, color in PERM3_COLORS.items():
        txt_widget.tag_configure(
            f"mx_{name}", foreground=color,
            font=(base_font[0], base_font[1], "bold"))

def insert_colored(txt_widget, text, base_tags=()):
    """Inserisce testo colorando i nomi di matrice (SCD_U, CDS_U ...) in bold."""
    if isinstance(base_tags, str):
        base_tags = (base_tags,)
    pat = _compile_perm3_pat()
    parts = pat.split(str(text))
    for part in parts:
        if not part:
            continue
        if part in PERM3_COLORS:
            txt_widget.insert("end", part, (f"mx_{part}",) + tuple(base_tags))
        elif base_tags:
            txt_widget.insert("end", part, tuple(base_tags))
        else:
            txt_widget.insert("end", part)


# ----------------------------------------------------------------- Tooltip ---

# Descrizioni leggibili degli elementi GEN3
_GEN3_DESCRIPTIONS = {
    "SCD_U": "SCD_U  [0,1,2]  Identità  (nessun movimento)",
    "SDC_U": "SDC_U  [0,2,1]  Scambio posizioni 1↔2  (trasposizione)",
    "CSD_U": "CSD_U  [1,0,2]  Scambio posizioni 0↔1  (trasposizione)",
    "CDS_U": "CDS_U  [1,2,0]  Rotazione ciclica  0→1→2→0",
    "DSC_U": "DSC_U  [2,0,1]  Rotazione ciclica  0→2→1→0",
    "DCS_U": "DCS_U  [2,1,0]  Riflessione  0↔2  (trasposizione)",
    "MSC":   "MSC  Mescolamento Standard delle Colonne  (permutazione fissa del trucco)",
}


class Tooltip:
    """
    Tooltip leggero per widget Tkinter.

    Uso:
        Tooltip(widget, "Testo del tooltip")
        Tooltip.attach_gen3(label_widget, "SCD_U")
    """

    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 600) -> None:
        self._widget   = widget
        self._text     = text
        self._delay_ms = delay_ms
        self._tip_win: "tk.Toplevel | None" = None
        self._after_id = None
        widget.bind("<Enter>",  self._on_enter,  add="+")
        widget.bind("<Leave>",  self._on_leave,  add="+")
        widget.bind("<Destroy>", self._on_leave, add="+")

    def _on_enter(self, event=None) -> None:
        self._after_id = self._widget.after(self._delay_ms, self._show)

    def _on_leave(self, event=None) -> None:
        if self._after_id is not None:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _show(self) -> None:
        if self._tip_win:
            return
        try:
            x = self._widget.winfo_rootx() + 20
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
            self._tip_win = tw = tk.Toplevel(self._widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            lbl = tk.Label(
                tw, text=self._text,
                background="#fffbe6", foreground="#222",
                relief="solid", borderwidth=1,
                font=("Segoe UI", 9),
                padx=6, pady=3,
                justify="left",
                wraplength=340,
            )
            lbl.pack()
        except tk.TclError:
            pass

    def _hide(self) -> None:
        if self._tip_win:
            try:
                self._tip_win.destroy()
            except tk.TclError:
                pass
            self._tip_win = None

    @classmethod
    def attach_gen3(cls, widget: tk.Widget, name: str) -> "Tooltip":
        """Aggiunge un tooltip con la descrizione di un elemento GEN3."""
        text = _GEN3_DESCRIPTIONS.get(name, name)
        return cls(widget, text)

    @classmethod
    def attach_text_tag(cls, text_widget: tk.Text, tag: str,
                        tooltip_text: str, delay_ms: int = 600) -> None:
        """
        Aggiunge tooltip a un tag di un tk.Text widget.
        Bind su <Enter> e <Leave> del tag.
        """
        tip: list = [None]
        after_id: list = [None]

        def _enter(event):
            if after_id[0]:
                text_widget.after_cancel(after_id[0])
            def show():
                if tip[0]:
                    return
                try:
                    x = event.x_root + 10
                    y = event.y_root + 18
                    tw = tk.Toplevel(text_widget)
                    tw.wm_overrideredirect(True)
                    tw.wm_geometry(f"+{x}+{y}")
                    tk.Label(
                        tw, text=tooltip_text,
                        background="#fffbe6", foreground="#222",
                        relief="solid", borderwidth=1,
                        font=("Segoe UI", 9),
                        padx=6, pady=3, justify="left", wraplength=340,
                    ).pack()
                    tip[0] = tw
                except tk.TclError:
                    pass
            after_id[0] = text_widget.after(delay_ms, show)

        def _leave(event):
            if after_id[0]:
                text_widget.after_cancel(after_id[0])
                after_id[0] = None
            if tip[0]:
                try:
                    tip[0].destroy()
                except tk.TclError:
                    pass
                tip[0] = None

        text_widget.tag_bind(tag, "<Enter>", _enter)
        text_widget.tag_bind(tag, "<Leave>", _leave)
