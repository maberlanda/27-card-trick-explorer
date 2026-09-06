"""
Verifica della convenzione di conversione permutazione -> matrice.

Convenzione richiesta (matrice che agisce su vettori COLONNA):
    p[i] = j  significa  i -> j
    P e_i = e_{p[i]}     ==>     M[p[i], i] = 1     (riga = arrivo, colonna = partenza)
    composizione:  P_p @ P_q = P_{p∘q}  con (p∘q)[i] = p[q[i]]

Convenzione Kronecker funzionale:
    (p ⊗ q ⊗ r)[9*n2 + 3*n1 + n0] = 9*p[n2] + 3*q[n1] + r[n0].
"""
import itertools
import random

import numpy as np
import pytest

from gioco27.core.algebra import AlgebraEngine

# Le sei permutazioni locali di S_3
S3 = {
    "SCD": [0, 1, 2],
    "SDC": [0, 2, 1],
    "CSD": [1, 0, 2],
    "CDS": [1, 2, 0],
    "DSC": [2, 0, 1],
    "DCS": [2, 1, 0],
}
S3_LIST = list(S3.values())

mat = AlgebraEngine.perm_to_matrix
kron_perm = AlgebraEngine.kronecker3


def compose(p, q):
    """(p∘q)[i] = p[q[i]]  (prima q, poi p)."""
    return [p[q[i]] for i in range(len(q))]


def e(n, i):
    v = np.zeros(n, dtype=int)
    v[i] = 1
    return v


# ───────────────────────── matrici locali S_3 ───────────────────────────────

@pytest.mark.parametrize("name,p", list(S3.items()))
def test_column_convention_P_ei_equals_e_pi(name, p):
    P = mat(p)
    for i in range(3):
        assert np.array_equal(P @ e(3, i), e(3, p[i])), \
            f"{name}: P e_{i} deve essere e_{p[i]}"


def test_one_per_row_and_col():
    for p in S3_LIST:
        P = mat(p)
        assert np.all(P.sum(axis=0) == 1) and np.all(P.sum(axis=1) == 1)


def test_explicit_DSC_matrix():
    # DSC = [2,0,1]  ->  M[p[i], i] = 1
    assert np.array_equal(mat([2, 0, 1]), np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 0],
    ]))


def test_explicit_CDS_matrix():
    # CDS = [1,2,0]
    assert np.array_equal(mat([1, 2, 0]), np.array([
        [0, 0, 1],
        [1, 0, 0],
        [0, 1, 0],
    ]))


def test_S3_composition_is_matmul():
    # Per tutte le 36 coppie:  P_p @ P_q == P_{p∘q}
    for p, q in itertools.product(S3_LIST, repeat=2):
        assert np.array_equal(mat(p) @ mat(q), mat(compose(p, q)))


def test_CDS_DSC_inverses_and_transpose():
    CDS, DSC = [1, 2, 0], [2, 0, 1]
    assert compose(CDS, DSC) == [0, 1, 2]
    assert compose(DSC, CDS) == [0, 1, 2]
    assert np.array_equal(mat(CDS).T, mat(DSC))
    assert np.array_equal(mat(DSC).T, mat(CDS))


# ───────────────────────── Kronecker (216 triple) ───────────────────────────

def test_kron_matrix_equals_np_kron_all_216():
    for p, q, r in itertools.product(S3_LIST, repeat=3):
        k = kron_perm(p, q, r)
        lhs = mat(k)
        rhs = np.kron(np.kron(mat(p), mat(q)), mat(r))
        assert np.array_equal(lhs, rhs)


def test_kron_perm_functional_convention():
    for p, q, r in itertools.product(S3_LIST, repeat=3):
        k = kron_perm(p, q, r)
        for n2 in range(3):
            for n1 in range(3):
                for n0 in range(3):
                    n = 9 * n2 + 3 * n1 + n0
                    assert k[n] == 9 * p[n2] + 3 * q[n1] + r[n0]


def test_kron_matrix_acts_as_e_ki():
    # P_k e_i == e_{k[i]} per alcune triple rappresentative (tutte e 216 sarebbe lento)
    triples = [
        ([2, 0, 1], [0, 1, 2], [0, 1, 2]),   # DSC ⊗ SCD ⊗ SCD
        ([1, 2, 0], [0, 1, 2], [0, 1, 2]),   # CDS ⊗ SCD ⊗ SCD
        ([1, 2, 0], [2, 0, 1], [2, 1, 0]),   # mista
        ([0, 2, 1], [1, 0, 2], [1, 2, 0]),   # mista
    ]
    for p, q, r in triples:
        k = kron_perm(p, q, r)
        P = mat(k)
        for i in range(27):
            assert np.array_equal(P @ e(27, i), e(27, k[i]))


def test_kron_composition_block_triples_and_sample():
    # A∘B = (p∘a, q∘b, r∘c);  P_A @ P_B == P_{A∘B}
    block = [(x, [0, 1, 2], [0, 1, 2]) for x in S3_LIST]      # 6 triple "a blocchi"
    for A, B in itertools.product(block, repeat=2):           # 36 coppie
        _check_kron_comp(A, B)
    rng = random.Random(2024)
    for _ in range(120):                                      # campione casuale ampio
        A = tuple(rng.choice(S3_LIST) for _ in range(3))
        B = tuple(rng.choice(S3_LIST) for _ in range(3))
        _check_kron_comp(A, B)


def _check_kron_comp(A, B):
    p, q, r = A
    a, b, c = B
    PA = mat(kron_perm(p, q, r))
    PB = mat(kron_perm(a, b, c))
    PAB = mat(kron_perm(compose(p, a), compose(q, b), compose(r, c)))
    assert np.array_equal(PA @ PB, PAB)


# ───────────────────────── blocchi identità (disegno) ───────────────────────

def _identity_block_positions(M):
    """Posizioni (R, C) dei blocchi 9x9 uguali a I_9 nella matrice 27x27."""
    I9 = np.eye(9, dtype=int)
    pos = []
    for R in range(3):
        for C in range(3):
            if np.array_equal(M[9 * R:9 * R + 9, 9 * C:9 * C + 9], I9):
                pos.append((R, C))
    return sorted(pos)


def test_blocks_DSC_SCD_SCD():
    # DSC ⊗ SCD ⊗ SCD : blocco 0->2, 1->0, 2->1
    k = kron_perm([2, 0, 1], [0, 1, 2], [0, 1, 2])
    assert k[0] == 18 and k[9] == 0 and k[18] == 9   # 0->blocco2, 1->blocco0, 2->blocco1
    M = mat(k)
    assert _identity_block_positions(M) == sorted([(2, 0), (0, 1), (1, 2)])


def test_blocks_CDS_SCD_SCD_is_transpose_of_DSC():
    # CDS ⊗ SCD ⊗ SCD : blocco 0->1, 1->2, 2->0
    k = kron_perm([1, 2, 0], [0, 1, 2], [0, 1, 2])
    M = mat(k)
    assert _identity_block_positions(M) == sorted([(1, 0), (2, 1), (0, 2)])
    # è la trasposta del caso DSC
    kd = kron_perm([2, 0, 1], [0, 1, 2], [0, 1, 2])
    assert np.array_equal(M.T, mat(kd))


def test_consistency_with_perm_to_mat3():
    # La conversione generale deve coincidere con perm_to_mat3 sul 3x3
    from gioco27.core.permutations import perm_to_mat3
    for p in S3_LIST:
        assert np.array_equal(mat(p), perm_to_mat3(p).astype(int))
