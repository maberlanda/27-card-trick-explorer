"""Regressioni B15-B17: callback reali, widget sostituiti senza aprire finestre."""
from types import SimpleNamespace

import pytest

from gioco27.core.algebra import Controller
from gioco27.gui import app as app_module
from gioco27.gui.explorer_tab import ExplorerTabMixin
from gioco27.gui.preview_tab import PreviewTabMixin
from gioco27.gui.shuffle import ShuffleViewerFrame


IDENTITY = "(SCD_U x SCD_U x SCD_U)"
CYCLE = "(CDS_U x SCD_U x SCD_U)"


class Widget:
    def __init__(self, value=""):
        self.value = value
        self.options = {}

    def get(self, *args):
        return self.value

    def set(self, value):
        self.value = value

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def delete(self, *args):
        self.value = ""

    def insert(self, index, text, *args):
        self.value += text


class Presentation:
    def __init__(self, parent=None):
        self.received = []
        self.lifted = False

    def update_from_T(self, data):
        self.received.append(list(data["perm"]))

    def winfo_exists(self):
        return True

    def lift(self):
        self.lifted = True

    def focus_force(self):
        pass


class ExplorerHarness(ExplorerTabMixin):
    _notify_T_changed = app_module.App._notify_T_changed
    _on_simulator_T = app_module.App._on_simulator_T
    _open_presentation = app_module.App._open_presentation

    def __init__(self):
        self._explorer_ctrl = Controller()
        self._explorer_entry = Widget(IDENTITY)
        self._explorer_status = Widget()
        self._explorer_last_result = None
        self._last_T_perm = list(range(27))
        self._presentation_win = None
        self.cycles, self.distribution = [], []
        self._cycles_frame = SimpleNamespace(set_permutation=lambda p: self.cycles.append(list(p)))
        self._distrib_frame = SimpleNamespace(set_permutation=lambda p: self.distribution.append(list(p)))
        self.output = {}
        for name in ("norm steps_sum perm period sig inv nf_kind nf_msc nf_sym "
                     "nf_kron nf_notes can_avail can_sym can_exp can_notes log rewrite eval").split():
            setattr(self, "_exp_" + name, name)
        self._exp_can_factors = ["f0", "f1", "f2"]
        self._exp_export_btn = Widget()
        self._decomp_btn = Widget()

    def _exp_set(self, widget, text):
        self.output[widget] = text

    def _exp_set_colored(self, widget, text, **kwargs):
        self._exp_set(widget, text)

    def _update_matrix_tab(self, result):
        pass

    def _reset_matrix_tab(self):
        pass


@pytest.mark.parametrize("already_open", [False, True])
def test_b15_explorer_e_presentazione_ricevono_la_nuova_t(already_open, monkeypatch):
    monkeypatch.setattr(app_module, "PresentationWindow", Presentation)
    app = ExplorerHarness()
    app._explorer_calc()
    old = list(app._last_T_perm)
    if already_open:
        app._open_presentation()
    app._explorer_entry.value = CYCLE
    app._explorer_calc()
    new = app._explorer_last_result["perm"]
    assert new != old
    assert app._last_T_perm == new
    app._open_presentation()
    assert app._presentation_win.received[-1] == new
    assert app.cycles[-1] == new and app.distribution[-1] == new
    if already_open:
        assert app._presentation_win.received == [old, new]
        assert app._presentation_win.lifted


def test_b15_simulatore_notifica_una_volta_e_conserva_copia(monkeypatch):
    monkeypatch.setattr(app_module, "PresentationWindow", Presentation)
    app = ExplorerHarness()
    perm = Controller().process(CYCLE)["perm"]
    expected = list(perm)
    app._on_simulator_T(perm)
    perm[:] = range(27)
    app._open_presentation()
    assert app._last_T_perm == expected
    assert app._presentation_win.received == [expected]
    assert app.cycles == [expected] and app.distribution == [expected]


def test_b15_anteprima_aggiorna_anche_presentazione(monkeypatch):
    monkeypatch.setattr(app_module, "PresentationWindow", Presentation)
    app = ExplorerHarness()
    app._prev_vars = [{name: Widget(value) for name, value in dict(
        p0="SCD_U", p1="SCD_U", p2="SCD_U", j0="I_3", j1="I_3", j2="I_3").items()}
        for _ in range(3)]
    app._prev_vars[0]["p2"].value = "CDS_U"
    app._prev_result = Widget()
    PreviewTabMixin._calcola_anteprima(app)
    assert app._prev_T_perm != list(range(27))
    app._open_presentation()
    assert app._last_T_perm == app._prev_T_perm
    assert app._presentation_win.received == [app._prev_T_perm]
    assert app.cycles == [app._prev_T_perm]
    assert app.distribution == [app._prev_T_perm]


@pytest.mark.parametrize("expression", ["", "???"])
def test_b15_calcolo_non_valido_non_sostituisce_ultima_t(expression):
    app = ExplorerHarness()
    app._last_T_perm = Controller().process(CYCLE)["perm"]
    old = list(app._last_T_perm)
    app._explorer_entry.value = expression
    app._explorer_calc()
    assert app._last_T_perm == old
    assert app.cycles == [] and app.distribution == []


class ShuffleHarness(ShuffleViewerFrame):
    def __init__(self):
        self._inv_labels = [Widget() for _ in range(27)]


@pytest.mark.parametrize("expression", [CYCLE, "MSC", CYCLE + " o MSC"])
@pytest.mark.parametrize("card_by_card", [False, True])
def test_b16_vettore_mostrato_e_inversa_explorer(expression, card_by_card):
    result = Controller().process(expression)
    assert result["ok"] and result["perm"] != result["inverse_perm"]
    view = ShuffleHarness()
    tokens = view._validate_and_parse(expression)
    if card_by_card:
        view._build_steps_card_by_card(tokens)
    else:
        view._build_steps(tokens)
    step = view._steps[-1]
    assert step["deck"].tolist() == result["inverse_perm"]
    view._redraw_inv_vector(step["deck"], step["changed"],
                            deck_before=step.get("deck_before"),
                            deck_final=step.get("deck_final"),
                            card_step=step.get("card_step", False))
    shown = [int(label.options["text"]) for label in view._inv_labels]
    assert shown == result["inverse_perm"]
    assert shown != result["perm"]


def test_b16_sottopassi_rivelano_le_posizioni_corrette():
    view = ShuffleHarness()
    view._build_steps_card_by_card(view._validate_and_parse(CYCLE))
    final = Controller().process(CYCLE)["inverse_perm"]
    intermediate = [s for s in view._steps if s.get("card_step")]
    assert intermediate
    for step in intermediate:
        view._redraw_inv_vector(step["deck"], step["changed"],
                                deck_before=step["deck_before"],
                                deck_final=step["deck_final"], card_step=True)
        for pos, label in enumerate(view._inv_labels):
            if step["deck"][pos] == final[pos]:
                assert label.options["text"] == f"{final[pos]:02d}"
                if pos in step["changed"]:
                    assert label.options["bg"] == view._CLR_MOVED
            else:
                assert label.options["text"] == "·"


@pytest.mark.parametrize("expression,identity", [
    (IDENTITY, True), ("MSC o MSC o MSC", True), ("J o J", True),
    ("J", False), ("MSC", False), (CYCLE, False),
])
def test_b17_note_identita_coerenti_con_permutazione(expression, identity):
    app = ExplorerHarness()
    app._explorer_entry.value = expression
    app._explorer_calc()
    result = app._explorer_last_result
    assert result["ok"]
    assert (result["perm"] == list(range(27))) == identity
    assert ("L'espressione è l'identità." in app.output["nf_notes"]) == identity
