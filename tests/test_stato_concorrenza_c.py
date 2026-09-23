"""Compartimento C — stato e concorrenza: provenienza dei dati mostrati.

Copre B02: gli aggregati e le righe grezze del tab Analisi vengono sempre
dalla stessa richiesta, o non ci sono.

Nessun test dipende dalla velocita' della macchina: i lavori vengono catturati e
fatti avanzare esplicitamente.
"""
from types import SimpleNamespace

import pytest

from gioco27.gui import analysis_tab
from gioco27.gui.analysis_tab import RisultatoAnalisi

FILTRI = [dict(p0="SCD_U", p1="SCD_U", p2="SCD_U",
               j0="I_3", j1="I_3", j2="I_3") for _ in range(3)]


# ─────────────────────────── armamentario ───────────────────────────────────

class _Var:
    def __init__(self, v=""):
        self._v = v

    def get(self):
        return self._v

    def set(self, v):
        self._v = v


class _Menu:
    def __init__(self):
        self.stati = {}

    def entryconfigure(self, indice, state):
        self.stati[indice] = state


class _MenuButton:
    def __init__(self):
        self.stato = "disabled"

    def configure(self, state):
        self.stato = state

    def __getitem__(self, _k):
        return None

    def __setitem__(self, _k, _v):
        pass


class _Lavoro:
    """Un job catturato, con la stessa semantica d'errore di run_in_thread."""

    def __init__(self, job, on_error):
        self.job = job
        self.on_error = on_error
        self.errore = None

    def esegui(self):
        try:
            self.job()
        except Exception as exc:          # come fa run_in_thread
            self.errore = exc
            if self.on_error is not None:
                self.on_error(exc)


class TabAnalisi(analysis_tab.AnalysisTabMixin):
    """Il mixin reale con una coda esplicita al posto del thread Tk."""

    def __init__(self):
        self._closing = False
        self._analisi_corrente = None
        self._analisi_risultati = []
        self._analisi_righe_raw = []
        self._analisi_status = _Var()
        self._analisi_exp_mb = _MenuButton()
        self._analisi_exp_menu = _Menu()
        self._analisi_voci_grezzi = (4, 5)
        self.progress = {}
        self.coda = []
        self.popolati = []

    # thread Tk simulato
    def _ui(self, fn):
        self.coda.append(fn)

    def esegui_coda(self):
        pendenti, self.coda = list(self.coda), []
        for fn in pendenti:
            fn()

    def update_idletasks(self):
        pass

    def _get_filters(self):
        return FILTRI

    def _analisi_populate(self, risultati, n_tot):
        self.popolati.append((list(risultati), n_tot))
        self._analisi_aggiorna_export()

    # comodita' per i test
    @property
    def origine(self):
        return self._analisi_corrente.origine if self._analisi_corrente else None


@pytest.fixture
def tab(monkeypatch):
    t = TabAnalisi()
    lavori = []
    monkeypatch.setattr(analysis_tab, "run_in_thread",
                        lambda widget, job, **kw: lavori.append(
                            _Lavoro(job, kw.get("on_error"))) or None)
    monkeypatch.setattr(analysis_tab, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: None, showwarning=lambda *a, **k: None,
        showerror=lambda *a, **k: None, askyesno=lambda *a, **k: True))
    t.lavori = lavori
    return t


def _csv_finto(monkeypatch, percorso="analisi.csv"):
    monkeypatch.setattr(analysis_tab.filedialog, "askopenfilename",
                        lambda **k: percorso)


def _risultati(n_sim, perm="[0]"):
    return [{"n_sim": n_sim, "perm_str": perm, "simboliche": [f"S{n_sim}"]}]


# ───────────────────────────── B02 ──────────────────────────────────────────

def test_b02_analisi_dai_filtri_porta_con_se_i_grezzi(tab, monkeypatch):
    monkeypatch.setattr(analysis_tab, "count_combinations_ex", lambda f: 2)
    monkeypatch.setattr(analysis_tab, "iter_combinations_ex", lambda f: iter([0, 1]))
    monkeypatch.setattr(analysis_tab, "make_csv_row",
                        lambda i, p: [str(i)] * 9)
    monkeypatch.setattr(analysis_tab, "analizza_righe", lambda righe: _risultati(2))

    tab._run_analisi()
    tab.lavori[0].esegui()
    tab.esegui_coda()

    assert tab.origine == "filtri"
    assert len(tab._analisi_righe_raw) == 2
    assert tab._analisi_risultati == _risultati(2)
    assert tab._analisi_exp_menu.stati == {4: "normal", 5: "normal"}


def test_b02_import_csv_non_eredita_i_grezzi_precedenti(tab, monkeypatch):
    """A -> import B: gli aggregati sono di B, i grezzi di A spariscono."""
    monkeypatch.setattr(analysis_tab, "count_combinations_ex", lambda f: 1)
    monkeypatch.setattr(analysis_tab, "iter_combinations_ex", lambda f: iter([0]))
    monkeypatch.setattr(analysis_tab, "make_csv_row", lambda i, p: ["A"] * 9)
    monkeypatch.setattr(analysis_tab, "analizza_righe", lambda righe: _risultati(1, "[A]"))
    tab._run_analisi()
    tab.lavori[0].esegui()
    tab.esegui_coda()
    assert tab._analisi_righe_raw and tab._analisi_righe_raw[0]["Stage0"] == "A"

    _csv_finto(monkeypatch)
    monkeypatch.setattr(analysis_tab, "analizza_csv", lambda p: _risultati(7, "[B]"))
    tab._analisi_load_csv()
    tab.lavori[1].esegui()
    tab.esegui_coda()

    assert tab.origine == "csv"
    assert tab._analisi_risultati[0]["perm_str"] == "[B]"
    assert tab._analisi_righe_raw == [], "i grezzi di A non devono sopravvivere"
    assert tab._analisi_exp_menu.stati == {4: "disabled", 5: "disabled"}
    assert tab._analisi_exp_mb.stato == "normal"


def test_b02_import_vuoto(tab, monkeypatch):
    _csv_finto(monkeypatch)
    monkeypatch.setattr(analysis_tab, "analizza_csv", lambda p: [])
    tab._analisi_load_csv()
    tab.lavori[0].esegui()
    tab.esegui_coda()
    assert tab._analisi_risultati == [] and tab._analisi_righe_raw == []
    assert tab._analisi_exp_mb.stato == "disabled"


def test_b02_import_fallito_lascia_lo_stato_precedente_coerente(tab, monkeypatch):
    monkeypatch.setattr(analysis_tab, "count_combinations_ex", lambda f: 1)
    monkeypatch.setattr(analysis_tab, "iter_combinations_ex", lambda f: iter([0]))
    monkeypatch.setattr(analysis_tab, "make_csv_row", lambda i, p: ["A"] * 9)
    monkeypatch.setattr(analysis_tab, "analizza_righe", lambda righe: _risultati(1, "[A]"))
    tab._run_analisi()
    tab.lavori[0].esegui()
    tab.esegui_coda()
    prima = (list(tab._analisi_risultati), list(tab._analisi_righe_raw))

    _csv_finto(monkeypatch)

    def rotto(_p):
        raise OSError("file illeggibile")

    monkeypatch.setattr(analysis_tab, "analizza_csv", rotto)
    tab._analisi_load_csv()
    tab.lavori[1].esegui()
    tab.esegui_coda()

    assert isinstance(tab.lavori[1].errore, OSError)
    # nulla e' stato pubblicato: lo stato resta quello di A, coerente in se'
    assert (tab._analisi_risultati, tab._analisi_righe_raw) == (prima[0], prima[1])
    assert tab.origine == "filtri"
    assert tab._analisi_status.get() != ""


def test_b02_catena_a_b_c(tab, monkeypatch):
    """A (filtri) -> B (csv) -> C (filtri): nessun dato di A riappare con C."""
    monkeypatch.setattr(analysis_tab, "count_combinations_ex", lambda f: 1)
    monkeypatch.setattr(analysis_tab, "make_csv_row", lambda i, p: ["A"] * 9)
    monkeypatch.setattr(analysis_tab, "iter_combinations_ex", lambda f: iter([0]))
    monkeypatch.setattr(analysis_tab, "analizza_righe", lambda righe: _risultati(1, "[A]"))
    tab._run_analisi(); tab.lavori[-1].esegui(); tab.esegui_coda()

    _csv_finto(monkeypatch)
    monkeypatch.setattr(analysis_tab, "analizza_csv", lambda p: _risultati(2, "[B]"))
    tab._analisi_load_csv(); tab.lavori[-1].esegui(); tab.esegui_coda()

    monkeypatch.setattr(analysis_tab, "make_csv_row", lambda i, p: ["C"] * 9)
    monkeypatch.setattr(analysis_tab, "analizza_righe", lambda righe: _risultati(3, "[C]"))
    tab._run_analisi(); tab.lavori[-1].esegui(); tab.esegui_coda()

    assert tab._analisi_risultati[0]["perm_str"] == "[C]"
    assert [r["Stage0"] for r in tab._analisi_righe_raw] == ["C"]
    assert tab.origine == "filtri"


def test_b02_aggregati_e_grezzi_vengono_sempre_dallo_stesso_risultato(tab):
    """La pubblicazione e' un unico punto: non esiste uno stato misto."""
    risultato = RisultatoAnalisi(origine="csv",
                                 aggregati=({"n_sim": 1, "perm_str": "[X]",
                                             "simboliche": []},),
                                 grezzi=({"Stage0": "X"},), totale=1)
    assert tab._analisi_pubblica(risultato) is True
    assert tab._analisi_corrente is risultato
    assert tab._analisi_risultati == list(risultato.aggregati)
    assert tab._analisi_righe_raw == list(risultato.grezzi)
