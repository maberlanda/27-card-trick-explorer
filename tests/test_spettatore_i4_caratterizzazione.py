"""Compartimento I4 — caratterizzazione della dinamica informativa (oracoli).

Qui non si usa il service dello spettatore: solo il core fisico
(`distribuisci`, `raccogli`) e l'aritmetica in base 3 scritta a mano, cosi'
che i test del service abbiano un oracolo indipendente.

Fonti (LIBRO_MAIN.pdf, verificate per I4):

* § 1.6 «la macchina che dimentica»; § 1.9 Prop. 1.6: la storia delle
  distribuzioni e' rev ω(n), **indipendente dalle raccolte**;
* § 7.1.11 A11 e § 7.2.2 B1: ``n = a1 + 3 a2 + 9 a3``, la prima risposta vale
  le unita'; esempi 17 → risposte 2, 2, 1 e C, D, S → 7;
* § 7.2.13 B12: ordine iniziale ignoto, tre raccolte osservate, riavvolgimento
  con T⁻¹ realizzato come (R), poi tre interrogazioni «al centro» → 13;
  esempio della disposizione #100.
"""
import itertools

import pytest

from gioco27.core import gioco_reale as gr
from gioco27.services import tabellone as tb


def _cifre_a_mano(n):
    """(n0, n1, n2) senza passare per il codice del programma."""
    return (n % 3, (n // 3) % 3, n // 9)


def _storia_fisica(carta, mescolamenti, mazzo=None):
    """Le colonne in cui la carta compare, simulando il mazzo carta per carta."""
    deck = list(range(27)) if mazzo is None else list(mazzo)
    storia = []
    for m in mescolamenti:
        cols = gr.distribuisci(deck)
        storia.append(next(g for g in range(3) if carta in cols[g]))
        deck = gr.raccogli(cols, m)
    return tuple(storia), deck


def _candidati_aritmetici(risposte):
    """Posizioni iniziali compatibili con le risposte (solo aritmetica)."""
    return {x for x in range(27)
            if all(_cifre_a_mano(x)[k] == a for k, a in enumerate(risposte))}


# ═════════════════ Prop. 1.6: storia = rev ω(n), qualunque raccolta ═════════

def test_la_storia_delle_distribuzioni_non_dipende_dalle_raccolte():
    """27 posizioni × 216 terne di raccolte = 5832 esecuzioni fisiche."""
    casi = 0
    for n in range(27):
        attesa = _cifre_a_mano(n)
        for terna in itertools.product(gr.SIGLE, repeat=3):
            storia, _ = _storia_fisica(n, terna)
            assert storia == attesa, (n, terna)
            casi += 1
    assert casi == 5832


def test_la_storia_e_la_parola_rovesciata():
    for n in range(27):
        storia, _ = _storia_fisica(n, ("SCD",) * 3)
        assert "".join("SCD"[a] for a in reversed(storia)) == gr.parola(n)


def test_l_indipendenza_vale_anche_con_un_mazzo_iniziale_qualunque():
    """Conta la posizione, non la carta: stesso risultato con un ordine mescolato."""
    import random
    rnd = random.Random(4)
    for _ in range(20):
        mazzo = list(range(27))
        rnd.shuffle(mazzo)
        for n in range(27):
            terna = tuple(rnd.choice(gr.SIGLE) for _ in range(3))
            storia, _ = _storia_fisica(mazzo[n], terna, mazzo)
            assert storia == _cifre_a_mano(n)


# ════════════════════════ B1 / A11: n = a1 + 3a2 + 9a3 ═══════════════════════

def test_esempio_a11_posizione_17():
    storia, _ = _storia_fisica(17, ("SCD",) * 3)
    assert storia == (2, 2, 1)
    a1, a2, a3 = storia
    assert a1 + 3 * a2 + 9 * a3 == 17


def test_esempio_b1_risposte_c_d_s_danno_7():
    a1, a2, a3 = ("SCD".index(x) for x in "CDS")
    assert a1 + 3 * a2 + 9 * a3 == 7


def test_esempio_19_e_dsc_e_si_osserva_c_s_d():
    assert gr.parola(19) == "DSC"
    storia, _ = _storia_fisica(19, ("CSD", "DCS", "SDC"))
    assert "".join("SCD"[a] for a in storia) == "CSD"


def test_l_ordine_delle_cifre_non_e_quello_opposto():
    """9a1 + 3a2 + a3 sbaglia su 18 posizioni su 27: solo le 9 palindrome coincidono."""
    sbagliate = 0
    for n in range(27):
        a1, a2, a3 = _cifre_a_mano(n)
        sbagliate += (9 * a1 + 3 * a2 + a3) != n
    assert sbagliate == 18        # le 9 parole palindrome coincidono


# ═════════════════ 27 → 9 → 3 → 1 sulle posizioni INIZIALI ══════════════════

def test_la_contrazione_27_9_3_1_per_ogni_terna():
    for terna in itertools.product(range(3), repeat=3):
        assert [len(_candidati_aritmetici(terna[:k])) for k in range(4)] == [27, 9, 3, 1]


def test_le_27_terne_sono_una_biiezione():
    immagini = [next(iter(_candidati_aritmetici(t)))
                for t in itertools.product(range(3), repeat=3)]
    assert sorted(immagini) == list(range(27))


def test_nel_27_ogni_risposta_e_sempre_possibile():
    """Qualunque raccolta: i candidati superstiti cadono in tutte e tre le pile.

    Legge (caratterizzazione): dopo k risposte i candidati occupano un blocco
    di 3^(3-k) posizioni consecutive, che la distribuzione ripartisce in parti
    uguali. Nel 27 standard una risposta S/C/D non e' mai incoerente.
    """
    for terna in itertools.product(gr.SIGLE, repeat=3):
        for risposte in itertools.product(range(3), repeat=2):
            deck = list(range(27))
            candidati = set(range(27))
            for k, a in enumerate(risposte):
                cols = gr.distribuisci(deck)
                assert all(candidati & set(c) for c in cols)
                candidati &= set(cols[a])
                deck = gr.raccogli(cols, terna[k])
            cols = gr.distribuisci(deck)
            assert all(len(candidati & set(c)) == 1 for c in cols)


# ════════════════════ controllo della destinazione: altra cosa ══════════════

def test_la_destinazione_dipende_dalle_raccolte_8_su_216():
    """Per ogni (c, t) esattamente 8 terne su 216 portano c in t."""
    for c in range(27):
        arrivi = {}
        for terna in itertools.product(gr.SIGLE, repeat=3):
            _, deck = _storia_fisica(c, terna)
            arrivi[deck.index(c)] = arrivi.get(deck.index(c), 0) + 1
        assert arrivi == {t: 8 for t in range(27)}


# ══════════════════════════════ B12 (§ 7.2.13) ══════════════════════════════

def test_b12_esempio_della_disposizione_100():
    osservati = ("DSC", "DSC", "CSD")                      # R0, R1, R2
    mescolamenti = tuple(gr.IMPILAMENTO_DI[r] for r in osservati)
    assert mescolamenti == ("CDS", "CDS", "CSD")           # M_i = R_i^-1
    assert gr.numero_tavola(mescolamenti) == 100
    ritorno = tb.ritorno(100)
    assert ritorno.mescolamenti == ("DSC", "DSC", "CSD")
    assert tuple(gr.IMPILAMENTO_DI[m] for m in ritorno.mescolamenti) == (
        "CDS", "CDS", "CSD")                               # libro: R = CDS, CDS, CSD


@pytest.mark.parametrize("numero", range(216))
def test_b12_il_riavvolgimento_annulla_la_storia_osservata(numero):
    import random
    mazzo = list(range(27))
    random.Random(numero).shuffle(mazzo)                   # ordine ignoto
    deck = list(mazzo)
    for m in gr.mescolamenti_da_numero(numero):
        deck = gr.raccogli(gr.distribuisci(deck), m)
    for m in tb.ritorno(numero).mescolamenti:
        deck = gr.raccogli(gr.distribuisci(deck), m)
    assert deck == mazzo


def test_b12_tre_raccolte_al_centro_portano_a_13_da_ogni_posizione():
    """«Raccolgo in mezzo il mazzetto indicato»: la sede C a ogni fase."""
    for n in range(27):
        deck = list(range(27))
        for _ in range(3):
            cols = gr.distribuisci(deck)
            a = next(g for g in range(3) if n in cols[g])
            altri = [g for g in range(3) if g != a]
            deck = cols[altri[0]] + cols[a] + cols[altri[1]]   # a in mezzo
        assert deck.index(n) == 13
