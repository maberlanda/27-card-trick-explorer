"""Sessione, cronologia, undo/redo e successione L90 (compartimento J).

`SessioneMixin` collega le viste esistenti a `services.sessione.SessioneLavoro`:

* **cattura** — le viste chiamano un solo punto (`_sessione_nota`) dopo una
  modifica scientifica (Explorer calcolato, sequenza del Simulatore, modalita'
  della Pratica, «Usa come T corrente» della Tavola, analisi del
  Riconoscimento, verifica del Laboratorio). Focus, ridimensionamenti,
  livello e schede non passano di qui: non sono eventi;
* **applicazione** — undo, redo e caricamento riportano nelle viste lo stato
  scientifico, strumento per strumento, solo dove e' cambiato; durante
  l'applicazione la cattura e' sospesa, cosi' non nascono eventi fantasma.

`SessioneDialog` e' la finestra «Esperimento e cronologia»: stato
dell'esperimento, annotazioni, file, undo/redo, elenco degli eventi e la
successione di Procedure (L90) con replay. Solo widget testuali, nessun
Canvas. Undo non tocca mai i file esportati.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..core import gioco_reale as gr
from ..services import archivio, esperimento as E
from ..services import tabellone as tb
from ..services.procedure import ProceduraGioco
from ..services.sessione import SessioneLavoro
from ..services.successione import Successione
from . import livelli as _livelli
from .i18n import tr

_RADICE = Path(__file__).resolve().parents[2]


def fonti_disponibili():
    """Provenienza: hash dei PDF solo se sono presenti accanto al programma (DP12 aperta)."""
    return (E.fonte("LIBRO_MAIN.pdf", "libro", _RADICE / "LIBRO_MAIN.pdf"),
            E.fonte("Articolo.pdf", "articolo", _RADICE / "Articolo.pdf"))


def _procedura_di_riga(numero):
    return E.procedura_in_dati(ProceduraGioco(tuple(gr.mescolamenti_da_numero(numero))))


class SessioneMixin:
    """Da mescolare in App: richiede _simulator_frame, _tavola_frame, ecc."""

    # ── stato ────────────────────────────────────────────────────────────────
    def _sessione_init(self):
        self._sessione = SessioneLavoro()
        self._sessione_applicando = False
        self._sessione_dialog = None

    def _sessione_collega(self):
        """Dopo la costruzione delle schede: aggancia le viste alla sessione."""
        sim = getattr(self, "_simulator_frame", None)
        if sim is not None:
            sim.on_stato = lambda: self._sessione_nota("simulatore")
        ric = getattr(self, "_riconoscimento", None)
        if ric is not None:
            ric.on_stato = lambda pi: self._sessione_nota("riconoscimento", pi)
        lab = getattr(self, "_laboratorio", None)
        if lab is not None:
            lab.on_stato = lambda pid, dom: self._sessione_nota("laboratorio", (pid, dom))

    # ── cattura ──────────────────────────────────────────────────────────────
    def _sessione_leggi(self, strumento, dato=None):
        """L'input scientifico corrente di uno strumento (None se non c'e')."""
        if strumento == "explorer":
            testo = self._explorer_entry.get("1.0", "end-1c").strip()
            return {"testo": testo} if testo else None
        if strumento == "simulatore":
            sim = self._simulator_frame
            if getattr(sim, "_sessione", None) is None:
                return None
            ses = sim._sessione
            fissa = getattr(sim, "_disposizione_fissa", None)
            return {"carta": int(ses.carta), "bersaglio": int(ses.bersaglio),
                    "disposizione_fissata": fissa,
                    "modalita_pratica": sim._p_modo_var.get()}
        if strumento == "tavola":
            numero = tb.numero_di(tuple(dato))
            return None if numero is None else _procedura_di_riga(numero)
        if strumento == "riconoscimento":
            return {"T": [int(x) for x in dato]}
        if strumento == "laboratorio":
            return {"proprieta": dato[0], "dominio": dato[1]}
        if strumento == "successione":
            return {"procedure": [E.procedura_in_dati(p) for p in dato.procedure],
                    "mazzo_iniziale": None, "generatore": None} if dato.lunghezza else None
        raise KeyError(strumento)

    def _sessione_nota(self, strumento, dato=None):
        if getattr(self, "_sessione_applicando", False) or not hasattr(self, "_sessione"):
            return None
        try:
            inp = self._sessione_leggi(strumento, dato)
        except (tk.TclError, AttributeError, ValueError):
            return None
        evento = self._sessione.registra(strumento, inp)
        self._sessione_aggiorna_dialog()
        return evento

    # ── applicazione ────────────────────────────────────────────────────────
    def _sessione_applica(self, prima, dopo):
        """Porta nelle viste gli strumenti il cui input e' cambiato."""
        self._sessione_applicando = True
        try:
            for strumento in E.STRUMENTI:
                vecchio = (prima or {}).get(strumento)
                nuovo = (dopo or {}).get(strumento)
                if vecchio != nuovo:
                    self._sessione_applica_strumento(strumento, nuovo)
        finally:
            self._sessione_applicando = False
        self._sessione_aggiorna_dialog()

    def _sessione_applica_strumento(self, strumento, inp):
        if strumento == "explorer":
            if inp is None:
                self._explorer_clear()
            else:
                self._explorer_entry.delete("1.0", "end")
                self._explorer_entry.insert("1.0", inp["testo"])
                self._explorer_calc()
        elif strumento == "simulatore":
            sim = self._simulator_frame
            if inp is None:
                sim.togli_disposizione_fissa()
                sim.reset()
                return
            sim._card_var.set(inp["carta"])
            sim._target_var.set(inp["bersaglio"])
            sim._p_modo_var.set(inp["modalita_pratica"])
            if inp["disposizione_fissata"] is None:
                sim.togli_disposizione_fissa()
            else:
                sim.imposta_disposizione_fissa(inp["disposizione_fissata"])
            sim._find_sequence()
            sim._su_modo()
        elif strumento == "tavola":
            if inp is not None:
                p = E.procedura_da_dati(inp)
                self._tavola_frame.vai_alla_riga(p.numero_tavola)
        elif strumento == "riconoscimento":
            ric = self._riconoscimento
            ric._modo_var.set("perm")
            ric._su_modo()
            ric._imposta(ric._campo1, "" if inp is None else " ".join(map(str, inp["T"])))
            if inp is not None:
                ric.analizza()
        elif strumento == "laboratorio":
            if inp is not None:
                lab = self._laboratorio
                from ..services import laboratorio as _lab
                indice = [p.id for p in _lab.CATALOGO].index(inp["proprieta"])
                lab._elenco.selection_clear(0, "end")
                lab._elenco.selection_set(indice)
                lab._su_proprieta()
                lab._dominio_var.set(inp["dominio"])
                lab.verifica()
        elif strumento == "successione":
            pass                                   # vive nella finestra della sessione

    def _sessione_annulla(self):
        prima = self._sessione.stato_scientifico
        if self._sessione.cronologia.annulla() is not None:
            self._sessione_applica(prima, self._sessione.stato_scientifico)

    def _sessione_ripristina(self):
        prima = self._sessione.stato_scientifico
        if self._sessione.cronologia.ripristina() is not None:
            self._sessione_applica(prima, self._sessione.stato_scientifico)

    # ── file ─────────────────────────────────────────────────────────────────
    def _sessione_presentazione(self):
        scheda = next((k for k, w in self._schede.items() if str(w) == self._nb.select()), None)
        sotto = None
        if scheda == "explorer":
            sel = self._explorer_nb.select()
            sotto = next((k for k, w in self._sottoschede_explorer.items() if str(w) == sel), None)
        self._sessione.imposta_presentazione(_livelli.normalizza(self._livello), scheda, sotto)

    def _sessione_salva(self, percorso):
        self._sessione_presentazione()
        self._sessione.salva(percorso, fonti_disponibili())
        self._sessione_aggiorna_dialog()

    def _sessione_conferma_sostituzione(self):
        if not self._sessione.modificata:
            return True
        return messagebox.askyesno(tr("session.confirm.title"), tr("session.confirm.discard"),
                                   parent=self)

    def _sessione_adotta(self, nuova):
        """Commit logico unico: nuova sessione + stato nelle viste + presentazione."""
        prima = self._sessione.stato_scientifico
        self._sessione = nuova
        self._sessione_applica(prima, nuova.stato_scientifico)
        pres = nuova.presentazione
        if pres:
            self._imposta_livello(pres["livello"])
            if pres["scheda"] and self._scheda_disponibile(pres["scheda"]):
                self._seleziona_scheda(pres["scheda"])
        self._sessione_aggiorna_dialog()

    def _sessione_carica(self, percorso):
        nuova, rapporto = SessioneLavoro.carica(percorso)
        if nuova is not None:
            self._sessione_adotta(nuova)
        return rapporto

    def _sessione_nuova(self):
        self._sessione_adotta(SessioneLavoro())

    def _sessione_aggiorna_dialog(self):
        d = getattr(self, "_sessione_dialog", None)
        if d is not None and d.winfo_exists():
            d.aggiorna()

    def _open_sessione(self):
        d = getattr(self, "_sessione_dialog", None)
        if d is not None and d.winfo_exists():
            d.lift()
            d.focus_set()
            return d
        self._sessione_dialog = SessioneDialog(self)
        return self._sessione_dialog


def _mazzo_breve(v, n=9):
    return " ".join(str(x) for x in v[:n]) + " …"


class SessioneDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title(tr("session.title"))
        self.geometry("980x600")
        self.minsize(760, 480)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._stato_lbl = ttk.Label(self, text="", font=("Segoe UI", 10, "bold"),
                                    foreground="#1F4E79", wraplength=940, justify="left")
        self._stato_lbl.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self._schede = nb
        self._costruisci_esperimento(nb)
        self._costruisci_cronologia(nb)
        self._costruisci_successione(nb)
        self.bind("<Control-z>", lambda e: self.annulla())
        self.bind("<Control-y>", lambda e: self.ripristina())
        self._passo = 0
        self.aggiorna()

    # ── esperimento ─────────────────────────────────────────────────────────
    def _costruisci_esperimento(self, nb):
        fr = ttk.Frame(nb, padding=8)
        fr.columnconfigure(1, weight=1)
        ttk.Label(fr, text=tr("session.field.title")).grid(row=0, column=0, sticky="w")
        self._titolo_var = tk.StringVar()
        self._titolo = ttk.Entry(fr, textvariable=self._titolo_var)
        self._titolo.grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(fr, text=tr("session.field.note")).grid(row=1, column=0, sticky="nw")
        self._nota = tk.Text(fr, height=5, wrap="word", font=("Segoe UI", 10))
        self._nota.grid(row=1, column=1, sticky="nsew", pady=2)
        self._nota.bind("<Tab>", lambda e: (e.widget.tk_focusNext().focus_set(), "break")[1])
        self._applica_ann = ttk.Button(fr, text=tr("session.apply_annotations"),
                                       command=self.applica_annotazioni)
        self._applica_ann.grid(row=2, column=1, sticky="w", pady=(2, 8))
        comandi = ttk.Frame(fr)
        comandi.grid(row=3, column=0, columnspan=2, sticky="w")
        self._pulsanti = {}
        for chiave, azione in (("new", self.nuova), ("open", self.apri), ("save", self.salva),
                               ("save_as", self.salva_come), ("verify", self.verifica),
                               ("undo", self.annulla), ("redo", self.ripristina)):
            b = ttk.Button(comandi, text=tr(f"session.button.{chiave}"), command=azione)
            b.pack(side="left", padx=(0, 6))
            self._pulsanti[chiave] = b
        self._esito = tk.Text(fr, height=8, wrap="word", font=("Consolas", 9), relief="flat",
                              background="#FAFCFF", state="disabled", takefocus=True)
        self._esito.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        fr.rowconfigure(4, weight=1)
        nb.add(fr, text=f" {tr('session.tab.experiment')} ")

    def _scrivi(self, testo, righe):
        testo.configure(state="normal")
        testo.delete("1.0", "end")
        testo.insert("1.0", "\n".join(righe))
        testo.configure(state="disabled")

    def aggiorna(self):
        s = self.app._sessione
        c = s.cronologia
        titolo = s.annotazioni["titolo"] or s.id[:8]
        self._stato_lbl.configure(text=tr(
            "session.status", title=titolo, path=s.percorso or "—", revision=c.revisione,
            saved=tr("session.state.dirty") if s.modificata else tr("session.state.clean"),
            events=c.numero_eventi,
            undo=tr("session.yes") if c.puo_annullare() else tr("session.no"),
            redo=tr("session.yes") if c.puo_ripristinare() else tr("session.no")))
        self._pulsanti["undo"].state(["!disabled"] if c.puo_annullare() else ["disabled"])
        self._pulsanti["redo"].state(["!disabled"] if c.puo_ripristinare() else ["disabled"])
        if self.focus_get() not in (self._titolo, self._nota):
            self._titolo_var.set(s.annotazioni["titolo"])
            self._nota.delete("1.0", "end")
            self._nota.insert("1.0", s.annotazioni["nota"])
        self._aggiorna_cronologia()
        self._aggiorna_successione()

    def applica_annotazioni(self):
        self.app._sessione.imposta_annotazioni(self._titolo_var.get(),
                                               self._nota.get("1.0", "end-1c"))
        self.aggiorna()

    def annulla(self):
        self.app._sessione_annulla()
        self.aggiorna()

    def ripristina(self):
        self.app._sessione_ripristina()
        self.aggiorna()

    def nuova(self):
        if self.app._sessione_conferma_sostituzione():
            self.app._sessione_nuova()
            self._passo = 0
            self.aggiorna()

    def apri(self, percorso=None):
        if not self.app._sessione_conferma_sostituzione():
            return None
        percorso = percorso or filedialog.askopenfilename(
            parent=self, filetypes=[(tr("session.filetype"), "*.json")])
        if not percorso:
            return None
        r = self.app._sessione_carica(percorso)
        self.mostra_rapporto(r)
        self._passo = 0
        self.aggiorna()
        return r

    def salva(self):
        if self.app._sessione.percorso:
            return self.salva_come(self.app._sessione.percorso)
        return self.salva_come()

    def salva_come(self, percorso=None):
        percorso = percorso or filedialog.asksaveasfilename(
            parent=self, defaultextension=".json",
            filetypes=[(tr("session.filetype"), "*.json")])
        if not percorso:
            return None
        try:
            self.app._sessione_salva(percorso)
        except OSError as e:
            self._scrivi(self._esito, [tr("session.error.save", error=str(e))])
            return None
        self._scrivi(self._esito, [tr("session.saved", path=percorso)])
        self.aggiorna()
        return percorso

    def verifica(self):
        doc = self.app._sessione.documento(fonti_disponibili())
        self.mostra_rapporto(E.verifica_testo(E.json_canonico(doc)))

    def mostra_rapporto(self, r):
        righe = [tr("session.report", status=r.stato.value,
                    meaning=tr(f"session.state.{r.stato.value.lower()}"), code=r.codice)]
        for d in r.diagnosi[:20]:
            righe.append(f"  {d.voce} · {d.campo}" + (
                "" if d.registrato is None and d.ricalcolato is None
                else f": {d.registrato!r} ≠ {d.ricalcolato!r}"))
        self._scrivi(self._esito, righe)

    # ── cronologia ──────────────────────────────────────────────────────────
    def _costruisci_cronologia(self, nb):
        fr = ttk.Frame(nb, padding=8)
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(1, weight=1)
        ttk.Label(fr, text=tr("session.history.intro"), wraplength=900,
                  justify="left").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._eventi = tk.Listbox(fr, height=14, font=("Consolas", 9), exportselection=False)
        self._eventi.grid(row=1, column=0, sticky="nsew")
        sb = ttk.Scrollbar(fr, orient="vertical", command=self._eventi.yview)
        self._eventi.configure(yscrollcommand=sb.set)
        sb.grid(row=1, column=1, sticky="ns")
        self._esporta_cr = ttk.Button(fr, text=tr("session.export_csv"),
                                      command=self.esporta_cronologia)
        self._esporta_cr.grid(row=2, column=0, sticky="w", pady=(6, 0))
        nb.add(fr, text=f" {tr('session.tab.history')} ")

    def _aggiorna_cronologia(self):
        c = self.app._sessione.cronologia
        self._eventi.delete(0, "end")
        for e in c.eventi:
            self._eventi.insert("end", tr("session.event", id=e["id"], kind=e["tipo"],
                                          origin=e["origine"], revision=e["revisione"]))
        for e in c._annullati[::-1]:
            self._eventi.insert("end", "↷ " + tr("session.event", id=e["id"], kind=e["tipo"],
                                                 origin=e["origine"], revision=e["revisione"]))
        for e in c.esterni:
            self._eventi.insert("end", "⤓ " + tr("session.event.external", id=e["id"],
                                                 kind=e["tipo"], name=e["dati"].get("nome", "")))

    def _esporta(self, contenuto, intest, righe, percorso=None):
        percorso = percorso or filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not percorso:
            return None
        try:
            m = archivio.scrivi_csv(percorso, contenuto, intest, righe, fonti_disponibili())
        except OSError as e:
            self.app._sessione.registra_export("csv", Path(percorso).name, None, False)
            self._scrivi(self._esito, [tr("session.error.save", error=str(e))])
            return None
        self.app._sessione.registra_export("csv", Path(percorso).name, m["sha256"], True)
        self.aggiorna()
        return m

    def esporta_cronologia(self, percorso=None):
        c = self.app._sessione.cronologia
        return self._esporta("cronologia", *archivio.righe_cronologia(
            list(c.eventi) + list(c.esterni)), percorso)

    # ── successione L90 ─────────────────────────────────────────────────────
    def _costruisci_successione(self, nb):
        fr = ttk.Frame(nb, padding=8)
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(1, weight=1)
        riga = ttk.Frame(fr)
        riga.grid(row=0, column=0, sticky="w")
        ttk.Label(riga, text=tr("sequence.procedure")).pack(side="left", padx=(0, 4))
        self._sigle = []
        for i in range(3):
            cb = ttk.Combobox(riga, state="readonly", width=5, values=list(gr.SIGLE))
            cb.current(0)
            cb.pack(side="left", padx=1)
            self._sigle.append(cb)
        self._eps = []
        for i in range(3):
            v = tk.IntVar(value=0)
            ttk.Checkbutton(riga, text=f"ε{i + 1}", variable=v).pack(side="left", padx=1)
            self._eps.append(v)
        self._btn = {}
        for chiave, azione in (("add", self.aggiungi), ("remove", self.rimuovi),
                               ("up", lambda: self.sposta(-1)), ("down", lambda: self.sposta(1))):
            b = ttk.Button(riga, text=tr(f"sequence.button.{chiave}"), command=azione)
            b.pack(side="left", padx=(6, 0))
            self._btn[chiave] = b
        colonne = ("passo", "procedura", "riga", "cumulativo", "disposizione")
        self._albero = ttk.Treeview(fr, columns=colonne, show="headings", height=8,
                                    selectmode="browse")
        larghezze = (50, 240, 120, 150, 300)
        for c, w in zip(colonne, larghezze):
            self._albero.heading(c, text=tr(f"sequence.col.{c}"))
            self._albero.column(c, width=w, stretch=(c == "disposizione"))
        self._albero.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        sb = ttk.Scrollbar(fr, orient="vertical", command=self._albero.yview)
        self._albero.configure(yscrollcommand=sb.set)
        sb.grid(row=1, column=1, sticky="ns", pady=(6, 0))
        rep = ttk.Frame(fr)
        rep.grid(row=2, column=0, sticky="w", pady=(6, 0))
        for chiave, azione in (("back", lambda: self.replay(-1)),
                               ("forward", lambda: self.replay(1)),
                               ("return", self.ritorno_compresso),
                               ("export", self.esporta_successione)):
            b = ttk.Button(rep, text=tr(f"sequence.button.{chiave}"), command=azione)
            b.pack(side="left", padx=(0, 6))
            self._btn[chiave] = b
        self._tappa_lbl = ttk.Label(rep, text="")
        self._tappa_lbl.pack(side="left", padx=(8, 0))
        self._replay = tk.Text(fr, height=6, wrap="word", font=("Consolas", 9),
                               relief="flat", background="#FAFCFF", state="disabled",
                               takefocus=True)
        self._replay.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        nb.add(fr, text=f" {tr('session.tab.sequence')} ")

    def successione(self) -> Successione:
        inp = self.app._sessione.input_di("successione")
        if inp is None:
            return Successione()
        return Successione(tuple(E.procedura_da_dati(d) for d in inp["procedure"]))

    def _registra(self, s):
        self.app._sessione_nota("successione", s)
        self.aggiorna()

    def aggiungi(self, procedura=None):
        if procedura is None:
            procedura = ProceduraGioco(tuple(cb.get() for cb in self._sigle),
                                       tuple(v.get() for v in self._eps))
        self._registra(self.successione().aggiungi(procedura))

    def _selezionato(self):
        sel = self._albero.selection()
        return int(sel[0]) if sel else None

    def rimuovi(self):
        i = self._selezionato()
        if i is not None:
            self._registra(self.successione().rimuovi(i))

    def sposta(self, verso):
        i, s = self._selezionato(), self.successione()
        if i is not None and 0 <= i + verso < s.lunghezza:
            self._registra(s.sposta(i, i + verso))
            self._albero.selection_set(str(i + verso))

    def _aggiorna_successione(self):
        s = self.successione()
        self._albero.delete(*self._albero.get_children())
        for p in s.passi():
            proc = " ".join(p.procedura.mescolamenti) + " · ε=" + \
                "".join(map(str, p.procedura.rovesciamenti))
            self._albero.insert("", "end", iid=str(p.indice - 1), values=(
                p.indice, proc, f"#{p.numero_tavola}", f"C{p.indice} = #{p.numero_cumulativo}",
                _mazzo_breve(p.disposizione)))
        self._passo = min(self._passo, s.lunghezza)
        self._mostra_tappa(s)

    def _mostra_tappa(self, s):
        v = s.disposizioni()[self._passo]
        self._tappa_lbl.configure(text=tr("sequence.stage", k=self._passo, n=s.lunghezza))
        self._scrivi(self._replay, [tr("sequence.deck", k=self._passo),
                                    " ".join(map(str, v))])

    def replay(self, verso):
        s = self.successione()
        self._passo = max(0, min(s.lunghezza, self._passo + verso))
        self._mostra_tappa(s)

    def ritorno_compresso(self):
        s = self.successione()
        r = s.ritorno_procedura()
        self._passo = 0
        self._mostra_tappa(s)
        self._scrivi(self._replay, [
            tr("sequence.return", n=s.lunghezza, stages=3 * s.lunghezza,
               codes=" ".join(r.mescolamenti), row=r.numero_tavola),
            tr("sequence.origin_vs_path"),
            " ".join(map(str, s.ritorno_compresso()))])
        return r

    def esporta_successione(self, percorso=None):
        return self._esporta("successione", *archivio.righe_successione(self.successione()),
                             percorso)


