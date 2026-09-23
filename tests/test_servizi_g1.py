"""Compartimento G1 — modelli applicativi e confini dei servizi.

Tre cose vengono verificate qui:

* **equivalenza** — il servizio dell'analisi produce esattamente cio' che
  produceva l'orchestrazione dentro la scheda. Il percorso vecchio e' scritto
  per esteso in questo file (`_percorso_storico`) e confrontato con il nuovo su
  ingressi rappresentativi: non e' la stessa funzione chiamata due volte;
* **modello** — `RisultatoAnalisi` distingue gli stati che prima la vista
  doveva indovinare da attributi indipendenti, e non ne ammette di impossibili;
* **architettura** — la direzione delle dipendenze (`gui → services → core`),
  l'unico proprietario del modello, la facciata di compatibilita' di
  `core.algebra` e l'assenza di cicli d'importazione.

Nessun test dipende da Tk: il servizio si prova come una funzione qualunque.
"""
import ast
import importlib
import pathlib
import subprocess
import sys
from types import SimpleNamespace

import pytest

from gioco27.core.analisi import (Aggregatore, PianoAnalisi, RisultatiImport,
                                  SchemaNonRiconosciuto, aggrega_righe,
                                  analizza_csv, importa_csv, pianifica_analisi)
from gioco27.core.combinations import FiltroNonValido, iter_combinations_ex
from gioco27.core.constants import ANY
from gioco27.core.permutations import CSV_HEADER, make_csv_row
from gioco27.services import (Provenienza, Revisioni, RisultatoAnalisi,
                              ServizioAnalisi, servizio_analisi)

RADICE = pathlib.Path(__file__).resolve().parents[1]
PACCHETTO = RADICE / "gioco27"

FISSO = dict(p0="SCD_U", p1="SCD_U", p2="SCD_U", j0="I_3", j1="I_3", j2="I_3")
IDENTITA = "[" + ",".join(str(i) for i in range(27)) + "]"


def _filtri(**modifica):
    primo = dict(FISSO, **modifica)
    return [primo, dict(FISSO), dict(FISSO)]


PICCOLI = [
    ("tutto fissato", _filtri()),
    ("un parametro libero", _filtri(p0=ANY)),
    ("due parametri liberi", _filtri(p0=ANY, j0=ANY)),
    ("sottoinsieme esplicito", _filtri(p0=["SCD_U", "DCS_U", "CDS_U"])),
    ("j uniforme", _filtri(j0=ANY, j1=ANY, j2=ANY, j_uniform=True)),
]


# ═══════════════════ il percorso storico, scritto per esteso ════════════════

def _percorso_storico(filtri, *, tieni_grezzi=True):
    """Com'era l'orchestrazione dentro `gui.analysis_tab` prima di G1.

    Copiata qui apposta: il confronto serve a niente se le due strade sono la
    stessa funzione chiamata due volte.
    """
    aggregatore = Aggregatore(tieni_grezzi=tieni_grezzi, aggrega=not tieni_grezzi)
    for i, params in enumerate(iter_combinations_ex(filtri), 1):
        rd = make_csv_row(i, params)
        aggregatore.aggiungi({
            "Stage0": rd[1], "Stage1": rd[2], "Stage2": rd[3],
            "A0": rd[4], "A1": rd[5], "A2": rd[6],
            "T_simbolica": rd[7], "T_permutazione": rd[8],
        })
    risultati = (aggrega_righe(aggregatore.grezzi) if tieni_grezzi
                 else aggregatore.risultati())
    return list(risultati), aggregatore.grezzi


def _scrivi_csv(percorso, righe, intestazione=None):
    intestazione = CSV_HEADER if intestazione is None else intestazione
    testo = ";".join(f'"{c}"' for c in intestazione) + "\n"
    for riga in righe:
        testo += ";".join(f'"{c}"' for c in riga) + "\n"
    percorso.write_text(testo, encoding="utf-8")
    return percorso


def _riga_csv(perm=IDENTITA, formula="T = MSC o MSC o MSC", numero=1):
    return [str(numero), "", "", "", "", "", "", formula, perm]


@pytest.fixture
def servizio():
    return ServizioAnalisi()


# ═══════════════════════════════ equivalenza ════════════════════════════════

@pytest.mark.parametrize("nota,filtri", PICCOLI, ids=[n for n, _ in PICCOLI])
def test_equivalenza_analisi_dai_filtri(servizio, nota, filtri):
    attesi, grezzi = _percorso_storico(filtri)
    risultato = servizio.da_filtri(filtri)

    assert list(risultato.aggregati) == attesi
    assert list(risultato.grezzi) == list(grezzi)
    assert risultato.totale == servizio.pianifica(filtri).combinazioni
    assert risultato.origine == Provenienza.FILTRI == "filtri"
    assert risultato.completo and not risultato.parziale
    assert risultato.grezzi_disponibili and not risultato.grezzi_scartati


@pytest.mark.parametrize("nota,filtri", PICCOLI, ids=[n for n, _ in PICCOLI])
def test_equivalenza_modalita_aggregata(servizio, nota, filtri):
    """Sopra il limite dei grezzi gli aggregati sono gli stessi, i grezzi no."""
    attesi, _ = _percorso_storico(filtri)
    senza_grezzi, grezzi = _percorso_storico(filtri, tieni_grezzi=False)
    assert senza_grezzi == attesi and grezzi == ()

    piano = PianoAnalisi(combinazioni=servizio.pianifica(filtri).combinazioni,
                         grezzi=False)
    risultato = servizio.da_filtri(filtri, piano=piano)
    assert list(risultato.aggregati) == attesi
    assert risultato.grezzi == () and risultato.grezzi_scartati
    assert not risultato.grezzi_disponibili
    assert not risultato.completo          # qualcosa non e' stato conservato
    assert not risultato.parziale          # ma nessuna riga e' stata rifiutata


def test_equivalenza_import_csv(servizio, tmp_path):
    percorso = _scrivi_csv(tmp_path / "combinazioni.csv",
                           [_riga_csv(numero=1), _riga_csv(numero=2)])
    atteso = analizza_csv(percorso)          # il percorso storico, ancora vivo
    risultato = servizio.da_csv(percorso)

    assert list(risultato.aggregati) == list(atteso)
    assert risultato.totale == sum(r["n_sim"] for r in atteso)
    assert risultato.origine == Provenienza.CSV == "csv"
    assert risultato.grezzi == () and not risultato.grezzi_scartati
    assert "combinazioni.csv" in risultato.diagnostica


def test_equivalenza_import_parziale(servizio, tmp_path):
    percorso = _scrivi_csv(tmp_path / "misto.csv",
                           [_riga_csv(numero=1),
                            _riga_csv("[0,0,99]", numero=2),
                            _riga_csv(numero=3)])
    atteso = importa_csv(percorso)
    risultato = servizio.da_csv(percorso)

    assert list(risultato.aggregati) == list(atteso)
    assert risultato.lette == atteso.lette == 3
    assert risultato.scartate == atteso.scartate
    assert risultato.parziale and not risultato.completo
    # H1: la nota del servizio porta il nome del file e basta — «quante righe
    # sono state scartate e perche'» e' una frase, e la compone la
    # presentation dai campi `lette` e `scartate`, che restano qui interi.
    assert risultato.diagnostica == "misto.csv"
    assert [s.numero for s in risultato.scartate] == [3]


def test_import_di_schema_invalido_resta_un_errore(servizio, tmp_path):
    percorso = _scrivi_csv(tmp_path / "ignoto.csv", [["1", "2"]],
                           intestazione=["foo", "bar"])
    with pytest.raises(SchemaNonRiconosciuto):
        analizza_csv(percorso)
    with pytest.raises(SchemaNonRiconosciuto):
        servizio.da_csv(percorso)


def test_export_analisi_resta_non_importabile(servizio, tmp_path):
    """F lo ha deciso, G1 non lo cambia."""
    percorso = _scrivi_csv(
        tmp_path / "analisi.csv", [[IDENTITA, "T = MSC", "1"]],
        intestazione=["T_permutazione  [lista 0..26]",
                      "T_simboliche_distinte  [separate da , ]",
                      "n_sim_distinte"])
    with pytest.raises(SchemaNonRiconosciuto):
        servizio.da_csv(percorso)


def test_pipeline_scrive_e_restituisce_lo_stesso_risultato(servizio, tmp_path):
    ingresso = _scrivi_csv(tmp_path / "in.csv", [_riga_csv(numero=1)])
    uscita_csv = tmp_path / "out.csv"
    uscita_xlsx = tmp_path / "out.xlsx"
    risultato = servizio.pipeline_csv(ingresso, uscita_csv, uscita_xlsx)

    assert uscita_csv.exists() and uscita_xlsx.exists()
    assert risultato.origine == Provenienza.PIPELINE == "pipeline"
    assert list(risultato.aggregati) == list(servizio.da_csv(ingresso).aggregati)
    intestazione = uscita_csv.read_text(encoding="utf-8").splitlines()[0]
    assert "T_permutazione" in intestazione and "n_sim_distinte" in intestazione


def test_il_piano_e_quello_di_f(servizio):
    """Il servizio non ha una policy propria: usa quella del compartimento F."""
    filtri = _filtri(p0=ANY)
    assert servizio.pianifica(filtri) == pianifica_analisi(filtri)
    with pytest.raises(FiltroNonValido):
        servizio.pianifica([dict(FISSO), dict(FISSO)])


def test_le_soglie_non_sono_cambiate():
    from gioco27.core import analisi
    assert analisi.LIMITE_GREZZI == 100_000
    assert analisi.LIMITE_ANALISI == 1_000_000


# ═════════════════════ interruzione e avanzamento ═══════════════════════════

def test_il_servizio_si_ferma_quando_la_richiesta_non_e_piu_corrente(servizio):
    """`ancora_valida` e' l'unico modo che il servizio ha di sapere di smettere."""
    visti = []

    def valida():
        visti.append(1)
        return len(visti) <= 2          # smette al terzo controllo

    assert servizio.da_filtri(_filtri(p0=ANY), ancora_valida=valida) is None


def test_il_servizio_riporta_l_avanzamento(servizio, monkeypatch):
    monkeypatch.setattr("gioco27.services.analisi.PASSO_AVANZAMENTO", 2)
    passi = []
    risultato = servizio.da_filtri(_filtri(p0=ANY),
                                   progresso=lambda f, t: passi.append((f, t)))
    assert passi == [(2, 6), (4, 6), (6, 6)]
    assert risultato.totale == 6


def test_il_servizio_non_sa_nulla_di_thread():
    """Sincrono: chi vuole un thread se lo mette lui attorno."""
    sorgente = (PACCHETTO / "services" / "analisi.py").read_text(encoding="utf-8")
    for vietato in ("threading", "Thread", "after(", "run_in_thread"):
        assert vietato not in sorgente


# ═══════════════════════ il modello e i suoi stati ══════════════════════════

def test_stati_distinguibili():
    vuoto = RisultatoAnalisi(origine=Provenienza.CSV)
    senza_grezzi = RisultatoAnalisi(origine=Provenienza.FILTRI,
                                    aggregati=({"n_sim": 1},), totale=1,
                                    grezzi_scartati=True)
    parziale = RisultatoAnalisi(origine=Provenienza.CSV,
                                aggregati=({"n_sim": 1},), totale=1,
                                lette=2, scartate=("riga 2",))
    completo = RisultatoAnalisi(origine=Provenienza.FILTRI,
                                aggregati=({"n_sim": 1},), totale=1,
                                grezzi=({"Stage0": "x"},))

    assert vuoto.vuoto and not vuoto.parziale and vuoto.completo
    assert not senza_grezzi.vuoto and not senza_grezzi.grezzi_disponibili
    assert not senza_grezzi.completo and not senza_grezzi.parziale
    assert parziale.parziale and not parziale.completo
    assert completo.completo and completo.grezzi_disponibili
    # «nessun grezzo perche' l'origine non ne ha» != «grezzi scartati»
    assert not vuoto.grezzi_scartati and senza_grezzi.grezzi_scartati


def test_il_modello_e_congelato():
    risultato = RisultatoAnalisi(origine=Provenienza.CSV)
    with pytest.raises(Exception):
        risultato.totale = 5
    assert isinstance(risultato.aggregati, tuple)
    assert isinstance(risultato.con_nota("ciao"), RisultatoAnalisi)
    assert risultato.con_nota("ciao").diagnostica == "ciao"
    assert risultato.diagnostica == ""


def test_la_provenienza_e_un_insieme_chiuso_ma_resta_testo():
    assert [p.value for p in Provenienza] == ["filtri", "csv", "pipeline"]
    assert Provenienza.FILTRI == "filtri" and str(Provenienza.CSV) == "csv"


# ═════════════════════════ architettura di G1 ═══════════════════════════════

def _moduli():
    for percorso in sorted(PACCHETTO.rglob("*.py")):
        yield percorso.relative_to(RADICE).as_posix(), percorso.read_text(encoding="utf-8")


def _importati(rel, sorgente):
    pacchetto = rel[:-3].replace("/", ".").removesuffix(".__init__").rsplit(".", 1)[0]
    fuori = set()
    for n in ast.walk(ast.parse(sorgente)):
        if isinstance(n, ast.ImportFrom):
            if n.level:
                base = pacchetto.split(".")
                base = base[:len(base) - (n.level - 1)] if n.level > 1 else base
                modulo = ".".join(base + ([n.module] if n.module else []))
            else:
                modulo = n.module or ""
            fuori.add(modulo)
        elif isinstance(n, ast.Import):
            fuori.update(a.name for a in n.names)
    return {m for m in fuori if m.startswith("gioco27")}


def test_i_servizi_non_importano_la_gui():
    for rel, sorgente in _moduli():
        if not rel.startswith("gioco27/services/"):
            continue
        for modulo in _importati(rel, sorgente):
            assert not modulo.startswith("gioco27.gui"), (rel, modulo)
        assert "tkinter" not in sorgente, rel


def test_il_core_non_importa_i_servizi_ne_la_gui():
    for rel, sorgente in _moduli():
        if not rel.startswith("gioco27/core/"):
            continue
        for modulo in _importati(rel, sorgente):
            assert not modulo.startswith("gioco27.services"), (rel, modulo)
            assert not modulo.startswith("gioco27.gui"), (rel, modulo)


def test_il_linguaggio_non_dipende_da_servizi_o_gui():
    for nome in ("core/algebra.py", "core/espressione.py"):
        sorgente = (PACCHETTO / nome).read_text(encoding="utf-8")
        for modulo in _importati("gioco27/" + nome, sorgente):
            assert not modulo.startswith(("gioco27.gui", "gioco27.services"))


def test_importare_un_servizio_non_importa_la_gui():
    codice = ("import sys; import gioco27.services as s; "
              "print(any(m.startswith('gioco27.gui') for m in sys.modules), "
              "any(m.startswith('tkinter') for m in sys.modules))")
    esito = subprocess.run([sys.executable, "-c", codice], cwd=str(RADICE),
                           capture_output=True, text=True, timeout=120)
    assert esito.returncode == 0, esito.stderr
    assert esito.stdout.split() == ["False", "False"], esito.stdout


def test_un_solo_proprietario_del_risultato():
    """`RisultatoAnalisi` e' definito una volta sola; la scheda lo ri-esporta."""
    definizioni = []
    for rel, sorgente in _moduli():
        for n in ast.walk(ast.parse(sorgente)):
            if isinstance(n, ast.ClassDef) and n.name == "RisultatoAnalisi":
                definizioni.append(rel)
    assert definizioni == ["gioco27/services/modelli.py"], definizioni

    from gioco27.gui import analysis_tab
    from gioco27.services import modelli
    assert analysis_tab.RisultatoAnalisi is modelli.RisultatoAnalisi


def test_la_scheda_non_ricostruisce_piu_gli_aggregati():
    """Nel tab Analisi non restano chiamate al motore dell'analisi."""
    sorgente = (PACCHETTO / "gui" / "analysis_tab.py").read_text(encoding="utf-8")
    albero = ast.parse(sorgente)
    vietate = {"analizza_righe", "analizza_csv", "importa_csv", "aggrega_righe",
               "pianifica_analisi", "iter_combinations_ex", "make_csv_row",
               "Aggregatore", "normalizza_filtri"}
    chiamate = set()
    for n in ast.walk(albero):
        if isinstance(n, ast.Call):
            f = n.func
            nome = (f.id if isinstance(f, ast.Name)
                    else f.attr if isinstance(f, ast.Attribute) else None)
            if nome in vietate:
                chiamate.add(nome)
    assert chiamate == set(), chiamate


def test_il_linguaggio_non_scrive_piu_su_disco():
    """`core.algebra` non contiene piu' export: solo il linguaggio."""
    sorgente = (PACCHETTO / "core" / "algebra.py").read_text(encoding="utf-8")
    albero = ast.parse(sorgente)
    nomi = {n.name.split(".")[0] for n in ast.walk(albero)
            if isinstance(n, ast.Import) for n in n.names}
    assert "csv" not in nomi and "openpyxl" not in nomi
    for classe in ("Lexer", "Parser", "Evaluator"):
        assert f"class {classe}" in sorgente, "il linguaggio resta qui"


def test_la_facciata_di_algebra_risolve_i_nomi_traslocati():
    """I nomi storici restano importabili, con il nuovo proprietario dietro."""
    from gioco27.core import algebra
    attesi = {
        "analizza_righe": "gioco27.core.analisi",
        "analizza_csv": "gioco27.core.analisi",
        "scrivi_output": "gioco27.core.export_analisi",
        "scrivi_excel": "gioco27.core.export_analisi",
    }
    for nome, proprietario in attesi.items():
        assert getattr(algebra, nome).__module__ == proprietario
    assert algebra.EXCEL_MAX_CELL_CHARS == 32767
    assert "analizza_righe" in dir(algebra)
    with pytest.raises(AttributeError):
        algebra.simbolo_che_non_esiste


def test_la_facciata_non_ricrea_il_ciclo_di_importazione():
    """La risoluzione differita e' cio' che tiene aciclico il grafo."""
    sorgente = (PACCHETTO / "core" / "algebra.py").read_text(encoding="utf-8")
    for modulo in _importati("gioco27/core/algebra.py", sorgente):
        assert not modulo.endswith(("core.analisi", "core.export_analisi")), modulo
    assert "def __getattr__(nome):" in sorgente


def test_nessun_ciclo_fra_i_moduli_del_linguaggio_e_dell_analisi():
    archi = {}
    for rel, sorgente in _moduli():
        nome = rel[:-3].replace("/", ".").removesuffix(".__init__")
        archi[nome] = _importati(rel, sorgente) - {nome}
    interessanti = {"gioco27.core.algebra", "gioco27.core.espressione",
                    "gioco27.core.analisi", "gioco27.core.export_analisi",
                    "gioco27.services.analisi", "gioco27.services.modelli"}

    def raggiungibili(partenza):
        visti, pila = set(), [partenza]
        while pila:
            m = pila.pop()
            for d in archi.get(m, ()):
                if d not in visti:
                    visti.add(d)
                    pila.append(d)
        return visti

    for modulo in sorted(interessanti):
        assert modulo not in raggiungibili(modulo), f"ciclo che passa da {modulo}"


def test_il_ciclo_storico_combinations_permutations_e_stato_sciolto():
    """Il debito dichiarato da G1 e' stato pagato in G2.

    Era: `core.permutations` chiedeva l'enumeratore a `core.combinations`
    dentro `write_csv` e `write_csv_parallel`, mentre `core.combinations`
    usa le primitive di `core.permutations`. Spezzarlo significava spostare
    l'orchestrazione degli export, che G1 non faceva.

    Ora quelle due funzioni sono in `core.export_combinazioni` e nessun
    import — nemmeno differito dentro una funzione — porta da `permutations`
    a `combinations`. La verifica dell'intero grafo sta in
    `tests/test_lifecycle_persistenza_g2.py`.
    """
    sorgente = (PACCHETTO / "core" / "permutations.py").read_text(encoding="utf-8")
    albero = ast.parse(sorgente)
    verso_combinations = [n for n in ast.walk(albero)
                          if isinstance(n, ast.ImportFrom)
                          and n.module == "combinations"]
    assert verso_combinations == []
    assert _importati("gioco27/core/permutations.py", sorgente) == {
        "gioco27.core.constants", "gioco27.core.log"}


# ═══════════════ la scheda come adattatore (senza aprire Tk) ════════════════

class _Var:
    def __init__(self, v=""):
        self._v = v

    def get(self):
        return self._v

    def set(self, v):
        self._v = v


class TabG1:
    """Il mixin reale con una coda esplicita al posto del thread Tk."""

    def __init__(self, filtri):
        from gioco27.gui import analysis_tab
        for nome in ("_analisi_nuova_revisione", "_analisi_e_corrente",
                     "_analisi_pubblica", "_analisi_aggiorna_export",
                     "_run_analisi", "_analisi_load_csv",
                     "_analisi_csv_pipeline"):
            setattr(type(self), nome,
                    getattr(analysis_tab.AnalysisTabMixin, nome))
        self._closing = False
        # G2: il contatore monotono delle richieste e' la primitiva
        # condivisa `services.Revisioni`, non piu' un intero scritto
        # a mano nella scheda.
        self._analisi_revisioni = Revisioni()
        self._analisi_corrente = None
        self._analisi_risultati = []
        self._analisi_righe_raw = []
        self._analisi_status = _Var()
        self.progress = {}
        self.coda = []
        self.popolati = []
        self._filtri = filtri

    def _ui(self, fn):
        self.coda.append(fn)

    def esegui_coda(self):
        pendenti, self.coda = list(self.coda), []
        for fn in pendenti:
            fn()

    def update_idletasks(self):
        pass

    def _get_filters(self):
        return self._filtri

    def _analisi_populate(self, risultati, n_tot):
        self.popolati.append((list(risultati), n_tot))

    def _analisi_aggiorna_export(self):
        pass


def test_la_scheda_pubblica_cio_che_il_servizio_restituisce(monkeypatch):
    from gioco27.gui import analysis_tab
    lavori = []
    monkeypatch.setattr(analysis_tab, "run_in_thread",
                        lambda widget, job, **kw: lavori.append(job) or None)
    monkeypatch.setattr(analysis_tab, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: None, showwarning=lambda *a, **k: None,
        showerror=lambda *a, **k: None, askyesno=lambda *a, **k: True))

    tab = TabG1(_filtri(p0=ANY))
    tab._analisi_aggiorna_export = lambda: None
    tab._run_analisi()
    lavori[0]()
    tab.esegui_coda()

    atteso, grezzi = _percorso_storico(_filtri(p0=ANY))
    assert tab._analisi_risultati == atteso
    assert tab._analisi_righe_raw == list(grezzi)
    assert tab._analisi_corrente.origine == "filtri"
    assert tab.popolati == [(atteso, 6)]


def test_la_revisione_continua_a_decidere_la_pubblicazione(monkeypatch):
    from gioco27.gui import analysis_tab
    lavori = []
    monkeypatch.setattr(analysis_tab, "run_in_thread",
                        lambda widget, job, **kw: lavori.append(job) or None)
    monkeypatch.setattr(analysis_tab, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: None, showwarning=lambda *a, **k: None,
        showerror=lambda *a, **k: None, askyesno=lambda *a, **k: True))

    tab = TabG1(_filtri())
    tab._analisi_aggiorna_export = lambda: None
    tab._run_analisi()
    tab._analisi_nuova_revisione()          # una richiesta piu' nuova
    lavori[0]()                             # il lavoro vecchio finisce ora
    tab.esegui_coda()
    assert tab.popolati == [] and tab._analisi_corrente is None


def test_il_servizio_condiviso_e_quello_usato_dalla_scheda():
    from gioco27.gui import analysis_tab
    assert analysis_tab.SERVIZIO is servizio_analisi()
    assert isinstance(analysis_tab.SERVIZIO, ServizioAnalisi)


def test_i_moduli_del_servizio_si_importano_da_soli():
    """Nessun import ciclico nascosto: ogni modulo si carica isolato."""
    for nome in ("gioco27.services.modelli", "gioco27.services.analisi",
                 "gioco27.core.export_analisi", "gioco27.core.analisi"):
        assert importlib.import_module(nome) is not None


def test_risultati_import_resta_il_contratto_interno():
    """Il modello applicativo non sostituisce quello dell'import (F)."""
    esito = aggrega_righe([{"T_permutazione": IDENTITA}])
    assert isinstance(esito, RisultatiImport) and isinstance(esito, list)


# ══════ caratterizzazione: il comportamento osservabile della scheda ════════
#
# Questi test non guardano dentro: guidano la scheda vera con il core vero —
# solo Tk e i thread sono finti — e fissano cio' che l'utente ottiene. Sono
# stati scritti PRIMA dell'estrazione dei servizi e non sono cambiati dopo:
# e' la prova che G1 ha spostato responsabilita' senza spostare comportamento.

def _tab_reale(monkeypatch, filtri=None):
    from gioco27.gui import analysis_tab
    lavori, avvisi = [], []
    monkeypatch.setattr(analysis_tab, "run_in_thread",
                        lambda widget, job, **kw: lavori.append(
                            (job, kw.get("on_error"))) or None)
    monkeypatch.setattr(analysis_tab, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: avvisi.append("info"),
        showwarning=lambda *a, **k: avvisi.append("warning"),
        showerror=lambda *a, **k: avvisi.append("error"),
        askyesno=lambda *a, **k: True))
    tab = TabG1(filtri or _filtri())
    tab._analisi_aggiorna_export = lambda: None
    tab.lavori, tab.avvisi = lavori, avvisi
    return tab


def _esegui(tab, indice=0):
    """Fa avanzare il lavoro catturato, con la stessa semantica d'errore."""
    job, on_error = tab.lavori[indice]
    try:
        job()
    except Exception as exc:
        tab.errore = exc
        if on_error is not None:
            on_error(exc)
    tab.esegui_coda()


def test_caratterizzazione_analisi_dai_filtri(monkeypatch):
    tab = _tab_reale(monkeypatch, _filtri(p0=ANY))
    tab._run_analisi()
    _esegui(tab)

    # sei combinazioni, sei T distinte: una riga per permutazione
    assert len(tab._analisi_risultati) == 6
    assert {r["n_sim"] for r in tab._analisi_risultati} == {1}
    assert len(tab._analisi_righe_raw) == 6
    assert tab._analisi_corrente.origine == "filtri"
    assert tab._analisi_corrente.diagnostica == ""
    assert tab.popolati == [(tab._analisi_risultati, 6)]


def test_caratterizzazione_import_csv(monkeypatch, tmp_path):
    from gioco27.gui import analysis_tab
    percorso = _scrivi_csv(tmp_path / "combinazioni.csv",
                           [_riga_csv(numero=1), _riga_csv(numero=2)])
    tab = _tab_reale(monkeypatch)
    monkeypatch.setattr(analysis_tab.filedialog, "askopenfilename",
                        lambda **k: str(percorso))
    tab._analisi_load_csv()
    _esegui(tab)

    assert len(tab._analisi_risultati) == 1
    assert tab._analisi_risultati[0]["n_sim"] == 1      # una sola formula distinta
    assert tab._analisi_righe_raw == []
    assert tab._analisi_corrente.origine == "csv"
    assert tab._analisi_corrente.diagnostica == "combinazioni.csv"


def test_caratterizzazione_import_parziale(monkeypatch, tmp_path):
    from gioco27.gui import analysis_tab
    percorso = _scrivi_csv(tmp_path / "misto.csv",
                           [_riga_csv(numero=1),
                            _riga_csv("[0,0,99]", numero=2)])
    tab = _tab_reale(monkeypatch)
    monkeypatch.setattr(analysis_tab.filedialog, "askopenfilename",
                        lambda **k: str(percorso))
    tab._analisi_load_csv()
    _esegui(tab)

    assert len(tab._analisi_risultati) == 1
    # H1: la scheda compone la diagnostica al momento di mostrarla; il
    # risultato conserva i dati (nome del file, righe lette e scartate).
    from gioco27.gui.errori import diagnostica_import
    risultato = tab._analisi_corrente
    assert risultato.diagnostica == "misto.csv"
    assert risultato.lette == 2 and [s.numero for s in risultato.scartate] == [3]
    diagnostica = diagnostica_import(risultato)
    assert "misto.csv" in diagnostica and "riga 3" in diagnostica


def test_caratterizzazione_schema_invalido(monkeypatch, tmp_path):
    from gioco27.gui import analysis_tab
    percorso = _scrivi_csv(tmp_path / "ignoto.csv", [["1", "2"]],
                           intestazione=["foo", "bar"])
    tab = _tab_reale(monkeypatch)
    monkeypatch.setattr(analysis_tab.filedialog, "askopenfilename",
                        lambda **k: str(percorso))
    tab._analisi_load_csv()
    _esegui(tab)

    assert isinstance(tab.errore, SchemaNonRiconosciuto)
    assert tab._analisi_risultati == [] and tab._analisi_corrente is None
    assert tab.popolati == []


def test_caratterizzazione_pipeline(monkeypatch, tmp_path):
    from gioco27.gui import analysis_tab
    ingresso = _scrivi_csv(tmp_path / "in.csv", [_riga_csv(numero=1)])
    uscita = tmp_path / "out.csv"
    tab = _tab_reale(monkeypatch)
    monkeypatch.setattr(analysis_tab.filedialog, "askopenfilename",
                        lambda **k: str(ingresso))
    monkeypatch.setattr(analysis_tab.filedialog, "asksaveasfilename",
                        lambda **k: str(uscita))
    tab._analisi_csv_pipeline()
    _esegui(tab)

    assert uscita.exists() and uscita.with_suffix(".xlsx").exists()
    assert tab._analisi_corrente.origine == "pipeline"
    assert "in.csv" in tab._analisi_corrente.diagnostica
    assert tab.avvisi == ["info"]
