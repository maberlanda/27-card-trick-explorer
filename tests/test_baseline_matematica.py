"""Baseline matematica del repository: rete di sicurezza per i compartimenti successivi.

Non introduce funzionalita' ne' API nuove: fissa le convenzioni e le cardinalita'
gia' verificate e registrate in `docs/decisions/GIT_BASELINE_AND_RECONCILIATION.md` (sezione 7),
cosi' che siano riproducibili dal repository e non da uno script esterno.

Convenzioni protette:
    T[carta] = posizione di destinazione        deck[posizione] = carta
    M[T[i], i] = 1                              (a o b)[i] = a[b[i]]
    M(a o b) = M(a) @ M(b)                      MSC(n) = 9*(n mod 3) + n//3
    MSC^3 = I                                   forma canonica K o MSC^k

Oracoli e loro indipendenza (dichiarazione esplicita, richiesta dalla baseline):

* `simula_fisicamente` e' riscritta qui dalla descrizione del gioco e NON usa
  `distribuisci`/`raccogli`/`esegui_partita`: e' un oracolo indipendente dalla
  simulazione del programma.
* `kron_oracle` calcola il prodotto di Kronecker dalle cifre in base 3 senza
  passare per le matrici: e' indipendente da `build_Ai_matrix`.
* Il confronto interno fra percorso vettoriale e percorso matriciale (quello del
  `selftest` del programma) NON e' un confronto fra oracoli indipendenti: entrambi
  derivano dalla stessa convenzione `M[T[i], i] = 1` e dalle stesse tabelle PERM3.
  Per questo i test qui sotto lo affiancano con l'oracolo fisico, non lo
  sostituiscono.
* Le implementazioni matematiche oggi duplicate nel package (inverse, tabelle
  GEN3/MSC, tavole di Cayley) restano tali di proposito: servono da oracoli
  reciproci finche' non esistera' un sostituto realmente indipendente.

Tutti i controlli stanno nella suite ordinaria: i due piu' costosi (le 419.904
coppie di H e le 419.904 composizioni canoniche) misurano insieme circa 1,5 s, e
non meritano quindi una selezione separata. Per eseguire solo questa baseline:

    pytest tests/test_baseline_matematica.py
"""
import itertools

import numpy as np
import pytest

from gioco27.core import gioco_reale as gr
from gioco27.core import analysis as an
from gioco27.core import kronecker as kr
from gioco27.core import permutations as pm
from gioco27.core.algebra import CanonicalForm
from gioco27.core.constants import PERM3, PERM3_J, _MSC_PERM
from gioco27.core.group_theory import get_group_data

MSC_FORMULA = tuple(9 * (n % 3) + n // 3 for n in range(27))
ID27 = tuple(range(27))
NOMI3 = sorted(PERM3)


def comp(a, b):
    """(a o b)[i] = a[b[i]] — composizione diretta, senza tabelle precalcolate."""
    return tuple(a[b[i]] for i in range(len(b)))


def potenza_msc(k):
    p = ID27
    for _ in range(k):
        p = comp(MSC_FORMULA, p)
    return p


def kron_oracle(f2, f1, f0):
    """(f2 x f1 x f0)[n] per n = 9*n2 + 3*n1 + n0, dalle sole cifre base 3."""
    return tuple(9 * f2[n // 9] + 3 * f1[(n // 3) % 3] + f0[n % 3] for n in range(27))


def simula_fisicamente(sigle, rovesciamenti=(False, False, False)):
    """Oracolo fisico indipendente: distribuzione round-robin e impilamento inverso.

    Riscritto dalla descrizione del gioco; usa di `gioco_reale` soltanto la
    tabella delle sigle, non le sue funzioni di simulazione.
    """
    mazzo = list(range(27))
    for sigla, rovescia in zip(sigle, rovesciamenti):
        colonne = [mazzo[i::3] for i in range(3)]
        mescolamento = gr.MESCOLAMENTO[sigla]
        inversa = [0, 0, 0]
        for gruppo, cifra in enumerate(mescolamento):
            inversa[cifra] = gruppo
        mazzo = colonne[inversa[0]] + colonne[inversa[1]] + colonne[inversa[2]]
        if rovescia:
            mazzo = mazzo[::-1]
    T = [0] * 27
    for posizione, carta in enumerate(mazzo):
        T[carta] = posizione
    return T


@pytest.fixture(scope="module")
def gruppo():
    return get_group_data()


@pytest.fixture(scope="module")
def elementi_H():
    """I 648 elementi di H = G semidiretto C3, come K o MSC^k."""
    arr = get_group_data().kron_arr
    return [comp(g.tolist(), potenza_msc(k)) for k in range(3) for g in arr]


# ───────────────────────────── S3 e MSC ─────────────────────────────────────

def test_s3_e_i_nomi_gen3():
    assert sorted(tuple(v) for v in PERM3.values()) == sorted(itertools.permutations(range(3)))
    assert len(PERM3) == 6
    assert sorted(PERM3_J) == ["I_3", "R_U"]
    assert tuple(PERM3_J["I_3"]) == (0, 1, 2)
    assert tuple(PERM3_J["R_U"]) == (2, 1, 0)


def test_msc_coincide_con_la_formula():
    assert tuple(_MSC_PERM) == MSC_FORMULA


def test_matrice_msc_rispetta_la_convenzione_delle_colonne():
    M = np.asarray(pm.MSC)
    assert M.sum() == 27
    assert tuple(int(np.argmax(M[:, i])) for i in range(27)) == MSC_FORMULA


def test_msc_al_cubo_e_identita():
    assert potenza_msc(3) == ID27
    assert potenza_msc(1) != ID27 and potenza_msc(2) != ID27


# ──────────────────────── Kronecker e convenzioni ───────────────────────────

def test_kronecker_coincide_con_oracolo_a_cifre():
    for a, b, c in itertools.product(NOMI3, repeat=3):
        atteso = kron_oracle(PERM3[a], PERM3[b], PERM3[c])
        assert tuple(pm.mat_to_perm27(pm.build_Ai_matrix(a, b, c))) == atteso


def test_convenzione_matriciale_e_roundtrip():
    rng = np.random.default_rng(20260922)
    for _ in range(50):
        perm = rng.permutation(27)
        M = pm.perm27_to_mat(perm)
        assert M.sum() == 27
        assert all(M[perm[i], i] == 1 for i in range(27))
        assert tuple(pm.mat_to_perm27(M)) == tuple(int(x) for x in perm)


def test_omomorfismo_matrice_composizione(gruppo):
    rng = np.random.default_rng(7)
    arr = gruppo.kron_arr
    for i in rng.choice(216, 20, replace=False):
        for j in rng.choice(216, 20, replace=False):
            a, b = arr[int(i)].tolist(), arr[int(j)].tolist()
            assert np.array_equal(pm.perm27_to_mat(comp(a, b)),
                                  pm.perm27_to_mat(a) @ pm.perm27_to_mat(b))


def test_intreccio_msc_kronecker():
    """MSC o (a x b x c) = (c x a x b) o MSC, su tutte le 216 terne."""
    for a, b, c in itertools.product(NOMI3, repeat=3):
        sinistra = comp(MSC_FORMULA, kron_oracle(PERM3[a], PERM3[b], PERM3[c]))
        destra = comp(kron_oracle(PERM3[c], PERM3[a], PERM3[b]), MSC_FORMULA)
        assert sinistra == destra


# ──────────────────────────── il gruppo G ───────────────────────────────────

def test_g_ha_216_elementi_distinti(gruppo):
    arr = gruppo.kron_arr
    assert len(arr) == 216
    assert len({a.tobytes() for a in arr}) == 216


def test_g_chiuso_e_tavola_di_cayley_corretta(gruppo):
    """46.656 = 216^2 coppie: chiusura e tavola verificate con la composizione diretta."""
    arr = gruppo.kron_arr
    indice = {arr[k].tobytes(): k for k in range(216)}
    cayley = gruppo.cayley
    for i in range(216):
        riga = arr[i][arr]
        for j in range(216):
            atteso = indice.get(riga[j].tobytes())
            assert atteso is not None
            assert int(cayley[i, j]) == atteso


def test_g_identita_inversi_e_associativita(gruppo):
    arr = gruppo.kron_arr
    identita = [k for k in range(216) if arr[k].tolist() == list(range(27))]
    assert len(identita) == 1
    e = identita[0]
    cayley, inverse = gruppo.cayley, gruppo.inverse
    for i in range(216):
        assert int(cayley[i, int(inverse[i])]) == e
        assert int(cayley[i, e]) == i == int(cayley[e, i])
    rng = np.random.default_rng(11)
    for _ in range(500):
        i, j, k = (int(x) for x in rng.integers(0, 216, 3))
        assert int(cayley[int(cayley[i, j]), k]) == int(cayley[i, int(cayley[j, k])])


# ──────────────────────────── il gruppo H ───────────────────────────────────

def test_h_ha_648_elementi_distinti(elementi_H):
    assert len(elementi_H) == 648
    assert len(set(elementi_H)) == 648


def test_h_e_chiuso_su_tutte_le_coppie(elementi_H):
    """419.904 = 648^2 coppie esaustive."""
    insieme = set(elementi_H)
    arr = np.array(elementi_H, dtype=np.int32)
    for i in range(648):
        riga = arr[i][arr]
        for j in range(648):
            assert tuple(riga[j].tolist()) in insieme


# ───────────────────── fisica del gioco contro algebra ──────────────────────

def test_simulazione_del_programma_contro_oracolo_fisico():
    for n in range(216):
        mescolamenti = gr.mescolamenti_da_numero(n)
        assert gr.T_da_partita(mescolamenti) == simula_fisicamente(mescolamenti)


def test_formula_a_cifre_contro_oracolo_fisico():
    """Oracoli davvero indipendenti: carta-per-carta contro aritmetica base 3."""
    for n in range(216):
        mescolamenti = gr.mescolamenti_da_numero(n)
        assert gr.T_da_tabellone(mescolamenti) == simula_fisicamente(mescolamenti)


def test_1728_configurazioni_di_stadio():
    """216 sequenze x 8 combinazioni di rovesciamento."""
    contate = 0
    for mescolamenti in itertools.product(gr.SIGLE, repeat=3):
        for rovesciamenti in itertools.product((False, True), repeat=3):
            assert (gr.T_da_partita(mescolamenti, rovesciamenti)
                    == simula_fisicamente(mescolamenti, rovesciamenti))
            contate += 1
    assert contate == 1728


# ───────────────────────── tavola 216 e trucco ──────────────────────────────

def test_tavola_216_bigezione_assi():
    assi = {}
    for n in range(216):
        riga = gr.riga_tavola(n)
        terna = riga["assi"]
        assi[terna] = assi.get(terna, 0) + 1
        mescolamenti, numero = gr.tabellone_da_assi(*terna)
        assert numero == n
        assert mescolamenti == riga["mescolamenti"]
    assert len(assi) == 216 and max(assi.values()) == 1


def test_statistiche_della_tavola_invarianti():
    st = gr.statistiche_tavola()
    assert st["periodi"] == {1: 1, 2: 63, 3: 26, 6: 126}
    assert st["autoinverse"] == 64
    assert len(st["tipi_ciclo"]) == 7


def test_729_coppie_carta_bersaglio():
    """Ogni piano prodotto dal solutore verificato con l'oracolo fisico."""
    contate = 0
    for carta in range(27):
        for bersaglio in range(27):
            piano = gr.risolvi_trucco(carta, bersaglio)
            assert simula_fisicamente(piano["mescolamenti"])[carta] == bersaglio
            contate += 1
    assert contate == 729


def test_cicli_ordine_e_periodo():
    for n in range(216):
        T = gr.T_da_tabellone(gr.mescolamenti_da_numero(n))
        cicli = an.cycle_decomposition(T)
        assert sorted(x for ciclo in cicli for x in ciclo) == list(range(27))
        mcm = 1
        for ciclo in cicli:
            a, b = mcm, len(ciclo)
            while b:
                a, b = b, a % b
            mcm = mcm * len(ciclo) // a
        assert an.order_of(T) == mcm == gr.periodo(T)


# ─────────────────────── decomposizioni e forma canonica ────────────────────

def test_bersaglio_in_g_ha_46656_decomposizioni_uniche(gruppo):
    bersaglio = gruppo.kron_arr[7].tolist()
    risultati = kr.find_all_kron_decompositions(bersaglio)
    assert len(risultati) == 46656
    assert len({tuple(tuple(s) for s in d) for d in risultati}) == 46656
    for d in risultati[:500]:
        assert tuple(kr.decomposition_perm(d)) == tuple(bersaglio)


def test_bersaglio_fuori_da_g_non_ha_decomposizioni(gruppo):
    fuori = list(comp(MSC_FORMULA, gruppo.kron_arr[7].tolist()))
    assert kr.find_all_kron_decompositions(fuori) == []


def test_try_kron_decompose_riconosce_esattamente_g(gruppo, elementi_H):
    arr = gruppo.kron_arr
    assert all(kr.try_kron_decompose(g.tolist()) is not None for g in arr)
    fuori = elementi_H[216:]          # le due classi con k = 1 e k = 2
    assert len(fuori) == 432
    assert all(kr.try_kron_decompose(list(p)) is None for p in fuori)


def forme_canoniche():
    return [CanonicalForm(kron_factors=[list(PERM3[a]), list(PERM3[b]), list(PERM3[c])],
                          msc_exp=k)
            for k in range(3) for a, b, c in itertools.product(NOMI3, repeat=3)]


def test_forma_canonica_parametrizza_h(elementi_H):
    perms = [tuple(f.to_perm()) for f in forme_canoniche()]
    assert len(perms) == 648
    assert len(set(perms)) == 648
    assert set(perms) == set(elementi_H)


def test_composizione_canonica_su_tutte_le_coppie():
    """419.904 = 648^2: la legge canonica contro la composizione delle permutazioni."""
    forme = forme_canoniche()
    perm_di = {}
    for f in forme:
        perm_di[(tuple(map(tuple, f.kron_factors)), f.msc_exp)] = tuple(f.to_perm())
    coppie = [(f, perm_di[(tuple(map(tuple, f.kron_factors)), f.msc_exp)]) for f in forme]
    for f1, p1 in coppie:
        for f2, p2 in coppie:
            r = f1.compose(f2)
            chiave = (tuple(map(tuple, r.kron_factors)), r.msc_exp)
            assert perm_di[chiave] == comp(p1, p2)
