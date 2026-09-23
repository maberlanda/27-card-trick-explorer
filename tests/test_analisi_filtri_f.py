"""Compartimento F — ingressi validati (B05) e filtri ancora incoerenti (B06).

La prima meta' del compartimento e' chiusa: schema, `T` e formula hanno un
contratto. La seconda e' qui misurata e non ancora corretta — conteggio,
enumerazione e validazione dei filtri descrivono domini diversi — con prove
`xfail(strict=True)` che dovranno smettere di fallire.
"""
import pathlib
from types import SimpleNamespace

import pytest

from gioco27.core.algebra import analizza_csv, analizza_righe
from gioco27.core.analisi import RisultatiImport, SchemaNonRiconosciuto, importa_csv, riconosci_schema
from gioco27.core.combinations import count_combinations_ex, iter_combinations_ex
from gioco27.core.constants import ANY
from gioco27.core.permutations import CSV_HEADER
from gioco27.gui import analysis_tab

RADICE = pathlib.Path(__file__).resolve().parents[1]

IDENTITA = "[" + ",".join(str(i) for i in range(27)) + "]"
FISSO = dict(p0="SCD_U", p1="SCD_U", p2="SCD_U", j0="I_3", j1="I_3", j2="I_3")
FILTRI_FISSI = [dict(FISSO) for _ in range(3)]


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


# ═════════════════ B06 — conteggio ed enumerazione divergono ════════════════
#
# `valida_filtri` non guarda ne' il numero di stadi ne' i valori;
# `count_combinations_ex` percorre tutti gli stadi ricevuti mentre
# `iter_combinations_ex` legge solo i primi tre. Tre descrizioni dello stesso
# dominio, e nessuna che valga per le altre due.

FILTRO_FISSO = dict(p0="SCD_U", p1="SCD_U", p2="SCD_U",
                    j0="I_3", j1="I_3", j2="I_3")

#: Strutture che non descrivono un dominio enumerabile a tre stadi.
FILTRI_MALFORMATI = [
    ("quattro stadi", [FILTRO_FISSO, FILTRO_FISSO, FILTRO_FISSO,
                       dict(FILTRO_FISSO, p0="*")]),
    ("due stadi",     [FILTRO_FISSO, FILTRO_FISSO]),
    ("nessuno stadio", []),
    ("chiave sconosciuta", [dict(FILTRO_FISSO, pX="SCD_U"),
                            FILTRO_FISSO, FILTRO_FISSO]),
    ("nome inesistente", [dict(FILTRO_FISSO, p0="NON_ESISTE"),
                          FILTRO_FISSO, FILTRO_FISSO]),
    ("tipo errato", [dict(FILTRO_FISSO, p0=3), FILTRO_FISSO, FILTRO_FISSO]),
    ("elenco con duplicati", [dict(FILTRO_FISSO, p0=["SCD_U", "SCD_U"]),
                              FILTRO_FISSO, FILTRO_FISSO]),
    ("j_uniform non booleano", [dict(FILTRO_FISSO, j_uniform="si"),
                                FILTRO_FISSO, FILTRO_FISSO]),
]


def _conta(filtri):
    try:
        return count_combinations_ex(filtri)
    except Exception as errore:
        return type(errore).__name__


def _enumera(filtri):
    try:
        return sum(1 for _ in iter_combinations_ex(filtri))
    except Exception as errore:
        return type(errore).__name__


@pytest.mark.xfail(strict=True, reason="B06: count=6 e iter=1 con quattro stadi")
def test_b06_conteggio_ed_enumerazione_descrivono_lo_stesso_dominio():
    discordi = [(nota, _conta(f), _enumera(f)) for nota, f in FILTRI_MALFORMATI
                if _conta(f) != _enumera(f)]
    assert discordi == []


@pytest.mark.xfail(strict=True,
                   reason="B06: valori e chiavi non validi passano senza un fiato")
def test_b06_le_strutture_malformate_vengono_rifiutate():
    accettate = [nota for nota, f in FILTRI_MALFORMATI
                 if isinstance(_conta(f), int) and isinstance(_enumera(f), int)]
    assert accettate == []
