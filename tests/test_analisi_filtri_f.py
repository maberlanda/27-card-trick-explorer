"""Compartimento F — ingressi e filtri hanno un contratto (B05, B06).

Un solo modello di filtro validato alimenta conteggio, enumerazione, export e
analisi: `count == iter` per costruzione, non per coincidenza.
"""
import ast
import pathlib
from types import SimpleNamespace

import pytest

from gioco27.core import combinations
from gioco27.core.algebra import analizza_csv, analizza_righe
from gioco27.core.analisi import RisultatiImport, SchemaNonRiconosciuto, importa_csv, riconosci_schema
from gioco27.core.combinations import (FiltroNonValido, N_STADI, cardinalita,
                                       count_combinations,
                                       count_combinations_ex,
                                       iter_combinations, iter_combinations_ex,
                                       normalizza_filtri)
from gioco27.core.constants import ANY, J_OPTS, P_OPTS
from gioco27.core.permutations import CSV_HEADER
from gioco27.gui import analysis_tab

RADICE = pathlib.Path(__file__).resolve().parents[1]

IDENTITA = "[" + ",".join(str(i) for i in range(27)) + "]"
FISSO = dict(p0="SCD_U", p1="SCD_U", p2="SCD_U", j0="I_3", j1="I_3", j2="I_3")
FILTRI_FISSI = [dict(FISSO) for _ in range(N_STADI)]


def _riga(perm=IDENTITA, **extra):
    riga = {"Stage0": "", "Stage1": "", "Stage2": "", "T_simbolica": "",
            "T_permutazione": perm}
    riga.update(extra)
    return riga


def _scrivi(percorso, righe, intestazione=None, bom=False, finale=True):
    """Scrive un CSV nel formato del programma (sep=;, campi fra apici)."""
    intestazione = CSV_HEADER if intestazione is None else intestazione
    corpo = ";".join(f'"{c}"' for c in intestazione) + "\n"
    for riga in righe:
        corpo += ";".join(f'"{c}"' for c in riga) + "\n"
    if not finale:
        corpo = corpo.rstrip("\n")
    testo = ("﻿" if bom else "") + corpo
    percorso.write_text(testo, encoding="utf-8")
    return percorso


def _riga_csv(perm=IDENTITA, formula="T = MSC o MSC o MSC", numero=1):
    """Una riga completa nello schema COMBINAZIONI (9 colonne)."""
    return [str(numero), "", "", "", "", "", "", formula, perm]


# ══════════════════════════ B05 — validazione della T ═══════════════════════

def test_b05_una_t_valida_entra_nei_risultati():
    esito = analizza_righe([_riga()])
    assert len(esito) == 1
    assert esito[0]["n_sim"] == 1 and esito[0]["perm_str"] == IDENTITA
    assert esito.scartate == ()


@pytest.mark.parametrize("perm,nota", [
    ("[0,0,99]",                                    "duplicati e fuori range"),
    ("[" + ",".join(str(i) for i in range(26)) + "]",            "26 elementi"),
    ("[" + ",".join(str(i) for i in range(28)) + "]",            "28 elementi"),
    ("[-1," + ",".join(str(i) for i in range(1, 27)) + "]",         "negativo"),
    ("[99," + ",".join(str(i) for i in range(1, 27)) + "]",  "valore 99"),
    ("[0,0," + ",".join(str(i) for i in range(2, 27)) + "]",       "duplicato"),
    ("[]",                                                       "lista vuota"),
    ("",                                                        "campo vuoto"),
    ("[a,b,c]",                                                    "stringhe"),
    ("[0.0," + ",".join(str(i) for i in range(1, 27)) + "]",          "float"),
    ("[True," + ",".join(str(i) for i in range(1, 27)) + "]",      "booleano"),
    ("[0,1,2]",                                                 "solo 3 valori"),
])
def test_b05_una_t_invalida_non_entra_nei_risultati(perm, nota):
    esito = analizza_righe([_riga(perm)])
    assert list(esito) == [], f"{nota}: accettata"
    assert len(esito.scartate) == 1
    scartata = esito.scartate[0]
    assert scartata.numero == 1 and scartata.campo == "T_permutazione"
    assert scartata.motivo


def test_b05_le_righe_invalide_non_spariscono():
    """Mix di valide e invalide: le buone passano, le altre si vedono."""
    esito = analizza_righe([_riga(), _riga("[0,0,99]"), _riga(), _riga("[]")])
    assert len(esito) == 1 and esito[0]["n_sim"] == 1
    assert esito.lette == 4 and len(esito.scartate) == 2
    assert [s.numero for s in esito.scartate] == [2, 4]
    assert esito.parziale
    assert "2 righe scartate su 4" in esito.diagnostica()


def test_b05_il_contratto_di_dominio_non_viene_riscritto():
    """La T passa dal validatore di D, non da un secondo controllo locale."""
    sorgente = (RADICE / "gioco27" / "core" / "analisi.py").read_text(encoding="utf-8")
    assert "from .dominio import" in sorgente
    assert "valida_permutazione" in sorgente


# ═══════════════════════ B05 — riconoscimento dello schema ══════════════════

def test_b05_schema_sconosciuto_non_e_un_analisi_vuota(tmp_path):
    percorso = _scrivi(tmp_path / "ignoto.csv", [["1", "2"]],
                       intestazione=["foo", "bar"])
    with pytest.raises(SchemaNonRiconosciuto) as errore:
        analizza_csv(percorso)
    assert "T_permutazione" in str(errore.value)


def test_b05_file_vuoto(tmp_path):
    percorso = tmp_path / "vuoto.csv"
    percorso.write_text("", encoding="utf-8")
    with pytest.raises(SchemaNonRiconosciuto):
        analizza_csv(percorso)


def test_b05_solo_intestazione_e_uno_schema_valido_senza_risultati(tmp_path):
    percorso = _scrivi(tmp_path / "vuoto_ma_valido.csv", [])
    esito = analizza_csv(percorso)
    assert list(esito) == [] and esito.scartate == ()
    assert esito.schema.nome == "combinazioni"


def test_b05_lo_schema_dell_export_analisi_viene_rifiutato_col_suo_nome(tmp_path):
    """Rileggerlo come combinazioni darebbe molteplicita' 1 ovunque."""
    percorso = _scrivi(
        tmp_path / "analisi.csv", [[IDENTITA, "T = MSC , T = J", "2"]],
        intestazione=["T_permutazione  [lista 0..26]",
                      "T_simboliche_distinte  [separate da , ]",
                      "n_sim_distinte  [molteplicita della permutazione]"])
    with pytest.raises(SchemaNonRiconosciuto) as errore:
        analizza_csv(percorso)
    assert "analisi" in str(errore.value)


def test_b05_schema_legacy_con_la_sola_t(tmp_path):
    """Un formato storico senza formula resta leggibile."""
    percorso = _scrivi(tmp_path / "solo_t.csv", [[IDENTITA], [IDENTITA]],
                       intestazione=["T_permutazione  [lista 0..26]"])
    esito = analizza_csv(percorso)
    assert len(esito) == 1 and esito[0]["n_sim"] == 1   # formula assente = una sola
    assert esito.scartate == ()


def test_b05_bom_colonne_extra_riga_corta_e_ultima_riga_senza_newline(tmp_path):
    intestazione = list(CSV_HEADER) + ["Nota  [colonna in piu']"]
    righe = [_riga_csv(numero=1) + ["innocua"],
             ["2", "", ""],                       # riga corta: T mancante
             _riga_csv(numero=3) + ["innocua"]]
    percorso = _scrivi(tmp_path / "vario.csv", righe, intestazione=intestazione,
                       bom=True, finale=False)
    esito = analizza_csv(percorso)
    assert esito.schema.nome == "combinazioni"
    assert len(esito) == 1 and esito[0]["n_sim"] == 1
    assert [s.numero for s in esito.scartate] == [3]     # 1 = intestazione


def test_b05_righe_vuote_non_contano_come_scarti(tmp_path):
    percorso = tmp_path / "con_vuote.csv"
    testo = ";".join(f'"{c}"' for c in CSV_HEADER) + "\n"
    testo += ";".join(f'"{c}"' for c in _riga_csv()) + "\n\n\n"
    percorso.write_text(testo, encoding="utf-8")
    esito = analizza_csv(percorso)
    assert len(esito) == 1 and esito.scartate == ()


def test_b05_il_numero_di_riga_e_quello_del_file(tmp_path):
    righe = [_riga_csv(numero=1), _riga_csv("[0,0,99]", numero=2),
             _riga_csv(numero=3)]
    percorso = _scrivi(tmp_path / "numeri.csv", righe)
    esito = analizza_csv(percorso)
    assert [s.numero for s in esito.scartate] == [3]
    assert "riga 3" in esito.diagnostica()


def test_b05_intestazione_riconosciuta_per_primo_token():
    schema, indici = riconosci_schema(list(CSV_HEADER))
    assert schema.nome == "combinazioni"
    assert indici["t_permutazione"] == len(CSV_HEADER) - 1
    assert indici["stage0"] == 1 and indici["t_simbolica"] == 7


# ═════════════════════ B05 — coerenza fra formula e T ═══════════════════════

def test_b05_formula_e_t_coerenti(tmp_path):
    perm = "[" + ",".join(str(x) for x in range(27)) + "]"
    percorso = _scrivi(tmp_path / "ok.csv", [_riga_csv(perm, "MSC o MSC o MSC")])
    esito = analizza_csv(percorso)
    assert len(esito) == 1 and esito.scartate == ()


@pytest.mark.parametrize("formula,nota", [
    ("MSC",                      "formula valida ma T diversa"),
    ("MSC o",                    "formula invalida (operatore finale)"),
    ("XYZ",                      "token sconosciuto"),
    ("SCD_U",                    "tipo non compatibile (permutazione di 3)"),
])
def test_b05_formula_incoerente_o_invalida_scarta_la_riga(tmp_path, formula, nota):
    percorso = _scrivi(tmp_path / "ko.csv", [_riga_csv(IDENTITA, formula)])
    esito = analizza_csv(percorso)
    assert list(esito) == [], nota
    assert len(esito.scartate) == 1
    assert esito.scartate[0].campo == "T_simbolica"


def test_b05_gli_alias_e_il_prefisso_t_restano_validi(tmp_path):
    """Il controllo usa il parser unico di E: alias e «T =» non sono errori."""
    from gioco27.core.espressione import permutazione_di
    formula = "T = (R_U x R_U x R_U) o MSC o (I_3 x I_3 x I_3)"
    perm = "[" + ",".join(str(x) for x in permutazione_di(formula)) + "]"
    percorso = _scrivi(tmp_path / "alias.csv", [_riga_csv(perm, formula)])
    esito = analizza_csv(percorso)
    assert len(esito) == 1 and esito.scartate == ()


def test_b05_la_verifica_della_formula_non_riscrive_il_parser():
    sorgente = (RADICE / "gioco27" / "core" / "analisi.py").read_text(encoding="utf-8")
    assert "from .espressione import" in sorgente
    assert "import re" not in sorgente


def test_b05_un_export_reale_si_rilegge(tmp_path):
    """Andata e ritorno sul file prodotto davvero dal programma."""
    from gioco27.core.permutations import write_csv
    filtri = [dict(FISSO, p0=ANY), dict(FISSO), dict(FISSO)]
    percorso = tmp_path / "combinazioni.csv"
    assert write_csv(percorso, filtri) == 6
    esito = analizza_csv(percorso)
    assert esito.scartate == ()
    assert sum(r["n_sim"] for r in esito) == 6


# ═════════════════════════ B06 — contratto dei filtri ═══════════════════════

@pytest.mark.parametrize("n_stadi", [0, 1, 2, 4, 5])
def test_b06_numero_di_stadi_non_supportato(n_stadi):
    filtri = [dict(FISSO) for _ in range(n_stadi)]
    for funzione in (count_combinations_ex, count_combinations,
                     lambda f: list(iter_combinations_ex(f)),
                     lambda f: list(iter_combinations(f)),
                     normalizza_filtri):
        with pytest.raises(FiltroNonValido):
            funzione(filtri)


def test_b06_il_caso_di_regressione_a_quattro_stadi():
    """Il caso che divergeva: count=6, iter=1."""
    filtri = [dict(FISSO), dict(FISSO), dict(FISSO), dict(FISSO, p0=ANY)]
    with pytest.raises(FiltroNonValido) as errore:
        count_combinations_ex(filtri)
    assert "4" in str(errore.value) and "tre stadi" in str(errore.value)
    with pytest.raises(FiltroNonValido):
        list(iter_combinations_ex(filtri))


@pytest.mark.parametrize("modifica,nota", [
    ({"pX": "SCD_U"},                 "chiave sconosciuta"),
    ({"p3": "SCD_U"},                 "chiave legacy a base 1"),
    ({"j3": "I_3"},                   "chiave legacy J"),
    ({"p0": "NON_ESISTE"},            "nome di permutazione inesistente"),
    ({"j0": "SCD_U"},                 "nome P al posto di un J"),
    ({"p0": 3},                       "tipo errato: intero"),
    ({"p0": None},                    "tipo errato: None"),
    ({"p0": True},                    "tipo errato: booleano"),
    ({"p0": []},                      "elenco vuoto"),
    ({"p0": ["SCD_U", "SCD_U"]},      "duplicato nell'elenco"),
    ({"p0": ["SCD_U", 3]},            "elenco con valore non testuale"),
    ({"j_uniform": "si"},             "j_uniform non booleano"),
])
def test_b06_valori_e_chiavi_non_ammessi(modifica, nota):
    filtri = [dict(FISSO, **modifica), dict(FISSO), dict(FISSO)]
    with pytest.raises(FiltroNonValido):
        count_combinations_ex(filtri)
    with pytest.raises(FiltroNonValido):
        list(iter_combinations_ex(filtri))


def test_b06_chiave_mancante():
    incompleto = {k: v for k, v in FISSO.items() if k != "j2"}
    with pytest.raises(FiltroNonValido) as errore:
        normalizza_filtri([incompleto, dict(FISSO), dict(FISSO)])
    assert "j2" in str(errore.value)


def test_b06_filtro_non_dizionario():
    with pytest.raises(FiltroNonValido):
        normalizza_filtri([FISSO, FISSO, ["p0"]])
    with pytest.raises(FiltroNonValido):
        normalizza_filtri(dict(FISSO))


def _famiglia_di_filtri():
    """Famiglia deterministica di filtri validi, tutti piccoli abbastanza."""
    famiglia = []
    famiglia.append(("tutto fissato", [dict(FISSO) for _ in range(3)]))
    for chiave in ("p0", "p1", "p2"):
        famiglia.append((f"{chiave} libero",
                         [dict(FISSO, **{chiave: ANY}), dict(FISSO), dict(FISSO)]))
    for chiave in ("j0", "j1", "j2"):
        famiglia.append((f"{chiave} libero",
                         [dict(FISSO), dict(FISSO, **{chiave: ANY}), dict(FISSO)]))
    famiglia.append(("due parametri liberi",
                     [dict(FISSO, p0=ANY, j0=ANY), dict(FISSO), dict(FISSO)]))
    famiglia.append(("tre parametri liberi su stadi diversi",
                     [dict(FISSO, p0=ANY), dict(FISSO, p1=ANY),
                      dict(FISSO, j2=ANY)]))
    famiglia.append(("sottoinsieme esplicito",
                     [dict(FISSO, p0=["SCD_U", "DCS_U", "CDS_U"]),
                      dict(FISSO), dict(FISSO)]))
    famiglia.append(("sottoinsieme su piu' chiavi",
                     [dict(FISSO, p0=["SCD_U", "DCS_U"], j1=["I_3", "R_U"]),
                      dict(FISSO, p2=["CSD_U", "DSC_U"]), dict(FISSO)]))
    famiglia.append(("j uniforme con j0 libero",
                     [dict(FISSO, j0=ANY, j1=ANY, j2=ANY, j_uniform=True),
                      dict(FISSO), dict(FISSO)]))
    famiglia.append(("j uniforme con j0 fissato",
                     [dict(FISSO, j_uniform=True), dict(FISSO), dict(FISSO)]))
    famiglia.append(("j uniforme su tutti gli stadi",
                     [dict(FISSO, j0=ANY, j_uniform=True) for _ in range(3)]))
    famiglia.append(("j uniforme con elenco",
                     [dict(FISSO, j0=["I_3", "R_U"], j_uniform=True),
                      dict(FISSO, p0=ANY), dict(FISSO)]))
    famiglia.append(("tutti i P liberi su uno stadio",
                     [dict(FISSO, p0=ANY, p1=ANY, p2=ANY), dict(FISSO),
                      dict(FISSO)]))
    return famiglia


FAMIGLIA = _famiglia_di_filtri()


@pytest.mark.parametrize("nota,filtri", FAMIGLIA, ids=[n for n, _ in FAMIGLIA])
def test_b06_count_uguale_a_iter(nota, filtri):
    atteso = count_combinations_ex(filtri)
    enumerate_ = list(iter_combinations_ex(filtri))
    assert atteso == len(enumerate_), nota
    # gli stessi filtri, letti dai nomi storici: stesso contratto
    assert count_combinations(filtri) == atteso
    assert len(list(iter_combinations(filtri))) == atteso
    # ogni combinazione e' fatta di tre stadi da sei nomi ammessi
    for combinazione in enumerate_:
        assert len(combinazione) == N_STADI
        for stadio in combinazione:
            assert len(stadio) == 6
            assert all(n in P_OPTS for n in stadio[:3])
            assert all(n in J_OPTS for n in stadio[3:])


@pytest.mark.parametrize("nota,filtri", FAMIGLIA, ids=[n for n, _ in FAMIGLIA])
def test_b06_nessuna_combinazione_ripetuta(nota, filtri):
    prodotte = [tuple(tuple(s) for s in c) for c in iter_combinations_ex(filtri)]
    assert len(set(prodotte)) == len(prodotte)


def test_b06_j_uniforme_produce_solo_triple_uguali():
    filtri = [dict(FISSO, j0=ANY, j1=ANY, j2=ANY, j_uniform=True),
              dict(FISSO), dict(FISSO)]
    for combinazione in iter_combinations_ex(filtri):
        j0, j1, j2 = combinazione[0][3:]
        assert j0 == j1 == j2


def test_b06_ordine_di_emissione_invariato():
    """La numerazione «Combinazione #N» di CSV e PDF dipende da quest'ordine."""
    import itertools
    filtri = [{"p0": ANY, "p1": "SCD_U", "p2": "SDC_U",
               "j0": ANY, "j1": ANY, "j2": "I_3"} for _ in range(3)]

    def scelte(valore, opzioni):
        return opzioni if valore == ANY else [valore]

    assi = [scelte(filtri[s][k], P_OPTS if k[0] == "p" else J_OPTS)
            for s in range(3) for k in ("p0", "p1", "p2", "j0", "j1", "j2")]
    attese = [[c[0:6], c[6:12], c[12:18]] for c in itertools.product(*assi)]
    prodotte = [[tuple(s) for s in c] for c in iter_combinations_ex(filtri)]
    assert prodotte == [[tuple(s) for s in c] for c in attese]


def test_b06_il_conteggio_non_enumera(monkeypatch):
    """Contare e' un prodotto di lunghezze: l'iteratore non viene toccato."""
    def esplode(*args, **kwargs):
        raise AssertionError("enumerazione avviata per contare")

    monkeypatch.setattr(combinations, "_combinazioni", esplode)
    assert count_combinations_ex(FILTRI_FISSI) == 1
    liberi = [{k: ANY for k in FISSO} for _ in range(3)]
    assert count_combinations_ex(liberi) == 5_159_780_352


def test_b06_un_solo_contratto_alimenta_tutti():
    """Conteggio, enumerazione, export e analisi passano dalla stessa porta."""
    sorgente = (RADICE / "gioco27" / "core" / "combinations.py").read_text(
        encoding="utf-8")
    albero = ast.parse(sorgente)
    for nome in ("iter_combinations", "count_combinations",
                 "iter_combinations_ex", "count_combinations_ex"):
        funzione = next(n for n in albero.body
                        if isinstance(n, ast.FunctionDef) and n.name == nome)
        chiamate = {c.func.id for c in ast.walk(funzione)
                    if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
        assert "normalizza_filtri" in chiamate, nome


def test_b06_il_filtro_normalizzato_e_immutabile():
    filtri = normalizza_filtri(FILTRI_FISSI)
    with pytest.raises(Exception):
        filtri[0].j_uniform = True
    assert cardinalita(filtri) == 1


# ═════════════════════════ R01 — la scheda Analisi ══════════════════════════

class _Var:
    def __init__(self, v=""):
        self._v = v

    def get(self):
        return self._v

    def set(self, v):
        self._v = v


class _Menu:
    def entryconfigure(self, *a, **k):
        pass


class _MenuButton:
    def configure(self, **k):
        pass

    def __setitem__(self, k, v):
        pass

    def __getitem__(self, k):
        return None


class TabF(analysis_tab.AnalysisTabMixin):
    """Il mixin reale, con una coda esplicita al posto del thread Tk."""

    def __init__(self, filtri=None):
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
        self._filtri = filtri or FILTRI_FISSI

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
        self._analisi_status.set(f"riepilogo {n_tot}")
        self._analisi_aggiorna_export()


@pytest.fixture
def tab(monkeypatch):
    t = TabF()
    lavori, avvisi = [], []
    monkeypatch.setattr(analysis_tab, "run_in_thread",
                        lambda widget, job, **kw: lavori.append(job) or None)
    monkeypatch.setattr(analysis_tab, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: avvisi.append(("info", a)),
        showwarning=lambda *a, **k: avvisi.append(("warning", a)),
        showerror=lambda *a, **k: avvisi.append(("error", a)),
        askyesno=lambda *a, **k: True))
    t.lavori, t.avvisi = lavori, avvisi
    return t


# ═════════════════════ contratti degli altri compartimenti ══════════════════

def test_f_non_tocca_i_contratti_di_c():
    """RisultatoAnalisi, revisioni e SessionePratica restano quelli di C."""
    from gioco27.gui.analysis_tab import RisultatoAnalisi
    from gioco27.gui.simulator_tab import SessionePratica
    campi = [c.name for c in RisultatoAnalisi.__dataclass_fields__.values()]
    assert campi == ["revisione", "origine", "aggregati", "grezzi", "totale",
                     "diagnostica"]
    assert SessionePratica.__dataclass_fields__.keys() == {
        "carta", "bersaglio", "piano"}


def test_f_usa_il_linguaggio_unico_di_e():
    from gioco27.core.algebra import Controller
    from gioco27.gui.shuffle import ShuffleViewerFrame
    vista = object.__new__(ShuffleViewerFrame)
    for cattiva in ("MSC o", "MSC)"):
        assert not Controller().process(cattiva)["ok"]
        with pytest.raises(Exception):
            vista._validate_and_parse(cattiva)
    assert Controller().process("I")["ok"]
    assert len(vista._validate_and_parse("I")) == 1


def test_f_i_risultati_restano_una_lista(tmp_path):
    """Nessun modello condiviso di G: e' una lista con la sua diagnostica."""
    esito = analizza_righe([_riga()])
    assert isinstance(esito, RisultatiImport) and isinstance(esito, list)
    assert esito == [dict(r) for r in esito]         # si confronta come lista
    assert esito[0]["n_sim"] == 1 and len(esito) == 1
    percorso = _scrivi(tmp_path / "uno.csv", [_riga_csv()])
    assert isinstance(importa_csv(percorso), list)
