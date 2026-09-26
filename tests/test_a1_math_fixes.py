"""Regressioni mirate per i cinque issue matematici dell'audit A1.

Gli oracoli numerici sono riscritti qui con aritmetica elementare, senza
riutilizzare le funzioni di composizione, inversione o Kronecker del core.
"""

from pathlib import Path

import numpy as np

from gioco27.core import gioco_reale as gr
from gioco27.core.algebra import AlgebraEngine
from gioco27.core.permutations import compute_stage, mat_to_perm27
from gioco27.i18n import set_language, tr
from gioco27.services import riconoscimento as ric


IDENT3 = (0, 1, 2)
CDS = (1, 2, 0)
SDC = (0, 2, 1)
DCS = (2, 1, 0)
MSC = tuple(9 * (x % 3) + 3 * (x // 9) + (x // 3) % 3
            for x in range(27))


def _compose(a, b):
    return tuple(a[b[x]] for x in range(len(b)))


def _inverse(p):
    q = [0] * len(p)
    for x, y in enumerate(p):
        q[y] = x
    return tuple(q)


def _power(p, exponent):
    result = tuple(range(len(p)))
    for _ in range(exponent):
        result = _compose(p, result)
    return result


def _kron(factors):
    p2, p1, p0 = factors
    return tuple(9 * p2[x // 9] + 3 * p1[(x // 3) % 3] + p0[x % 3]
                 for x in range(27))


def _final_deck(transformation, initial=tuple(range(27))):
    final = [None] * 27
    for start, arrival in enumerate(transformation):
        final[arrival] = initial[start]
    return tuple(final)


def test_a1_math_01_inverse_matrix_uses_column_as_start_and_row_as_arrival():
    # C9 non e' un'involuzione; la sua inversa C18 evita una verifica ambigua.
    inverse_c9 = tuple((x + 18) % 27 for x in range(27))
    matrix = AlgebraEngine.perm_to_matrix(list(inverse_c9))
    start, arrival = 1, 19
    assert inverse_c9[start] == arrival
    assert matrix[arrival, start] == 1
    assert matrix[start, arrival] == 0

    set_language("it")
    italian = tr("guide.s17.right.body")
    assert "posizione j viene riportata alla posizione i" in italian
    assert "colonna j è la partenza" in italian
    set_language("en")
    english = tr("guide.s17.right.body")
    assert "position j is brought back to position i" in english
    assert "column j is the start" in english


def test_a1_math_02_public_kronecker_order_matches_ternary_oracle():
    p0, p1, p2 = CDS, SDC, DCS
    matrix = compute_stage("CDS_U", "SDC_U", "DCS_U",
                           "I_3", "I_3", "I_3")[0]
    actual = tuple(np.argmax(matrix[:, x]) for x in range(27))
    expected = _kron((p2, p1, p0))
    assert actual == expected

    for language in ("it", "en"):
        set_language(language)
        for key in ("filter.intro", "guide.s16.subtabs.items",
                    "guide.s17.inverse_formula"):
            value = tr(key, digits="0,1,2", msc_power="MSC",
                       ref_s17="s17", ref_s18="s18")
            assert "P₂" in value and "P₁" in value and "P₀" in value
            assert value.index("P₂") < value.index("P₁") < value.index("P₀")
            assert "P₃" not in value
        assert "f₂ x f₁ x f₀" in tr("cayley.help.intro")
        assert "(f₂,f₁,f₀)" in tr(
            "conjugacy.help.intro", classes="classi")

    source = (Path(__file__).resolve().parents[1] / "gioco27" / "gui" /
              "explorer_tab.py").read_text(encoding="utf-8")
    assert 'for lab in ("P₂", "P₁", "P₀")' in source
    assert '[f"f₂={f2}", f"f₁={f1}", f"f₀={f0}"]' in source


def test_a1_math_03_inverse_formula_rotates_by_k_for_every_exponent():
    factors = (CDS, SDC, DCS)  # asimmetrici: distinguono rot_k da rot_2k
    inverse_factors = tuple(_inverse(factor) for factor in factors)

    for k in range(3):
        transformation = _compose(_kron(factors), _power(MSC, k))
        expected_inverse = _inverse(transformation)
        rotated = inverse_factors[k:] + inverse_factors[:k]
        stated_formula = _compose(
            _kron(rotated), _power(MSC, (3 - k) % 3))
        assert stated_formula == expected_inverse
        identity = tuple(range(27))
        assert _compose(transformation, stated_formula) == identity
        assert _compose(stated_formula, transformation) == identity

        if k:
            wrong_steps = (2 * k) % 3
            wrong = inverse_factors[wrong_steps:] + inverse_factors[:wrong_steps]
            old_formula = _compose(
                _kron(wrong), _power(MSC, (3 - k) % 3))
            assert old_formula != expected_inverse

    for language in ("it", "en"):
        set_language(language)
        formula = tr("guide.s17.inverse_formula", msc_power="MSC^(3-k)")
        assert "rotₖ(K⁻¹)" in formula
        assert "rot₂ₖ" not in formula


def test_a1_math_04_reversal_is_before_the_deal_of_the_same_stage():
    stage = tuple(mat_to_perm27(compute_stage(
        "SCD_U", "SCD_U", "CDS_U", "R_U", "R_U", "R_U")[2]))
    pickup = _kron((CDS, IDENT3, IDENT3))
    reversal = tuple(26 - x for x in range(27))
    pre_deal = _compose(pickup, _compose(MSC, reversal))
    post_collection = _compose(reversal, _compose(pickup, MSC))
    assert stage == pre_deal
    assert stage != post_collection

    set_language("it")
    assert "prima della distribuzione dello stadio i" in tr("guide.s01.steps")
    assert "prima della distribuzione dello stadio i" in tr("guide.s05.intro")
    set_language("en")
    assert "before the deal of stage i" in tr("guide.s01.steps")
    assert "before the deal of stage i" in tr("guide.s05.intro")


def test_a1_math_05_a8_separability_requires_twin_decks_from_h():
    ta = tuple(gr.riga_tavola(91)["T"])
    tb = tuple(gr.riga_tavola(100)["T"])
    deck_a, deck_b = _final_deck(ta), _final_deck(tb)
    relative_twins = ric.trasformazione_relativa(deck_a, deck_b)
    assert relative_twins == _compose(tb, _inverse(ta))
    assert ric.separabile(relative_twins).separabile

    c1 = tuple((x + 1) % 27 for x in range(27))
    relative_arbitrary = ric.trasformazione_relativa(
        tuple(range(27)), _final_deck(c1))
    assert relative_arbitrary == c1
    assert not ric.separabile(relative_arbitrary).separabile

    set_language("it")
    italian = tr("guide.i5.other", digits="0,1,2")
    assert "T_A,T_B ∈ H" in italian and "non c'è questa garanzia" in italian
    set_language("en")
    english = tr("guide.i5.other", digits="0,1,2")
    assert "T_A,T_B ∈ H" in english and "no such guarantee" in english


def test_a1_source_tensions_are_explicit_and_match_the_oracles():
    set_language("it")
    reversals = tr("guide.i1.reversals")
    sums = tr("guide.i5.directions", digits="0,1,2")
    cuts = tr("guide.i3.errors")
    assert "Articolo base" in reversals and "senza rovesciamenti" in reversals
    assert "App. D" in reversals and "prima della distribuzione" in reversals
    assert "App. D, Teor. 6.4" in sums and "Articolo, Oss. 5.3" in sums
    assert "C9 e C18 stanno in H" in cuts and "altre 24" in cuts

    in_h = []
    outside_gamma = []
    for k in range(1, 27):
        cut = ric.traslazione(k)
        if ric.separabile(cut).separabile:
            in_h.append(k)
        if not ric.classe_estesa(cut).appartiene:
            outside_gamma.append(k)
    assert in_h == [9, 18]
    assert outside_gamma == [k for k in range(1, 27) if k not in (9, 18)]
