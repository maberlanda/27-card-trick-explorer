"""
Tab "🔬 Explorer" — analisi simbolica, traccia di riscrittura, forma canonica,
matrici 27×27 di T e T⁻¹.

Mixin per App: fornisce _build_explorer_tab() e tutti i callback Explorer.
Estratto da app.py (v2.8.0) senza modifiche funzionali.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from ..core.algebra import (AlgebraEngine, Controller, CanonicalForm,
                            display_normal_form_kind)
from ..core.constants import PERM3
from ..core.kronecker import try_kron_decompose, decomposition_context
from ..services import tabellone as _tb
from .common import configure_matrix_tags, insert_colored
from .decomposition import DecompositionDialog
from .i18n import tr
from .riconoscimento_tab import RiconoscimentoFrame
from .laboratorio_tab import LaboratorioFrame
from . import livelli as _livelli
from .shuffle import ShuffleViewerFrame


class ExplorerTabMixin:
    """Metodi del tab Explorer. Richiede gli attributi/metodi di App:
    _open_export_dialog(), _notify_T_changed(), _last_T_perm, _last_inv_perm."""

    def _build_explorer_tab(self, parent):
        # blocco superiore compatto: lo spazio verticale serve alle sotto-schede
        # I runner Linux lasciano 1242 px utili a 1280×720: 4 px per lato
        # conservano il margine e tengono la riga dei comandi nella vista.
        outer = ttk.Frame(parent, padding=(4, 2, 4, 6))
        outer.rowconfigure(2, weight=1)
        outer.columnconfigure(0, weight=1)

        self._explorer_ctrl        = Controller()
        self._explorer_last_result = None

        hdr = ttk.Frame(outer)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 1))
        ttk.Button(hdr, text=tr("ux3.example.load"), command=self._explorer_example).pack(side="right")
        ttk.Label(hdr, text=f"🔬  {tr('explorer.title')}",
                  font=("Segoe UI", 13, "bold"), foreground="#1F4E79").pack(side="left")
        ttk.Label(hdr,
                  text=tr("ux3.explorer.purpose"),
                  font=("Segoe UI", 10, "italic"), foreground="#555",
                  wraplength=580, justify="left").pack(side="left", padx=8)

        inp_frame = ttk.LabelFrame(
            outer, text=f"  {tr('explorer.expression')}  ", padding=(10, 2))
        inp_frame.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        inp_frame.columnconfigure(0, weight=1)

        self._explorer_entry = tk.Text(
            inp_frame, height=2, font=("Consolas", 11),
            bg="#FAFCFF", fg="#1a1a2e", padx=6, pady=4, relief="flat", wrap="word")
        self._explorer_entry.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        self._explorer_entry.bind("<Control-Return>", lambda e: self._explorer_calc())
        self._explorer_entry.bind("<<Modified>>", self._explorer_input_changed)
        self._explorer_entry.edit_modified(False)

        btn_row = ttk.Frame(inp_frame)
        btn_row.grid(row=1, column=0, sticky="w")
        ttk.Button(btn_row, text=f"▶  {tr('button.calculate')}", style="Action.TButton",
                   command=self._explorer_calc).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text=f"✕  {tr('explorer.button.clear')}", style="Preset.TButton",
                   command=self._explorer_clear).pack(side="left", padx=(0, 12))
        self._decomp_btn = ttk.Button(
            btn_row, text=f"🔍  {tr('explorer.button.decompositions_inverse')}",
            state="disabled", command=self._explorer_find_decompositions)
        self._decomp_btn.pack(side="left", padx=(6, 0))
        self._exp_export_btn = ttk.Button(
            btn_row, text=f"📄  {tr('explorer.button.export')}",
            state="disabled",
            command=self._explorer_export)
        self._exp_export_btn.pack(side="left", padx=(6, 0))
        # I2d: la T calcolata, se e' una disposizione della Tavola, vi si apre;
        # il pulsante sta con gli altri comandi, sotto resta solo il motivo
        self._exp_tavola_btn = ttk.Button(
            btn_row, text=tr("nav.show_in_table"), state="disabled",
            command=self._explorer_to_tavola)
        self._exp_tavola_btn.pack(side="left", padx=(6, 0))
        self._explorer_status = tk.StringVar(
            value=tr("ux2.result.absent") + " — " + tr("explorer.status.prompt"))
        ttk.Label(btn_row, textvariable=self._explorer_status,
                  font="GiocoHelp", foreground="#333",
                  wraplength=380).pack(side="left", padx=(10, 0))

        # una sola riga compatta: «Riga #… della Tavola» o il motivo.
        # K: la riga si mostra solo quando ha un testo; vuota occupava ~19 px
        # di altezza utile sopra Matrice, Riconoscimento e Laboratorio.
        nav_row = ttk.Frame(inp_frame)
        nav_row.grid(row=2, column=0, sticky="w", pady=(1, 0))
        self._exp_tavola_motivo = ttk.Label(nav_row, text="", foreground="#555",
                                            font=("Segoe UI", 8))
        self._exp_tavola_motivo.pack(side="left")
        self._exp_nav_row = nav_row
        nav_row.grid_remove()
        self._exp_tavola_numero = None

        enb = ttk.Notebook(outer)
        enb.grid(row=2, column=0, sticky="nsew")
        self._explorer_nb = enb
        enb.bind("<<NotebookTabChanged>>", self._exp_adatta_altezza, add="+")
        self._build_explorer_tab_numeric(enb)
        self._build_explorer_tab_rewrite(enb)
        self._build_explorer_tab_algebra(enb)
        self._build_explorer_tab_steps(enb)
        self._build_explorer_tab_canonical(enb)
        self._build_explorer_tab_matrix(enb)
        self._build_explorer_tab_shuffle(enb)
        self._build_explorer_tab_riconoscimento(enb)
        self._build_explorer_tab_laboratorio(enb)
        # K: nove linguette in una riga. Gli spazi attorno alle etichette
        # facevano da margine: con DejaVu Sans (il font di ripiego di Tk 8.6
        # su Linux) la riga superava i 1242 px utili a 1280×720 e compariva la
        # barra orizzontale (H2). Il margine lo da' ora lo stile: 2 px per
        # lato lasciano le nove linguette leggibili e mantengono la vista
        # entro i 1280 px anche con le metriche dei runner Linux.
        ttk.Style(enb).configure("Explorer.TNotebook.Tab", padding=(2, 2))
        enb.configure(style="Explorer.TNotebook")
        for scheda in enb.tabs():
            enb.tab(scheda, text=" ".join(enb.tab(scheda, "text").split()))
        # I7 (DP7): chiavi stabili delle nove sotto-schede, per il livello
        self._sottoschede_explorer = dict(zip(
            _livelli.ORDINE_SOTTOSCHEDE_EXPLORER,
            (enb.nametowidget(t) for t in enb.tabs())))
        return outer

    def _explorer_example(self):
        from ..services.procedure import ProceduraGioco
        from ..services.tabellone import espressione_per_explorer
        expression = espressione_per_explorer(ProceduraGioco.da_identificatore(100, 0))
        self._explorer_entry.delete("1.0", "end")
        self._explorer_entry.insert("1.0", expression)
        self._explorer_calc()

    def _exp_adatta_altezza(self, _evento=None):
        """Matrice, Riconoscimento e Laboratorio: riquadro alto quanto il contenuto.

        Un `ttk.Notebook` chiede l'altezza della sua sotto-scheda piu' alta
        (671 px) e la riga dell'Explorer lo allunga ancora (weight=1): sotto i
        pannelli della Matrice restava un grande vuoto grigio, e lo
        scorrimento H2 lo attraversava. Con una pagina «compatta» selezionata
        (Matrice, da I5 Riconoscimento, da I6 Laboratorio) l'altezza del riquadro e' quella
        richiesta dalla pagina e la riga non si allunga; le altre sotto-schede
        tornano al comportamento di prima.
        """
        nb = getattr(self, "_explorer_nb", None)
        compatte = [p for p in (getattr(self, "_mat_scheda", None),
                                getattr(self, "_riconoscimento", None),
                                getattr(self, "_laboratorio", None)) if p is not None]
        if nb is None or not compatte:
            return
        try:
            scelta = next((p for p in compatte if nb.select() == str(p)), None)
            if scelta is not None:
                scelta.update_idletasks()
                nb.configure(height=scelta.winfo_reqheight())
                nb.master.rowconfigure(2, weight=0)
            else:
                nb.configure(height=0)
                nb.master.rowconfigure(2, weight=1)
        except tk.TclError:
            return
        area = getattr(self, "_aree_scorrevoli", {}).get("explorer")
        if area is not None:
            # prima si propaga la nuova altezza richiesta, poi l'area
            # scorrevole ricalcola regione e barre sul contenuto reale
            try:
                area.update_idletasks()
            except tk.TclError:
                return
            area.ricalcola()

    # ── Explorer sub-tab helpers ──────────────────────────────────────────────

    def _exp_scrolled(self, parent, height=4, mono=True, wrap="word"):
        """(frame, Text) con scrollbar verticale. Usa pack sul frame."""
        font = ("Consolas", 9) if mono else ("Segoe UI", 10)
        fr = ttk.Frame(parent)
        fr.rowconfigure(0, weight=1)
        fr.columnconfigure(0, weight=1)
        # width=1: la larghezza la decide il layout (sticky/fill). Il default di
        # Tk (80 caratteri) con i font monospazio di ripiego di Linux rendeva
        # due colonne affiancate piu' larghe di 1280 px (K, CI con Tk 8.6).
        w = tk.Text(fr, height=height, width=1, font=font,
                    bg="#FAFCFF", fg="#1a1a2e",
                    padx=6, pady=4, relief="flat", wrap=wrap, state="disabled")
        sb = ttk.Scrollbar(fr, orient="vertical", command=w.yview)
        w.configure(yscrollcommand=sb.set)
        w.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        return fr, w

    def _build_explorer_tab_riconoscimento(self, nb):
        """I5: «Riconoscimento» — dal mazzo alla legge (services.riconoscimento)."""
        def fornisci_T():
            r = getattr(self, "_explorer_last_result", None) or {}
            return r.get("perm") if r.get("ok", True) else None
        self._riconoscimento = RiconoscimentoFrame(nb, fornisci_T)
        nb.add(self._riconoscimento,
               text=f"  \U0001f50e  {tr('recognition.tab')}  ")
        return self._riconoscimento

    def _build_explorer_tab_laboratorio(self, nb):
        """I6: «Laboratorio» — proprieta', domini e piccoli grafi (services.laboratorio)."""
        self._laboratorio = LaboratorioFrame(nb)
        nb.add(self._laboratorio,
               text=f"  \U0001f9ea  {tr('lab.tab')}  ")
        return self._laboratorio

    def _build_explorer_tab_shuffle(self, nb):
        """Tab '\U0001f3b4 Mescolamento' — simulazione visiva passo-per-passo."""
        self._shuffle_viewer = ShuffleViewerFrame(nb, self)
        nb.add(self._shuffle_viewer,
               text=f"  \U0001f3b4  {tr('explorer.tab.shuffle')}  ")
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
        nb.add(fr, text=f"  🔢 {tr('explorer.tab.numeric')}  ")

        self._exp_lbl(fr, tr("explorer.normalized_form"), bold=True)
        _f, self._exp_norm = self._exp_scrolled(fr, height=2)
        _f.pack(fill="x")

        self._exp_lbl(fr, tr("explorer.rewrite_summary"))
        _f, self._exp_steps_sum = self._exp_scrolled(fr, height=2)
        _f.pack(fill="x")

        self._exp_lbl(fr, tr("explorer.permutation_vector"), bold=True)
        _f, self._exp_perm = self._exp_scrolled(fr, height=4)
        _f.pack(fill="x")

        row2 = ttk.Frame(fr)
        row2.pack(fill="x", pady=4)
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)

        col_a = ttk.Frame(row2)
        col_a.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._exp_lbl(col_a, tr("explorer.period"))
        _f, self._exp_period = self._exp_scrolled(col_a, height=1)
        _f.pack(fill="x")
        self._exp_lbl(col_a, tr("explorer.canonical_signature"))
        _f, self._exp_sig = self._exp_scrolled(col_a, height=2)
        _f.pack(fill="x")

        col_b = ttk.Frame(row2)
        col_b.grid(row=0, column=1, sticky="nsew")
        self._exp_lbl(col_b, tr("explorer.inverse_permutation"))
        _f, self._exp_inv = self._exp_scrolled(col_b, height=4)
        _f.pack(fill="x")

        self._exp_lbl(fr, tr("explorer.log_errors"))
        _f, self._exp_log = self._exp_scrolled(fr, height=3)
        _f.pack(fill="x")
        children = fr.winfo_children()
        # Present the numerical effect before its algebraic descriptions.
        children[4].pack(before=children[0])
        children[5].pack(before=children[0])

    def _build_explorer_tab_rewrite(self, nb):
        fr = ttk.Frame(nb, padding=8)
        nb.add(fr, text=f"  ✏️ {tr('explorer.tab.rewrite')}  ")
        fr.rowconfigure(1, weight=1)
        fr.columnconfigure(0, weight=1)
        ttk.Label(fr,
                  text=tr("explorer.rewrite.subtitle"),
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
        nb.add(fr, text=f"  🧮 {tr('explorer.tab.algebra')}  ")
        fr.columnconfigure(0, weight=1)
        ttk.Label(fr, text=tr("explorer.algebra.subtitle"),
                  font=("Segoe UI", 10, "italic"),
                  foreground="#555").pack(anchor="w", pady=(0, 6))
        row_meta = ttk.Frame(fr)
        row_meta.pack(fill="x", pady=(0, 4))
        row_meta.columnconfigure(0, weight=1)
        row_meta.columnconfigure(1, weight=1)
        for col_i, (label, attr) in enumerate([
            (tr("explorer.normal_form_type"), "_exp_nf_kind"),
            (tr("explorer.msc_exponent_mod"), "_exp_nf_msc"),
        ]):
            box = ttk.LabelFrame(row_meta, text=f"  {label}  ", padding=(6, 4))
            box.grid(row=0, column=col_i, sticky="nsew", padx=4)
            w = tk.Text(box, height=1, width=1, font=("Consolas", 10, "bold"),
                        bg="#EBF5FB", fg="#1F4E79",
                        padx=4, pady=2, relief="flat", state="disabled")
            w.pack(fill="x")
            setattr(self, attr, w)
        self._exp_lbl(fr, tr("explorer.readable_symbolic_form"), bold=True)
        _f, self._exp_nf_sym = self._exp_scrolled(fr, height=2)
        _f.pack(fill="x")
        self._exp_lbl(fr, tr("explorer.residual_kronecker_factors"))
        _f, self._exp_nf_kron = self._exp_scrolled(fr, height=4)
        _f.pack(fill="x")
        self._exp_lbl(fr, tr("explorer.notes"))
        _f, self._exp_nf_notes = self._exp_scrolled(fr, height=3)
        _f.pack(fill="x")

    def _build_explorer_tab_steps(self, nb):
        fr = ttk.Frame(nb, padding=8)
        nb.add(fr, text=f"  📋 {tr('explorer.tab.partial_steps')}  ")
        fr.rowconfigure(1, weight=1)
        fr.columnconfigure(0, weight=1)
        ttk.Label(fr,
                  text=tr("explorer.partial.subtitle"),
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
        nb.add(fr, text=f"  ⧆ {tr('explorer.tab.canonical')}  ")
        fr.columnconfigure(0, weight=1)
        ttk.Label(fr,
                  text=tr("explorer.canonical.subtitle"),
                  font=("Segoe UI", 10, "italic"),
                  foreground="#555").pack(anchor="w", pady=(0, 8))
        for label, attr in [
            (tr("explorer.available"), "_exp_can_avail"),
            (tr("explorer.symbolic_form"), "_exp_can_sym"),
        ]:
            ttk.Label(fr, text=f"{label}:",
                      font=("Segoe UI", 10, "bold"),
                      foreground="#1F4E79").pack(anchor="w", pady=(4, 1))
            h = 1 if attr == "_exp_can_avail" else 2
            _f, w = self._exp_scrolled(fr, height=h)
            _f.pack(fill="x")
            setattr(self, attr, w)
        ttk.Separator(fr, orient="horizontal").pack(fill="x", pady=6)
        self._exp_lbl(fr, tr("explorer.kronecker_factors"), bold=True)
        self._exp_can_factors = []
        for lab in ("P₂", "P₁", "P₀"):
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
        self._exp_lbl(fr, tr("explorer.msc_exponent"))
        _f, self._exp_can_exp = self._exp_scrolled(fr, height=1)
        _f.pack(fill="x")
        self._exp_lbl(fr, tr("explorer.coherence_notes"))
        _f, self._exp_can_notes = self._exp_scrolled(fr, height=4)
        _f.pack(fill="x")


    # ── Tab Matrice (T e T⁻¹ affiancate) ─────────────────────────────────────

    def _build_explorer_tab_matrix(self, nb):
        """
        Tab '📐 Matrice' — T (sinistra) e T⁻¹ (destra).

        In ciascun pannello la griglia 27×27 sta a sinistra; a destra, dall'alto,
        la forma canonica, i tre fattori Kronecker 3×3 e l'alternativa testuale
        della matrice. I fattori, informazione strutturale, sono all'altezza
        della parte alta della griglia: visibili appena si apre la sotto-scheda
        anche a 1280×720, senza scorrere.
        """
        # CELL 12: griglia 27×27 di 328 px, la dimensione originale. I fattori
        # stanno accanto alla sua parte alta; lo spazio verticale non si
        # recupera rimpicciolendola, ma togliendo il vuoto sotto (vedi
        # `_exp_adatta_altezza`).
        CELL  = 12
        SMALL = 20

        outer = ttk.Frame(nb, padding=(8, 2, 8, 4))
        nb.add(outer, text=f"  \U0001f4d0  {tr('explorer.tab.matrix')}  ")
        self._mat_scheda = outer
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(1, weight=1)

        cv_size = CELL * 27 + 2

        def make_panel(col, title_text, tag):
            """Pannello: griglia 27×27 a sinistra; a destra forma canonica,
            fattori 3×3 e testo, che arriva fino al fondo della griglia."""
            panel = ttk.Frame(outer, relief="groove", borderwidth=1)
            panel.grid(row=0, column=col, rowspan=2, sticky="nsew",
                       padx=(0 if col else 0, 6 if col == 0 else 0))
            panel.columnconfigure(0, weight=1)

            title = ttk.Label(panel,
                              text=title_text,
                              font=("Segoe UI", 11, "bold"),
                              foreground="#1F4E79",
                              anchor="center")
            title.grid(row=0, column=0, sticky="ew", pady=(2, 2))

            # corpo alto quanto la griglia: il pannello puo' allungarsi, il
            # contenuto no (il box di testo si ferma al fondo della griglia)
            corpo = ttk.Frame(panel)
            corpo.grid(row=1, column=0, sticky="new", padx=(6, 8), pady=(0, 6))
            corpo.columnconfigure(1, weight=1)
            corpo.rowconfigure(2, weight=1)

            cv = tk.Canvas(corpo, width=cv_size+26, height=cv_size+26,
                           bg="white", highlightthickness=1,
                           highlightbackground="#AAAAAA")
            cv.grid(row=0, column=0, rowspan=3, sticky="n", padx=(0, 8))
            self._draw_empty_grid(cv, 27, CELL)

            cf_lbl = ttk.Label(corpo,
                               text=tr("explorer.matrix.canonical_empty"),
                               font=("Consolas", 9),
                               foreground="#555",
                               wraplength=220, justify="left")
            cf_lbl.grid(row=0, column=1, sticky="nw")

            factors_row = ttk.Frame(corpo)
            factors_row.grid(row=1, column=1, sticky="nw", pady=(4, 4))
            fcvs, flbls = [], []
            for i in range(3):
                col_fr = ttk.Frame(factors_row)
                col_fr.pack(side="left", padx=(0, 8))
                fcv = tk.Canvas(col_fr, width=SMALL*3+2, height=SMALL*3+2,
                                bg="white", highlightthickness=1,
                                highlightbackground="#888")
                fcv.pack()
                self._draw_empty_grid(fcv, 3, SMALL)
                flbl = ttk.Label(col_fr, text=f"P{2-i} = —",
                                 font=("Consolas", 9), foreground="#1F4E79")
                flbl.pack(pady=(2, 0))
                fcvs.append(fcv)
                flbls.append(flbl)

            # H2: la matrice 27×27 è un disegno, e finora era l'unico posto in
            # cui la permutazione esisteva in questa vista. Qui c'è la stessa
            # informazione in testo, selezionabile e raggiungibile con Tab:
            # chi non interpreta il disegno legge i 27 valori.
            testo = tk.Text(corpo, height=1, width=1, wrap="word", relief="flat",
                            font=("Consolas", 9), background="#F7F9FC",
                            foreground="#1F4E79", takefocus=True)
            testo.grid(row=2, column=1, sticky="nsew")
            testo.insert("1.0", tr("explorer.matrix.as_text_empty"))
            testo.configure(state="disabled")

            return cv, cf_lbl, fcvs, flbls, testo

        (self._mat_cv_t, self._mat_lbl_t, self._mat_fcvs_t, self._mat_flbls_t,
         self._mat_txt_t
         ) = make_panel(0, tr("explorer.matrix.permutation", symbol="T"), "T")
        (self._mat_cv_inv, self._mat_lbl_inv, self._mat_fcvs_inv,
         self._mat_flbls_inv, self._mat_txt_inv
         ) = make_panel(1, tr("explorer.matrix.permutation", symbol="T⁻¹"), "T_inv")

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
        if n == 27:
            for i in (0, 3, 6, 9, 12, 15, 18, 21, 24, 26):
                canvas.create_text((i + .5) * cell, size + 12, text=str(i), font=("Segoe UI", 8), fill="#333")
                canvas.create_text(size + 12, (i + .5) * cell, text=str(i), font=("Segoe UI", 8), fill="#333")

    def _draw_perm_on_canvas(self, canvas, perm, cell, color="#27AE60"):
        """Disegna la matrice di permutazione: perm[col]=row → quadratino verde."""
        n = len(perm)
        self._draw_empty_grid(canvas, n, cell)
        pad = max(1, cell // 6)
        for col, row in enumerate(perm):
            x0, y0 = col*cell+pad, row*cell+pad
            x1, y1 = (col+1)*cell-pad, (row+1)*cell-pad
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

    @staticmethod
    def _matrice_in_testo(perm27, fattori=None):
        """La stessa informazione della matrice, in parole (H2).

        La griglia 27×27 e i tre quadrati 3×3 sono un disegno: chi non lo
        interpreta — perché non lo vede, perché lo legge con uno strumento, o
        perché gli serve copiarlo — qui trova i 27 valori e i tre fattori
        scritti. Non è un riassunto: è la permutazione, per intero.
        """
        valori = ", ".join(str(v) for v in perm27)
        righe = [tr("ux4.matrix.axes"), tr("explorer.matrix.as_text", values=valori)]
        if fattori:
            righe.append(tr("explorer.matrix.factors_as_text",
                            factors=" ⊗ ".join(str(f) for f in fattori)))
        return "\n".join(righe)

    def _mostra_matrice_in_testo(self, testo, perm27, fattori=None):
        if testo is None:
            return
        testo.configure(state="normal")
        testo.delete("1.0", "end")
        testo.insert("1.0", self._matrice_in_testo(perm27, fattori))
        testo.configure(state="disabled")

    def _fill_matrix_panel(self, perm27, canonical_form, cv, cf_lbl, fcvs,
                           flbls, testo=None):
        """Popola un pannello (T o T⁻¹): disegna griglia + fattori Kronecker."""
        CELL  = self._mat_cell_size
        SMALL = self._mat_small_size
        self._draw_perm_on_canvas(cv, perm27, CELL)
        nomi_fattori = None
        if canonical_form is not None:
            try:
                names = canonical_form.kron_factor_names()
                sym   = canonical_form.symbolic()
                cf_lbl.config(text=tr("explorer.matrix.canonical", form=sym))
                nomi_fattori = list(names)
                for i, (fcv, flbl) in enumerate(zip(fcvs, flbls)):
                    self._draw_perm_on_canvas(fcv, canonical_form.kron_factors[i], SMALL)
                    flbl.config(text=f"P{2-i} = {names[i]}")
            except Exception:
                cf_lbl.config(text=tr("explorer.matrix.canonical_error"))
        else:
            # Fallback: prova ad estrarre i fattori direttamente dalla matrice
            try:
                factors = try_kron_decompose(perm27)
            except Exception:
                factors = None
            if factors is not None:
                f2, f1, f0 = factors
                nomi_fattori = [f2, f1, f0]
                cf_lbl.config(text=tr(
                    "explorer.matrix.canonical_from_matrix",
                    form=f"{f2} ⊗ {f1} ⊗ {f0}"))
                for fcv, flbl, fname, fperm in zip(
                        fcvs, flbls,
                        [f"f₂={f2}", f"f₁={f1}", f"f₀={f0}"],
                        [PERM3[f2], PERM3[f1], PERM3[f0]]):
                    self._draw_perm_on_canvas(fcv, fperm, SMALL)
                    flbl.config(text=fname)
            else:
                cf_lbl.config(text=tr("explorer.matrix.canonical_unavailable"))
                for fcv, flbl in zip(fcvs, flbls):
                    self._draw_empty_grid(fcv, 3, SMALL)
                    flbl.config(text="—")
        self._mostra_matrice_in_testo(testo, perm27, nomi_fattori)

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
                                 self._mat_fcvs_t, self._mat_flbls_t,
                                 self._mat_txt_t)

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
                                     self._mat_fcvs_inv, self._mat_flbls_inv,
                                     self._mat_txt_inv)

    def _reset_matrix_tab(self):
        """Svuota entrambi i pannelli del tab Matrice."""
        CELL  = self._mat_cell_size
        SMALL = self._mat_small_size
        for cv in (self._mat_cv_t, self._mat_cv_inv):
            self._draw_empty_grid(cv, 27, CELL)
        for lbl in (self._mat_lbl_t, self._mat_lbl_inv):
            lbl.config(text=tr("explorer.matrix.canonical_empty"))
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
            r = getattr(self, "_explorer_last_result", None)
            if r and r.get("ok"):
                stale = self._explorer_entry.get("1.0", "end-1c").strip() != getattr(
                    self, "_explorer_calculated_input", None)
                self._explorer_status.set(tr("ux2.result.stale" if stale else "ux2.result.current"))
                self._exp_export_btn.configure(text=tr("ux2.export.last"))

    def _explorer_find_decompositions(self):
        """Apre il dialog con tutte le decomposizioni Kronecker di T e T⁻¹."""
        r = self._explorer_last_result
        if not r:
            return
        perm     = r.get("perm")
        inv_perm = r.get("inverse_perm")
        if not inv_perm:
            messagebox.showinfo(tr("explorer.inverse_unavailable_title"),
                                tr("explorer.inverse_unavailable"))
            return
        # La ricerca usa il risultato locale: non ripubblica la T condivisa.
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
            self._explorer_clear_results()
            self._aggiorna_link_tavola(None)
            self._explorer_status.set(
                f"⚠  {tr('explorer.status.empty_expression')}")
            return
        result = self._explorer_ctrl.process(text)
        self._explorer_last_result = result
        self._aggiorna_link_tavola(result)
        if not result["ok"]:
            self._explorer_status.set(f"✗  {tr('explorer.status.error_log')}")
            self._exp_set(self._exp_log, result["error"])
            self._explorer_clear_results(except_log=True)
        else:
            self._explorer_calculated_input = text
            period = result["period"]
            sig    = result["signature"][:40]
            self._explorer_status.set(
                f"{tr('ux2.result.current')} — {tr('explorer.status.result', period=period, signature=sig)}")
            self._exp_set(self._exp_log, "")
            self._explorer_display(result)
            if result.get('perm') is not None:
                self._T_origin = "Explorer"
                self._notify_T_changed(list(result['perm']))
            if hasattr(self, "_exp_export_btn") and result.get("perm") is not None:
                self._exp_export_btn.configure(state="normal", text=tr("ux2.export.last"))
            if hasattr(self, "_decomp_btn") and result.get("inverse_perm"):
                self._decomp_btn.configure(state="normal")
        # J: l'espressione calcolata e' lo stato scientifico dell'Explorer
        if hasattr(self, "_sessione_nota"):
            self._sessione_nota("explorer")

    def _aggiorna_link_tavola(self, result=None):
        """Abilita «Mostra nella Tavola» solo se T e' una delle 216 (via (R))."""
        if not hasattr(self, "_exp_tavola_btn"):   # stesso riguardo degli altri
            return                                 # pulsanti opzionali
        perm = result.get("perm") if result and result.get("ok") else None
        numero = _tb.numero_di(list(perm)) if perm is not None else None
        self._exp_tavola_numero = numero
        if numero is None:
            self._exp_tavola_btn.state(["disabled"])
            self._exp_tavola_motivo.configure(
                text=tr("nav.not_in_table") if perm is not None else "")
        else:
            self._exp_tavola_btn.state(["!disabled"])
            self._exp_tavola_motivo.configure(text=tr("nav.in_table",
                                                      number=numero))
        riga = getattr(self, "_exp_nav_row", None)
        if riga is not None:
            if self._exp_tavola_motivo.cget("text"):
                riga.grid()
            else:
                riga.grid_remove()

    def _explorer_to_tavola(self):
        if self._exp_tavola_numero is not None:
            self._mostra_nella_tavola(self._exp_tavola_numero)

    def _explorer_clear(self):
        self._aggiorna_link_tavola(None)
        self._explorer_entry.delete("1.0", "end")
        self._explorer_clear_results()
        self._explorer_status.set(tr("ux2.result.absent"))

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
            title_label=r.get("normalized_str", "T"), origin="Explorer")

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
                      else tr("explorer.period_not_found"))
        self._exp_set(self._exp_sig, r.get("signature", ""))
        self._exp_set(self._exp_inv, self._fmt_perm27(r.get("inverse_perm")))
        # Traccia riscrittura
        trace = r.get("rewrite_trace", [])
        lines = []
        div = "─" * 72
        # Legenda delle regole, sempre in testa
        lines += [
            tr("explorer.rewrite.legend_title"),
            div,
            *tr("explorer.rewrite.legend").split("\n"),
            "",
        ]
        for idx, step in enumerate(trace):
            lines.append("═" * 72)
            lines.append(f"  {tr('explorer.rewrite.step', number=idx, rule=step.rule)}")
            lines.append(div)
            if step.detail:
                det = str(step.detail).split("\n")
                lines.append(f"  {tr('explorer.rewrite.note', detail=det[0])}")
                lines.extend(f"  {d}" for d in det[1:])
                lines.append("")
            if step.expr_before and step.expr_before != "—":
                lines.append(f"  {tr('explorer.rewrite.before', expression=step.expr_before)}")
                lines.append("")
            lines.append(f"  {tr('explorer.rewrite.after', expression=step.expr_after)}")
            state = getattr(step, "state_after", "")
            if state and state != step.expr_after:
                lines.append("")
                lines.append(f"  {tr('explorer.rewrite.full_expression')}")
                lines.append(f"      {state}")
            lines.append("")
        self._exp_set_colored(self._exp_rewrite, "\n".join(lines))
        # Forma algebrica
        nf = r.get("normal_form")
        if nf:
            self._exp_set(self._exp_nf_kind, display_normal_form_kind(nf.kind))
            msc_str = (f"MSC^{nf.msc_exponent}" if nf.msc_exponent > 0
                       else tr("explorer.no_msc_exponent"))
            self._exp_set(self._exp_nf_msc, msc_str)
            self._exp_set_colored(self._exp_nf_sym, nf.symbolic)
            if nf.kron_factors_repr:
                kron_str = "\n".join(
                    f"  P{2-i} = {f}" for i, f in enumerate(nf.kron_factors_repr))
            else:
                kron_str = f"  {tr('explorer.no_residual_kronecker')}"
            self._exp_set_colored(self._exp_nf_kron, kron_str)
            notes = [
                tr("explorer.normal_form_state",
                   value=tr("explorer.value.yes") if nf.already_normal
                   else tr("explorer.value.no")),
                tr("explorer.normal_form_kind",
                   kind=display_normal_form_kind(nf.kind)),
            ]
            actual_perm = r.get("perm")
            if (actual_perm is not None
                    and list(actual_perm) == list(range(len(actual_perm)))):
                notes.append(tr("explorer.identity"))
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
            step_lines.append(
                f"  {tr('explorer.partial.permutation')}  :  {inline[:100]}")
            if sig2:
                tail = "…" if len(sig2) > 70 else ""
                step_lines.append(
                    f"  {tr('explorer.partial.signature')} :  {sig2[:70]}{tail}")
            step_lines.append("")
        self._exp_set_colored(self._exp_eval, "\n".join(step_lines))
        # Forma canonica
        avail  = r.get("canonical_available", False)
        cf     = r.get("canonical_form")
        cf_sym = r.get("canonical_symbolic", "")
        self._exp_set(self._exp_can_avail,
                      tr("explorer.value.yes") if avail
                      else tr("explorer.value.no"))
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
                f"⚠  {tr('explorer.canonical.unavailable')}")
        else:
            can_notes.append(f"✓  {tr('explorer.canonical.calculated')}")
            if cf is not None:
                try:
                    if cf.to_perm() == r.get("perm"):
                        can_notes.append(f"✓  {tr('explorer.canonical.coherent')}")
                    else:
                        can_notes.append(f"⚠  {tr('explorer.canonical.mismatch')}")
                except Exception as ex:
                    can_notes.append(
                        f"   {tr('explorer.canonical.verification_skipped', detail=ex)}")
                if cf.is_identity():
                    can_notes.append(f"✓  {tr('explorer.identity')}")
        self._exp_set(self._exp_can_notes, "\n".join(can_notes))
        self._update_matrix_tab(r)

    def _switch_to_explorer(self):
        """H1: per chiave stabile, non cercando «Explorer» fra i titoli.

        Funzionava perche' quella parola si scrive uguale nelle due lingue:
        una coincidenza, non un contratto.
        """
        self._seleziona_scheda("explorer")
