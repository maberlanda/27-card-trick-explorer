"""Explorer → «Riconoscimento» (compartimento I5).

Flusso esplicito: INGRESSO → RICONOSCIMENTO → DIAGNOSTICA → FATTORI / SOMME /
RICOSTRUZIONE. Tutta la matematica sta in `services.riconoscimento`; qui solo
lettura dei campi, testo localizzato e marcatori ✔/✘ (non solo colore).
Solo widget testuali: nessun Canvas.
"""

import re
import tkinter as tk
from tkinter import ttk

from ..core import gioco_reale as gr
from ..core.dominio import PermutazioneNonValida
from ..services import riconoscimento as rc
from .i18n import tr
from . import context_help, guidance
from .tooltip import attach

MODO_PERM, MODO_MAZZI, MODO_DUE = "perm", "mazzi", "due"
_SIGLA = {v: k for k, v in gr.MESCOLAMENTO.items()}
_ORDINATO = " ".join(str(i) for i in range(27))


def _ok(v):
    return "✔" if v else "✘"


def _terna(t):
    return "(" + ", ".join(str(x) for x in t) + ")"


def _sigla(t):
    return _SIGLA.get(tuple(t), "?")


def _elenco(p):
    return " ".join(str(x) for x in p)


def _gettoni(testo):
    return [g for g in re.split(r"[\s,;\[\]()]+", testo.strip()) if g]


def _esempi():
    """Esempi fissi delle fonti: (chiave i18n, modo, testo 1, testo 2)."""
    r0, r1, r2 = (1, 2, 0), (2, 1, 0), (1, 0, 2)
    es71 = [9 * r2[x // 9] + 3 * r1[(x // 3) % 3] + r0[x % 3] for x in range(27)]
    v248 = [22, 23, 21, 19, 20, 18, 25, 26, 24, 13, 14, 12, 10, 11, 9, 16, 17, 15,
            4, 5, 3, 1, 2, 0, 7, 8, 6]
    equil = [20, 4, 17, 23, 8, 3, 16, 0, 26, 5, 12, 13, 11, 25, 14, 6, 21, 10,
             15, 22, 9, 2, 7, 24, 19, 18, 1]
    m100, _ = gr.esegui_partita(gr.mescolamenti_da_numero(100))
    m91, _ = gr.esegui_partita(gr.mescolamenti_da_numero(91))
    return [
        ("recognition.example.identity", MODO_PERM, _ORDINATO, ""),
        ("recognition.example.es71", MODO_PERM, _elenco(es71), ""),
        ("recognition.example.row100", MODO_PERM, _elenco(gr.riga_tavola(100)["T"]), ""),
        ("recognition.example.final248", MODO_MAZZI, _ORDINATO, _elenco(v248)),
        ("recognition.example.c1", MODO_PERM, _elenco(rc.traslazione(1)), ""),
        ("recognition.example.c9", MODO_PERM, _elenco(rc.traslazione(9)), ""),
        ("recognition.example.c18", MODO_PERM, _elenco(rc.traslazione(18)), ""),
        ("recognition.example.balanced", MODO_PERM, _elenco(equil), ""),
        ("recognition.example.twins", MODO_DUE, _elenco(m100), _elenco(m91)),
    ]


class RiconoscimentoFrame(ttk.Frame):
    """`fornisci_T()` restituisce la T calcolata nell'Explorer, o None."""

    def __init__(self, master, fornisci_T=None, **kw):
        super().__init__(master, padding=(8, 4), **kw)
        self._fornisci_T = fornisci_T or (lambda: None)
        self._pi = None
        self._mazzi = None
        self._esempi = _esempi()
        self.columnconfigure(0, weight=1)
        self._costruisci_ingresso()
        self._esito_lbl = ttk.Label(self, text=tr("recognition.idle"),
                                    font=("Segoe UI", 10, "bold"),
                                    foreground="#1F4E79")
        self._esito_lbl.grid(row=1, column=0, sticky="w", pady=(4, 4))
        self._costruisci_schede()
        self._su_modo()
        context_help.banner(self, "A08", getattr(self.winfo_toplevel(), "_open_guide", None)).grid(
            row=3, column=0, sticky="ew", pady=4)
        guidance.install(self, "recognition")
        attach(self._campo1, lambda: tr("ux4.input.permutation") if self._modo_var.get() == MODO_PERM else tr("ux4.input.decks"))
        attach(self._campo2, tr("ux4.input.decks"))
        attach(self._esempio_cb, tr("ux4.input.examples"))
        for entry in self._a1_campi:
            attach(entry, tr("ux4.input.a1"))

    def reset(self):
        self._pi = self._mazzi = None
        self._modo_var.set(MODO_PERM)
        self._verso_var.set(rc.AVANTI)
        self._pos_var.set(0)
        self._q0_var.set(2)
        self._q2_var.set(22)
        self._su_modo()
        self._esempio_cb.set("")
        for campo in (self._campo1, self._campo2, self._diretto_txt,
                      self._somme_txt, self._estesa_txt, self._guide_txt,
                      self._a1_txt, self._vw_txt):
            self._imposta(campo, "")
        for campo in self._a1_campi:
            campo.delete(0, "end")
        self._errore_lbl.configure(text="")
        self._esito_lbl.configure(text=tr("recognition.idle"))

    # ── costruzione ──────────────────────────────────────────────────────────
    def _costruisci_ingresso(self):
        fr = ttk.LabelFrame(self, text=f" {tr('recognition.input')} ", padding=(8, 2))
        fr.grid(row=0, column=0, sticky="ew")
        fr.columnconfigure(1, weight=1)
        modi = ttk.Frame(fr)
        modi.grid(row=0, column=0, columnspan=2, sticky="w")
        self._modo_var = tk.StringVar(value=MODO_PERM)
        self._modi_rb = []
        for valore, chiave in ((MODO_PERM, "recognition.mode.permutation"),
                               (MODO_MAZZI, "recognition.mode.decks"),
                               (MODO_DUE, "recognition.mode.twins")):
            rb = ttk.Radiobutton(modi, text=tr(chiave), value=valore,
                                 variable=self._modo_var, command=self._su_modo)
            rb.pack(side="left", padx=(0, 12))
            self._modi_rb.append(rb)
        self._lbl1 = ttk.Label(fr, text="")
        self._lbl1.grid(row=1, column=0, sticky="nw", pady=(4, 0))
        self._input_hint = ttk.Label(fr, wraplength=1000, justify="left")
        self._input_hint.grid(row=5, column=0, columnspan=2, sticky="w", pady=2)
        self._campo1 = tk.Text(fr, height=2, width=80, font=("Consolas", 10),
                               wrap="word", undo=True)
        self._campo1.grid(row=1, column=1, sticky="ew", pady=(4, 0))
        self._lbl2 = ttk.Label(fr, text="")
        self._lbl2.grid(row=2, column=0, sticky="nw", pady=(2, 0))
        self._campo2 = tk.Text(fr, height=2, width=80, font=("Consolas", 10),
                               wrap="word", undo=True)
        self._campo2.grid(row=2, column=1, sticky="ew", pady=(2, 0))
        for campo in (self._campo1, self._campo2):     # Tab esce dal campo
            campo.bind("<Tab>", lambda e: (e.widget.tk_focusNext().focus_set(), "break")[1])
            campo.bind("<Shift-Tab>", lambda e: (e.widget.tk_focusPrev().focus_set(), "break")[1])
        comandi = ttk.Frame(fr)
        comandi.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 2))
        self._analizza_btn = ttk.Button(comandi, text=f"▶  {tr('recognition.analyze')}",
                                        command=self.analizza)
        self._analizza_btn.pack(side="left")
        self._usa_T_btn = ttk.Button(comandi, text=tr("recognition.use_explorer"),
                                     command=self.usa_T_explorer)
        self._usa_T_btn.pack(side="left", padx=(6, 0))
        ttk.Label(comandi, text=tr("recognition.examples")).pack(side="left", padx=(16, 4))
        self._esempio_cb = ttk.Combobox(
            comandi, state="readonly", width=34,
            values=[tr(k) for k, *_ in self._esempi])
        self._esempio_cb.pack(side="left")
        self._esempio_btn = ttk.Button(comandi, text=tr("recognition.load_example"),
                                       command=self.carica_esempio)
        self._esempio_btn.pack(side="left", padx=(6, 0))
        self._errore_lbl = ttk.Label(fr, text="", foreground="#9B1C1C",
                                     wraplength=1000, justify="left")
        self._errore_lbl.grid(row=4, column=0, columnspan=2, sticky="w")

    def _testo(self, padre, altezza=13):
        t = tk.Text(padre, height=altezza, width=100, wrap="word", relief="flat",
                    font=("Consolas", 9), background="#FAFCFF", takefocus=True)
        t.configure(state="disabled")
        return t

    def _costruisci_schede(self):
        nb = ttk.Notebook(self)
        nb.grid(row=2, column=0, sticky="nsew")
        self._schede = nb

        self._diretto_txt = self._testo(nb)
        nb.add(self._diretto_txt, text=f" {tr('recognition.tab.direct')} ")

        somme = ttk.Frame(nb, padding=(4, 2))
        somme.columnconfigure(0, weight=1)
        versi = ttk.Frame(somme)
        versi.grid(row=0, column=0, sticky="w")
        self._verso_var = tk.StringVar(value=rc.AVANTI)
        self._verso_rb = []
        for valore, chiave in ((rc.AVANTI, "recognition.sums.forward"),
                               (rc.INDIETRO, "recognition.sums.backward")):
            rb = ttk.Radiobutton(versi, text=tr(chiave), value=valore,
                                 variable=self._verso_var, command=self._mostra_somme)
            rb.pack(side="left", padx=(0, 12))
            self._verso_rb.append(rb)
        self._somme_txt = self._testo(somme, 12)
        self._somme_txt.grid(row=1, column=0, sticky="nsew", pady=(2, 0))
        nb.add(somme, text=f" {tr('recognition.tab.sums')} ")

        self._estesa_txt = self._testo(nb)
        nb.add(self._estesa_txt, text=f" {tr('recognition.tab.extended')} ")

        guide = ttk.Frame(nb, padding=(4, 2))
        guide.columnconfigure(0, weight=1)
        riga = ttk.Frame(guide)
        riga.grid(row=0, column=0, sticky="w")
        ttk.Label(riga, text=tr("recognition.guides.q0")).pack(side="left")
        self._q0_var, self._q2_var = tk.IntVar(value=2), tk.IntVar(value=22)
        self._q0_spin = ttk.Spinbox(riga, from_=0, to=26, width=4, textvariable=self._q0_var)
        self._q0_spin.pack(side="left", padx=(4, 12))
        ttk.Label(riga, text=tr("recognition.guides.q2")).pack(side="left")
        self._q2_spin = ttk.Spinbox(riga, from_=0, to=26, width=4, textvariable=self._q2_var)
        self._q2_spin.pack(side="left", padx=(4, 12))
        self._guide_btn = ttk.Button(riga, text=tr("recognition.guides.run"),
                                     command=self.guide_da_posizioni)
        self._guide_btn.pack(side="left")
        self._guide_mazzi_btn = ttk.Button(riga, text=tr("recognition.guides.from_decks"),
                                           command=self.guide_da_mazzi)
        self._guide_mazzi_btn.pack(side="left", padx=(6, 0))
        ttk.Label(guide, text=tr("ux3.guides.positions"), wraplength=900,
                  justify="left").grid(row=1, column=0, sticky="w", pady=3)
        self._guide_txt = self._testo(guide, 12)
        self._guide_txt.grid(row=2, column=0, sticky="nsew", pady=(2, 0))
        nb.add(guide, text=f" {tr('recognition.tab.guides')} ")

        a1 = ttk.Frame(nb, padding=(4, 2))
        a1.columnconfigure(1, weight=1)
        self._a1_campi = []
        ttk.Label(a1, text=tr("ux3.a1"), wraplength=1000).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=4)
        for r, chiave in enumerate(("recognition.a1.initial", "recognition.a1.final",
                                    "recognition.a1.transformation")):
            ttk.Label(a1, text=tr(chiave)).grid(row=r+1, column=0, sticky="w")
            e = ttk.Entry(a1, font=("Consolas", 9))
            e.grid(row=r+1, column=1, sticky="ew", pady=1)
            self._a1_campi.append(e)
        self._a1_btn = ttk.Button(a1, text=tr("recognition.a1.run"), command=self.a1)
        self._a1_btn.grid(row=4, column=0, sticky="w", pady=(2, 2))
        self._a1_txt = self._testo(a1, 8)
        self._a1_txt.grid(row=5, column=0, columnspan=2, sticky="nsew")
        nb.add(a1, text=f" {tr('recognition.tab.a1')} ")

        vw = ttk.Frame(nb, padding=(4, 2))
        vw.columnconfigure(0, weight=1)
        riga = ttk.Frame(vw)
        riga.grid(row=0, column=0, sticky="w")
        ttk.Label(riga, text=tr("recognition.vw.position")).pack(side="left")
        self._pos_var = tk.IntVar(value=0)
        self._pos_spin = ttk.Spinbox(riga, from_=0, to=26, width=4, textvariable=self._pos_var)
        self._pos_spin.pack(side="left", padx=(4, 8))
        self._effetto_btn = ttk.Button(riga, text=tr("recognition.vw.effect"),
                                       command=self.mostra_effetto)
        self._effetto_btn.pack(side="left")
        self._vw_txt = self._testo(vw, 12)
        self._vw_txt.grid(row=1, column=0, sticky="nsew", pady=(2, 0))
        nb.add(vw, text=f" {tr('recognition.tab.reach')} ")

    # ── ingresso ─────────────────────────────────────────────────────────────
    def _su_modo(self):
        modo = self._modo_var.get()
        self._input_hint.configure(text=tr("ux3.recognition.independent") + "\n" +
                                  tr("ux3.permutation" if modo == MODO_PERM else "ux3.decks"))
        etichette = {MODO_PERM: ("recognition.field.T", None),
                     MODO_MAZZI: ("recognition.field.initial", "recognition.field.final"),
                     MODO_DUE: ("recognition.field.deck_a", "recognition.field.deck_b")}
        k1, k2 = etichette[modo]
        self._lbl1.configure(text=tr(k1))
        if k2 is None:
            self._lbl2.configure(text="")
            self._campo2.configure(state="disabled", background="#EEEEEE")
            # K: in «Permutazione T» il secondo campo non serve: prima restava
            # visibile e disattivato (42 px). Ora si ritira e riappare negli
            # altri due modi, nella stessa posizione e nello stesso ordine di Tab.
            self._lbl2.grid_remove()
            self._campo2.grid_remove()
        else:
            self._lbl2.configure(text=tr(k2))
            self._campo2.configure(state="normal", background="white")
            self._lbl2.grid()
            self._campo2.grid()

    def _imposta(self, campo, testo):
        stato = campo.cget("state")
        campo.configure(state="normal")
        campo.delete("1.0", "end")
        campo.insert("1.0", testo)
        campo.configure(state=stato)

    def usa_T_explorer(self):
        T = self._fornisci_T()
        if T is None:
            self._errore_lbl.configure(text=f"⚠ {tr('recognition.error.no_explorer_T')}")
            return
        self._modo_var.set(MODO_PERM)
        self._su_modo()
        self._imposta(self._campo1, _elenco(T))
        self.analizza()

    def carica_esempio(self):
        i = self._esempio_cb.current()
        if i < 0:
            return
        _, modo, t1, t2 = self._esempi[i]
        self._modo_var.set(modo)
        self._su_modo()
        self._imposta(self._campo1, t1)
        self._imposta(self._campo2, t2)
        self.analizza()

    def _leggi(self):
        modo = self._modo_var.get()
        g1 = _gettoni(self._campo1.get("1.0", "end"))
        if modo == MODO_PERM:
            try:
                valori = [int(x) for x in g1]
            except ValueError:
                raise PermutazioneNonValida("", codice="non_intero")
            return rc.permutazione(valori), None
        g2 = _gettoni(self._campo2.get("1.0", "end"))
        return rc.da_mazzi(g1, g2), (g1, g2)

    def _errore(self, e):
        self._errore_lbl.configure(text=f"⚠ {self._testo_errore(e)}")

    # ── analisi ──────────────────────────────────────────────────────────────
    def analizza(self):
        try:
            pi, mazzi = self._leggi()
        except (PermutazioneNonValida, rc.IngressoNonValido) as e:
            self._errore(e)
            self._pi = self._mazzi = None
            self._esito_lbl.configure(text=tr("recognition.idle"))
            return
        self._errore_lbl.configure(text="")
        self._pi, self._mazzi = pi, mazzi
        self._diretto = rc.separabile(pi)
        self._estesa = rc.classe_estesa(pi)
        somme = rc.criterio_somme(pi, rc.AVANTI)
        riga = self._diretto.numero_tavola
        self._esito_lbl.configure(text=tr(
            "recognition.summary", direct=_ok(self._diretto.separabile),
            sums=_ok(somme.vero), extended=_ok(self._estesa.appartiene),
            row=f"#{riga}" if riga is not None else "—"))
        self._mostra_diretto()
        self._mostra_somme()
        self._mostra_estesa()
        self._mostra_vw()
        # J: la sessione registra il nuovo stato scientifico (se collegata)
        avvisa = getattr(self, "on_stato", None)
        if avvisa is not None:
            avvisa(pi)

    def _scrivi(self, testo, righe):
        testo.configure(state="normal")
        testo.delete("1.0", "end")
        testo.insert("1.0", "\n".join(righe))
        testo.configure(state="disabled")

    def _mostra_diretto(self):
        d = self._diretto
        righe = [tr("recognition.direct.intro"), ""]
        for l in d.livelli:
            if l.passa:
                righe.append(tr("recognition.direct.level_ok", level=l.livello,
                                weight=3 ** l.livello, factor=_terna(l.fattore),
                                code=_sigla(l.fattore)))
            else:
                c = l.conflitto
                righe.append(tr("recognition.direct.level_fail", level=l.livello,
                                weight=3 ** l.livello, digit=c.cifra, x1=c.x1, x2=c.x2,
                                y1=c.immagine1, y2=c.immagine2,
                                d1=c.cifra_immagine1, d2=c.cifra_immagine2))
        righe.append("")
        if d.separabile:
            righe.append(tr("recognition.direct.yes", row=d.numero_tavola,
                            codes=" ".join(d.sigle)))
        else:
            righe.append(tr("recognition.direct.no"))
        self._scrivi(self._diretto_txt, righe)

    def _mostra_somme(self):
        if self._pi is None:
            return
        verso = self._verso_var.get()
        c = rc.criterio_somme(self._pi, verso)
        righe = [tr("recognition.sums.intro_forward" if verso == rc.AVANTI
                    else "recognition.sums.intro_backward"),
                 tr("recognition.sums.formula", c0=rc.COSTANTI_C[0],
                    c1=rc.COSTANTI_C[1], c2=rc.COSTANTI_C[2]), ""]
        for l in c.livelli:
            righe.append(tr("recognition.sums.level", level=l.livello,
                            sums=_terna(l.somme),
                            candidates=_terna(str(x) for x in l.candidati)))
            righe.append(tr("recognition.sums.checks", integer=_ok(l.interi),
                            domain=_ok(l.in_dominio), distinct=_ok(l.distinti),
                            perm=_ok(l.permutazione)))
            if l.permutazione:
                righe.append(tr("recognition.sums.factor", factor=_terna(l.fattore),
                                code=_sigla(l.fattore)))
        righe.append("")
        if c.vero:
            righe.append(tr("recognition.sums.true", same=_ok(c.coincide)))
        else:
            righe.append(tr("recognition.sums.false"))
        self._scrivi(self._somme_txt, righe)

    def _mostra_estesa(self):
        e = self._estesa
        if e.appartiene:
            righe = [tr("recognition.extended.yes", k=e.k),
                     tr("recognition.extended.component",
                        row=e.separabilita.numero_tavola,
                        codes=" ".join(e.separabilita.sigle))]
            if e.k == 0:
                righe.append(tr("recognition.extended.separable"))
        else:
            righe = [tr("recognition.extended.no")]
        self._scrivi(self._estesa_txt, [tr("recognition.extended.intro"), ""] + righe)

    # ── strumenti ────────────────────────────────────────────────────────────
    def _righe_guide(self, g):
        righe = [tr("recognition.guides.digits", q0=g.q0, q2=g.q2,
                    u=_terna(g.cifre_q0), v=_terna(g.cifre_q2))]
        for h, valido in zip((2, 1, 0), g.livelli_validi):
            righe.append(tr("recognition.guides.level", level=h, ok=_ok(valido)))
        if not g.valide:
            righe.append(tr("recognition.guides.invalid"))
            return righe
        for h, tau in zip((2, 1, 0), g.ritorno):
            righe.append(tr("recognition.guides.row", level=h, row=_terna(tau),
                            code=_sigla(tau)))
        righe.append(tr("recognition.guides.return", row=g.numero_ritorno,
                        stackings=" ".join(gr.IMPILAMENTO_DI[s] for s in
                                           gr.mescolamenti_da_numero(g.numero_ritorno))))
        righe.append(tr("recognition.guides.third", q1=g.terza_guida))
        if g.verifica is not None:
            righe.append(tr("recognition.guides.check_ok") if g.verifica else
                         tr("recognition.guides.check_fail", position=g.primo_scarto))
        return righe

    def guide_da_posizioni(self):
        try:
            g = rc.ritorno_da_guide(int(self._q0_var.get()), int(self._q2_var.get()))
        except (tk.TclError, ValueError, PermutazioneNonValida):
            self._scrivi(self._guide_txt, [f"⚠ {tr('recognition.error.guides')}"])
            return
        self._scrivi(self._guide_txt, [tr("recognition.guides.intro"), ""] + self._righe_guide(g))

    def guide_da_mazzi(self):
        if self._mazzi is None or self._modo_var.get() != MODO_MAZZI:
            self._scrivi(self._guide_txt, [f"⚠ {tr('recognition.error.need_decks')}"])
            return
        g = rc.ritorno_da_mazzi(*self._mazzi)
        self._q0_var.set(g.q0)
        self._q2_var.set(g.q2)
        self._scrivi(self._guide_txt, [tr("recognition.guides.intro"), ""] + self._righe_guide(g))

    def a1(self):
        valori = [e.get().strip() for e in self._a1_campi]
        try:
            ini = _gettoni(valori[0]) or None
            fin = _gettoni(valori[1]) or None
            T = [int(x) for x in _gettoni(valori[2])] or None
            esito = rc.nota_due(ini, fin, T)
        except ValueError as e:
            if not hasattr(e, "codice"):
                e = PermutazioneNonValida("", codice="non_intero")
            self._scrivi(self._a1_txt, [f"⚠ {self._testo_errore(e)}"])
            return
        righe = [tr("recognition.a1.law"), tr(f"recognition.a1.law.{esito.legge}"), ""]
        if esito.calcolato:
            righe.append(tr(f"recognition.a1.computed.{esito.calcolato}"))
        righe += [tr("recognition.a1.show_initial", deck=_elenco(esito.iniziale)),
                  tr("recognition.a1.show_final", deck=_elenco(esito.finale)),
                  tr("recognition.a1.show_T", T=_elenco(esito.trasformazione))]
        self._scrivi(self._a1_txt, righe)

    def _testo_errore(self, e):
        codice = getattr(e, "codice", "") or "generic"
        try:
            return tr(f"recognition.error.{codice}")
        except KeyError:                      # codice senza frase dedicata
            return tr("recognition.error.generic", code=codice)

    def _mostra_vw(self):
        righe = []
        if self._modo_var.get() == MODO_DUE and self._mazzi is not None:
            r = rc.raggiungibile(*self._mazzi)
            righe += [tr("recognition.vw.reach_intro"),
                      tr("recognition.vw.guides", q0=r.guide.q0, q2=r.guide.q2)]
            if not r.guide.valide:
                bad = [h for h, ok in zip((2, 1, 0), r.guide.livelli_validi) if not ok]
                righe.append(tr("recognition.vw.no_digits", levels=", ".join(map(str, bad))))
            else:
                righe.append(tr("recognition.vw.card13", expected=r.posizione_attesa_13,
                                actual=r.posizione_reale_13,
                                ok=_ok(r.posizione_attesa_13 == r.posizione_reale_13)))
                righe.append(tr("recognition.vw.yes", row=r.numero) if r.raggiungibile
                             else tr("recognition.vw.no", label=r.primo_scarto))
            righe.append("")
        righe.append(tr("recognition.vw.effect_intro"))
        self._scrivi(self._vw_txt, righe)

    def mostra_effetto(self):
        if self._pi is None:
            return
        try:
            e = rc.effetto(self._pi, int(self._pos_var.get()))
        except (tk.TclError, ValueError):
            return
        self._mostra_vw()
        self._vw_txt.configure(state="normal")
        self._vw_txt.insert("end", "\n" + tr("recognition.vw.effect_result",
                                             p=e.posizione, image=e.immagine,
                                             pre=e.preimmagine))
        self._vw_txt.configure(state="disabled")
