"""Vista «Spettatore (carta ignota)» del Simulatore — compartimento I4.

L'utente fa lo spettatore: pensa una carta e a ogni distribuzione indica
soltanto il mazzetto in cui la vede. Il programma non conosce la carta: la
raccolta viene da `services.spettatore.scelta_raccolta` (bersaglio, fase,
risposta). Due riquadri separati, anche nel testo:

* STATO FISICO — il mazzo, la distribuzione, le raccolte eseguite;
* STATO DELL'INFORMAZIONE — le posizioni iniziali ancora candidate.

Solo widget testuali e tabellari (H2): nessun Canvas.
"""

import random
import tkinter as tk
from tkinter import ttk

from ..core import gioco_reale as gr
from ..services import spettatore as sp
from .i18n import tr

MODO_NOTO = "noto"
MODO_B12 = "b12"
_ESEMPIO_B12 = ("DSC", "DSC", "CSD")          # libro § 7.2.13: disposizione #100


def _carta(c):
    return f"C{c:02d}"


def _elenco(posizioni):
    return " ".join(str(p) for p in sorted(posizioni))


class SpettatoreFrame(ttk.Frame):
    """Sessione di spettatore; `casuale` rende riproducibili i mazzi (test)."""

    def __init__(self, master, casuale=None, **kw):
        super().__init__(master, **kw)
        self._rnd = casuale or random.Random()
        self._sessione = None
        self._riavvolgimento = None
        self._facce = None           # carta in ciascuna posizione iniziale
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self._costruisci()
        self._aggiorna_controlli()
        self._mostra()

    def reset(self):
        self._sessione = self._riavvolgimento = self._facce = None
        self._modo_var.set(MODO_NOTO)
        self._bersaglio_var.set(13)
        self._mescolato_var.set(False)
        for var, sigla in zip(self._osservati_var, _ESEMPIO_B12):
            var.set(sigla)
        self._aggiorna_controlli()
        self._mostra()

    # ── costruzione ──────────────────────────────────────────────────────────
    def _costruisci(self):
        ttk.Label(self, text=tr("spectator.intro"), wraplength=880,
                  justify="left").grid(row=0, column=0, columnspan=2,
                                       sticky="w", padx=10, pady=(8, 4))

        ctrl = ttk.Frame(self)
        ctrl.grid(row=1, column=0, columnspan=2, sticky="w", padx=10)
        ttk.Label(ctrl, text=tr("spectator.order.label")).grid(
            row=0, column=0, sticky="w")
        self._modo_var = tk.StringVar(value=MODO_NOTO)
        self._modo_noto = ttk.Radiobutton(
            ctrl, text=tr("spectator.order.known"), variable=self._modo_var,
            value=MODO_NOTO, command=self._aggiorna_controlli)
        self._modo_b12 = ttk.Radiobutton(
            ctrl, text=tr("spectator.order.unknown"), variable=self._modo_var,
            value=MODO_B12, command=self._aggiorna_controlli)
        self._modo_noto.grid(row=0, column=1, sticky="w", padx=(6, 0))
        self._modo_b12.grid(row=0, column=2, sticky="w", padx=(6, 0))

        ttk.Label(ctrl, text=tr("spectator.target")).grid(
            row=1, column=0, sticky="w", pady=(4, 0))
        self._bersaglio_var = tk.IntVar(value=13)
        self._bersaglio_spin = ttk.Spinbox(ctrl, from_=0, to=26, width=4,
                                           textvariable=self._bersaglio_var)
        self._bersaglio_spin.grid(row=1, column=1, sticky="w", padx=(6, 0),
                                  pady=(4, 0))
        self._mescolato_var = tk.BooleanVar(value=False)
        self._mescolato_chk = ttk.Checkbutton(
            ctrl, text=tr("spectator.shuffled"), variable=self._mescolato_var)
        self._mescolato_chk.grid(row=1, column=2, sticky="w", padx=(6, 0),
                                 pady=(4, 0))

        self._osservati_fr = ttk.Frame(ctrl)
        self._osservati_fr.grid(row=2, column=0, columnspan=3, sticky="w",
                                pady=(4, 0))
        ttk.Label(self._osservati_fr, text=tr("spectator.b12.observed")).pack(
            side="left")
        self._osservati_var = [tk.StringVar(value=s) for s in _ESEMPIO_B12]
        self._osservati_cb = []
        for var in self._osservati_var:
            cb = ttk.Combobox(self._osservati_fr, textvariable=var,
                              values=list(gr.SIGLE), width=5, state="readonly")
            cb.pack(side="left", padx=(6, 0))
            self._osservati_cb.append(cb)

        self._avvia_btn = ttk.Button(ctrl, text=tr("spectator.start"),
                                     command=self.avvia)
        self._avvia_btn.grid(row=3, column=0, sticky="w", pady=(6, 0))

        # ── stato fisico ────────────────────────────────────────────────────
        fis = ttk.LabelFrame(self, text=f" {tr('spectator.physical.title')} ",
                             padding=(8, 4))
        fis.grid(row=2, column=0, sticky="nsew", padx=(10, 5), pady=8)
        fis.columnconfigure(0, weight=1)
        self._fase_lbl = ttk.Label(fis, text="", font=("Segoe UI", 10, "bold"))
        self._fase_lbl.grid(row=0, column=0, sticky="w")
        self._pile = ttk.Treeview(fis, columns=("S", "C", "D"), show="headings",
                                  height=9, selectmode="none")
        for g, col in enumerate(("S", "C", "D")):
            self._pile.heading(col, text=self._nome_mazzetto(g))
            self._pile.column(col, width=110, anchor="center", stretch=False)
        self._pile.grid(row=1, column=0, sticky="w", pady=(4, 4))

        risp = ttk.Frame(fis)
        risp.grid(row=2, column=0, sticky="w")
        ttk.Label(risp, text=tr("spectator.answer.question")).pack(anchor="w")
        bottoni = ttk.Frame(risp)
        bottoni.pack(anchor="w", pady=(2, 0))
        self._risposta_btn = []
        for g in range(3):
            b = ttk.Button(bottoni, text=self._nome_mazzetto(g),
                           command=lambda g=g: self.rispondi(g))
            b.pack(side="left", padx=(0, 6))
            self._risposta_btn.append(b)

        self._raccolta_lbl = ttk.Label(fis, text="", wraplength=420,
                                       justify="left")
        self._raccolta_lbl.grid(row=3, column=0, sticky="w", pady=(6, 2))
        self._raccolta_btn = ttk.Button(fis, text=tr("spectator.gather"),
                                        command=self.esegui_raccolta)
        self._raccolta_btn.grid(row=4, column=0, sticky="w")
        self._fisico_txt = self._testo(fis, 5)

        # ── stato dell'informazione ─────────────────────────────────────────
        inf = ttk.LabelFrame(self, text=f" {tr('spectator.info.title')} ",
                             padding=(8, 4))
        inf.grid(row=2, column=1, sticky="nsew", padx=(5, 10), pady=8)
        inf.columnconfigure(0, weight=1)
        self._conteggio_lbl = ttk.Label(inf, text="",
                                        font=("Consolas", 12, "bold"))
        self._conteggio_lbl.grid(row=0, column=0, sticky="w")
        ttk.Label(inf, text=tr("spectator.info.note"), wraplength=420,
                  justify="left", foreground="#555").grid(
            row=1, column=0, sticky="w", pady=(2, 4))
        self._info_txt = self._testo(inf, 2, altezza=18)

    def _testo(self, padre, riga, altezza=10):
        t = tk.Text(padre, height=altezza, width=52, wrap="word", relief="flat",
                    font=("Consolas", 9), background="#FAFCFF", takefocus=True)
        t.grid(row=riga, column=0, sticky="nsew", pady=(4, 0))
        t.configure(state="disabled")
        return t

    @staticmethod
    def _nome_mazzetto(g):
        nome = tr(("simulator.column.left", "simulator.column.center",
                   "simulator.column.right")[g])
        return f"{sp.lettera_mazzetto(g)} — {nome}"

    # ── controlli ────────────────────────────────────────────────────────────
    def _aggiorna_controlli(self):
        b12 = self._modo_var.get() == MODO_B12
        if b12:
            self._bersaglio_var.set(sp.CENTRO)
            self._bersaglio_spin.configure(state="disabled")
            self._mescolato_chk.configure(state="disabled")
            for cb in self._osservati_cb:
                cb.configure(state="readonly")
        else:
            self._bersaglio_spin.configure(state="normal")
            self._mescolato_chk.configure(state="normal")
            for cb in self._osservati_cb:
                cb.configure(state="disabled")

    def avvia(self):
        """Nuova sessione con i controlli correnti."""
        if self._modo_var.get() == MODO_B12:
            osservati = tuple(v.get() for v in self._osservati_var)
            self._riavvolgimento, self._sessione = sp.avvia_b12(osservati)
            facce = list(range(27))
            self._rnd.shuffle(facce)          # ordine vero, ignoto all'esecutore
            self._facce = tuple(facce)
        else:
            try:
                bersaglio = int(self._bersaglio_var.get())
            except (tk.TclError, ValueError):
                bersaglio = -1
            if not 0 <= bersaglio <= 26:
                self._riavvolgimento = self._sessione = None
                self._mostra(errore=tr("spectator.error.target"))
                return
            facce = list(range(27))
            if self._mescolato_var.get():
                self._rnd.shuffle(facce)
            self._facce = tuple(facce)
            self._riavvolgimento = None
            self._sessione = sp.avvia_spettatore(bersaglio, self._facce)
        self._mostra()

    def rispondi(self, mazzetto):
        if self._sessione is None:
            return
        try:
            self._sessione = sp.rispondi(self._sessione, mazzetto)
        except sp.RispostaNonAccettata as e:
            self._mostra(errore=tr(f"spectator.error.{e.codice}"))
            return
        self._mostra()

    def esegui_raccolta(self):
        if self._sessione is None:
            return
        try:
            self._sessione = sp.esegui_raccolta(self._sessione)
        except sp.RispostaNonAccettata as e:
            self._mostra(errore=tr(f"spectator.error.{e.codice}"))
            return
        self._mostra()

    # ── rappresentazione ─────────────────────────────────────────────────────
    def _mostra(self, errore=None):
        s = self._sessione
        attende_risposta = (s is not None and not s.conclusa
                            and not s.in_attesa_della_raccolta)
        for b in self._risposta_btn:
            b.configure(state="normal" if attende_risposta else "disabled")
        self._raccolta_btn.configure(
            state="normal" if s is not None and s.in_attesa_della_raccolta
            else "disabled")
        self._mostra_pile(s)
        self._mostra_conteggio(s)
        self._raccolta_lbl.configure(text=self._testo_raccolta(s))
        self._scrivi(self._fisico_txt, self._righe_fisiche(s, errore))
        self._scrivi(self._info_txt, self._righe_informative(s))

    def _mostra_pile(self, s):
        self._pile.delete(*self._pile.get_children())
        if s is None:
            self._fase_lbl.configure(text=tr("spectator.idle"))
            return
        if s.conclusa:
            self._fase_lbl.configure(text=tr("spectator.done"))
            return
        fase = s.fase + 1
        self._fase_lbl.configure(text=tr("spectator.phase", phase=fase))
        pile = sp.distribuzione_corrente(s)
        for i in range(9):
            self._pile.insert("", "end", iid=f"r{i}", values=tuple(
                _carta(self._facce[pile[g][i]]) for g in range(3)))

    def _mostra_conteggio(self, s):
        tappe = (27, 9, 3, 1)
        k = 0 if s is None else len(s.risposte)
        parti = [f"▶[{n}]" if i == k else str(n) for i, n in enumerate(tappe)]
        self._conteggio_lbl.configure(text=" → ".join(parti))

    def _testo_raccolta(self, s):
        if s is None or not s.in_attesa_della_raccolta:
            return ""
        fase = s.fase + 1
        a = s.risposte[-1]
        m = sp.scelta_raccolta(s.bersaglio, fase, a)
        sede = s.cifra_bersaglio(fase)
        return tr("spectator.gather.choice", pile=self._nome_mazzetto(a),
                  seat=sede, first=9 * sede, last=9 * sede + 8,
                  stacking=gr.IMPILAMENTO_DI[m], shuffle=m)

    def _righe_fisiche(self, s, errore):
        righe = []
        if errore:
            righe.append(f"⚠ {errore}")
        if s is None:
            return righe
        if self._riavvolgimento is not None:
            rv = self._riavvolgimento
            righe += [
                tr("spectator.b12.history",
                   stackings=", ".join(rv.impilamenti_osservati),
                   shuffles=", ".join(rv.mescolamenti_osservati),
                   number=rv.numero_osservato),
                tr("spectator.b12.rewind", number=rv.numero_ritorno,
                   stackings=", ".join(rv.impilamenti_di_ritorno)),
                tr("spectator.b12.rewound"), ""]
        else:
            righe += [tr("spectator.physical.known_order",
                         cards=" ".join(_carta(c) for c in self._facce)), ""]
        for p in sp.storia_informativa(s):
            if p.raccolta is None:
                continue
            righe.append(tr("spectator.physical.gathered", phase=p.fase,
                            pile=sp.lettera_mazzetto(p.risposta), seat=p.sede,
                            stacking=p.impilamento, shuffle=p.raccolta))
        if s.risposte:
            righe.append(tr("spectator.physical.candidates_now",
                            positions=_elenco(sp.posizioni_correnti_dei_candidati(s))))
        e = sp.esito(s)
        if e is not None:
            righe += ["", tr("spectator.physical.final",
                             position=e.posizione_finale, target=e.bersaglio,
                             number=e.numero_disposizione,
                             shuffles=" ".join(e.raccolte))]
        return righe

    def _righe_informative(self, s):
        if s is None:
            return [tr("spectator.info.start")]
        righe = [tr("spectator.info.initial")]
        for p in sp.storia_informativa(s):
            cifre = ["?", "?", "?"]
            for q in sp.storia_informativa(s)[:p.fase]:
                cifre[2 - q.indice_cifra] = sp.lettera_mazzetto(q.risposta)
            righe += [
                "",
                tr("spectator.info.phase", phase=p.fase,
                   letter=sp.lettera_mazzetto(p.risposta), answer=p.risposta,
                   digit=p.indice_cifra, word="".join(cifre)),
                tr("spectator.info.before", count=len(p.candidati_prima),
                   positions=_elenco(p.candidati_prima)),
                tr("spectator.info.after", count=len(p.candidati_dopo),
                   positions=_elenco(p.candidati_dopo)),
            ]
        e = sp.esito(s)
        if e is None:
            n = sp.posizione_iniziale_determinata(s)
            if n is not None:
                righe += ["", tr("spectator.info.determined", position=n)]
            return righe
        a1, a2, a3 = e.risposte
        n2, n1, n0 = e.cifre
        righe += [
            "", tr("spectator.result.title"),
            tr("spectator.result.answers", history=", ".join(e.storia),
               a1=a1, a2=a2, a3=a3),
            tr("spectator.result.formula", a1=a1, a2=a2, a3=a3,
               position=e.posizione_iniziale),
            tr("spectator.result.digits", n2=n2, n1=n1, n0=n0, word=e.parola,
               history=e.storia),
        ]
        if e.carta is not None:
            righe.append(tr("spectator.result.card", card=_carta(e.carta),
                            position=e.posizione_iniziale))
        else:
            righe.append(tr("spectator.result.card_unknown",
                            position=e.posizione_finale))
        righe.append(tr("spectator.result.target_yes" if e.bersaglio_raggiunto
                        else "spectator.result.target_no",
                        position=e.posizione_finale, target=e.bersaglio))
        return righe

    @staticmethod
    def _scrivi(testo, righe):
        testo.configure(state="normal")
        testo.delete("1.0", "end")
        testo.insert("end", "\n".join(righe) + "\n")
        testo.configure(state="disabled")
