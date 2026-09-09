"""ShuffleViewerFrame: visualizzatore animato del mescolamento."""
import tkinter as tk
from tkinter import ttk
import numpy as np

from ..core.constants import PERM3, _MSC_PERM

class ShuffleViewerFrame(ttk.Frame):
    """
    Pannello che simula passo-per-passo l'azione di una formula simbolica
    K_n o MSC o ... o K_1 o MSC  sul mazzo di 27 carte.
    """

    GEN3 = {"SCD_U", "SDC_U", "CSD_U", "CDS_U", "DSC_U", "DCS_U"}
    _CLR_NORMAL   = "#FFFFFF"
    _CLR_MOVED    = "#FFF59D"
    _CLR_MSC_HDR  = "#1565C0"
    _CLR_KRON_HDR = "#2E7D32"
    _CLR_DONE     = "#1B5E20"
    _CLR_ERR      = "#C62828"

    def __init__(self, parent, app):
        super().__init__(parent, padding=6)
        self._app      = app
        self._steps    = []
        self._cur      = 0
        self._playing  = False
        self._play_id  = None
        self._speed_ms = 800
        self._build_ui()

    # ─── UI ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        # Riga 0: formula + pulsante Carica
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Formula attiva:",
                  font=("Segoe UI", 10, "bold"),
                  foreground="#1a3a5c").grid(row=0, column=0, padx=(0, 6))
        self._formula_lbl = ttk.Label(
            top, text="— nessuna formula caricata —",
            font=("Courier New", 9), foreground="#888",
            wraplength=760, justify="left", anchor="w")
        self._formula_lbl.grid(row=0, column=1, sticky="ew")
        ttk.Button(top, text="\u2b06  Carica da Explorer",
                   command=self.load_formula).grid(row=0, column=2, padx=(8, 0))

        # Riga 1: step counter + label operazione
        info = ttk.Frame(self)
        info.grid(row=1, column=0, sticky="ew", pady=(0, 3))
        self._step_lbl = ttk.Label(info, text="Step \u2014 / \u2014",
                                    font=("Segoe UI", 10, "bold"),
                                    foreground="#555", width=16)
        self._step_lbl.pack(side="left", padx=(0, 10))
        self._op_lbl = ttk.Label(info, text="",
                                  font=("Segoe UI", 11, "bold"),
                                  foreground=self._CLR_MSC_HDR)
        self._op_lbl.pack(side="left")

        # Riga 2: griglia + vettore
        mid = ttk.Frame(self)
        mid.grid(row=2, column=0, sticky="nsew")
        mid.rowconfigure(0, weight=1)
        mid.columnconfigure(0, weight=0)
        mid.columnconfigure(1, weight=1)


        # Griglia 9 righe x 3 colonne
        gf = ttk.LabelFrame(mid, text=" Griglia 3 \u00d7 9 ", padding=4)
        gf.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        for c, lbl_txt in enumerate(["Col 0", "Col 1", "Col 2"]):
            ttk.Label(gf, text=lbl_txt, font=("Segoe UI", 8, "bold"),
                      foreground="#555", width=6,
                      anchor="center").grid(row=0, column=c, pady=(0, 2))
        self._cell_labels = []
        for row in range(9):
            row_lbls = []
            for col in range(3):
                lbl = tk.Label(gf, text="C00",
                               font=("Courier New", 9, "bold"),
                               width=5, relief="solid", borderwidth=1,
                               bg=self._CLR_NORMAL, padx=3, pady=3,
                               anchor="center")
                lbl.grid(row=row + 1, column=col, padx=2, pady=1,
                         sticky="nsew")
                row_lbls.append(lbl)
            self._cell_labels.append(row_lbls)

        # Pannello destro: vettore + log
        vf = ttk.LabelFrame(mid, text=" Stato mazzo ", padding=4)
        vf.grid(row=0, column=1, sticky="nsew")
        vf.rowconfigure(2, weight=1)
        vf.columnconfigure(0, weight=1)

        self._vec_text = tk.Text(
            vf, font=("Courier New", 9), state="disabled",
            wrap="none", height=5, bg="#FAFBFC",
            borderwidth=1, relief="groove")
        self._vec_text.grid(row=0, column=0, columnspan=2,
                             sticky="ew", pady=(0, 4))
        self._vec_text.tag_configure(
            "pos",  foreground="#888", font=("Courier New", 8))
        self._vec_text.tag_configure(
            "card", foreground="#1a3a5c", font=("Courier New", 9, "bold"))
        self._vec_text.tag_configure(
            "mv",   foreground="#B8520A", font=("Courier New", 9, "bold"))
        self._vec_text.tag_configure(
            "blank", foreground="#cccccc", font=("Courier New", 9))

        ttk.Label(vf, text="Storico passi:",
                  font=("Segoe UI", 9, "bold"),
                  foreground="#555").grid(row=1, column=0,
                                          sticky="w", pady=(0, 2))
        log_fr = ttk.Frame(vf)
        log_fr.grid(row=2, column=0, columnspan=2, sticky="nsew")
        log_fr.rowconfigure(0, weight=1)
        log_fr.columnconfigure(0, weight=1)

        self._log_text = tk.Text(
            log_fr, font=("Courier New", 8), state="disabled",
            wrap="none", bg="#FAFBFC",
            borderwidth=1, relief="groove")
        log_sb = ttk.Scrollbar(log_fr, orient="vertical",
                                command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=log_sb.set)
        self._log_text.grid(row=0, column=0, sticky="nsew")
        log_sb.grid(row=0, column=1, sticky="ns")
        self._log_text.tag_configure(
            "msc",  foreground=self._CLR_MSC_HDR,
            font=("Courier New", 8, "bold"))
        self._log_text.tag_configure(
            "kron", foreground=self._CLR_KRON_HDR,
            font=("Courier New", 8, "bold"))
        self._log_text.tag_configure(
            "init", foreground="#555", font=("Courier New", 8, "italic"))
        self._log_text.tag_configure(
            "done", foreground=self._CLR_DONE,
            font=("Courier New", 8, "bold"))
        self._log_text.tag_configure("cur", background="#E3F2FD")

        # Riga 3: vettore inverso T⁻¹ (1 riga × 27 celle)
        inv_row_f = ttk.LabelFrame(
            self, text=" T⁻¹  —  indice = posizione nel mazzo,  contenuto = valore carta ",
            padding=(4, 2))
        inv_row_f.grid(row=3, column=0, sticky="ew", pady=(4, 2))
        self._inv_labels = []
        for v in range(27):
            lbl = tk.Label(inv_row_f, text="·",
                           font=("Courier New", 8, "bold"),
                           width=3, relief="solid", borderwidth=1,
                           bg="#F0F0F0", fg="#aaa",
                           padx=1, pady=3, anchor="center")
            lbl.grid(row=0, column=v, padx=1, pady=2, sticky="nsew")
            self._inv_labels.append(lbl)
        # piccola etichetta sotto ogni cella con la posizione nel mazzo
        for v in range(27):
            ttk.Label(inv_row_f, text=f"{v:02d}",
                      font=("Segoe UI", 6), foreground="#999",
                      anchor="center").grid(row=1, column=v, sticky="ew")

        # Riga 4: controlli
        ctrl = ttk.Frame(self)
        ctrl.grid(row=4, column=0, sticky="ew", pady=(6, 2))
        ttk.Button(ctrl, text="\u23ee  Reset",
                   command=self.reset).pack(side="left", padx=2)
        ttk.Button(ctrl, text="\u23ed  Step",
                   command=self.step_once).pack(side="left", padx=2)
        self._play_btn = ttk.Button(ctrl, text="\u25b6  Play",
                                     command=self._toggle_play)
        self._play_btn.pack(side="left", padx=2)
        ttk.Button(ctrl, text="\U0001f501  Replay",
                   command=self._replay).pack(side="left", padx=2)
        ttk.Separator(ctrl, orient="vertical").pack(
            side="left", fill="y", padx=10)
        ttk.Label(ctrl, text="Velocit\u00e0:").pack(side="left")
        self._speed_var = tk.IntVar(value=self._speed_ms)
        self._speed_var.trace_add("write", self._on_speed_trace)
        ttk.Scale(ctrl, from_=100, to=3000,
                  variable=self._speed_var, orient="horizontal",
                  length=180, command=self._on_speed_cmd
                  ).pack(side="left", padx=4)
        self._speed_lbl = ttk.Label(ctrl, text="800 ms", width=8)
        self._speed_lbl.pack(side="left")

        # Toggle carta-per-carta
        ttk.Separator(ctrl, orient="vertical").pack(
            side="left", fill="y", padx=10)
        self._card_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctrl, text="Carta per carta",
                        variable=self._card_mode,
                        command=self._on_card_mode_change
                        ).pack(side="left", padx=2)

        # Riga 3b: navigazione estesa
        ctrl2 = ttk.Frame(self)
        ctrl2.grid(row=5, column=0, sticky="ew", pady=(0, 2))

        ttk.Button(ctrl2, text="⏮ Inizio",
                   command=self._goto_start
                   ).pack(side="left", padx=2)
        ttk.Button(ctrl2, text="⏪ Inizio step",
                   command=self._goto_start_of_step
                   ).pack(side="left", padx=2)
        ttk.Button(ctrl2, text="◄ Indietro",
                   command=self._step_back
                   ).pack(side="left", padx=2)
        ttk.Separator(ctrl2, orient="vertical").pack(
            side="left", fill="y", padx=8)
        ttk.Button(ctrl2, text="Fine step ⏩",
                   command=self._goto_end_of_step
                   ).pack(side="left", padx=2)
        ttk.Button(ctrl2, text="Pross. step ⏭",
                   command=self._goto_start_of_next_step
                   ).pack(side="left", padx=2)
        ttk.Button(ctrl2, text="Fine ⏭",
                   command=self._goto_end
                   ).pack(side="left", padx=2)

        # Riga 4: messaggio (ora riga 5)
        self._msg_lbl = ttk.Label(
            self, text="", font=("Segoe UI", 9, "italic"),
            foreground="#555", wraplength=950, justify="left")
        self._msg_lbl.grid(row=6, column=0, sticky="ew", pady=(2, 0))

    # ─── caricamento e validazione ────────────────────────────────────────────
    def load_formula(self):
        raw = self._app._explorer_entry.get("1.0", "end").strip()
        if not raw:
            self._set_error(
                "Nessuna formula nell'Explorer. "
                "Inserisci una formula e premi 'Carica da Explorer'.")
            return
        try:
            tokens = self._validate_and_parse(raw)
        except ValueError as exc:
            self._set_error(str(exc))
            self._formula_lbl.configure(
                text=raw.replace("\n", " ")[:120],
                foreground=self._CLR_ERR)
            return
        n_msc  = sum(1 for t in tokens if t[0] == "MSC")
        n_kron = sum(1 for t in tokens if t[0] == "KRON")
        self._formula_lbl.configure(
            text=raw.replace("\n", " ")[:160], foreground="#333")
        self._set_msg(
            f"Formula caricata: {n_kron} blocco/i Kronecker + {n_msc} MSC. "
            f"Totale passi: {1 + len(tokens)} (gli operatori si applicano "
            f"da destra a sinistra).")
        self._kron_blocks = tokens
        if self._card_mode.get():
            self._build_steps_card_by_card(tokens)
        else:
            self._build_steps(tokens)
        self.reset()

    def _validate_and_parse(self, expr):
        """
        Parser della formula per la simulazione visiva.

        Dalla v2.8.6 accetta la notazione di gioco completa dell'Explorer:
          • blocchi Kronecker  (a x b x c)  con a,b,c ∈ GEN3 ∪ {R_U, I_3}
          • MSC
          • composizione con  'o', '∘' o '@'
          • parentesi quadre attorno ai turni e prefisso  'T ='
          • qualunque sequenza di blocchi e MSC (non solo K∘MSC alternati):
            un turno di gioco  (P) o MSC o (J)  produce i passi  J → MSC → P
            (la composizione si applica da destra a sinistra)

        Restituisce una lista di token [(tipo, valore, etichetta), ...]
        nell'ordine testuale (sinistra→destra):
          ("MSC",  None,          "MSC")
          ("KRON", (p3, p2, p1),  "(p3 x p2 x p1)")   # nomi GIA' normalizzati
        """
        import re
        e = expr.strip()
        if e.startswith("T ="):
            e = e[3:].strip()
        # normalizza operatori
        e = e.replace("\u2218", " o ")   # ∘
        e = e.replace("@", " o ")
        e = e.replace("\u2297", " x ")   # ⊗
        e = e.replace("\n", " ")
        # le parentesi quadre raggruppano i turni: per associativita'
        # sono irrilevanti nella sequenza piatta
        e = e.replace("[", " ").replace("]", " ")
        e = re.sub(r"[ \t]+", " ", e).strip()
        e = re.sub(r"\s+o\s*$", "", e).strip()

        # 1. estrai i blocchi Kronecker sostituendoli con segnaposto,
        #    cosi' le parentesi residue (di solo raggruppamento) si
        #    possono eliminare senza ambiguita'
        kron_re = re.compile(
            r"\(\s*([A-Za-z0-9_]+)\s+x\s+([A-Za-z0-9_]+)"
            r"\s+x\s+([A-Za-z0-9_]+)\s*\)")
        blocks = []
        def _stash(m):
            blocks.append((m.group(1), m.group(2), m.group(3)))
            return f" \x00K{len(blocks)-1}\x00 "
        e = kron_re.sub(_stash, e)
        # eventuali parentesi tonde rimaste sono solo raggruppamento
        e = e.replace("(", " ").replace(")", " ")
        e = re.sub(r"[ \t]+", " ", e).strip()

        # 2. split per ' o '
        parts = [p.strip() for p in re.split(r"\s+o\s+", e) if p.strip()]
        if not parts:
            raise ValueError("Formula vuota.")

        # 3. classifica
        alias = {"R_U": "DCS_U", "I_3": "SCD_U"}
        tokens = []
        ph_re = re.compile(r"^\x00K(\d+)\x00$")
        for part in parts:
            if part == "MSC":
                tokens.append(("MSC", None, "MSC"))
                continue
            m = ph_re.match(part)
            if not m:
                raise ValueError(
                    f"Token non riconosciuto: \u00ab{part}\u00bb\n"
                    "Attesi blocchi (a x b x c), MSC e l'operatore 'o'.")
            orig = blocks[int(m.group(1))]
            norm = tuple(alias.get(p, p) for p in orig)
            for p in norm:
                if p not in self.GEN3:
                    raise ValueError(
                        f"Generatore sconosciuto: '{p}'.\n"
                        "Ammessi: " + ", ".join(sorted(self.GEN3))
                        + ", R_U, I_3")
            label = f"({orig[0]} x {orig[1]} x {orig[2]})"
            tokens.append(("KRON", norm, label))

        return tokens

    # ─── costruzione passi ────────────────────────────────────────────────────
    def _build_steps(self, tokens):
        """Un passo per ogni operatore, applicati da DESTRA a SINISTRA."""
        msc_inv = np.argsort(np.array(_MSC_PERM, dtype=np.int32))
        deck    = np.arange(27, dtype=np.int32)
        n       = len(tokens)
        steps   = [dict(type="INIT",
                        deck_before=deck.copy(), deck=deck.copy(),
                        changed=set(), changed_order=[],
                        label="Stato iniziale", ki=0, n=n)]
        for ki, (typ, val, label) in enumerate(reversed(tokens), 1):
            if typ == "MSC":
                nd  = deck[msc_inv]
                lbl = f"MSC  (op. {ki}/{n})"
            else:
                p3, p2, p1 = val
                nd  = deck[np.argsort(self._make_kron27(p3, p2, p1))]
                lbl = f"K = {label}  (op. {ki}/{n})"
            changed = {i for i in range(27) if nd[i] != deck[i]}
            steps.append(dict(type=typ,
                              deck_before=deck.copy(), deck=nd.copy(),
                              deck_final=nd.copy(),
                              changed=changed,
                              changed_order=sorted(changed),
                              label=lbl, ki=ki, n=n))
            deck = nd
        self._steps = steps
        self._cur   = 0

    def _build_steps_card_by_card(self, tokens):
        """Come _build_steps, ma ogni operazione è espansa in un sotto-passo
        per carta spostata (deck intermedio cumulativo; card_step=True salta
        il controllo di validità della permutazione in _refresh)."""
        msc_inv = np.argsort(np.array(_MSC_PERM, dtype=np.int32))
        deck    = np.arange(27, dtype=np.int32)
        n       = len(tokens)
        steps   = [dict(type="INIT",
                        deck_before=deck.copy(), deck=deck.copy(),
                        changed=set(), changed_order=[],
                        label="Stato iniziale", ki=0, n=n,
                        card_step=False)]
        for ki, (typ, val, label) in enumerate(reversed(tokens), 1):
            if typ == "MSC":
                nd  = deck[msc_inv]
                lbl = f"MSC  (op. {ki}/{n})"
            else:
                p3, p2, p1 = val
                nd  = deck[np.argsort(self._make_kron27(p3, p2, p1))]
                lbl = f"K = {label}  (op. {ki}/{n})"
            changed = [i for i in range(27) if nd[i] != deck[i]]
            total_c = len(changed)
            db      = deck.copy()
            if total_c == 0:
                steps.append(dict(type=typ,
                                  deck_before=db, deck=nd.copy(),
                                  changed=set(), changed_order=[],
                                  label=lbl + "  (nessuna carta si muove)",
                                  ki=ki, n=n, card_step=False))
            else:
                for sub, pos in enumerate(changed):
                    mid = db.copy()
                    for j in range(sub + 1):
                        mid[changed[j]] = nd[changed[j]]
                    is_last = (sub == total_c - 1)
                    steps.append(dict(type=typ,
                                      deck_before=db,
                                      deck=mid,
                                      deck_final=nd,
                                      changed={pos},
                                      changed_order=[pos],
                                      label=(lbl if is_last
                                             else lbl + f"  [{sub+1}/{total_c}]"),
                                      ki=ki, n=n,
                                      card_step=not is_last))
            deck = nd
        self._steps = steps
        self._cur   = 0

    @staticmethod
    def _make_kron27(p3n, p2n, p1n):
        a = np.array(PERM3[p3n], dtype=np.int32)
        b = np.array(PERM3[p2n], dtype=np.int32)
        c = np.array(PERM3[p1n], dtype=np.int32)
        r = np.empty(27, dtype=np.int32)
        for i in range(27):
            i2, rem = divmod(i, 9); i1, i0 = divmod(rem, 3)
            r[i] = 9 * a[i2] + 3 * b[i1] + c[i0]
        return r

    # ─── controlli ────────────────────────────────────────────────────────────
    def _on_speed_cmd(self, val):
        ms = int(float(val))
        self._speed_lbl.configure(text=f"{ms} ms")

    def _on_speed_trace(self, *_):
        try:
            ms = int(self._speed_var.get())
            self._speed_lbl.configure(text=f"{ms} ms")
        except Exception:
            pass

    def _on_card_mode_change(self):
        """Rebuild step list when card-by-card mode is toggled."""
        self.pause()
        if hasattr(self, "_kron_blocks") and self._kron_blocks:
            if self._card_mode.get():
                self._build_steps_card_by_card(self._kron_blocks)
            else:
                self._build_steps(self._kron_blocks)
        self.reset()

    # ─── navigazione ─────────────────────────────────────────────────────────
    def _group_id(self, idx):
        """Identifica il gruppo (operazione) a cui appartiene lo step idx."""
        s = self._steps[idx]
        return (s["ki"], s["type"])

    def _step_back(self):
        """Vai indietro di un passo (o una carta in modalità carta-per-carta)."""
        self.pause()
        if self._cur > 0:
            self._cur -= 1
            self._refresh()

    def _goto_start_of_step(self):
        """Vai all'inizio dell'operazione corrente."""
        self.pause()
        if not self._steps:
            return
        gid = self._group_id(self._cur)
        i = self._cur
        while i > 0 and self._group_id(i - 1) == gid:
            i -= 1
        self._cur = i
        self._refresh()

    def _goto_end_of_step(self):
        """Vai all'ultimo sub-step dell'operazione corrente."""
        self.pause()
        if not self._steps:
            return
        gid = self._group_id(self._cur)
        i = self._cur
        while i < len(self._steps) - 1 and self._group_id(i + 1) == gid:
            i += 1
        self._cur = i
        self._refresh()

    def _goto_start_of_next_step(self):
        """Vai al primo sub-step dell'operazione successiva (se esiste)."""
        self.pause()
        if not self._steps:
            return
        gid = self._group_id(self._cur)
        i = self._cur
        # salta alla fine del gruppo corrente
        while i < len(self._steps) - 1 and self._group_id(i + 1) == gid:
            i += 1
        # avanza di uno per entrare nel gruppo successivo
        if i < len(self._steps) - 1:
            self._cur = i + 1
            self._refresh()

    def _goto_start(self):
        """Vai allo step 0 (inizio assoluto)."""
        self.pause()
        self._cur = 0
        self._refresh()

    def _goto_end(self):
        """Vai all'ultimo step (fine assoluta)."""
        self.pause()
        self._cur = len(self._steps) - 1
        self._refresh()

    def reset(self):
        self.pause()
        self._cur = 0
        self._refresh()

    def clear_all(self):
        """Reset completo: scarica la formula e torna allo stato iniziale."""
        self.pause()
        self._kron_blocks = None
        self._build_steps([])          # solo lo stato iniziale (mazzo ordinato)
        self._formula_lbl.configure(text="", foreground="#333")
        self._set_msg("Nessuna formula caricata.")
        self._cur = 0
        self._refresh()

    def step_once(self):
        """Avanza di un passo (o una carta in modalità carta-per-carta)."""
        if not self._steps:
            return
        if self._cur < len(self._steps) - 1:
            self._cur += 1
            self._refresh()
        else:
            self.pause()
            self._set_done()

    def _replay(self):
        self.pause()
        self._cur = 0
        self.play()

    def _toggle_play(self):
        if self._playing: self.pause()
        else:             self.play()

    def play(self):
        if not self._steps:
            self._set_error(
                "Nessuna formula caricata. "
                "Premi 'Carica da Explorer' prima.")
            return
        self._playing = True
        self._play_btn.configure(text="⏸  Pausa")
        self._tick()

    def pause(self):
        self._playing = False
        self._play_btn.configure(text="▶  Play")
        if self._play_id is not None:
            self.after_cancel(self._play_id)
            self._play_id = None

    def _tick(self):
        if not self._playing:
            return
        if self._cur >= len(self._steps) - 1:
            self.pause()
            self._set_done()
            return
        self._cur += 1
        self._refresh()
        self._play_id = self.after(int(self._speed_var.get()), self._tick)

    # ─── refresh ──────────────────────────────────────────────────────────────
    def _refresh(self):
        if not self._steps:
            return
        s     = self._steps[self._cur]
        total = len(self._steps)
        deck  = s["deck"]
        chg   = s["changed"]

        if not s.get("card_step") and (
                len(deck) != 27 or len(set(deck.tolist())) != 27):
            self.pause()
            self._set_error("Stato mazzo non valido!")
            return

        self._step_lbl.configure(
            text=f"Step {self._cur} / {total - 1}")

        if s["type"] == "INIT":
            self._op_lbl.configure(
                text="Stato iniziale  (mazzo ordinato  C00 … C26)",
                foreground="#555")
        elif s["type"] == "MSC":
            self._op_lbl.configure(
                text=f"Operazione corrente:  {s['label']}",
                foreground=self._CLR_MSC_HDR)
        else:
            self._op_lbl.configure(
                text=f"Operazione corrente:  {s['label']}",
                foreground=self._CLR_KRON_HDR)

        self._redraw_grid(deck, chg)
        self._redraw_vector(deck, chg,
                            deck_before=s.get("deck_before"),
                            card_step=s.get("card_step", False))
        self._redraw_inv_vector(deck, chg,
                                deck_before=s.get("deck_before"),
                                deck_final=s.get("deck_final", deck),
                                card_step=s.get("card_step", False))
        self._update_log()
        if self._cur == total - 1:
            self._set_done()
        else:
            self._set_msg("")

    def _redraw_grid(self, deck, changed):
        for row in range(9):
            for col in range(3):
                pos  = col * 9 + row
                card = int(deck[pos])
                bg   = self._CLR_MOVED if pos in changed else self._CLR_NORMAL
                self._cell_labels[row][col].configure(
                    text=f"C{card:02d}", bg=bg)

    def _redraw_vector(self, deck, changed, deck_before=None, card_step=False):
        """Disegna il vettore mazzo.
        In modalità carta-per-carta (card_step=True) le posizioni non ancora
        rivelate (deck[i]==deck_before[i]) appaiono come "---" in grigio chiaro,
        mentre le carte già spostate mostrano il loro valore finale.
        """
        self._vec_text.configure(state="normal")
        self._vec_text.delete("1.0", "end")
        for start in range(0, 27, 9):
            self._vec_text.insert(
                "end", f"pos {start:02d}-{start+8:02d}:  ", "pos")
            for i in range(start, start + 9):
                if card_step and deck_before is not None and int(deck[i]) == int(deck_before[i]):
                    # carta non ancora spostata: mostra vuoto
                    self._vec_text.insert("end", "---", "blank")
                else:
                    tag = "mv" if i in changed else "card"
                    self._vec_text.insert("end", f"C{int(deck[i]):02d}", tag)
                if i < start + 8:
                    self._vec_text.insert("end", "  ")
            self._vec_text.insert("end", "\n")
        self._vec_text.configure(state="disabled")

    def _redraw_inv_vector(self, deck, changed, deck_before=None,
                           deck_final=None, card_step=False):
        """Aggiorna la griglia T⁻¹: cella pos = carta nella posizione pos.

        In modalità carta-per-carta una cella è rivelata quando contiene già
        la carta prevista da deck_final per quella posizione nello step.
        """
        _CLR_EMPTY   = "#F0F0F0"
        _CLR_DONE    = "#D6EDD6"   # verde chiaro — rivelata
        _CLR_CURRENT = self._CLR_MOVED   # arancione — appena mossa

        if deck_final is None:
            deck_final = deck
        for pos in range(27):
            final_card = int(deck_final[pos])
            lbl = self._inv_labels[pos]

            if card_step and deck_before is not None:
                revealed = (int(deck[pos]) == final_card)
            else:
                revealed = True

            if not revealed:
                lbl.configure(text="·", bg=_CLR_EMPTY, fg="#aaa")
            elif pos in changed:
                lbl.configure(text=f"{final_card:02d}", bg=_CLR_CURRENT, fg="white")
            else:
                lbl.configure(text=f"{final_card:02d}", bg=_CLR_DONE, fg="#1a5c1a")

    def _update_log(self):
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        for i, s in enumerate(self._steps):
            extra = ("cur",) if i == self._cur else ()
            pre   = f"  {i:>3}  "
            if s["type"] == "INIT":
                self._log_text.insert(
                    "end", f"{pre}Stato iniziale\n", ("init",) + extra)
            elif s["type"] == "MSC":
                self._log_text.insert(
                    "end",
                    f"{pre}MSC  ({len(s['changed'])} carte spostate)\n",
                    ("msc",) + extra)
            else:
                self._log_text.insert(
                    "end",
                    f"{pre}{s['label']}  ({len(s['changed'])} carte)\n",
                    ("kron",) + extra)
        self._log_text.see(f"{self._cur + 1}.0")
        self._log_text.configure(state="disabled")

    # ─── messaggi ─────────────────────────────────────────────────────────────
    def _set_error(self, msg):
        self._msg_lbl.configure(text=f"\u26a0  {msg}",
                                 foreground=self._CLR_ERR)

    def _set_msg(self, msg):
        col = self._CLR_DONE if msg.startswith("\u2713") else "#555"
        self._msg_lbl.configure(text=msg, foreground=col)

    def _set_done(self):
        if not self._steps: return
        final = self._steps[-1]["deck"]
        vec   = "  ".join(f"C{int(x):02d}" for x in final)
        self._msg_lbl.configure(
            text=f"\u2713  Simulazione completata.  Vettore finale:  {vec}",
            foreground=self._CLR_DONE)


# ─────────────────────────────────────────────────────────────────────────────
# DIALOG  —  Decomposizioni di T⁻¹
# ─────────────────────────────────────────────────────────────────────────────
