"""Compartimento C — stato e concorrenza: provenienza, revisioni, sessioni.

Copre B02 (aggregati e grezzi della stessa richiesta), B03 (risposte tardive e
fuori ordine), B04 (sessione di pratica con input congelati), R05 (ogni lavoro
finisce in uno stato conclusivo) e M03 (contratto delle notifiche di T).

Nessun test dipende dalla velocita' della macchina: i lavori vengono catturati e
fatti avanzare esplicitamente, e dove serve un thread vero lo si aspetta con
`join` prima di controllare.
"""
import ast
import pathlib
import threading
from types import SimpleNamespace

import pytest

from gioco27.core import gioco_reale as gr
from gioco27.core.analisi import PianoAnalisi
from gioco27.gui import analysis_tab, app as app_module, common, simulator_tab
from gioco27.gui.analysis_tab import RisultatoAnalisi
from gioco27.gui.simulator_tab import SessionePratica

RADICE = pathlib.Path(__file__).resolve().parents[1]
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
        self._analisi_revisione = 0
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


def _piano(monkeypatch, combinazioni, grezzi=True):
    """Finge il preflight dell'analisi.

    Il compartimento F ha sostituito il conteggio nudo del dominio con un piano
    calcolato prima di enumerare: e' li' che la scheda decide quante
    combinazioni ci sono e se terra' le righe grezze. I test che qui fingono un
    dominio piccolo fingono il piano; il contratto di C — revisioni,
    pubblicazione unica, RisultatoAnalisi — non cambia.
    """
    monkeypatch.setattr(analysis_tab, "pianifica_analisi",
                        lambda f: PianoAnalisi(combinazioni=combinazioni,
                                               grezzi=grezzi))


# ───────────────────────────── B02 ──────────────────────────────────────────

def test_b02_analisi_dai_filtri_porta_con_se_i_grezzi(tab, monkeypatch):
    _piano(monkeypatch, 2)
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
    _piano(monkeypatch, 1)
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
    _piano(monkeypatch, 1)
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
    _piano(monkeypatch, 1)
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
    risultato = RisultatoAnalisi(revisione=tab._analisi_revisione, origine="csv",
                                 aggregati=({"n_sim": 1, "perm_str": "[X]",
                                             "simboliche": []},),
                                 grezzi=({"Stage0": "X"},), totale=1)
    assert tab._analisi_pubblica(risultato) is True
    assert tab._analisi_corrente is risultato
    assert tab._analisi_risultati == list(risultato.aggregati)
    assert tab._analisi_righe_raw == list(risultato.grezzi)


# ───────────────────────────── B03 ──────────────────────────────────────────

def _prepara_due_analisi(tab, monkeypatch):
    _piano(monkeypatch, 1)
    monkeypatch.setattr(analysis_tab, "iter_combinations_ex", lambda f: iter([0]))
    etichette = iter(["A", "B"])

    def righe(i, p):
        return [next(etichette)] * 9

    monkeypatch.setattr(analysis_tab, "make_csv_row", righe)
    monkeypatch.setattr(analysis_tab, "analizza_righe",
                        lambda rows: _risultati(1, f"[{rows[0]['Stage0']}]"))


def test_b03_completamenti_fuori_ordine_pubblicano_solo_il_corrente(tab, monkeypatch):
    """Avvio A, avvio B, completa B, completa A -> resta B.

    A e' un'analisi dai filtri, B un import CSV: due produttori distinti, cosi'
    l'esito non dipende dall'ordine in cui i due job vengono fatti avanzare.
    """
    _prepara_due_analisi(tab, monkeypatch)
    _csv_finto(monkeypatch)
    monkeypatch.setattr(analysis_tab, "analizza_csv", lambda p: _risultati(9, "[B]"))

    tab._run_analisi()                     # A parte per prima
    tab._analisi_load_csv()                # B e' la richiesta corrente
    lavoro_a, lavoro_b = tab.lavori

    lavoro_b.esegui(); tab.esegui_coda()   # B finisce per prima
    assert tab._analisi_risultati[0]["perm_str"] == "[B]"

    lavoro_a.esegui(); tab.esegui_coda()   # risposta tardiva di A
    assert tab._analisi_risultati[0]["perm_str"] == "[B]", "A non deve ripubblicarsi"
    assert [p[0][0]["perm_str"] for p in tab.popolati] == ["[B]"]
    assert tab.origine == "csv"


def test_b03_pubblicazione_rifiuta_una_revisione_superata(tab):
    """Il controllo di identita', isolato dal resto."""
    rev_a = tab._analisi_nuova_revisione()
    rev_b = tab._analisi_nuova_revisione()
    risultato_a = RisultatoAnalisi(revisione=rev_a, origine="filtri",
                                   aggregati=(), grezzi=(), totale=0)
    risultato_b = RisultatoAnalisi(revisione=rev_b, origine="csv",
                                   aggregati=(), grezzi=(), totale=0)
    assert tab._analisi_pubblica(risultato_b) is True
    assert tab._analisi_pubblica(risultato_a) is False
    assert tab._analisi_corrente is risultato_b


def test_b03_reset_invalida_il_lavoro_in_corso(tab, monkeypatch):
    _prepara_due_analisi(tab, monkeypatch)
    tab._run_analisi()
    tab._reset_analisi()
    stato_dopo_reset = (list(tab._analisi_risultati), list(tab._analisi_righe_raw))
    tab.lavori[0].esegui(); tab.esegui_coda()
    assert (tab._analisi_risultati, tab._analisi_righe_raw) == stato_dopo_reset == ([], [])
    assert tab._analisi_corrente is None
    assert tab.popolati == []


def test_b03_reset_durante_import(tab, monkeypatch):
    _csv_finto(monkeypatch)
    monkeypatch.setattr(analysis_tab, "analizza_csv", lambda p: _risultati(5))
    tab._analisi_load_csv()
    tab._reset_analisi()
    tab.lavori[0].esegui(); tab.esegui_coda()
    assert tab._analisi_risultati == [] and tab._analisi_corrente is None


def test_b03_nuova_richiesta_durante_import(tab, monkeypatch):
    _csv_finto(monkeypatch)
    monkeypatch.setattr(analysis_tab, "analizza_csv", lambda p: _risultati(5, "[CSV]"))
    tab._analisi_load_csv()                       # import in corso
    _prepara_due_analisi(tab, monkeypatch)
    tab._run_analisi()                            # nuova richiesta dai filtri
    tab.lavori[1].esegui(); tab.esegui_coda()     # la nuova finisce per prima
    tab.lavori[0].esegui(); tab.esegui_coda()     # l'import arriva tardi
    assert tab._analisi_risultati[0]["perm_str"] == "[A]"
    assert tab.origine == "filtri"


def test_b03_chiusura_durante_il_lavoro(tab, monkeypatch):
    _prepara_due_analisi(tab, monkeypatch)
    tab._run_analisi()
    tab._closing = True
    tab.lavori[0].esegui(); tab.esegui_coda()
    assert tab.popolati == [] and tab._analisi_corrente is None


def test_b03_la_revisione_e_monotona(tab):
    prima = tab._analisi_revisione
    assert tab._analisi_nuova_revisione() == prima + 1
    assert tab._analisi_nuova_revisione() == prima + 2
    assert tab._analisi_e_corrente(prima + 2) is True
    assert tab._analisi_e_corrente(prima + 1) is False


# ───────────────────────────── B04 ──────────────────────────────────────────

class _Testo:
    def __init__(self):
        self.parti = []

    def configure(self, **kw):
        pass

    def delete(self, *a):
        self.parti.clear()

    def insert(self, _dove, testo, tag=None):
        self.parti.append(testo)

    def see(self, *a):
        pass


def _simulatore(carta=0, bersaglio=13):
    sim = object.__new__(simulator_tab.SimulatorFrame)
    sim._card_var = _Var(carta)
    sim._target_var = _Var(bersaglio)
    sim._p_log = _Testo()
    sim._p_errors = 0
    sim._p_err_log = []
    sim._sessione = None
    return sim


def test_b04_la_sessione_congela_i_suoi_input():
    sessione = SessionePratica.calcola(0, 13)
    assert (sessione.carta, sessione.bersaglio) == (0, 13)
    assert sessione.piano["T"][0] == 13
    with pytest.raises(Exception):            # frozen: non si riscrive
        sessione.carta = 1
    with pytest.raises(TypeError):            # il piano e' di sola lettura
        sessione.piano["mescolamenti"] = ()


def test_b04_ricomincia_usa_la_sessione_non_i_campi():
    """Il bug: cambiando il campo carta, «ricomincia» riusava il piano 0->13."""
    sim = _simulatore()
    sim._sessione = SessionePratica.calcola(0, 13)
    ricevute = []
    sim._init_practice = lambda sessione: ricevute.append(sessione)

    sim._card_var.set(1)                      # l'utente cambia il campo
    sim._target_var.set(5)
    sim._practice_reset()

    assert ricevute == [sim._sessione]
    assert (ricevute[0].carta, ricevute[0].bersaglio) == (0, 13)
    # e il piano continua a fare cio' per cui era stato calcolato
    assert ricevute[0].piano["T"][0] == 13


def test_b04_riepilogo_giudica_sul_bersaglio_della_sessione():
    sim = _simulatore()
    sim._sessione = SessionePratica.calcola(0, 13)
    sim._p_deck = [0] * 27
    mazzo = list(range(27))
    for sigla in sim._sessione.piano["mescolamenti"]:
        mazzo = gr.raccogli(gr.distribuisci(mazzo), sigla)
    sim._p_deck = mazzo
    sim._target_var.set(25)                   # cambiato a pratica iniziata

    sim._show_practice_summary()
    testo = "".join(sim._p_log.parti)
    assert "13" in testo
    assert "25" not in testo, "il campo modificato non deve entrare nel giudizio"


def test_b04_pratica_senza_sessione_non_fa_nulla():
    sim = _simulatore()
    sim._init_practice = lambda sessione: pytest.fail("non deve partire")
    sim._practice_reset()                     # nessuna sessione: nessun effetto


@pytest.mark.parametrize("carta, bersaglio", [("", 13), ("x", 13), (0, ""),
                                              (99, 13), (0, 99), (-1, 0)])
def test_b04_input_non_validi_non_creano_sessione(carta, bersaglio):
    sim = _simulatore(carta, bersaglio)
    stato = []
    sim._status_lbl = SimpleNamespace(configure=lambda **kw: stato.append(kw))
    sim._find_sequence()
    assert sim._sessione is None
    assert stato and "✗" in stato[0]["text"]


def test_b04_reset_dimentica_la_sessione():
    sim = _simulatore()
    sim._sessione = SessionePratica.calcola(3, 7)
    fatto = []
    sim._status_lbl = SimpleNamespace(configure=lambda **kw: None)
    sim._istr_txt = sim._deck_log = _Testo()
    sim._write_placeholder_istr = lambda: fatto.append("placeholder")
    sim._phase_var = _Var(0)
    sim._phase_lbl = SimpleNamespace(configure=lambda **kw: None)
    sim._p_set_state = lambda stato: fatto.append(stato)
    sim._card_var = _Var(0)
    sim._target_var = _Var(13)

    simulator_tab.SimulatorFrame.reset(sim)
    assert sim._sessione is None and "idle" in fatto


def test_b04_tutte_le_729_coppie_restano_coerenti():
    """Il piano di ogni sessione porta la SUA carta al SUO bersaglio."""
    for carta in range(27):
        for bersaglio in range(27):
            sessione = SessionePratica.calcola(carta, bersaglio)
            assert sessione.piano["T"][sessione.carta] == sessione.bersaglio


def test_b04_i_campi_si_leggono_in_un_solo_punto():
    sorgente = (RADICE / "gioco27" / "gui" / "simulator_tab.py").read_text(
        encoding="utf-8")
    letture = sorgente.count("_card_var.get()") + sorgente.count("_target_var.get()")
    assert letture == 2, "i campi vanno letti solo in _find_sequence"


# ───────────────────────────── R05 ──────────────────────────────────────────

class AppSelftest:
    """App ridotta all'osso: coda di callback e stato testuale."""

    _ui = app_module.App._ui
    _run_selftest = app_module.App._run_selftest

    def __init__(self):
        self._closing = False
        self.status_var = _Var()
        self.coda = []
        self.mostrati = []

    def after(self, _delay, fn):
        self.coda.append(fn)

    def winfo_exists(self):
        return True

    def esegui_coda(self):
        pendenti, self.coda = list(self.coda), []
        for fn in pendenti:
            fn()


@pytest.fixture
def app_selftest(monkeypatch):
    app = AppSelftest()
    monkeypatch.setattr(app_module, "messagebox", SimpleNamespace(
        showinfo=lambda t, m, **k: app.mostrati.append(("info", t, m)),
        showerror=lambda t, m, **k: app.mostrati.append(("error", t, m))))
    monkeypatch.setattr(common, "messagebox", SimpleNamespace(
        showerror=lambda t, m: app.mostrati.append(("error", t, m))))
    return app


def _esegui_selftest(app, monkeypatch, selftest):
    from gioco27.core import gioco_reale
    monkeypatch.setattr(gioco_reale, "selftest", selftest)
    errori_thread = []
    monkeypatch.setattr(threading, "excepthook",
                        lambda args: errori_thread.append(args.exc_value))
    thread = app._run_selftest()
    if thread is not None:
        thread.join(30)
        assert not thread.is_alive()
    app.esegui_coda()
    return errori_thread


def test_r05_successo(app_selftest, monkeypatch):
    errori = _esegui_selftest(app_selftest, monkeypatch,
                              lambda completo=True: {"esito": "TUTTO OK"})
    assert errori == []
    assert app_selftest.status_var.get().startswith("Verifica completata")
    assert app_selftest.mostrati and app_selftest.mostrati[0][0] == "info"


@pytest.mark.parametrize("eccezione", [
    None,                                     # VerificaFallita, risolta sotto
    ImportError("numpy non disponibile"),
    RuntimeError("guasto inatteso"),
    MemoryError("memoria esaurita"),
])
def test_r05_ogni_errore_produce_uno_stato_conclusivo(eccezione, app_selftest,
                                                      monkeypatch):
    from gioco27.core.gioco_reale import VerificaFallita
    exc = VerificaFallita("ancora #100") if eccezione is None else eccezione

    def rotto(completo=True):
        raise exc

    errori = _esegui_selftest(app_selftest, monkeypatch, rotto)

    assert errori == [], "nessuna eccezione deve sfuggire dal thread"
    stato = app_selftest.status_var.get()
    assert stato and "in corso" not in stato and "progress" not in stato.lower()
    assert stato != ""
    tipi = [t for t, *_ in app_selftest.mostrati]
    assert "error" in tipi, "l'utente deve vedere il fallimento"


def test_r05_lo_stato_non_resta_in_corso(app_selftest, monkeypatch):
    in_corso = []

    def rotto(completo=True):
        in_corso.append(app_selftest.status_var.get())
        raise RuntimeError("x")

    _esegui_selftest(app_selftest, monkeypatch, rotto)
    assert in_corso and "in corso" in in_corso[0]
    assert "in corso" not in app_selftest.status_var.get()


# ───────────────────────────── M03 ──────────────────────────────────────────

class _VistaSpia:
    def __init__(self):
        self.chiamate = []

    def __getattr__(self, nome):
        def registra(*a, **k):
            self.chiamate.append(nome)
        return registra


def test_m03_la_distribuzione_non_riceve_la_T():
    """Contratto: la Distribuzione e' globale, non rappresenta la T corrente."""
    app = object.__new__(app_module.App)
    cicli, distrib = _VistaSpia(), _VistaSpia()
    app._cycles_frame = cicli
    app._distrib_frame = distrib
    app._presentation_win = None

    app_module.App._notify_T_changed(app, list(range(27)))

    assert cicli.chiamate == ["set_permutation"]
    assert distrib.chiamate == [], "nessuna notifica non pertinente"
    assert app._last_T_perm == list(range(27))


def test_m03_la_distribuzione_non_espone_set_permutation():
    """La chiamata rimossa non poteva funzionare: il metodo non esiste."""
    from gioco27.gui.distribution_tab import DistributionFrame

    assert not hasattr(DistributionFrame, "set_permutation")


def test_m03_la_presentazione_riceve_la_T():
    app = object.__new__(app_module.App)
    app._cycles_frame = _VistaSpia()
    presentazione = _VistaSpia()
    app._presentation_win = presentazione
    app_module.App._notify_T_changed(app, list(range(27)))
    assert presentazione.chiamate == ["update_from_T"]


def test_m03_nessuna_eccezione_silenziata_nella_notifica():
    sorgente = (RADICE / "gioco27" / "gui" / "app.py").read_text(encoding="utf-8")
    albero = ast.parse(sorgente)
    funzione = next(n for n in ast.walk(albero)
                    if isinstance(n, ast.FunctionDef) and n.name == "_notify_T_changed")
    for handler in [n for n in ast.walk(funzione) if isinstance(n, ast.ExceptHandler)]:
        assert handler.type is not None, "except nudo"
        nome = getattr(handler.type, "attr", getattr(handler.type, "id", ""))
        assert nome != "Exception", "except Exception nella notifica"
        assert not all(isinstance(s, ast.Pass) for s in handler.body)
