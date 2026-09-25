"""Explorer → «Laboratorio» (compartimento I6).

[Catalogo proprieta'] | [Dettaglio / verifica], piu' quattro viste sulle
strutture finite: Classi, Classi laterali e stadi, Tavola locale 6×6, Grafi.
Tutta la matematica sta in `services.laboratorio`; qui solo lettura dei campi
e testo localizzato. Esiti con ✔/✘ e parole (non solo colore). Solo widget
testuali: nessun Canvas, i grafi sono resi come elenchi di vertici e archi.

Notazione DP2: «H — 216», «Γ — 648», «S27». Una sola nota tecnica ricorda i
nomi legacy (G = 216 nel core, H = 648 altrove).
"""

import tkinter as tk
from tkinter import ttk

from ..core import gioco_reale as gr
from ..services import laboratorio as lab
from ..services.laboratorio import Dominio, Esito, Metodo
from .i18n import tr

_SEGNO = {Esito.VERA: "✔", Esito.FALSA: "✘", Esito.NON_DECISA: "?"}


def _perm(p):
    return " ".join(str(x) for x in p)


def _tipo(t):
    """((1, 3), (2, 12)) → 1³ 2¹²  (in testo: 1^3 2^12)."""
    return " ".join(f"{l}^{c}" for l, c in t)


def _dominio(d):
    return tr(f"lab.domain.{d.value}")


class LaboratorioFrame(ttk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, padding=(8, 4), **kw)
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text=tr("lab.header"), font=("Segoe UI", 10, "bold"),
                  foreground="#1F4E79").grid(row=0, column=0, sticky="w")
        self._nota_legacy = ttk.Label(self, text=tr("lab.legacy_note"),
                                      foreground="#555555", wraplength=1100,
                                      justify="left")
        self._nota_legacy.grid(row=1, column=0, sticky="w", pady=(0, 4))
        nb = ttk.Notebook(self)
        nb.grid(row=2, column=0, sticky="nsew")
        self._schede = nb
        self._costruisci_proprieta(nb)
        self._costruisci_classi(nb)
        self._costruisci_coset(nb)
        self._costruisci_locale(nb)
        self._costruisci_grafi(nb)
        self._elenco.selection_set(0)
        self._su_proprieta()

    # ── utilita' ─────────────────────────────────────────────────────────────
    def _testo(self, padre, altezza=11, larghezza=96):
        t = tk.Text(padre, height=altezza, width=larghezza, wrap="word", relief="flat",
                    font=("Consolas", 9), background="#FAFCFF", takefocus=True)
        t.configure(state="disabled")
        return t

    def _con_barra(self, padre, testo):
        sb = ttk.Scrollbar(padre, orient="vertical", command=testo.yview)
        testo.configure(yscrollcommand=sb.set)
        return sb

    def _scrivi(self, testo, righe):
        testo.configure(state="normal")
        testo.delete("1.0", "end")
        testo.insert("1.0", "\n".join(righe))
        testo.configure(state="disabled")

    # ═════════════════════════════ Proprieta' ═══════════════════════════════
    def _costruisci_proprieta(self, nb):
        fr = ttk.Frame(nb, padding=(4, 4))
        fr.columnconfigure(2, weight=1)
        fr.rowconfigure(1, weight=1)
        ttk.Label(fr, text=tr("lab.catalog")).grid(row=0, column=0, sticky="w")
        self._elenco = tk.Listbox(fr, height=11, width=34, exportselection=False,
                                  activestyle="dotbox", font=("Segoe UI", 9))
        for p in lab.CATALOGO:
            self._elenco.insert("end", tr(f"lab.name.{p.id}"))
        self._elenco.grid(row=1, column=0, sticky="nsw")
        sb = ttk.Scrollbar(fr, orient="vertical", command=self._elenco.yview)
        self._elenco.configure(yscrollcommand=sb.set)
        sb.grid(row=1, column=1, sticky="ns", padx=(0, 8))
        self._elenco.bind("<<ListboxSelect>>", lambda e: self._su_proprieta())

        destra = ttk.Frame(fr)
        destra.grid(row=0, column=2, rowspan=2, sticky="nsew")
        destra.columnconfigure(0, weight=1)
        destra.rowconfigure(1, weight=1)
        riga = ttk.Frame(destra)
        riga.grid(row=0, column=0, sticky="w")
        ttk.Label(riga, text=tr("lab.domain_choice")).pack(side="left", padx=(0, 6))
        self._dominio_var = tk.StringVar(value=Dominio.H.value)
        self._domini_rb = {}
        for d in Dominio:
            rb = ttk.Radiobutton(riga, text=tr(f"lab.domain.short.{d.value}"),
                                 value=d.value, variable=self._dominio_var,
                                 command=self.verifica)
            rb.pack(side="left", padx=(0, 8))
            self._domini_rb[d] = rb
        self._verifica_btn = ttk.Button(riga, text=f"▶  {tr('lab.verify')}",
                                        command=self.verifica)
        self._verifica_btn.pack(side="left", padx=(8, 0))
        self._dettaglio_txt = self._testo(destra, 10, 90)
        self._dettaglio_txt.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self._con_barra(destra, self._dettaglio_txt).grid(row=1, column=1, sticky="ns",
                                                           pady=(4, 0))
        nb.add(fr, text=f" {tr('lab.tab.properties')} ")

    def proprieta_scelta(self):
        sel = self._elenco.curselection()
        return lab.CATALOGO[sel[0] if sel else 0]

    def _su_proprieta(self):
        p = self.proprieta_scelta()
        for d, rb in self._domini_rb.items():
            rb.configure(state="normal" if d in p.domini else "disabled")
        if Dominio(self._dominio_var.get()) not in p.domini:
            self._dominio_var.set(p.domini[0].value)
        self.verifica()

    def verifica(self):
        p = self.proprieta_scelta()
        d = Dominio(self._dominio_var.get())
        if d not in p.domini:                       # radiobutton disattivato
            d = p.domini[0]
            self._dominio_var.set(d.value)
        v = p.verifica(d)
        self._verifica = v
        self._scrivi(self._dettaglio_txt, self._righe_verifica(p, v))
        # J: la sessione registra il nuovo stato scientifico (se collegata)
        avvisa = getattr(self, "on_stato", None)
        if avvisa is not None:
            avvisa(p.id, d.value)

    def _righe_verifica(self, p, v):
        altri = ", ".join(tr(f"lab.domain.short.{x.value}") for x in p.domini)
        righe = [
            f"{tr('lab.field.statement')}: {tr(f'lab.prop.{p.id}')}",
            f"{tr('lab.field.domain')}: {_dominio(v.dominio)}   "
            f"({tr('lab.field.declared_domains')}: {altri})",
            f"{tr('lab.field.outcome')}: {_SEGNO[v.esito]} {tr(f'lab.outcome.{v.esito.value}')}",
            f"{tr('lab.field.verification')}: {tr(f'lab.method.{v.metodo.value}')} — "
            + self._conteggio(v),
            f"{tr('lab.field.counterexample')}: " + self._controesempio(v),
            f"{tr('lab.field.source')}: {tr(f'lab.source.{p.fonte}')}",
        ]
        nota = p.nota(v.dominio)
        if nota:
            righe.append(f"{tr('lab.field.note')}: {tr(f'lab.note.{nota}')}")
        return righe

    def _conteggio(self, v):
        if v.metodo is Metodo.TEOREMA_FONTE:
            return tr("lab.checked.theorem", theorem=tr(f"lab.theorem.{v.fonte}"))
        if v.dominio is Dominio.S27:
            return tr("lab.checked.s27", checked=v.controllati)
        if v.vera:
            return tr("lab.checked.all", checked=v.controllati, total=v.totale)
        return tr("lab.checked.until", checked=v.controllati, total=v.totale)

    def _dove(self, p):
        e = lab.etichetta(p)
        if e.dominio is Dominio.H:
            return tr("lab.where.h", row=e.numero_tavola, codes=" ".join(e.sigle))
        if e.dominio is Dominio.GAMMA:
            return tr("lab.where.gamma", r=e.r, row=e.numero_tavola)
        return tr("lab.where.s27")

    def _controesempio(self, v):
        ce = v.controesempio
        if ce is None:
            return "—"
        dati = dict(ce.dati)
        if ce.codice == "due_carte":
            corpo = tr("lab.cex.due_carte", **dati)
        elif ce.codice == "carta_bersaglio":
            corpo = tr("lab.cex.carta_bersaglio", card=dati["carta"],
                       position=dati["posizione"], solutions=dati["soluzioni"])
        else:
            valori = {}
            if "punti_fissi" in dati:
                valori["fixed"] = dati["punti_fissi"]
            if "ordine" in dati:
                valori["order"] = dati["ordine"]
            if "somma" in dati:
                valori["sum"] = dati["somma"]
            if "tipo" in dati:
                valori["type"] = _tipo(dati["tipo"])
            corpo = tr(f"lab.cex.{ce.codice}", **valori) if valori else tr(f"lab.cex.{ce.codice}")
        righe = [corpo]
        for nome, el in zip(("a", "b"), ce.elementi):
            etichetta = f"T{'' if len(ce.elementi) == 1 else ' ' + nome} = "
            if len(el) == 3:                                    # S3: una sigla
                righe.append(f"  {etichetta}{_sigla(el)}  ({_perm(el)})")
            else:
                righe.append(f"  {etichetta}{_perm(el)}")
                righe.append(f"      {self._dove(el)}")
        if "ab" in dati:
            ab, ba = dati["ab"], dati["ba"]
            f = _sigla if len(ab) == 3 else _perm
            righe.append(f"  a∘b = {f(ab)}")
            righe.append(f"  b∘a = {f(ba)}")
        righe.append("  " + tr("lab.cex.minimal"))
        return "\n".join(righe)

    # ═══════════════════════════════ Classi ══════════════════════════════════
    def _costruisci_classi(self, nb):
        fr = ttk.Frame(nb, padding=(4, 4))
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(1, weight=1)
        riga = ttk.Frame(fr)
        riga.grid(row=0, column=0, sticky="w")
        self._vista_classi = tk.StringVar(value="classi")
        self._classi_rb = []
        for valore in ("classi", "fusione", "centro", "j"):
            rb = ttk.Radiobutton(riga, text=tr(f"lab.classes.view.{valore}"), value=valore,
                                 variable=self._vista_classi, command=self.mostra_classi)
            rb.pack(side="left", padx=(0, 12))
            self._classi_rb.append(rb)
        self._classi_txt = self._testo(fr, 11)
        self._classi_txt.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self._con_barra(fr, self._classi_txt).grid(row=1, column=1, sticky="ns", pady=(4, 0))
        nb.add(fr, text=f" {tr('lab.tab.classes')} ")
        self.mostra_classi()

    def mostra_classi(self):
        vista = self._vista_classi.get()
        if vista == "classi":
            righe = [tr("lab.classes.intro"), "", tr("lab.classes.header")]
            for c in lab.classi_h():
                rap = gr.mescolamenti_da_numero(c.elementi[0])
                righe.append(f"{c.numero:>3}  {'(' + ', '.join(c.tipo) + ')':<11}"
                             f"{c.cardinalita:>5}  {c.ordine:>5}  {c.punti_fissi:>5}  "
                             f"{_tipo(c.tipo_ciclico):<14}#{c.elementi[0]} {' '.join(rap)}"
                             + ("  ⋆" if c.centrale else ""))
            eq = " + ".join(str(c.cardinalita) for c in lab.classi_h())
            righe += ["", tr("lab.classes.equation", eq=eq)]
        elif vista == "fusione":
            righe = [tr("lab.fusion.intro"), "", tr("lab.fusion.header")]
            for t in lab.fusione_in_s27():
                righe.append(f"{t.numero:>3}  {_tipo(t.tipo):<14}{t.ordine:>5}  "
                             f"{t.punti_fissi:>5}  {'+' if t.segno > 0 else '−':>5}  "
                             f"{t.cardinalita:>6}  {', '.join(map(str, t.classi))}")
            righe += ["", tr("lab.fusion.total",
                             classes=sum(len(t.classi) for t in lab.fusione_in_s27()),
                             types=len(lab.fusione_in_s27()))]
        elif vista == "centro":
            c = lab.centro()
            righe = [tr("lab.center.body", size=len(c.elementi),
                        elements=", ".join(f"#{n}" for n in c.elementi),
                        checks=c.commutazioni_controllate,
                        legacy="✔" if c.legacy_concorda else "✘")]
        else:
            j = lab.scheda_j()
            righe = [tr("lab.j.body", row=j.numero_tavola, codes=" ".join(j.sigle),
                        perm=_perm(j.permutazione), order=j.ordine,
                        type=_tipo(j.tipo_ciclico),
                        fixed=", ".join(map(str, j.punti_fissi)),
                        cls=j.classe, clstype="(" + ", ".join(j.tipo_classe) + ")",
                        procedures=", ".join(f"({n}, {m})" for n, m in j.procedure))]
        self._scrivi(self._classi_txt, righe)

    # ═══════════════════════ Classi laterali e stadi ══════════════════════════
    def _costruisci_coset(self, nb):
        fr = ttk.Frame(nb, padding=(4, 4))
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(0, weight=1)
        self._coset_txt = self._testo(fr, 12)
        self._coset_txt.grid(row=0, column=0, sticky="nsew")
        self._con_barra(fr, self._coset_txt).grid(row=0, column=1, sticky="ns")
        righe = [tr("lab.cosets.objects"), "", tr("lab.cosets.intro")]
        for c in lab.classi_laterali():
            righe.append(tr("lab.cosets.row", r=c.r, size=c.cardinalita,
                            h="  = H" if c.contiene_h else ""))
        righe += ["", tr("lab.stages.header")]
        for s in lab.stadi():
            righe.append(f"{s.j:>3}  {s.prefissi_senza:>6} → {s.trasformazioni_senza:<5}"
                         f"{s.prefissi_con:>8} → {s.trasformazioni_con:<5}"
                         f"{'×' + ','.join(map(str, s.molteplicita)):>6}   "
                         f"H∘R^{s.classi_laterali[0]}")
        r3 = lab.stadi()[-1]
        righe += ["", tr("lab.stages.match", n=r3.configurazioni_uguali_a_procedure)]
        self._scrivi(self._coset_txt, righe)
        nb.add(fr, text=f" {tr('lab.tab.cosets')} ")

    # ═════════════════════════ Tavola locale 6×6 ══════════════════════════════
    def _costruisci_locale(self, nb):
        fr = ttk.Frame(nb, padding=(4, 4))
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(1, weight=1)
        riga = ttk.Frame(fr)
        riga.grid(row=0, column=0, sticky="w")
        sigle = list(lab.ORDINE_TAVOLA_LOCALE)
        ttk.Label(riga, text=tr("lab.local.decomp.label")).pack(side="left")
        self._risultato_cb = ttk.Combobox(riga, state="readonly", width=6, values=sigle)
        self._risultato_cb.current(1)
        self._risultato_cb.pack(side="left", padx=(4, 16))
        ttk.Label(riga, text=tr("lab.local.transition.from")).pack(side="left")
        self._da_cb = ttk.Combobox(riga, state="readonly", width=6, values=sigle)
        self._da_cb.current(1)
        self._da_cb.pack(side="left", padx=(4, 8))
        ttk.Label(riga, text=tr("lab.local.transition.to")).pack(side="left")
        self._a_cb = ttk.Combobox(riga, state="readonly", width=6, values=sigle)
        self._a_cb.current(3)
        self._a_cb.pack(side="left", padx=(4, 8))
        self._locale_btn = ttk.Button(riga, text=f"▶  {tr('lab.local.show')}",
                                      command=self.mostra_locale)
        self._locale_btn.pack(side="left", padx=(8, 0))
        for cb in (self._risultato_cb, self._da_cb, self._a_cb):
            cb.bind("<<ComboboxSelected>>", lambda e: self.mostra_locale())
        self._locale_txt = self._testo(fr, 11)
        self._locale_txt.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self._con_barra(fr, self._locale_txt).grid(row=1, column=1, sticky="ns", pady=(4, 0))
        nb.add(fr, text=f" {tr('lab.tab.local')} ")
        self.mostra_locale()

    def mostra_locale(self):
        t = lab.tavola_locale()
        tipi = dict(t.tipi)
        righe = [tr("lab.local.intro"), "",
                 "  P \\ Q  " + " ".join(f"{q:>4}" for q in t.ordine)]
        for p, riga in zip(t.ordine, t.celle):
            righe.append(f"  {p} ({tipi[p]}) " + " ".join(f"{c:>4}" for c in riga))
        righe += ["", tr("lab.local.check", n=t.celle_concordi),
                  tr("lab.local.inverses",
                     pairs=", ".join(f"{p}⁻¹ = {q}" for p, q in t.inversi))]
        r = self._risultato_cb.get()
        righe += ["", tr("lab.local.decomp.title", r=r)]
        righe.append("   " + "   ".join(f"{p}∘{q}" for p, q in lab.decomposizioni_locali(r)))
        da, a = self._da_cb.get(), self._a_cb.get()
        righe += ["", tr("lab.local.transition.result", y=da, x=a,
                         r=lab.transizione_locale(da, a))]
        self._scrivi(self._locale_txt, righe)

    # ═══════════════════════════════ Grafi ═══════════════════════════════════
    def _costruisci_grafi(self, nb):
        fr = ttk.Frame(nb, padding=(4, 4))
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(1, weight=1)
        riga = ttk.Frame(fr)
        riga.grid(row=0, column=0, sticky="w")
        self._grafo_var = tk.StringVar(value="cayley_s3")
        self._grafi_rb = []
        for g in lab.grafi():
            rb = ttk.Radiobutton(riga, text=tr(f"lab.graph.{g.id}.name"), value=g.id,
                                 variable=self._grafo_var, command=self.mostra_grafo)
            rb.pack(side="left", padx=(0, 12))
            self._grafi_rb.append(rb)
        ttk.Label(riga, text=tr("lab.graph.path.label")).pack(side="left", padx=(8, 4))
        self._da_var, self._a_var = tk.IntVar(value=0), tk.IntVar(value=215)
        self._da_spin = ttk.Spinbox(riga, from_=0, to=215, width=4, textvariable=self._da_var)
        self._da_spin.pack(side="left")
        ttk.Label(riga, text="→").pack(side="left", padx=2)
        self._a_spin = ttk.Spinbox(riga, from_=0, to=215, width=4, textvariable=self._a_var)
        self._a_spin.pack(side="left")
        self._cammino_btn = ttk.Button(riga, text=tr("lab.graph.path.run"),
                                       command=self.mostra_grafo)
        self._cammino_btn.pack(side="left", padx=(6, 0))
        self._grafi_txt = self._testo(fr, 11)
        self._grafi_txt.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self._con_barra(fr, self._grafi_txt).grid(row=1, column=1, sticky="ns", pady=(4, 0))
        nb.add(fr, text=f" {tr('lab.tab.graphs')} ")
        self.mostra_grafo()

    def _nome_vertice(self, g, v):
        if g.dominio is Dominio.S3:
            return g.vertici[v]
        return f"#{v}"

    def mostra_grafo(self):
        g = lab.grafo(self._grafo_var.get())
        righe = [tr(f"lab.graph.{g.id}.meaning"), "",
                 tr("lab.graph.declaration", vertices=len(g.vertici), edges=len(g.archi),
                    domain=_dominio(g.dominio),
                    orientation=tr("lab.graph.directed" if g.orientato else "lab.graph.undirected"),
                    degree=", ".join(map(str, g.gradi)), diameter=g.diametro,
                    distribution=", ".join(f"{k}: {n}" for k, n in enumerate(g.distribuzione)),
                    root=self._nome_vertice(g, g.radice))]
        abilita = "normal" if g.dominio is Dominio.H else "disabled"
        for w in (self._da_spin, self._a_spin, self._cammino_btn):
            w.configure(state=abilita)
        if g.dominio is Dominio.H:
            try:
                da, a = int(self._da_var.get()), int(self._a_var.get())
            except (tk.TclError, ValueError):
                da, a = -1, -1
            if 0 <= da <= 215 and 0 <= a <= 215:
                c = lab.cammino(g, da, a)
                passi = " → ".join(f"#{n} {'·'.join(gr.mescolamenti_da_numero(n))}" for n in c)
                righe += ["", tr("lab.graph.path.result", length=len(c) - 1), "  " + passi]
            else:
                righe += ["", tr("lab.graph.path.invalid")]
        righe += ["", tr("lab.graph.adjacency")]
        adj = g.adiacenza
        for v in range(len(g.vertici)):             # alternativa testuale completa
            righe.append(f"  {self._nome_vertice(g, v)}: "
                         + ", ".join(self._nome_vertice(g, w) for w in adj[v]))
        self._scrivi(self._grafi_txt, righe)


def _sigla(t):
    return {tuple(v): k for k, v in gr.MESCOLAMENTO.items()}.get(tuple(t), "?")
