"""M02 — le convenzioni sugli indici sono verificate, non soltanto dichiarate.

Il glossario sta in `gioco27/core/dominio.py`:

    stage_index  0,1,2   quale stadio (lo 0 agisce per primo), T = S2 o S1 o S0
    digit_index  0,1,2   quale cifra di n = 9*n2 + 3*n1 + n0 (0 = meno significativa)
    base 1       storica numerazione del programma C, conservata nei formati esportati

Questi test fissano l'ordine degli argomenti delle primitive del dominio: se
qualcuno invertisse P0 e P2 "per coerenza con una docstring", fallirebbero.
La matematica sottostante e' gia' coperta da `test_baseline_matematica.py` e non
viene qui ricontrollata.
"""
import itertools

import pytest

from gioco27.core.constants import PERM3, PERM3_J
from gioco27.core.permutations import (Ai_label, build_Ai_matrix, build_J27,
                                       build_P27, compute_Ai_symbolic,
                                       compute_stage, mat_to_perm27,
                                       stage_label)

NOMI3 = sorted(PERM3)
IDENT = "SCD_U"          # identita' fra i nomi GEN3
IDENT_J = "I_3"


def kron_da_cifre(f2, f1, f0):
    """(f₂ ⊗ f₁ ⊗ f₀)[n], scritto direttamente sulle cifre in base 3."""
    return tuple(9 * f2[n // 9] + 3 * f1[(n // 3) % 3] + f0[n % 3] for n in range(27))


# ───────────────────── ordine degli argomenti: P e J ────────────────────────

@pytest.mark.parametrize("nome", [n for n in sorted(PERM3) if n != "SCD_U"])
def test_build_P27_primo_argomento_agisce_sulla_cifra_0(nome):
    """`build_P27(p0n, p1n, p2n)`: p0n tocca la cifra MENO significativa."""
    perm = tuple(mat_to_perm27(build_P27(nome, IDENT, IDENT)))
    assert perm == kron_da_cifre(PERM3[IDENT], PERM3[IDENT], PERM3[nome])


@pytest.mark.parametrize("nome", [n for n in sorted(PERM3) if n != "SCD_U"])
def test_build_P27_terzo_argomento_agisce_sulla_cifra_2(nome):
    perm = tuple(mat_to_perm27(build_P27(IDENT, IDENT, nome)))
    assert perm == kron_da_cifre(PERM3[nome], PERM3[IDENT], PERM3[IDENT])


def test_build_P27_ordine_completo():
    for a, b, c in itertools.product(NOMI3, repeat=3):
        perm = tuple(mat_to_perm27(build_P27(a, b, c)))     # (p0, p1, p2)
        assert perm == kron_da_cifre(PERM3[c], PERM3[b], PERM3[a])


def test_build_J27_stesso_ordine_di_build_P27():
    for a, b, c in itertools.product(sorted(PERM3_J), repeat=3):
        perm = tuple(mat_to_perm27(build_J27(a, b, c)))     # (j0, j1, j2)
        assert perm == kron_da_cifre(PERM3_J[c], PERM3_J[b], PERM3_J[a])


def test_build_Ai_matrix_ordine_opposto_cifra_piu_significativa_per_prima():
    """`build_Ai_matrix(f2, f1, f0)`: qui il PRIMO argomento è la cifra 2."""
    for a, b, c in itertools.product(NOMI3, repeat=3):
        perm = tuple(mat_to_perm27(build_Ai_matrix(a, b, c)))
        assert perm == kron_da_cifre(PERM3[a], PERM3[b], PERM3[c])
    assert Ai_label("A", "B", "C") == "(A x B x C)"


# ───────────────────── chiavi di filtro ↔ argomenti ─────────────────────────

def test_le_chiavi_di_filtro_arrivano_in_ordine_di_cifra():
    """Uno stadio (p0,p1,p2,j0,j1,j2) entra posizionalmente in compute_stage."""
    stadio = ("CDS_U", IDENT, IDENT, IDENT_J, IDENT_J, IDENT_J)
    P, _J, _S = compute_stage(*stadio)
    assert tuple(mat_to_perm27(P)) == kron_da_cifre(
        PERM3[IDENT], PERM3[IDENT], PERM3["CDS_U"])       # p0 tocca la cifra 0


def test_compute_Ai_symbolic_restituisce_f2_f1_f0():
    """f_k = P_k ∘ J_((k+1) mod 3), dal più significativo al meno."""
    from gioco27.core.permutations import compose3

    stadio = ("CDS_U", "SDC_U", "DCS_U", "R_U", IDENT_J, "R_U")
    p0n, p1n, p2n, j0n, j1n, j2n = stadio
    f2, f1, f0 = compute_Ai_symbolic(*stadio)
    assert f2 == compose3(p2n, j0n)
    assert f1 == compose3(p1n, j2n)
    assert f0 == compose3(p0n, j1n)


# ───────────────────────── etichette esportate ──────────────────────────────

def test_stage_label_usa_lo_stage_index_base_0_e_l_ordine_kronecker():
    etichetta = stage_label(0, "p0", "p1", "p2", "j0", "j1", "j2")
    assert etichetta == "Stage0 = (p2 x p1 x p0) o MSC o (j2 x j1 x j0)"
    assert stage_label(2, "a", "b", "c", "d", "e", "f").startswith("Stage2 = ")


def test_numerazione_storica_documentata_dove_sopravvive():
    """I moduli che riproducono il formato del C devono dichiarare la base 1."""
    import pathlib

    radice = pathlib.Path(__file__).resolve().parents[1] / "gioco27" / "core"
    for nome in ("detail.py", "detail_pdf.py"):
        testo = (radice / nome).read_text(encoding="utf-8")
        assert "stage_index" in testo, f"{nome}: manca il raccordo con la numerazione del dominio"
    glossario = (radice / "dominio.py").read_text(encoding="utf-8")
    for voce in ("stage_index", "digit_index", "p0/p1/p2", "base 1"):
        assert voce in glossario
