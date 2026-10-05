"""Pratica con conseguenze reali (compartimento I3, D-I3-4/5/6).

Mixin del `SimulatorFrame`: aggiunge alla Pratica una modalità opt-in in cui
il gesto eseguito viene applicato davvero al mazzo. La modalità storica
(«Valutazione») resta il default e resta nel suo percorso, intatta.

Tutta la fisica sta in `services.errori` (ordine degli eventi, E1–E5, confronto,
recupero, ritorno): qui si leggono i dati e si compongono le frasi del catalogo.
"""
import tkinter as tk
from tkinter import ttk

from ..core import gioco_reale as gr
from ..services import errori as er
from .i18n import tr
from .dialoghi_stato import _scegli

__all__ = ["PraticaRealeMixin", "MODO_VALUTAZIONE", "MODO_CONSEGUENZE"]

MODO_VALUTAZIONE = "valutazione"
MODO_CONSEGUENZE = "conseguenze"
_NOMI_CIFRE = {2: "n2", 1: "n1", 0: "n0"}


def _terna(posizione):
    return "({},{},{})".format(*gr.digits3(posizione))


class PraticaRealeMixin:
    """Richiede gli attributi della Pratica di `SimulatorFrame`."""

    # ── costruzione ──────────────────────────────────────────────────────────
    def _costruisci_pratica_reale(self, fr, phdr):
        modi = ttk.Frame(phdr)
        modi.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))
        ttk.Label(modi, text=tr("practice.real.mode.label")).pack(side="left")
        self._p_modo_var = tk.StringVar(value=MODO_VALUTAZIONE)
        self._p_modo_attivo = MODO_VALUTAZIONE
        self._p_modo_valutazione = ttk.Radiobutton(
            modi, text=tr("practice.real.mode.evaluation"),
            variable=self._p_modo_var, value=MODO_VALUTAZIONE,
            command=self._su_modo)
        self._p_modo_conseguenze = ttk.Radiobutton(
            modi, text=tr("practice.real.mode.consequences"),
            variable=self._p_modo_var, value=MODO_CONSEGUENZE,
            command=self._su_modo)
        self._p_modo_valutazione.pack(side="left", padx=(6, 0))
        self._p_modo_conseguenze.pack(side="left", padx=(6, 0))
        self._p_piano_lbl = ttk.Label(phdr, text="", wraplength=1050)
        self._p_piano_lbl.grid(row=2, column=0, columnspan=3, sticky="w")

        # errore fisico della fase corrente (E2/E3), solo in conseguenze reali
        self._p_fisico_var = tk.StringVar(value="nessuno")
        self._p_fisico_fr = ttk.Frame(self._p_action_fr)
        self._p_fisico_fr.grid(row=4, column=0, sticky="w", pady=(8, 0))
        ttk.Label(self._p_fisico_fr,
                  text=tr("practice.real.physical")).pack(anchor="w")
        self._p_fisico_radios = []
        for valore, chiave in (("nessuno", "practice.real.physical.none"),
                               ("E2", "practice.real.physical.E2"),
                               ("E3", "practice.real.physical.E3")):
            rb = ttk.Radiobutton(self._p_fisico_fr, text=tr(chiave),
                                 variable=self._p_fisico_var, value=valore)
            rb.pack(side="left", padx=(6, 0))
            self._p_fisico_radios.append(rb)
        # ordine di Tab = ordine visivo: impilamento → errore fisico → conferma
        self._p_fisico_fr.lower(self._p_confirm_btn)
        self._p_fisico_fr.grid_remove()

        # confronto previsto/eseguito e recupero
        self._p_reale_fr = ttk.LabelFrame(
            fr, text=f" {tr('practice.real.frame')} ", padding=(8, 4))
        self._p_reale_fr.grid(row=2, column=0, padx=10, pady=(0, 8), sticky="new")
        self._p_reale_fr.columnconfigure(0, weight=1)
        self._p_confronto_txt = tk.Text(
            self._p_reale_fr, height=4, width=48, wrap="word", relief="flat",
            font=("Consolas", 9), background="#FAFCFF", takefocus=True)
        self._p_confronto_txt.grid(row=0, column=0, columnspan=3, sticky="ew")
        self._p_confronto_txt.configure(state="disabled")
        sb = ttk.Scrollbar(self._p_reale_fr, command=self._p_confronto_txt.yview)
        sb.grid(row=0, column=3, sticky="ns")
        self._p_confronto_txt.configure(yscrollcommand=sb.set)
        self._p_recovery_fr = ttk.Frame(self._p_action_fr)
        self._p_recovery_fr.grid(row=8, column=0, sticky="ew", pady=3)
        self._p_recupero_lbl = ttk.Label(self._p_recovery_fr, text="",
                                         wraplength=400, justify="left")
        self._p_recupero_lbl.grid(row=1, column=0, columnspan=3, sticky="w",
                                  pady=(4, 2))
        self._p_recupero_var = tk.StringVar()
        self._p_recupero_cb = ttk.Combobox(self._p_recovery_fr,
                                           textvariable=self._p_recupero_var,
                                           state="disabled", width=32)
        self._p_recupero_cb.grid(row=2, column=0, sticky="w")
        self._p_recupero_btn = ttk.Button(
            self._p_recovery_fr, text=tr("practice.real.recovery.apply"),
            command=self._reale_applica_recupero, state="disabled")
        self._p_recupero_btn.grid(row=2, column=1, sticky="w", padx=6)
        self._p_reale_fr.grid_remove()
        self._p_recovery_fr.grid_remove()
        self._p_stato = None
        self._p_prevista = None
        self._p_esito = None
        self._p_opzioni_recupero = ()
        self._p_col_indicata = None

    # ── modalità ─────────────────────────────────────────────────────────────
    def _modo_reale(self):
        return self._p_modo_var.get() == MODO_CONSEGUENZE

    def _su_modo(self):
        """Cambiare modalità ricomincia la stessa sessione (stessi input)."""
        if self._p_modo_var.get() == self._p_modo_attivo:
            return
        advanced = self._sessione is not None and (self._pstep > 1 or self._pstate == "order_q")
        if advanced and _scegli(self, tr("ux3.mode.title"), tr("ux3.mode.restart"),
                               ((True, "ux3.mode.change"), (False, "button.cancel"))) is not True:
            self._p_modo_var.set(self._p_modo_attivo)
            return
        self._p_modo_attivo = self._p_modo_var.get()
        if self._modo_reale():
            self._p_reale_fr.grid()
        else:
            self._p_reale_fr.grid_remove()
            self._p_recovery_fr.grid_remove()
        if self._sessione is not None:
            self._init_practice(self._sessione)
        # J: la sessione registra il nuovo stato scientifico (se collegata)
        avvisa = getattr(self, "on_stato", None)
        if avvisa is not None:
            avvisa()

    def _p_impilamento_atteso(self):
        """L'impilamento corretto per la fase corrente (in entrambe le modalità)."""
        if not self._modo_reale():
            return self._sessione.piano["impilamenti"][self._pstep - 1]
        inteso = er.mescolamento_inteso(self._p_stato, self._p_col_indicata)
        return gr.IMPILAMENTO_DI[inteso]

    # ── percorso «conseguenze reali» ─────────────────────────────────────────
    def _reale_init(self, sessione):
        piano = sessione.piano
        self._p_sessione_errori = er.SessioneErrori(
            sessione.carta, sessione.bersaglio, tuple(piano["mescolamenti"]),
            guidata_dal_bersaglio=not piano.get("disposizione_fissata", False))
        self._p_stato = er.avvia(self._p_sessione_errori)
        self._p_prevista = er.traccia_prevista(self._p_sessione_errori)
        self._p_esito = None
        self._p_col_indicata = None
        self._p_opzioni_recupero = ()
        self._p_cols = [list(c) for c in self._p_stato.colonne()]
        self._scrivi_confronto("")
        self._aggiorna_recupero()

    def _reale_choose_col(self, col):
        reale = er.colonna_reale(self._p_stato)
        self._p_col_indicata = col
        self._p_render_cols(show_target=True)
        nomi = self._nomi_colonne()
        if col == reale:
            fb, fg = ("✓ " + tr("simulator.practice.correct_column",
                                card=self._p_card, column=nomi[reale]), "#006400")
        else:
            fb, fg = ("✗ " + tr("practice.real.column_used", chosen=nomi[col],
                                correct=nomi[reale]), "#cc0000")
        self._p_set_state("order_q")
        self._p_col_feedback.configure(text=fb, foreground=fg)
        self._p_col_feedback.grid()
        self._p_order_var.set(self._p_impilamento_atteso())
        self._p_on_order_select()

    def _reale_domanda_impilamento(self):
        inteso = er.mescolamento_inteso(self._p_stato, self._p_col_indicata)
        return tr("practice.real.intended", phase=self._pstep, shuffle=inteso,
                  stacking=gr.IMPILAMENTO_DI[inteso])

    def _reale_confirm(self):
        fisico = self._p_fisico_var.get()
        gesti = er.GestiFase(colonna_indicata=self._p_col_indicata,
                             impilamento=self._p_order_var.get(),
                             ordine_interno_invertito=fisico == "E3",
                             rovesciamento_dopo=fisico == "E2")
        self._p_stato = er.esegui_fase(self._p_stato, gesti)
        passo = self._p_stato.passi[-1]
        self._p_deck = list(self._p_stato.mazzo)
        for evento in passo.eventi:
            self._p_errors += 1
            testo = tr(f"practice.real.event.{evento.tipo.value}", phase=evento.fase)
            self._p_err_log.append(testo)
            self._p_log_append(testo + "\n", "err")
        if not passo.eventi:
            self._p_log_append(tr("simulator.practice.stacking_ok_log",
                                  phase=passo.fase,
                                  chosen=passo.impilamento_eseguito,
                                  gesture=passo.impilamento_eseguito) + "\n", "ok")
        self._p_err_count_lbl.configure(text=str(self._p_errors))
        self._scrivi_confronto(self._confronto_fase(passo))
        self._p_fisico_var.set("nessuno")
        self._p_col_indicata = None
        self._aggiorna_recupero()
        if not self._p_stato.completata:
            self._pstep += 1
            self._p_cols = [list(c) for c in self._p_stato.colonne()]
            self._pstep_lbl.configure(text=tr(
                "simulator.practice.step_target", phase=self._pstep,
                card=self._p_card))
            self._p_set_state("col_q")
            self._p_render_cols(show_target=False)
        else:
            self._p_cols = [list(c) for c in self._p_stato.colonne()]
            self._pstep_lbl.configure(
                text=f"✅  {tr('simulator.practice.completed')}")
            self._p_set_state("done")
            self._p_render_cols(show_target=True)
            self._reale_summary()

    # ── confronto per fase ───────────────────────────────────────────────────
    def _nomi_colonne(self):
        # stesse chiavi di `simulator_tab._column_name`, senza importarlo:
        # il mixin non deve dipendere dal modulo che lo usa (niente cicli)
        return tuple(tr(k) for k in ("simulator.column.left",
                                     "simulator.column.center",
                                     "simulator.column.right"))

    def _confronto_fase(self, passo):
        previsto = self._p_prevista.passi[passo.fase - 1]
        nomi = self._nomi_colonne()

        def riga(chiave, a, b):
            segno = "=" if a == b else "≠"
            return f"{segno} " + tr(chiave, planned=a, executed=b)

        righe = [tr("practice.real.compare.heading", phase=passo.fase),
                 riga("practice.real.compare.column",
                      nomi[previsto.colonna_reale], nomi[passo.colonna_indicata]),
                 riga("practice.real.compare.shuffle",
                      previsto.mescolamento_eseguito, passo.mescolamento_eseguito),
                 riga("practice.real.compare.stacking",
                      previsto.impilamento_eseguito, passo.impilamento_eseguito),
                 riga("practice.real.compare.position",
                      previsto.posizione_dopo, passo.posizione_dopo),
                 riga("practice.real.compare.digits",
                      _terna(previsto.posizione_dopo), _terna(passo.posizione_dopo))]
        cambiate = er.cifre_cambiate(previsto.posizione_dopo, passo.posizione_dopo)
        if cambiate:
            righe.append("≠ " + tr("practice.real.compare.digits_changed",
                                   digits=", ".join(_NOMI_CIFRE[c] for c in cambiate)))
        righe += [tr(f"practice.real.event.{e.tipo.value}", phase=e.fase)
                  for e in passo.eventi]
        if not passo.eventi and not cambiate:
            righe.append(tr("practice.real.compare.no_change"))
        return "\n".join(righe)

    def _scrivi_confronto(self, testo):
        self._p_confronto_txt.configure(state="normal")
        self._p_confronto_txt.delete("1.0", "end")
        self._p_confronto_txt.insert("1.0", testo)
        self._p_confronto_txt.configure(state="disabled")

    # ── recupero delle fasi residue ──────────────────────────────────────────
    def _aggiorna_recupero(self):
        stato = self._p_stato
        con_errori = stato is not None and any(p.eventi for p in stato.passi)
        (self._p_recovery_fr.grid if con_errori and not stato.completata
         else self._p_recovery_fr.grid_remove)()
        if stato is None or stato.completata or not stato.passi or not con_errori:
            self._p_opzioni_recupero = ()
            self._p_recupero_lbl.configure(text="")
            self._p_recupero_cb.configure(values=(), state="disabled")
            self._p_recupero_var.set("")
            self._p_recupero_btn.state(["disabled"])
            return
        self._p_opzioni_recupero = er.recuperi(stato)
        if not self._p_opzioni_recupero:
            self._p_recupero_lbl.configure(text=tr("practice.real.recovery.none"))
            self._p_recupero_cb.configure(values=(), state="disabled")
            self._p_recupero_var.set("")
            self._p_recupero_btn.state(["disabled"])
            return
        self._p_recupero_lbl.configure(text=tr(
            "practice.real.recovery.count", count=len(self._p_opzioni_recupero)))
        valori = [tr("practice.real.recovery.option",
                     shuffles=" ".join(o.suffisso), changes=o.modifiche,
                     non_scd=o.raccolte_non_scd)
                  for o in self._p_opzioni_recupero]
        self._p_recupero_cb.configure(values=valori, state="readonly")
        self._p_recupero_cb.current(0)
        self._p_recupero_btn.state(["!disabled"])

    def _reale_applica_recupero(self):
        if not self._p_opzioni_recupero:
            return
        indice = max(0, self._p_recupero_cb.current())
        opzione = self._p_opzioni_recupero[indice]
        self._p_stato = er.applica_recupero(self._p_stato, opzione)
        self._p_piano_lbl.configure(text=tr("ux3.plan.active",
            initial=" ".join(self._sessione.piano["mescolamenti"]),
            active=" ".join(opzione.suffisso)))
        self._status_lbl.configure(text=self._p_piano_lbl.cget("text"))
        self._p_log_append(tr("practice.real.recovery.applied",
                              phase=opzione.dopo_fase,
                              shuffles=" ".join(opzione.suffisso)) + "\n", "info")
        self._p_opzioni_recupero = ()
        self._p_recupero_cb.configure(values=(), state="disabled")
        self._p_recupero_btn.state(["disabled"])

    # ── riepilogo ────────────────────────────────────────────────────────────
    def _reale_summary(self):
        traccia = er.traccia(self._p_stato)
        esito = er.confronta(traccia)
        self._p_esito = esito
        ritorno = er.ritorno_eseguito(traccia)
        righe = [("═" * 50 + "\n", "title"),
                 (f"  {tr('practice.real.summary.title')}\n", "title"),
                 ("═" * 50 + "\n\n", "title"),
                 (f"  {tr('practice.real.summary.card_target', card=esito.carta, target=esito.bersaglio)}\n", "info")]
        if esito.bersaglio_raggiunto:
            righe.append((f"  {tr('practice.real.summary.target_reached', position=esito.posizione_eseguita)}\n", "ok"))
            chiave = ("practice.real.summary.full_success"
                      if esito.stessa_trasformazione
                      else "practice.real.summary.target_but_other_T")
            righe.append((f"  {tr(chiave)}\n",
                          "ok" if esito.stessa_trasformazione else "err"))
        else:
            righe.append((f"  {tr('practice.real.summary.target_missed', position=esito.posizione_eseguita, target=esito.bersaglio)}\n", "err"))
        righe += [
            (f"  {tr('practice.real.summary.T_planned', values=', '.join(map(str, esito.T_prevista)))}\n", "info"),
            (f"  {tr('practice.real.summary.T_executed', values=', '.join(map(str, esito.T_eseguita)))}\n", "info"),
            (f"  {tr('practice.real.summary.same_T.yes' if esito.stessa_trasformazione else 'practice.real.summary.same_T.no')}\n", "info"),
            (f"  {tr('practice.real.summary.same_card.yes' if esito.stesso_effetto_carta else 'practice.real.summary.same_card.no')}\n", "info")]
        if esito.numero_eseguito is None:
            righe.append((f"  {tr('practice.real.summary.row_outside', planned=esito.numero_previsto)}\n", "info"))
        else:
            righe.append((f"  {tr('practice.real.summary.rows', planned=esito.numero_previsto, executed=esito.numero_eseguito)}\n", "info"))
        if esito.eventi:
            elenco = "; ".join(tr(f"practice.real.event.{e.tipo.value}", phase=e.fase)
                               for e in esito.eventi)
            righe.append((f"  {tr('practice.real.summary.events', events=elenco)}\n", "err"))
        else:
            righe.append((f"  {tr('practice.real.summary.no_events')}\n", "ok"))
        cambiate = ", ".join(_NOMI_CIFRE[c] for c in esito.cifre_cambiate) \
            or tr("practice.real.summary.none")
        righe.append((f"  {tr('practice.real.summary.digits', planned=_terna(esito.posizione_prevista), executed=_terna(esito.posizione_eseguita), changed=cambiate)}\n", "info"))
        if esito.piano_modificato:
            righe.append((f"  {tr('practice.real.summary.plan_changed')}\n", "info"))
        if ritorno.disponibile:
            if not esito.stessa_trasformazione:
                righe.append((f"  {tr('practice.real.summary.realizable', number=esito.numero_eseguito)}\n", "info"))
            righe.append((f"  {tr('practice.real.summary.return', number=ritorno.numero_eseguito, back=ritorno.numero_ritorno, shuffles=' '.join(ritorno.procedura.mescolamenti))}\n", "info"))
        else:
            righe.append((f"  {tr('practice.real.summary.no_return')}\n", "info"))
        righe.append(("\n" + "═" * 50 + "\n", "title"))
        self._p_log.configure(state="normal")
        for testo, tag in righe:
            self._p_log.insert("end", testo, tag)
        self._p_log.see("end")
        self._p_log.configure(state="disabled")
