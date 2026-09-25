"""Compartimento J — esperimenti, persistenza, cronologia, undo/redo, L90.

Servizi puri (niente Tk). Gli oracoli sono scritti qui, indipendenti dal
codice sotto test: composizione carta per carta, un modello a liste per
undo/redo, fault injection sul salvataggio.
"""
import copy
import json
import os
import random
from pathlib import Path

import pytest

from gioco27.services import archivio, esperimento as E, tabellone as tb
from gioco27.services.cronologia import Cronologia, stato_vuoto
from gioco27.services.procedure import ProceduraGioco, servizio_procedure
from gioco27.services.sessione import SessioneLavoro
from gioco27.services.successione import (IDENTITA, MAX_PROCEDURE, Successione,
                                          SuccessioneNonValida, procedure_casuali)

P = ProceduraGioco.da_identificatore
N = 27


def T_di(p):
    return tuple(servizio_procedure().trasformazione(p))


# ═══════════════════════════ L90 — successione ═══════════════════════════════

def _traccia(procedure, mazzo):
    """Oracolo: ogni carta seguita posizione per posizione, T dopo T."""
    pos = {carta: i for i, carta in enumerate(mazzo)}
    tappe = [tuple(mazzo)]
    for p in procedure:
        T = T_di(p)
        pos = {carta: T[i] for carta, i in pos.items()}
        v = [None] * N
        for carta, i in pos.items():
            v[i] = carta
        tappe.append(tuple(v))
    return tappe


def test_n0_identita():
    s = Successione()
    assert s.cumulativo() == IDENTITA and s.ritorno() == IDENTITA
    assert s.ritorno_procedura().numero_tavola == 0
    assert s.replay_inverso() == (IDENTITA,) and s.disposizioni() == (IDENTITA,)


def test_n1_cumulativo_e_la_trasformazione():
    p = P(100, 0)
    s = Successione((p,))
    assert s.cumulativo() == T_di(p)
    assert s.ritorno_procedura().numero_tavola == 93           # ritorno di #100 (I2)


def test_n2_come_nel_libro():
    """§ 10.1: v1 = T(1)(v0), v2 = T(2)(v1) = (T(2) ∘ T(1))(v0)."""
    p1, p2 = P(100, 0), P(91, 5)
    s = Successione((p1, p2))
    T1, T2 = T_di(p1), T_di(p2)
    assert s.cumulativo() == tuple(T2[T1[i]] for i in range(N))
    mazzo = tuple(f"c{i}" for i in range(N))
    s = Successione((p1, p2), mazzo)
    assert list(s.disposizioni()) == _traccia((p1, p2), mazzo)


@pytest.mark.parametrize("seed", [1, 7, 42])
def test_molte_procedure_carta_per_carta(seed):
    procedure = procedure_casuali(60, seed)
    rng = random.Random(seed)
    mazzo = list(range(N))
    rng.shuffle(mazzo)
    s = Successione(procedure, tuple(mazzo))
    tappe = _traccia(procedure, mazzo)
    assert list(s.disposizioni()) == tappe
    C = s.cumulativo()
    for i, carta in enumerate(mazzo):
        assert tappe[-1][C[i]] == carta                            # C_N carta per carta
    assert s.ritorno_compresso() == tuple(mazzo)                   # vN --R--> v0
    assert list(s.replay_inverso()) == list(reversed(tappe))       # tutte le tappe
    for passo in s.passi():                                        # ogni prefisso sta in H
        assert passo.numero_cumulativo is not None and passo.numero_tavola is not None
    r = s.ritorno_procedura()
    assert r.rovesciamenti == (0, 0, 0) and T_di(r) == s.ritorno()  # 3N stadi → 3


def test_procedure_diverse_stessa_T_restano_distinte():
    classe = servizio_procedure().classe_trasformazione(T_di(P(100, 0)))
    a, b = classe[0], classe[1]
    assert a != b and T_di(a) == T_di(b)
    sa, sb = Successione((a,)), Successione((b,))
    assert sa.cumulativo() == sb.cumulativo()
    assert sa.procedure != sb.procedure                            # storia non collassata
    da = E.crea_documento({"successione": {"procedure": [E.procedura_in_dati(a)],
                                           "mazzo_iniziale": None, "generatore": None}})
    db = E.crea_documento({"successione": {"procedure": [E.procedura_in_dati(b)],
                                           "mazzo_iniziale": None, "generatore": None}})
    assert da["digest"]["scientifico"] != db["digest"]["scientifico"]
    assert "SAME_RESULT_DIFFERENT_HISTORY" in E.confronta(da, db)


def test_successioni_diverse_stesso_cumulativo():
    a, b = P(100, 0), P(56, 3)
    s1 = Successione((a, b))
    compresso = Successione((tb.realizza(s1.cumulativo()),))
    ritorno = Successione((a, tb.ritorno(100)))                    # T e poi T⁻¹
    assert s1.cumulativo() == compresso.cumulativo()
    assert s1.disposizioni()[1] not in compresso.disposizioni()    # il cammino e' diverso
    assert ritorno.cumulativo() == IDENTITA and ritorno.lunghezza == 2


def test_rovesciamenti_conservati():
    p = ProceduraGioco(("SCD", "SDC", "CSD"), (1, 0, 1))
    s = Successione((p,)).aggiungi(P(3, 6)).sposta(1, 0)
    assert s.procedure[1].rovesciamenti == (1, 0, 1)
    assert s.procedure[0].identificatore == (3, 6)
    assert s.rimuovi(0).procedure == (p,)


def test_limiti_e_seed():
    with pytest.raises(SuccessioneNonValida) as e:
        Successione((P(0, 0),) * (MAX_PROCEDURE + 1))
    assert e.value.codice == "troppo_lunga"
    assert procedure_casuali(5, 3) == procedure_casuali(5, 3) != procedure_casuali(5, 4)
    with pytest.raises(SuccessioneNonValida):
        procedure_casuali(5, True)
    with pytest.raises(SuccessioneNonValida):
        Successione((), (0,) * 27)
    with pytest.raises(SuccessioneNonValida):
        Successione((P(0, 0),)).rimuovi(3)


# ═══════════════════════════ documento e digest ══════════════════════════════

STATO = {
    "explorer": {"testo": "(SCD_U x SDC_U x SDC_U) o MSC"},
    "simulatore": {"carta": 0, "bersaglio": 13, "disposizione_fissata": None,
                   "modalita_pratica": "conseguenze"},
    "tavola": {"mescolamenti": ["CSD", "CDS", "CDS"], "rovesciamenti": [0, 1, 0]},
    "riconoscimento": {"T": list(range(9, 27)) + list(range(9))},
    "laboratorio": {"proprieta": "ordini_1_2_3_6", "dominio": "gamma"},
    "successione": {"procedure": [{"mescolamenti": ["SCD", "SDC", "CSD"],
                                   "rovesciamenti": [1, 0, 0]}],
                    "mazzo_iniziale": None, "generatore": None},
}


@pytest.fixture(scope="module")
def doc():
    return E.crea_documento(copy.deepcopy(STATO), titolo="t", nota="n",
                            presentazione={"livello": "avanzato", "scheda": "explorer",
                                           "sottoscheda": None})


def _testo(d):
    return E.json_canonico(d)


def test_round_trip_e_json_canonico(doc):
    b = _testo(doc)
    assert _testo(json.loads(b)) == b
    r = E.verifica_testo(b)
    assert r.stato is E.Stato.VERIFIED and r.documento == json.loads(b)
    assert b == E.json_canonico(json.loads(b.decode("utf-8")))
    assert set(doc["convenzioni"]["regole"]) >= {"posizioni", "trasformazione", "mazzo",
                                                  "composizione", "rovesciamento", "cifre",
                                                  "msc", "gruppi"}
    assert doc["voci"][0]["risultato"]["ok"] is True                # explorer
    assert doc["programma"]["versione"]


def test_digest_scientifico(doc):
    altro = E.crea_documento(copy.deepcopy(STATO), titolo="diverso", nota="",
                             presentazione=None)
    assert altro["digest"]["scientifico"] == doc["digest"]["scientifico"]
    assert altro["digest"]["documento"] != doc["digest"]["documento"]
    diverso = copy.deepcopy(STATO)
    diverso["simulatore"]["carta"] = 1
    assert E.crea_documento(diverso)["digest"]["scientifico"] != doc["digest"]["scientifico"]
    ordine = copy.deepcopy(STATO)
    ordine["successione"]["procedure"].append({"mescolamenti": ["DCS", "SCD", "SCD"],
                                               "rovesciamenti": [0, 0, 0]})
    inverso = copy.deepcopy(ordine)
    inverso["successione"]["procedure"].reverse()
    assert E.crea_documento(ordine)["digest"]["scientifico"] != \
        E.crea_documento(inverso)["digest"]["scientifico"]


def _v(d, strumento):
    return next(v for v in d["voci"] if v["strumento"] == strumento)


def _stato(d):
    return E.verifica_documento(json.loads(_testo(d)) if isinstance(d, dict) else d)


@pytest.mark.parametrize("guasto,stato,codice", [
    (lambda d: d.pop("voci"), E.Stato.CORRUPT, "campo_mancante"),
    (lambda d: d.__setitem__("seed", "7"), E.Stato.CORRUPT, "tipo_errato"),
    (lambda d: d.__setitem__("schema_version", 99), E.Stato.UNSUPPORTED_SCHEMA, "schema_futuro"),
    (lambda d: d.pop("schema_version"), E.Stato.UNSUPPORTED_SCHEMA, "versione_mancante"),
    (lambda d: d.__setitem__("schema", "altro"), E.Stato.UNSUPPORTED_SCHEMA, "schema_sconosciuto"),
    (lambda d: d["convenzioni"].__setitem__("versione", "J0"),
     E.Stato.INCOMPATIBLE_CONVENTION, "convenzione_diversa"),
    (lambda d: d["convenzioni"]["regole"].__setitem__("composizione", "a[b] prima a"),
     E.Stato.INCOMPATIBLE_CONVENTION, "convenzione_diversa"),
    (lambda d: d["digest"].__setitem__("scientifico", "0" * 64), E.Stato.MISMATCH, None),
    (lambda d: _v(d, "simulatore")["risultato"].__setitem__("numero_tavola", 1),
     E.Stato.MISMATCH, None),
    (lambda d: _v(d, "simulatore")["input"].__setitem__("carta", 5), E.Stato.MISMATCH, None),
    (lambda d: d.__setitem__("extra", 1), E.Stato.CORRUPT, "campo_sconosciuto"),
    (lambda d: d["annotazioni"].__setitem__("nota", "x" * (E.LIMITI["nota"] + 1)),
     E.Stato.CORRUPT, "annotazione_troppo_grande"),
    (lambda d: d["presentazione"].__setitem__("livello", "esperto"),
     E.Stato.CORRUPT, "valore_non_valido"),
])
def test_documenti_rifiutati_o_discrepanti(doc, guasto, stato, codice):
    d = json.loads(_testo(doc))
    guasto(d)
    r = E.verifica_documento(d)
    assert r.stato is stato, (r.stato, r.codice, r.diagnosi)
    if codice:
        assert r.codice == codice
    if stato is E.Stato.MISMATCH:
        assert r.diagnosi and r.documento is not None


def test_discrepanza_diagnosticata_campo_per_campo(doc):
    d = json.loads(_testo(doc))
    voce = next(v for v in d["voci"] if v["strumento"] == "simulatore")
    voce["risultato"]["numero_tavola"] = 1
    r = E.verifica_documento(d)
    campi = {(x.voce, x.campo) for x in r.diagnosi}
    assert (voce["id"], "risultato.numero_tavola") in campi
    assert ("documento", "digest.scientifico") in campi
    reg = next(x for x in r.diagnosi if x.campo == "risultato.numero_tavola")
    assert reg.registrato == 1 and reg.ricalcolato != 1


@pytest.mark.parametrize("testo,codice", [
    (b'{"schema": "gioco27.esperimento", "schema_version": 1', "json_invalido"),
    (b"not json", "json_invalido"),
    (b'{"a": 1, "a": 2}', "json_invalido"),
    (b'{"a": NaN}', "json_invalido"),
    (b"\xff\xfe", "json_invalido"),
    (b"[1, 2]", "tipo_errato"),
])
def test_file_troncati_o_invalidi(testo, codice):
    r = E.verifica_testo(testo)
    assert r.stato is E.Stato.CORRUPT and r.codice == codice


def test_file_troppo_grande(tmp_path):
    f = tmp_path / "enorme.json"
    f.write_bytes(b" " * (E.LIMITI["byte"] + 1))
    r = archivio.carica_documento(f)
    assert r.stato is E.Stato.CORRUPT and r.codice == "troppo_grande"
    assert E.verifica_testo(b" " * (E.LIMITI["byte"] + 1)).codice == "troppo_grande"


def test_nessuna_esecuzione_del_contenuto(monkeypatch):
    chiamate = []
    monkeypatch.setattr(os, "system", lambda *a: chiamate.append(a))
    import builtins
    orig_eval = builtins.eval
    monkeypatch.setattr(builtins, "eval", lambda *a, **k: chiamate.append(a) or orig_eval(*a, **k))
    stato = {"explorer": {"testo": "__import__('os').system('echo x')"}}
    d = E.crea_documento(stato)
    assert d["voci"][0]["risultato"] == {"ok": False, "T": None}
    assert E.verifica_testo(E.json_canonico(d)).verificato
    assert chiamate == []
    src = Path(E.__file__).read_text(encoding="utf-8") + \
        Path(archivio.__file__).read_text(encoding="utf-8")
    for vietato in ("import pickle", "pickle.", " eval(", " exec(", "__import__(",
                    "importlib", "subprocess", "os.system"):
        assert vietato not in src, vietato


def test_migrazioni_meccanismo(monkeypatch, doc):
    assert E.MIGRAZIONI == {}                       # nessun formato storico inventato
    d = json.loads(_testo(doc))
    monkeypatch.setattr(E, "SCHEMA_VERSION", 2)
    with pytest.raises(E.EsperimentoNonValido) as e:
        E.migra(copy.deepcopy(d))
    assert e.value.codice == "migrazione_assente"
    monkeypatch.setitem(E.MIGRAZIONI, 1, lambda x: {**x, "schema_version": 2})
    assert E.migra(copy.deepcopy(d))["schema_version"] == 2


def test_seed_e_generatore_riproducibili():
    procedure = [E.procedura_in_dati(p) for p in procedure_casuali(5, 42)]
    stato = {"successione": {"procedure": procedure, "mazzo_iniziale": None,
                             "generatore": {"n": 5}}}
    d = E.crea_documento(stato, seed=42)
    assert E.verifica_testo(E.json_canonico(d)).verificato
    alterato = json.loads(E.json_canonico(d))
    alterato["seed"] = 43
    r = E.verifica_documento(alterato)
    assert r.stato is E.Stato.MISMATCH
    assert any(x.campo == "input.procedure" for x in r.diagnosi)
    senza = json.loads(E.json_canonico(d))
    senza["seed"] = None
    assert E.verifica_documento(senza).codice == "seed_mancante"
    # un'operazione esaustiva non usa seed
    lab = E.crea_documento({"laboratorio": {"proprieta": "centro_banale", "dominio": "h"}})
    assert lab["seed"] is None


def test_record_i6_esportabile_e_ricalcolabile(tmp_path):
    d = E.crea_documento({"laboratorio": {"proprieta": "due_carte_forzabili", "dominio": "h"}})
    r = d["voci"][0]["risultato"]
    assert (r["esito"], r["metodo"], r["controllati"], r["totale"]) == \
        ("falsa", "esaustivo", 3, 492804)
    assert r["controesempio"]["dati"] == {"c1": 0, "c2": 1, "t1": 0, "t2": 3}
    intest, righe = archivio.righe_proprieta(d["voci"])
    m = archivio.scrivi_csv(tmp_path / "i6.csv", "verifiche_i6", intest, righe)
    assert m["sha256"] == E.sha256((tmp_path / "i6.csv").read_bytes())
    assert json.loads((tmp_path / "i6.csv.manifest.json").read_text())["convenzioni"]["versione"] \
        == E.CONVENTION_VERSION
    assert E.verifica_testo(E.json_canonico(d)).verificato


def test_fonti_solo_hash_e_mai_aperte(tmp_path):
    libro = tmp_path / "LIBRO_MAIN.pdf"
    libro.write_bytes(b"%PDF-1.4 finto")
    f1 = E.fonte("LIBRO_MAIN.pdf", "libro", libro)
    f2 = E.fonte("Articolo.pdf", "articolo", tmp_path / "manca.pdf")
    assert f1["disponibile"] and f1["sha256"] == E.sha256(b"%PDF-1.4 finto")
    assert f2 == {"nome": "Articolo.pdf", "ruolo": "articolo", "sha256": None,
                  "disponibile": False}
    d = E.crea_documento({}, fonti=(f1, f2))
    assert b"%PDF" not in E.json_canonico(d)                  # mai incorporati
    assert "percorso" not in f1                                # nessun path da aprire
    d2 = E.crea_documento({}, fonti=(E.fonte("LIBRO_MAIN.pdf", "libro", None),))
    assert "DIFFERENT_SOURCE_HASHES" in E.confronta(d, d2)


def test_confronto_strutturato(doc):
    stesso = E.crea_documento(copy.deepcopy(STATO), titolo="altro")
    c = E.confronta(doc, stesso)
    assert "SAME_SCIENTIFIC_CONTENT" in c and "ANNOTATIONS_ONLY" in c
    t1 = {"tavola": E.procedura_in_dati(P(100, 0))}
    classe = servizio_procedure().classe_trasformazione(T_di(P(100, 0)))
    altra = next(p for p in classe if p.rovesciamenti != (0, 0, 0))
    t2 = {"tavola": E.procedura_in_dati(altra)}
    assert "SAME_RESULT_DIFFERENT_HISTORY" in E.confronta(E.crea_documento(t1),
                                                          E.crea_documento(t2))
    falso = json.loads(_testo(doc))
    _v(falso, "simulatore")["risultato"]["numero_tavola"] = 1
    assert "RESULT_MISMATCH" in E.confronta(doc, falso)
    conv = json.loads(_testo(doc))
    conv["convenzioni"]["versione"] = "J2"
    assert "DIFFERENT_CONVENTION" in E.confronta(doc, conv)
    prog = json.loads(_testo(doc))
    prog["programma"]["versione"] = "9.9.9"
    c = E.confronta(doc, prog)
    assert "DIFFERENT_PROGRAM_VERSION" in c and "SAME_SCIENTIFIC_CONTENT" in c
    assert "DIFFERENT_CONVENTION" not in c


# ═══════════════════════════ salvataggio atomico ═════════════════════════════

def _temporanei(cartella):
    return list(Path(cartella).glob(".gioco27-*"))


def test_salvataggio_round_trip_e_destinazione_preesistente(tmp_path, doc):
    f = tmp_path / "e.json"
    f.write_text("vecchio", encoding="utf-8")
    digest = archivio.salva_documento(doc, f)
    assert digest == E.sha256(f.read_bytes())
    r = archivio.carica_documento(f)
    assert r.verificato and r.documento["id"] == doc["id"]
    assert _temporanei(tmp_path) == []


@pytest.mark.parametrize("fase", ["serializzazione", "scrittura", "replace"])
def test_salvataggio_con_guasto_lascia_intatto(tmp_path, doc, monkeypatch, fase):
    f = tmp_path / "e.json"
    f.write_bytes(b"precedente")

    class Guasto(Exception):
        pass

    def esplodi(*a, **k):
        raise Guasto(fase)
    if fase == "serializzazione":
        monkeypatch.setattr(archivio.E, "json_canonico", esplodi)
    elif fase == "scrittura":
        from gioco27.core import parallel
        originale = parallel.atomic_write

        def guasta(*a, **k):
            cm = originale(*a, **k)

            class File:
                def __init__(self_, fh):
                    self_.fh = fh

                def write(self_, dati):
                    self_.fh.write(dati[:5])          # scrittura parziale, poi guasto
                    raise Guasto(fase)

            class Wrap:
                def __enter__(self_):
                    return File(cm.__enter__())

                def __exit__(self_, *exc):
                    return cm.__exit__(*exc)
            return Wrap()
        monkeypatch.setattr(archivio, "atomic_write", guasta)
    else:
        monkeypatch.setattr(os, "replace", esplodi)
    with pytest.raises(Guasto):
        archivio.salva_documento(doc, f)
    assert f.read_bytes() == b"precedente"
    assert _temporanei(tmp_path) == []


# ═══════════════════════════ cronologia, undo/redo ═══════════════════════════

def _st(n):
    s = stato_vuoto()
    s["scientifico"]["tavola"] = {"mescolamenti": ["SCD", "SCD", "SCD"], "rovesciamenti": [0, 0, 0],
                                  "n": n}
    return s


def test_zero_e_un_evento():
    c = Cronologia()
    assert (c.numero_eventi, c.puo_annullare(), c.puo_ripristinare()) == (0, False, False)
    assert c.annulla() is None and c.ripristina() is None
    assert c.registra("x", "tavola", c.stato) is None               # nessun cambiamento
    e = c.registra("x", "tavola", _st(1))
    assert e["id"] == 1 and e["revisione"] == 1 and c.puo_annullare()
    assert c.annulla() == stato_vuoto() and c.ripristina() == _st(1)


def test_sequenze_lunghe_contro_un_modello():
    rng = random.Random(2026)
    c = Cronologia()
    storia, futuro, corrente = [], [], stato_vuoto()
    for passo in range(600):
        azione = rng.choice(["modifica", "modifica", "undo", "redo"])
        if azione == "modifica":
            nuovo = _st(rng.randrange(8))
            if nuovo != corrente:
                storia.append(corrente)
                futuro.clear()
                corrente = nuovo
            c.registra("m", "tavola", nuovo)
        elif azione == "undo" and storia:
            futuro.append(corrente)
            corrente = storia.pop()
            assert c.annulla() == corrente
        elif azione == "redo" and futuro:
            storia.append(corrente)
            corrente = futuro.pop()
            assert c.ripristina() == corrente
        else:
            assert (c.annulla() if azione == "undo" else c.ripristina()) is None
        assert c.stato == corrente
    fine = futuro[0] if futuro else corrente
    while c.puo_annullare():                                          # fino all'origine
        c.annulla()
    assert c.stato == stato_vuoto()
    while c.puo_ripristinare():                                       # fino alla fine
        c.ripristina()
    assert c.stato == fine


def test_undo_e_nuova_modifica_tronca_redo():
    c = Cronologia()
    for n in range(3):
        c.registra("m", "tavola", _st(n + 1))
    c.annulla()
    c.annulla()
    assert c.puo_ripristinare()
    c.registra("m", "tavola", _st(9))
    assert not c.puo_ripristinare() and c.stato == _st(9)


def test_stato_salvato_e_modificato():
    c = Cronologia()
    c.registra("m", "tavola", _st(1))
    c.segna_salvato()
    assert not c.modificata
    c.registra("m", "tavola", _st(2))
    assert c.modificata
    c.annulla()
    assert not c.modificata                                          # undo allo stato salvato
    c.annulla()
    assert c.modificata                                              # redo/undo lontano
    c.ripristina()
    assert not c.modificata


def test_sessione_annotazioni_presentazione_ed_export(tmp_path):
    s = SessioneLavoro()
    s.registra("tavola", {"mescolamenti": ["SCD", "SDC", "CSD"], "rovesciamenti": [0, 0, 0]})
    rev = s.cronologia.revisione
    s.imposta_annotazioni("titolo", "nota")
    assert s.cronologia.revisione == rev and s.modificata          # annotazione: dirty, non scienza
    eventi = s.cronologia.numero_eventi
    s.imposta_presentazione("laboratorio", "explorer", "laboratorio")
    assert s.cronologia.numero_eventi == eventi                     # presentazione: nessun evento
    out = tmp_path / "export.csv"
    intest, righe = archivio.righe_mapping(IDENTITA)
    m = archivio.scrivi_csv(out, "mapping", intest, righe)
    s.registra_export("csv", out.name, m["sha256"])
    s.registra("tavola", {"mescolamenti": ["DCS", "SDC", "CSD"], "rovesciamenti": [0, 0, 0]})
    while s.cronologia.puo_annullare():
        s.cronologia.annulla()
    assert out.exists() and E.sha256(out.read_bytes()) == m["sha256"]  # undo ≠ delete
    assert [e["tipo"] for e in s.cronologia.esterni] == ["esportato"]


def test_sessione_salva_carica_round_trip(tmp_path):
    s = SessioneLavoro()
    for chiave, inp in STATO.items():
        s.registra(chiave, copy.deepcopy(inp))
    s.imposta_annotazioni("esperimento", "nota lunga")
    s.imposta_presentazione("avanzato", "explorer", None)
    s.cronologia.annulla()                                          # un ramo di redo
    f = tmp_path / "s.json"
    s.salva(f)
    assert not s.modificata
    nuova, rapporto = SessioneLavoro.carica(f)
    assert rapporto.verificato
    assert nuova.stato_scientifico == s.stato_scientifico
    assert nuova.annotazioni == s.annotazioni
    assert nuova.presentazione == s.presentazione
    assert nuova.cronologia.puo_ripristinare() and not nuova.modificata
    assert nuova.cronologia.eventi == s.cronologia.eventi           # cronologia deterministica
    nuova.cronologia.ripristina()
    assert nuova.modificata


def test_caricamento_transazionale(tmp_path):
    s = SessioneLavoro()
    s.registra("tavola", {"mescolamenti": ["SCD", "SDC", "CSD"], "rovesciamenti": [0, 0, 0]})
    prima = (s.stato_scientifico, s.cronologia.numero_eventi, s.id)
    rotto = tmp_path / "rotto.json"
    rotto.write_bytes(b'{"schema": "gioco27.esperimento"')
    nuova, rapporto = SessioneLavoro.carica(rotto)
    assert nuova is None and rapporto.stato is E.Stato.CORRUPT
    assert (s.stato_scientifico, s.cronologia.numero_eventi, s.id) == prima


def test_cronologia_deterministica():
    def storia():
        c = Cronologia()
        for n in (1, 2, 3):
            c.registra("m", "tavola", _st(n))
        c.annulla()
        c.registra_esterno("esportato", "export", {"nome": "a.csv"})
        return c.a_dati()
    assert storia() == storia()
    assert E.json_canonico(storia()) == E.json_canonico(storia())
