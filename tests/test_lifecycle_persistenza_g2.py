"""Compartimento G2 — lifecycle dei lavori, persistenza e pubblicazione atomica.

Questo file nasce prima delle correzioni: la prima sezione descrive il
comportamento **attuale**, difetto compreso, cosi' che il commit successivo
possa dimostrare di averlo cambiato e nient'altro.

Tre cose vengono verificate qui:

* **persistenza** (R07) — `Config.save()` inghiottiva ogni errore di scrittura:
  registrava il traceback nel log e tornava come se avesse salvato. Chi chiama
  mostrava poi «lingua salvata, riavvia» o chiudeva il dialogo delle
  impostazioni, cioe' presentava un fallimento come un successo;
* **lifecycle** — i lavori asincroni reali del programma (analisi, export,
  selftest, decomposizioni, distribuzione) e i loro esiti terminali. Cancellato,
  obsoleto e fallito sono tre cose diverse e devono restare distinguibili;
* **pubblicazione** — ogni rotta che scrive un file deve lasciare la
  destinazione precedente intatta quando la generazione fallisce.

Nessun test dipende dalla velocita' della macchina o dai permessi del
filesystem: i guasti sono iniettati (i permessi POSIX non sono riproducibili su
Windows), i lavori vengono catturati e fatti avanzare esplicitamente, e dove
serve un thread vero lo si aspetta con `join`.
"""
import json
import os
import pathlib
import threading
from types import SimpleNamespace

import pytest

from gioco27.core import config as config_mod
from gioco27.core import parallel
from gioco27.core.parallel import ExportAnnullato
from gioco27.gui import analysis_tab
from gioco27.gui import app as app_module
from gioco27.services.modelli import Provenienza, RisultatoAnalisi

RADICE = pathlib.Path(__file__).resolve().parents[1]
PACCHETTO = RADICE / "gioco27"

FILTRI = [dict(p0="SCD_U", p1="SCD_U", p2="SCD_U",
               j0="I_3", j1="I_3", j2="I_3") for _ in range(3)]


# ════════════════════════════ armamentario ══════════════════════════════════

class _Var:
    """Una StringVar: si scrive e si rilegge."""

    def __init__(self, v=""):
        self._v = v

    def get(self):
        return self._v

    def set(self, v):
        self._v = v


class _Bottone:
    def __init__(self):
        self.stato = "disabled"

    def configure(self, **kw):
        self.stato = kw.get("state", self.stato)

    def __setitem__(self, k, v):
        pass

    def __getitem__(self, k):
        return None


def _boom(*_a, **_k):
    raise OSError(28, "disco pieno (iniettato)")


def _config_isolata(tmp_path, monkeypatch, sottocartella=".gioco27"):
    """Una `Config` che scrive in `tmp_path`, mai nella home dell'utente."""
    cartella = tmp_path / sottocartella
    monkeypatch.setattr(config_mod, "_CONFIG_DIR", cartella)
    monkeypatch.setattr(config_mod, "_CONFIG_FILE", cartella / "config.json")
    return config_mod.Config()


# ═════════════ R07 — il salvataggio della configurazione ════════════════════
#
# Quattro modi di fallire, uno di riuscire. Nessuno usa i permessi del
# filesystem: `chmod` non ha lo stesso effetto su Windows, e un test che li
# usasse verrebbe semplicemente saltato la' dove il programma gira di piu'.

def test_r07_salvataggio_riuscito(tmp_path, monkeypatch):
    cfg = _config_isolata(tmp_path, monkeypatch)
    cfg["language"] = "en"
    cfg.save()
    scritto = json.loads((tmp_path / ".gioco27" / "config.json")
                         .read_text(encoding="utf-8"))
    assert scritto["language"] == "en"


def test_r07_la_configurazione_e_pubblicata_atomicamente(tmp_path, monkeypatch):
    """L'atomicita' esiste gia': G2 la conserva, non la reinventa."""
    sorgente = (PACCHETTO / "core" / "config.py").read_text(encoding="utf-8")
    assert "atomic_write" in sorgente, "la primitiva comune resta quella"
    assert sorgente.count("import tempfile") == 0, "nessuna seconda implementazione"

    cfg = _config_isolata(tmp_path, monkeypatch)
    cfg["language"] = "it"
    cfg.save()
    precedente = (tmp_path / ".gioco27" / "config.json").read_bytes()

    cfg["language"] = "en"
    monkeypatch.setattr(config_mod, "json",
                        SimpleNamespace(dump=_boom, load=json.load))
    try:
        cfg.save()
    except OSError:
        pass
    assert (tmp_path / ".gioco27" / "config.json").read_bytes() == precedente
    residui = [p.name for p in (tmp_path / ".gioco27").iterdir()]
    assert residui == ["config.json"], residui


@pytest.mark.xfail(strict=True, reason="R07: save() inghiotte l'errore e "
                                       "torna come se avesse salvato")
@pytest.mark.parametrize("nome,inietta", [
    ("cartella non creabile", None),
    ("errore durante la scrittura", "dump"),
    ("errore durante la pubblicazione", "replace"),
    ("destinazione non scrivibile", "apertura"),
])
def test_r07_il_fallimento_arriva_al_chiamante(nome, inietta, tmp_path,
                                               monkeypatch):
    """Un salvataggio fallito deve essere distinguibile da uno riuscito.

    Prima di G2 il traceback finiva nel log e basta: nessun chiamante poteva
    accorgersene senza leggere il file di log. Il contratto scelto e' quello
    gia' usato nel resto del programma — un'eccezione applicativa esplicita —
    quindi il test chiede un `OSError`, che e' cio' che l'errore nuovo e'.
    """
    if inietta is None:
        # Un file al posto della cartella: mkdir fallisce su Windows e su Linux
        # allo stesso modo, senza toccare i permessi.
        (tmp_path / "ostacolo").write_text("non sono una cartella")
        cfg = _config_isolata(tmp_path, monkeypatch,
                              sottocartella="ostacolo/.gioco27")
    else:
        cfg = _config_isolata(tmp_path, monkeypatch)
        if inietta == "dump":
            monkeypatch.setattr(config_mod, "json",
                                SimpleNamespace(dump=_boom, load=json.load))
        elif inietta == "replace":
            monkeypatch.setattr(os, "replace", _boom)
        else:
            monkeypatch.setattr(config_mod, "atomic_write", _boom)

    with pytest.raises(OSError):
        cfg.save()


@pytest.mark.xfail(strict=True, reason="R07: la preferenza di lingua annuncia "
                                       "«riavvia» anche quando non ha salvato")
def test_r07_la_gui_non_dichiara_successo_dopo_il_fallimento(tmp_path,
                                                             monkeypatch):
    """La preferenza di lingua: se il salvataggio fallisce, niente «riavvia».

    E' il falso successo che G2 deve eliminare. Il test e' scritto sul metodo
    reale di `App`, non su una copia.
    """
    cfg = _config_isolata(tmp_path, monkeypatch)
    monkeypatch.setattr(config_mod, "atomic_write", _boom)

    mostrati = []
    monkeypatch.setattr(app_module, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: mostrati.append(("info", a)),
        showerror=lambda *a, **k: mostrati.append(("errore", a)),
        showwarning=lambda *a, **k: mostrati.append(("avviso", a)),
        askyesno=lambda *a, **k: True))

    finto = SimpleNamespace(_cfg=cfg)
    esito = app_module.App._save_language_preference(finto, "en", parent=None)

    assert esito is False, "non ha salvato: non puo' dire di averlo fatto"
    assert [tipo for tipo, _ in mostrati] == ["errore"], mostrati


# ═══════════════ lifecycle — i lavori asincroni reali ═══════════════════════
#
# L'inventario e' in G2_LIFECYCLE_PERSISTENCE_CLOSED.md. Qui si fissa cio' che
# conta: per ogni famiglia di lavoro, come finisce e cosa la distingue dalle
# altre. «Annullato», «obsoleto» e «fallito» non sono sinonimi.

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


class TabG2(analysis_tab.AnalysisTabMixin):
    """Il mixin reale dell'analisi, con una coda esplicita al posto di Tk."""

    def __init__(self):
        self._closing = False
        self._analisi_revisione = 0
        self._analisi_corrente = None
        self._analisi_risultati = []
        self._analisi_righe_raw = []
        self._analisi_status = _Var()
        self._analisi_exp_mb = _Bottone()
        self._analisi_exp_menu = SimpleNamespace(
            entryconfigure=lambda *a, **k: None)
        self._analisi_voci_grezzi = (4, 5)
        self.progress = {}
        self.coda = []
        self.pubblicati = []

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
        self.pubblicati.append((list(risultati), n_tot))
        self._analisi_aggiorna_export()


def _risultato(aggregati=({"n_sim": 1},), totale=1):
    return RisultatoAnalisi(origine=Provenienza.FILTRI,
                            aggregati=tuple(aggregati), totale=totale)


@pytest.fixture
def tab(monkeypatch):
    t = TabG2()
    lavori = []
    monkeypatch.setattr(analysis_tab, "run_in_thread",
                        lambda widget, job, **kw: lavori.append(
                            _Lavoro(job, kw.get("on_error"))) or None)
    monkeypatch.setattr(analysis_tab, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: None, showwarning=lambda *a, **k: None,
        showerror=lambda *a, **k: None, askyesno=lambda *a, **k: True))
    t.lavori = lavori
    return t


def test_lifecycle_analisi_obsoleta_finisce_ma_non_pubblica(tab, monkeypatch):
    """Il principio di C: una richiesta vecchia puo' terminare, non pubblicare."""
    visto = {"interrogato": 0}

    class ServizioLento:
        def pianifica(self, filtri):
            from gioco27.core.analisi import PianoAnalisi
            return PianoAnalisi(combinazioni=1, grezzi=True)

        def da_filtri(self, filtri, *, piano=None, progresso=None,
                      ancora_valida=None):
            visto["interrogato"] += 1
            if ancora_valida is not None and not ancora_valida():
                return None                      # obsoleto: si ferma da solo
            return _risultato()

    monkeypatch.setattr(analysis_tab, "SERVIZIO", ServizioLento())
    tab._run_analisi()
    tab._analisi_nuova_revisione()               # arriva una richiesta piu' nuova
    tab.lavori[0].esegui()
    tab.esegui_coda()

    assert visto["interrogato"] == 1, "il lavoro e' comunque partito"
    assert tab.pubblicati == [], "ma non ha pubblicato nulla"
    assert tab.lavori[0].errore is None, "obsoleto non e' un errore"


def test_lifecycle_analisi_fallita_e_un_errore(tab, monkeypatch):
    """Fallito: l'eccezione esce, `on_error` la vede. Diverso da obsoleto."""

    class ServizioRotto:
        def pianifica(self, filtri):
            from gioco27.core.analisi import PianoAnalisi
            return PianoAnalisi(combinazioni=1, grezzi=True)

        def da_filtri(self, *a, **k):
            raise RuntimeError("guasto nel motore")

    monkeypatch.setattr(analysis_tab, "SERVIZIO", ServizioRotto())
    tab._run_analisi()
    tab.lavori[0].esegui()
    tab.esegui_coda()

    assert isinstance(tab.lavori[0].errore, RuntimeError)
    assert tab.pubblicati == []


def test_lifecycle_analisi_completata_pubblica(tab, monkeypatch):
    class ServizioBuono:
        def pianifica(self, filtri):
            from gioco27.core.analisi import PianoAnalisi
            return PianoAnalisi(combinazioni=3, grezzi=True)

        def da_filtri(self, filtri, *, piano=None, progresso=None,
                      ancora_valida=None):
            return _risultato(totale=3)

    monkeypatch.setattr(analysis_tab, "SERVIZIO", ServizioBuono())
    tab._run_analisi()
    tab.lavori[0].esegui()
    tab.esegui_coda()

    assert tab.pubblicati and tab.pubblicati[0][1] == 3
    assert tab.lavori[0].errore is None


# ─────────────────────── export: annullato ≠ fallito ────────────────────────

class AppG2:
    """I metodi reali di `App` che governano il ciclo di un export."""

    _run_generation = app_module.App._run_generation
    _annulla_export = app_module.App._annulla_export
    _fine_export = app_module.App._fine_export
    _run_selftest = app_module.App._run_selftest

    def __init__(self):
        self._closing = False
        self._export_busy = False
        self._export_stop = threading.Event()
        self._btn_annulla = _Bottone()
        self.progress = {}
        self.status_var = _Var()
        self.coda = []

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


@pytest.fixture
def applicazione(monkeypatch, tmp_path):
    a = AppG2()
    lavori = []
    monkeypatch.setattr(app_module, "run_in_thread",
                        lambda widget, job, **kw: lavori.append(
                            _Lavoro(job, kw.get("on_error"))) or None)
    monkeypatch.setattr(app_module, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: None, showwarning=lambda *a, **k: None,
        showerror=lambda *a, **k: a.coda.append(lambda: None),
        askyesno=lambda *a, **k: True))
    monkeypatch.setattr(app_module.filedialog, "asksaveasfilename",
                        lambda **kw: str(tmp_path / "uscita.csv"))
    monkeypatch.setattr(app_module, "get_config", lambda: SimpleNamespace(
        effective_n_workers=1, get=lambda *a: False))
    a.lavori = lavori
    a.destinazione = tmp_path / "uscita.csv"
    return a


def test_lifecycle_export_annullato_non_e_un_guasto(applicazione):
    """`ExportAnnullato` chiude il lavoro senza errore e senza toccare il file."""
    applicazione.destinazione.write_text("precedente", encoding="utf-8")

    def genera(path, filters, **kw):
        raise ExportAnnullato(3, 10)

    applicazione._run_generation(gen_func=genera, kind="CSV", unit="riga",
                                 unit_plural="righe", step=1, dialog_kw={})
    assert applicazione._export_busy is True
    applicazione.lavori[0].esegui()
    applicazione.esegui_coda()

    assert applicazione.lavori[0].errore is None, "annullato non e' fallito"
    assert applicazione._export_busy is False, "stato terminale raggiunto"
    assert applicazione.destinazione.read_text(encoding="utf-8") == "precedente"


def test_lifecycle_export_fallito_libera_comunque_lo_stato(applicazione):
    """Fallito: l'errore esce, ma il lavoro raggiunge lo stato terminale."""

    def genera(path, filters, **kw):
        raise RuntimeError("guasto nel generatore")

    applicazione._run_generation(gen_func=genera, kind="CSV", unit="riga",
                                 unit_plural="righe", step=1, dialog_kw={})
    applicazione.lavori[0].esegui()
    applicazione.esegui_coda()

    assert isinstance(applicazione.lavori[0].errore, RuntimeError)
    assert applicazione._export_busy is False


def test_lifecycle_annullamento_e_una_richiesta_di_fermarsi(applicazione):
    """Annullare chiede al lavoro di smettere: e' diverso dal renderlo obsoleto."""
    visto = {}

    def genera(path, filters, *, annullato, **kw):
        visto["prima"] = annullato()
        applicazione._annulla_export()
        visto["dopo"] = annullato()
        return 0

    applicazione._run_generation(gen_func=genera, kind="CSV", unit="riga",
                                 unit_plural="righe", step=1, dialog_kw={})
    applicazione.lavori[0].esegui()
    applicazione.esegui_coda()

    assert visto == {"prima": False, "dopo": True}


def test_lifecycle_un_solo_export_alla_volta(applicazione):
    """`_export_busy` e' l'esclusione mutua, non uno stato del lavoro."""
    applicazione._export_busy = True
    chiamate = []
    applicazione._run_generation(gen_func=lambda *a, **k: chiamate.append(1),
                                 kind="CSV", unit="riga", unit_plural="righe",
                                 step=1, dialog_kw={})
    assert chiamate == [] and applicazione.lavori == []


# ───────────────────────── selftest: R05 non regredisce ─────────────────────

@pytest.mark.parametrize("guasto,atteso", [
    (None, "completata"),
    (AssertionError("incoerenza"), "fallita"),
    (ImportError("numpy assente"), "fallita"),
    (RuntimeError("guasto"), "fallita"),
    (MemoryError(), "fallita"),
])
def test_lifecycle_selftest_finisce_sempre(guasto, atteso, monkeypatch):
    """R05: nessun esito lascia la UI con «verifica in corso»."""
    a = AppG2()
    lavori = []
    monkeypatch.setattr(app_module, "run_in_thread",
                        lambda widget, job, **kw: lavori.append(
                            _Lavoro(job, kw.get("on_error"))) or None)
    monkeypatch.setattr(app_module, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: None, showerror=lambda *a, **k: None))

    from gioco27.core import gioco_reale

    def finto_selftest():
        if guasto is not None:
            raise guasto
        return {"ok": True}

    monkeypatch.setattr(gioco_reale, "selftest", finto_selftest)
    monkeypatch.setattr(app_module, "format_selftest_report",
                        lambda r: "rapporto")

    a._run_selftest()
    assert a.status_var.get(), "lo stato «in corso» e' stato impostato"
    lavori[0].esegui()
    a.esegui_coda()

    stato = a.status_var.get()
    assert stato and "corso" not in stato.lower() and "running" not in stato.lower()
    from gioco27.i18n import tr
    assert stato == tr("status.integrity_completed" if atteso == "completata"
                       else "status.integrity_failed")


# ────────────────── decomposizioni: obsolescenza per identita' ──────────────

class FinestraG2:
    """Il polling reale della ricerca decomposizioni, senza Tk."""

    from gioco27.gui import decomposition as _d
    _poll_progress = _d.DecompositionDialog._poll_progress
    del _d

    def __init__(self):
        self._search_id = 0
        self._results = []
        self.riprogrammazioni = 0
        self.accettati = []
        self._progress_bar = {}
        self._progress_lbl = _Bottone()
        self._status_var = _Var()
        self._export_mb = _Bottone()
        self.ridisegni = 0

    def winfo_exists(self):
        return True

    def after(self, _ms, _fn):
        self.riprogrammazioni += 1

    def _accept_results(self, target, inverse, results):
        self.accettati.append(list(results))
        self._results = list(results)

    def _redisplay(self):
        self.ridisegni += 1


def test_lifecycle_decomposizione_obsoleta_non_pubblica():
    """Stessa semantica dell'analisi, scritta una seconda volta.

    Due contatori monotoni indipendenti: e' la duplicazione che G2 consolida.
    Il test fissa il comportamento, non l'implementazione.
    """
    import queue

    f = FinestraG2()
    f._search_id = 2                    # una ricerca piu' nuova e' gia' partita
    coda = queue.Queue()
    coda.put(("DONE", [((1, 2, 3), (4, 5, 6), (7, 8, 9))]))

    f._poll_progress(1, (0,) * 27, False, coda)

    assert f.accettati == [], "una risposta obsoleta non pubblica"
    assert f.riprogrammazioni == 0, "e non si riprogramma"


def test_lifecycle_decomposizione_corrente_pubblica():
    import queue

    f = FinestraG2()
    f._search_id = 1
    coda = queue.Queue()
    coda.put(("DONE", [((1, 2, 3), (4, 5, 6), (7, 8, 9))]))

    f._poll_progress(1, (0,) * 27, False, coda)

    assert len(f.accettati) == 1 and f.ridisegni == 1
    assert f._export_mb.stato == "normal"


# ══════════════════ pubblicazione: la destinazione precedente ═══════════════

def test_una_scrittura_fallita_non_tocca_il_file_precedente(tmp_path):
    """Il contratto della primitiva comune, su cui G2 porta le rotte residue."""
    dest = tmp_path / "uscita.txt"
    dest.write_text("precedente", encoding="utf-8")
    with pytest.raises(RuntimeError):
        with parallel.atomic_write(dest, "w", encoding="utf-8") as f:
            f.write("nuovo, ma incompleto")
            raise RuntimeError("guasto a meta' generazione")
    assert dest.read_text(encoding="utf-8") == "precedente"
    assert [p.name for p in tmp_path.iterdir()] == ["uscita.txt"]
