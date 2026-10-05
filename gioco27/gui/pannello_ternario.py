"""Pannello ternario della Tavola (compartimento I2).

Tre schede interne — «Tabellone», «Una carta», «27 posizioni» — alimentate
dal presenter `services.tabellone`. La vista non calcola nulla: legge i dati
strutturati (cronologia, righe della griglia, colonne-Assi, T e T⁻¹, flusso
delle cifre) e li rende in etichette e testo, con le frasi del catalogo i18n.

Contratti (docs/decisions/V4_PRE_I2_VIEW_DECISIONS.md, D-I2-2/3/5/6/8):

* cronologia (fase 1 → 2 → 3) e griglia (fase 3 in alto) sono mostrate
  **insieme**, con le etichette «fase · peso · cifra» su ogni riga;
* T («destinazione di ogni carta») e T⁻¹ («carta in ogni posizione / mazzo
  finale») hanno sempre il loro nome;
* ogni resa ha un'alternativa testuale di sola lettura raggiungibile con Tab;
* lo stato evidenziato porta il marcatore «▶», non solo un colore;
* nessun Canvas.
"""
import tkinter as tk
from tkinter import ttk

from ..services import tabellone as _tb
from ..services.procedure import ProceduraGioco
from .i18n import tr
from .scorrimento import AreaScorrevole

__all__ = ["PannelloTernario"]

MARCATORE = "▶"
_LARGHEZZA_TESTO = 340          # a capo delle etichette lunghe (px)


def _testo_sola_lettura(parent, altezza):
    """Alternativa testuale H2: sola lettura, ma raggiungibile con Tab."""
    testo = tk.Text(parent, height=altezza, width=44, wrap="word", relief="flat",
                    font=("Consolas", 9), background="#FAFCFF",
                    foreground="#1F4E79", takefocus=True)
    testo.configure(state="disabled")
    return testo


def _scrivi(testo, contenuto):
    testo.configure(state="normal")
    testo.delete("1.0", "end")
    testo.insert("1.0", contenuto)
    testo.configure(state="disabled")


def _cella(testo, evidenziata):
    return f"{MARCATORE}{testo}" if evidenziata else f" {testo} "


class PannelloTernario(ttk.Frame):
    """Il pannello a destra della Tavola. `mostra_disposizione(n)` lo aggiorna."""

    def __init__(self, parent, on_vai_alla_riga=None, **kw):
        super().__init__(parent, **kw)
        self._on_vai_alla_riga = on_vai_alla_riga
        self._numero = None
        self._tabellone = None
        self._celle_evidenziate = ()
        self._carta = 0
        self._passo = 0
        self._flusso = None
        self._stile()
        self._schede = ttk.Notebook(self)
        self._schede.pack(fill="both", expand=True)
        self._area_tabellone = AreaScorrevole(self._schede)
        self._schede.add(self._area_tabellone, text=tr("ternary.tab.board"))
        self._costruisci_tabellone(self._area_tabellone.contenuto)
        self._area_carta = AreaScorrevole(self._schede)
        self._schede.add(self._area_carta, text=tr("ternary.tab.card"))
        self._costruisci_carta(self._area_carta.contenuto)
        self._area_posizioni = AreaScorrevole(self._schede)
        self._schede.add(self._area_posizioni, text=tr("ternary.tab.positions"))
        self._costruisci_posizioni(self._area_posizioni.contenuto)
        # Le tre schede scorrono da sole: la loro richiesta minima resta piccola,
        # cosi' il pannello non costringe l'intera Tavola a scorrere (H2).
        for area in (self._area_tabellone, self._area_carta,
                     self._area_posizioni):
            area.tela.configure(width=360, height=220)
        self._mostra_vuoto()

    # ── stato pubblico ───────────────────────────────────────────────────────
    @property
    def numero(self):
        """# della disposizione mostrata, o None prima della prima selezione."""
        return self._numero

    @property
    def tabellone_corrente(self):
        return self._tabellone

    @property
    def carta(self):
        return self._carta

    @property
    def passo(self):
        """Passo del flusso mostrato: 0 = prima della fase 1, 3 = fine."""
        return self._passo

    def _stile(self):
        stile = ttk.Style(self)
        stile.configure("Cella.TLabel", font=("Consolas", 12, "bold"),
                        anchor="center", padding=(6, 2), relief="groove")
        stile.configure("CellaEvid.TLabel", font=("Consolas", 12, "bold"),
                        anchor="center", padding=(6, 2), relief="groove",
                        background="#fff2c4")
        stile.configure("Fase.TLabel", padding=(3, 1), relief="ridge",
                        font=("Segoe UI", 8),
                        justify="center", anchor="center")

    # ── scheda «Tabellone» ───────────────────────────────────────────────────
    def _costruisci_tabellone(self, dentro):
        dentro.columnconfigure(0, weight=1)
        riga = 0
        self._titolo = ttk.Label(dentro, font=("Segoe UI", 11, "bold"),
                                 foreground="#1F4E79",
                                 wraplength=_LARGHEZZA_TESTO)
        self._titolo.grid(row=riga, column=0, sticky="w", padx=6, pady=(6, 2))
        riga += 1

        ttk.Label(dentro, text=tr("ternary.board.chronology"),
                  foreground="#555").grid(row=riga, column=0, sticky="w", padx=6)
        riga += 1
        striscia = ttk.Frame(dentro)
        striscia.grid(row=riga, column=0, sticky="w", padx=6, pady=(0, 6))
        self._fasi = []
        for i in range(3):
            if i:
                ttk.Label(striscia, text="→").pack(side="left", padx=1)
            lbl = ttk.Label(striscia, style="Fase.TLabel")
            lbl.pack(side="left")
            self._fasi.append(lbl)
        riga += 1

        self._titolo_diretto, self._etichette_righe, self._celle, \
            self._piede_diretto, riga = self._griglia(dentro, riga)
        self._titolo_inverso, self._etichette_inverse, self._celle_inverse, \
            self._piede_inverso, riga = self._griglia(dentro, riga)

        self._autoinversa = ttk.Label(dentro, wraplength=_LARGHEZZA_TESTO)
        self._autoinversa.grid(row=riga, column=0, sticky="w", padx=6, pady=(2, 6))
        riga += 1
        self._realizza = ttk.Label(dentro, wraplength=_LARGHEZZA_TESTO)
        self._realizza.grid(row=riga, column=0, sticky="w", padx=6)
        riga += 1
        self._ritorno = ttk.Label(dentro, wraplength=_LARGHEZZA_TESTO)
        self._ritorno.grid(row=riga, column=0, sticky="w", padx=6, pady=(2, 0))
        riga += 1
        self._vai_ritorno = ttk.Button(dentro, command=self._vai_al_ritorno,
                                       state="disabled")
        self._vai_ritorno.grid(row=riga, column=0, sticky="w", padx=6, pady=4)
        riga += 1
        ttk.Label(dentro, text=tr("ternary.text.heading"),
                  foreground="#555").grid(row=riga, column=0, sticky="w", padx=6)
        riga += 1
        self._testo_tabellone = _testo_sola_lettura(dentro, 12)
        self._testo_tabellone.grid(row=riga, column=0, sticky="nsew", padx=6,
                                   pady=(0, 6))
        dentro.rowconfigure(riga, weight=1)

    def _griglia(self, dentro, riga):
        titolo = ttk.Label(dentro, font=("Segoe UI", 9, "bold"),
                           wraplength=_LARGHEZZA_TESTO)
        titolo.grid(row=riga, column=0, sticky="w", padx=6)
        riga += 1
        quadro = ttk.Frame(dentro)
        quadro.grid(row=riga, column=0, sticky="w", padx=6)
        for d, lettera in enumerate("SCD"):
            ttk.Label(quadro, text=f"{d} / {lettera}", foreground="#555",
                      anchor="center").grid(row=0, column=d + 1, padx=2)
        etichette, celle = [], []
        for r in range(3):
            lbl = ttk.Label(quadro, foreground="#1F4E79")
            lbl.grid(row=r + 1, column=0, sticky="e", padx=(0, 6))
            etichette.append(lbl)
            riga_celle = []
            for d in range(3):
                c = ttk.Label(quadro, style="Cella.TLabel", width=3)
                c.grid(row=r + 1, column=d + 1, padx=2, pady=1)
                riga_celle.append(c)
            celle.append(riga_celle)
        riga += 1
        piede = ttk.Label(dentro, wraplength=_LARGHEZZA_TESTO, foreground="#555")
        piede.grid(row=riga, column=0, sticky="w", padx=6, pady=(2, 8))
        riga += 1
        return titolo, etichette, celle, piede, riga

    # ── aggiornamento ────────────────────────────────────────────────────────
    def _mostra_vuoto(self):
        self._titolo.configure(text=tr("ternary.none"))
        _scrivi(self._testo_tabellone, tr("ternary.none"))
        _scrivi(self._testo_carta, tr("ternary.none"))
        self._dettaglio_posizione.configure(text=tr("ternary.none"))
        for b in (self._btn_inizio, self._btn_indietro, self._btn_avanti,
                  self._vai_realizzata):
            b.state(["disabled"])

    def reset(self):
        self._numero = self._tabellone = self._flusso = None
        self._celle_evidenziate = ()
        self._carta = self._passo = 0
        self._carta_var.set("0")
        for var in self._eps_vars:
            var.set(False)
        self._tabella.delete(*self._tabella.get_children())
        for nome in ("_titolo_diretto", "_titolo_inverso", "_piede_diretto",
                     "_piede_inverso", "_autoinversa", "_realizza", "_ritorno",
                     "_indirizzo", "_registro", "_dettaglio_passo", "_etichetta_passo",
                     "_storia_distribuzioni", "_storia_raccolte", "_lettura", "_realizzata"):
            getattr(self, nome).configure(text="")
        for lbl in self._fasi:
            lbl.configure(text="")
        for lbl in (*self._etichette_righe, *self._etichette_inverse):
            lbl.configure(text="")
        for griglia in (self._celle, self._celle_inverse):
            for riga in griglia:
                for lbl in riga:
                    lbl.configure(text="", style="Cella.TLabel")
        self._vai_ritorno.state(["disabled"])
        self._mostra_vuoto()

    def mostra_disposizione(self, numero):
        """Mostra la disposizione `numero` (0..215) in tutte le schede.

        La carta e i rovesciamenti scelti restano; il flusso riparte dal passo 0.
        """
        t = _tb.tabellone(numero)
        self._numero, self._tabellone = t.numero, t
        self._celle_evidenziate = ()
        self._aggiorna_tabellone()
        self._riempi_posizioni()
        self._passo = 0
        self._aggiorna_carta()
        self._ricalcola_aree()

    def _ricalcola_aree(self):
        """Le tre aree rivalutano le barre: il contenuto puo' essersi ristretto."""
        self.update_idletasks()
        for area in (self._area_tabellone, self._area_carta,
                     self._area_posizioni):
            area.ricalcola()

    def _aggiorna_tabellone(self):
        t = self._tabellone
        self._titolo.configure(text=tr("ternary.board.title", number=t.numero))
        for lbl, f in zip(self._fasi, t.cronologia):
            lbl.configure(text=tr("ternary.board.phase_cell", phase=f.fase,
                                  shuffle=f.mescolamento, stacking=f.impilamento))
        self._titolo_diretto.configure(text=(
            f"{tr('ternary.board.direct_title')} · "
            f"{tr('ternary.board.direct_reading')}"))
        self._titolo_inverso.configure(text=(
            f"{tr('ternary.board.inverse_title')} · "
            f"{tr('ternary.board.inverse_reading')}"))
        self._riempi_griglia(t.righe, self._etichette_righe, self._celle,
                             self._celle_evidenziate)
        self._riempi_griglia(t.righe_inverse, self._etichette_inverse,
                             self._celle_inverse, ())
        spades, clubs, hearts = (c.posizione for c in t.colonne_assi)
        self._piede_diretto.configure(text=tr(
            "ternary.board.aces_direct", spades=spades, clubs=clubs,
            hearts=hearts))
        first, middle, last = (c.carta for c in t.colonne_inverse)
        self._piede_inverso.configure(text=tr(
            "ternary.board.aces_inverse", first=first, middle=middle, last=last))
        self._autoinversa.configure(text=tr(
            "ternary.board.self_inverse" if t.autoinversa
            else "ternary.board.not_self_inverse"))
        self._realizza.configure(text=tr(
            "ternary.board.realize",
            shuffles=" ".join(f.mescolamento for f in t.cronologia),
            stackings=" ".join(f.impilamento for f in t.cronologia)))
        ritorno = _tb.ritorno(t.numero)
        self._numero_ritorno = ritorno.numero_tavola
        self._ritorno.configure(text=tr(
            "ternary.board.return", number=ritorno.numero_tavola,
            shuffles=" ".join(ritorno.mescolamenti)))
        self._vai_ritorno.configure(
            text=tr("ternary.board.goto", number=ritorno.numero_tavola),
            state="normal" if self._on_vai_alla_riga else "disabled")
        _scrivi(self._testo_tabellone, self._tabellone_in_testo())

    def _riempi_griglia(self, righe, etichette, celle, evidenziate):
        for rv, (r, lbl, riga_celle) in enumerate(zip(righe, etichette, celle)):
            lbl.configure(text=tr("ternary.board.row_label", phase=r.fase,
                                  weight=r.peso, digit=r.indice_cifra))
            for d, c in enumerate(riga_celle):
                evid = (rv, d) in evidenziate
                c.configure(text=_cella(r.sigla[d], evid),
                            style="CellaEvid.TLabel" if evid else "Cella.TLabel")

    def _tabellone_in_testo(self):
        """La stessa informazione della scheda, per intero, in parole (H2)."""
        t = self._tabellone
        righe = [tr("ternary.board.title", number=t.numero),
                 tr("ternary.board.chronology")]
        righe += [tr("ternary.board.phase_text", phase=f.fase,
                     shuffle=f.mescolamento, stacking=f.impilamento)
                  for f in t.cronologia]
        for titolo, lettura, dati, chiave in (
                ("ternary.board.direct_title", "ternary.board.direct_reading",
                 t.righe, "ternary.board.row_text"),
                ("ternary.board.inverse_title", "ternary.board.inverse_reading",
                 t.righe_inverse, "ternary.board.inverse_row_text")):
            righe.append("")
            righe.append(f"{tr(titolo)} · {tr(lettura)}")
            for r in dati:
                etichetta = tr("ternary.board.row_label", phase=r.fase,
                               weight=r.peso, digit=r.indice_cifra)
                righe.append(tr(chiave, label=etichetta, shuffle=r.sigla,
                                s=r.sigla[0], c=r.sigla[1], d=r.sigla[2]))
        righe.append("")
        righe.append(self._piede_diretto.cget("text"))
        righe.append(self._piede_inverso.cget("text"))
        righe.append(tr("ternary.board.values",
                        label=tr("ternary.board.direct_reading"),
                        values=", ".join(map(str, t.destinazioni))))
        righe.append(tr("ternary.board.values",
                        label=tr("ternary.board.inverse_reading"),
                        values=", ".join(map(str, t.mazzo_finale))))
        righe.append(self._autoinversa.cget("text"))
        righe.append(self._realizza.cget("text"))
        righe.append(self._ritorno.cget("text"))
        return "\n".join(righe)

    def evidenzia_celle(self, celle):
        """Marca con «▶» le celle (riga visiva, colonna) della lettura corrente."""
        self._celle_evidenziate = tuple(celle)
        if self._tabellone is not None:
            self._riempi_griglia(self._tabellone.righe, self._etichette_righe,
                                 self._celle, self._celle_evidenziate)

    # ── scheda «Una carta» ───────────────────────────────────────────────────
    def _costruisci_carta(self, dentro):
        dentro.columnconfigure(0, weight=1)
        riga = 0
        scelta = ttk.Frame(dentro)
        scelta.grid(row=riga, column=0, sticky="w", padx=6, pady=(6, 2))
        ttk.Label(scelta, text=tr("ternary.card.card")).pack(side="left")
        self._carta_var = tk.StringVar(value="0")
        self._spin_carta = ttk.Spinbox(scelta, from_=0, to=26, width=4,
                                       textvariable=self._carta_var,
                                       command=self._su_carta)
        self._spin_carta.pack(side="left", padx=4)
        self._spin_carta.bind("<Return>", self._su_carta)
        self._spin_carta.bind("<FocusOut>", self._su_carta)
        riga += 1

        rov = ttk.Frame(dentro)
        rov.grid(row=riga, column=0, sticky="w", padx=6)
        self._eps_vars, self._eps_check = [], []
        for fase in (1, 2, 3):
            v = tk.BooleanVar(value=False)
            c = ttk.Checkbutton(rov, text=tr("ternary.card.flip", phase=fase),
                                variable=v, command=self._su_rovesciamenti)
            c.pack(anchor="w")
            self._eps_vars.append(v)
            self._eps_check.append(c)
        riga += 1
        ttk.Label(dentro, text=tr("ternary.card.flips_note"), foreground="#555",
                  wraplength=_LARGHEZZA_TESTO).grid(row=riga, column=0,
                                                     sticky="w", padx=6)
        riga += 1

        passi = ttk.Frame(dentro)
        passi.grid(row=riga, column=0, sticky="w", padx=6, pady=4)
        self._btn_inizio = ttk.Button(passi, text=tr("ternary.card.start"),
                                      command=lambda: self._vai_al_passo(0))
        self._btn_indietro = ttk.Button(
            passi, text=tr("ternary.card.back"),
            command=lambda: self._vai_al_passo(self._passo - 1))
        self._btn_avanti = ttk.Button(
            passi, text=tr("ternary.card.forward"),
            command=lambda: self._vai_al_passo(self._passo + 1))
        for b in (self._btn_inizio, self._btn_indietro, self._btn_avanti):
            b.pack(side="left", padx=(0, 4))
        self._etichetta_passo = ttk.Label(passi)
        self._etichetta_passo.pack(side="left", padx=6)
        riga += 1

        def etichetta(**kw):
            nonlocal riga
            lbl = ttk.Label(dentro, wraplength=_LARGHEZZA_TESTO, justify="left",
                            **kw)
            lbl.grid(row=riga, column=0, sticky="w", padx=6, pady=1)
            riga += 1
            return lbl

        self._indirizzo = etichetta(font=("Segoe UI", 10, "bold"))
        self._registro = etichetta(font=("Consolas", 10), foreground="#1F4E79")
        self._dettaglio_passo = etichetta()
        etichetta(text=tr("ternary.card.law"), foreground="#555")
        self._storia_distribuzioni = etichetta()
        self._storia_raccolte = etichetta()
        self._lettura = etichetta()
        self._realizzata = etichetta()
        self._vai_realizzata = ttk.Button(dentro, command=self._vai_alla_realizzata)
        self._vai_realizzata.grid(row=riga, column=0, sticky="w", padx=6, pady=4)
        riga += 1
        ttk.Label(dentro, text=tr("ternary.text.heading"),
                  foreground="#555").grid(row=riga, column=0, sticky="w", padx=6)
        riga += 1
        self._testo_carta = _testo_sola_lettura(dentro, 12)
        self._testo_carta.grid(row=riga, column=0, sticky="nsew", padx=6,
                               pady=(0, 6))
        dentro.rowconfigure(riga, weight=1)

    def _procedura(self):
        """La procedura della riga selezionata con i rovesciamenti scelti (D-I2-5)."""
        return ProceduraGioco(
            tuple(f.mescolamento for f in self._tabellone.cronologia),
            tuple(bool(v.get()) for v in self._eps_vars))

    def imposta_carta(self, carta):
        """Sceglie la carta seguita (0..26): il flusso riparte dal passo 0."""
        carta = int(carta)
        if not 0 <= carta <= 26:
            return
        self._carta = carta
        self._carta_var.set(str(carta))
        self._passo = 0
        self._aggiorna_carta()

    def _su_carta(self, _ev=None):
        try:
            carta = int(self._carta_var.get())
        except ValueError:
            self._carta_var.set(str(self._carta))
            return
        if carta != self._carta or _ev is None:
            self.imposta_carta(carta)

    def _su_rovesciamenti(self):
        self._passo = 0
        self._aggiorna_carta()

    def _vai_al_passo(self, passo):
        self._passo = max(0, min(3, passo))
        self._aggiorna_carta()

    def _aggiorna_carta(self):
        if self._numero is None:
            return
        procedura = self._procedura()
        f = _tb.flusso_carta(procedura, self._carta)
        self._flusso = f
        lettura = _tb.lettura_cifre(self._numero, self._carta)
        d2, d1, d0 = f.cifre_iniziali
        self._indirizzo.configure(text=tr(
            "ternary.card.address", position=f.carta, d2=d2, d1=d1, d0=d0,
            word=f.parola_iniziale))
        if self._passo == 0:
            pos, cifre, parola = f.carta, f.cifre_iniziali, f.parola_iniziale
            dettaglio = self._frase_iniziale(f)
        else:
            ps = f.passi[self._passo - 1]
            pos, cifre, parola = ps.posizione_dopo, ps.cifre_dopo, ps.parola_dopo
            dettaglio = "\n".join(self._frasi_passo(ps))
        self._registro.configure(text=tr(
            "ternary.card.register", d2=cifre[0], d1=cifre[1], d0=cifre[2],
            position=pos, word=parola))
        self._dettaglio_passo.configure(text=dettaglio)
        self._etichetta_passo.configure(text=tr("ternary.card.step",
                                                step=self._passo))
        self._btn_inizio.state(["!disabled"] if self._passo else ["disabled"])
        self._btn_indietro.state(["!disabled"] if self._passo else ["disabled"])
        self._btn_avanti.state(["!disabled"] if self._passo < 3 else ["disabled"])
        self._storia_distribuzioni.configure(text=self._frase_distribuzioni(f))
        self._storia_raccolte.configure(text=self._frase_raccolte(f))
        self._lettura.configure(text=self._frase_lettura(lettura))
        self.evidenzia_celle(lettura.celle)
        self._numero_realizzato = _tb.disposizione_realizzata(procedura)
        self._realizzata.configure(text=tr("ternary.card.realized",
                                           number=self._numero_realizzato))
        self._vai_realizzata.configure(text=tr("ternary.board.goto",
                                               number=self._numero_realizzato))
        self._vai_realizzata.state(["!disabled"] if self._on_vai_alla_riga
                                   else ["disabled"])
        _scrivi(self._testo_carta, self._carta_in_testo(f, lettura))

    # ── frasi (catalogo i18n; nessun calcolo) ────────────────────────────────
    @staticmethod
    def _frase_iniziale(f):
        d2, d1, d0 = f.cifre_iniziali
        return tr("ternary.card.initial", position=f.carta, d2=d2, d1=d1,
                  d0=d0, word=f.parola_iniziale)

    @staticmethod
    def _frasi_passo(ps):
        frasi = []
        if ps.rovesciamento:
            b2, b1, b0 = ps.cifre_prima
            a2, a1, a0 = ps.cifre_distribuite
            frasi.append(tr("ternary.card.flip_step", phase=ps.fase,
                            before=ps.posizione_prima, b2=b2, b1=b1, b0=b0,
                            after=ps.posizione_distribuita, a2=a2, a1=a1, a0=a0))
        a2, a1, a0 = ps.cifre_dopo
        frasi.append(tr("ternary.card.phase_step", phase=ps.fase,
                        position=ps.posizione_distribuita, column=ps.colonna,
                        letter=ps.lettera_colonna, height=ps.altezza,
                        shuffle=ps.mescolamento, block=ps.destinazione_blocco,
                        after=ps.posizione_dopo, a2=a2, a1=a1, a0=a0,
                        word=ps.parola_dopo, out=ps.cifra_uscente,
                        into=ps.cifra_entrante))
        return frasi

    @staticmethod
    def _frase_distribuzioni(f):
        colonne = ", ".join(f"{ps.colonna} ({ps.lettera_colonna})"
                            for ps in f.passi)
        frasi = [tr("ternary.card.distributions", columns=colonne)]
        complementate = [str(ps.fase) for ps in f.passi if ps.complementata]
        if any(f.procedura.rovesciamenti):
            frasi.append(tr("ternary.card.distributions_flip",
                            phases=", ".join(complementate)))
        else:
            n0, n1, n2 = f.cifre_origine_nel_tempo
            frasi.append(tr("ternary.card.distributions_rev", position=f.carta,
                            n0=n0, n1=n1, n2=n2))
        return "\n".join(frasi)

    @staticmethod
    def _frase_raccolte(f):
        s0, s1, s2 = f.storia_raccolte
        return tr("ternary.card.collections", s0=s0, s1=s1, s2=s2,
                  position=f.posizione_finale)

    @staticmethod
    def _frasi_azioni(lettura):
        return [tr("ternary.card.action", phase=a.fase, weight=a.peso,
                   digit=a.indice_cifra, before=a.cifra_iniziale,
                   after=a.cifra_finale, shuffle=a.sigla)
                for a in lettura.azioni]

    def _frase_lettura(self, lettura):
        d2, d1, d0 = lettura.cifre_iniziali
        b2, b1, b0 = lettura.cifre_finali
        testa = tr("ternary.card.reading", number=lettura.numero, d2=d2, d1=d1,
                   d0=d0, b2=b2, b1=b1, b0=b0, position=lettura.destinazione,
                   word=lettura.parola_finale)
        return "\n".join([testa] + self._frasi_azioni(lettura))

    def _carta_in_testo(self, f, lettura):
        """Tutti i passi del flusso, qualunque sia il passo mostrato (H2)."""
        d2, d1, d0 = f.cifre_iniziali
        righe = [tr("ternary.card.address", position=f.carta, d2=d2, d1=d1,
                    d0=d0, word=f.parola_iniziale)]
        if any(f.procedura.rovesciamenti):
            righe.append(tr("ternary.card.flips_note"))
        righe += [tr("ternary.card.law"), self._frase_iniziale(f)]
        for ps in f.passi:
            righe += self._frasi_passo(ps)
        c2, c1, c0 = f.cifre_finali
        righe.append(tr("ternary.card.final", position=f.posizione_finale,
                        d2=c2, d1=c1, d0=c0, word=f.parola_finale))
        righe += [self._frase_distribuzioni(f), self._frase_raccolte(f),
                  self._frase_lettura(lettura),
                  tr("ternary.card.realized", number=self._numero_realizzato)]
        return "\n".join(righe)

    # ── scheda «27 posizioni» ────────────────────────────────────────────────
    _COLONNE = (("n", "ternary.pos.col.n", 32),
                ("terna", "ternary.pos.col.digits", 56),
                ("parola", "ternary.pos.col.word", 56),
                ("terna_finale", "ternary.pos.col.final_digits", 56),
                ("parola_finale", "ternary.pos.col.final_word", 56),
                ("dest", "ternary.pos.col.dest", 36))

    def _costruisci_posizioni(self, dentro):
        dentro.columnconfigure(0, weight=1)
        ttk.Label(dentro, text=tr("ternary.pos.hint"), foreground="#555",
                  wraplength=_LARGHEZZA_TESTO).grid(row=0, column=0,
                                                     columnspan=2, sticky="w",
                                                     padx=6, pady=(6, 2))
        tab = ttk.Treeview(dentro, columns=[c for c, _, _ in self._COLONNE],
                           show="tree headings", selectmode="browse", height=12)
        tab.heading("#0", text="")
        tab.column("#0", width=128, stretch=False)
        for c, chiave, w in self._COLONNE:
            tab.heading(c, text=tr(chiave))
            tab.column(c, width=w, anchor="center", stretch=False)
        vs = ttk.Scrollbar(dentro, orient="vertical", command=tab.yview)
        hs = ttk.Scrollbar(dentro, orient="horizontal", command=tab.xview)
        tab.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tab.grid(row=1, column=0, sticky="nsew", padx=(6, 0))
        vs.grid(row=1, column=1, sticky="ns")
        hs.grid(row=2, column=0, sticky="ew", padx=(6, 0))
        dentro.rowconfigure(1, weight=1)
        tab.bind("<<TreeviewSelect>>", self._su_posizione)
        self._tabella = tab
        self._dettaglio_posizione = ttk.Label(dentro, wraplength=_LARGHEZZA_TESTO,
                                              justify="left")
        self._dettaglio_posizione.grid(row=3, column=0, columnspan=2, sticky="w",
                                       padx=6, pady=6)

    def _riempi_posizioni(self):
        tab = self._tabella
        tab.delete(*tab.get_children(""))
        righe = _tb.tabella_posizioni(self._numero)
        for blocco in range(3):
            prima = righe[9 * blocco]
            gid = f"blocco{blocco}"
            tab.insert("", "end", iid=gid, open=True, text=tr(
                "ternary.pos.group", digit=blocco,
                letter=prima.parola_iniziale[0], first=9 * blocco,
                last=9 * blocco + 8))
            for r in righe[9 * blocco: 9 * blocco + 9]:
                tab.insert(gid, "end", iid=f"pos{r.carta}", values=(
                    r.carta, "({},{},{})".format(*r.cifre_iniziali),
                    r.parola_iniziale, "({},{},{})".format(*r.cifre_finali),
                    r.parola_finale, r.destinazione))
        self._dettaglio_posizione.configure(text=tr("ternary.pos.hint"))

    def _su_posizione(self, _ev=None):
        sel = self._tabella.selection()
        if not sel or not sel[0].startswith("pos") or self._numero is None:
            return
        carta = int(sel[0][3:])
        lettura = _tb.lettura_cifre(self._numero, carta)
        testa = tr("ternary.pos.detail_heading", position=carta,
                   word=lettura.parola_iniziale,
                   destination=lettura.destinazione,
                   final_word=lettura.parola_finale)
        self._dettaglio_posizione.configure(
            text="\n".join([testa] + self._frasi_azioni(lettura)))
        if carta != self._carta:
            self.imposta_carta(carta)
        else:
            self.evidenzia_celle(lettura.celle)

    # ── azioni ───────────────────────────────────────────────────────────────
    def _vai_al_ritorno(self):
        if self._on_vai_alla_riga and self._tabellone is not None:
            self._on_vai_alla_riga(self._numero_ritorno)

    def _vai_alla_realizzata(self):
        if self._on_vai_alla_riga and self._flusso is not None:
            self._on_vai_alla_riga(self._numero_realizzato)
