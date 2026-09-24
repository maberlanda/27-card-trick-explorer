"""Un'area che scorre quando il contenuto non ci sta, e non scorre quando ci sta.

Compartimento H2. Le schede del programma sono dense: l'Explorer chiede 1392×1002
px, il Simulatore 1006×725. Finché la finestra è grande non si nota; a 1280×720
il contenuto finisce sotto il bordo e lì resta — misurato: nel Simulatore
sparivano «Conferma impilamento» e «Ricomincia», cioè le due azioni con cui si
porta avanti la pratica.

`AreaScorrevole` mette il contenuto dentro una tela e lo lascia scorrere quando
serve. Due regole, perché non diventi un fastidio:

* **le barre compaiono solo quando servono.** Se il contenuto ci sta, l'area si
  comporta come un frame qualunque e non c'è niente in più da guardare;
* **il contenuto si allarga.** La finestra interna viene tenuta grande almeno
  quanto la tela, così i pesi di `grid`/`pack` dentro la scheda continuano a
  distribuire lo spazio come prima: si scorre solo per la parte che eccede.

Si scorre anche senza mouse: la tela prende il focus con Tab e risponde a
frecce, PagSu/PagGiù, Inizio/Fine; le barre sono a loro volta raggiungibili con
Tab. La rotella è legata solo mentre il puntatore è dentro l'area, così due aree
annidate non si rubano lo scorrimento.

Costo: gli unici calcoli in `<Configure>` sono un `bbox` e due confronti. Le
barre vengono aggiunte o tolte solo quando la necessità cambia davvero, e una
guardia impedisce che quel cambiamento rientri su se stesso — il ciclo classico
«aggiungo la barra → resta meno spazio → tolgo la barra».
"""

import tkinter as tk
from tkinter import ttk

__all__ = ["AreaScorrevole"]


class AreaScorrevole(ttk.Frame):
    """Contenitore scorrevole. Il contenuto va messo dentro `.contenuto`."""

    #: Tolleranza in pixel: sotto questa differenza non si considera che il
    #: contenuto ecceda. Evita che un pixel di arrotondamento faccia comparire
    #: e sparire una barra a ogni ridisegno.
    TOLLERANZA = 2

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._tela = tk.Canvas(self, highlightthickness=0, bd=0, takefocus=True)
        self._tela.grid(row=0, column=0, sticky="nsew")
        self._vs = ttk.Scrollbar(self, orient="vertical",
                                 command=self._tela.yview, takefocus=True)
        self._hs = ttk.Scrollbar(self, orient="horizontal",
                                 command=self._tela.xview, takefocus=True)
        self._tela.configure(yscrollcommand=self._vs.set,
                             xscrollcommand=self._hs.set)

        self.contenuto = ttk.Frame(self._tela)
        self._finestra = self._tela.create_window(
            (0, 0), window=self.contenuto, anchor="nw")

        self._mostrate = (False, False)      # (verticale, orizzontale)
        self._in_aggiornamento = False

        self.contenuto.bind("<Configure>", self._aggiorna)
        self._tela.bind("<Configure>", self._aggiorna)
        self._lega_tastiera()
        self._lega_rotella()

    # ── tastiera ─────────────────────────────────────────────────────────────

    def _lega_tastiera(self):
        for bersaglio in (self._tela, self._vs, self._hs):
            bersaglio.bind("<Up>", lambda _e: self._scorri_y(-1))
            bersaglio.bind("<Down>", lambda _e: self._scorri_y(1))
            bersaglio.bind("<Prior>", lambda _e: self._pagina_y(-1))
            bersaglio.bind("<Next>", lambda _e: self._pagina_y(1))
            bersaglio.bind("<Home>", lambda _e: self._tela.yview_moveto(0))
            bersaglio.bind("<End>", lambda _e: self._tela.yview_moveto(1))
            bersaglio.bind("<Left>", lambda _e: self._scorri_x(-1))
            bersaglio.bind("<Right>", lambda _e: self._scorri_x(1))

    def _scorri_y(self, verso):
        self._tela.yview_scroll(verso, "units")
        return "break"

    def _pagina_y(self, verso):
        self._tela.yview_scroll(verso, "pages")
        return "break"

    def _scorri_x(self, verso):
        self._tela.xview_scroll(verso, "units")
        return "break"

    # ── rotella, solo mentre il puntatore è dentro ───────────────────────────

    def _lega_rotella(self):
        self.bind("<Enter>", self._accendi_rotella)
        self.bind("<Leave>", self._spegni_rotella)
        self.bind("<Destroy>", self._spegni_rotella)

    def _accendi_rotella(self, _evento=None):
        self._tela.bind_all("<MouseWheel>", self._rotella, add="+")
        self._tela.bind_all("<Button-4>", self._rotella, add="+")
        self._tela.bind_all("<Button-5>", self._rotella, add="+")

    def _spegni_rotella(self, _evento=None):
        for sequenza in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                self._tela.unbind_all(sequenza)
            except tk.TclError:
                pass

    def _rotella(self, evento):
        if not self._mostrate[0]:
            return
        if getattr(evento, "num", None) == 4:
            passi = -1
        elif getattr(evento, "num", None) == 5:
            passi = 1
        else:
            passi = -1 if getattr(evento, "delta", 0) > 0 else 1
        self._tela.yview_scroll(passi, "units")

    # ── disposizione ─────────────────────────────────────────────────────────

    def _aggiorna(self, _evento=None):
        if self._in_aggiornamento:
            return
        self._in_aggiornamento = True
        try:
            self._ridisegna()
        finally:
            self._in_aggiornamento = False

    def _ridisegna(self):
        try:
            larghezza_tela = self._tela.winfo_width()
            altezza_tela = self._tela.winfo_height()
        except tk.TclError:
            return
        if larghezza_tela <= 1 or altezza_tela <= 1:
            return

        larghezza_contenuto = self.contenuto.winfo_reqwidth()
        altezza_contenuto = self.contenuto.winfo_reqheight()

        # Il contenuto non è mai più piccolo della tela: così i pesi interni
        # della scheda continuano a distribuire lo spazio come prima, e si
        # scorre soltanto per la parte che eccede.
        self._tela.itemconfigure(
            self._finestra,
            width=max(larghezza_contenuto, larghezza_tela),
            height=max(altezza_contenuto, altezza_tela))
        self._tela.configure(scrollregion=(
            0, 0, max(larghezza_contenuto, larghezza_tela),
            max(altezza_contenuto, altezza_tela)))

        serve_v = altezza_contenuto > altezza_tela + self.TOLLERANZA
        serve_h = larghezza_contenuto > larghezza_tela + self.TOLLERANZA
        self._mostra_barre(serve_v, serve_h)

    def _mostra_barre(self, verticale, orizzontale):
        if (verticale, orizzontale) == self._mostrate:
            return
        self._mostrate = (verticale, orizzontale)
        if verticale:
            self._vs.grid(row=0, column=1, sticky="ns")
        else:
            self._vs.grid_remove()
        if orizzontale:
            self._hs.grid(row=1, column=0, sticky="ew")
        else:
            self._hs.grid_remove()

    def ricalcola(self):
        """Rivaluta le barre dopo un cambio di contenuto (I2).

        Quando il contenuto si *restringe* dentro una finestra che la tela
        tiene gia' larga almeno quanto se stessa, Tk non genera un nuovo
        `<Configure>`: chi aggiorna il contenuto lo chiede qui, esplicitamente.
        """
        self._aggiorna()

    # ── per i test ───────────────────────────────────────────────────────────

    @property
    def tela(self):
        return self._tela

    def barre_visibili(self):
        """`(verticale, orizzontale)`: quali barre sono in uso adesso."""
        return self._mostrate

    def puo_scorrere(self):
        """True se una delle due direzioni ha qualcosa da scorrere."""
        return any(self._mostrate)
