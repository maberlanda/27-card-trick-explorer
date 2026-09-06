"""
Tab "📊 Distribuzione"

Calcola (in background) per ogni T raggiungibile quante decomposizioni
Kronecker possiede, poi mostra:
  - istogramma su canvas tkinter
  - tabella: k decomposizioni → quante T
  - statistiche aggregate
"""
import tkinter as tk
from tkinter import ttk
import threading, queue


from .common import EtaEstimator


class DistributionFrame(ttk.Frame):

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._result   = None
        self._computing = False
        self._q        = queue.Queue()
        self._build_ui()

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Intestazione
        hdr = ttk.Frame(self, padding=(10, 8, 10, 2))
        hdr.grid(row=0, column=0, sticky="ew")
        ttk.Label(hdr,
                  text="Distribuzione delle decomposizioni su tutti i T raggiungibili",
                  font=("Segoe UI", 12, "bold"),
                  foreground="#1a3a5c").pack(side="left")

        # Controlli
        ctrl = ttk.Frame(self, padding=(10, 4, 10, 4))
        ctrl.grid(row=1, column=0, sticky="ew")
        self._btn = ttk.Button(ctrl, text="▶  Calcola distribuzione",
                               command=self._start_compute)
        self._btn.pack(side="left")
        self._prog_bar = ttk.Progressbar(ctrl, orient="horizontal",
                                          mode="determinate", maximum=216,
                                          value=0, length=300)
        self._prog_bar.pack(side="left", padx=(12, 6))
        self._prog_lbl = ttk.Label(ctrl, text="",
                                    font=("Courier New", 9), foreground="#555", width=30)
        self._prog_lbl.pack(side="left")

        # Notebook: Istogramma | Tabella
        nb = ttk.Notebook(self)
        nb.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))

        self._histo_tab = ttk.Frame(nb)
        self._table_tab = ttk.Frame(nb)
        nb.add(self._histo_tab, text="  Istogramma  ")
        nb.add(self._table_tab, text="  Tabella dati  ")

        self._build_histo_tab()
        self._build_table_tab()

    def _build_histo_tab(self):
        fr = self._histo_tab
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(fr, background="#FAFBFC",
                                  highlightthickness=0)
        vsb = ttk.Scrollbar(fr, orient="vertical",   command=self._canvas.yview)
        hsb = ttk.Scrollbar(fr, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        self._placeholder(self._canvas,
                          "Clicca '▶ Calcola distribuzione' per avviare il calcolo.\n"
                          "Tempo atteso: ~30 secondi.")

    def _build_table_tab(self):
        fr = self._table_tab
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(0, weight=1)

        self._tbl_txt = tk.Text(fr, font=("Courier New", 10),
                                 state="disabled", wrap="none",
                                 background="#FAFBFC", relief="flat")
        vsb = ttk.Scrollbar(fr, orient="vertical",   command=self._tbl_txt.yview)
        hsb = ttk.Scrollbar(fr, orient="horizontal", command=self._tbl_txt.xview)
        self._tbl_txt.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tbl_txt.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._placeholder_txt(
            "Calcolo non ancora avviato.\n"
            "Premi '▶ Calcola distribuzione'.")

    # ─── Calcolo in background ────────────────────────────────────────────────

    def _start_compute(self):
        if self._computing:
            return
        self._computing = True
        self._btn.configure(state="disabled", text="⏳  Calcolo in corso…")
        self._prog_bar["value"] = 0
        self._prog_lbl.configure(text="")
        self._q = queue.Queue()
        self._eta = EtaEstimator()
        threading.Thread(target=self._compute_worker, daemon=True).start()
        self._poll_queue()

    def _compute_worker(self):
        try:
            from ..core.config import get_config
            cfg = get_config()
            nw = cfg.effective_n_workers if cfg.get("use_parallel", True) else 1
            result = _compute_distribution_fast(
                n_workers=nw,
                progress_cb=lambda done, n: self._q.put(("P", done - 1, n)))
            self._q.put(("DONE", result))
        except Exception as exc:
            self._q.put(("ERR", str(exc)))

    def _poll_queue(self):
        try:
            item = self._q.get_nowait()
            if item[0] == "P":
                _, i, n = item
                self._prog_bar["value"] = i + 1
                self._prog_lbl.configure(
                    text=f"{i+1:>3}/{n}  iterazione esterna"
                         f"{self._eta.text(i + 1, n)}")
            elif item[0] == "DONE":
                self._result    = item[1]
                self._computing = False
                self._btn.configure(state="normal", text="▶  Ricalcola")
                self._prog_bar["value"] = 216
                self._prog_lbl.configure(text="✓  completato")
                self._show_results()
                return
            elif item[0] == "ERR":
                self._computing = False
                self._btn.configure(state="normal", text="▶  Riprova")
                self._prog_lbl.configure(text=f"✗  {item[1][:50]}")
                return
        except Exception:
            pass
        if self._computing:
            self.after(50, self._poll_queue)

    # ─── Visualizzazione risultati ────────────────────────────────────────────

    def _show_results(self):
        r = self._result
        self._draw_histogram(r)
        self._fill_table(r)

    def _draw_histogram(self, r):
        histo   = r["histogram"]   # {k_decomp: n_T}
        total_T = r["total_T"]
        canvas  = self._canvas
        canvas.delete("all")

        if not histo:
            self._placeholder(canvas, "Nessun dato.")
            return

        w  = max(canvas.winfo_width(),  600)
        h  = max(canvas.winfo_height(), 400)
        lm, rm, tm, bm = 80, 30, 30, 60  # margini

        keys  = sorted(histo.keys())
        vals  = [histo[k] for k in keys]
        max_v = max(vals)

        bar_w    = max(8, min(40, (w - lm - rm) // max(len(keys), 1) - 4))
        x_step   = (w - lm - rm) / max(len(keys), 1)
        y_scale  = (h - tm - bm) / max_v if max_v else 1

        # Asse Y (griglia)
        canvas.create_line(lm, tm, lm, h - bm, fill="#ccc", width=1)
        for frac in [0.25, 0.5, 0.75, 1.0]:
            yy = h - bm - frac * (h - tm - bm)
            canvas.create_line(lm, yy, w - rm, yy, fill="#eee", width=1, dash=(4, 4))
            canvas.create_text(lm - 5, yy, text=f"{int(frac*max_v):,}",
                                anchor="e", font=("Segoe UI", 8), fill="#666")

        # Barre
        for i, (k, v) in enumerate(zip(keys, vals)):
            x0  = lm + i * x_step + (x_step - bar_w) / 2
            x1  = x0 + bar_w
            y0  = h - bm - v * y_scale
            y1  = h - bm
            v / total_T * 100
            canvas.create_rectangle(x0, y0, x1, y1, fill="#4E79A7",
                                     outline="#2C5F8A", width=1)
            # Etichetta sopra barra
            if bar_w >= 16:
                canvas.create_text((x0+x1)/2, y0 - 3,
                                    text=f"{v:,}", anchor="s",
                                    font=("Segoe UI", 7), fill="#333")
            # Etichetta X
            canvas.create_text((x0+x1)/2, h - bm + 4,
                                text=str(k), anchor="n",
                                font=("Courier New", 8), fill="#444")

        # Titoli assi
        canvas.create_text(lm + (w - lm - rm)/2, h - 10,
                            text="numero di decomposizioni Kronecker",
                            font=("Segoe UI", 9), fill="#444")
        canvas.create_text(12, tm + (h - tm - bm)/2,
                            text="# T raggiungibili", angle=90,
                            font=("Segoe UI", 9), fill="#444")
        canvas.create_text(lm + (w - lm - rm)/2, 10,
                            text=f"Distribuzione su {total_T:,} permutazioni T distinte",
                            font=("Segoe UI", 10, "bold"), fill="#1a3a5c")

        canvas.configure(scrollregion=canvas.bbox("all"))

    def _fill_table(self, r):
        txt     = self._tbl_txt
        histo   = r["histogram"]
        total_T = r["total_T"]
        total_d = r["total_decomp"]

        txt.configure(state="normal")
        txt.delete("1.0", "end")
        txt.tag_configure("hdr", font=("Courier New", 10, "bold"),   foreground="#1a3a5c")
        txt.tag_configure("row", font=("Courier New", 10),           foreground="#222")
        txt.tag_configure("sep", foreground="#ccc")
        txt.tag_configure("sum", font=("Courier New", 10, "bold"),   foreground="#333")
        txt.tag_configure("note",font=("Segoe UI",   9,  "italic"),  foreground="#666")

        txt.insert("end",
                   f"  Totale T raggiungibili : {total_T:>10,}\n"
                   f"  Totale decomposizioni  : {total_d:>10,}\n"
                   f"  Media per T            : {total_d/total_T:>10.1f}\n\n",
                   "sum")
        txt.insert("end",
                   f"  {'k-decomp':>10}  {'# T':>10}  {'% T':>8}  {'cum%':>8}\n"
                   f"  {'─'*10}  {'─'*10}  {'─'*8}  {'─'*8}\n",
                   "hdr")

        cum = 0
        for k in sorted(histo):
            n   = histo[k]
            cum += n
            pct = n   / total_T * 100
            cpct= cum  / total_T * 100
            txt.insert("end",
                       f"  {k:>10}  {n:>10,}  {pct:>7.2f}%  {cpct:>7.2f}%\n",
                       "row")

        txt.insert("end", "\n", "sep")
        txt.insert("end",
                   "  Nota: k-decomp = numero di decomposizioni A2∘MSC∘A1∘MSC∘A0∘MSC\n"
                   "  per quella specifica T. T con k=0 non sono raggiungibili\n"
                   "  dal meccanismo Kronecker.\n",
                   "note")
        txt.configure(state="disabled")

    # ─── Helper ───────────────────────────────────────────────────────────────

    def _placeholder(self, canvas, text):
        canvas.delete("all")
        canvas.create_text(300, 200, text=text,
                            font=("Segoe UI", 11, "italic"),
                            fill="#aaa", justify="center")

    def _placeholder_txt(self, text):
        t = self._tbl_txt
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("end", text)
        t.configure(state="disabled")

    def _on_canvas_resize(self, event):
        if self._result:
            self._draw_histogram(self._result)


# ─────────────────────────────────────────────────────────────────────────────
# Calcolo vettorizzato della distribuzione
# ─────────────────────────────────────────────────────────────────────────────

def _compute_distribution_fast(progress_cb=None, n_workers=None):
    """
    Calcolo della distribuzione delle decomposizioni.

    Delega alla versione parallela in core.analysis (ProcessPoolExecutor sui
    216 indici esterni), che ha un fallback sequenziale automatico.
    """
    from ..core.analysis import compute_distribution_parallel
    return compute_distribution_parallel(n_workers=n_workers, progress_cb=progress_cb)
