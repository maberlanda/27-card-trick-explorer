"""
DecompositionDialog: cerca e mostra tutte le decomposizioni di T o T^-1,
con albero a tre livelli (A0 -> A1 -> A2) con lazy loading,
oppure tabella piatta con colonne A0 | A1 | A2.

Novita v3:
  - Opzione T / T^-1 via radio button
  - Cache su disco (gioco27/core/cache.py)
  - Ricerca parallela (gioco27/core/kronecker.py)
  - Espressioni inviate all'Explorer usano 'o' e 'x'
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .help_banner import HelpBanner
import queue
import threading
from collections import defaultdict

from ..core.kronecker import (find_all_kron_decompositions,
                               find_all_kron_decompositions_parallel)
from ..core.cache  import load_decompositions, save_decompositions
from ..core.config import get_config

_PLACEHOLDER = "__placeholder__"
_BATCH = 600


def _disp(t):
    return "({} x {} x {})".format(*t)

def _expr_triple(t):
    return "({} x {} x {})".format(*t)


class DecompositionDialog(tk.Toplevel):
    """Mostra tutte le decomposizioni A2 o MSC o A1 o MSC o A0 o MSC = target."""

    def __init__(self, parent, perm, inv_perm, on_results=None):
        """
        perm       : permutazione T (lista 27 int)
        inv_perm   : permutazione T^-1 (lista 27 int)
        on_results : callback(results) chiamato quando la ricerca finisce
        """
        super().__init__(parent)
        self._app        = parent
        self._on_results = on_results
        self._perm     = list(perm)
        self._inv_perm = list(inv_perm)
        self._results  = []
        self._group_mode = tk.BooleanVar(value=False)
        self._target_inv = tk.BooleanVar(value=True)   # True = T^-1, False = T
        self._node_expr  = {}
        self._node_data  = {}
        self._flat_job   = None
        self._cfg        = get_config()

        self.title("Decomposizioni — A2 o MSC o A1 o MSC o A0 o MSC")
        self.geometry("1260x760")
        self.resizable(True, True)
        self._build_ui()
        self._start_search()

    # ----------------------------------------------------------------- UI ---

    def _build_ui(self):
        hdr = ttk.Frame(self, padding=(10, 8, 10, 4))
        hdr.pack(fill="x")
        ttk.Label(hdr,
                  text="A2 o MSC o A1 o MSC o A0 o MSC  =  TARGET"
                       "   (A0,A1,A2 in GEN3 x GEN3 x GEN3)",
                  font=("Segoe UI", 11, "bold"),
                  foreground="#1a3a5c").pack(side="left")

        HelpBanner(
            self,
            "Elenca i modi di scrivere il TARGET come A₂∘MSC∘A₁∘MSC∘A₀∘MSC.",
            long=("Cerca le decomposizioni di Kronecker: ogni riga è una "
                  "sequenza di tre raccolte Aᵢ alternate al mescolamento MSC "
                  "che riproduce esattamente la trasformazione cercata."),
            on_open_guide=getattr(self.master, "_open_guide", None),
        ).pack(fill="x", padx=10, pady=(0, 4))

        self._status_var = tk.StringVar(value="Ricerca in corso...")
        ttk.Label(self, textvariable=self._status_var,
                  font=("Segoe UI", 10, "italic"),
                  foreground="#555", padding=(10, 0, 10, 4)).pack(fill="x")

        prog_fr = ttk.Frame(self, padding=(10, 0, 10, 6))
        prog_fr.pack(fill="x")
        self._progress_bar = ttk.Progressbar(
            prog_fr, orient="horizontal", mode="determinate",
            maximum=216, value=0, length=400)
        self._progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._progress_lbl = ttk.Label(
            prog_fr, text="  0 / 216  --  trovate: 0",
            font=("Courier New", 9), foreground="#444", width=30)
        self._progress_lbl.pack(side="left")

        ctrl_fr = ttk.Frame(self, padding=(10, 2, 10, 2))
        ctrl_fr.pack(fill="x")

        # Scelta target
        ttk.Label(ctrl_fr, text="Target:", font=("Segoe UI", 9)).pack(
            side="left", padx=(0, 4))
        ttk.Radiobutton(ctrl_fr, text="T⁻¹",
                        variable=self._target_inv, value=True,
                        command=self._on_target_changed).pack(side="left")
        ttk.Radiobutton(ctrl_fr, text="T",
                        variable=self._target_inv, value=False,
                        command=self._on_target_changed).pack(side="left", padx=(0, 20))

        ttk.Checkbutton(ctrl_fr, text="Albero A0 -> A1 -> A2",
                        variable=self._group_mode,
                        command=self._redisplay).pack(side="left")

        ttk.Label(ctrl_fr, text="  Filtro A1:", font=("Segoe UI", 9)).pack(
            side="left", padx=(20, 4))
        self._filter_var = tk.StringVar(value="")
        fe = ttk.Entry(ctrl_fr, textvariable=self._filter_var, width=22)
        fe.pack(side="left")
        fe.bind("<Return>", lambda e: self._redisplay())
        ttk.Button(ctrl_fr, text="Applica", command=self._redisplay).pack(
            side="left", padx=4)
        ttk.Button(ctrl_fr, text="X",
                   command=lambda: (self._filter_var.set(""), self._redisplay()),
                   width=3).pack(side="left", padx=(0, 20))

        self._load_lbl = ttk.Label(
            ctrl_fr, text="", font=("Segoe UI", 9, "italic"), foreground="#888")
        self._load_lbl.pack(side="left")
        self._sel_lbl = ttk.Label(
            ctrl_fr, text="", font=("Segoe UI", 9, "italic"), foreground="#555")
        self._sel_lbl.pack(side="left", padx=(20, 0))

        tf = ttk.Frame(self, padding=(8, 0, 8, 8))
        tf.pack(fill="both", expand=True)
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)

        cols = ("a1", "a2", "a3")
        self._tree = ttk.Treeview(tf, columns=cols, show="tree headings",
                                   selectmode="browse")
        self._tree.heading("#0", text="")
        self._tree.heading("a1", text="A0", command=lambda: self._sort_col("a1"))
        self._tree.heading("a2", text="A1", command=lambda: self._sort_col("a2"))
        self._tree.heading("a3", text="A2  (doppio clic -> Explorer)",
                           command=lambda: self._sort_col("a3"))
        self._tree.column("#0", width=24,  stretch=False, minwidth=24)
        self._tree.column("a1", width=285, stretch=True,  minwidth=200)
        self._tree.column("a2", width=285, stretch=True,  minwidth=200)
        self._tree.column("a3", width=285, stretch=True,  minwidth=200)

        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._tree.tag_configure("a1_node",  foreground="#7B3F00",
                                 font=("Segoe UI", 9, "bold"))
        self._tree.tag_configure("a2_node",  foreground="#1a5c1a",
                                 font=("Segoe UI", 9, "bold"))
        self._tree.tag_configure("a3_leaf",  foreground="#1a3a5c",
                                 font=("Courier New", 9))
        self._tree.tag_configure("flat_row", font=("Courier New", 9))

        self._tree.bind("<<TreeviewOpen>>",   self._on_open)
        self._tree.bind("<Double-1>",         self._on_double_click)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        bf = ttk.Frame(self, padding=(8, 4))
        bf.pack(fill="x")
        self._open_btn = ttk.Button(bf, text="Apri nell'Explorer", state="disabled",
                                    command=self._open_selected_in_explorer)
        self._open_btn.pack(side="left", padx=(0, 8))
        self._export_mb = tk.Menubutton(bf, text="Esporta…", relief="raised",
                                        state="disabled")
        exp_menu = tk.Menu(self._export_mb, tearoff=0)
        exp_menu.add_command(label="📄  TXT",      command=self._export_txt)
        exp_menu.add_command(label="📊  CSV (;)",  command=self._export_csv)
        exp_menu.add_command(label="🌐  HTML",     command=self._export_html)
        self._export_mb["menu"] = exp_menu
        self._export_mb.pack(side="left", padx=(0, 8))
        ttk.Button(bf, text="Chiudi", command=self.destroy).pack(side="left")

    # -------------------------------------------------- target / search -----

    def _current_target(self):
        return self._inv_perm if self._target_inv.get() else self._perm

    def _on_target_changed(self):
        self._results = []
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._node_expr.clear(); self._node_data.clear()
        self._open_btn.configure(state="disabled")
        self._export_mb.configure(state="disabled")
        self._status_var.set("Ricerca in corso...")
        self._progress_bar["value"] = 0
        self._progress_lbl.configure(text="  0 / 216  --  trovate: 0")
        self._start_search()

    def _start_search(self):
        target = self._current_target()
        # Prova cache
        cached = load_decompositions(target)
        if cached is not None:
            self._results = cached
            if self._on_results is not None:
                try: self._on_results(cached)
                except Exception: pass
            n = len(cached)
            self._progress_bar["value"] = 216
            self._progress_lbl.configure(text=f"216 / 216  --  trovate: {n:,}  (cache)")
            lbl = "T⁻¹" if self._target_inv.get() else "T"
            self._status_var.set(
                f"Trovate {n:,} decomposizioni di {lbl}  (da cache)")
            self._export_mb.configure(state="normal")
            self._redisplay()
            return

        self._progress_q = queue.Queue()
        threading.Thread(target=self._search_thread,
                         args=(target,), daemon=True).start()
        self.after(60, self._poll_progress)

    def _search_thread(self, target):
        try:
            use_par = self._cfg.get("use_parallel", True)
            n_workers = self._cfg.effective_n_workers

            def _cb(done, found):
                self._progress_q.put((done, found))

            if use_par and n_workers > 1:
                results = find_all_kron_decompositions_parallel(
                    target, n_workers=n_workers, progress_cb=_cb)
            else:
                results = find_all_kron_decompositions(target, progress_cb=_cb)

            save_decompositions(target, results)
            self._results   = results
            if self._on_results is not None:
                try: self._on_results(results)
                except Exception: pass
            self._progress_q.put(None)
        except Exception as exc:
            self._progress_q.put(("ERR", str(exc)))

    def _poll_progress(self):
        last_done = last_found = 0
        done_flag = False
        err_msg   = None
        try:
            for _ in range(50):
                item = self._progress_q.get_nowait()
                if item is None:
                    done_flag = True; break
                if isinstance(item, tuple) and item[0] == "ERR":
                    err_msg = item[1]; break
                last_done, last_found = item
        except queue.Empty:
            pass
        try:
            if err_msg:
                self._status_var.set("Errore: " + err_msg)
                return
            if last_done:
                self._progress_bar["value"] = min(last_done, 216)
                self._progress_lbl.configure(
                    text=f"{min(last_done,216):>3} / 216  --  trovate: {last_found:,}")
            if done_flag:
                n   = len(self._results)
                lbl = "T⁻¹" if self._target_inv.get() else "T"
                self._progress_bar["value"] = 216
                self._progress_lbl.configure(text=f"216 / 216  --  trovate: {n:,}")
                self._status_var.set(
                    f"Trovate {n:,} decomposizioni di {lbl}"
                    f"  (A0, A1, A2 in GEN3 x GEN3 x GEN3)")
                self._export_mb.configure(state="normal")
                self.after(0, lambda: self._redisplay())
                return
        except tk.TclError:
            return
        self.after(60, self._poll_progress)

    # ------------------------------------------------------ display ----------

    def _cancel_flat_job(self):
        if self._flat_job is not None:
            try:
                self.after_cancel(self._flat_job)
            except Exception:
                pass
            self._flat_job = None

    def _redisplay(self):
        if not self._results:
            return
        self._cancel_flat_job()
        results = self._results
        flt = self._filter_var.get().strip().upper()
        if flt:
            results = [r for r in results if flt in str(r[0]).upper()]
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._node_expr.clear(); self._node_data.clear()
        self._open_btn.configure(state="disabled")
        self._sel_lbl.configure(text="")
        if self._group_mode.get():
            self._build_tree(results)
        else:
            self._build_flat_async(results, 0)

    # ---- tree mode ----------------------------------------------------------

    def _build_tree(self, results):
        tree  = self._tree
        by_a1 = defaultdict(lambda: defaultdict(list))
        for (a1, a2, a3) in results:
            by_a1[a1][a2].append(a3)
        self._load_lbl.configure(
            text=f"Albero: {len(by_a1)} nodi A0 (espandi per A1 -> A2)")
        for a1, by_a2 in sorted(by_a1.items()):
            a1_disp = _disp(a1)
            n_a1    = sum(len(v) for v in by_a2.values())
            a1_node = tree.insert("", "end", text="",
                                  values=(a1_disp, "", f"[{n_a1} comb.]"),
                                  open=False, tags=("a1_node",))
            self._node_data[a1_node] = (a1, by_a2)
            tree.insert(a1_node, "end", iid=f"{a1_node}{_PLACEHOLDER}",
                        text="", values=("  ...", "", ""))

    def _on_open(self, event):
        item = self._tree.focus()
        if not item:
            return
        children = self._tree.get_children(item)
        if children and str(children[0]).endswith(_PLACEHOLDER):
            for ch in children:
                self._tree.delete(ch)
            if item in self._node_data:
                a1, by_a2 = self._node_data[item]
                self._expand_a1(item, a1, by_a2)

    def _expand_a1(self, a1_node, a1, by_a2):
        tree   = self._tree
        a1_disp = _disp(a1);  a1_exp = _expr_triple(a1)
        for a2, a3_list in sorted(by_a2.items()):
            a2_disp = _disp(a2);  a2_exp = _expr_triple(a2)
            a2_node = tree.insert(a1_node, "end", text="",
                                  values=(a1_disp, a2_disp, f"[{len(a3_list)} A2]"),
                                  open=False, tags=("a2_node",))
            for a3 in sorted(a3_list):
                a3_disp = _disp(a3);  a3_exp = _expr_triple(a3)
                expr = "{} o MSC o {} o MSC o {} o MSC".format(
                    a3_exp, a2_exp, a1_exp)
                iid = tree.insert(a2_node, "end", text="",
                                  values=(a1_disp, a2_disp, a3_disp),
                                  tags=("a3_leaf",))
                self._node_expr[iid] = expr

    # ---- flat mode ----------------------------------------------------------

    def _build_flat_async(self, results, start):
        if not self.winfo_exists():
            return
        tree = self._tree
        end  = min(start + _BATCH, len(results))
        for i in range(start, end):
            a1, a2, a3 = results[i]
            a1d = _disp(a1);  a1e = _expr_triple(a1)
            a2d = _disp(a2);  a2e = _expr_triple(a2)
            a3d = _disp(a3);  a3e = _expr_triple(a3)
            expr = "{} o MSC o {} o MSC o {} o MSC".format(a3e, a2e, a1e)
            iid = tree.insert("", "end", text="",
                              values=(a1d, a2d, a3d), tags=("flat_row",))
            self._node_expr[iid] = expr
        loaded = end; total = len(results)
        try:
            if loaded < total:
                pct = int(100 * loaded / total)
                self._load_lbl.configure(
                    text=f"Caricamento... {loaded:,} / {total:,}  ({pct}%)")
                self._flat_job = self.after(
                    10, lambda: self._build_flat_async(results, loaded))
            else:
                self._load_lbl.configure(
                    text=f"Tabella: {total:,} righe  (doppio clic -> Explorer)")
                self._flat_job = None
        except tk.TclError:
            pass

    # ---- sort ---------------------------------------------------------------

    def _sort_col(self, col):
        if self._group_mode.get():
            return
        items = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        items.sort()
        for idx, (_, k) in enumerate(items):
            self._tree.move(k, "", idx)

    # ---- interaction --------------------------------------------------------

    def _on_select(self, event):
        item = self._tree.focus()
        if not item:
            return
        expr = self._node_expr.get(item)
        if expr:
            short = expr[:90] + "..." if len(expr) > 90 else expr
            self._sel_lbl.configure(text=short)
            self._open_btn.configure(state="normal")
        else:
            self._sel_lbl.configure(text="")
            self._open_btn.configure(state="disabled")

    def _on_double_click(self, event):
        item = self._tree.identify_row(event.y)
        if item and item in self._node_expr:
            self._send_to_explorer(self._node_expr[item])

    def _open_selected_in_explorer(self):
        item = self._tree.focus()
        expr = self._node_expr.get(item)
        if expr:
            self._send_to_explorer(expr)

    def _send_to_explorer(self, expr):
        app = self._app
        app._explorer_entry.delete("1.0", "end")
        app._explorer_entry.insert("1.0", expr)
        app._switch_to_explorer()
        app._flash_entry()
        app._explorer_calc()
        self.after(100, self.lift)

    # ---- export -------------------------------------------------------------

    def _export_txt(self):
        if not self._results:
            return
        lbl = "T-inv" if self._target_inv.get() else "T"
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".txt",
            filetypes=[("Testo", "*.txt"), ("Tutti", "*.*")],
            title=f"Salva decomposizioni {lbl}")
        if not path:
            return
        W = 28
        target = self._current_target()
        lines = [
            f"{lbl} = [" + ", ".join(str(x) for x in target) + "]",
            "Decomposizioni trovate: {:,}".format(len(self._results)),
            "",
            "  {:>6}   {:<{w}}  {:<{w}}  A2".format("#", "A0", "A1", w=W),
            "-" * (14 + 3 * W + 6),
        ]
        for i, (a1, a2, a3) in enumerate(self._results, 1):
            lines.append("{:>6}.  {:<{w}}  {:<{w}}  {}".format(
                i, _disp(a1), _disp(a2), _disp(a3), w=W))
        lines.append("")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("Esportato",
                                "Salvate {:,} righe in:\n{}".format(
                                    len(self._results), path),
                                parent=self)
        except OSError as exc:
            messagebox.showerror("Errore", str(exc), parent=self)

    def _export_csv(self):
        """Esporta le decomposizioni in CSV con separatore ;."""
        if not self._results:
            return
        import csv
        lbl = "T-inv" if self._target_inv.get() else "T"
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Tutti", "*.*")],
            title=f"Salva decomposizioni {lbl} — CSV")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";", quotechar='"',
                               quoting=csv.QUOTE_ALL, lineterminator="\n")
                w.writerow(["#", "A0", "A1", "A2"])
                for i, (a1, a2, a3) in enumerate(self._results, 1):
                    w.writerow([i, _disp(a1), _disp(a2), _disp(a3)])
            messagebox.showinfo("Esportato",
                                f"Salvate {len(self._results):,} righe in:\n{path}",
                                parent=self)
        except OSError as exc:
            messagebox.showerror("Errore", str(exc), parent=self)

    def _export_html(self):
        """Esporta le decomposizioni in HTML."""
        if not self._results:
            return
        import html as _h
        lbl = "T⁻¹" if self._target_inv.get() else "T"
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("Tutti", "*.*")],
            title=f"Salva decomposizioni {lbl} — HTML")
        if not path:
            return
        target = self._current_target()
        target_str = "[" + ", ".join(str(x) for x in target) + "]"
        rows = ""
        for i, (a1, a2, a3) in enumerate(self._results, 1):
            rows += (f"<tr><td style='text-align:right'>{i}</td>"
                     f"<td><code>{_h.escape(_disp(a1))}</code></td>"
                     f"<td><code>{_h.escape(_disp(a2))}</code></td>"
                     f"<td><code>{_h.escape(_disp(a3))}</code></td></tr>\n")
        html_str = f"""<!DOCTYPE html><html lang='it'><head><meta charset='UTF-8'>
<title>Decomposizioni {_h.escape(lbl)}</title>
<style>body{{font-family:sans-serif;padding:20px;max-width:900px;margin:auto}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:4px 10px;font-family:'Courier New',monospace;font-size:0.84em}}
th{{background:#f0f4f0}}tr:nth-child(even){{background:#fafafa}}
code{{font-family:'Courier New',monospace;font-size:0.9em}}</style></head>
<body>
<h2>Decomposizioni — {_h.escape(lbl)}</h2>
<p><code>{_h.escape(target_str)}</code></p>
<p>Trovate: <strong>{len(self._results):,}</strong></p>
<table><tr><th>#</th><th>A0</th><th>A1</th><th>A2</th></tr>
{rows}</table>
<p style='color:#888;font-size:0.85em'>Generato da Gioco delle 27 Carte</p>
</body></html>"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_str)
            import webbrowser
            webbrowser.open(f"file://{path}")
        except OSError as exc:
            messagebox.showerror("Errore", str(exc), parent=self)
