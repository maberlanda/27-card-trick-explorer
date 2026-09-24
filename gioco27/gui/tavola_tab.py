"""
Tab "📚 Tavola 216" — la tavola delle disposizioni semplici del libro.

Per ciascuna delle 216 sequenze di tre mescolamenti (senza rovesciamenti):
numero #, mescolamenti, impilamenti (gesto fisico), posizioni finali dei
tre Assi, periodo, punti fissi, tipo ciclico, parità, auto-inversa.

Strumenti:
  • filtro live su qualunque colonna;
  • ricostruzione del tabellone dalle posizioni degli Assi;
  • dettaglio T / T⁻¹ con doppio clic;
  • esportazione CSV.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

from ..core import gioco_reale as gr
from ..core.parallel import atomic_write
from ..services import tabellone as _tb
from ..services.procedure import ProceduraGioco
from .i18n import tr
from .pannello_ternario import PannelloTernario


class TavolaFrame(ttk.Frame):

    _COLS = (
        ("num",  "#",            46),
        ("mesc", "Mescolamenti", 130),
        ("imp",  "Impilamenti",  130),
        ("assi", "Assi (A♠ A♣ A♥)", 120),
        ("per",  "Periodo",      64),
        ("fix",  "Punti fissi",  80),
        ("tipo", "Tipo ciclico", 150),
        ("par",  "Parità",       60),
        ("auto", "Auto-inversa", 96),
    )
    _COL_KEYS = {
        "num": "table.col.number",
        "mesc": "table.col.shuffles",
        "imp": "table.col.stackings",
        "assi": "table.col.aces",
        "per": "table.col.period",
        "fix": "table.col.fixed_points",
        "tipo": "table.col.cycle_type",
        "par": "table.col.parity",
        "auto": "table.col.self_inverse",
    }

    def __init__(self, parent, on_usa_T=None, on_apri_explorer=None,
                 on_apri_cicli=None, scheda_disponibile=None, on_pratica=None,
                 **kw):
        """I2 (D-I2-7): le azioni verso le altre viste sono callback dell'App.

        on_usa_T(perm)            pubblica T come T corrente (esplicito)
        on_apri_explorer(espr)    porta un'espressione nell'Explorer
        on_apri_cicli(perm)       pubblica T e mostra i Cicli
        scheda_disponibile(k)     True se la scheda k e' visibile nel livello
        on_pratica(numero)        I3 (D-I3-7): pratica con il piano fissato
        """
        super().__init__(parent, **kw)
        self._on_usa_T = on_usa_T
        self._on_apri_explorer = on_apri_explorer
        self._on_apri_cicli = on_apri_cicli
        self._on_pratica = on_pratica
        self._scheda_disponibile = scheda_disponibile
        self._righe = gr.tavola_216()
        self._build_ui()
        self._popola()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        top = ttk.Frame(self, padding=(8, 6))
        top.pack(fill="x")

        ttk.Label(top, text=tr("table.filter")).pack(side="left")
        self._filtro_var = tk.StringVar()
        ent = ttk.Entry(top, textvariable=self._filtro_var, width=24)
        ent.pack(side="left", padx=(4, 12))
        self._filtro_var.trace_add("write", lambda *a: self._popola())
        ttk.Label(top, foreground="#666",
                  text=tr("table.search_hint")).pack(side="left")

        ttk.Button(top, text=f"⬇  {tr('table.export_csv')}",
                   command=self._esporta_csv).pack(side="right", padx=4)

        # ── ricostruzione dagli assi ──
        rec = ttk.LabelFrame(
            self,
            text=f"  {tr('table.reconstruct_axes')}  "
                 f"{tr('table.positions_note')}  ",
            padding=(8, 6))
        rec.pack(fill="x", padx=8, pady=(0, 4))
        self._asso_vars = []
        for key in ("table.ace_spades", "table.ace_clubs", "table.ace_hearts"):
            lbl = tr(key)
            ttk.Label(rec, text=lbl).pack(side="left", padx=(8, 2))
            v = tk.StringVar()
            ttk.Spinbox(rec, from_=0, to=26, width=4,
                        textvariable=v).pack(side="left")
            self._asso_vars.append(v)
        ttk.Button(rec, text=f"🔎  {tr('table.find_arrangement')}",
                   command=self._ricostruisci).pack(side="left", padx=12)
        self._rec_lbl = ttk.Label(rec, text="", foreground="#00427e")
        self._rec_lbl.pack(side="left", padx=6)

        # ── tabella a sinistra, pannello ternario a destra (I2, D-I2-2) ──
        self._divisore = ttk.Panedwindow(self, orient="horizontal")
        self._divisore.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        # La tabella non impone la propria larghezza (876 px di colonne): a
        # 1280×720 cede spazio al pannello e scorre con la sua barra (H2).
        wrap = ttk.Frame(self._divisore, width=500, height=300)
        wrap.grid_propagate(False)
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        self._divisore.add(wrap, weight=1)
        self.pannello = PannelloTernario(self._divisore,
                                         on_vai_alla_riga=self.vai_alla_riga)
        self._divisore.add(self.pannello, weight=1)
        cols = [c for c, _, _ in self._COLS]
        tv = ttk.Treeview(wrap, columns=cols, show="headings",
                          selectmode="browse")
        for c, testo, w in self._COLS:
            tv.heading(c, text=tr(self._COL_KEYS[c]))
            tv.column(c, width=w, anchor="center", stretch=(c in ("mesc", "imp", "tipo")))
        vs = ttk.Scrollbar(wrap, orient="vertical", command=tv.yview)
        hs = ttk.Scrollbar(wrap, orient="horizontal", command=tv.xview)
        tv.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tv.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        tv.bind("<Double-1>", self._dettaglio)
        # I2: la selezione aggiorna soltanto il pannello; non pubblica T (D-I2-7)
        tv.bind("<<TreeviewSelect>>", self._su_selezione)

        # ── collegamenti espliciti verso le altre viste (I2d) ──
        nav = ttk.Frame(wrap)
        nav.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self._btn_usa_T = ttk.Button(nav, text=tr("nav.use_as_current"),
                                     command=self._usa_come_T, state="disabled")
        self._btn_explorer = ttk.Button(nav, text=tr("nav.open_explorer"),
                                        command=self._apri_explorer,
                                        state="disabled")
        self._btn_cicli = ttk.Button(nav, text=tr("nav.open_cycles"),
                                     command=self._apri_cicli, state="disabled")
        self._btn_pratica = ttk.Button(nav, text=tr("nav.practice_disposition"),
                                       command=self._pratica, state="disabled")
        self._btn_usa_T.pack(side="left")
        self._btn_pratica.pack(side="left", padx=(6, 0))
        self._esito_navigazione = ttk.Label(nav, text=tr("nav.select_row"),
                                            foreground="#555", wraplength=360)
        self._nav = nav
        self.aggiorna_navigazione()
        tv.tag_configure("pari", background="#f4f9f4")
        tv.tag_configure("evid", background="#fff2c4")
        self._tv = tv

        self._status = ttk.Label(self, text="", padding=(10, 2),
                                 foreground="#555")
        self._status.pack(fill="x")

    # ── dati ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _valori(r):
        return (
            r["numero"],
            " ".join(r["mescolamenti"]),
            " ".join(r["impilamenti"]),
            "{:2d} {:2d} {:2d}".format(*r["assi"]),
            r["periodo"],
            r["punti_fissi"],
            "·".join(str(l) for l in r["tipo_ciclo"] if l > 1) or tr("table.identity"),
            tr("table.even") if r["parita"] > 0 else tr("table.odd"),
            tr("table.yes") if r["autoinversa"] else "",
        )

    def _popola(self, evidenzia=None):
        f = self._filtro_var.get().strip().lower()
        tv = self._tv
        tv.delete(*tv.get_children())
        n_vis = 0
        for r in self._righe:
            vals = self._valori(r)
            if f and f not in " ".join(str(v).lower() for v in vals):
                continue
            tags = []
            if evidenzia is not None and r["numero"] == evidenzia:
                tags.append("evid")
            elif n_vis % 2:
                tags.append("pari")
            tv.insert("", "end", iid=str(r["numero"]), values=vals,
                      tags=tuple(tags))
            n_vis += 1
        self._status.configure(text=tr("table.status_shown", visible=n_vis))

    # ── azioni ────────────────────────────────────────────────────────────────

    def _su_selezione(self, _ev=None):
        sel = self._tv.selection()
        if sel:
            self.pannello.mostra_disposizione(int(sel[0]))
            for b in (self._btn_usa_T, self._btn_explorer, self._btn_cicli,
                      self._btn_pratica):
                b.state(["!disabled"])

    def aggiorna_navigazione(self):
        """Mostra solo le azioni verso schede disponibili nel livello (DP7 invariata)."""
        for b in (self._btn_explorer, self._btn_cicli):
            b.pack_forget()
        self._esito_navigazione.pack_forget()
        for chiave, btn, cb in (("explorer", self._btn_explorer,
                                 self._on_apri_explorer),
                                ("cicli", self._btn_cicli, self._on_apri_cicli)):
            if cb is not None and (self._scheda_disponibile is None
                                   or self._scheda_disponibile(chiave)):
                btn.pack(side="left", padx=(6, 0))
        self._esito_navigazione.pack(side="left", padx=8)

    def _T_selezionata(self):
        t = self.pannello.tabellone_corrente
        return None if t is None else list(t.destinazioni)

    def _usa_come_T(self):
        T = self._T_selezionata()
        if T is None or self._on_usa_T is None:
            return
        self._on_usa_T(T)
        self._esito_navigazione.configure(
            text=tr("nav.published", number=self.pannello.numero))

    def _apri_explorer(self):
        if self.pannello.numero is None or self._on_apri_explorer is None:
            return
        procedura = ProceduraGioco.da_identificatore(self.pannello.numero, 0)
        self._on_apri_explorer(_tb.espressione_per_explorer(procedura))

    def _pratica(self):
        """I3e: la riga diventa il piano fisso della Pratica (azione esplicita)."""
        if self.pannello.numero is not None and self._on_pratica is not None:
            self._on_pratica(self.pannello.numero)

    def _apri_cicli(self):
        T = self._T_selezionata()
        if T is not None and self._on_apri_cicli is not None:
            self._on_apri_cicli(T)

    def vai_alla_riga(self, numero):
        """Porta in vista e seleziona la riga `numero`, togliendo il filtro."""
        numero = int(numero)
        if self._filtro_var.get():
            self._filtro_var.set("")
        self._popola(evidenzia=numero)
        self._tv.see(str(numero))
        self._tv.selection_set(str(numero))
        self._tv.focus(str(numero))
        self.pannello.mostra_disposizione(numero)

    def _ricostruisci(self):
        try:
            pos = [int(v.get()) for v in self._asso_vars]
        except ValueError:
            messagebox.showwarning(tr("table.reconstruct_axes"),
                                    tr("table.warning_axes"))
            return
        try:
            mesc, num = gr.tabellone_da_assi(*pos)
        except ValueError as e:
            self._rec_lbl.configure(
                text=f"✗ {tr('table.no_arrangement_status')}",
                foreground="#aa0000")
            messagebox.showinfo(
                tr("table.reconstruct_title"),
                tr("table.no_arrangement", detail=e))
            return
        self._rec_lbl.configure(
            text=f"→ #{num}:  {' '.join(mesc)}", foreground="#006400")
        self._filtro_var.set("")
        self._popola(evidenzia=num)
        try:
            self._tv.see(str(num))
            self._tv.selection_set(str(num))
        except tk.TclError:
            pass

    def _dettaglio(self, _ev=None):
        sel = self._tv.selection()
        if not sel:
            return
        r = self._righe[int(sel[0])]
        win = tk.Toplevel(self)
        win.title(tr("table.detail_title", number=r["numero"]))
        txt = tk.Text(win, width=88, height=24, font=("Consolas", 10),
                      wrap="none", padx=10, pady=8)
        txt.pack(fill="both", expand=True)

        def riga27(nome, arr):
            testa = "  ".join(f"{i:2d}" for i in range(27))
            corpo = "  ".join(f"{v:2d}" for v in arr)
            return f"{nome}\n   n  {testa}\n      {corpo}\n\n"

        mesc, imp = r["mescolamenti"], r["impilamenti"]
        inversa = tr("table.detail.self_inverse" if r["autoinversa"]
                     else "table.detail.not_self_inverse")
        txt.insert("end",
            f"{tr('table.detail.heading', number=r['numero'])}\n"
            f"{'='*60}\n"
            f"{tr('table.detail.shuffles', codes=' '.join(mesc))}\n"
            f"{tr('table.detail.stackings', codes=' '.join(imp))}\n"
            f"{tr('table.detail.aces', spades=r['assi'][0], clubs=r['assi'][1], hearts=r['assi'][2])}\n"
            f"{tr('table.detail.period', period=r['periodo'], fixed=r['punti_fissi'], inverse=inversa)}\n\n")
        txt.insert("end", riga27(tr("table.detail.t"), r["T"]))
        txt.insert("end", riga27(tr("table.detail.t_inverse"), r["T_inv"]))
        txt.insert("end",
            tr("table.detail.board") + "\n" +
            "".join(tr("table.detail.board_row", row=i, shuffle=m, stacking=p) + "\n"
                    for i, (m, p) in enumerate(zip(mesc, imp), 1)))
        txt.configure(state="disabled")

    def _esporta_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="tavola_216.csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            # G2: pubblicazione atomica (temporaneo + os.replace).
            with atomic_write(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh, delimiter=";")
                w.writerow(["numero", "mesc_1", "mesc_2", "mesc_3",
                            "imp_1", "imp_2", "imp_3",
                            "asso_picche", "asso_fiori", "asso_cuori",
                            "periodo", "punti_fissi", "tipo_ciclico",
                            "parita", "autoinversa"] +
                           [f"T_{i}" for i in range(27)])
                for r in self._righe:
                    w.writerow([r["numero"], *r["mescolamenti"],
                                *r["impilamenti"], *r["assi"],
                                r["periodo"], r["punti_fissi"],
                                "-".join(map(str, r["tipo_ciclo"])),
                                r["parita"], int(r["autoinversa"])] +
                               list(r["T"]))
        except OSError as e:
            messagebox.showerror(tr("table.export_title"),
                                 tr("table.export_error", detail=e))
            return
        messagebox.showinfo(tr("table.export_title"),
                            tr("table.export_success", path=path))
