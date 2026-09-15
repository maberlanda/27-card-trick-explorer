"""
Tab "🎩 Simulatore"

Simula il trucco delle 27 carte esattamente come si esegue col mazzo vero:

  1. l'utente sceglie la posizione della carta del pubblico e la posizione
     finale desiderata;
  2. il sistema calcola ISTANTANEAMENTE (forma chiusa, nessuna ricerca) i
     tre mescolamenti: al passo i la carta sta in una colonna nota c_i e
     serve un mescolamento M con M(c_i) = cifra ternaria del bersaglio;
  3. le istruzioni distinguono sempre MESCOLAMENTO (sigla funzionale,
     riga del tabellone) e IMPILAMENTO (gesto fisico, inversa);
  4. la visualizzazione mostra le 7 fotografie fisiche del mazzo
     (iniziale, colonne/raccolta per ciascuna fase);
  5. la pratica interattiva chiede colonna e impilamento, contando gli errori.

Convenzione: posizione 0 = carta al DORSO del mazzo tenuto a faccia in giù.
"""
import tkinter as tk
from tkinter import ttk

from ..core import gioco_reale as gr
from .i18n import tr

# ─── Costanti ─────────────────────────────────────────────────────────────────

_SIGLA_DESC = {
    code: f"simulator.shuffle_desc.{code}" for code in gr.SIGLE
}


def _column_name(index):
    return tr(("simulator.column.left", "simulator.column.center",
               "simulator.column.right")[index])


def _gesto(imp):
    """Descrizione del gesto fisico per la sigla di impilamento data."""
    names = {"S": _column_name(0), "C": _column_name(1),
             "D": _column_name(2)}
    return tr("simulator.gesture", first=names[imp[0]],
              second=names[imp[1]], third=names[imp[2]])

_C_NORMAL  = "#D6EDD6"
_C_TARGET  = "#FFD700"
_C_HIDDEN  = "#F0F0F0"


class SimulatorFrame(ttk.Frame):

    def __init__(self, parent, on_new_T=None, **kw):
        super().__init__(parent, **kw)
        self._on_new_T = on_new_T    # callback(list[int]) per app/gobbo
        self._plan   = None          # risultato di gr.risolvi_trucco
        self._phases = []

        # stato pratica
        self._pstate   = "idle"      # idle | col_q | order_q | done
        self._pstep    = 0
        self._p_errors = 0
        self._p_err_log = []
        self._p_deck   = None        # mazzo fisico corrente (lista 27)
        self._p_cols   = None        # colonne correnti (dopo distribuzione)
        self._p_card   = 0

        self._build_ui()

    # ─── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        hdr = ttk.Frame(self, padding=(10, 8, 10, 4))
        hdr.grid(row=0, column=0, sticky="ew")
        ttk.Label(hdr,
                  text=f"🎩  {tr('simulator.title')}",
                  font=("Segoe UI", 13, "bold"),
                  foreground="#1a3a5c").pack(side="left")

        ctrl = ttk.LabelFrame(
            self, text=f" {tr('simulator.settings')} ", padding=(10, 6))
        ctrl.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        ctrl.columnconfigure(7, weight=1)

        ttk.Label(ctrl, text=tr("simulator.chosen_card"),
                  font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        self._card_var = tk.IntVar(value=0)
        ttk.Spinbox(ctrl, from_=0, to=26, textvariable=self._card_var,
                    width=4).grid(row=0, column=1, padx=6)

        ttk.Label(ctrl, text=tr("simulator.final_position"),
                  font=("Segoe UI", 10)).grid(row=0, column=2, padx=(20, 4), sticky="w")
        self._target_var = tk.IntVar(value=13)
        ttk.Spinbox(ctrl, from_=0, to=26, textvariable=self._target_var,
                    width=4).grid(row=0, column=3, padx=6)

        self._go_btn = ttk.Button(
            ctrl, text=f"▶  {tr('simulator.calculate_sequence')}",
                                  command=self._find_sequence)
        self._go_btn.grid(row=0, column=4, padx=12)

        self._status_lbl = ttk.Label(ctrl, text="",
                                     font=("Segoe UI", 9, "italic"),
                                     foreground="#555")
        self._status_lbl.grid(row=0, column=5, sticky="w")

        nb = ttk.Notebook(self)
        nb.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))
        self._istr_tab     = ttk.Frame(nb)
        self._deck_tab     = ttk.Frame(nb)
        self._practice_tab = ttk.Frame(nb)
        nb.add(self._istr_tab,
               text=f"  📋 {tr('simulator.tab.instructions')}  ")
        nb.add(self._deck_tab, text=f"  🃏 {tr('simulator.tab.deck')}  ")
        nb.add(self._practice_tab,
               text=f"  🎯 {tr('simulator.tab.practice')}  ")

        self._build_istr_tab()
        self._build_deck_tab()
        self._build_practice_tab()

    def _build_istr_tab(self):
        fr = self._istr_tab
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(0, weight=1)
        txt = tk.Text(fr, font=("Segoe UI", 10), wrap="word",
                      padx=14, pady=10, state="disabled",
                      background="#FDFDF6", relief="flat")
        vsb = ttk.Scrollbar(fr, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=vsb.set)
        txt.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        for tag, cfg in {
            "title":  dict(font=("Segoe UI", 13, "bold"), foreground="#1a3a5c"),
            "step":   dict(font=("Segoe UI", 11, "bold"), foreground="#7b4000"),
            "action": dict(font=("Segoe UI", 10)),
            "pile":   dict(font=("Segoe UI", 11, "bold"), foreground="#006400"),
            "mesc":   dict(font=("Segoe UI", 10, "bold"), foreground="#00427e"),
            "note":   dict(font=("Segoe UI", 9, "italic"), foreground="#666"),
            "result": dict(font=("Segoe UI", 11, "bold"), foreground="#B8860B"),
        }.items():
            txt.tag_configure(tag, **cfg)
        self._istr_txt = txt
        self._write_placeholder_istr()

    def _build_deck_tab(self):
        fr = self._deck_tab
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(2, weight=1)

        bar = ttk.Frame(fr, padding=(10, 8))
        bar.grid(row=0, column=0, sticky="ew")
        ttk.Label(bar, text=tr("simulator.photo"),
                  font=("Segoe UI", 10, "bold")
                  ).pack(side="left")
        self._phase_var = tk.IntVar(value=0)
        self._phase_scale = ttk.Scale(bar, from_=0, to=6, orient="horizontal",
                                      variable=self._phase_var, length=280,
                                      command=self._on_phase_change)
        self._phase_scale.pack(side="left", padx=10)
        self._phase_lbl = ttk.Label(bar, text="—",
                                    font=("Segoe UI", 10, "bold"),
                                    foreground="#1a3a5c")
        self._phase_lbl.pack(side="left", padx=6)

        grid_fr = ttk.Frame(fr, padding=(10, 4))
        grid_fr.grid(row=1, column=0)
        self._deck_labels = []
        self._deck_col_hdrs = []
        for col in range(3):
            col_f = ttk.Frame(grid_fr)
            col_f.grid(row=0, column=col, padx=16)
            h = ttk.Label(col_f, text="", font=("Segoe UI", 9, "bold"),
                          foreground="#1a3a5c")
            h.grid(row=0, column=0, pady=(0, 3))
            self._deck_col_hdrs.append(h)
            labels = []
            for row in range(9):
                lbl = tk.Label(col_f, text="---",
                               font=("Courier New", 9, "bold"),
                               width=4, relief="solid", borderwidth=1,
                               bg=_C_HIDDEN, padx=2, pady=2)
                lbl.grid(row=row + 1, column=0, padx=1, pady=1)
                labels.append(lbl)
            self._deck_labels.append(labels)

        self._deck_log = tk.Text(fr, height=4, font=("Segoe UI", 9),
                                 state="disabled", wrap="word",
                                 background="#F8F8F8", relief="flat",
                                 padx=8, pady=4)
        self._deck_log.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 8))

    def _build_practice_tab(self):
        fr = self._practice_tab
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(3, weight=1)

        phdr = ttk.Frame(fr, padding=(10, 6, 10, 4))
        phdr.grid(row=0, column=0, sticky="ew")
        phdr.columnconfigure(1, weight=1)
        self._pstep_lbl = ttk.Label(
            phdr, text=tr("simulator.practice.first_calculate"),
            font=("Segoe UI", 11, "bold"), foreground="#1a3a5c")
        self._pstep_lbl.grid(row=0, column=0, sticky="w")

        err_row = ttk.Frame(phdr)
        err_row.grid(row=0, column=2, sticky="e")
        ttk.Label(err_row, text=tr("simulator.practice.errors"),
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self._p_err_count_lbl = ttk.Label(
            err_row, text="—", width=3,
            font=("Segoe UI", 12, "bold"), foreground="#cc0000")
        self._p_err_count_lbl.pack(side="left", padx=(4, 12))
        self._p_reset_btn = ttk.Button(
            err_row, text=f"↺  {tr('simulator.practice.restart')}",
            command=self._practice_reset, state="disabled")
        self._p_reset_btn.pack(side="left")

        deck_fr = ttk.LabelFrame(
            fr, text=f" {tr('simulator.practice.table_columns')} ",
            padding=(6, 4))
        deck_fr.grid(row=1, column=0, padx=10, pady=4, sticky="ew")
        self._p_deck_col_labels = []
        for col in range(3):
            col_f = ttk.Frame(deck_fr)
            col_f.grid(row=0, column=col, padx=14)
            nome = tr("simulator.deck.column_header",
                      column=_column_name(col), code="SCD"[col])
            ttk.Label(col_f, text=nome, font=("Segoe UI", 9, "bold"),
                      foreground="#1a3a5c").grid(row=0, column=0, pady=(0, 3))
            col_labels = []
            for row in range(9):
                lbl = tk.Label(col_f, text="---",
                               font=("Courier New", 9, "bold"),
                               width=4, relief="solid", borderwidth=1,
                               bg=_C_HIDDEN, padx=2, pady=2)
                lbl.grid(row=row + 1, column=0, padx=1, pady=1)
                col_labels.append(lbl)
            self._p_deck_col_labels.append(col_labels)

        self._p_action_fr = ttk.LabelFrame(
            fr, text=f" {tr('simulator.practice.action_required')} ",
                                           padding=(12, 8))
        self._p_action_fr.grid(row=2, column=0, padx=10, pady=4, sticky="ew")
        self._p_action_fr.columnconfigure(0, weight=1)

        self._p_question_lbl = ttk.Label(
            self._p_action_fr, text="",
            font=("Segoe UI", 10), wraplength=720, justify="left")
        self._p_question_lbl.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self._p_col_btn_frame = ttk.Frame(self._p_action_fr)
        self._p_col_btn_frame.grid(row=1, column=0, sticky="w")
        for i, nome in enumerate(_column_name(i) for i in range(3)):
            ttk.Button(self._p_col_btn_frame, text=f"   {nome}   ",
                       command=lambda c=i: self._practice_choose_col(c)
                       ).grid(row=0, column=i, padx=6)

        self._p_col_feedback = ttk.Label(self._p_action_fr, text="",
                                         font=("Segoe UI", 10))
        self._p_col_feedback.grid(row=2, column=0, sticky="w", pady=(6, 0))

        self._p_order_frame = ttk.Frame(self._p_action_fr)
        self._p_order_frame.grid(row=3, column=0, sticky="w", pady=(10, 0))
        ttk.Label(self._p_order_frame,
                  text=tr("simulator.practice.stacking"),
                  font=("Segoe UI", 10)).pack(side="left")
        self._p_order_var = tk.StringVar(value="SCD")
        order_cb = ttk.Combobox(
            self._p_order_frame, textvariable=self._p_order_var,
            values=list(gr.SIGLE), width=8, state="readonly")
        order_cb.pack(side="left", padx=8)
        self._p_order_desc_lbl = ttk.Label(
            self._p_order_frame, text=_gesto("SCD"),
            font=("Segoe UI", 9, "italic"), foreground="#555")
        self._p_order_desc_lbl.pack(side="left", padx=4)
        order_cb.bind("<<ComboboxSelected>>", self._p_on_order_select)

        self._p_confirm_btn = ttk.Button(
            self._p_action_fr,
            text=f"✔  {tr('simulator.practice.confirm_stacking')}",
            command=self._practice_confirm_order)
        self._p_confirm_btn.grid(row=4, column=0, sticky="w", pady=(10, 0))

        log_fr = ttk.Frame(fr)
        log_fr.grid(row=3, column=0, sticky="nsew", padx=10, pady=(4, 8))
        log_fr.columnconfigure(0, weight=1)
        log_fr.rowconfigure(0, weight=1)
        self._p_log = tk.Text(log_fr, font=("Segoe UI", 9), state="disabled",
                              wrap="word", height=8, background="#F8F8F8",
                              relief="flat", padx=8, pady=4)
        vsb = ttk.Scrollbar(log_fr, orient="vertical",
                            command=self._p_log.yview)
        self._p_log.configure(yscrollcommand=vsb.set)
        self._p_log.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        for tag, cfg in {
            "ok":    dict(foreground="#006400", font=("Segoe UI", 9, "bold")),
            "err":   dict(foreground="#cc0000", font=("Segoe UI", 9, "bold")),
            "info":  dict(foreground="#444444"),
            "title": dict(foreground="#1a3a5c", font=("Segoe UI", 10, "bold")),
            "sum":   dict(foreground="#006400", font=("Segoe UI", 10, "bold")),
        }.items():
            self._p_log.tag_configure(tag, **cfg)

        self._p_set_state("idle")

    # ─── Calcolo della sequenza (forma chiusa, istantaneo) ────────────────────

    def _find_sequence(self):
        try:
            card   = int(self._card_var.get())
            target = int(self._target_var.get())
            plan   = gr.risolvi_trucco(card, target)
        except (ValueError, tk.TclError):
            self._status_lbl.configure(
                text=f"✗  {tr('simulator.validation.positions')}")
            return
        self._plan = plan
        self._status_lbl.configure(
            text="✓  " + tr("simulator.status.sequence",
                            shuffles=" ".join(plan["mescolamenti"]),
                            number=plan["numero"]))
        self._build_istruzioni(plan)
        self._build_deck_phases(plan)
        self._init_practice(plan, card)
        if self._on_new_T is not None:
            try:
                self._on_new_T(list(plan["T"]))
            except Exception:
                pass

    # ─── Tab Istruzioni ────────────────────────────────────────────────────────

    def _build_istruzioni(self, plan):
        card   = int(self._card_var.get())
        target = int(self._target_var.get())
        txt = self._istr_txt
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        ins = lambda t, tag="action": txt.insert("end", t, tag)

        ins(f"✨  {tr('simulator.instructions.title')}\n\n", "title")
        ins(tr("simulator.instructions.positions", card=card, target=target)
            + "\n", "action")
        ins(tr("simulator.instructions.arrangement", number=plan["numero"],
               shuffles=" ".join(plan["mescolamenti"]),
               stackings=" ".join(plan["impilamenti"])) + "\n\n", "mesc")
        ins("─" * 70 + "\n\n", "note")

        ins(tr("simulator.instructions.preparation_title") + "\n", "step")
        ins(tr("simulator.instructions.preparation", card=card) + "\n\n",
            "action")

        for i, (mesc, imp, col) in enumerate(zip(plan["mescolamenti"],
                                                 plan["impilamenti"],
                                                 plan["colonne"]), start=1):
            nome_col = _column_name(col)
            ins("\n" + tr("simulator.instructions.phase_title", phase=i)
                + "\n", "step")
            ins(tr("simulator.instructions.deal") + "\n", "action")
            ins(tr("simulator.instructions.chosen_column",
                   column=nome_col) + "\n", "note")
            ins(tr("simulator.instructions.perform_shuffle", shuffle=mesc,
                   description=tr(_SIGLA_DESC[mesc])) + "\n", "action")
            ins(tr("simulator.instructions.gesture",
                   gesture=_gesto(imp)) + "\n", "pile")
            if mesc != imp:
                ins(tr("simulator.instructions.seldon_warning",
                       stacking=imp, shuffle=mesc) + "\n", "note")
            ins(tr("simulator.instructions.pick_up") + "\n", "action")

        ins("\n" + "─" * 70 + "\n\n", "note")
        ins(tr("simulator.instructions.result_title") + "\n", "step")
        ins(tr("simulator.instructions.result", target=target,
               number=target + 1) + "\n\n", "result")
        ins(tr("simulator.instructions.board_note", t0=plan["T"][0],
               t13=plan["T"][13], t26=plan["T"][26]) + "\n", "note")
        txt.configure(state="disabled")

    # ─── Tab Mazzo: 7 fotografie fisiche ──────────────────────────────────────

    def _build_deck_phases(self, plan):
        card = int(self._card_var.get())
        _, fasi = gr.esegui_partita(plan["mescolamenti"])
        phases = []
        for f in fasi:
            if f["tipo"] == "iniziale":
                phases.append(("deck", f["deck"],
                               tr("simulator.phase.initial_deck")))
            elif f["tipo"] == "colonne":
                phases.append(("cols", f["cols"], tr(
                    "simulator.phase.columns", phase=f["fase"])))
            else:
                key = ("simulator.phase.after_shuffle_reversed"
                       if f.get("rovesciato")
                       else "simulator.phase.after_shuffle")
                phases.append(("deck", f["deck"], tr(
                    key, phase=f["fase"], shuffle=f["sigla"],
                    stacking=f["impilamento"])))
        self._phases = phases
        self._target_card = card
        self._phase_scale.configure(to=len(phases) - 1)
        self._phase_var.set(0)
        self._render_phase(0)

    def _on_phase_change(self, val):
        try:
            self._render_phase(int(float(val)))
        except (ValueError, tk.TclError):
            pass

    def _render_phase(self, idx):
        if not self._phases or idx >= len(self._phases):
            return
        kind, data, label = self._phases[idx]
        card = self._target_card
        self._phase_lbl.configure(text=label)

        pos_txt = ""
        if kind == "deck":
            hdrs = tuple(tr("simulator.deck.position_header", start=start,
                            end=start + 8) for start in (0, 9, 18))
            for col in range(3):
                self._deck_col_hdrs[col].configure(text=hdrs[col])
                for row in range(9):
                    val = data[col * 9 + row]
                    self._deck_labels[col][row].configure(
                        text=f"C{val:02d}",
                        bg=_C_TARGET if val == card else _C_NORMAL)
            p = data.index(card)
            pos_txt = tr("simulator.deck.card_position", card=card,
                         position=p, reading_column=p // 9 + 1)
        else:
            hdrs = tuple(tr("simulator.deck.column_header",
                            column=_column_name(col), code="SCD"[col])
                         for col in range(3))
            for col in range(3):
                self._deck_col_hdrs[col].configure(text=hdrs[col])
                for row in range(9):
                    val = data[col][row]
                    self._deck_labels[col][row].configure(
                        text=f"C{val:02d}",
                        bg=_C_TARGET if val == card else _C_NORMAL)
            for g in range(3):
                if card in data[g]:
                    pos_txt = tr(
                        "simulator.deck.card_column", card=card,
                        column=_column_name(g), number=data[g].index(card) + 1)
        log = self._deck_log
        log.configure(state="normal")
        log.delete("1.0", "end")
        log.insert("end", f"{label}\n{pos_txt}\n")
        log.configure(state="disabled")

    # ─── Pratica interattiva ──────────────────────────────────────────────────

    def _p_on_order_select(self, _event=None):
        self._p_order_desc_lbl.configure(
            text=_gesto(self._p_order_var.get()))

    def _p_set_state(self, state):
        self._pstate = state
        (self._p_col_btn_frame.grid if state == "col_q"
         else self._p_col_btn_frame.grid_remove)()
        (self._p_col_feedback.grid if state in ("order_q", "done")
         else self._p_col_feedback.grid_remove)()
        if state == "order_q":
            self._p_order_frame.grid()
            self._p_confirm_btn.grid()
        else:
            self._p_order_frame.grid_remove()
            self._p_confirm_btn.grid_remove()

        if state == "idle":
            self._p_question_lbl.configure(
                text=tr("simulator.practice.first_calculate"))
        elif state == "col_q":
            self._p_question_lbl.configure(text=tr(
                "simulator.practice.question_column", phase=self._pstep,
                card=self._p_card))
        elif state == "order_q":
            mesc = self._plan["mescolamenti"][self._pstep - 1]
            self._p_question_lbl.configure(text=tr(
                "simulator.practice.question_stacking", phase=self._pstep,
                shuffle=mesc))
        elif state == "done":
            self._p_question_lbl.configure(
                text=f"✅  {tr('simulator.practice.completed_log')}")

    def _init_practice(self, plan, card):
        self._p_card    = card
        self._p_errors  = 0
        self._p_err_log = []
        self._pstep     = 1
        self._p_deck    = list(range(27))
        self._p_cols    = gr.distribuisci(self._p_deck)

        self._p_err_count_lbl.configure(text="0")
        self._p_reset_btn.configure(state="normal")
        self._pstep_lbl.configure(text=tr(
            "simulator.practice.step_target", phase=1, card=card))

        self._p_log.configure(state="normal")
        self._p_log.delete("1.0", "end")
        self._p_log.insert(
            "end", f"━━━ {tr('simulator.practice.new_session')} ━━━\n", "title")
        self._p_log.insert(
            "end",
            tr("simulator.practice.session_data", card=card,
               shuffles=" ".join(plan["mescolamenti"]),
               stackings=" ".join(plan["impilamenti"])) + "\n\n", "info")
        self._p_log.configure(state="disabled")

        self._p_set_state("col_q")
        self._p_render_cols(show_target=False)

    def _practice_reset(self):
        if self._plan is not None:
            self._init_practice(self._plan, int(self._card_var.get()))

    def reset(self):
        """Riporta il simulatore allo stato iniziale (per «Reset tutto»)."""
        self._plan   = None
        self._pstate = "idle"
        self._card_var.set(0)
        self._target_var.set(13)
        self._status_lbl.configure(text="")
        for w in ("_istr_txt", "_deck_log", "_p_log"):
            box = getattr(self, w, None)
            if box is not None:
                box.configure(state="normal")
                box.delete("1.0", "end")
                box.configure(state="disabled")
        self._write_placeholder_istr()
        self._phases = []
        try:
            self._phase_var.set(0)
            self._phase_lbl.configure(text="—")
        except tk.TclError:
            pass
        self._p_set_state("idle")

    def _p_render_cols(self, show_target=True):
        if self._p_cols is None:
            return
        card = self._p_card
        for g in range(3):
            for row in range(9):
                val = self._p_cols[g][row]
                lbl = self._p_deck_col_labels[g][row]
                if val == card and not show_target:
                    lbl.configure(text="C??", bg=_C_HIDDEN)
                else:
                    lbl.configure(text=f"C{val:02d}",
                                  bg=_C_TARGET if val == card else _C_NORMAL)

    def _practice_choose_col(self, col):
        if self._pstate != "col_q":
            return
        card = self._p_card
        actual_col = next(g for g in range(3) if card in self._p_cols[g])
        self._p_render_cols(show_target=True)
        nomi = tuple(_column_name(i) for i in range(3))
        if col == actual_col:
            fb, fg = ("✓ " + tr("simulator.practice.correct_column",
                                  card=card, column=nomi[actual_col]),
                      "#006400")
            self._p_log_append(
                tr("simulator.practice.column_ok_log", phase=self._pstep,
                   column=nomi[col]) + "\n", "ok")
        else:
            fb, fg = ("✗ " + tr("simulator.practice.wrong_column",
                                  chosen=nomi[col],
                                  correct=nomi[actual_col]), "#cc0000")
            self._p_errors += 1
            self._p_err_log.append(tr(
                "simulator.practice.column_error_detail", phase=self._pstep,
                chosen=nomi[col], correct=nomi[actual_col]))
            self._p_log_append(
                tr("simulator.practice.column_error_log", phase=self._pstep,
                   chosen=nomi[col], correct=nomi[actual_col]) + "\n", "err")
            self._p_err_count_lbl.configure(text=str(self._p_errors))
        self._p_set_state("order_q")
        self._p_col_feedback.configure(text=fb, foreground=fg)
        self._p_col_feedback.grid()

    def _practice_confirm_order(self):
        if self._pstate != "order_q":
            return
        chosen  = self._p_order_var.get()
        mesc    = self._plan["mescolamenti"][self._pstep - 1]
        correct = self._plan["impilamenti"][self._pstep - 1]

        if chosen == correct:
            self._p_log_append(
                tr("simulator.practice.stacking_ok_log", phase=self._pstep,
                   chosen=chosen, gesture=_gesto(chosen)) + "\n", "ok")
        else:
            self._p_errors += 1
            is_seldon = chosen == mesc and mesc != correct
            detail_key = ("simulator.practice.stacking_error_seldon_detail"
                          if is_seldon
                          else "simulator.practice.stacking_error_detail")
            log_key = ("simulator.practice.stacking_error_seldon_log"
                       if is_seldon
                       else "simulator.practice.stacking_error_log")
            self._p_err_log.append(tr(
                detail_key, phase=self._pstep, chosen=chosen, correct=correct))
            self._p_log_append(tr(
                log_key, phase=self._pstep, chosen=chosen,
                correct=correct) + "\n", "err")
            self._p_err_count_lbl.configure(text=str(self._p_errors))

        # applica SEMPRE il mescolamento corretto al mazzo fisico
        self._p_deck = gr.raccogli(self._p_cols, mesc)

        if self._pstep < 3:
            self._pstep += 1
            self._p_cols = gr.distribuisci(self._p_deck)
            self._pstep_lbl.configure(text=tr(
                "simulator.practice.step_target", phase=self._pstep,
                card=self._p_card))
            self._p_set_state("col_q")
            self._p_render_cols(show_target=False)
        else:
            self._p_cols = gr.distribuisci(self._p_deck)  # per il rendering
            self._pstep_lbl.configure(
                text=f"✅  {tr('simulator.practice.completed')}")
            self._p_set_state("done")
            self._p_render_cols(show_target=True)
            self._show_practice_summary()

    def _show_practice_summary(self):
        card      = self._p_card
        target    = int(self._target_var.get())
        final_pos = self._p_deck.index(card)
        success   = final_pos == target
        max_err   = 6
        score     = max(0, round(100 * (max_err - self._p_errors) / max_err))
        grade_key = ("simulator.summary.grade.perfect"
                     if self._p_errors == 0 else
                     "simulator.summary.grade.very_good"
                     if self._p_errors <= 2 else
                     "simulator.summary.grade.fair"
                     if self._p_errors <= 4 else
                     "simulator.summary.grade.review")
        grade = tr(grade_key)
        error_key = ("simulator.summary.errors.one" if self._p_errors == 1
                     else "simulator.summary.errors.many")

        lines = [
            ("═" * 50 + "\n", "title"),
            (f"  {tr('simulator.summary.title')}\n", "title"),
            ("═" * 50 + "\n\n", "title"),
            (f"  {tr('simulator.summary.target_card', card=card)}\n", "info"),
            (f"  {tr('simulator.summary.final_success', position=final_pos) if success else tr('simulator.summary.final_failure', position=final_pos, target=target)}\n",
             "ok" if success else "err"),
            (f"\n  {tr(error_key, count=self._p_errors, maximum=max_err)}\n", "info"),
            (f"  {tr('simulator.summary.score', score=score, grade=grade)}\n\n", "sum"),
        ]
        if self._p_err_log:
            lines.append((f"  {tr('simulator.summary.error_details')}\n", "err"))
            lines += [(f"    • {e}\n", "info") for e in self._p_err_log]
        else:
            lines.append((f"  {tr('simulator.summary.no_errors')}\n", "ok"))
        lines.append(("\n" + "═" * 50 + "\n", "title"))

        self._p_log.configure(state="normal")
        for text, tag in lines:
            self._p_log.insert("end", text, tag)
        self._p_log.see("end")
        self._p_log.configure(state="disabled")

    def _p_log_append(self, text, tag="info"):
        self._p_log.configure(state="normal")
        self._p_log.insert("end", text, tag)
        self._p_log.see("end")
        self._p_log.configure(state="disabled")

    # ─── Helper ───────────────────────────────────────────────────────────────

    def _write_placeholder_istr(self):
        txt = self._istr_txt
        txt.configure(state="normal")
        txt.insert("end", tr("simulator.instructions.placeholder"), "note")
        txt.configure(state="disabled")

    # compatibilità col vecchio nome usato in reset()
    _decomp = None
