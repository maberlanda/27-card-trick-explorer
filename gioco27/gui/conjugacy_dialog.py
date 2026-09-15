"""
ConjugacyDialog: mostra le classi di coniugio e il centro di GEN3^3.

Struttura:
  - Pannello sinistro: lista classi (dimensione, ordine del rappresentante)
  - Pannello destro: elementi della classe selezionata
  - Riquadro Centro Z(G)
  - Export TXT
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ..core.group_theory import get_group_data
from ..core.log import get_logger
from .common import run_in_thread, ui_call
from .i18n import tr

_log = get_logger(__name__)
from .tooltip import attach as _tip

# Classe di coniugio in S3 di ciascun generatore GEN3:
# l'identità, le 3 trasposizioni, i 2 tre-cicli.
_S3_CLASS = {
    "SCD_U": ("conjugacy.type.identity",      1),
    "SDC_U": ("conjugacy.type.transposition", 3),
    "CSD_U": ("conjugacy.type.transposition", 3),
    "DCS_U": ("conjugacy.type.transposition", 3),
    "CDS_U": ("conjugacy.type.three_cycle",   2),
    "DSC_U": ("conjugacy.type.three_cycle",   2),
}


def _class_type(triple):
    """(f3,f2,f1) → ('(id, trasp., 3-ciclo)', dimensione_attesa).
    In S3×S3×S3 la classe di coniugio di (a,b,c) è il prodotto delle classi
    dei fattori: il tipo identifica la classe e la dimensione è il prodotto
    delle dimensioni (1 per id, 3 per trasposizioni, 2 per 3-cicli)."""
    kinds = [tr(_S3_CLASS[f][0]) for f in triple]
    size  = 1
    for f in triple:
        size *= _S3_CLASS[f][1]
    return "(" + ", ".join(kinds) + ")", size


class ConjugacyDialog(tk.Toplevel):
    """Dialog classi di coniugio e centro di G = GEN3^3."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title(tr("conjugacy.window_title"))
        self.geometry("1100x680")
        self.resizable(True, True)
        self._gd = None
        self._build_ui()
        # run_in_thread (non Thread nudo): registra il traceback nel log e
        # mostra un messaggio se il precalcolo del gruppo fallisce, invece di
        # lasciare la finestra bloccata su "Calcolo in corso..." per sempre.
        run_in_thread(self, self._load,
                      error_title=tr("conjugacy.error.calculation"))

    # ---------------------------------------------------------------- UI ----

    def _build_ui(self):
        hdr = ttk.Frame(self, padding=(10, 8, 10, 4))
        hdr.pack(fill="x")
        ttk.Label(hdr,
                  text=tr("conjugacy.header"),
                  font=("Segoe UI", 12, "bold"),
                  foreground="#1a3a5c").pack(side="left")

        ttk.Label(self,
                  text=("Due elementi x, y sono CONIUGATI se esiste g con "
                        "g∘x∘g⁻¹ = y: fanno «la stessa cosa» a meno di una "
                        "rinominazione delle posizioni. In G = S₃×S₃×S₃ la "
                        "classe di un elemento (f₃,f₂,f₁) è la terna delle "
                        "classi dei fattori in S₃ {id, trasposizioni, 3-cicli}: "
                        "per questo le classi sono esattamente 3³ = 27 e la "
                        "dimensione di ciascuna è il prodotto delle dimensioni "
                        "(1, 3 o 2) dei fattori."),
                  font=("Segoe UI", 9), foreground="#444",
                  wraplength=1050, justify="left",
                  padding=(10, 2, 10, 4)).pack(fill="x")

        self._status = tk.StringVar(value=tr("conjugacy.status.calculating"))
        ttk.Label(self, textvariable=self._status,
                  font=("Segoe UI", 9, "italic"),
                  foreground="#666", padding=(10, 0)).pack(fill="x")

        # --- Bottoni: impaccati per primi in basso (side="bottom") così
        #     restano sempre visibili, anche se la finestra è piccola o il
        #     contenuto centrale è alto. ---
        bf = ttk.Frame(self, padding=(8, 4))
        bf.pack(side="bottom", fill="x")
        self._exp_mb = tk.Menubutton(bf, text=tr("button.export"), relief="raised")
        exp_menu = tk.Menu(self._exp_mb, tearoff=0)
        exp_menu.add_command(label="📄  TXT",  command=self._export_txt)
        exp_menu.add_command(label="🌐  HTML", command=self._export_html)
        exp_menu.add_separator()
        exp_menu.add_command(label="📐  LaTeX / SVG…", command=self._export_latex_svg)
        self._exp_mb["menu"] = exp_menu
        self._exp_mb.pack(side="left", padx=(0, 8))
        _tip(self._exp_mb, tr("conjugacy.tooltip.export"))
        ttk.Button(bf, text=tr("button.close"), command=self.destroy).pack(side="left")

        # Frame principale a tre colonne
        main = ttk.Frame(self, padding=(8, 4))
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=3)
        main.columnconfigure(2, weight=2)
        main.rowconfigure(0, weight=1)

        # --- Colonna sinistra: lista classi ---
        lf = ttk.LabelFrame(main, text=tr("conjugacy.classes.title"), padding=6)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

        cls_cols = ("idx", "size", "ord", "tipo")
        self._cls_tree = ttk.Treeview(
            lf, columns=cls_cols, show="headings", selectmode="browse")
        self._cls_tree.heading("idx",  text="#")
        self._cls_tree.heading("size", text=tr("conjugacy.column.size"), command=lambda: self._sort_cls("size"))
        self._cls_tree.heading("ord",  text=tr("conjugacy.column.order"))
        self._cls_tree.heading("tipo", text=tr("conjugacy.column.type"))
        self._cls_tree.column("idx",  width=36,  stretch=False, anchor="center")
        self._cls_tree.column("size", width=50,  stretch=False, anchor="center")
        self._cls_tree.column("ord",  width=46,  stretch=False, anchor="center")
        self._cls_tree.column("tipo", width=190, anchor="w")
        self._cls_tree.tag_configure("center_cls", foreground="#8B0000",
                                     font=("Segoe UI", 9, "bold"))
        vsb1 = ttk.Scrollbar(lf, orient="vertical", command=self._cls_tree.yview)
        self._cls_tree.configure(yscrollcommand=vsb1.set)
        self._cls_tree.grid(row=0, column=0, sticky="nsew")
        _tip(self._cls_tree, tr("conjugacy.tooltip.classes"))
        vsb1.grid(row=0, column=1, sticky="ns")
        self._cls_tree.bind("<<TreeviewSelect>>", self._on_cls_select)

        # --- Colonna centrale: elementi della classe ---
        ef = ttk.LabelFrame(main, text=tr("conjugacy.elements.title"), padding=6)
        ef.grid(row=0, column=1, sticky="nsew", padx=4)
        ef.rowconfigure(0, weight=1)
        ef.columnconfigure(0, weight=1)

        self._elem_box = tk.Text(ef, font=("Courier New", 9),
                                 wrap="none", state="disabled",
                                 background="#f8f8f8")
        vsb2 = ttk.Scrollbar(ef, orient="vertical", command=self._elem_box.yview)
        hsb2 = ttk.Scrollbar(ef, orient="horizontal", command=self._elem_box.xview)
        self._elem_box.configure(yscrollcommand=vsb2.set, xscrollcommand=hsb2.set)
        self._elem_box.grid(row=0, column=0, sticky="nsew")
        vsb2.grid(row=0, column=1, sticky="ns")
        hsb2.grid(row=1, column=0, sticky="ew")

        # --- Colonna destra: centro e statistiche ---
        rf = ttk.LabelFrame(main, text=tr("conjugacy.center_stats.title"), padding=6)
        rf.grid(row=0, column=2, sticky="nsew", padx=(4, 0))
        rf.rowconfigure(1, weight=1)
        rf.columnconfigure(0, weight=1)

        self._stats_lbl = ttk.Label(rf, text="",
                                    font=("Segoe UI", 9),
                                    justify="left", wraplength=240)
        self._stats_lbl.grid(row=0, column=0, sticky="nw", pady=(0, 8))

        ttk.Label(rf, text=tr("conjugacy.center_elements"),
                  font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="nw")
        self._center_box = tk.Text(rf, font=("Courier New", 9),
                                   wrap="word", state="disabled",
                                   background="#fff8f0", height=8)
        self._center_box.grid(row=2, column=0, sticky="nsew")


    # --------------------------------------------------------------- load ---

    def _load(self):
        gd = get_group_data()
        _ = gd.classes   # forza calcolo
        _ = gd.orders
        self._gd = gd
        ui_call(self, self._populate)

    def _populate(self):
        if not self.winfo_exists():
            return
        gd = self._gd
        cls = gd.classes
        ord_arr = gd.orders
        center  = gd.center

        n_cls  = len(cls)
        center_set = set(center)

        # Statistiche
        from collections import Counter
        size_counts = Counter(len(c) for c in cls)
        stats = tr("conjugacy.stats.header", group_size=len(gd.kron_arr),
                   class_count=n_cls, center_size=len(center))
        for sz in sorted(size_counts):
            stats += tr("conjugacy.stats.class_size", size=sz,
                        count=size_counts[sz])
        stats += tr("conjugacy.stats.orders")
        ord_counter = Counter(int(ord_arr[i]) for i in range(len(gd.kron_arr)))
        for o in sorted(ord_counter):
            stats += tr("conjugacy.stats.order", order=o, count=ord_counter[o])
        # Equazione delle classi: |G| = somma delle dimensioni
        eq_parts = [f"{sz}·{cnt}" for sz, cnt in sorted(size_counts.items())]
        stats += tr("conjugacy.stats.equation", terms=" + ".join(eq_parts),
                    products=" + ".join(
                        str(sz * cnt) for sz, cnt in sorted(size_counts.items())))
        stats += tr("conjugacy.stats.center", identity="e",
                    center_identity="(e,e,e)")
        stats += tr("conjugacy.stats.game")
        self._stats_lbl.configure(text=stats)

        # Popolamento lista classi (col tipo S3 dei tre fattori)
        for i, c in enumerate(cls):
            rep_ord = int(ord_arr[c[0]])
            is_ctr  = all(idx in center_set for idx in c)
            tags    = ("center_cls",) if is_ctr else ()
            tipo, size_att = _class_type(gd.kron_names[c[0]])
            if size_att != len(c):
                # Coerenza teoria ↔ calcolo. Era un `assert`: con `python -O`
                # gli assert vengono rimossi, quindi l'incoerenza passava
                # inosservata proprio nella configurazione "di produzione".
                # Qui viene registrata nel log e mostrata nella colonna, senza
                # far esplodere la finestra.
                _log.error("Classe %d: dimensione teorica %d != calcolata %d "
                           "(rappresentante %s)",
                           i + 1, size_att, len(c), gd.kron_names[c[0]])
                tipo = f"{tipo} ⚠"
            self._cls_tree.insert("", "end", iid=str(i),
                                  values=(i + 1, len(c), rep_ord, tipo),
                                  tags=tags)

        # Centro
        self._center_box.configure(state="normal")
        self._center_box.delete("1.0", "end")
        if center:
            for idx in center:
                self._center_box.insert("end", gd.name(idx) + "\n")
        else:
            self._center_box.insert(
                "end", tr("conjugacy.center.trivial", identity="e"))
        self._center_box.configure(state="disabled")

        self._status.set(tr("conjugacy.status.ready", class_count=n_cls,
                            center_size=len(center)))

    def _on_cls_select(self, event):
        sel = self._cls_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        gd  = self._gd
        if gd is None:
            return
        cls = gd.classes[idx]
        ord_arr = gd.orders

        tipo, _ = _class_type(gd.kron_names[cls[0]])
        sizes = [str(_S3_CLASS[f][1]) for f in gd.kron_names[cls[0]]]
        self._elem_box.configure(state="normal")
        self._elem_box.delete("1.0", "end")
        self._elem_box.insert("end", tr(
            "conjugacy.class.details", number=idx + 1, count=len(cls),
            order=int(ord_arr[cls[0]]), type=tipo,
            dimensions=" × ".join(sizes), representative=gd.name(cls[0]),
            separator="─" * 52))
        for j, elem_idx in enumerate(cls):
            self._elem_box.insert(
                "end", f"  {j+1:>3}.  {gd.name(elem_idx)}\n")
        self._elem_box.configure(state="disabled")

    def _sort_cls(self, col):
        items = [(self._cls_tree.set(k, col), k)
                 for k in self._cls_tree.get_children("")]
        items.sort(key=lambda x: int(x[0]))
        for pos, (_, k) in enumerate(items):
            self._cls_tree.move(k, "", pos)

    # -------------------------------------------------------------- export --

    def _export_txt(self):
        if self._gd is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".txt",
            filetypes=[(tr("common.filetype_text"), "*.txt"),
                       (tr("common.filetype_all"), "*.*")],
            title=tr("conjugacy.export.title"))
        if not path:
            return
        gd = self._gd
        cls = gd.classes
        ord_arr = gd.orders
        center = gd.center
        lines = [
            "CLASSI DI CONIUGIO  G = GEN3^3",
            f"|G| = {len(gd.kron_arr)},  classi: {len(cls)},  |Z(G)| = {len(center)}",
            "=" * 60,
        ]
        for i, c in enumerate(cls):
            lines.append(f"\nClasse {i+1}  (dim={len(c)}, ord={int(ord_arr[c[0]])})")
            lines.append("-" * 40)
            for j, idx in enumerate(c):
                lines.append(f"  {j+1:>3}. {gd.name(idx)}")
        lines += ["", "CENTRO Z(G)", "-" * 40]
        if center:
            for idx in center:
                lines.append(f"  {gd.name(idx)}")
        else:
            lines.append("  {e}  (centro triviale)")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo(tr("export.completed_title"),
                                tr("conjugacy.export.saved", path=path),
                                parent=self)
        except OSError as exc:
            messagebox.showerror(tr("error.generic"), str(exc), parent=self)

    def _export_latex_svg(self):
        """Apre il dialog di export LaTeX/SVG delle classi di coniugio."""
        gd = getattr(self, "_gd", None)
        if gd is None:
            messagebox.showinfo(tr("conjugacy.wait.title"),
                                tr("conjugacy.wait.message"),
                                parent=self)
            return
        from .export_group_dialog import ConjugacyExportDialog
        ConjugacyExportDialog(self, gd)

    def _export_html(self):
        """Esporta le classi di coniugio in HTML."""
        import html as _h
        gd = getattr(self, "_gd", None)
        if gd is None:
            return
        path = __import__("tkinter.filedialog", fromlist=["asksaveasfilename"]).asksaveasfilename(
            parent=self, defaultextension=".html",
            filetypes=[("HTML", "*.html"),
                       (tr("common.filetype_all"), "*.*")],
            title=tr("conjugacy.export.html_title"))
        if not path:
            return
        classes = gd.classes
        center  = gd.center
        rows = ""
        for i, cls in enumerate(classes, 1):
            rep  = gd.name(cls[0])
            elts = ", ".join(gd.name(e) for e in cls)
            rows += (f"<tr><td>{i}</td><td><code>{_h.escape(rep)}</code></td>"
                     f"<td>{len(cls)}</td><td style='font-size:0.85em'>{_h.escape(elts)}</td></tr>\n")
        center_str = ", ".join(gd.name(e) for e in center)
        html = f"""<!DOCTYPE html><html lang='it'><head><meta charset='UTF-8'>
<title>Classi di coniugio GEN3³</title>
<style>body{{font-family:sans-serif;padding:20px}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:4px 8px;text-align:left;font-family:'Courier New',monospace;font-size:0.85em}}
th{{background:#f0f4f0}}tr:nth-child(even){{background:#fafafa}}</style></head>
<body><h2>Classi di coniugio — GEN3³ (216 elementi)</h2>
<p>Numero di classi: <strong>{len(classes)}</strong> &nbsp;|&nbsp;
   Centro: <em>{_h.escape(center_str)}</em></p>
<table><tr><th>#</th><th>Rappresentante</th><th>Dim.</th><th>Elementi</th></tr>
{rows}</table></body></html>"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            __import__("webbrowser").open(f"file://{path}")
        except Exception as exc:
            __import__("tkinter.messagebox", fromlist=["showerror"]).showerror(
                tr("error.generic"), str(exc), parent=self)
