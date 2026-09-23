"""Compartimento G1 — modello applicativo condiviso del risultato.

La caratterizzazione del comportamento (invariata) piu' gli stati che il nuovo
modello rende distinguibili: zero risultati, grezzi non conservati, import
parziale, risultato completo.
"""
import ast
import pathlib
from types import SimpleNamespace

import pytest

from gioco27.core.analisi import Aggregatore, SchemaNonRiconosciuto, aggrega_righe
from gioco27.core.combinations import iter_combinations_ex
from gioco27.core.constants import ANY
from gioco27.core.permutations import CSV_HEADER, make_csv_row
from gioco27.services import Provenienza, RisultatoAnalisi

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
        self._analisi_revisione = 0
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
    diagnostica = tab._analisi_corrente.diagnostica
    assert "misto.csv" in diagnostica
    assert "1 righe scartate su 2" in diagnostica and "riga 3" in diagnostica


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
