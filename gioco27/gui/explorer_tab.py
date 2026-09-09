"""
Tab "🔬 Explorer" — analisi simbolica, traccia di riscrittura, forma canonica,
matrici 27×27 di T e T⁻¹.

Mixin per App: fornisce _build_explorer_tab() e tutti i callback Explorer.
Estratto da app.py (v2.8.0) senza modifiche funzionali.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from ..core.algebra import AlgebraEngine, Controller, CanonicalForm
from ..core.constants import PERM3
from ..core.kronecker import try_kron_decompose, decomposition_context
from .common import configure_matrix_tags, insert_colored
from .decomposition import DecompositionDialog
from .shuffle import ShuffleViewerFrame


class ExplorerTabMixin:
    """Metodi del tab Explorer. Richiede gli attributi/metodi di App:
    _open_export_dialog(), _notify_T_changed(), _last_T_perm, _last_inv_perm."""

    def _build_explorer_tab(self, parent):
        outer = ttk.Frame(parent, padding=10)
        outer.rowconfigure(2, weight=1)
        outer.columnconfigure(0, weight=1)

        self._explorer_ctrl        = Controller()
        self._explorer_last_result = None

        hdr = ttk.Frame(outer)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(hdr, text="🔬  Explorer Algebrico",
                  font=("Segoe UI", 13, "bold"), foreground="#1F4E79").pack(side="left")
        ttk.Label(hdr,
                  text="   — analisi simbolica, traccia di riscrittura e forma canonica",
                  font=("Segoe UI", 10, "italic"), foreground="#555").pack(side="left")

        inp_frame = ttk.LabelFrame(outer, text="  Espressione T  ", padding=(10, 6))
        inp_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        inp_frame.columnconfigure(0, weight=1)

        self._explorer_entry = tk.Text(
            inp_frame, height=3, font=("Consolas", 11),
            bg="#FAFCFF", fg="#1a1a2e", padx=6, pady=4, relief="flat", wrap="word")
        self._explorer_entry.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self._explorer_entry.bind("<Control-Return>", lambda e: self._explorer_calc())
        self._explorer_entry.bind("<<Modified>>", self._explorer_input_changed)
        self._explorer_entry.edit_modified(False)

        btn_row = ttk.Frame(inp_frame)
        btn_row.grid(row=1, column=0, sticky="w")
        ttk.Button(btn_row, text="▶  Calcola", style="Action.TButton",
                   command=self._explorer_calc).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text="✕  Pulisci", style="Preset.TButton",
                   command=self._explorer_clear).pack(side="left", padx=(0, 12))
        self._decomp_btn = ttk.Button(
            btn_row, text="🔍  Decomposizioni T⁻¹",
            state="disabled", command=self._explorer_find_decompositions)
        self._decomp_btn.pack(side="left", padx=(6, 0))
        self._exp_export_btn = ttk.Button(
            btn_row, text="📄  Esporta LaTeX / SVG",
            state="disabled",
            command=self._explorer_export)
        self._exp_export_btn.pack(side="left", padx=(6, 0))
        self._explorer_status = tk.StringVar(
            value="Scrivi un'espressione (es. P1 MSC J1) e premi  ▶ Calcola.")
        ttk.Label(btn_row, textvariable=self._explorer_status,
                  font="GiocoHelp", foreground="#333",
                  wraplength=600).pack(side="left")

        enb = ttk.Notebook(outer)
        enb.grid(row=2, column=0, sticky="nsew")
        self._explorer_nb = enb
        self._build_explorer_tab_numeric(enb)
        self._build_explorer_tab_rewrite(enb)
        self._build_explorer_tab_algebra(enb)
        self._build_explorer_tab_steps(enb)
        self._build_explorer_tab_canonical(enb)
        self._build_explorer_tab_matrix(enb)
        self._build_explorer_tab_shuffle(enb)
        return outer

    # ── Explorer sub-tab helpers ──────────────────────────────────────────────

    def _exp_scrolled(self, parent, height=4, mono=True, wrap="word"):
        """(frame, Text) con scrollbar verticale. Usa pack sul frame."""
        font = ("Consolas", 9) if mono else ("Segoe UI", 10)
        fr = ttk.Frame(parent)
        fr.rowconfigure(0, weight=1)
        fr.columnconfigure(0, weight=1)
        w = tk.Text(fr, height=height, font=font,
                    bg="#FAFCFF", fg="#1a1a2e",
                    padx=6, pady=4, relief="flat", wrap=wrap, state="disabled")
        sb = ttk.Scrollbar(fr, orient="vertical", command=w.yview)
        w.configure(yscrollcommand=sb.set)
        w.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        return fr, w

    def _build_explorer_tab_shuffle(self, nb):
        """Tab '\U0001f3b4 Mescolamento' — simulazione visiva passo-per-passo."""
        self._shuffle_viewer = ShuffleViewerFrame(nb, self)
        nb.add(self._shuffle_viewer, text="  \U0001f3b4  Mescolamento  ")
        return self._shuffle_viewer


    def _exp_set(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", str(text))
        widget.configure(state="disabled")

    def _exp_set_colored(self, widget, text, base_font=("Consolas", 9)):
        """Come _exp_set, ma colora i nomi GEN3 (SCD_U, CDS_U, ...) con i
        6 colori della palette standard (PERM3_COLORS).
        base_font permette di rispettare la dimensione del widget di
        destinazione (es. i fattori canonici usano Consolas 10)."""
        if not getattr(widget, "_mx_tags_done", False):
            configure_matrix_tags(widget, base_font=base_font)
            widget._mx_tags_done = True
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        insert_colored(widget, str(text))
        widget.configure(state="disabled")

    def _exp_lbl(self, parent, text, bold=False):
        font = ("Segoe UI", 10, "bold") if bold else ("Segoe UI", 10)
        ttk.Label(parent, text=text, font=font,
                  foreground="#1F4E79").pack(anchor="w", pady=(6, 1))

    def _build_explorer_tab_numeric(self, nb):
        fr = ttk.Frame(nb, padding=8)
        nb.add(fr, text="  🔢 Numerico  ")

        self._exp_lbl(fr, "Forma normalizzata", bold=True)
        _f, self._exp_norm = self._exp_scrolled(fr, height=2)
        _f.pack(fill="x")

        self._exp_lbl(fr, "Riepilogo passi di riscrittura")
        _f, self._exp_steps_sum = self._exp_scrolled(fr, height=2)
        _f.pack(fill="x")

        self._exp_lbl(fr, "Vettore di permutazione  T[0..26]", bold=True)
        _f, self._exp_perm = self._exp_scrolled(fr, height=4)
        _f.pack(fill="x")

        row2 = ttk.Frame(fr)
        row2.pack(fill="x", pady=4)
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)

        col_a = ttk.Frame(row2)
        col_a.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._exp_lbl(col_a, "Periodo (ordine della permutazione)")
        _f, self._exp_period = self._exp_scrolled(col_a, height=1)
        _f.pack(fill="x")
        self._exp_lbl(col_a, "Firma canonica")
        _f, self._exp_sig = self._exp_scrolled(col_a, height=2)
        _f.pack(fill="x")

        col_b = ttk.Frame(row2)
        col_b.grid(row=0, column=1, sticky="nsew")
        self._exp_lbl(col_b, "Permutazione inversa")
        _f, self._exp_inv = self._exp_scrolled(col_b, height=4)
        _f.pack(fill="x")

        self._exp_lbl(fr, "Log / Errori")
        _f, self._exp_log = self._exp_scrolled(fr, height=3)
        _f.pack(fill="x")

    def _build_explorer_tab_rewrite(self, nb):
        fr = ttk.Frame(nb, padding=8)
        nb.add(fr, text="  ✏️ Traccia riscrittura  ")
        fr.rowconfigure(1, weight=1)
        fr.columnconfigure(0, weight=1)
        ttk.Label(fr,
                  text="Ogni passo: regola applicata · espressione prima · dopo",
                  font=("Segoe UI", 10, "italic"),
                  foreground="#555").grid(row=0, column=0, sticky="w", pady=(0, 4))
        tf = ttk.Frame(fr)
        tf.grid(row=1, column=0, sticky="nsew")
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)
        self._exp_rewrite = tk.Text(
            tf, font=("Consolas", 9), bg="#FAFCFF", fg="#1a1a2e",
            padx=6, pady=4, relief="flat", state="disabled", wrap="none")
        sbv = ttk.Scrollbar(tf, orient="vertical",   command=self._exp_rewrite.yview)
        sbh = ttk.Scrollbar(tf, orient="horizontal", command=self._exp_rewrite.xview)
        self._exp_rewrite.configure(yscrollcommand=sbv.set, xscrollcommand=sbh.set)
        self._exp_rewrite.grid(row=0, column=0, sticky="nsew")
        sbv.grid(row=0, column=1, sticky="ns")
        sbh.grid(row=1, column=0, sticky="ew")

    def _build_explorer_tab_algebra(self, nb):
        fr = ttk.Frame(nb, padding=8)
        nb.add(fr, text="  🧮 Forma algebrica  ")
        fr.columnconfigure(0, weight=1)
        ttk.Label(fr, text="Forma normale strutturata  K ∘ MSCᵏ",
                  font=("Segoe UI", 10, "italic"),
                  foreground="#555").pack(anchor="w", pady=(0, 6))
        row_meta = ttk.Frame(fr)
        row_meta.pack(fill="x", pady=(0, 4))
        row_meta.columnconfigure(0, weight=1)
        row_meta.columnconfigure(1, weight=1)
        for col_i, (label, attr) in enumerate([
            ("Tipo forma normale",    "_exp_nf_kind"),
            ("Esponente MSC (mod 3)", "_exp_nf_msc"),
        ]):
            box = ttk.LabelFrame(row_meta, text=f"  {label}  ", padding=(6, 4))
            box.grid(row=0, column=col_i, sticky="nsew", padx=4)
            w = tk.Text(box, height=1, font=("Consolas", 10, "bold"),
                        bg="#EBF5FB", fg="#1F4E79",
                        padx=4, pady=2, relief="flat", state="disabled")
            w.pack(fill="x")
            setattr(self, attr, w)
        self._exp_lbl(fr, "Forma simbolica leggibile", bold=True)
        _f, self._exp_nf_sym = self._exp_scrolled(fr, height=2)
        _f.pack(fill="x")
        self._exp_lbl(fr, "Fattori Kronecker residui  P₁, P₂, P₃")
        _f, self._exp_nf_kron = self._exp_scrolled(fr, height=4)
        _f.pack(fill="x")
        self._exp_lbl(fr, "Note")
        _f, self._exp_nf_notes = self._exp_scrolled(fr, height=3)
        _f.pack(fill="x")

    def _build_explorer_tab_steps(self, nb):
        fr = ttk.Frame(nb, padding=8)
        nb.add(fr, text="  📋 Passi parziali  ")
        fr.rowconfigure(1, weight=1)
        fr.columnconfigure(0, weight=1)
        ttk.Label(fr,
                  text="Permutazione parziale dopo ogni operazione elementare",
                  font=("Segoe UI", 10, "italic"),
                  foreground="#555").grid(row=0, column=0, sticky="w", pady=(0, 4))
        tf = ttk.Frame(fr)
        tf.grid(row=1, column=0, sticky="nsew")
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)
        self._exp_eval = tk.Text(
            tf, font=("Consolas", 9), bg="#FAFCFF", fg="#1a1a2e",
            padx=6, pady=4, relief="flat", state="disabled", wrap="none")
        sbv = ttk.Scrollbar(tf, orient="vertical",   command=self._exp_eval.yview)
        sbh = ttk.Scrollbar(tf, orient="horizontal", command=self._exp_eval.xview)
        self._exp_eval.configure(yscrollcommand=sbv.set, xscrollcommand=sbh.set)
        self._exp_eval.grid(row=0, column=0, sticky="nsew")
        sbv.grid(row=0, column=1, sticky="ns")
        sbh.grid(row=1, column=0, sticky="ew")

    def _build_explorer_tab_canonical(self, nb):
        fr = ttk.Frame(nb, padding=8)
        nb.add(fr, text="  ⧆ Forma canonica  ")
        fr.columnconfigure(0, weight=1)
        ttk.Label(fr,
                  text="Forma canonica globale  K ∘ MSCᵏ  "
                       "(disponibile solo per espressioni senza J)",
                  font=("Segoe UI", 10, "italic"),
                  foreground="#555").pack(anchor="w", pady=(0, 8))
        for label, attr in [
            ("Disponibile",     "_exp_can_avail"),
            ("Forma simbolica", "_exp_can_sym"),
        ]:
            ttk.Label(fr, text=f"{label}:",
                      font=("Segoe UI", 10, "bold"),
                      foreground="#1F4E79").pack(anchor="w", pady=(4, 1))
            h = 1 if label == "Disponibile" else 2
            _f, w = self._exp_scrolled(fr, height=h)
            _f.pack(fill="x")
            setattr(self, attr, w)
        ttk.Separator(fr, orient="horizontal").pack(fill="x", pady=6)
        self._exp_lbl(fr, "Fattori Kronecker  P₁, P₂, P₃", bold=True)
        self._exp_can_factors = []
        for lab in ("P₁", "P₂", "P₃"):
            row = ttk.Frame(fr)
            row.pack(fill="x", pady=1)
            ttk.Label(row, text=f"  {lab} =",
                      font=("Consolas", 10),
                      foreground="#1F4E79", width=6).pack(side="left")
            w = tk.Text(row, height=1, font=("Consolas", 10),
                        bg="#EBF5FB", fg="#1F4E79",
                        padx=4, pady=2, relief="flat", state="disabled")
            w.pack(side="left", fill="x", expand=True)
            self._exp_can_factors.append(w)
        self._exp_lbl(fr, "Esponente MSC  k")
        _f, self._exp_can_exp = self._exp_scrolled(fr, height=1)
        _f.pack(fill="x")
        self._exp_lbl(fr, "Note / Verifica coerenza")
        _f, self._exp_can_notes = self._exp_scrolled(fr, height=4)
        _f.pack(fill="x")


    # ── Tab Matrice (T e T⁻¹ affiancate) ─────────────────────────────────────

    def _build_explorer_tab_matrix(self, nb):
        """
        Tab '📐 Matrice' — griglie 27×27 di T (sinistra) e T⁻¹ (destra),
        con i fattori Kronecker canonici di ciascuna mostrati sotto.
        """
        CELL  = 12
        SMALL = 20

        outer = ttk.Frame(nb, padding=8)
        nb.add(outer, text="  \U0001f4d0  Matrice  ")
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(1, weight=1)

        cv_size = CELL * 27 + 2

        def make_panel(col, title_text, tag):
            """Crea un pannello con griglia 27×27 + fattori Kronecker."""
            panel = ttk.Frame(outer, relief="groove", borderwidth=1)
            panel.grid(row=0, column=col, rowspan=2, sticky="nsew",
                       padx=(0 if col else 0, 6 if col == 0 else 0))
            panel.columnconfigure(0, weight=1)
            panel.rowconfigure(1, weight=1)

            title = ttk.Label(panel,
                              text=title_text,
                              font=("Segoe UI", 11, "bold"),
                              foreground="#1F4E79",
                              anchor="center")
            title.grid(row=0, column=0, sticky="ew", pady=(6, 4))

            cv = tk.Canvas(panel, width=cv_size, height=cv_size,
                           bg="white", highlightthickness=1,
                           highlightbackground="#AAAAAA")
            cv.grid(row=1, column=0, sticky="n", padx=6)
            self._draw_empty_grid(cv, 27, CELL)

            cf_lbl = ttk.Label(panel,
                               text="Forma canonica:  —",
                               font=("Consolas", 9),
                               foreground="#555")
            cf_lbl.grid(row=2, column=0, sticky="w", padx=8, pady=(4, 2))

            factors_row = ttk.Frame(panel)
            factors_row.grid(row=3, column=0, sticky="w", padx=8, pady=(0, 8))
            fcvs, flbls = [], []
            for i in range(3):
                col_fr = ttk.Frame(factors_row)
                col_fr.pack(side="left", padx=8)
                fcv = tk.Canvas(col_fr, width=SMALL*3+2, height=SMALL*3+2,
                                bg="white", highlightthickness=1,
                                highlightbackground="#888")
                fcv.pack()
                self._draw_empty_grid(fcv, 3, SMALL)
                flbl = ttk.Label(col_fr, text=f"P{i+1} = —",
                                 font=("Consolas", 9), foreground="#1F4E79")
                flbl.pack(pady=(2, 0))
                fcvs.append(fcv)
                flbls.append(flbl)

            return cv, cf_lbl, fcvs, flbls

        (self._mat_cv_t,   self._mat_lbl_t,   self._mat_fcvs_t,   self._mat_flbls_t
         ) = make_panel(0, "Permutazione  T", "T")
        (self._mat_cv_inv, self._mat_lbl_inv, self._mat_fcvs_inv, self._mat_flbls_inv
         ) = make_panel(1, "Permutazione  T⁻\xb9", "T_inv")

        self._mat_cell_size = CELL
        self._mat_small_size = SMALL

    def _draw_empty_grid(self, canvas, n, cell):
        """Disegna una griglia n×n vuota sul canvas."""
        canvas.delete("all")
        size = n * cell
        canvas.create_rectangle(0, 0, size+1, size+1, fill="white", outline="")
        for i in range(n + 1):
            x = i * cell
            if n == 27:
                if   i % 9 == 0: col, w = "#333333", 2
                elif i % 3 == 0: col, w = "#777777", 1
                else:             col, w = "#CCCCCC", 1
            else:
                col, w = "#444444", (2 if (i == 0 or i == n) else 1)
            canvas.create_line(x, 0, x, size+1, fill=col, width=w)
            canvas.create_line(0, x, size+1, x, fill=col, width=w)
        canvas.create_rectangle(0, 0, size, size, outline="#333333", width=2)

    def _draw_perm_on_canvas(self, canvas, perm, cell, color="#27AE60"):
        """Disegna la matrice di permutazione: perm[col]=row → quadratino verde."""
        n = len(perm)
        self._draw_empty_grid(canvas, n, cell)
        pad = max(1, cell // 6)
        for col, row in enumerate(perm):
            x0, y0 = col*cell+pad, row*cell+pad
            x1, y1 = (col+1)*cell-pad, (row+1)*cell-pad
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

    def _fill_matrix_panel(self, perm27, canonical_form, cv, cf_lbl, fcvs, flbls):
        """Popola un pannello (T o T⁻¹): disegna griglia + fattori Kronecker."""
        CELL  = self._mat_cell_size
        SMALL = self._mat_small_size
        self._draw_perm_on_canvas(cv, perm27, CELL)
        if canonical_form is not None:
            try:
                names = canonical_form.kron_factor_names()
                sym   = canonical_form.symbolic()
                cf_lbl.config(text=f"Forma canonica:  {sym}")
                for i, (fcv, flbl) in enumerate(zip(fcvs, flbls)):
                    self._draw_perm_on_canvas(fcv, canonical_form.kron_factors[i], SMALL)
                    flbl.config(text=f"P{i+1} = {names[i]}")
            except Exception:
                cf_lbl.config(text="Forma canonica:  errore nel calcolo")
        else:
            # Fallback: prova ad estrarre i fattori direttamente dalla matrice
            try:
                factors = try_kron_decompose(perm27)
            except Exception:
                factors = None
            if factors is not None:
                f3, f2, f1 = factors
                cf_lbl.config(
                    text=f"Forma canonica (da matrice):  {f3} ⊗ {f2} ⊗ {f1}")
                for fcv, flbl, fname, fperm in zip(
                        fcvs, flbls,
                        [f"f₃={f3}", f"f₂={f2}", f"f₁={f1}"],
                        [PERM3[f3], PERM3[f2], PERM3[f1]]):
                    self._draw_perm_on_canvas(fcv, fperm, SMALL)
                    flbl.config(text=fname)
            else:
                cf_lbl.config(text="Forma canonica:  non disponibile")
                for fcv, flbl in zip(fcvs, flbls):
                    self._draw_empty_grid(fcv, 3, SMALL)
                    flbl.config(text="—")

    def _update_matrix_tab(self, r):
        """Aggiorna il tab Matrice con i dati del risultato r di Controller.process()."""
        perm     = r.get("perm")
        inv_perm = r.get("inverse_perm")
        cf_t     = r.get("canonical_form")  # CanonicalForm di T, o None
        if perm is None:
            return

        # Pannello T
        self._fill_matrix_panel(perm, cf_t,
                                 self._mat_cv_t, self._mat_lbl_t,
                                 self._mat_fcvs_t, self._mat_flbls_t)

        # Calcola forma canonica di T⁻¹ dalla forma canonica di T
        cf_inv = None
        if cf_t is not None and inv_perm is not None:
            try:
                k     = cf_t.msc_exp
                k_inv = (3 - k) % 3
                inv_f = [AlgebraEngine.inverse_perm(f) for f in cf_t.kron_factors]
                rot   = (2 * k_inv) % 3
                rot_f = AlgebraEngine.rotate_kron_factors(inv_f, rot)
                cf_inv = CanonicalForm(kron_factors=rot_f, msc_exp=k_inv)
            except Exception:
                cf_inv = None

        # Pannello T⁻¹
        if inv_perm is not None:
            self._fill_matrix_panel(inv_perm, cf_inv,
                                     self._mat_cv_inv, self._mat_lbl_inv,
                                     self._mat_fcvs_inv, self._mat_flbls_inv)

    def _reset_matrix_tab(self):
        """Svuota entrambi i pannelli del tab Matrice."""
        CELL  = self._mat_cell_size
        SMALL = self._mat_small_size
        for cv in (self._mat_cv_t, self._mat_cv_inv):
            self._draw_empty_grid(cv, 27, CELL)
        for lbl in (self._mat_lbl_t, self._mat_lbl_inv):
            lbl.config(text="Forma canonica:  —")
        for fcvs, flbls in ((self._mat_fcvs_t, self._mat_flbls_t),
                             (self._mat_fcvs_inv, self._mat_flbls_inv)):
            for fcv, flbl in zip(fcvs, flbls):
                self._draw_empty_grid(fcv, 3, SMALL)
                flbl.config(text="—")

    # ── Explorer callbacks ────────────────────────────────────────────────────

    def _invalidate_decompositions(self):
        self._decomposition_revision = getattr(self, "_decomposition_revision", 0) + 1
        self._last_decompositions = None

    def _explorer_input_changed(self, _event=None):
        if self._explorer_entry.edit_modified():
            self._invalidate_decompositions()
            self._explorer_entry.edit_modified(False)

    def _explorer_find_decompositions(self):
        """Apre il dialog con tutte le decomposizioni Kronecker di T e T⁻¹."""
        r = self._explorer_last_result
        if not r:
            return
        perm     = r.get("perm")
        inv_perm = r.get("inverse_perm")
        if not inv_perm:
            messagebox.showinfo("T⁻¹ non disponibile",
                                "T⁻¹ non disponibile per questa espressione.")
            return
        # Memorizza per il Protocollo
        self._last_T_perm   = perm
        self._last_inv_perm = inv_perm
        self._invalidate_decompositions()
        revision = self._decomposition_revision

        def accept(context):
            if (revision != self._decomposition_revision
                    or self._explorer_last_result is not r):
                return
            self._last_decompositions = decomposition_context(context, perm, inv_perm)

        DecompositionDialog(self, perm, inv_perm, on_results=accept)

    def _flash_entry(self, widget=None):
        """Anima un flash giallo → bianco sull'entry dell'Explorer (500 ms)."""
        if widget is None:
            widget = self._explorer_entry
        # Colore di partenza (bianco) e picco (giallo pastello)
        r0, g0, b0 = 255, 255, 255   # bianco
        rp, gp, bp = 255, 255, 200   # giallo pastello #FFFFC8
        steps  = 10                  # step per direzione
        hold   = 100                 # ms di pausa al picco
        dt     = 20                  # ms per step

        def interp(t, start, end):
            return int(start + (end - start) * t / steps)

        def set_bg(r, g, b):
            try:
                widget.configure(bg=f"#{r:02X}{g:02X}{b:02X}")
            except tk.TclError:
                pass

        def fade_in(i=0):
            if i > steps:
                widget.after(hold, fade_out)
                return
            set_bg(interp(i, r0, rp), interp(i, g0, gp), interp(i, b0, bp))
            widget.after(dt, lambda: fade_in(i + 1))

        def fade_out(i=0):
            if i > steps:
                set_bg(r0, g0, b0)   # assicura il bianco finale
                return
            set_bg(interp(i, rp, r0), interp(i, gp, g0), interp(i, bp, b0))
            widget.after(dt, lambda: fade_out(i + 1))

        fade_in()

    def _explorer_calc(self, _event=None):
        self._invalidate_decompositions()
        text = self._explorer_entry.get("1.0", "end-1c").strip()
        if not text:
            self._explorer_last_result = None
            self._explorer_status.set("⚠  Nessuna espressione inserita.")
            return
        result = self._explorer_ctrl.process(text)
        self._explorer_last_result = result
        if not result["ok"]:
            self._explorer_status.set("✗  Errore — vedi scheda Numerico (Log)")
            self._exp_set(self._exp_log, result["error"])
            self._explorer_clear_results(except_log=True)
        else:
            period = result["period"]
            sig    = result["signature"][:40]
            self._explorer_status.set(
                f"✓  Periodo: {period}   Firma: {sig}…")
            self._exp_set(self._exp_log, "")
            self._explorer_display(result)
            if result.get('perm') is not None:
                self._notify_T_changed(list(result['perm']))
            if hasattr(self, "_exp_export_btn") and result.get("perm") is not None:
                self._exp_export_btn.configure(state="normal")
            if hasattr(self, "_decomp_btn") and result.get("inverse_perm"):
                self._decomp_btn.configure(state="normal")

    def _explorer_clear(self):
        self._explorer_entry.delete("1.0", "end")
        self._explorer_clear_results()
        self._explorer_status.set("")

    def _explorer_export(self):
        r = getattr(self, "_explorer_last_result", None)
        if not r or not r.get("ok") or r.get("perm") is None:
            return
        import numpy as np
        perm    = list(r["perm"])
        inv     = list(r.get("inverse_perm") or np.argsort(perm))
        decomps = getattr(self, "_last_decompositions", None)
        self._open_export_dialog(
            perm=perm, inv_perm=inv,
            decompositions=decomps,
            title_label=r.get("normalized_str", "T"))

    def _explorer_clear_results(self, except_log=False):
        self._invalidate_decompositions()
        self._explorer_last_result = None
        scalar = [
            self._exp_norm, self._exp_steps_sum, self._exp_perm,
            self._exp_period, self._exp_sig, self._exp_inv,
            self._exp_nf_kind, self._exp_nf_msc, self._exp_nf_sym,
            self._exp_nf_kron, self._exp_nf_notes,
            self._exp_can_avail, self._exp_can_sym,
            self._exp_can_exp, self._exp_can_notes,
        ]
        if not except_log:
            scalar.append(self._exp_log)
        for w in scalar:
            self._exp_set(w, "")
        self._exp_set(self._exp_rewrite, "")
        self._exp_set(self._exp_eval, "")
        for w in self._exp_can_factors:
            self._exp_set(w, "")
        self._reset_matrix_tab()
        if hasattr(self, "_exp_export_btn"):
            self._exp_export_btn.configure(state="disabled")
        if hasattr(self, "_decomp_btn"):
            self._decomp_btn.configure(state="disabled")

    def _fmt_perm27(self, perm):
        if perm is None:
            return ""
        lines = []
        for s in range(0, len(perm), 9):
            chunk = perm[s:s+9]
            lines.append("  ".join(f"{v:2d}" for v in chunk))
        return "\n".join(lines)

    def _explorer_display(self, r):
        # Numerico
        self._exp_set_colored(self._exp_norm, r.get("normalized_str", ""))
        self._exp_set(self._exp_steps_sum, r.get("norm_steps", ""))
        self._exp_set(self._exp_perm,      self._fmt_perm27(r.get("perm")))
        period = r.get("period")
        self._exp_set(self._exp_period,
                      str(period) if period is not None
                      else "Non trovato (limite 200 iter.)")
        self._exp_set(self._exp_sig, r.get("signature", ""))
        self._exp_set(self._exp_inv, self._fmt_perm27(r.get("inverse_perm")))
        # Traccia riscrittura
        trace = r.get("rewrite_trace", [])
        lines = []
        div = "─" * 72
        # Legenda delle regole, sempre in testa
        lines += [
            "  REGOLE DI RISCRITTURA",
            div,
            "  R1  Trasporto   MSC ∘ (a ⊗ b ⊗ c)  =  (c ⊗ a ⊗ b) ∘ MSC",
            "  R2  Potenze     MSC ∘ MSC ∘ MSC  =  I          (esponente mod 3)",
            "  R3  Fusione     (a⊗b⊗c) ∘ (d⊗e⊗f)  =  (a∘d ⊗ b∘e ⊗ c∘f)",
            "  R4  Identità    I ∘ X  =  X ∘ I  =  X",
            "",
            "  «Prima/Dopo» mostrano il SOTTOTERMINE riscritto dal passo;",
            "  «Espressione» è lo stato completo dopo il passo.",
            "",
            "  NOTA SULL'ORDINE — non confondere due cose diverse:",
            "  • APPLICAZIONE della permutazione: da DESTRA a SINISTRA",
            "    (il termine più a destra agisce per primo; vedi scheda",
            "    «Passi parziali» per l'ordine fisico di esecuzione);",
            "  • RISCRITTURA algebrica (questa scheda): le regole R1–R4 sono",
            "    identità valide in qualunque punto dell'espressione, quindi",
            "    l'ordine con cui vengono applicate (qui: da sinistra) è solo",
            "    una strategia e non cambia né la T né la forma normale.",
            "",
        ]
        for idx, step in enumerate(trace):
            lines.append("═" * 72)
            lines.append(f"  Passo {idx}  ·  {step.rule}")
            lines.append(div)
            if step.detail:
                det = str(step.detail).split("\n")
                lines.append(f"  Nota : {det[0]}")
                lines.extend(f"  {d}" for d in det[1:])
                lines.append("")
            if step.expr_before and step.expr_before != "—":
                lines.append(f"  Prima: {step.expr_before}")
                lines.append("")
            lines.append(f"  Dopo : {step.expr_after}")
            state = getattr(step, "state_after", "")
            if state and state != step.expr_after:
                lines.append("")
                lines.append("  Espressione completa dopo il passo:")
                lines.append(f"      {state}")
            lines.append("")
        self._exp_set_colored(self._exp_rewrite, "\n".join(lines))
        # Forma algebrica
        nf = r.get("normal_form")
        if nf:
            self._exp_set(self._exp_nf_kind, nf.kind)
            msc_str = f"MSC^{nf.msc_exponent}" if nf.msc_exponent > 0 else "nessuno (exp=0)"
            self._exp_set(self._exp_nf_msc, msc_str)
            self._exp_set_colored(self._exp_nf_sym, nf.symbolic)
            if nf.kron_factors_repr:
                kron_str = "\n".join(
                    f"  P{i+1} = {f}" for i, f in enumerate(nf.kron_factors_repr))
            else:
                kron_str = "  (nessun blocco Kronecker residuo)"
            self._exp_set_colored(self._exp_nf_kron, kron_str)
            notes = [
                f"Già in forma normale: {'SÌ' if nf.already_normal else 'NO'}",
                f"Tipo: {nf.kind}",
            ]
            actual_perm = r.get("perm")
            if (actual_perm is not None
                    and list(actual_perm) == list(range(len(actual_perm)))):
                notes.append("L'espressione è l'identità.")
            self._exp_set(self._exp_nf_notes, "\n".join(notes))
        # Passi parziali
        descs = r.get("partial_descriptions", [])
        perms = r.get("partial_perms", [])
        sigs  = r.get("partial_signatures", [])
        step_lines = []
        for idx, (desc, perm, sig2) in enumerate(zip(descs, perms, sigs)):
            step_lines.append("─" * 55)
            step_lines.append(f"  [{idx:2d}]  {desc}")
            inline = "  ".join(f"{v:2d}" for v in perm)
            step_lines.append(f"  perm  :  {inline[:100]}")
            if sig2:
                tail = "…" if len(sig2) > 70 else ""
                step_lines.append(f"  firma :  {sig2[:70]}{tail}")
            step_lines.append("")
        self._exp_set_colored(self._exp_eval, "\n".join(step_lines))
        # Forma canonica
        avail  = r.get("canonical_available", False)
        cf     = r.get("canonical_form")
        cf_sym = r.get("canonical_symbolic", "")
        self._exp_set(self._exp_can_avail, "SÌ" if avail else "NO")
        self._exp_set_colored(self._exp_can_sym, cf_sym if cf_sym else "—")
        if avail and cf is not None:
            for w, nm, pv in zip(self._exp_can_factors,
                                  cf.kron_factor_names(), cf.kron_factors):
                self._exp_set_colored(w, f"{nm}  =  {list(pv)}", base_font=("Consolas", 10))
            self._exp_set(self._exp_can_exp,
                          f"k = {cf.msc_exp}  (MSC^{cf.msc_exp})")
        else:
            for w in self._exp_can_factors:
                self._exp_set(w, "—")
            self._exp_set(self._exp_can_exp, "—")
        can_notes = []
        if not avail:
            can_notes.append(
                "⚠  Forma canonica non disponibile.\n"
                "   L'espressione contiene J o non è riducibile a K ∘ MSCᵏ.")
        else:
            can_notes.append("✓  Forma canonica calcolata.")
            if cf is not None:
                try:
                    if cf.to_perm() == r.get("perm"):
                        can_notes.append("✓  Coerenza verificata: perm canonica == perm calcolata.")
                    else:
                        can_notes.append("⚠  Attenzione: perm canonica ≠ perm calcolata!")
                except Exception as ex:
                    can_notes.append(f"   (verifica non eseguita: {ex})")
                if cf.is_identity():
                    can_notes.append("✓  L'espressione è l'identità.")
        self._exp_set(self._exp_can_notes, "\n".join(can_notes))
        self._update_matrix_tab(r)

    def _switch_to_explorer(self):
        for w in self.winfo_children():
            if isinstance(w, ttk.Notebook):
                for i, tab in enumerate(w.tabs()):
                    if "Explorer" in w.tab(tab, "text"):
                        w.select(i)
                        return
