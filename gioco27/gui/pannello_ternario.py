"""Pannello ternario della Tavola (compartimento I2).

Tre schede interne — «Tabellone», «Una carta», «27 posizioni» — alimentate
dal presenter `services.tabellone`. La vista non calcola nulla: legge i dati
strutturati (cronologia, righe della griglia, colonne-Assi, T e T⁻¹, flusso
delle cifre) e li rende in etichette e testo, con le frasi del catalogo i18n.

Contratti (V4_PRE_I2_VIEW_DECISIONS.md, D-I2-2/3/5/6/8):

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
from .i18n import tr
from .scorrimento import AreaScorrevole

__all__ = ["PannelloTernario"]

MARCATORE = "▶"
_LARGHEZZA_TESTO = 380          # a capo delle etichette lunghe (px)


def _testo_sola_lettura(parent, altezza):
    """Alternativa testuale H2: sola lettura, ma raggiungibile con Tab."""
    testo = tk.Text(parent, height=altezza, wrap="word", relief="flat",
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
        self._stile()
        self._schede = ttk.Notebook(self)
        self._schede.pack(fill="both", expand=True)
        self._area_tabellone = AreaScorrevole(self._schede)
        self._schede.add(self._area_tabellone, text=tr("ternary.tab.board"))
        self._costruisci_tabellone(self._area_tabellone.contenuto)
        self._area_carta = AreaScorrevole(self._schede)
        self._schede.add(self._area_carta, text=tr("ternary.tab.card"))
        self._area_posizioni = AreaScorrevole(self._schede)
        self._schede.add(self._area_posizioni, text=tr("ternary.tab.positions"))
        self._mostra_vuoto()

    # ── stato pubblico ───────────────────────────────────────────────────────
    @property
    def numero(self):
        """# della disposizione mostrata, o None prima della prima selezione."""
        return self._numero

    @property
    def tabellone_corrente(self):
        return self._tabellone

    def _stile(self):
        stile = ttk.Style(self)
        stile.configure("Cella.TLabel", font=("Consolas", 12, "bold"),
                        anchor="center", padding=(6, 2), relief="groove")
        stile.configure("CellaEvid.TLabel", font=("Consolas", 12, "bold"),
                        anchor="center", padding=(6, 2), relief="groove",
                        background="#fff2c4")
        stile.configure("Fase.TLabel", padding=(6, 2), relief="ridge",
                        justify="center", anchor="center")

    # ── scheda «Tabellone» ───────────────────────────────────────────────────
    def _costruisci_tabellone(self, dentro):
        dentro.columnconfigure(0, weight=1)
        riga = 0
        self._titolo = ttk.Label(dentro, font=("Segoe UI", 11, "bold"),
                                 foreground="#1F4E79")
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
                ttk.Label(striscia, text="→").pack(side="left", padx=2)
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

    def mostra_disposizione(self, numero):
        """Mostra la disposizione `numero` (0..215) in tutte le schede."""
        t = _tb.tabellone(numero)
        self._numero, self._tabellone = t.numero, t
        self._celle_evidenziate = ()
        self._aggiorna_tabellone()

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

    # ── azioni ───────────────────────────────────────────────────────────────
    def _vai_al_ritorno(self):
        if self._on_vai_alla_riga and self._tabellone is not None:
            self._on_vai_alla_riga(self._numero_ritorno)
