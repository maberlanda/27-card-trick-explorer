"""FilterFrame: selettore combinazioni P/J per ogni stadio."""
import tkinter as tk
from tkinter import ttk

from ..core.constants import P_OPTS, J_OPTS, ANY
from .tooltip import attach as _tip

# Descrizioni in parole semplici delle 6 permutazioni P (su S=sinistra,
# C=centro, D=destra) e delle 2 orientazioni J.
_PERM3_DESC = {
    "SCD_U": "Identità: S→S, C→C, D→D (non cambia nulla).",
    "SDC_U": "Scambia Centro e Destra (Sinistra ferma).",
    "CSD_U": "Scambia Sinistra e Centro (Destra ferma).",
    "CDS_U": "Rotazione in avanti: S→C, C→D, D→S.",
    "DSC_U": "Rotazione indietro: S→D, C→S, D→C.",
    "DCS_U": "Scambia Sinistra e Destra (Centro fermo).",
}
_J_DESC = {
    "I_3": "Identità: nessuna inversione.",
    "R_U": "Inversione: capovolge l'ordine (Sinistra↔Destra).",
}
# Significato di ciascun livello di Kronecker.
_LEVEL_DESC = {
    "P0": "P₀ — livello carte: riordina le 3 carte dentro ogni terzina "
          "(agisce sulla cifra ternaria i₀).",
    "P1": "P₁ — livello terzine: riordina le 3 terzine dentro ogni pacchetto "
          "(cifra i₁).",
    "P2": "P₂ — livello pacchetti: riordina i 3 pacchetti (cifra i₂).",
    "J0": "J₀ — orientazione a livello carte.",
    "J1": "J₁ — orientazione a livello terzine.",
    "J2": "J₂ — orientazione a livello pacchetti.",
}

class FilterFrame(ttk.LabelFrame):
    """
    Pannello filtro per uno stadio con due sezioni affiancate:

    ┌─ Stadio N ────────────────────────────────────────────────────────────────┐
    │ ┌── Permutazioni P ──────────────────────────────┐ ┌── Permutazioni J ──┐ │
    │ │  Fissa      Seleziona uno o più valori          │ │ ☑ J UNIFORMI      │ │
    │ │  P0 [ANY▼]  ☑SCD ☑SDC ☑CSD ☑CDS ☑DSC ☑DCS    │ │   (J0 = J1 = J2)  │ │
    │ │  P1 [ANY▼]  ☑SCD ☑SDC ☑CSD ☑CDS ☑DSC ☑DCS    │ │ ─────────────────  │ │
    │ │  P2 [ANY▼]  ☑SCD ☑SDC ☑CSD ☑CDS ☑DSC ☑DCS    │ │  J0 [ANY▼] ☑I ☑R  │ │
    │ └───────────────────────────────────────────────┘ │  J1 [ANY▼] ☑I ☑R  │ │
    │                                                    │  J2 [ANY▼] ☑I ☑R  │ │
    │                                                    └───────────────────┘ │
    └────────────────────────────────────────────────────────────────────────────┘
    """

    def __init__(self, parent, stage_num, on_change=None, **kw):
        super().__init__(parent,
                         text=f"  Stadio {stage_num}  ",
                         padding=10, **kw)
        self.stage_num = stage_num
        self._on_change = on_change   # callback per aggiornamento live
        self._vars = {}               # nome → (StringVar_dropdown, [(opt, BoolVar)])
        self._j_row_widgets = []      # widget J1 e J2 da disabilitare

        # ── Pannello esplicativo (cosa sono questi controlli) ──────────────
        intro = tk.Frame(self, bg="#EFF5FB",
                         highlightbackground="#BcD3EA",
                         highlightthickness=1)
        intro.pack(side="top", fill="x", pady=(0, 8))
        tk.Label(
            intro,
            text=(
                "Questo stadio applica  P ∘ MSC ∘ J : prima orienti il mazzo (J), "
                "poi lo mescoli in colonne (MSC), poi raccogli (P).\n"
                "P e J sono prodotti di Kronecker di tre matrici 3×3  —  P₃ ⊗ P₂ ⊗ P₁  —  "
                "una per livello:  ① le 3 carte di ogni terzina,  ② le 3 terzine di ogni "
                "pacchetto,  ③ i 3 pacchetti.\n"
                "Fissa un valore col menu «Fissa» per vincolarlo, oppure spunta più caselle "
                "per esplorarne le combinazioni.\n"
                "Vincolo del gioco reale: solo poche scelte sono fisicamente eseguibili — il "
                "preset «Gioco Reale» tiene 12 possibilità per stadio (12³ = 1 728 sequenze). "
                "Liberando tutti i livelli fai una «sintonia fine»: 6×6×6 (P) × 2×2×2 (J) = "
                "1 728 per stadio, cioè 1 728³ ≈ 5,16 miliardi in tutto, comprese trasformazioni "
                "non ottenibili col gioco base."
            ),
            font="GiocoHelp", fg="#243b53", bg="#EFF5FB",
            justify="left", wraplength=1100, anchor="w",
        ).pack(fill="x", padx=10, pady=6)

        # ── Due sezioni affiancate ─────────────────────────────────────────
        p_frame = ttk.LabelFrame(self,
                                  text="  📐  Permutazioni  P  ",
                                  padding=(10, 6),
                                  style="PSection.TLabelframe")
        p_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        j_frame = ttk.LabelFrame(self,
                                  text="  🔀  Permutazioni  J  ",
                                  padding=(10, 6),
                                  style="JSection.TLabelframe")
        j_frame.pack(side="left", fill="y", padx=(10, 0))

        # ── Intestazione colonne P ─────────────────────────────────────────
        hdr = ("Segoe UI", 9, "bold")
        ttk.Label(p_frame, text="",      width=4).grid(row=0, column=0)
        ttk.Label(p_frame, text="Fissa", font=hdr,
                  width=13, anchor="center").grid(row=0, column=1, padx=6)
        ttk.Label(p_frame, text="oppure seleziona uno o più valori:",
                  font=hdr).grid(row=0, column=2, columnspan=7,
                  padx=4, sticky="w")

        # ── Righe P ────────────────────────────────────────────────────────
        for row, name in enumerate(["P0", "P1", "P2"], 1):
            self._add_field_row(p_frame, row, name, P_OPTS,
                                lbl_fg="#1a5276",
                                chk_style="P.TCheckbutton",
                                is_j_secondary=False)

        # ── Flag J uniformi (in cima alla sezione J) ───────────────────────
        self._j_uniform_var = tk.BooleanVar(value=False)
        if on_change:
            self._j_uniform_var.trace_add("write",
                lambda *_: on_change())

        j_unif_frame = tk.Frame(j_frame, bg="#FFF3E0",
                                highlightbackground="#E65100",
                                highlightthickness=1)
        j_unif_frame.grid(row=0, column=0, columnspan=6,
                           sticky="ew", pady=(0, 8), padx=2)

        self._j_uniform_chk = ttk.Checkbutton(
            j_unif_frame,
            text="  ⚡  J UNIFORMI  —  J0 = J1 = J2",
            variable=self._j_uniform_var,
            command=self._on_j_uniform_toggle,
            style="JUniform.TCheckbutton",
        )
        self._j_uniform_chk.pack(fill="x", padx=6, pady=5)

        ttk.Label(j_unif_frame,
                  text="     2 combinazioni J invece di 8",
                  font=("Segoe UI", 9, "italic"),
                  foreground="#BF360C",
                  background="#FFF3E0").pack(anchor="w", padx=6, pady=(0, 4))

        ttk.Separator(j_frame, orient="horizontal").grid(
            row=1, column=0, columnspan=6, sticky="ew", pady=(0, 6))

        # ── Intestazione colonne J ─────────────────────────────────────────
        ttk.Label(j_frame, text="",      width=4).grid(row=2, column=0)
        ttk.Label(j_frame, text="Fissa", font=hdr,
                  width=10, anchor="center").grid(row=2, column=1, padx=6)
        ttk.Label(j_frame, text="Valori:",
                  font=hdr).grid(row=2, column=2, columnspan=3,
                  padx=4, sticky="w")

        # ── Righe J ────────────────────────────────────────────────────────
        for row, name in enumerate(["J0", "J1", "J2"], 3):
            ws = self._add_field_row(j_frame, row, name, J_OPTS,
                                     lbl_fg="#7b4000",
                                     chk_style="J.TCheckbutton",
                                     is_j_secondary=(name in ("J1", "J2")))
            if name in ("J1", "J2"):
                self._j_row_widgets.extend(ws)

    # ─────────────────────────────────────────────────────────────────────────

    def _add_field_row(self, parent, row, name, opts,
                       lbl_fg, chk_style, is_j_secondary):
        """
        Aggiunge una riga label + combo + checkbox.
        Ritorna lista dei widget (per abilitazione/disabilitazione J1/J2).
        """
        widgets = []

        lbl = ttk.Label(parent, text=name,
                        font=("Consolas", 11, "bold"),
                        foreground=lbl_fg, width=4, anchor="e")
        lbl.grid(row=row, column=0, sticky="e", padx=(4, 2), pady=5)
        widgets.append(lbl)
        if name in _LEVEL_DESC:
            _tip(lbl, _LEVEL_DESC[name])

        dvar = tk.StringVar(value=ANY)
        if self._on_change:
            dvar.trace_add("write", lambda *_: self._on_change())
        combo = ttk.Combobox(parent, textvariable=dvar,
                             values=[ANY] + opts, width=11,
                             state="readonly",
                             font=("Consolas", 10))
        combo.grid(row=row, column=1, padx=(2, 10), pady=5)
        widgets.append(combo)
        _tip(combo, "Fissa " + name + " a un valore preciso "
                    "(oppure * = considera tutte le opzioni).")

        bvars = []
        for k, opt in enumerate(opts):
            bv = tk.BooleanVar(value=True)
            if self._on_change:
                bv.trace_add("write", lambda *_: self._on_change())
            chk = ttk.Checkbutton(parent, text=opt,
                                  variable=bv,
                                  style=chk_style)
            chk.grid(row=row, column=2 + k, padx=4, pady=5, sticky="w")
            bvars.append((opt, bv))
            widgets.append(chk)
            _desc = _PERM3_DESC.get(opt) or _J_DESC.get(opt)
            if _desc:
                _tip(chk, opt + " — " + _desc)

        self._vars[name] = (dvar, bvars)
        return widgets

    # ─────────────────────────────────────────────────────────────────────────

    def _on_j_uniform_toggle(self):
        """Abilita/disabilita i controlli J1 e J2 in base al flag."""
        state = "disabled" if self._j_uniform_var.get() else "normal"
        for w in self._j_row_widgets:
            try:
                w.configure(state=state)
            except tk.TclError:
                pass
        if self._on_change:
            self._on_change()

    # ─────────────────────────────────────────────────────────────────────────

    def get_filter(self):
        """
        Ritorna un dict con chiavi:
            p0, p1, p2  → valore fisso, ANY, o lista
            j0, j1, j2  → valore fisso, ANY, o lista
            j_uniform   → bool

        Quando j_uniform=True, i valori j2 e j3 nel dict vengono
        ignorati dal generatore, che usa solo j1 come valore comune.
        """
        result = {}
        for name, (dvar, bvars) in self._vars.items():
            dval = dvar.get()
            if dval != ANY:
                result[name.lower()] = dval
            else:
                selected = [opt for opt, bv in bvars if bv.get()]
                opts = P_OPTS if name.startswith("P") else J_OPTS
                if len(selected) == len(opts):
                    result[name.lower()] = ANY
                elif len(selected) == 1:
                    result[name.lower()] = selected[0]
                elif len(selected) == 0:
                    result[name.lower()] = opts[0]   # fallback
                else:
                    result[name.lower()] = selected
        result['j_uniform'] = self._j_uniform_var.get()
        return result

    def reset(self):
        """Azzera tutti i controlli incluso il flag J uniformi."""
        for name, (dvar, bvars) in self._vars.items():
            dvar.set(ANY)
            for _, bv in bvars:
                bv.set(True)
        self._j_uniform_var.set(False)
        self._on_j_uniform_toggle()

    def set_preset_gioco_reale(self):
        """
        Preset Gioco Reale:
          P2 = libero  (6 scelte — la raccolta fisica agisce al livello
                        dei blocchi: è il fattore piu' significativo)
          P1 = SCD_U   (identità)
          P2 = SCD_U   (identità)
          J  = uniformi (J0 = J1 = J2, 2 scelte: rovesciamento del mazzo)
        → 1 × 1 × 6 × 2 = 12 combinazioni per stadio → 12³ = 1728 totali

        Nota: liberare P0 o P1 al posto di P2 genera lo stesso INSIEME di
        216 tabelloni (la distribuzione MSC fa ruotare i livelli), ma la
        corrispondenza fra singola scelta di raccolta e tabellone è
        quella del gioco fisico solo con P2 (verificata contro la tavola
        delle disposizioni semplici del libro: vedi core/gioco_reale.py).
        """
        # Reset completo
        for name, (dvar, bvars) in self._vars.items():
            dvar.set(ANY)
            for _, bv in bvars:
                bv.set(True)
        # Fissa P0 e P1 (la raccolta reale è P2)
        self._vars['P0'][0].set('SCD_U')
        self._vars['P1'][0].set('SCD_U')
        # Attiva J uniformi
        self._j_uniform_var.set(True)
        self._on_j_uniform_toggle()

    def set_j_uniform(self, val: bool):
        """Imposta il flag J uniformi e aggiorna i widget."""
        self._j_uniform_var.set(val)
        self._on_j_uniform_toggle()


# ─────────────────────────────────────────────────────────────────────────────
# GUI — APPLICAZIONE PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# RICERCA ALGEBRICA DI TUTTE LE DECOMPOSIZIONI  T⁻¹ = A2∘MSC∘A1∘MSC∘A0∘MSC
# ─────────────────────────────────────────────────────────────────────────────

