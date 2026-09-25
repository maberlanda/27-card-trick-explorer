"""Barre di azioni che vanno a capo invece di uscire dalla finestra.

Compartimento H2. Le barre in cima alla finestra erano righe di widget
impacchettati con `pack(side="left")` e `pack(side="right")`. Finché lo spazio
basta, il risultato è quello voluto; quando finisce, `pack` non taglia e non
scorre: **smette di mostrare** i widget che non ci stanno più, a partire da
quelli impacchettati per ultimi. Misurato sull'applicazione vera: a 1280×720
sparivano cinque pulsanti — Verifica, Presentazione, Protocollo, Cayley,
Coniugio — e a 1366×768 quattro. Non tagliati a metà: assenti, e senza alcun
modo di arrivarci.

`BarraAdattiva` tiene gli stessi widget, nello stesso ordine e con le stesse
funzioni, ma li dispone su più righe quando la larghezza non basta. Nessun
pulsante scompare, nessuna coordinata è fissa, e non c'è nessun menu a
scomparsa: cambia solo quante righe occupa la barra.

    ┌────────────────────────────────────────────────────────────────┐
    │ Conta  Genera…  Reset │ Principiante │ 1 728        Esci  ⚙  ✔ │   largo
    └────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────┐
    │ Conta  Genera…  Reset │ Princip… │                                 stretto
    │ 1 728   Coniugio  Cayley  │ …    │
    │ Verifica  Impostazioni  Esci     │
    └──────────────────────────────────┘

Costo del ridisegno: la disposizione viene ricalcolata solo quando il
risultato cambia davvero. Un `<Configure>` che non cambia il numero di righe
non tocca nessun widget, quindi non esiste il ciclo
configure → geometry → configure, e il ridimensionamento resta leggero (non
c'è nessun calcolo che non sia una somma di larghezze già note).
"""
from tkinter import ttk

__all__ = ["BarraAdattiva"]


class BarraAdattiva(ttk.Frame):
    """Una riga di azioni che diventa più righe quando la finestra si stringe.

    Uso::

        barra = BarraAdattiva(genitore, padding=(10, 8))
        barra.pack(fill="x")
        barra.aggiungi(ttk.Button(barra, text="Conta"))
        barra.separatore()
        barra.aggiungi(ttk.Button(barra, text="Esci"), a_destra=True)

    I widget vanno creati con la barra come genitore. Quelli marcati
    `a_destra` restano allineati a destra **finché tutto sta su una riga**:
    quando si va a capo l'allineamento a destra perderebbe l'ordine di
    lettura, e conta di più che le azioni restino in fila.
    """

    def __init__(self, parent, padding=(10, 8), **kw):
        super().__init__(parent, padding=padding, **kw)
        self._voci = []                  # [(widget, padx, a_destra)]
        self._nascosti = set()           # I7: widget esclusi dal livello
        self._elastici = set()           # widget che possono restringersi
        self._disposizione = None        # l'ultima calcolata, per non rifarla
        self._orizzontale = self._padding_orizzontale(padding)
        self.bind("<Configure>", self._su_configure)

    # ── costruzione ──────────────────────────────────────────────────────────

    @staticmethod
    def _padding_orizzontale(padding):
        if isinstance(padding, (tuple, list)) and padding:
            return 2 * int(padding[0])
        try:
            return 2 * int(padding)
        except (TypeError, ValueError):
            return 0

    #: Larghezza minima riservata a un widget elastico quando si decide se la
    #: riga è piena: il resto se lo prende se avanza, e lo cede se manca.
    MINIMO_ELASTICO = 40

    def aggiungi(self, widget, padx=4, a_destra=False, elastico=False):
        """Aggiunge un widget in coda. Restituisce il widget, per comodità.

        `elastico=True` segnala un widget che può restringersi — la riga di
        stato — e che quindi non deve far andare a capo la barra: nel calcolo
        pesa `MINIMO_ELASTICO` invece della sua larghezza naturale, e in
        griglia prende lo spazio che avanza.
        """
        self._voci.append((widget, padx, a_destra))
        self._elastici.add(str(widget))
        if not elastico:
            self._elastici.discard(str(widget))
        self._disposizione = None
        return widget

    def separatore(self, padx=10, a_destra=False):
        """Un separatore verticale, come quelli della barra originale."""
        return self.aggiungi(ttk.Separator(self, orient="vertical"),
                             padx=padx, a_destra=a_destra)

    def elastico(self, a_destra=False):
        """Uno spazio che si allarga: tiene a destra ciò che viene dopo."""
        vuoto = ttk.Frame(self)
        self._voci.append((vuoto, 0, a_destra))
        self._elastico = vuoto
        self._disposizione = None
        return vuoto

    def mostra(self, widget, visibile=True):
        """I7 (DP7): include o esclude una voce senza distruggerla.

        Una voce nascosta non occupa spazio e non conta nel calcolo delle
        righe; tornando visibile riprende il suo posto nell'ordine originale.
        """
        chiave = str(widget)
        prima = chiave in self._nascosti
        if visibile:
            self._nascosti.discard(chiave)
        else:
            self._nascosti.add(chiave)
        if prima != (chiave in self._nascosti):
            self._disposizione = None
            if not visibile:
                widget.grid_forget()
            self._su_configure()

    def _visibili(self):
        return [v for v in self._voci if str(v[0]) not in self._nascosti]

    # ── disposizione ─────────────────────────────────────────────────────────

    def _larghezza_utile(self):
        larghezza = self.winfo_width() - self._orizzontale
        return larghezza if larghezza > 1 else 0

    def _righe(self, larghezza):
        """Spezza le voci in righe, nell'ordine in cui sono state aggiunte."""
        righe, riga, usata = [], [], 0
        for voce in self._visibili():
            widget, padx, _ = voce
            naturale = (self.MINIMO_ELASTICO if str(widget) in self._elastici
                        else widget.winfo_reqwidth())
            costo = naturale + 2 * (padx if isinstance(padx, int) else sum(padx))
            if riga and usata + costo > larghezza:
                righe.append(riga)
                riga, usata = [], 0
            riga.append(voce)
            usata += costo
        if riga:
            righe.append(riga)
        return righe

    def _su_configure(self, _evento=None):
        larghezza = self._larghezza_utile()
        if not larghezza or not self._visibili():
            return
        righe = self._righe(larghezza)
        # Nessun widget viene toccato se la disposizione non è cambiata: è
        # questo che impedisce il ciclo configure → geometry → configure.
        firma = tuple(tuple(str(w) for w, _, _ in riga) for riga in righe)
        if firma == self._disposizione:
            return
        self._disposizione = firma
        self._disponi(righe)

    def _disponi(self, righe):
        for widget, _, _ in self._voci:
            widget.grid_forget()
        for colonna in range(self.grid_size()[0]):
            self.columnconfigure(colonna, weight=0, minsize=0)

        una_riga = len(righe) == 1
        for numero, riga in enumerate(righe):
            colonna = 0
            spazio_messo = False
            for widget, padx, a_destra in riga:
                if una_riga and a_destra and not spazio_messo:
                    # Su una riga sola il gruppo di destra resta a destra: fra
                    # i due gruppi si mette una colonna che si allarga.
                    self.columnconfigure(colonna, weight=1)
                    colonna += 1
                    spazio_messo = True
                if str(widget) in self._elastici:
                    # `minsize` perché una colonna elastica in una riga piena
                    # arriverebbe a zero, e Tk smette di mostrare un widget
                    # largo zero: la riga di stato sparirebbe proprio quando
                    # ha qualcosa da dire.
                    self.columnconfigure(colonna, weight=1,
                                         minsize=self.MINIMO_ELASTICO)
                    aggancio = "ew"
                elif isinstance(widget, ttk.Separator):
                    aggancio = "ns"
                else:
                    aggancio = "w"
                widget.grid(row=numero, column=colonna, padx=padx, pady=1,
                            sticky=aggancio)
                colonna += 1

    # ── per i test e per chi deve sapere com'è andata ────────────────────────

    def numero_di_righe(self):
        """Quante righe occupa la barra con la larghezza attuale."""
        larghezza = self._larghezza_utile()
        if not larghezza or not self._voci:
            return 0
        return len(self._righe(larghezza))

    def voci(self):
        """I widget nella barra, nell'ordine di lettura."""
        return [widget for widget, _, _ in self._voci]
