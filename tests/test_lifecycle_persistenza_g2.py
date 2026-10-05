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
import contextlib
import json
import os
import pathlib
import sys
import threading
from types import SimpleNamespace

import pytest

from gioco27.core import config as config_mod
from gioco27.core import parallel
from gioco27.core.parallel import ExportAnnullato
from gioco27.gui import analysis_tab
from gioco27.gui import app as app_module
from gioco27.services import Revisioni
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

    with pytest.raises(config_mod.ConfigNonSalvata) as errore:
        cfg.save()

    exc = errore.value
    assert isinstance(exc, OSError), "resta un errore di I/O"
    assert exc.operazione and exc.percorso and exc.causa is not None
    assert str(exc.percorso) in str(exc)
    assert exc.__cause__ is exc.causa, "la causa originale non si perde"


def test_r07_il_salvataggio_riuscito_non_solleva(tmp_path, monkeypatch):
    """Il contratto ha due esiti, non uno: riuscito e' silenzioso."""
    cfg = _config_isolata(tmp_path, monkeypatch)
    assert cfg.save() is None


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

    finto = SimpleNamespace(
        _cfg=cfg,
        _segnala_config_non_salvata=lambda exc, parent: (
            app_module.App._segnala_config_non_salvata(finto, exc, parent)))
    esito = app_module.App._save_language_preference(finto, "en", parent=None)

    assert esito is False, "non ha salvato: non puo' dire di averlo fatto"
    assert [tipo for tipo, _ in mostrati] == ["errore"], mostrati


def test_r07_ogni_salvataggio_nella_gui_e_gestito():
    """G2-G2: nessun `save()` nella GUI lascia passare un fallimento in silenzio.

    Due soli esiti ammessi per ciascun punto di chiamata: l'errore viene
    mostrato, oppure e' deliberatamente ignorato in un contesto dove non c'e'
    nulla da annunciare (avvio e chiusura). Cio' che non e' ammesso e' che il
    fallimento passi inosservato mentre la UI dichiara di aver salvato.
    """
    import ast

    albero = ast.parse((PACCHETTO / "gui" / "app.py").read_text(encoding="utf-8"))
    genitori = {}
    for nodo in ast.walk(albero):
        for figlio in ast.iter_child_nodes(nodo):
            genitori[figlio] = nodo

    salvataggi = [n for n in ast.walk(albero)
                  if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute) and n.func.attr in ("save", "commit")
                  and isinstance(n.func.value, ast.Attribute)
                  and n.func.value.attr == "_cfg"]
    assert len(salvataggi) == 4, f"punti di salvataggio: {len(salvataggi)}"

    for chiamata in salvataggi:
        nodo, protetto = chiamata, False
        while nodo in genitori:
            nodo = genitori[nodo]
            if isinstance(nodo, ast.Try) and nodo.handlers:
                protetto = True
                break
        assert protetto, ast.dump(chiamata)[:80]


def test_r07_il_dialogo_impostazioni_non_si_chiude_se_non_ha_salvato():
    """`do_save` chiude il dialogo solo dopo un salvataggio riuscito.

    Il dialogo vive dentro `_open_settings` e si costruisce con widget veri:
    qui si verifica la forma del flusso, che e' esattamente cio' che decide
    se un fallimento viene presentato come un successo.
    """
    import ast

    albero = ast.parse((PACCHETTO / "gui" / "app.py").read_text(encoding="utf-8"))
    do_save = next(n for n in ast.walk(albero)
                   if isinstance(n, ast.FunctionDef) and n.name == "do_save")

    prove = [n for n in do_save.body if isinstance(n, ast.Try)]
    assert len(prove) == 1, "un solo blocco protetto attorno al salvataggio"
    prova = prove[0]

    def chiamate(nodo):
        return {n.func.attr for n in ast.walk(nodo)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}

    assert "commit" in chiamate(prova)
    assert "destroy" not in chiamate(prova), "chiudere non fa parte del tentativo"
    assert any(isinstance(n, ast.Return) for h in prova.handlers
               for n in ast.walk(h)), "il fallimento interrompe il flusso"
    indice = do_save.body.index(prova)
    coda = do_save.body[indice + 1:]
    assert any("destroy" in chiamate(n) for n in coda), \
        "il dialogo si chiude solo dopo il tentativo riuscito"


# ═══════════════ lifecycle — i lavori asincroni reali ═══════════════════════
#
# L'inventario e' in docs/history/G2_LIFECYCLE_PERSISTENCE_CLOSED.md. Qui si fissa cio' che
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
        self._ricerche = Revisioni()
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
    f._ricerche = Revisioni(2)          # una ricerca piu' nuova e' gia' partita
    coda = queue.Queue()
    coda.put(("DONE", [((1, 2, 3), (4, 5, 6), (7, 8, 9))]))

    f._poll_progress(1, (0,) * 27, False, coda)

    assert f.accettati == [], "una risposta obsoleta non pubblica"
    assert f.riprogrammazioni == 0, "e non si riprogramma"


def test_lifecycle_decomposizione_corrente_pubblica():
    import queue

    f = FinestraG2()
    f._ricerche = Revisioni(1)
    coda = queue.Queue()
    coda.put(("DONE", [((1, 2, 3), (4, 5, 6), (7, 8, 9))]))

    f._poll_progress(1, (0,) * 27, False, coda)

    assert len(f.accettati) == 1 and f.ridisegni == 1
    assert f._export_mb.stato == "normal"


# ═══════════════ la primitiva condivisa: identita' delle richieste ══════════

def test_revisioni_e_monotona():
    r = Revisioni()
    assert r.corrente == 0
    prima, seconda = r.nuova(), r.nuova()
    assert (prima, seconda) == (1, 2)
    assert r.e_corrente(seconda) and not r.e_corrente(prima)


def test_revisioni_e_sicura_fra_thread():
    """`nuova()` e' «leggi, incrementa, scrivi»: il GIL non basta.

    Niente sleep: i thread partono insieme con una barriera e si aspettano
    con join. Il test fallisce se due richieste ricevono la stessa identita'.
    """
    r = Revisioni()
    n_thread, per_thread = 8, 200
    partenza = threading.Barrier(n_thread)
    raccolti = []
    lucchetto = threading.Lock()

    def corri():
        partenza.wait(10)
        miei = [r.nuova() for _ in range(per_thread)]
        with lucchetto:
            raccolti.extend(miei)

    thread = [threading.Thread(target=corri) for _ in range(n_thread)]
    for t in thread:
        t.start()
    for t in thread:
        t.join(20)
        assert not t.is_alive()

    atteso = n_thread * per_thread
    assert len(raccolti) == atteso
    assert len(set(raccolti)) == atteso, "due richieste con la stessa identita'"
    assert r.corrente == atteso


def test_la_revisione_non_e_un_annullamento():
    """G2-G5: due nozioni separate, e devono restare separate.

    `Revisioni` non ha modo di chiedere a un lavoro di fermarsi, e il
    contratto di annullamento (`annullato() -> bool`, `ExportAnnullato`) vive
    nel core e non sa nulla di revisioni. Fonderle in un unico booleano
    perderebbe la distinzione introdotta in C: una richiesta superata
    continua e viene scartata, non viene interrotta.
    """
    r = Revisioni()
    for metodo in ("annulla", "cancel", "stop", "set", "is_set"):
        assert not hasattr(r, metodo), metodo
    assert set(dir(parallel)) >= {"mai_annullato", "ExportAnnullato"}
    assert parallel.mai_annullato() is False

    sorgente = (RADICE / "gioco27" / "services" / "lavoro.py").read_text(
        encoding="utf-8")
    assert "threading" in sorgente
    assert "tkinter" not in sorgente and "gioco27.gui" not in sorgente


def test_le_due_schede_condividono_la_primitiva():
    """Nessun contatore monotono scritto a mano resta nella presentation."""
    import ast

    for rel in ("gui/analysis_tab.py", "gui/decomposition.py"):
        sorgente = (PACCHETTO / rel).read_text(encoding="utf-8")
        assert "Revisioni" in sorgente, rel
        albero = ast.parse(sorgente)
        incrementi = [n for n in ast.walk(albero)
                      if isinstance(n, ast.AugAssign)
                      and isinstance(n.op, ast.Add)
                      and isinstance(n.target, ast.Attribute)
                      and ("revision" in n.target.attr
                           or "search_id" in n.target.attr)]
        assert incrementi == [], rel
    assert "_search_id" not in (PACCHETTO / "gui" / "decomposition.py").read_text(
        encoding="utf-8")


# ═══════════════ il grafo delle importazioni: nessun ciclo ══════════════════
#
# La misura e' fatta sull'AST e conta ANCHE gli import scritti dentro una
# funzione: un import differito e' comunque una dipendenza, e nasconderlo
# dietro a un `def` non scioglie un ciclo, lo rende solo piu' difficile da
# vedere. Le uniche eccezioni sono le due facciate di compatibilita', che
# risolvono per nome e sono elencate qui sotto una per una.

def _moduli_del_pacchetto():
    for percorso in sorted(PACCHETTO.rglob("*.py")):
        yield percorso.relative_to(RADICE).as_posix(), percorso.read_text(
            encoding="utf-8")


def _nome_e_pacchetto(rel):
    """Nome del modulo e pacchetto contro cui risolvere gli import relativi.

    Per un `__init__.py` il pacchetto e' se stesso; per ogni altro modulo e'
    quello che lo contiene. Sbagliare questa distinzione fa sparire gli archi
    che partono dagli `__init__`.
    """
    nome = rel[:-3].replace("/", ".")
    if nome.endswith(".__init__"):
        nome = nome[:-len(".__init__")]
        return nome, nome
    return nome, nome.rsplit(".", 1)[0]


def _archi():
    import ast

    archi = {}
    for rel, sorgente in _moduli_del_pacchetto():
        nome, pacchetto = _nome_e_pacchetto(rel)
        fuori = set()
        for n in ast.walk(ast.parse(sorgente)):
            if isinstance(n, ast.ImportFrom):
                if n.level:
                    base = pacchetto.split(".")
                    base = base[:len(base) - (n.level - 1)] if n.level > 1 else base
                    if n.module:
                        fuori.add(".".join(base + [n.module]))
                    else:
                        # `from . import a, b`: i nomi importati SONO i moduli.
                        # Trattarli come un import del solo pacchetto farebbe
                        # sparire archi veri dal grafo.
                        fuori.update(".".join(base + [a.name]) for a in n.names)
                    continue
                fuori.add(n.module or "")
            elif isinstance(n, ast.Import):
                fuori.update(a.name for a in n.names)
        archi[nome] = {m for m in fuori if m.startswith("gioco27")} - {nome}
    noti = set(archi)
    return {k: {m for m in v if m in noti} for k, v in archi.items()}


def _cicli(archi):
    """Cicli elementari, ciascuno contato una volta dal suo nodo minimo."""
    trovati = set()

    def esplora(inizio, nodo, cammino, visti):
        for d in sorted(archi.get(nodo, ())):
            if d == inizio:
                trovati.add(tuple(cammino))
            elif d not in visti and d > inizio:
                esplora(inizio, d, cammino + [d], visti | {d})

    for nodo in sorted(archi):
        esplora(nodo, nodo, [nodo], {nodo})
    return trovati


def test_nessun_ciclo_statico_fra_i_moduli_applicativi():
    """G2-G11/G2-G12: zero cicli, e non uno piu' lungo al posto di quello vecchio."""
    cicli = _cicli(_archi())
    leggibili = sorted(" -> ".join(c) for c in cicli)
    assert leggibili == [], leggibili


def test_il_grafo_e_quello_atteso_attorno_all_export_csv():
    """La direzione delle frecce, non solo l'assenza di cicli."""
    archi = _archi()
    assert "gioco27.core.permutations" in archi["gioco27.core.combinations"]
    assert archi["gioco27.core.permutations"] == {
        "gioco27.core.constants", "gioco27.core.log"}
    assert {"gioco27.core.combinations", "gioco27.core.permutations"} <= \
        archi["gioco27.core.export_combinazioni"]


def test_importare_permutations_non_tira_dentro_l_enumeratore():
    """La prova che conta: a runtime, non solo nell'AST.

    Se la facciata di compatibilita' importasse davvero i moduli traslocati,
    il ciclo sarebbe ancora li' — solo spostato dentro un `def`.
    """
    import subprocess
    import sys

    codice = ("import sys, gioco27.core.permutations; "
              "print(any(m.endswith(('core.combinations', "
              "'core.export_combinazioni')) for m in sys.modules))")
    esito = subprocess.run([sys.executable, "-c", codice], cwd=str(RADICE),
                           capture_output=True, text=True, timeout=120)
    assert esito.returncode == 0, esito.stderr
    assert esito.stdout.split() == ["False"], esito.stdout


def test_i_nomi_storici_dell_export_csv_restano_importabili():
    """G2 non fa una migrazione flag-day: l'API pubblica non si sposta."""
    from gioco27.core import permutations

    for nome in ("write_csv", "write_csv_parallel"):
        funzione = getattr(permutations, nome)
        assert funzione.__module__ == "gioco27.core.export_combinazioni"
        assert nome in dir(permutations)

    from gioco27.core.permutations import write_csv          # noqa: F401
    from gioco27.core.export_combinazioni import write_csv as diretto
    assert write_csv is diretto

    with pytest.raises(AttributeError):
        permutations.nome_che_non_esiste


def test_le_facciate_di_compatibilita_sono_dichiarate():
    """Due sole, ed entrambe elencano per nome cio' che risolvono.

    Una facciata differita e' una dipendenza che il grafo statico non vede:
    l'unico modo perche' non diventi un ciclo nascosto e' che siano poche,
    dichiarate e verificate. Questo test fallisce se ne compare una terza.
    """
    import ast

    con_getattr, facciate = [], {}
    for rel, sorgente in _moduli_del_pacchetto():
        albero = ast.parse(sorgente)
        if not any(isinstance(n, ast.FunctionDef) and n.name == "__getattr__"
                   for n in albero.body):
            continue
        con_getattr.append(rel)
        traslochi = next(
            (n for n in ast.walk(albero) if isinstance(n, ast.Assign)
             and any(getattr(t, "id", "") == "_TRASLOCHI" for t in n.targets)),
            None)
        if traslochi is not None:
            facciate[rel] = {k.value for k in traslochi.value.keys}

    assert sorted(con_getattr) == ["gioco27/core/algebra.py",
                                   "gioco27/core/permutations.py",
                                   "gioco27/gui/i18n.py"], con_getattr
    # Le due facciate di traslocazione elencano per nome cio' che risolvono.
    assert facciate["gioco27/core/permutations.py"] == {
        "write_csv", "write_csv_parallel"}
    assert facciate["gioco27/core/algebra.py"] == {
        "analizza_righe", "analizza_csv", "scrivi_output", "scrivi_excel",
        "EXCEL_MAX_CELL_CHARS"}
    # `gui.i18n` non e' una traslocazione ma un proxy di un solo proprietario:
    # riesporta `gioco27.i18n` per intero, e non nasconde nessun arco perche'
    # quel proprietario e' importato in cima al file.
    assert "gioco27/gui/i18n.py" not in facciate
    assert "gioco27.i18n" in _archi()["gioco27.gui.i18n"]


def test_la_matematica_non_si_e_spostata():
    """Il ciclo si e' sciolto spostando l'orchestrazione, non i conti."""
    from gioco27.core import permutations

    for nome in ("compute_stage", "compute_R", "compute_T_perm",
                 "compute_T_full", "compose3", "build_P27", "build_J27",
                 "perm_to_mat3", "mat_to_perm27", "make_csv_row"):
        assert getattr(permutations, nome).__module__ == \
            "gioco27.core.permutations", nome
    assert permutations.CSV_HEADER[0] == "#"


# ══════════════════ pubblicazione: la destinazione precedente ═══════════════

def test_nessuna_rotta_pubblica_scrive_direttamente_il_file_finale():
    """Censimento: `open(..., "w")` non pubblica piu' nessun file di destinazione.

    Restano due usi dichiarati, e sono entrambi temporanei — non destinazioni:

    * `gui/protocol_dialog.py` crea un file temporaneo da aprire nel browser;
      non sostituisce nulla, e il suo residuo (M05) appartiene a H;
    * `core/pdfmerge.py` scrive il proprio temporaneo e poi lo pubblica con
      `_sostituisci`, che e' gia' una sostituzione atomica.
    """
    import ast

    MODI = ("w", "wb", "a", "ab", "w+", "wb+")
    dichiarate = {"gioco27/gui/protocol_dialog.py", "gioco27/core/pdfmerge.py"}
    trovate = set()
    for rel, sorgente in _moduli_del_pacchetto():
        for n in ast.walk(ast.parse(sorgente)):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            nome = (f.id if isinstance(f, ast.Name)
                    else f.attr if isinstance(f, ast.Attribute) else "")
            if nome not in ("open", "fdopen"):
                continue
            modi = [a.value for a in n.args[1:2]
                    if isinstance(a, ast.Constant)]
            modi += [k.value.value for k in n.keywords
                     if k.arg == "mode" and isinstance(k.value, ast.Constant)]
            if any(m in MODI for m in modi):
                trovate.add(rel)
    assert trovate == dichiarate, sorted(trovate)


class _DialogoDecomposizioni:
    """I due export testuali reali della finestra decomposizioni, senza Tk."""

    from gioco27.gui import decomposition as _d
    _export_txt = _d.DecompositionDialog._export_txt
    _export_csv = _d.DecompositionDialog._export_csv
    del _d

    def __init__(self, risultati):
        self._result_context = {"target": tuple(range(27)), "inverse": False,
                                "results": risultati}


class _TavolaDelle216:
    """L'export CSV reale della tavola, senza Tk."""

    from gioco27.gui import tavola_tab as _t
    _esporta_csv = _t.TavolaFrame._esporta_csv
    del _t

    def __init__(self, righe):
        self._righe = righe


def _riga_tavola(numero):
    return {"numero": numero, "mescolamenti": ("A", "B", "C"),
            "impilamenti": ("D", "E", "F"), "assi": (1, 2, 3),
            "periodo": 3, "punti_fissi": 0, "tipo_ciclo": (3, 3),
            "parita": 1, "autoinversa": False, "T": list(range(27))}


def _zittisci(monkeypatch, modulo, percorso, errori):
    """Sostituisce i dialoghi della rotta e raccoglie gli errori mostrati."""
    monkeypatch.setattr(modulo.filedialog, "asksaveasfilename",
                        lambda **kw: str(percorso))
    monkeypatch.setattr(modulo, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: None,
        showerror=lambda *a, **k: errori.append(a)))


def _rotte_migrate(tmp_path, monkeypatch, errori):
    """(nome, esegui, destinazione, riporta) per ogni rotta resa atomica in G2.

    `riporta` distingue le rotte della GUI — che intercettano l'OSError e lo
    mostrano — da quelle del core, che lo lasciano salire al chiamante.
    """
    import numpy as np

    from gioco27.core.group_theory import GroupData
    from gioco27.gui import decomposition, tavola_tab

    decomposizioni = [(("A", "B", "C"), ("D", "E", "F"), ("G", "H", "I"))] * 5

    def txt_decomposizioni(dest):
        _zittisci(monkeypatch, decomposition, dest, errori)
        _DialogoDecomposizioni(decomposizioni)._export_txt()

    def csv_decomposizioni(dest):
        _zittisci(monkeypatch, decomposition, dest, errori)
        _DialogoDecomposizioni(decomposizioni)._export_csv()

    def csv_tavola(dest):
        _zittisci(monkeypatch, tavola_tab, dest, errori)
        _TavolaDelle216([_riga_tavola(i) for i in range(1, 4)])._esporta_csv()

    def csv_cayley(dest):
        arr = np.array([list(range(27)), list(range(27))], dtype=np.int32)
        gd = GroupData(kron_arr=arr, kron_names=[("I", "I", "I")] * 2)
        gd.export_cayley_csv(str(dest))

    return [
        ("TXT decomposizioni", txt_decomposizioni, tmp_path / "dec.txt", True),
        ("CSV decomposizioni", csv_decomposizioni, tmp_path / "dec.csv", True),
        ("CSV tavola delle 216", csv_tavola, tmp_path / "tavola.csv", True),
        ("CSV tavola di Cayley", csv_cayley, tmp_path / "cayley.csv", False),
    ]


def test_le_rotte_migrate_scrivono_il_file(tmp_path, monkeypatch):
    errori = []
    for nome, esegui, dest, _ in _rotte_migrate(tmp_path, monkeypatch, errori):
        esegui(dest)
        assert dest.exists() and dest.stat().st_size > 0, nome
    assert errori == []


@pytest.mark.parametrize("guasto", ["generazione", "pubblicazione"])
def test_un_guasto_non_corrompe_la_destinazione(guasto, tmp_path, monkeypatch):
    """G2-G10: il file precedente resta, e nessun temporaneo sopravvive."""
    errori = []
    for nome, esegui, dest, riporta in _rotte_migrate(tmp_path, monkeypatch,
                                                      errori):
        dest.write_text("precedente", encoding="utf-8")
        prima = sorted(p.name for p in tmp_path.iterdir())
        errori.clear()

        with monkeypatch.context() as mp:
            if guasto == "generazione":
                # A meta' scrittura: il temporaneo ha gia' del contenuto e la
                # generazione si interrompe. Le quattro rotte scrivono tutte in
                # modo testo, quindi basta una stringa.
                @contextlib.contextmanager
                def a_meta(percorso, *a, **k):
                    with parallel.atomic_write(percorso, *a, **k) as f:
                        f.write("contenuto incompleto\n")
                        raise OSError(28, "disco pieno (iniettato)")

                for modulo in ("gioco27.gui.decomposition",
                               "gioco27.gui.tavola_tab",
                               "gioco27.core.group_theory"):
                    mp.setattr(sys.modules[modulo], "atomic_write", a_meta)
            else:
                mp.setattr(os, "replace", _boom)

            if riporta:
                esegui(dest)
                assert errori, f"{nome}: guasto silenzioso"
            else:
                with pytest.raises(OSError):
                    esegui(dest)

        assert dest.read_text(encoding="utf-8") == "precedente", nome
        assert sorted(p.name for p in tmp_path.iterdir()) == prima, nome


def test_l_export_multiplo_pubblica_ogni_file_atomicamente(tmp_path,
                                                           monkeypatch):
    """`ExportDialog._export_all` scrive fino a cinque file in una cartella.

    Prima di G2 erano `open(...).write(...)` senza nemmeno un `with`: un
    guasto sul terzo lasciava i primi due buoni e il terzo troncato.
    """
    from gioco27.gui import export_dialog

    class _Opzione:
        def __init__(self, v=True):
            self._v = v

        def get(self):
            return self._v

    class Dialogo:
        _export_all = export_dialog.ExportDialog._export_all

        def __init__(self, esplode_su=None):
            self._lbl = "T"
            self._perm = list(range(27))
            self._inv = list(range(27))
            self._decomps = []
            self._opt_perm = _Opzione()
            self._opt_cycles = _Opzione()
            self._opt_svg = _Opzione()
            self._opt_decomp = _Opzione(False)
            self._opt_txt = _Opzione()
            self._esplode_su = esplode_su

        def _uno(self, marca):
            if self._esplode_su == marca:
                raise OSError(28, "disco pieno (iniettato)")
            return f"contenuto {marca}"

        def _latex_perm(self, p, iv, lbl):
            return self._uno("perm")

        def _latex_cycles(self, p, lbl):
            return self._uno("cicli")

        def _svg_arrows(self, p, lbl):
            return self._uno("svg")

        def _txt_summary(self, p, iv, lbl):
            return self._uno("txt")

    monkeypatch.setattr(export_dialog.filedialog, "askdirectory",
                        lambda **kw: str(tmp_path))
    mostrati = []
    monkeypatch.setattr(export_dialog, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: mostrati.append("info"),
        showerror=lambda *a, **k: mostrati.append("errore")))

    Dialogo()._export_all()
    assert {p.name for p in tmp_path.iterdir()} == {
        "T_permutazione.tex", "T_cicli.tex", "T_frecce.svg", "T_analisi.txt"}
    assert mostrati == ["info"]
    contenuti = {p.name: p.read_text(encoding="utf-8")
                 for p in tmp_path.iterdir()}

    # Ora il terzo generatore fallisce: i due gia' pubblicati restano com'erano
    # e non compare un .svg troncato.
    mostrati.clear()
    Dialogo(esplode_su="svg")._export_all()
    assert mostrati == ["errore"]
    assert set(p.name for p in tmp_path.iterdir()) == set(contenuti)
    assert {p.name: p.read_text(encoding="utf-8")
            for p in tmp_path.iterdir()} == contenuti


# ═══════════════════════ confini architetturali di G ════════════════════════

_MUTAZIONI_TK = {"configure", "config", "set", "insert", "delete", "destroy",
                 "grid", "pack", "focus_force", "lift", "update_idletasks",
                 "entryconfigure", "after_cancel"}
#: Chi marshalla il lavoro sul thread Tk. Tutto cio' che tocca un widget deve
#: passare da qui — oppure da una coda letta dal thread Tk.
_PONTI = {"_ui", "ui_call", "after", "put", "put_nowait"}


def _funzioni_di_lavoro(albero):
    """Nomi delle funzioni avviate in un thread: `Thread(target=…)` e job."""
    import ast

    nomi = set()
    for n in ast.walk(albero):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        chiamata = (f.id if isinstance(f, ast.Name)
                    else f.attr if isinstance(f, ast.Attribute) else "")
        candidati = []
        if chiamata == "Thread":
            candidati = [k.value for k in n.keywords if k.arg == "target"]
        elif chiamata == "run_in_thread" and len(n.args) >= 2:
            candidati = [n.args[1]]
        for c in candidati:
            if isinstance(c, ast.Name):
                nomi.add(c.id)
            elif isinstance(c, ast.Attribute):
                nomi.add(c.attr)
    return nomi


def _mutazioni_proprie(nodo):
    """Le mutazioni di widget al livello di `nodo`, escluse le callable interne."""
    import ast

    interne = set()
    for n in ast.walk(nodo):
        if isinstance(n, (ast.Lambda, ast.FunctionDef)) and n is not nodo:
            interne.update(id(x) for x in ast.walk(n))
    proprie = []
    for n in ast.walk(nodo):
        if id(n) in interne or not isinstance(n, ast.Call):
            continue
        f = n.func
        if not (isinstance(f, ast.Attribute) and f.attr in _MUTAZIONI_TK):
            continue
        if isinstance(f.value, ast.Name) and f.value.id == "self":
            continue                       # self.<metodo>(): non e' un widget
        proprie.append(f.attr)
    return proprie


def test_nessun_worker_tocca_un_widget_tk():
    """G2-G6: Tk non e' thread-safe, e questo e' il modo di non scoprirlo.

    Per ogni funzione avviata in un thread — `Thread(target=…)` o job di
    `run_in_thread` — si controlla che non modifichi un widget al proprio
    livello, e che ogni callable annidata che ne modifica uno venga
    consegnata al thread Tk (`_ui`, `ui_call`, `after`) o messa in una coda
    che il thread Tk svuota.
    """
    import ast

    violazioni, esaminate = [], []
    for rel, sorgente in _moduli_del_pacchetto():
        if not rel.startswith("gioco27/gui/"):
            continue
        albero = ast.parse(sorgente)
        lavoratori = _funzioni_di_lavoro(albero)
        if not lavoratori:
            continue
        for fn in ast.walk(albero):
            if not (isinstance(fn, ast.FunctionDef) and fn.name in lavoratori):
                continue
            esaminate.append(f"{rel}:{fn.name}")
            for attr in _mutazioni_proprie(fn):
                violazioni.append(f"{rel}:{fn.name} tocca .{attr}() direttamente")

            # Cio' che viene consegnato a un ponte verso il thread Tk.
            consegnati = set()
            for n in ast.walk(fn):
                if not isinstance(n, ast.Call):
                    continue
                f = n.func
                nome = (f.id if isinstance(f, ast.Name)
                        else f.attr if isinstance(f, ast.Attribute) else "")
                if nome not in _PONTI:
                    continue
                for a in list(n.args) + [k.value for k in n.keywords]:
                    consegnati.add(id(a))
                    if isinstance(a, ast.Name):
                        consegnati.add(a.id)

            for n in ast.walk(fn):
                if not isinstance(n, (ast.Lambda, ast.FunctionDef)) or n is fn:
                    continue
                if not _mutazioni_proprie(n):
                    continue
                consegnata = id(n) in consegnati or (
                    isinstance(n, ast.FunctionDef) and n.name in consegnati)
                if not consegnata:
                    violazioni.append(
                        f"{rel}:{fn.name}: una callable che tocca widget non "
                        f"passa da {sorted(_PONTI)}")

    assert violazioni == [], violazioni
    # Il test non deve passare perche' non ha trovato nessun worker.
    assert len(esaminate) >= 7, esaminate
    assert any("_compute_worker" in e for e in esaminate)


def test_i_servizi_restano_sincroni_e_senza_gui():
    """G2-G8/G2-G13: nessun servizio crea thread, tocca Tk o importa la GUI."""
    import ast

    for rel, sorgente in _moduli_del_pacchetto():
        if not rel.startswith("gioco27/services/"):
            continue
        assert "tkinter" not in sorgente, rel
        for modulo in _archi()[_nome_e_pacchetto(rel)[0]]:
            assert not modulo.startswith("gioco27.gui"), (rel, modulo)
        albero = ast.parse(sorgente)
        creati = [n for n in ast.walk(albero) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute)
                  and n.func.attr in ("Thread", "ProcessPoolExecutor",
                                      "ThreadPoolExecutor")]
        assert creati == [], rel

    # `services/lavoro.py` e' la primitiva del lifecycle: non dipende da nulla
    # del programma, nemmeno dal core.
    assert _archi()["gioco27.services.lavoro"] == set()


def test_il_core_non_importa_i_servizi():
    """G2-G14: la direzione stabilita in G1 non si e' invertita per comodita'."""
    archi = _archi()
    for nome, dipendenze in archi.items():
        if not nome.startswith("gioco27.core"):
            continue
        for d in dipendenze:
            assert not d.startswith("gioco27.services"), (nome, d)
            assert not d.startswith("gioco27.gui"), (nome, d)


def test_il_parser_autorevole_resta_uno():
    """G2-G15: il linguaggio di E ha un solo lexer e un solo parser."""
    import ast

    definizioni = {"Lexer": [], "Parser": [], "Evaluator": []}
    for rel, sorgente in _moduli_del_pacchetto():
        for n in ast.walk(ast.parse(sorgente)):
            if isinstance(n, ast.ClassDef) and n.name in definizioni:
                definizioni[n.name].append(rel)
    for nome, dove in definizioni.items():
        assert dove == ["gioco27/core/algebra.py"], (nome, dove)


def test_g2_non_ha_inventato_uno_scheduler():
    """G2-G7: nessun framework di code o priorita' senza una necessita' reale.

    L'inventario non ha trovato nessun flusso con una semantica di priorita'
    fra lavori, ne' un punto che memorizzi o interroghi uno stato del lavoro:
    un `JobManager` o un `JobState` sarebbero stati un tipo senza lettori.
    Questo test rende esplicita la decisione, cosi' che reintrodurli sia una
    scelta e non una svista.
    """
    import ast

    vietati = {"JobManager", "GestoreLavori", "Scheduler", "Pianificatore",
               "TaskQueue", "CodaLavori", "JobState", "StatoLavoro",
               "PriorityQueue"}
    trovati = []
    for rel, sorgente in _moduli_del_pacchetto():
        for n in ast.walk(ast.parse(sorgente)):
            if isinstance(n, ast.ClassDef) and n.name in vietati:
                trovati.append(f"{rel}:{n.name}")
    assert trovati == [], trovati

    # Nel codice (non nei commenti, dove la decisione e' spiegata) la
    # primitiva non nomina code, priorita' o executor.
    albero = ast.parse(
        (PACCHETTO / "services" / "lavoro.py").read_text(encoding="utf-8"))
    identificatori = {n.id for n in ast.walk(albero) if isinstance(n, ast.Name)}
    identificatori |= {n.attr for n in ast.walk(albero)
                       if isinstance(n, ast.Attribute)}
    identificatori |= {n.name for n in ast.walk(albero)
                       if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    for parola in ("priorita", "priority", "queue", "coda", "executor", "pool"):
        assert not any(parola in i.lower() for i in identificatori), parola


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
