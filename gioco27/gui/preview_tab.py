"""
Tab "🔍 Anteprima" — calcolo di una singola combinazione al volo.

Mixin per App: fornisce _build_anteprima_tab() e i relativi callback.
Estratto da app.py (v2.8.0) senza modifiche funzionali.
"""
import tkinter as tk
from tkinter import ttk

from ..core.constants import P_OPTS, J_OPTS
from ..core.permutations import compute_T_full, kron_label


class PreviewTabMixin:
    """Metodi del tab Anteprima. Richiede gli attributi/metodi di App:
    _open_export_dialog(), _notify_T_changed()."""

    def _build_anteprima_tab(self, parent):
        """
        Tab per calcolare una singola combinazione al volo.
        Mostra i parametri di tutti e tre gli stadi e, dopo "Calcola",
        visualizza le etichette Stage, A_i, T simbolica e T permutazione.
        """
        outer = ttk.Frame(parent, padding=12)
        outer.rowconfigure(1, weight=1)
        outer.columnconfigure(0, weight=1)

        # ── Intestazione ──────────────────────────────────────────────────────
        hdr_frame = ttk.Frame(outer)
        hdr_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(hdr_frame,
                  text="🔍  Anteprima singola combinazione",
                  font=("Segoe UI", 13, "bold"),
                  foreground="#1a5276").pack(side="left")
        ttk.Label(hdr_frame,
                  text="   — seleziona un valore per ciascun parametro e premi Calcola",
                  font=("Segoe UI", 10, "italic"),
                  foreground="#555").pack(side="left")

        # ── Griglia parametri (3 stadi × 6 colonne) ──────────────────────────
        param_frame = ttk.LabelFrame(outer,
                                      text="  Parametri  ",
                                      padding=(12, 8))
        param_frame.grid(row=1, column=0, sticky="nsew")
        outer.rowconfigure(1, weight=0)
        outer.rowconfigure(2, weight=1)

        self._prev_vars = []   # lista di 3 dict: nome → StringVar

        col_labels = ["P0  (carte)", "P1  (terzine)", "P2  (pacchetti)",
                      "J0", "J1", "J2"]
        col_opts   = [P_OPTS, P_OPTS, P_OPTS, J_OPTS, J_OPTS, J_OPTS]
        col_fg     = ["#1a5276","#1a5276","#1a5276",
                      "#7b4000","#7b4000","#7b4000"]

        for col, (lbl, fg) in enumerate(zip(col_labels, col_fg)):
            ttk.Label(param_frame, text=lbl,
                      font=("Segoe UI", 10, "bold"),
                      foreground=fg).grid(
                row=0, column=col+1, padx=8, pady=(0, 4))

        for s in range(3):
            ttk.Label(param_frame,
                      text=f"Stadio {s}",
                      font=("Segoe UI", 11, "bold"),
                      foreground="#333").grid(
                row=s+1, column=0, sticky="e", padx=(4, 10), pady=6)

            stage_vars = {}
            for col, (opts, lbl) in enumerate(zip(col_opts, col_labels)):
                key = ["p0","p1","p2","j0","j1","j2"][col]
                var = tk.StringVar(value=opts[0])
                combo = ttk.Combobox(param_frame, textvariable=var,
                                     values=opts, width=10,
                                     state="readonly",
                                     font=("Consolas", 11))
                combo.grid(row=s+1, column=col+1, padx=8, pady=6)
                stage_vars[key] = var
            self._prev_vars.append(stage_vars)

        # ── Bottone Calcola ───────────────────────────────────────────────────
        btn_frame = ttk.Frame(outer)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=10)

        ttk.Button(btn_frame,
                   text="  ▶  Calcola  ",
                   style="Action.TButton",
                   command=self._calcola_anteprima).pack(side="left")

        ttk.Button(btn_frame,
                   text="↺ Reset",
                   style="Preset.TButton",
                   command=self._reset_anteprima).pack(side="left", padx=8)

        self._prev_export_btn = ttk.Button(
            btn_frame,
            text="📄  Esporta LaTeX / SVG",
            state="disabled",
            command=self._anteprima_export)
        self._prev_export_btn.pack(side="left", padx=8)

        # ── Area risultati ────────────────────────────────────────────────────
        res_frame = ttk.LabelFrame(outer,
                                    text="  Risultato  ",
                                    padding=(12, 10))
        res_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 6))
        outer.rowconfigure(3, weight=1)
        res_frame.columnconfigure(0, weight=1)
        res_frame.rowconfigure(0, weight=1)

        self._prev_result = tk.Text(
            res_frame, wrap="word",
            font=("Consolas", 11),
            bg="#FAFCFF", fg="#1a1a2e",
            padx=12, pady=10,
            relief="flat", borderwidth=0,
            height=12,
            state="disabled")
        vsb = ttk.Scrollbar(res_frame, orient="vertical",
                            command=self._prev_result.yview)
        self._prev_result.configure(yscrollcommand=vsb.set)
        self._prev_result.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # tag colori per il testo
        self._prev_result.tag_configure(
            "head", font=("Segoe UI", 11, "bold"), foreground="#1F4E79")
        self._prev_result.tag_configure(
            "formula", font=("Consolas", 11), foreground="#7B2D00",
            background="#FFF8F0")
        self._prev_result.tag_configure(
            "ok", font=("Segoe UI", 11, "bold"), foreground="#1a7a1a")
        self._prev_result.tag_configure(
            "perm", font=("Consolas", 10), foreground="#333")
        self._prev_result.tag_configure(
            "placeholder", font="GiocoHelpItalic", foreground="#8a96a3")
        self._prev_show_placeholder()

        return outer

    def _prev_show_placeholder(self):
        """Stato vuoto del riquadro Risultato (prima del calcolo)."""
        txt = self._prev_result
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        txt.insert(
            "end",
            "Imposta P e J per i tre stadi qui sopra e premi  ▶ Calcola.\n"
            "Qui compariranno le formule degli stadi e la permutazione T "
            "risultante.",
            "placeholder")
        txt.configure(state="disabled")

    def _reset_anteprima(self):
        for s, stage_vars in enumerate(self._prev_vars):
            for key, var in stage_vars.items():
                opts = P_OPTS if key.startswith("p") else J_OPTS
                var.set(opts[0])
        self._prev_show_placeholder()

    def _anteprima_export(self):
        perm = getattr(self, "_prev_T_perm", None)
        if perm is None:
            return
        import numpy as np
        inv = list(np.argsort(perm))
        self._open_export_dialog(perm=perm, inv_perm=inv, title_label="T (Anteprima)")

    def _calcola_anteprima(self):
        params = []
        for stage_vars in self._prev_vars:
            # ordine posizionale: (P₀, P₁, P₂, J₀, J₁, J₂)
            p = (stage_vars['p0'].get(), stage_vars['p1'].get(),
                 stage_vars['p2'].get(), stage_vars['j0'].get(),
                 stage_vars['j1'].get(), stage_vars['j2'].get())
            params.append(p)

        ai_labels, T_label, T_perm, _ = compute_T_full(params)

        txt = self._prev_result
        txt.configure(state="normal")
        txt.delete("1.0", "end")

        def ins(tag, text):
            txt.insert("end", text, tag)

        for i, (p, ai_lbl) in enumerate(zip(params, ai_labels)):
            p1,p2,p3,j1,j2,j3 = p
            lp = kron_label(p3, p2, p1)
            lj = kron_label(j3, j2, j1)
            ins("head", f"Stadio {i}:  ")
            ins("formula", f"Stage{i} = {lp} ∘ MSC ∘ {lj}\n")
            ins("head", f"  →  A{i} = ")
            ins("formula", f"{ai_lbl}\n")

        ins("head", "\n")
        ins("ok", "T = A2 ∘ MSC ∘ A1 ∘ MSC ∘ A0 ∘ MSC\n")
        ins("head", "T simbolica:  ")
        ins("formula", f"{T_label}\n\n")
        ins("head", "T permutazione:\n")
        # Stampa in 3 righe da 9 elementi (blocchi ternari)
        for block in range(3):
            chunk = T_perm[block*9:(block+1)*9]
            s = "  " + "  ".join(f"[{i+block*9:2}]→{v}" for i, v in enumerate(chunk))
            ins("perm", s + "\n")

        txt.configure(state="disabled")
        self._prev_T_perm = list(T_perm)
        if hasattr(self, "_prev_export_btn"):
            self._prev_export_btn.configure(state="normal")
        self._notify_T_changed(list(T_perm))
