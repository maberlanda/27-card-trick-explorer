"""
Stadi e fattori sono numerati a BASE 0.

Fino alla 3.0.3 gli stadi erano 1, 2, 3 e i fattori P1/P2/P3, J1/J2/J3 —
sfasati di uno rispetto a tutto il resto del programma, che è a base 0: cifre
ternarie i₂i₁i₀, posizioni 0-26, numerazione D# da 0, flag di rovesciamento
M0/M1/M2. Nella stessa pagina del PDF dettagliato lo stesso stadio compariva
come «Mescolamento 1» e come «M0».

Ora P_k agisce sulla cifra i_k, e lo Stadio k è il k-esimo. Questi test
impediscono il ritorno alla numerazione precedente.
"""
import re

import pytest

from gioco27.core.combinations import (CHIAVI_FILTRO, CHIAVI_J, CHIAVI_P,
                                       count_combinations_ex,
                                       iter_combinations_ex, valida_filtri)
from gioco27.core.constants import ANY
from gioco27.core.permutations import CSV_HEADER


def _filtro(**kw):
    base = {k: ANY for k in CHIAVI_FILTRO}
    base.update(kw)
    return base


# ────────────────────────────── chiavi dei filtri ──────────────────────────

def test_chiavi_a_base_zero():
    assert CHIAVI_P == ('p0', 'p1', 'p2')
    assert CHIAVI_J == ('j0', 'j1', 'j2')


def test_chiavi_legacy_rifiutate():
    """
    Non basta ignorarle: la vecchia `p2` (terzine) è la nuova `p1`, quindi un
    filtro con i nomi vecchi verrebbe interpretato in modo silenziosamente
    diverso. Meglio un errore esplicito.
    """
    vecchio = {'p1': ANY, 'p2': ANY, 'p3': ANY, 'j1': ANY, 'j2': ANY, 'j3': ANY}
    with pytest.raises(ValueError, match="obsolete"):
        valida_filtri([vecchio, vecchio, vecchio])


def test_chiavi_mancanti_rifiutate():
    incompleto = {'p0': ANY, 'p1': ANY}
    with pytest.raises(ValueError, match="mancanti"):
        valida_filtri([incompleto, incompleto, incompleto])


def test_le_funzioni_pubbliche_validano():
    vecchio = {'p1': ANY, 'p2': ANY, 'p3': ANY, 'j1': ANY, 'j2': ANY, 'j3': ANY}
    for fn in (count_combinations_ex, lambda f: list(iter_combinations_ex(f))):
        with pytest.raises(ValueError):
            fn([vecchio, vecchio, vecchio])


# ─────────────────────────── intestazioni del CSV ──────────────────────────

def test_intestazioni_csv_a_base_zero():
    assert CSV_HEADER[1].startswith("Stage0")
    assert CSV_HEADER[2].startswith("Stage1")
    assert CSV_HEADER[3].startswith("Stage2")
    assert CSV_HEADER[4].startswith("A0")
    assert CSV_HEADER[5].startswith("A1")
    assert CSV_HEADER[6].startswith("A2")
    unite = " ".join(CSV_HEADER)
    for vecchio in ("Stage3", "A3", "P3", "J3"):
        assert vecchio not in unite, f"{vecchio}: numerazione a base 1"


def test_formula_csv_coerente_con_la_base_zero():
    assert "P2xP1xP0" in CSV_HEADER[1]
    assert "J2xJ1xJ0" in CSV_HEADER[1]
    assert "(P2oJ0) x (P1oJ2) x (P0oJ1)" in CSV_HEADER[4]
    assert "A2 o MSC o A1 o MSC o A0 o MSC" in CSV_HEADER[7]


# ─────────────────── la formula incrociata in forma chiusa ─────────────────

def test_regola_incrociata_f_k_uguale_P_k_composto_J_k_piu_1():
    """
    In base 0 la regola degli indici incrociati diventa una formula sola:
        f_k = P_k ∘ J_(k+1 mod 3)
    Con i vecchi nomi si leggeva come tre casi separati (P3←J1, P2←J3, P1←J2):
    era la numerazione a nascondere la regolarità.
    """
    from gioco27.core.permutations import compose3, compute_Ai_symbolic

    P = ("CDS_U", "DSC_U", "DCS_U")          # P0, P1, P2
    J = ("R_U", "I_3", "R_U")                # J0, J1, J2
    # compute_Ai_symbolic vuole (p0,p1,p2,j0,j1,j2) e restituisce (f2,f1,f0)
    f2, f1, f0 = compute_Ai_symbolic(*P, *J)
    atteso = [compose3(P[k], J[(k + 1) % 3]) for k in range(3)]
    assert [f0, f1, f2] == atteso


# ─────────────────── il PDF dettagliato usa la stessa base ────────────────

def test_mescolamenti_e_flag_M_hanno_la_stessa_base(tmp_path):
    """
    Il difetto che ha originato la rinumerazione: nella stessa pagina lo stesso
    stadio era «Mescolamento 1» e «M0».
    """
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    from pypdf import PdfReader
    from gioco27.core.detail_pdf import _generate_sequential, annotate_like_c

    params = [[("SCD_U", "SCD_U", "CDS_U", "I_3", "I_3", "I_3")] * 3]
    labels, transposes = annotate_like_c(params)
    out = tmp_path / "x.pdf"
    _generate_sequential(str(out), params, labels, transposes)
    testo = PdfReader(str(out)).pages[0].extract_text()

    mescolamenti = sorted(re.findall(r"Mescolamento (\d)", testo))
    flag = sorted(re.findall(r"M(\d) = ", testo))
    assert mescolamenti == ["0", "1", "2"], f"trovati: {mescolamenti}"
    assert flag == ["0", "1", "2"], f"trovati: {flag}"
    assert mescolamenti == flag, "stessa base per mescolamenti e flag M"


# ──────────── la Guida descrive il preset come lo fa il codice ─────────────

def test_guida_descrive_il_preset_come_il_codice():
    """
    La Guida affermava che il preset «Gioco Reale» lascia libero il fattore
    delle CARTE e fissa gli altri due. È il contrario: libera il fattore dei
    PACCHETTI (la raccolta fisica). Errore preesistente, trovato rileggendo
    riga per riga durante la rinumerazione.
    """
    import pathlib
    radice = pathlib.Path(__file__).resolve().parent.parent

    codice = (radice / "gioco27" / "gui" / "filter_frame.py").read_text(encoding="utf-8")
    preset = codice.split("def set_preset_gioco_reale", 1)[1].split("def ", 1)[0]
    fissati = set(re.findall(r"self\._vars\['(P\d)'\]\[0\]\.set\('SCD_U'\)", preset))
    assert fissati == {"P0", "P1"}, f"il preset fissa {fissati}"
    libero = ({"P0", "P1", "P2"} - fissati).pop()
    assert libero == "P2"

    # Dal Blocco i18n 14 il testo della Guida sta nei cataloghi: si legge la
    # Guida renderizzata (in italiano), non il sorgente di guide.py.
    from gioco27.gui.guide import render_guide_segments
    guida = "".join(testo for _tag, testo in render_guide_segments("it"))
    assert f"{libero} varia" in guida or f"{libero} libero" in guida, \
        f"la Guida non dice che {libero} è il fattore libero"
    for f in sorted(fissati):
        assert f"{f} = " in guida, f"la Guida non dice che {f} è fissato"
    # e non deve dire il contrario
    assert "solo P0 varia" not in guida
    assert "P0 libero" not in guida


def test_i_conti_del_preset_tornano():
    """6 scelte per il fattore libero × 2 per le J uniformi = 12 per stadio."""
    filtri = [_filtro(p0="SCD_U", p1="SCD_U", j_uniform=True) for _ in range(3)]
    assert count_combinations_ex(filtri) == 12 ** 3 == 1728
