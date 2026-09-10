"""
Tab "🔄 Cicli e Ordine"

Mostra per la permutazione T corrente:
  - Ordine di T nel gruppo S_27 (mcm delle lunghezze dei cicli)
  - Decomposizione in cicli disgiunti (colorati)
  - Tabella: carta → posizione dopo k applicazioni di T (orbita)
  - Tipo di ciclo: quanti cicli di ogni lunghezza
"""
import tkinter as tk
from tkinter import ttk

from ..core.analysis import cycle_decomposition, order_of, cycle_type, orbit_of
from .i18n import tr

# Palette colori per i cicli (fino a 27 colori distinti)
_CYCLE_PALETTE = [
    "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
    "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
    "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF",
    "#AEC7E8", "#FFBB78", "#98DF8A", "#FF9896", "#C5B0D5",
    "#C49C94", "#F7B6D2",
]


class CyclesFrame(ttk.Frame):
    """
    Frame da inserire come tab nell'App principale.
    Richiede che l'App chiami  set_permutation(perm_27)  ogni volta
    che la permutazione T cambia.
    """

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._perm = None
        self._build_ui()

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # ── Intestazione ───────────────────────────────────────────────────
        hdr = ttk.Frame(self, padding=(10, 8, 10, 4))
        hdr.grid(row=0, column=0, sticky="ew")
        ttk.Label(hdr,
                  text=tr("cycles.title"),
                  font=("Segoe UI", 12, "bold"),
                  foreground="#1a3a5c").pack(side="left")
        self._hint = ttk.Label(hdr,
                               text=tr("cycles.hint"),
                               font=("Segoe UI", 9, "italic"),
                               foreground="#888")
        self._hint.pack(side="left", padx=10)

        # ── Pannello riepilogo ─────────────────────────────────────────────
        info_fr = ttk.LabelFrame(self, text=f" {tr('cycles.summary')} ",
                                 padding=(10, 6))
        info_fr.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        for i in range(6):
            info_fr.columnconfigure(i, weight=1)

        lbl = lambda text, col, bold=False: ttk.Label(
            info_fr, text=text,
            font=("Segoe UI", 10, "bold" if bold else "normal"))

        lbl(tr("cycles.order"), 0, bold=True).grid(row=0, column=0, sticky="w")
        self._order_var = tk.StringVar(value="—")
        ttk.Label(info_fr, textvariable=self._order_var,
                  font=("Courier New", 12, "bold"),
                  foreground="#1a5c1a").grid(row=0, column=1, sticky="w", padx=(4, 20))

        lbl(tr("cycles.count"), 2, bold=True).grid(row=0, column=2, sticky="w")
        self._ncycles_var = tk.StringVar(value="—")
        ttk.Label(info_fr, textvariable=self._ncycles_var,
                  font=("Courier New", 12, "bold"),
                  foreground="#1a3a5c").grid(row=0, column=3, sticky="w", padx=(4, 20))

        lbl(tr("cycles.type"), 4, bold=True).grid(row=0, column=4, sticky="w")
        self._type_var = tk.StringVar(value="—")
        ttk.Label(info_fr, textvariable=self._type_var,
                  font=("Courier New", 10),
                  foreground="#555").grid(row=0, column=5, sticky="w", padx=4)

        # ── Notebook interno: Cicli | Orbite ───────────────────────────────
        nb = ttk.Notebook(self)
        nb.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))

        self._cycles_tab  = ttk.Frame(nb)
        self._orbits_tab  = ttk.Frame(nb)
        nb.add(self._cycles_tab,
               text=f"  {tr('cycles.tab.disjoint')}  ")
        nb.add(self._orbits_tab,
               text=f"  {tr('cycles.tab.orbits')}  ")

        self._build_cycles_tab()
        self._build_orbits_tab()

    def _build_cycles_tab(self):
        fr = self._cycles_tab
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(1, weight=1)

        ttk.Label(fr,
                  text=tr("cycles.row_hint"),
                  font=("Segoe UI", 9, "italic"),
                  foreground="#666").grid(row=0, column=0, sticky="w", padx=8, pady=(6, 2))

        # Canvas scrollabile per i cicli
        cf = ttk.Frame(fr)
        cf.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        cf.columnconfigure(0, weight=1)
        cf.rowconfigure(0, weight=1)

        self._cycles_txt = tk.Text(
            cf, font=("Courier New", 10), state="disabled",
            wrap="none", background="#FAFBFC", relief="flat")
        vsb = ttk.Scrollbar(cf, orient="vertical",   command=self._cycles_txt.yview)
        hsb = ttk.Scrollbar(cf, orient="horizontal", command=self._cycles_txt.xview)
        self._cycles_txt.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._cycles_txt.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._cycles_placeholder()

    def _cycles_placeholder(self):
        """Stato vuoto: nessuna permutazione T caricata."""
        txt = self._cycles_txt
        txt.tag_configure("placeholder", foreground="#8a96a3",
                          font="GiocoHelpItalic")
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        txt.insert(
            "end",
            tr("cycles.empty_state"),
            "placeholder")
        txt.configure(state="disabled")

    def _build_orbits_tab(self):
        fr = self._orbits_tab
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(1, weight=1)

        ctrl = ttk.Frame(fr, padding=(8, 4))
        ctrl.grid(row=0, column=0, sticky="ew")
        ttk.Label(ctrl, text=tr("cycles.card"),
                  font=("Segoe UI", 10)).pack(side="left")
        self._card_var = tk.IntVar(value=0)
        self._card_spin = ttk.Spinbox(ctrl, from_=0, to=26,
                                      textvariable=self._card_var,
                                      width=4, command=self._refresh_orbit)
        self._card_spin.pack(side="left", padx=4)
        self._card_spin.bind("<Return>", lambda e: self._refresh_orbit())
        ttk.Label(ctrl,
                  text=tr("cycles.orbit_hint"),
                  font=("Segoe UI", 9, "italic"),
                  foreground="#666").pack(side="left", padx=8)

        of = ttk.Frame(fr)
        of.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        of.columnconfigure(0, weight=1)
        of.rowconfigure(0, weight=1)

        self._orbits_txt = tk.Text(
            of, font=("Courier New", 10), state="disabled",
            wrap="none", background="#FAFBFC", relief="flat")
        vsb2 = ttk.Scrollbar(of, orient="vertical",   command=self._orbits_txt.yview)
        hsb2 = ttk.Scrollbar(of, orient="horizontal", command=self._orbits_txt.xview)
        self._orbits_txt.configure(yscrollcommand=vsb2.set, xscrollcommand=hsb2.set)
        self._orbits_txt.grid(row=0, column=0, sticky="nsew")
        vsb2.grid(row=0, column=1, sticky="ns")
        hsb2.grid(row=1, column=0, sticky="ew")

    # ─── API pubblica ─────────────────────────────────────────────────────────

    def set_permutation(self, perm):
        """Aggiorna la visualizzazione con una nuova permutazione T (list/array len 27)."""
        self._perm = list(perm)
        self._hint.configure(text="")
        self._refresh_summary()
        self._refresh_cycles_text()
        self._refresh_orbit()

    def reset(self):
        """Riporta il tab allo stato iniziale (nessuna T caricata)."""
        self._perm = None
        for var in (self._order_var, self._ncycles_var, self._type_var):
            var.set("—")
        for w in (self._cycles_txt, self._orbits_txt):
            w.configure(state="normal")
            w.delete("1.0", "end")
            w.configure(state="disabled")
        self._cycles_placeholder()
        self._hint.configure(
            text=tr("cycles.reset_hint"))

    # ─── Refresh ─────────────────────────────────────────────────────────────

    def _refresh_summary(self):
        if self._perm is None:
            return
        perm = self._perm
        ord_ = order_of(perm)
        cycs = cycle_decomposition(perm)
        ct   = cycle_type(perm)
        type_str = "  ".join(f"{cnt}×({ln})" for ln, cnt in sorted(ct.items()))
        self._order_var.set(str(ord_))
        self._ncycles_var.set(str(len(cycs)))
        self._type_var.set(type_str)

    def _refresh_cycles_text(self):
        if self._perm is None:
            return
        txt  = self._cycles_txt
        perm = self._perm
        cycs = cycle_decomposition(perm)
        ct   = cycle_type(perm)

        # Assegna un colore per lunghezza di ciclo
        lengths = sorted(ct.keys())
        col_for_len = {l: _CYCLE_PALETTE[i % len(_CYCLE_PALETTE)]
                       for i, l in enumerate(lengths)}

        txt.configure(state="normal")
        txt.delete("1.0", "end")

        # Configura tag
        for l, c in col_for_len.items():
            txt.tag_configure(f"cyc_{l}", foreground=c, font=("Courier New", 10, "bold"))
        txt.tag_configure("label", foreground="#555", font=("Courier New", 9))
        txt.tag_configure("fixed", foreground="#aaa", font=("Courier New", 10, "italic"))

        txt.insert("end",
                   f"  {'#':>3}  {tr('cycles.length'):>3}  "
                   f"{tr('cycles.cycle')}\n"
                   f"  {'─'*3}  {'─'*3}  {'─'*60}\n",
                   "label")

        for idx, cyc in enumerate(cycs, 1):
            l   = len(cyc)
            tag = f"cyc_{l}"
            cyc_str = " → ".join(f"C{c:02d}" for c in cyc)
            if l == 1:
                txt.insert(
                    "end",
                    f"  {idx:>3}  {l:>3}  ({cyc_str})  "
                    f"[{tr('cycles.fixed_point')}]\n",
                    "fixed")
            else:
                txt.insert("end", f"  {idx:>3}  {l:>3}  ({cyc_str} →)\n", tag)

        txt.configure(state="disabled")

    def _refresh_orbit(self):
        if self._perm is None:
            return
        txt  = self._orbits_txt
        perm = self._perm
        try:
            card = int(self._card_var.get())
        except (ValueError, tk.TclError):
            return
        card = max(0, min(26, card))

        orbit = orbit_of(perm, card)
        ord_  = len(orbit)

        txt.configure(state="normal")
        txt.delete("1.0", "end")
        txt.tag_configure("hdr",  font=("Segoe UI", 10, "bold"), foreground="#1a3a5c")
        txt.tag_configure("pos",  font=("Courier New", 10), foreground="#444")
        txt.tag_configure("card", font=("Courier New", 10, "bold"), foreground="#1a5c1a")
        txt.tag_configure("arr",  font=("Courier New", 10), foreground="#aaa")

        txt.insert(
            "end",
            tr("cycles.orbit_summary", card=card, length=ord_, order=ord_)
            + "\n\n",
            "hdr")

        # Tabella: applicazione k → posizione
        txt.insert(
            "end",
            tr("cycles.orbit_header", k_label="k",
               expression=f"T^k(C{card})", position=tr("cycles.position"))
            + "\n",
            "pos")
        txt.insert("end", f"  {'─'*40}\n", "pos")
        for k, pos in enumerate(orbit):
            txt.insert("end", f"  {k:>4}   ", "pos")
            txt.insert("end", f"C{pos:02d}", "card")
            txt.insert("end", f"         {tr('cycles.position')} {pos:02d}\n", "pos")
        # Chiusura ciclo
        txt.insert("end", f"  {ord_:>4}   ", "pos")
        txt.insert("end", f"C{card:02d}", "card")
        txt.insert(
            "end",
            f"         = C{card:02d}  ({tr('cycles.return')})\n",
            "arr")

        txt.configure(state="disabled")
