"""Compartimento I4 — service dello spettatore (`services.spettatore`).

Gli oracoli sono indipendenti dal service: aritmetica a mano (cifre, 
``a1 + 3a2 + 9a3``) e il core fisico. `risolvi_trucco` compare solo dove la
consegna lo chiede come termine di confronto (le 729 raccolte adattive).
Lo spettatore simulato dei test conosce la propria carta; il service no.
"""
import ast
import dataclasses
import inspect
import itertools
import pathlib
import random

import pytest

from gioco27.core import gioco_reale as gr
from gioco27.services import spettatore as sp
from gioco27.services import tabellone as tb

SORGENTE = pathlib.Path(sp.__file__)


def _cifre_a_mano(n):
    return (n % 3, (n // 3) % 3, n // 9)          # (n0, n1, n2)


def _spettatore(s, posizione_iniziale):
    """La risposta di uno spettatore onesto: il mazzetto dove vede la carta."""
    pile = sp.distribuzione_corrente(s)
    return next(g for g in range(3) if posizione_iniziale in pile[g])


def _gioca(c, t, mazzo=None, raccolte=None):
    s = sp.avvia_spettatore(t, mazzo)
    tappe = [s]
    for k in range(3):
        s = sp.rispondi(s, _spettatore(s, c))
        tappe.append(s)
        s = sp.esegui_raccolta(s, None if raccolte is None else raccolte[k])
    return s, tappe


# ═══════════════════ gate centrale: 27 × 27 = 729 casi ══════════════════════

def test_i729_casi_carta_bersaglio():
    casi = 0
    for c in range(27):
        for t in range(27):
            s, tappe = _gioca(c, t)
            assert [len(sp.posizioni_iniziali_candidate(x)) for x in tappe] == [27, 9, 3, 1]
            assert sp.posizioni_iniziali_candidate(s) == {c}
            atteso = gr.risolvi_trucco(c, t)
            assert s.raccolte == atteso["mescolamenti"], (c, t)
            assert s.risposte == atteso["colonne"], (c, t)
            e = sp.esito(s)
            assert e.posizione_iniziale == c and e.posizione_finale == t
            assert e.bersaglio_raggiunto and e.protocollo_adattivo
            assert e.numero_disposizione == atteso["numero"]
            casi += 1
    assert casi == 729


def test_la_carta_finisce_davvero_al_bersaglio_nel_mazzo_fisico():
    """Oracolo fisico indipendente: si rigioca il mazzo con le raccolte scelte."""
    for c in range(27):
        for t in range(27):
            s, _ = _gioca(c, t)
            deck = list(range(27))
            for m in s.raccolte:
                deck = gr.raccogli(gr.distribuisci(deck), m)
            assert deck.index(c) == t


# ═════════════════════════════ 27 terne ═════════════════════════════════════

def test_le_27_terne_identificano_27_posizioni():
    mappa = {}
    for terna in itertools.product(range(3), repeat=3):
        s = sp.avvia_spettatore(13)
        for a in terna:
            s = sp.esegui_raccolta(sp.rispondi(s, a))
        mappa[terna] = sp.esito(s).posizione_iniziale
    assert len(mappa) == 27                                  # totale
    assert len(set(mappa.values())) == 27                    # iniettiva
    assert set(mappa.values()) == set(range(27))             # suriettiva
    for (a1, a2, a3), n in mappa.items():
        assert n == a1 + 3 * a2 + 9 * a3                     # A11, prima = unita'


@pytest.mark.parametrize("terna", list(itertools.product(range(3), repeat=3)))
def test_candidati_uguali_all_oracolo_aritmetico(terna):
    s = sp.avvia_spettatore(5)
    for k, a in enumerate(terna):
        s = sp.rispondi(s, a)
        attesi = {x for x in range(27)
                  if all(_cifre_a_mano(x)[j] == terna[j] for j in range(k + 1))}
        assert sp.posizioni_iniziali_candidate(s) == attesi
        assert len(attesi) == 3 ** (2 - k)
        s = sp.esegui_raccolta(s)


def test_la_ricostruzione_usa_le_cifre_di_i2():
    s, _ = _gioca(19, 13)
    e = sp.esito(s)
    assert e.storia == "CSD" and e.parola == "DSC" == gr.parola(19)
    assert e.cifre == gr.digits3(19) == (2, 0, 1)
    assert e.risposte == (1, 0, 2)


# ═══════════════ identificazione ≠ controllo della destinazione ═════════════

def test_identificazione_indipendente_dal_bersaglio():
    for c in range(27):
        visti = set()
        for t in range(27):
            s, _ = _gioca(c, t)
            e = sp.esito(s)
            visti.add((e.risposte, e.posizione_iniziale))
        assert visti == {(_cifre_a_mano(c), c)}


def test_identificazione_indipendente_dalle_raccolte():
    """27 × 216 raccolte libere: si identifica sempre; al bersaglio 8 su 216."""
    for c in range(27):
        arrivi = 0
        for terna in itertools.product(gr.SIGLE, repeat=3):
            s, _ = _gioca(c, 0, raccolte=terna)
            e = sp.esito(s)
            assert e.posizione_iniziale == c
            assert e.risposte == _cifre_a_mano(c)
            arrivi += e.bersaglio_raggiunto
            assert e.protocollo_adattivo == (e.bersaglio_raggiunto and
                                             terna == gr.risolvi_trucco(c, 0)["mescolamenti"])
        assert arrivi == 8


def test_la_fisica_resta_una_permutazione_a_ogni_passo():
    for c in (0, 13, 26):
        _, tappe = _gioca(c, 7)
        for s in tappe:
            assert sorted(sp.ordine_corrente(s)) == list(range(27))
            x = sp.posizioni_iniziali_candidate(s)
            assert len(sp.posizioni_correnti_dei_candidati(s)) == len(x)


# ═══════════════════ modalita' A: ordine iniziale noto ══════════════════════

def test_ordine_noto_con_un_mazzo_mescolato_identifica_la_carta():
    rnd = random.Random(27)
    for _ in range(10):
        mazzo = list(range(27))
        rnd.shuffle(mazzo)
        for c in range(27):
            t = rnd.randrange(27)
            s, tappe = _gioca(c, t, mazzo)
            assert sp.carta_determinata(tappe[2]) is None
            assert sp.carta_determinata(tappe[3]) == mazzo[c]
            e = sp.esito(s)
            assert e.carta == mazzo[c] and e.posizione_iniziale == c
            assert e.modalita is sp.Modalita.ORDINE_NOTO


# ═══════════════════════════ esempi didattici fissi ═════════════════════════

ESEMPI = [
    # c, t, risposte, raccolte (mescolamenti)
    (0, 13, (0, 0, 0), None),
    (13, 13, (1, 1, 1), ("SCD", "SCD", "SCD")),
    (26, 13, (2, 2, 2), None),
    (19, 13, (1, 0, 2), None),
    (0, 0, (0, 0, 0), ("SCD", "SCD", "SCD")),
    (19, 26, (1, 0, 2), None),
    (26, 5, (2, 2, 2), None),
]


@pytest.mark.parametrize("c,t,risposte,raccolte", ESEMPI)
def test_esempi_didattici(c, t, risposte, raccolte):
    s, tappe = _gioca(c, t)
    assert s.risposte == risposte
    assert [len(sp.posizioni_iniziali_candidate(x)) for x in tappe] == [27, 9, 3, 1]
    passi = sp.storia_informativa(s)
    assert [p.indice_cifra for p in passi] == [0, 1, 2]
    assert [p.risposta for p in passi] == list(_cifre_a_mano(c))
    assert [p.sede for p in passi] == list(_cifre_a_mano(t))
    if raccolte is not None:
        assert s.raccolte == raccolte
    for p, m in zip(passi, s.raccolte):
        assert gr.MESCOLAMENTO[m][p.risposta] == p.sede      # mazzetto → sede
    e = sp.esito(s)
    assert (e.posizione_iniziale, e.posizione_finale) == (c, t)
    a1, a2, a3 = e.risposte
    assert a1 + 3 * a2 + 9 * a3 == c


def test_esempio_b1_del_libro_c_d_s_e_7():
    s = sp.avvia_spettatore(13)
    for a in (1, 2, 0):
        s = sp.esegui_raccolta(sp.rispondi(s, a))
    assert sp.esito(s).posizione_iniziale == 7


# ═══════════════ nessuna scorciatoia: la carta non entra ════════════════════

def test_la_scelta_della_raccolta_non_riceve_la_carta():
    assert list(inspect.signature(sp.scelta_raccolta).parameters) == [
        "bersaglio", "fase", "risposta"]
    for f in (sp.rispondi, sp.esegui_raccolta, sp.avvia_spettatore):
        assert not any("carta" in p for p in inspect.signature(f).parameters)
    campi = {f.name for f in dataclasses.fields(sp.SessioneSpettatore)}
    assert campi == {"bersaglio", "mazzo_iniziale", "risposte", "raccolte"}


def test_una_sola_regola_autorevole_e_nessun_solutore():
    albero = ast.parse(SORGENTE.read_text(encoding="utf-8"))
    chiamati = {n.func.attr for n in ast.walk(albero)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    nomi = {n.attr for n in ast.walk(albero) if isinstance(n, ast.Attribute)}
    nomi |= {n.id for n in ast.walk(albero) if isinstance(n, ast.Name)}
    assert "mescolamento_per_colonna" in chiamati
    assert "risolvi_trucco" not in nomi                 # solo citato nel testo
    # la regola e' chiamata in un solo punto: scelta_raccolta
    assert sum(1 for n in ast.walk(albero) if isinstance(n, ast.Call)
               and getattr(n.func, "attr", "") == "mescolamento_per_colonna") == 1


def test_scelta_raccolta_coincide_con_la_regola_per_fase():
    for t in range(27):
        for fase in (1, 2, 3):
            for a in range(3):
                m = sp.scelta_raccolta(t, fase, a)
                assert m == gr.mescolamento_per_colonna(a, gr.digits3(t)[3 - fase])
                assert gr.MESCOLAMENTO[m][a] == _cifre_a_mano(t)[fase - 1]


def test_il_service_e_puro():
    testo = SORGENTE.read_text(encoding="utf-8")
    for vietato in ("tkinter", "from ..gui", "i18n", "print("):
        assert vietato not in testo


# ═══════════════════════ risposte non accettate ═════════════════════════════

def test_ogni_risposta_s_c_d_e_possibile_nel_27():
    for terna in itertools.product(range(3), repeat=2):
        s = sp.avvia_spettatore(13)
        assert sp.risposte_possibili(s) == (0, 1, 2)
        for a in terna:
            s = sp.esegui_raccolta(sp.rispondi(s, a))
            assert sp.risposte_possibili(s) == (0, 1, 2)


def test_nessuna_risposta_e_incoerente_qualunque_raccolta():
    """Legge del 27: 216 terne di raccolte × 9 coppie di risposte."""
    for raccolte in itertools.product(gr.SIGLE, repeat=3):
        for risposte in itertools.product(range(3), repeat=2):
            s = sp.avvia_spettatore(0)
            for k, a in enumerate(risposte):
                assert sp.risposte_possibili(s) == (0, 1, 2)
                s = sp.esegui_raccolta(sp.rispondi(s, a), raccolte[k])
            assert sp.risposte_possibili(s) == (0, 1, 2)


def test_una_risposta_che_svuota_i_candidati_e_rifiutata(monkeypatch):
    """Il 27 non produce mai questo stato: lo si forza per provare la guardia."""
    s = sp.avvia_spettatore(13)
    monkeypatch.setattr(sp, "posizioni_iniziali_candidate",
                        lambda _s: frozenset({0}))          # solo in S
    assert sp.risposte_possibili(s) == (0,)
    with pytest.raises(sp.RispostaNonAccettata) as e:
        sp.rispondi(s, 2)
    assert e.value.codice == "risposta_incoerente"
    assert e.value.dati == {"risposta": 2, "fase": 1}
    assert sp.rispondi(s, 0).risposte == (0,)


@pytest.mark.parametrize("valore", [3, -1, True, "S", None, 1.5])
def test_risposte_fuori_dominio(valore):
    with pytest.raises(sp.RispostaNonAccettata) as e:
        sp.rispondi(sp.avvia_spettatore(13), valore)
    assert e.value.codice == "risposta_fuori_dominio"


def test_ordine_dei_passi_controllato():
    s = sp.avvia_spettatore(13)
    with pytest.raises(sp.RispostaNonAccettata) as e:
        sp.esegui_raccolta(s)
    assert e.value.codice == "risposta_mancante"
    s = sp.rispondi(s, 1)
    with pytest.raises(sp.RispostaNonAccettata) as e:
        sp.rispondi(s, 1)
    assert e.value.codice == "raccolta_in_sospeso"
    with pytest.raises(sp.RispostaNonAccettata) as e:
        sp.esegui_raccolta(s, "XYZ")
    assert e.value.codice == "raccolta_fuori_dominio"
    s, _ = _gioca(4, 4)
    for passo in (lambda: sp.rispondi(s, 0), lambda: sp.esegui_raccolta(s)):
        with pytest.raises(sp.RispostaNonAccettata) as e:
            passo()
        assert e.value.codice == "sessione_conclusa"
    assert isinstance(e.value, ValueError)


def test_esito_solo_a_sessione_conclusa():
    s = sp.rispondi(sp.avvia_spettatore(13), 2)
    assert sp.esito(s) is None
    assert sp.posizione_iniziale_determinata(s) is None


def test_ingressi_non_validi_all_avvio():
    from gioco27.core.dominio import PermutazioneNonValida
    with pytest.raises(ValueError):
        sp.avvia_spettatore(27)
    with pytest.raises(PermutazioneNonValida):
        sp.avvia_spettatore(13, [0] * 27)


# ═══════════════════════════════════ B12 ════════════════════════════════════

def test_b12_esempio_100():
    rv, s = sp.avvia_b12(("DSC", "DSC", "CSD"))
    assert rv.mescolamenti_osservati == ("CDS", "CDS", "CSD")
    assert rv.numero_osservato == 100
    assert rv.impilamenti_di_ritorno == ("CDS", "CDS", "CSD")
    assert rv.ritorno == tb.ritorno(100)
    assert s.bersaglio == sp.CENTRO == 13
    assert s.mazzo_iniziale is None and s.modalita is sp.Modalita.ORDINE_IGNOTO


def test_b12_esaustivo_216_disposizioni_per_27_posizioni():
    """Mazzo ignoto (casuale), storia osservata, riavvolgimento, interrogazione."""
    for numero in range(216):
        rnd = random.Random(numero)
        mazzo = list(range(100, 127))
        rnd.shuffle(mazzo)                      # facce ignote all'esecutore
        rv, s0 = sp.avvia_b12(tuple(gr.IMPILAMENTO_DI[m]
                                    for m in gr.mescolamenti_da_numero(numero)))
        assert rv.numero_osservato == numero
        deck = list(mazzo)
        for m in rv.mescolamenti_osservati + rv.ritorno.mescolamenti:
            deck = gr.raccogli(gr.distribuisci(deck), m)
        assert deck == mazzo                    # T⁻¹ T = I
        for n in range(27):
            s = s0
            for _ in range(3):
                # lo spettatore guarda la faccia della propria carta nel mazzo vero
                vero = [mazzo[p] for p in sp.ordine_corrente(s)]
                pile = gr.distribuisci(vero)
                a = next(g for g in range(3) if mazzo[n] in pile[g])
                s = sp.esegui_raccolta(sp.rispondi(s, a))
            e = sp.esito(s)
            assert e.posizione_iniziale == n and e.posizione_finale == 13
            assert e.carta is None                          # identita' ignota
            assert sp.carta_determinata(s) is None


def test_b12_raccolte_al_centro():
    for fase in (1, 2, 3):
        for a in range(3):
            assert gr.MESCOLAMENTO[sp.scelta_raccolta(sp.CENTRO, fase, a)][a] == 1


def test_b12_osservazioni_non_valide():
    with pytest.raises(sp.RispostaNonAccettata):
        sp.avvia_b12(("DSC", "DSC"))
    with pytest.raises(sp.RispostaNonAccettata):
        sp.avvia_b12(("DSC", "DSC", "XYZ"))
