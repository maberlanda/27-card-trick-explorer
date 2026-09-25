"""Compartimento I1 — caratterizzazione dei fatti matematici, senza il servizio.

Questi test fissano i contratti che il servizio delle procedure (I1) dovra'
rispettare, usando SOLO il core esistente e oracoli indipendenti scritti qui:

* la formula cifra per cifra del libro (cap. 5, § 5.1.17; App. D § 5), che
  non passa per `compute_T_perm`;
* l'enumerazione del preset «Gioco Reale» dei filtri (P0 = P1 = SCD_U,
  P2 libero, J uniforme): 6³·2³ = 1728 combinazioni;
* l'oracolo fisico carta per carta di `gioco_reale` (convenzione B:
  rovesciamento DOPO la raccolta).

Convenzione canonica approvata (DP3 = A): il rovesciamento dello stadio i
avviene PRIMA della distribuzione, T_i = (S_i ⊗ I ⊗ I) ∘ MSC ∘ J^εi.
Riferimenti: docs/decisions/V4_PRE_I1_PRODUCT_DECISIONS.md §§ 3, 7.
"""
from collections import Counter

import pytest

from gioco27.core import gioco_reale as gr
from gioco27.core.combinations import iter_combinations_ex
from gioco27.core.constants import ANY, PERM3
from gioco27.core.permutations import compute_T_perm

R = (2, 1, 0)
IDENT3 = (0, 1, 2)
J27 = tuple(26 - i for i in range(27))
BIT = ((0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1),
       (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1))      # indice m = 4e1+2e2+e3


def _c3(a, b):
    return tuple(a[b[i]] for i in range(3))


def _pot(p, e):
    return p if e else IDENT3


def _comp27(a, b):
    """(a ∘ b)[i] = a[b[i]]."""
    return tuple(a[b[i]] for i in range(27))


def _T_libro(mesc, eps):
    """Oracolo indipendente: formula cifra per cifra del libro (convenzione A).

    M2 = S3∘R^e3∘R^e2∘R^e1,  M1 = R^e3∘S2∘R^e2∘R^e1,  M0 = R^e3∘R^e2∘S1∘R^e1
    T(n) = 9·M2(n2) + 3·M1(n1) + M0(n0)
    """
    s1, s2, s3 = (gr.MESCOLAMENTO[s] for s in mesc)
    e1, e2, e3 = eps
    r1, r2, r3 = _pot(R, e1), _pot(R, e2), _pot(R, e3)
    m2 = _c3(s3, _c3(r3, _c3(r2, r1)))
    m1 = _c3(r3, _c3(s2, _c3(r2, r1)))
    m0 = _c3(r3, _c3(r2, _c3(s1, r1)))
    return tuple(9 * m2[n // 9] + 3 * m1[(n // 3) % 3] + m0[n % 3]
                 for n in range(27))


def _T_fisico_B(mesc, rov):
    """Oracolo fisico: rovesciamento DOPO la raccolta (convenzione B)."""
    return tuple(gr.T_da_partita(mesc, tuple(bool(x) for x in rov)))


def _procedure():
    for m in range(8):
        for n in range(216):
            yield gr.mescolamenti_da_numero(n), BIT[m]


def _preset_gioco_reale():
    """(mescolamenti, eps, T) per le 1728 combinazioni del preset Gioco Reale."""
    stadio = dict(p0="SCD_U", p1="SCD_U", p2=ANY, j0=ANY, j1=ANY, j2=ANY,
                  j_uniform=True)
    for params in iter_combinations_ex([dict(stadio), dict(stadio), dict(stadio)]):
        mesc, eps = [], []
        for p0, p1, p2, j0, j1, j2 in params:
            assert p0 == p1 == "SCD_U" and j0 == j1 == j2
            sigla = [s for s, v in gr.MESCOLAMENTO.items()
                     if tuple(PERM3[p2]) == v]
            mesc.append(sigla[0])
            eps.append(1 if j0 == "R_U" else 0)
        yield tuple(mesc), tuple(eps), tuple(compute_T_perm(params)[2])


@pytest.fixture(scope="module")
def preset():
    return list(_preset_gioco_reale())


# ═════════════════════════ modello A e core autorevole ══════════════════════

def test_il_preset_gioco_reale_e_il_dominio_delle_1728_procedure(preset):
    assert len(preset) == 1728
    assert len({(m, e) for m, e, _ in preset}) == 1728


def test_formula_del_libro_coincide_col_core_su_1728(preset):
    diversi = [(m, e) for m, e, T in preset if _T_libro(m, e) != T]
    assert diversi == []


def test_216_trasformazioni_otto_procedure_ciascuna(preset):
    conta = Counter(T for _, _, T in preset)
    assert len(conta) == 216
    assert set(conta.values()) == {8}


def test_profilo_dei_rovesciamenti_in_ogni_classe(preset):
    classi = {}
    for _, e, T in preset:
        classi.setdefault(T, []).append(sum(e))
    assert {tuple(sorted(v)) for v in classi.values()} == {(0, 1, 1, 1, 2, 2, 2, 3)}
    assert len(classi) == 216


# ═════════════════════════ DP3: oracolo fisico B ════════════════════════════

def test_A_si_ottiene_dall_oracolo_fisico_B():
    """T_A(S; e1,e2,e3) = T_B(S; e2,e3,0) ∘ J^e1   (1728/1728)."""
    for mesc, (e1, e2, e3) in _procedure():
        destra = _T_fisico_B(mesc, (e2, e3, 0))
        if e1:
            destra = _comp27(destra, J27)
        assert _T_libro(mesc, (e1, e2, e3)) == destra, (mesc, e1, e2, e3)


def test_B_si_ottiene_da_A_con_rovesciamento_finale():
    """T_B(S; r1,r2,r3) = J^r3 ∘ T_A(S; 0,r1,r2)   (1728/1728)."""
    for mesc, (r1, r2, r3) in _procedure():
        sinistra = _T_libro(mesc, (0, r1, r2))
        if r3:
            sinistra = _comp27(J27, sinistra)
        assert _T_fisico_B(mesc, (r1, r2, r3)) == sinistra


def test_A_e_B_allo_stesso_indice_non_sono_equivalenti():
    uguali = sum(_T_libro(m, e) == _T_fisico_B(m, e) for m, e in _procedure())
    assert uguali == 512


CSD3 = ("CSD", "CSD", "CSD")


@pytest.mark.parametrize("gesto,assi", [
    ("A:000", (13, 0, 26)),
    ("A:010", (25, 2, 12)),      # = B:100 (dopo la raccolta 1)
    ("A:001", (22, 8, 9)),       # = B:010 (dopo la raccolta 2)
    ("A:100", (26, 0, 13)),      # mazzo iniziale capovolto: nessun analogo in B
    ("B:001", (13, 26, 0)),      # dopo l'ultima raccolta: nessun analogo in A
    ("A:011", (10, 6, 23)),      # = B:110
    ("B:101", (1, 24, 14)),
    ("B:111", (16, 20, 3)),
])
def test_esempio_discriminante_csd3(gesto, assi):
    """Memo pre-I1 § 3.3: (CSD,CSD,CSD) distingue A da B."""
    conv, bit = gesto.split(":")
    e = tuple(int(b) for b in bit)
    T = _T_libro(CSD3, e) if conv == "A" else _T_fisico_B(CSD3, e)
    assert (T[0], T[13], T[26]) == assi


def test_esempio_discriminante_a_indice_uguale():
    assert _T_libro(CSD3, (1, 0, 0)) != _T_fisico_B(CSD3, (1, 0, 0))


def test_esempio_del_libro_paragrafo_2_5():
    """SCD, DCS, J, SCD (J dopo la seconda raccolta) = A con eps=(0,0,1)."""
    atteso = (20, 19, 18, 23, 22, 21, 26, 25, 24, 11, 10, 9, 14, 13, 12,
              17, 16, 15, 2, 1, 0, 5, 4, 3, 8, 7, 6)
    mesc = ("SCD", "DCS", "SCD")
    assert _T_fisico_B(mesc, (0, 1, 0)) == atteso
    assert _T_libro(mesc, (0, 0, 1)) == atteso
    # stessa trasformazione della disposizione semplice #185
    assert tuple(gr.T_da_tabellone(gr.mescolamenti_da_numero(185))) == atteso


# ═════════════════════════ costi del solutore storico ═══════════════════════

def _cifre(n):
    return (n % 3, (n // 3) % 3, n // 9)          # (d0, d1, d2)


def test_kappa_del_solutore_storico_in_forma_chiusa():
    cicliche_totali, migliorabili = 0, 0
    for c in range(27):
        for t in range(27):
            mesc = gr.risolvi_trucco(c, t)["mescolamenti"]
            k1 = sum(s != "SCD" for s in mesc)
            k2 = sum(s in ("CDS", "DSC") for s in mesc)
            cc, ct = _cifre(c), _cifre(t)
            assert k1 == sum(a != b for a, b in zip(cc, ct))
            assert k2 == sum({a, b} == {0, 2} for a, b in zip(cc, ct))
            cicliche_totali += k2
            migliorabili += k2 > 0
    assert migliorabili == 386
    assert cicliche_totali == 486
