"""Percorso e contratti osservabili del Blocco 3; nessun nuovo test matematico."""
import pytest

from gioco27 import i18n
from gioco27.core import config, gioco_reale as gr
from gioco27.gui import pratica_reale
from gioco27.gui.app import App


@pytest.fixture(scope="module")
def workspace(tmp_path_factory):
    path = tmp_path_factory.mktemp("ux3")
    patch = pytest.MonkeyPatch()
    patch.setattr(config, "_CONFIG_DIR", path)
    patch.setattr(config, "_CONFIG_FILE", path / "config.json")
    cfg = config.Config()
    cfg._data.update(language="it", livello="base", ui_intro_done=True, use_parallel=False)
    patch.setattr(config, "_instance", cfg)
    app = App()
    app.geometry("1280x800")
    app.withdraw()
    app.update()
    yield app
    app.destroy()
    patch.undo()


@pytest.fixture
def app(workspace):
    workspace._simulator_frame.reset()
    workspace._riconoscimento.reset()
    workspace._explorer_clear()
    workspace.update()
    return workspace


def prepare(app, mode="valutazione"):
    sim = app._simulator_frame
    sim._card_var.set(0)
    sim._target_var.set(13)
    sim._find_sequence()
    sim._p_modo_var.set(mode)
    sim._su_modo()
    return sim


def phase(sim, physical="nessuno"):
    col = next(i for i, pile in enumerate(sim._p_cols) if sim._p_card in pile)
    sim._practice_choose_col(col)
    sim._p_order_var.set(sim._p_impilamento_atteso())
    sim._p_fisico_var.set(physical)
    sim._practice_confirm_order()


def test_t01_entry_destinations(app):
    for index, dest in ((0, "simulatore"), (2, "tavola")):
        app._onboard_actions[index].invoke()
        assert app._nb.select() == str(app._schede[dest])
    app._imposta_livello("base")
    app._onboard_actions[1].invoke()
    assert app._livello == "avanzato"
    assert app._nb.select() == str(app._schede["explorer"])
    assert app._explorer_nb.select() == str(app._riconoscimento)


def test_t02_table_opens_practice_with_selected_plan(app):
    app._pratica_disposizione(100)
    sim = app._simulator_frame
    assert sim._notebook.select() == str(sim._practice_tab)
    assert sim._sessione.piano["numero"] == 100
    assert list(sim._sessione.piano["T"]) == gr.riga_tavola(100)["T"]


def test_t03_mode_cancel_preserves_and_confirm_restarts(app, monkeypatch):
    sim = prepare(app)
    phase(sim)
    deck = list(sim._p_deck)
    monkeypatch.setattr(pratica_reale, "_scegli", lambda *a: False)
    sim._p_modo_var.set("conseguenze")
    sim._su_modo()
    assert sim._p_modo_var.get() == "valutazione"
    assert sim._pstep == 2 and sim._p_deck == deck
    monkeypatch.setattr(pratica_reale, "_scegli", lambda *a: True)
    sim._p_modo_var.set("conseguenze")
    sim._su_modo()
    assert sim._pstep == 1 and sim._p_stato is not None
    assert sim._p_errors == 0


def test_t04_recovery_labels_distinguish_original_and_active(app):
    sim = prepare(app, "conseguenze")
    initial = tuple(sim._sessione.piano["mescolamenti"])
    phase(sim, "E3")
    assert sim._p_opzioni_recupero
    sim._reale_applica_recupero()
    text = sim._p_piano_lbl.cget("text")
    assert "Piano iniziale" in text and "Piano attivo" in text
    assert tuple(sim._sessione.piano["mescolamenti"]) == initial
    assert sim._status_lbl.cget("text") == text
    sim._practice_reset()
    assert "Piano attivo" not in sim._status_lbl.cget("text")


@pytest.mark.parametrize("unknown", [False, True])
def test_t05_t06_spectator_independent_target_and_final_deck(app, unknown):
    from gioco27.gui.spettatore_tab import MODO_B12
    from gioco27.services import spettatore as sp
    sim = app._simulator_frame
    sim._target_var.set(26)
    s = sim._spettatore
    s._bersaglio_var.set(5)
    if unknown:
        s._modo_var.set(MODO_B12)
    s._aggiorna_controlli()
    s.avvia()
    target = 13 if unknown else 5
    assert s._sessione.bersaglio == target
    assert sim._target_var.get() == 26
    for _ in range(3):
        piles = sp.distribuzione_corrente(s._sessione)
        col = next(i for i, pile in enumerate(piles) if 0 in pile)
        s.rispondi(col)
        s.esegui_raccolta()
    assert s._sessione.conclusa
    assert len(s._pile.get_children()) == 9
    assert "Procedura terminata" in s._info_txt.get("1.0", "2.0")
    assert str(target) in s._fase_lbl.cget("text")
    assert s._pile.heading("C", "text") == "Posizioni 9–17"
    s.reset()
    assert "Centro" in s._pile.heading("C", "text")


def test_t07_explorer_example_is_table_row_100(app):
    app._explorer_example()
    result = app._explorer_last_result
    assert result["ok"]
    assert list(result["perm"]) == gr.riga_tavola(100)["T"]


@pytest.mark.parametrize("values, phrase", [
    (list(range(26)), "27"),
    (list(range(26)) + [27], "0 e 26"),
    (list(range(26)) + [0], "due volte"),
])
def test_t08_t09_recognition_local_validation_without_explorer(app, values, phrase):
    r = app._riconoscimento
    r._imposta(r._campo1, " ".join(map(str, values)))
    r.analizza()
    assert r._pi is None and phrase in r._errore_lbl.cget("text")
    assert app._explorer_last_result is None


def test_t09_valid_and_a1_two_known_inputs(app):
    r = app._riconoscimento
    ordered = " ".join(map(str, range(27)))
    r._imposta(r._campo1, ordered)
    r.analizza()
    assert r._pi is not None and not r._errore_lbl.cget("text")
    for e, text in zip(r._a1_campi, (ordered, "", ordered)):
        e.insert(0, text)
    r.a1()
    assert "⚠" not in r._a1_txt.get("1.0", "end")
    assert "Compila due" in i18n.tr("ux3.a1")


def test_t10_new_keys_available_in_both_languages():
    keys = {k for k in i18n.CATALOGS["it"] if k.startswith("ux3.")}
    assert keys and keys <= i18n.CATALOGS["en"].keys()
    for key in keys:
        assert i18n.CATALOGS["it"][key] and i18n.CATALOGS["en"][key]


def test_t03_same_mode_preserves_trial_without_confirmation(app, monkeypatch):
    sim = prepare(app)
    phase(sim)
    def unexpected(*args):
        pytest.fail("La modalità invariata non richiede conferma")
    monkeypatch.setattr(pratica_reale, "_scegli", unexpected)
    sim._su_modo()
    assert sim._pstep == 2


def test_t09_a1_all_three_checks_consistency(app):
    r = app._riconoscimento
    ordered = " ".join(map(str, range(27)))
    for field in r._a1_campi:
        field.delete(0, "end")
        field.insert(0, ordered)
    r.a1()
    assert "⚠" not in r._a1_txt.get("1.0", "end")


def test_t06_practice_latest_feedback_and_recovery_access_at_1280(app):
    app.deiconify()
    app._seleziona_scheda("simulatore")
    sim = prepare(app, "conseguenze")
    sim._notebook.select(sim._practice_tab)
    phase(sim, "E3")
    app.update()
    assert "E3" in sim._p_latest_feedback.cget("text")
    for widget in (sim._pstep_lbl, sim._p_col_btn_frame,
                   sim._p_latest_feedback, sim._p_recupero_btn):
        assert widget.winfo_ismapped()
        assert widget.winfo_rooty() + widget.winfo_height() < app.winfo_rooty() + app.winfo_height()
    app.withdraw()


def test_f24_positions_headers_and_groups_fit_their_columns(app):
    from tkinter import font, ttk
    panel = app._tavola_frame.pannello
    panel.mostra_disposizione(100)
    tree = panel._tabella
    style = ttk.Style(tree)
    heading_font = font.Font(font=style.lookup("Treeview.Heading", "font") or "TkHeadingFont")
    body_font = font.Font(font=style.lookup("Treeview", "font") or "TkDefaultFont")
    for col in tree.cget("columns"):
        assert heading_font.measure(tree.heading(col, "text")) + 12 <= tree.column(col, "width")
    for group in tree.get_children():
        assert body_font.measure(tree.item(group, "text")) + 32 <= tree.column("#0", "width")
    assert tree.cget("xscrollcommand") and tree.cget("yscrollcommand")


def test_f24_conjugacy_centre_and_statistics_remain_consultable(app, monkeypatch):
    from gioco27.gui import conjugacy_dialog as module
    monkeypatch.setattr(module, "run_in_thread", lambda widget, job, **kw: job())
    monkeypatch.setattr(module, "ui_call", lambda widget, job: job())
    dialog = module.ConjugacyDialog(app)
    try:
        app.update()
        assert dialog._stats_txt.get("1.0", "end").strip()
        assert dialog._stats_txt.cget("yscrollcommand")
        assert dialog._center_box.winfo_ismapped()
        assert dialog._center_box.winfo_height() > 100
        assert dialog._center_box.winfo_rooty() + dialog._center_box.winfo_height() <= dialog.winfo_rooty() + dialog.winfo_height()
    finally:
        dialog.destroy()
