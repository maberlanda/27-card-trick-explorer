"""
CayleyDialog: calcolatore interattivo di prodotti in G = GEN3^3
e export della tabella di Cayley completa (216x216) in CSV.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ..core.group_theory import get_group_data
from .common import run_in_thread, ui_call
from .tooltip import attach as _tip
from .i18n import tr


class CayleyDialog(tk.Toplevel):
    """Calcolatore prodotti A o B con export tabella di Cayley CSV."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title(tr("cayley.window_title"))
        self.geometry("900x600")
        self.resizable(True, True)
        self._gd = None
        self._names: list = []
        self._build_ui()
        # run_in_thread (non Thread nudo): registra il traceback nel log e
        # mostra un messaggio se il precalcolo del gruppo fallisce, invece di
        # lasciare la finestra bloccata su "Calcolo in corso..." per sempre.
        run_in_thread(self, self._load,
                      error_title=tr("cayley.error.calculation"))

    # ----------------------------------------------------------------- UI ---

    def _build_ui(self):
        hdr = ttk.Frame(self, padding=(10, 8, 10, 4))
        hdr.pack(fill="x")
        ttk.Label(hdr,
                  text=tr("cayley.header"),
                  font=("Segoe UI", 12, "bold"),
                  foreground="#1a3a5c").pack(side="left")

        ttk.Label(self,
                  text=("A ∘ B significa: esegui PRIMA la raccolta B, POI la "
                        "raccolta A (composizione da destra a sinistra). "
                        "Ogni elemento è una terna (f₃ x f₂ x f₁) che agisce su "
                        "pacchetti, terzine e carte. Il calcolatore mostra anche "
                        "il commutatore, le potenze e il sottogruppo generato: "
                        "strumenti per capire quanto «si intrecciano» due raccolte."),
                  font=("Segoe UI", 9), foreground="#444",
                  wraplength=860, justify="left",
                  padding=(10, 2, 10, 4)).pack(fill="x")

        self._status = tk.StringVar(value=tr("cayley.status.calculating"))
        ttk.Label(self, textvariable=self._status,
                  font=("Segoe UI", 9, "italic"),
                  foreground="#666", padding=(10, 0)).pack(fill="x")

        # Calcolatore prodotti
        calc = ttk.LabelFrame(self, text=tr("cayley.calculator"), padding=10)
        calc.pack(fill="x", padx=10, pady=(4, 0))

        row1 = ttk.Frame(calc)
        row1.pack(fill="x")

        ttk.Label(row1, text="A =", font=("Segoe UI", 10, "bold")).pack(side="left")
        self._combo_a = ttk.Combobox(row1, state="readonly", width=32)
        self._combo_a.pack(side="left", padx=(4, 20))
        _tip(self._combo_a, tr("cayley.tooltip.a"))

        ttk.Label(row1, text="B =", font=("Segoe UI", 10, "bold")).pack(side="left")
        self._combo_b = ttk.Combobox(row1, state="readonly", width=32)
        self._combo_b.pack(side="left", padx=(4, 20))
        _tip(self._combo_b, tr("cayley.tooltip.b"))

        _bc = ttk.Button(row1, text=tr("button.calculate"), command=self._calc)
        _bc.pack(side="left")
        _tip(_bc, tr("cayley.tooltip.calculate"))
        _bs = ttk.Button(row1, text=tr("button.swap_ab"), command=self._swap)
        _bs.pack(side="left", padx=(8, 0))
        _tip(_bs, tr("cayley.tooltip.swap"))

        row2 = ttk.Frame(calc)
        row2.pack(fill="x", pady=(8, 0))

        for lbl, attr in [("A ∘ B =", "_res_ab"), ("B ∘ A =", "_res_ba"),
                          ("A⁻¹ =", "_res_inv_a"), ("B⁻¹ =", "_res_inv_b")]:
            f = ttk.Frame(row2)
            f.pack(side="left", padx=(0, 24))
            ttk.Label(f, text=lbl, font=("Segoe UI", 9, "bold")).pack(side="left")
            var = tk.StringVar(value="—")
            setattr(self, attr, var)
            ttk.Label(f, textvariable=var,
                      font=("Courier New", 9),
                      foreground="#1a3a5c").pack(side="left", padx=(4, 0))

        # Riquadro ordini e informazioni
        info = ttk.LabelFrame(self, text=tr("cayley.info.title"),
                              padding=8)
        info.pack(fill="x", padx=10, pady=6)

        self._info_var = tk.StringVar(value=tr("cayley.info.prompt"))
        ttk.Label(info, textvariable=self._info_var,
                  font=("Courier New", 9), foreground="#333",
                  justify="left").pack(anchor="w")

        # --- Bottoni: impaccati per primi in basso (side="bottom") così
        #     restano sempre visibili anche con finestra piccola. ---
        bf = ttk.Frame(self, padding=(8, 4))
        bf.pack(side="bottom", fill="x")
        self._exp_mb = tk.Menubutton(bf, text=tr("button.export"), relief="raised",
                                     state="disabled")
        exp_menu = tk.Menu(self._exp_mb, tearoff=0)
        exp_menu.add_command(label="📊  CSV (;)", command=self._export_csv)
        exp_menu.add_command(label="🌐  HTML",   command=self._export_html)
        exp_menu.add_separator()
        exp_menu.add_command(label="📐  LaTeX / SVG…", command=self._export_latex_svg)
        self._exp_mb["menu"] = exp_menu
        self._exp_mb.pack(side="left", padx=(0, 8))
        _tip(self._exp_mb, tr("cayley.tooltip.export"))
        ttk.Button(bf, text=tr("button.close"), command=self.destroy).pack(side="left")

        # Sottogruppo generato
        sg = ttk.LabelFrame(self, text=tr("cayley.subgroup.title"),
                             padding=8)
        sg.pack(fill="both", expand=True, padx=10, pady=(0, 4))
        sg.rowconfigure(0, weight=1); sg.columnconfigure(0, weight=1)

        self._sg_box = tk.Text(sg, font=("Courier New", 9),
                               wrap="none", state="disabled",
                               background="#f4f8ff", height=6)
        vsb = ttk.Scrollbar(sg, orient="vertical", command=self._sg_box.yview)
        hsb = ttk.Scrollbar(sg, orient="horizontal", command=self._sg_box.xview)
        self._sg_box.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._sg_box.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")


    # ------------------------------------------------------------ load ------

    def _load(self):
        gd = get_group_data()
        _ = gd.cayley
        _ = gd.orders
        _ = gd.classes
        self._gd = gd
        self._names = [gd.name(i) for i in range(len(gd.kron_arr))]
        self._class_of = {}
        for ci, c in enumerate(gd.classes):
            for e in c:
                self._class_of[int(e)] = ci
        ui_call(self, self._on_loaded)

    def _on_loaded(self):
        if not self.winfo_exists():
            return
        values = self._names
        self._combo_a["values"] = values
        self._combo_b["values"] = values
        self._combo_a.current(0)
        self._combo_b.current(1)
        self._status.set(tr("cayley.status.ready",
                            count=len(self._gd.kron_arr)))
        self._exp_mb.configure(state="normal")

    # ------------------------------------------------------------ calc ------

    def _calc(self):
        gd = self._gd
        if gd is None:
            return
        ia = self._combo_a.current()
        ib = self._combo_b.current()
        if ia < 0 or ib < 0:
            return

        cay   = gd.cayley
        inv   = gd.inverse
        ord_a = int(gd.orders[ia])
        ord_b = int(gd.orders[ib])

        ab    = int(cay[ia, ib])
        ba    = int(cay[ib, ia])
        inv_a = int(inv[ia])
        inv_b = int(inv[ib])

        self._res_ab.set(gd.name(ab))
        self._res_ba.set(gd.name(ba))
        self._res_inv_a.set(gd.name(inv_a))
        self._res_inv_b.set(gd.name(inv_b))

        # potenze di A fino all'identità: A, A², ..., A^ord = e
        iden = gd._identity_index()
        pows, cur = [], ia
        while cur != iden:
            pows.append(gd.name(cur))
            cur = int(cay[ia, cur])
        pows.append("e")
        pow_str = "  →  ".join(pows)

        # commutatore [A,B] = A⁻¹ ∘ B⁻¹ ∘ A ∘ B  (= e ⇔ A e B commutano)
        comm = int(cay[inv_a, int(cay[inv_b, ab])])

        # coniugio: A e B nella stessa classe?  inoltre B∘A = B(A∘B)B⁻¹
        same_cls = (self._class_of.get(ia) == self._class_of.get(ib))

        commute = tr("cayley.commute.yes" if ab == ba else
                     "cayley.commute.no")
        product_note = ("" if ab == ba else
                        tr("cayley.products.conjugate",
                           order=int(gd.orders[ab])))
        commutator_note = tr("cayley.commutator.identity" if comm == iden else
                             "cayley.commutator.non_identity")
        conjugate = tr("cayley.conjugate.yes" if same_cls else
                       "cayley.conjugate.no")
        info = tr(
            "cayley.info.details", a_name=gd.name(ia), a_order=ord_a,
            b_name=gd.name(ib), b_order=ord_b, powers=pow_str,
            commute=commute, product_note=product_note,
            commutator=gd.name(comm), commutator_note=commutator_note,
            conjugate=conjugate, ab_order=int(gd.orders[ab]),
            ba_order=int(gd.orders[ba]))
        self._info_var.set(info)

        # Sottogruppo generato da A e B
        self._compute_subgroup(ia, ib)

    def _swap(self):
        a, b = self._combo_a.current(), self._combo_b.current()
        if a >= 0 and b >= 0:
            self._combo_a.current(b)
            self._combo_b.current(a)
            self._calc()

    def _compute_subgroup(self, ia: int, ib: int):
        gd  = self._gd
        cay = gd.cayley
        inv = gd.inverse
        n   = len(gd.kron_arr)
        iden = gd._identity_index()

        # BFS: genera tutti i prodotti di A, B e loro inversi
        generators = {ia, ib, int(inv[ia]), int(inv[ib])}
        subgroup   = {iden}
        frontier   = {iden}
        while frontier:
            nxt = set()
            for g in frontier:
                for gen in generators:
                    prod = int(cay[g, gen])
                    if prod not in subgroup:
                        subgroup.add(prod)
                        nxt.add(prod)
            frontier = nxt
            if len(subgroup) > n:
                break

        # proprietà del sottogruppo
        k = len(subgroup)
        sg_list = sorted(subgroup)
        abelian = all(int(cay[x, y]) == int(cay[y, x])
                      for xi, x in enumerate(sg_list)
                      for y in sg_list[xi + 1:])
        intestazione = tr(
            "cayley.subgroup.summary", order=k, index=n // k,
            structure=tr("cayley.subgroup.abelian" if abelian else
                         "cayley.subgroup.non_abelian"),
            all_group=(tr("cayley.subgroup.all_group") if k == n else ""),
            separator="─" * 54)
        self._sg_box.configure(state="normal")
        self._sg_box.delete("1.0", "end")
        self._sg_box.insert("end", intestazione)
        for j, idx in enumerate(sg_list):
            self._sg_box.insert("end",
                f"  {j+1:>3}. {gd.name(idx)}\n")
        self._sg_box.configure(state="disabled")

    # ----------------------------------------------------------- export -----

    def _export_csv(self):
        gd = self._gd
        if gd is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), (tr("common.filetype_all"), "*.*")],
            title=tr("cayley.export.title"))
        if not path:
            return
        self._status.set(tr("cayley.status.exporting"))
        self.update_idletasks()
        try:
            gd.export_cayley_csv(path)
            self._status.set(tr("cayley.status.exported"))
            messagebox.showinfo(tr("export.completed_title"),
                                tr("cayley.export.saved", path=path),
                                parent=self)
        except Exception as exc:
            messagebox.showerror(tr("error.generic"), str(exc), parent=self)

    def _export_latex_svg(self):
        """Apre il dialog di export LaTeX/SVG con A,B correnti."""
        gd = getattr(self, "_gd", None)
        if gd is None:
            return
        from .export_group_dialog import CayleyExportDialog
        ia = self._combo_a.current()
        ib = self._combo_b.current()
        CayleyExportDialog(self, gd,
                           ia if ia >= 0 else 0,
                           ib if ib >= 0 else 1)

    def _export_html(self):
        """Esporta la tavola di Cayley in HTML."""
        import html as _h
        gd = getattr(self, "_gd", None)
        if gd is None:
            return
        path = __import__("tkinter.filedialog", fromlist=["asksaveasfilename"]).asksaveasfilename(
            parent=self, defaultextension=".html",
            filetypes=[("HTML", "*.html"), (tr("common.filetype_all"), "*.*")],
            title=tr("cayley.export.html_title"))
        if not path:
            return
        self._status.set(tr("cayley.status.exporting_html"))
        self.update_idletasks()
        try:
            names = self._names
            n = len(names)
            hdr = "".join(f"<th>{_h.escape(nm)}</th>" for nm in names)
            rows = ""
            cay = gd.cayley
            for i in range(n):
                cells = "".join(f"<td>{_h.escape(names[int(cay[i,j])])}</td>" for j in range(n))
                rows += f"<tr><th>{_h.escape(names[i])}</th>{cells}</tr>\n"
            html_str = f"""<!DOCTYPE html><html lang='it'><head><meta charset='UTF-8'>
<title>Tavola di Cayley GEN3³</title>
<style>body{{font-family:monospace;font-size:0.7em;padding:10px}}
table{{border-collapse:collapse}}
th,td{{border:1px solid #ddd;padding:2px 5px;white-space:nowrap;font-family:'Courier New',monospace;font-size:0.78em}}
th{{background:#f0f4f0;font-weight:bold}}</style></head>
<body><h3>Tavola di Cayley — GEN3³ ({n}×{n})</h3>
<table><tr><th></th>{hdr}</tr>{rows}</table></body></html>"""
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_str)
            self._status.set(tr("cayley.status.exported_html"))
            __import__("webbrowser").open(f"file://{path}")
        except Exception as exc:
            __import__("tkinter.messagebox", fromlist=["showerror"]).showerror(
                tr("error.generic"), str(exc), parent=self)
            self._status.set("")
