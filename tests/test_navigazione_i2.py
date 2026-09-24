"""Compartimento I2d — navigazione minima fra Tavola, Explorer, Cicli, Simulatore.

Contratto D-I2-7 (V4_PRE_I2_VIEW_DECISIONS.md § 14):

* Tavola ↔ Explorer, Tavola ↔ Cicli, Simulatore → Tavola; **nessun** Tavola →
  Simulatore;
* la sola selezione di una riga della Tavola **non** pubblica T; la pubblica
  soltanto l'azione esplicita «Usa come T corrente»;
* «Mostra nella Tavola» usa (R) e, per una T che non e' una disposizione della
  Tavola, resta disabilitata con il motivo scritto;
* in Principiante le azioni verso schede nascoste non compaiono (DP7 non si
  tocca).

L'applicazione vera sotto un display; i test si saltano senza.
"""
import pathlib
import tkinter as tk

import pytest

from gioco27 import i18n as catalogo
from gioco27.core import gioco_reale as gr
from gioco27.services import tabellone as tb
from gioco27.services.procedure import ProceduraGioco

RADICE = pathlib.Path(__file__).resolve().parents[1]


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


@pytest.fixture
def pubblicazioni(app, monkeypatch):
    """Registra ogni chiamata a _notify_T_changed, lasciandola avvenire."""
    chiamate = []
    originale = app._notify_T_changed

    def spia(perm):
        chiamate.append(list(perm))
        return originale(perm)
    monkeypatch.setattr(app, "_notify_T_changed", spia)
    return chiamate


def _seleziona(app, numero):
    tv = app._tavola_frame._tv
    app._tavola_frame._filtro_var.set("")
    app.update()
    tv.selection_set(str(numero))
    tv.see(str(numero))
    app.update()


def _scheda_corrente(app):
    return next(k for k, w in app._schede.items() if str(w) == app._nb.select())


# ═══════════════════ la selezione non pubblica T (D-I2-7) ═══════════════════

def test_selezionare_una_riga_non_pubblica_T(app, pubblicazioni):
    prima = app._last_T_perm
    _seleziona(app, 100)
    assert pubblicazioni == []
    assert app._last_T_perm == prima
    assert app._tavola_frame.pannello.numero == 100


def test_usa_come_T_corrente_pubblica_esplicitamente(app, pubblicazioni):
    _seleziona(app, 100)
    app._tavola_frame._btn_usa_T.invoke()
    app.update()
    assert pubblicazioni == [gr.riga_tavola(100)["T"]]
    assert app._cycles_frame._perm == gr.riga_tavola(100)["T"]
    assert app._tavola_frame._esito_navigazione.cget("text") == catalogo.tr(
        "nav.published", number=100)


def test_la_presentazione_riceve_T_solo_su_azione(app, monkeypatch):
    ricevute = []

    class Finta:
        def update_from_T(self, dati):
            ricevute.append(list(dati["perm"]))
    monkeypatch.setattr(app, "_presentation_win", Finta())
    _seleziona(app, 56)
    assert ricevute == []
    app._tavola_frame._btn_usa_T.invoke()
    app.update()
    assert ricevute == [gr.riga_tavola(56)["T"]]


# ═══════════════════════════════ Tavola ↔ Cicli ═════════════════════════════

def test_tavola_verso_cicli_e_ritorno(app):
    _seleziona(app, 91)
    app._tavola_frame._btn_cicli.invoke()
    app.update()
    assert _scheda_corrente(app) == "cicli"
    assert app._cycles_frame._perm == gr.riga_tavola(91)["T"]
    assert app._cycles_frame._btn_tavola.instate(["!disabled"])
    _seleziona(app, 0)
    app._seleziona_scheda("cicli")
    app._cycles_frame._btn_tavola.invoke()
    app.update()
    assert _scheda_corrente(app) == "tavola"
    assert app._tavola_frame._tv.selection() == ("91",)
    assert app._tavola_frame.pannello.numero == 91


def test_cicli_con_T_fuori_dalla_tavola(app):
    msc = [9 * (n % 3) + n // 3 for n in range(27)]      # MSC da sola
    assert tb.numero_di(msc) is None
    app._cycles_frame.set_permutation(msc)
    app.update()
    assert app._cycles_frame._btn_tavola.instate(["disabled"])
    assert app._cycles_frame._motivo_tavola.cget("text") == catalogo.tr(
        "nav.not_in_table")


# ═══════════════════════════════ Tavola ↔ Explorer ══════════════════════════

def test_tavola_verso_explorer_e_ritorno(app):
    _seleziona(app, 100)
    app._tavola_frame._btn_explorer.invoke()
    app.update()
    assert _scheda_corrente(app) == "explorer"
    risultato = app._explorer_last_result
    assert risultato["ok"] and list(risultato["perm"]) == gr.riga_tavola(100)["T"]
    assert app._exp_tavola_btn.instate(["!disabled"])
    assert app._exp_tavola_motivo.cget("text") == catalogo.tr("nav.in_table",
                                                              number=100)
    _seleziona(app, 0)
    app._seleziona_scheda("explorer")
    app._exp_tavola_btn.invoke()
    app.update()
    assert _scheda_corrente(app) == "tavola"
    assert app._tavola_frame._tv.selection() == ("100",)


def test_f10_explorer_con_rovesciamento_canonico_verso_185(app):
    p = ProceduraGioco(("SCD", "DCS", "SCD"), (0, 0, 1))
    app._explorer_entry.delete("1.0", "end")
    app._explorer_entry.insert("1.0", tb.espressione_per_explorer(p))
    app._explorer_calc()
    app.update()
    assert app._exp_tavola_btn.instate(["!disabled"])
    app._exp_tavola_btn.invoke()
    app.update()
    assert app._tavola_frame._tv.selection() == ("185",)


def test_explorer_con_T_fuori_dalla_tavola(app):
    app._explorer_entry.delete("1.0", "end")
    app._explorer_entry.insert("1.0", "MSC")
    app._explorer_calc()
    app.update()
    assert app._explorer_last_result["ok"]
    assert app._exp_tavola_btn.instate(["disabled"])
    assert app._exp_tavola_motivo.cget("text") == catalogo.tr("nav.not_in_table")
    app._explorer_clear()
    app.update()
    assert app._exp_tavola_btn.instate(["disabled"])


def test_espressione_per_explorer_riproduce_la_trasformazione():
    from gioco27.core.algebra import Controller
    from gioco27.services.procedure import servizio_procedure
    ctrl, servizio = Controller(), servizio_procedure()
    for p in servizio.procedure[::37]:
        r = ctrl.process(tb.espressione_per_explorer(p))
        assert r["ok"] and list(r["perm"]) == list(servizio.trasformazione(p))


# ═══════════════════════════════ Simulatore → Tavola ════════════════════════

def test_simulatore_verso_tavola(app):
    sim = app._simulator_frame
    assert sim._btn_tavola.instate(["disabled"])
    sim._card_var.set(0)
    sim._target_var.set(13)
    sim._find_sequence()
    app.update()
    assert sim._btn_tavola.cget("text") == catalogo.tr("nav.simulator_show",
                                                       number=86)
    sim._btn_tavola.invoke()
    app.update()
    assert _scheda_corrente(app) == "tavola"
    assert app._tavola_frame._tv.selection() == ("86",)


def test_nessun_collegamento_tavola_verso_simulatore():
    """I2: nessun Tavola → Simulatore guidato dal trucco.

    Aggiornato in I3 (D-I3-7): esiste una sola via, esplicita, «Pratica questa
    disposizione», che fissa il piano della riga. Nessuna via passa per il
    trucco (carta → bersaglio → risolvi_trucco), e la selezione non la usa.
    """
    sorgente = (RADICE / "gioco27" / "gui" / "tavola_tab.py").read_text(encoding="utf-8")
    assert "risolvi_trucco" not in sorgente
    assert sorgente.count("self._on_pratica(") == 1
    pannello = (RADICE / "gioco27" / "gui" / "pannello_ternario.py").read_text(
        encoding="utf-8")
    assert "simulat" not in pannello.lower()


# ═══════════════════════════════ Principiante ═══════════════════════════════

def test_in_principiante_niente_azioni_verso_schede_nascoste(app):
    t = app._tavola_frame
    try:
        app._livello = "principiante"
        app._apply_livello()
        app.update()
        assert not t._btn_explorer.winfo_ismapped()
        assert not t._btn_cicli.winfo_ismapped()
        assert t._btn_usa_T.winfo_ismapped()
        assert t.pannello.winfo_ismapped() or app._nb.select() != str(app._schede["tavola"])
        app._seleziona_scheda("tavola")
        app.update()
        assert t.pannello.winfo_ismapped()
        assert str(app._tab_explorer) in [str(w) for w in app._advanced_tabs]
    finally:
        app._livello = "esperto"
        app._apply_livello()
        app.update()
    app._seleziona_scheda("tavola")
    app.update()
    assert t._btn_explorer.winfo_ismapped() and t._btn_cicli.winfo_ismapped()
