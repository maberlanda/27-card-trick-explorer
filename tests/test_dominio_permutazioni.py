"""R04 — contratti agli ingressi delle API matematiche pubbliche.

Prima di questa correzione varie funzioni presumevano di ricevere una
permutazione valida: `orbit_of([1, 1], 0)` non terminava, altre restituivano
numeri privi di significato o sollevavano IndexError a caso.

La politica di validazione e' descritta in `gioco27/core/dominio.py`; qui viene
esercitata ai confini reali, insieme alla prova che gli ingressi validi
continuano a produrre esattamente gli stessi risultati.
"""
import os
import pathlib
import subprocess
import sys

import numpy as np
import pytest

from gioco27.core.analysis import (cycle_decomposition, cycle_type, orbit_of,
                                   order_of)
from gioco27.core.dominio import (PermutazioneNonValida, valida_indice,
                                  valida_permutazione)
from gioco27.core.gioco_reale import (T_da_tabellone, mescolamenti_da_numero,
                                      parita, periodo, punti_fissi, tipo_ciclo)
from gioco27.core.kronecker import (appartiene_a_G, appartiene_a_Gamma,
                                    appartiene_a_H,
                                    find_all_kron_decompositions,
                                    try_kron_decompose)

RADICE = pathlib.Path(__file__).resolve().parents[1]
IDENTITA = list(range(27))
T100 = T_da_tabellone(mescolamenti_da_numero(100))


# ───────────────────────────── il contratto ─────────────────────────────────

@pytest.mark.parametrize("valida", [
    [0, 1, 2],
    (2, 0, 1),
    range(27),
    np.array([2, 0, 1]),
    np.arange(27),
    IDENTITA,
    T100,
])
def test_ingressi_validi_sono_accettati(valida):
    out = valida_permutazione(valida)
    assert isinstance(out, tuple)
    assert sorted(out) == list(range(len(out)))
    assert all(type(v) is int for v in out)


@pytest.mark.parametrize("invalida, motivo", [
    ([0, 0, 1], "duplicati"),
    ([-1, 0, 1], "valore negativo"),
    ([0, 1, 3], "valore >= n"),
    ([], "input vuoto"),
    ("012", "tipo errato: str"),
    ({0: 1}, "tipo errato: dict"),
    ([True, False], "tipo errato: bool"),
    ([0.0, 1.0], "tipo errato: float"),
    (["0", "1"], "tipo errato: str negli elementi"),
    (42, "tipo errato: non iterabile"),
    (np.zeros((3, 3), dtype=int), "array non monodimensionale"),
])
def test_ingressi_invalidi_sono_rifiutati(invalida, motivo):
    with pytest.raises(PermutazioneNonValida):
        valida_permutazione(invalida)


def test_lunghezza_errata_quando_n_e_richiesto():
    with pytest.raises(PermutazioneNonValida, match="lunghezza"):
        valida_permutazione([0, 1, 2], 27)
    with pytest.raises(PermutazioneNonValida, match="lunghezza"):
        valida_permutazione(IDENTITA + [27], 27)
    assert valida_permutazione(IDENTITA, 27) == tuple(range(27))


def test_valida_indice():
    assert valida_indice(np.int64(5), 27) == 5
    for cattivo in (-1, 27, True, 1.0, "3"):
        with pytest.raises(PermutazioneNonValida):
            valida_indice(cattivo, 27)


# ───────────────────────── analisi ciclica (R04) ────────────────────────────

PROGRAMMA_ORBITA = """
import sys
sys.path.insert(0, {radice!r})
from gioco27.core.analysis import orbit_of
from gioco27.core.dominio import PermutazioneNonValida
try:
    orbit_of([1, 1], 0)
    print("NESSUN ERRORE")
except PermutazioneNonValida:
    print("ERRORE CONTROLLATO")
"""


def test_orbita_su_ingresso_non_bigettivo_termina(tmp_path):
    """Regressione di R04: `orbit_of([1, 1], 0)` non terminava affatto.

    Il sottoprocesso con timeout e' una protezione del test, non un rimedio
    applicativo: se la funzione tornasse a ciclare, il test fallirebbe invece di
    bloccare la suite.
    """
    res = subprocess.run(
        [sys.executable, "-c", PROGRAMMA_ORBITA.format(radice=str(RADICE))],
        capture_output=True, text=True, timeout=30,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == "ERRORE CONTROLLATO"


@pytest.mark.parametrize("funzione", [cycle_decomposition, order_of, cycle_type,
                                      periodo, tipo_ciclo, punti_fissi, parita])
@pytest.mark.parametrize("invalida", [[1, 1], [0, 5], [-1, 0], [], "abc", [True, False]])
def test_api_cicliche_rifiutano_ingressi_invalidi(funzione, invalida):
    with pytest.raises(PermutazioneNonValida):
        funzione(invalida)


def test_orbit_of_rifiuta_una_carta_fuori_dominio():
    with pytest.raises(PermutazioneNonValida):
        orbit_of(IDENTITA, 27)
    with pytest.raises(PermutazioneNonValida):
        orbit_of(IDENTITA, -1)
    with pytest.raises(PermutazioneNonValida):
        orbit_of(IDENTITA, True)


def test_risultati_validi_invariati():
    """La validazione non cambia nulla per gli ingressi leciti."""
    assert orbit_of(T100, 0) == _orbita_riferimento(T100, 0)
    assert cycle_decomposition(IDENTITA) == [[i] for i in range(27)]
    assert order_of(IDENTITA) == 1
    assert cycle_type(IDENTITA) == {1: 27}
    assert periodo(T100) == order_of(T100)
    assert tuple(sorted(len(c) for c in cycle_decomposition(T100))) == tipo_ciclo(T100)
    assert punti_fissi(T100) == sum(1 for i, v in enumerate(T100) if i == v)
    assert parita(T100) in (1, -1)


def _orbita_riferimento(perm, carta):
    """Oracolo minimo: iterazione diretta, indipendente da orbit_of."""
    out, cur = [carta], perm[carta]
    while cur != carta:
        out.append(cur)
        cur = perm[cur]
    return out


def test_orbite_coincidono_con_l_oracolo():
    for carta in range(27):
        assert orbit_of(T100, carta) == _orbita_riferimento(T100, carta)


# ─────────────────────── decomposizioni e appartenenza ──────────────────────

@pytest.mark.parametrize("invalida", [[1, 1], IDENTITA[:-1], [0.0] * 27, "x" * 27])
def test_decomposizioni_rifiutano_bersagli_invalidi(invalida):
    with pytest.raises(PermutazioneNonValida):
        find_all_kron_decompositions(invalida)
    with pytest.raises(PermutazioneNonValida):
        try_kron_decompose(invalida)


def test_decomposizioni_valide_invariate():
    assert len(find_all_kron_decompositions(IDENTITA)) == 46656
    assert try_kron_decompose(IDENTITA) is not None


# appartenenza (nomenclatura del libro): H (216), Γ \ H (432), fuori da Γ
def _comp(a, b):
    return tuple(a[b[i]] for i in range(len(b)))


@pytest.fixture(scope="module")
def famiglie():
    from gioco27.core.constants import _MSC_PERM
    from gioco27.core.group_theory import get_group_data
    msc = tuple(_MSC_PERM)
    H = [g.tolist() for g in get_group_data().kron_arr]
    potenze = [tuple(range(27))]
    for _ in range(2):
        potenze.append(_comp(msc, potenze[-1]))
    gamma = [_comp(g, k) for k in potenze for g in H]
    return H, gamma


def test_appartenenza_a_H(famiglie):
    H, gamma = famiglie
    assert len(H) == 216
    assert all(appartiene_a_H(g) for g in H)
    assert not any(appartiene_a_H(p) for p in gamma[216:])      # Γ \ H


def test_alias_legacy_appartiene_a_G_e_H():
    """Fase P: `appartiene_a_G` resta come alias legacy del gruppo di 216."""
    assert appartiene_a_G is appartiene_a_H


def test_appartenenza_a_Gamma(famiglie):
    H, gamma = famiglie
    assert len(set(gamma)) == 648
    assert all(appartiene_a_Gamma(p) for p in gamma)


def test_fuori_da_Gamma(famiglie):
    """Una trasposizione di due carte non e' in Γ: H e Γ sono sottoinsiemi propri di S27."""
    _H, gamma = famiglie
    fuori = list(range(27))
    fuori[0], fuori[1] = fuori[1], fuori[0]
    assert tuple(fuori) not in set(gamma)
    assert not appartiene_a_H(fuori)
    assert not appartiene_a_Gamma(fuori)
