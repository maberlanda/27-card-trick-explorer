"""Widget e tag tkinter condivisi tra tutti i moduli GUI."""
import threading
import tkinter as tk
import time
from collections import deque
from tkinter import messagebox

from ..core.constants import PERM3_COLORS
from ..core.log import get_logger
from ..core.permutations import _compile_perm3_pat
from .errori import per_utente
from .i18n import tr

_log = get_logger(__name__)


def run_in_thread(widget, job, error_title=None, on_error=None):
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
    if error_title is None:
        # Risolto alla chiamata, non alla definizione: segue la lingua attiva.
        error_title = tr("error.generic")

    def runner():
        if getattr(widget, "_closing", False):
            return
        try:
            job()
        except Exception as e:
            _log.exception("Errore nel thread di lavoro (%s)", error_title)
            def report(e=e):
                # H1: il titolo lo sceglie chi ha avviato il lavoro, che sa di
                # che lavoro si tratta; il messaggio lo compone il confine di
                # presentation, che sa dirlo nella lingua attiva. Prima era
                # `str(e)`, cioe' il testo neutro del core — italiano anche in
                # inglese.
                messagebox.showerror(error_title, per_utente(e)[1])
                if on_error is not None:
                    on_error(e)
            ui_call(widget, report)
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
    if getattr(widget, "_closing", False):
        return

    def invoke():
        if getattr(widget, "_closing", False):
            return
        try:
            exists = widget.winfo_exists()
        except tk.TclError:
            return
        if exists:
            fn()

    try:
        if widget.winfo_exists():
            widget.after(0, invoke)
    except (tk.TclError, RuntimeError):
        pass


def prepara_dialogo(dialogo, primo=None):
    """Focus iniziale scelto, e Esc che chiude (H2).

    Prima nessun dialogo sceglieva il proprio focus: lo assegnava Tk, cioè il
    primo widget che capitava nell'ordine di creazione. Chi arriva con la
    tastiera si trovava «da qualche parte» e doveva cercare. `primo` è il
    controllo da cui ha senso cominciare — il campo che si compila, l'elenco
    che si consulta — e viene messo a fuoco dopo la mappatura della finestra,
    perché prima Tk lo rifiuterebbe.

    Esc chiude: per questi dialoghi «chiudi» e «annulla» sono la stessa cosa,
    e ognuno ha già il suo pulsante Chiudi. Dove non lo sono — il dialogo
    delle impostazioni — Esc viene legato dal dialogo stesso a ciò che
    equivale davvero ad annullare.
    """
    dialogo.bind("<Escape>", lambda _e: dialogo.destroy())
    if primo is not None:
        dialogo._focus_iniziale = primo
        dialogo.after(0, lambda: _focus_se_esiste(primo))
    return dialogo


def _focus_se_esiste(widget):
    try:
        if widget.winfo_exists():
            widget.focus_set()
    except tk.TclError:
        pass


def rendi_azionabile(etichetta, comando, sfondo=None, colore_focus=None):
    """Una Label che si comporta da comando anche senza mouse (H2).

    Restano Label per ragioni grafiche — sono i collegamenti del banner
    d'aiuto, dentro un riquadro colorato, e un `ttk.Button` lì stonerebbe. Ma
    una cosa che si può solo cliccare non è raggiungibile: qui prende il
    focus con Tab, si attiva con Invio o Spazio, e il focus si vede perché il
    bordo cambia colore.
    """
    sfondo = sfondo or etichetta.cget("background")
    colore_focus = colore_focus or etichetta.cget("foreground")
    etichetta.configure(takefocus=True, highlightthickness=1,
                        highlightbackground=sfondo, highlightcolor=colore_focus)
    for sequenza in ("<Button-1>", "<Return>", "<KP_Enter>", "<space>"):
        etichetta.bind(sequenza, lambda _e, c=comando: (c(), "break")[1])
    return etichetta


def rendi_menu_apribile(menubutton):
    """Un menu a tendina raggiungibile e apribile da tastiera (H2).

    `tk.Menubutton` nasce con `takefocus 0`: Tab non lo raggiunge, e la sua
    associazione di classe per lo spazio non arriva mai a servire, perche' il
    widget non riceve mai il focus. Un menu di esportazione che si apre solo
    col mouse non e' un dettaglio: e' la via principale per portare fuori un
    risultato. Qui il pulsante entra nel giro di Tab e Invio, Spazio o Giu'
    aprono la tendina come farebbe un clic — dentro, i tasti sono quelli di
    Tk: frecce per scorrere, Invio per scegliere, Esc per chiudere.
    """
    menubutton.configure(takefocus=True)

    def apri(_evento=None):
        menu = str(menubutton.cget("menu") or "")
        if not menu or str(menubutton.cget("state")) == "disabled":
            return None
        try:
            menubutton.tk.call("tk::MbPost", str(menubutton))
            menubutton.tk.call("tk::MenuFirstEntry", menu)
        except tk.TclError:
            return None
        return "break"

    for sequenza in ("<Return>", "<KP_Enter>", "<space>", "<Down>"):
        menubutton.bind(sequenza, apri)
    return menubutton


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
        return f"  -  ~{fmt_duration(remaining)} {tr('common.remaining')}"
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
