"""Regressioni B18-B19: percorso di chiusura e tre fasi obbligatorie."""
from itertools import product

import pytest

from gioco27.core import gioco_reale as gr
from gioco27.gui.app import App


class Config(dict):
    def __init__(self):
        super().__init__()
        self.saved = []

    def save(self):
        self.saved.append(dict(self))


class AppHarness:
    _quit_app = App._quit_app

    def __init__(self):
        self._cfg = Config()
        self.closed = 0
        self.destroyed = 0
        self._analisi_risultati = [1]
        self._analisi_righe_raw = [2]
        self._explorer_last_result = {"perm": list(range(27))}

    def _on_close(self):
        self.closed += 1
        App._on_close(self)

    def geometry(self):
        return "1170x830+40+60"

    def destroy(self):
        self.destroyed += 1


@pytest.mark.parametrize("command", ["_on_close", "_quit_app"])
def test_b18_chiusure_salvano_geometria_e_distruggono_una_volta(command):
    app = AppHarness()
    with pytest.raises(SystemExit) as exit_info:
        getattr(app, command)()
    assert exit_info.value.code == 0
    assert app.closed == app.destroyed == 1
    assert app._cfg.saved == [{"window_geometry": "1170x830+40+60"}]
    assert app._analisi_risultati == app._analisi_righe_raw == []
    assert app._explorer_last_result is None


@pytest.mark.parametrize("length", [0, 1, 2, 4, 8])
@pytest.mark.parametrize("container", [tuple, list])
def test_b19_lunghezze_errate_rifiutate_prima_delle_fasi(length, container, monkeypatch):
    def forbidden(*args):
        pytest.fail("non deve iniziare una partita con inversioni incomplete")

    monkeypatch.setattr(gr, "distribuisci", forbidden)
    with pytest.raises(ValueError, match="esattamente 3 rovesciamenti"):
        gr.esegui_partita(("CDS", "CDS", "CDS"), container([False] * length))


@pytest.mark.parametrize("reversals", list(product([False, True], repeat=3)))
def test_b19_tre_inversioni_preservano_la_simulazione(reversals):
    shuffles = ("CDS", "SDC", "DSC")
    # Riferimento per singola carta, indipendente dalla costruzione del mazzo.
    expected = []
    for card in range(27):
        pos = card
        for name, reverse in zip(shuffles, reversals):
            pos = 9 * gr.MESCOLAMENTO[name][pos % 3] + pos // 3
            if reverse:
                pos = 26 - pos
        expected.append(pos)
    deck, steps = gr.esegui_partita(shuffles, reversals)
    assert deck == [expected.index(pos) for pos in range(27)]
    assert len(steps) == 7
    collections = [step for step in steps if step["tipo"] == "raccolta"]
    assert [step["fase"] for step in collections] == [1, 2, 3]
    assert [step["rovesciato"] for step in collections] == list(reversals)


def test_b19_default_invariato():
    shuffles = ("CDS", "CDS", "CDS")
    assert gr.esegui_partita(shuffles) == gr.esegui_partita(shuffles, (False, False, False))
