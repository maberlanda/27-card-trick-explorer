"""Compartimento I3d/I3e — Pratica con conseguenze reali e piano fissato.

* D-I3-4: la Pratica storica resta il default e non cambia; la modalità
  «conseguenze reali» è opt-in e applica davvero il gesto (E1–E5).
* D-I3-5/6: confronto previsto/eseguito per fase, riepilogo con T prevista e
  T eseguita, recupero delle fasi residue e ritorno con T_eseguita⁻¹.
* D-I3-7: dalla Tavola, piano fissato (una disposizione): carta variabile,
  bersaglio = T[carta], nessuna chiamata a `risolvi_trucco`.

SimulatorFrame vero sotto un display; i test si saltano senza.
"""
import tkinter as tk

import pytest

from gioco27 import i18n as catalogo
from gioco27.core import gioco_reale as gr


@pytest.fixture
def lingua():
    precedente = catalogo.get_language()
    yield catalogo.set_language
    catalogo.set_language(precedente)


@pytest.fixture
def sim(lingua):
    lingua("it")
    from gioco27.gui.simulator_tab import SimulatorFrame
    try:
        radice = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    radice.geometry("1366x768")
    frame = SimulatorFrame(radice)
    frame.pack(fill="both", expand=True)
    radice.update()
    try:
        yield frame
    finally:
        radice.destroy()


def _calcola(sim, carta, bersaglio, modo="valutazione"):
    sim._card_var.set(carta)
    sim._target_var.set(bersaglio)
    sim._find_sequence()
    sim._p_modo_var.set(modo)
    sim._su_modo()
    sim.update()


def _colonna_reale(sim):
    carta = sim._sessione.carta
    return next(g for g in range(3) if carta in sim._p_cols[g])


def _fase(sim, colonna=None, impilamento=None, fisico="nessuno"):
    sim._practice_choose_col(_colonna_reale(sim) if colonna is None else colonna)
    if impilamento is None:
        impilamento = sim._p_impilamento_atteso()
    sim._p_order_var.set(impilamento)
    sim._p_fisico_var.set(fisico)
    sim._practice_confirm_order()
    sim.update()


def _log(sim):
    return sim._p_log.get("1.0", "end")


# ═══════════════════════ la Pratica storica resta tale ══════════════════════

def test_la_modalita_predefinita_e_quella_storica(sim):
    sim._card_var.set(0)
    sim._target_var.set(20)
    sim._find_sequence()
    assert sim._p_modo_var.get() == "valutazione"
    _fase(sim, impilamento="DSC")               # E1: contato ma non applicato
    _fase(sim)
    _fase(sim)
    assert sim._p_deck.index(0) == 20
    assert sim._p_errors == 1
    assert not sim._p_reale_fr.grid_info()


def test_la_logica_storica_e_ancora_nel_percorso_storico():
    import pathlib
    sorgente = (pathlib.Path(__file__).resolve().parents[1] / "gioco27" / "gui"
                / "simulator_tab.py").read_text(encoding="utf-8")
    assert "# applica SEMPRE il mescolamento corretto al mazzo fisico" in sorgente


# ═══════════════════════ conseguenze reali (opt-in) ═════════════════════════

def test_e1_accade_davvero(sim):
    _calcola(sim, 0, 20, "conseguenze")
    assert sim._p_reale_fr.grid_info()
    _fase(sim, impilamento="DSC")
    _fase(sim)
    _fase(sim)
    esito = sim._p_esito
    assert esito.posizione_eseguita == 19 and esito.numero_eseguito == 112
    assert not esito.bersaglio_raggiunto
    testo = _log(sim)
    assert catalogo.tr("practice.real.event.E1", phase=1) in testo
    assert catalogo.tr("practice.real.summary.target_missed", position=19,
                       target=20) in testo


def test_e4_la_colonna_indicata_viene_usata(sim):
    _calcola(sim, 0, 13, "conseguenze")
    sim._practice_choose_col(1)                 # la carta e' in S (0)
    assert sim._p_impilamento_atteso() == "SCD"
    assert catalogo.tr("practice.real.intended", phase=1, shuffle="SCD",
                       stacking="SCD") in sim._p_question_lbl.cget("text")
    sim._p_order_var.set("SCD")
    sim._p_fisico_var.set("nessuno")
    sim._practice_confirm_order()
    _fase(sim)
    _fase(sim)
    assert sim._p_esito.posizione_eseguita == 12
    assert [e.tipo.value for e in sim._p_esito.eventi] == ["E4"]


def test_e2_finale_carta_al_bersaglio_ma_trasformazione_diversa(sim):
    _calcola(sim, 0, 13, "conseguenze")
    _fase(sim)
    _fase(sim)
    _fase(sim, fisico="E2")
    esito = sim._p_esito
    assert esito.bersaglio_raggiunto and not esito.stessa_trasformazione
    testo = _log(sim)
    assert catalogo.tr("practice.real.summary.target_but_other_T") in testo
    assert catalogo.tr("practice.real.summary.full_success") not in testo
    assert catalogo.tr("practice.real.summary.rows", planned=86,
                       executed=172) in testo


def test_e3_e_il_confronto_per_fase(sim):
    _calcola(sim, 0, 13, "conseguenze")
    _fase(sim, fisico="E3")
    confronto = sim._p_confronto_txt.get("1.0", "end")
    assert catalogo.tr("practice.real.compare.heading", phase=1) in confronto
    assert catalogo.tr("practice.real.event.E3", phase=1) in confronto
    assert sim._p_confronto_txt.cget("takefocus")
    assert sim._p_confronto_txt.cget("state") == "disabled"


def test_cifre_diverse_segnate_non_solo_col_colore(sim):
    _calcola(sim, 0, 20, "conseguenze")
    _fase(sim, impilamento="DSC")               # la fase 1 scrive n0 sbagliata
    confronto = sim._p_confronto_txt.get("1.0", "end")
    assert "≠" in confronto
    # la cifra appena scritta entra in alto: nella posizione intermedia e' n2
    assert catalogo.tr("practice.real.compare.digits_changed", digits="n2") in confronto


def test_recupero_dopo_e3_alla_fase_1(sim):
    _calcola(sim, 0, 13, "conseguenze")
    _fase(sim, fisico="E3")
    opzioni = sim._p_opzioni_recupero
    assert opzioni
    assert sim._p_recupero_lbl.cget("text") == catalogo.tr(
        "practice.real.recovery.count", count=len(opzioni))
    assert sim._p_recupero_btn.instate(["!disabled"])
    sim._p_recupero_cb.current(0)
    sim._p_recupero_btn.invoke()
    sim.update()
    _fase(sim)
    _fase(sim)
    assert sim._p_esito.bersaglio_raggiunto and sim._p_esito.piano_modificato


def test_senza_recupero_possibile_lo_dice(sim):
    _calcola(sim, 0, 20, "conseguenze")
    _fase(sim, impilamento="DSC")
    assert sim._p_opzioni_recupero == ()
    assert sim._p_recupero_lbl.cget("text") == catalogo.tr("practice.real.recovery.none")
    assert sim._p_recupero_btn.instate(["disabled"])


def test_riepilogo_completo_e_ritorno(sim):
    _calcola(sim, 0, 20, "conseguenze")
    _fase(sim, impilamento="DSC")
    _fase(sim)
    _fase(sim)
    testo = _log(sim)
    from gioco27.services import tabellone as tb
    ritorno = tb.ritorno(112)
    for attesa in (
            catalogo.tr("practice.real.summary.card_target", card=0, target=20),
            catalogo.tr("practice.real.summary.rows", planned=111, executed=112),
            catalogo.tr("practice.real.summary.same_T.no"),
            catalogo.tr("practice.real.summary.same_card.no"),
            catalogo.tr("practice.real.summary.digits", planned="(2,0,2)",
                        executed="(2,0,1)", changed="n0"),
            catalogo.tr("practice.real.summary.realizable", number=112),
            catalogo.tr("practice.real.summary.return", number=112,
                        back=ritorno.numero_tavola,
                        shuffles=" ".join(ritorno.mescolamenti))):
        assert attesa in testo, attesa


def test_cambiare_modalita_riparte_dalla_stessa_sessione(sim, monkeypatch):
    from gioco27.gui import pratica_reale
    monkeypatch.setattr(pratica_reale, "_scegli", lambda *args: True)
    _calcola(sim, 0, 13, "conseguenze")
    _fase(sim, fisico="E2")
    sim._p_modo_var.set("valutazione")
    sim._su_modo()
    assert sim._pstep == 1 and sim._p_deck == list(range(27))
    assert (sim._sessione.carta, sim._sessione.bersaglio) == (0, 13)


# ═══════════════════════ piano fissato dalla Tavola (I3e) ═══════════════════

def test_piano_fissato_senza_risolvi_trucco(sim, monkeypatch):
    def vietato(*a, **k):
        raise AssertionError("il piano fissato non passa da risolvi_trucco")
    monkeypatch.setattr(gr, "risolvi_trucco", vietato)
    sim.imposta_disposizione_fissa(56)
    sim._card_var.set(5)
    sim._find_sequence()
    riga = gr.riga_tavola(56)
    assert sim._sessione.piano["mescolamenti"] == riga["mescolamenti"]
    assert sim._sessione.bersaglio == riga["T"][5]
    assert sim._target_var.get() == riga["T"][5]
    assert sim._fissa_lbl.cget("text") == catalogo.tr(
        "simulator.fixed.active", number=56)
    sim._card_var.set(11)                        # carta variabile
    sim._find_sequence()
    assert sim._sessione.bersaglio == riga["T"][11]
    assert sim._sessione.piano["mescolamenti"] == riga["mescolamenti"]


def test_piano_fissato_in_conseguenze_reali(sim):
    sim.imposta_disposizione_fissa(56)
    sim._card_var.set(0)
    sim._find_sequence()
    sim._p_modo_var.set("conseguenze")
    sim._su_modo()
    _fase(sim)
    _fase(sim)
    _fase(sim)
    assert sim._p_esito.bersaglio_raggiunto and sim._p_esito.stessa_trasformazione
    assert sim._p_esito.numero_previsto == 56


def test_togliere_il_piano_fissato_torna_al_trucco(sim):
    sim.imposta_disposizione_fissa(56)
    sim.togli_disposizione_fissa()
    sim._card_var.set(0)
    sim._target_var.set(13)
    sim._find_sequence()
    assert sim._sessione.piano["mescolamenti"] == ("CSD", "CSD", "CSD")
    assert not sim._fissa_lbl.winfo_ismapped()


def test_in_inglese_davvero(lingua):
    lingua("en")
    from gioco27.gui.simulator_tab import SimulatorFrame
    try:
        radice = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    try:
        sim_en = SimulatorFrame(radice)
        sim_en.pack(fill="both", expand=True)
        radice.update()
        _calcola(sim_en, 0, 13, "conseguenze")
        _fase(sim_en)
        _fase(sim_en)
        _fase(sim_en, fisico="E2")
        testo = _log(sim_en)
        assert catalogo.tr("practice.real.summary.target_but_other_T") in testo
        assert "trasformazione" not in testo.lower()
        assert sim_en._p_modo_conseguenze.cget("text") == catalogo.tr(
            "practice.real.mode.consequences")
    finally:
        radice.destroy()


# ═══════════════════════ Tavola → Pratica (App vera) ════════════════════════

@pytest.fixture(scope="module")
def app():
    try:
        radice = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    radice.destroy()
    from gioco27.gui import app as app_module
    a = app_module.App()
    a._livello = "esperto"
    a._apply_livello()
    a.geometry("1366x768")
    a.update()
    try:
        yield a
    finally:
        try:
            a.destroy()
        except tk.TclError:
            pass


def _seleziona_riga(app, numero):
    tv = app._tavola_frame._tv
    tv.selection_set(str(numero))
    tv.see(str(numero))
    app.update()


def test_selezionare_una_riga_non_tocca_la_pratica(app):
    sim = app._simulator_frame
    sessione = sim._sessione
    _seleziona_riga(app, 56)
    assert getattr(sim, "_disposizione_fissa", None) is None
    assert sim._sessione is sessione


def test_pratica_questa_disposizione(app, monkeypatch):
    def vietato(*a, **k):
        raise AssertionError("il piano fissato non passa da risolvi_trucco")
    monkeypatch.setattr(gr, "risolvi_trucco", vietato)
    _seleziona_riga(app, 100)
    app._tavola_frame._btn_pratica.invoke()
    app.update()
    sim = app._simulator_frame
    assert str(app._nb.select()) == str(app._schede["simulatore"])
    assert sim._disposizione_fissa == 100
    assert sim._sessione.piano["mescolamenti"] == gr.riga_tavola(100)["mescolamenti"]
    carta = sim._sessione.carta
    assert sim._sessione.bersaglio == gr.riga_tavola(100)["T"][carta]
    sim.togli_disposizione_fissa()


def test_in_principiante_la_pratica_della_riga_resta(app):
    try:
        app._livello = "principiante"
        app._apply_livello()
        app._seleziona_scheda("tavola")
        app.update()
        assert app._tavola_frame._btn_pratica.winfo_ismapped()
    finally:
        app._livello = "esperto"
        app._apply_livello()
        app.update()
