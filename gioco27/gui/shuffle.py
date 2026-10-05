"""ShuffleViewerFrame: visualizzatore animato del mescolamento."""
import tkinter as tk
from tkinter import ttk
import numpy as np

from ..core.espressione import ParseError, traccia_simulazione
from .i18n import tr
from . import guidance

class ShuffleViewerFrame(ttk.Frame):
    """
    Pannello che simula passo-per-passo l'azione di una formula simbolica
    K_n o MSC o ... o K_1 o MSC  sul mazzo di 27 carte.
    """

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
        guidance.install(self, "shuffle")

    # ─── UI ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        # Riga 0: formula + pulsante Carica
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text=tr("shuffle.formula_active"),
                  font=("Segoe UI", 10, "bold"),
                  foreground="#1a3a5c").grid(row=0, column=0, padx=(0, 6))
        self._formula_lbl = ttk.Label(
            top, text=tr("shuffle.no_formula"),
            font=("Courier New", 9), foreground="#888",
            wraplength=760, justify="left", anchor="w")
        self._formula_lbl.grid(row=0, column=1, sticky="ew")
        ttk.Button(top, text=f"\u2b06  {tr('shuffle.load_explorer')}",
                   command=self.load_formula).grid(row=0, column=2, padx=(8, 0))

        # Riga 1: step counter + label operazione
        info = ttk.Frame(self)
        info.grid(row=1, column=0, sticky="ew", pady=(0, 3))
        self._step_lbl = ttk.Label(info, text=tr("shuffle.step", current="—", total="—"),
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
        gf = ttk.LabelFrame(mid, text=f" {tr('shuffle.grid')} ", padding=4)
        gf.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        for c in range(3):
            lbl_txt = tr("shuffle.column", number=c)
            ttk.Label(gf, text=lbl_txt, font=("Segoe UI", 8, "bold"),
                      foreground="#555", width=6,
                      anchor="center").grid(row=0, column=c, pady=(0, 2))
        self._cell_labels = []
        for row in range(9):
            row_lbls = []
            for col in range(3):
                lbl = tk.Label(gf, text="—",
                               font=("Courier New", 9, "bold"),
                               width=5, relief="solid", borderwidth=1,
                               bg=self._CLR_NORMAL, padx=3, pady=3,
                               anchor="center")
                lbl.grid(row=row + 1, column=col, padx=2, pady=1,
                         sticky="nsew")
                row_lbls.append(lbl)
            self._cell_labels.append(row_lbls)

        # Pannello destro: vettore + log
        vf = ttk.LabelFrame(mid, text=f" {tr('shuffle.deck_state')} ", padding=4)
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

        ttk.Label(vf, text=tr("shuffle.step_history"),
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
            self, text=f" {tr('shuffle.inverse_info')} ",
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
                      font=("Segoe UI", 8), foreground="#526273",
                      anchor="center").grid(row=1, column=v, sticky="ew")

        # Riga 4: controlli
        ctrl = ttk.Frame(self)
        ctrl.grid(row=2, column=0, sticky="ew", pady=(6, 2))
        mid.grid_configure(row=4)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(4, weight=1)
        ttk.Button(ctrl, text=f"\u23ee  {tr('shuffle.reset')}",
                   command=self.reset).pack(side="left", padx=2)
        ttk.Button(ctrl, text=f"\u23ed  {tr('shuffle.step_button')}",
                   command=self.step_once).pack(side="left", padx=2)
        self._play_btn = ttk.Button(ctrl, text=f"\u25b6  {tr('shuffle.play')}",
                                     command=self._toggle_play)
        self._play_btn.pack(side="left", padx=2)
        ttk.Button(ctrl, text=f"\U0001f501  {tr('shuffle.replay')}",
                   command=self._replay).pack(side="left", padx=2)
        ttk.Separator(ctrl, orient="vertical").pack(
            side="left", fill="y", padx=10)
        ttk.Label(ctrl, text=tr("shuffle.speed")).pack(side="left")
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
        ttk.Checkbutton(ctrl, text=tr("shuffle.card_by_card"),
                        variable=self._card_mode,
                        command=self._on_card_mode_change
                        ).pack(side="left", padx=2)

        # Riga 3b: navigazione estesa
        ctrl2 = ttk.Frame(self)
        ctrl2.grid(row=3, column=0, sticky="ew", pady=(0, 2))
        inv_row_f.grid_configure(row=5)

        ttk.Button(ctrl2, text=f"⏮ {tr('shuffle.start')}",
                   command=self._goto_start
                   ).pack(side="left", padx=2)
        ttk.Button(ctrl2, text=f"⏪ {tr('shuffle.start_step')}",
                   command=self._goto_start_of_step
                   ).pack(side="left", padx=2)
        ttk.Button(ctrl2, text=f"◄ {tr('shuffle.back')}",
                   command=self._step_back
                   ).pack(side="left", padx=2)
        ttk.Separator(ctrl2, orient="vertical").pack(
            side="left", fill="y", padx=8)
        ttk.Button(ctrl2, text=f"{tr('shuffle.end_step')} ⏩",
                   command=self._goto_end_of_step
                   ).pack(side="left", padx=2)
        ttk.Button(ctrl2, text=f"{tr('shuffle.next_step')} ⏭",
                   command=self._goto_start_of_next_step
                   ).pack(side="left", padx=2)
        ttk.Button(ctrl2, text=f"{tr('shuffle.end')} ⏭",
                   command=self._goto_end
                   ).pack(side="left", padx=2)

        # Riga 4: messaggio (ora riga 5)
        self._msg_lbl = ttk.Label(
            self, text="", font=("Segoe UI", 9, "italic"),
            foreground="#555", wraplength=950, justify="left")
        self._msg_lbl.grid(row=6, column=0, sticky="ew", pady=(2, 0))
        self._transport = [w for row in (ctrl, ctrl2) for w in row.winfo_children()
                           if isinstance(w, ttk.Button)]
        self._update_transport()

    def _update_transport(self):
        for button in self._transport:
            button.state(["!disabled" if self._steps else "disabled"])

    # ─── caricamento e validazione ────────────────────────────────────────────
    def load_formula(self):
        raw = self._app._explorer_entry.get("1.0", "end").strip()
        if not raw:
            self._set_error(
                tr("shuffle.no_formula_explorer"))
            return
        try:
            traccia = self._validate_and_parse(raw)
        except (ParseError, ValueError) as exc:
            # ParseError: non e' una formula. EspressioneNonSimulabile: lo e',
            # ma non descrive un mazzo di 27 carte. Due cause distinte, non un
            # unico «non ho capito».
            self._set_error(str(exc))
            self._formula_lbl.configure(
                text=raw.replace("\n", " ")[:120],
                foreground=self._CLR_ERR)
            return
        n_msc  = sum(1 for passo in traccia if passo.operazione == "MSC")
        n_kron = sum(1 for passo in traccia if passo.operazione == "KRON")
        self._formula_lbl.configure(
            text=raw.replace("\n", " ")[:160], foreground="#333")
        self._set_msg(tr("shuffle.formula_loaded", kron=n_kron, msc=n_msc,
                         total=1 + len(traccia)))
        self._traccia = traccia
        if self._card_mode.get():
            self._build_steps_card_by_card(traccia)
        else:
            self._build_steps(traccia)
        self.reset()
        self._update_transport()

    def _validate_and_parse(self, expr):
        """Adattatore: chiede il parsing al linguaggio, non lo esegue.

        Fino al compartimento E questo metodo **era** un secondo parser: una
        manciata di espressioni regolari che cancellavano l'operatore finale,
        buttavano via le parentesi spaiate e conoscevano soltanto MSC e i
        blocchi Kronecker. Accettava `MSC o` e `MSC)`, che l'Explorer
        rifiutava, e rifiutava `I`, `J` e i fattori Kronecker composti, che
        l'Explorer accettava: era B07.

        Ora qui non c'e' nessuna grammatica. Il testo va al parser autorevole
        (`core.algebra`, via `core.espressione`) e torna una
        `TracciaEsecuzione` derivata dalla stessa AST che l'Explorer valuta.
        Il metodo resta solo perche' e' il punto di ingresso storico della
        vista.

        Solleva `ParseError` se il testo non e' una formula valida e
        `EspressioneNonSimulabile` se lo e' ma non descrive un mazzo di 27.
        """
        return traccia_simulazione(expr)

    # ─── costruzione passi ────────────────────────────────────────────────────
    def _etichetta_operazione(self, passo, totale):
        """Testo dell'intestazione per un passo della traccia."""
        if passo.operazione == "MSC":
            return tr("shuffle.operation_msc",
                      current=passo.indice + 1, total=totale)
        if passo.operazione == "KRON":
            return tr("shuffle.operation_kron", label=passo.etichetta,
                      current=passo.indice + 1, total=totale)
        return tr("shuffle.operation_atom", label=passo.etichetta,
                  current=passo.indice + 1, total=totale)

    def _build_steps(self, traccia):
        """Un passo visivo per ogni passo della traccia.

        L'ordine e' gia' quello cronologico deciso dal linguaggio (il fattore
        piu' a destra e' il primo applicato): qui non si inverte nulla e non si
        calcola nessuna permutazione. Lo stato del mazzo arriva dalla traccia.
        """
        passi = list(traccia)
        n     = len(passi)
        deck  = np.arange(27, dtype=np.int32)
        steps = [dict(type="INIT",
                      deck_before=deck.copy(), deck=deck.copy(),
                      changed=set(), changed_order=[],
                      label=tr("shuffle.initial_state"), ki=0, n=n)]
        for passo in passi:
            nd      = np.array(passo.mazzo, dtype=np.int32)
            lbl     = self._etichetta_operazione(passo, n)
            changed = {i for i in range(27) if nd[i] != deck[i]}
            steps.append(dict(type=passo.operazione,
                              deck_before=deck.copy(), deck=nd.copy(),
                              deck_final=nd.copy(),
                              changed=changed,
                              changed_order=sorted(changed),
                              label=lbl, ki=passo.indice + 1, n=n))
            deck = nd
        self._steps = steps
        self._cur   = 0

    def _build_steps_card_by_card(self, traccia):
        """Come _build_steps, ma ogni operazione è espansa in un sotto-passo
        per carta spostata (deck intermedio cumulativo; card_step=True salta
        il controllo di validità della permutazione in _refresh)."""
        passi = list(traccia)
        n     = len(passi)
        deck  = np.arange(27, dtype=np.int32)
        steps = [dict(type="INIT",
                      deck_before=deck.copy(), deck=deck.copy(),
                      changed=set(), changed_order=[],
                      label=tr("shuffle.initial_state"), ki=0, n=n,
                      card_step=False)]
        for passo in passi:
            nd      = np.array(passo.mazzo, dtype=np.int32)
            lbl     = self._etichetta_operazione(passo, n)
            ki      = passo.indice + 1
            changed = [i for i in range(27) if nd[i] != deck[i]]
            total_c = len(changed)
            db      = deck.copy()
            if total_c == 0:
                steps.append(dict(type=passo.operazione,
                                  deck_before=db, deck=nd.copy(),
                                  changed=set(), changed_order=[],
                                  label=tr("shuffle.no_card_movement", label=lbl),
                                  ki=ki, n=n, card_step=False))
            else:
                for sub_i, pos in enumerate(changed):
                    mid = db.copy()
                    for j in range(sub_i + 1):
                        mid[changed[j]] = nd[changed[j]]
                    is_last = (sub_i == total_c - 1)
                    steps.append(dict(type=passo.operazione,
                                      deck_before=db,
                                      deck=mid,
                                      deck_final=nd,
                                      changed={pos},
                                      changed_order=[pos],
                                      label=(lbl if is_last else tr(
                                          "shuffle.substep", label=lbl,
                                          current=sub_i + 1, total=total_c)),
                                      ki=ki, n=n,
                                      card_step=not is_last))
            deck = nd
        self._steps = steps
        self._cur   = 0

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
        if getattr(self, "_traccia", None):
            if self._card_mode.get():
                self._build_steps_card_by_card(self._traccia)
            else:
                self._build_steps(self._traccia)
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
        self._traccia = None
        self._steps = []
        for row in self._cell_labels:
            for label in row:
                label.configure(text="—", bg=self._CLR_NORMAL)
        for label in self._inv_labels:
            label.configure(text="·", bg="#F0F0F0", fg="#555")
        for text in (self._vec_text, self._log_text):
            text.configure(state="normal")
            text.delete("1.0", "end")
            text.configure(state="disabled")
        self._formula_lbl.configure(text=tr("shuffle.no_formula"), foreground="#555")
        self._step_lbl.configure(text=tr("shuffle.step", current="—", total="—"))
        self._op_lbl.configure(text="")
        self._set_msg(tr("shuffle.no_formula_loaded"))
        self._cur = 0
        self._refresh()
        self._update_transport()

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
            self._set_error(tr("shuffle.play_requires_formula"))
            return
        self._playing = True
        self._play_btn.configure(text=f"⏸  {tr('shuffle.pause')}")
        self._tick()

    def pause(self):
        self._playing = False
        self._play_btn.configure(text=f"▶  {tr('shuffle.play')}")
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
            self._set_error(tr("shuffle.invalid_deck"))
            return

        self._step_lbl.configure(
            text=tr("shuffle.step", current=self._cur, total=total - 1))

        if s["type"] == "INIT":
            self._op_lbl.configure(
                text=tr("shuffle.ordered_deck"),
                foreground="#555")
        elif s["type"] == "MSC":
            self._op_lbl.configure(
                text=s["label"],
                foreground=self._CLR_MSC_HDR)
        else:
            self._op_lbl.configure(
                text=s["label"],
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
                "end", tr("shuffle.position_range", start=start,
                           end=start + 8), "pos")
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
                    "end", f"{pre}{tr('shuffle.log_initial')}\n",
                    ("init",) + extra)
            elif s["type"] == "MSC":
                self._log_text.insert(
                    "end",
                    f"{pre}{tr('shuffle.log_msc', count=len(s['changed']))}\n",
                    ("msc",) + extra)
            else:
                self._log_text.insert(
                    "end",
                    f"{pre}{tr('shuffle.log_kron', label=s['label'], count=len(s['changed']))}\n",
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
            text=f"\u2713  {tr('shuffle.completed', vector=vec)}",
            foreground=self._CLR_DONE)


# ─────────────────────────────────────────────────────────────────────────────
# DIALOG  —  Decomposizioni di T⁻¹
# ─────────────────────────────────────────────────────────────────────────────
