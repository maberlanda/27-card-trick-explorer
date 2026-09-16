"""D1-D3: ambito dei gruppi, conteggi e indici tecnici, senza correggere D4."""
import math
from pathlib import Path
import re

import pytest

from gioco27.gui.protocol_dialog import _ai_phase_html, generate_protocol_html


GUIDE = Path(__file__).resolve().parents[1] / "gioco27" / "gui" / "guide.py"


def _guide_text(language="it"):
    """Guida renderizzata: dal Blocco i18n 14 i testi stanno nei cataloghi."""
    from gioco27.gui.guide import render_guide_segments
    return "".join(text for _tag, text in render_guide_segments(language))


@pytest.fixture
def text():
    return _guide_text("it")


def _check_groups(text):
    # S3 ha 3! elementi e tre tipi ciclici: identita', trasposizioni, 3-cicli.
    order, classes = math.factorial(3) ** 3, 3 ** 3
    assert re.findall(r"\|G\|\s*=\s*(\d+)", text) == [str(order)]
    counts = re.findall(r"\b(\d+) classi", text)
    assert counts and set(counts) == {str(classes)}
    assert not re.search(r"\b648\b|\b17 classi", text)
    assert "gruppo del gioco G = S₃³" in text
    assert "gruppo esteso G_ext = ⟨S₃³, MSC⟩" in text
    assert "MSC non appartiene a G" in text
    assert re.search(r"per ogni T ∈ G = S₃³ esistono\s+46 656 decomposizioni", text)
    assert "per MSC si ottengono 0 decomposizioni a tre stadi" in text
    assert not re.search(r"per ogni T ∈ G\s*=\s*⟨S₃³, MSC⟩", text)
    assert "Aᵢ ∈ GEN3⊗GEN3⊗GEN3" in text


def test_d1_gruppi_distinti_e_decomposizioni_nel_sottogruppo(text):
    _check_groups(text)


@pytest.mark.parametrize("obsolete", ["|G| = 648", "17 classi di coniugio",
                                     "per ogni T ∈ G = ⟨S₃³, MSC⟩ esistono sempre 46 656 decomposizioni"])
def test_d1_rifiuta_vecchie_affermazioni_anche_se_coesistono(text, obsolete):
    with pytest.raises(AssertionError):
        _check_groups(text + "\n" + obsolete)


def _check_counts(text):
    decompositions = (math.factorial(3) ** 3) ** 2
    complete = decompositions * (2 ** 3) ** 3
    fixed_level = (math.factorial(3) ** 2 * 2 ** 3) ** 3
    assert complete == fixed_level == 23_887_872
    assert complete > 20_000_000
    fmt = lambda n: f"{n:,}".replace(",", " ")
    assert f"{fmt(decompositions)} × 8³ = {fmt(complete)}" in text
    assert not re.search(r"373[ .]?248|19[ .]?683[ .]?000", text)


def test_d2_conteggi_indipendenti_e_conseguenza_sul_limite(text):
    _check_counts(text)
    from gioco27.gui.guide import render_guide_segments
    segments = render_guide_segments("it")
    rows = [i for i, (tag, line) in enumerate(segments)
            if tag == "bullet" and line.strip().startswith("•  Un livello P fissato")]
    assert len(rows) == 1
    line = segments[rows[0]][1]
    assert line.split("→", 1)[1].split("(", 1)[0].strip() == "23 887 872"
    assert segments[rows[0] + 1] == ("bullet2", "     RIFIUTATO: oltre il limite\n")


@pytest.mark.parametrize("obsolete", ["373 248", "373.248", "19 683 000", "19.683.000"])
def test_d2_rifiuta_vecchi_conteggi_anche_se_coesistono(text, obsolete):
    with pytest.raises(AssertionError):
        _check_counts(text + "\n" + obsolete)


def test_d3_formule_tecniche_base_zero(text):
    assert not re.search(r"\b[PJ][3₃]", text)
    assert "Ogni stadio i (0, 1, 2)" in text
    assert "Ogni stadio i (1, 2, 3)" not in text
    assert "(3,2,1)" not in text
    assert "(2,1,0) → (0,2,1)" in text
    assert "Pᵢ = P2ᵢ ⊗ P1ᵢ ⊗ P0ᵢ" in text
    assert "Jᵢ = J2ᵢ ⊗ J1ᵢ ⊗ J0ᵢ" in text
    pairs = re.findall(r"\(P(\d)ᵢ\s*∘\s*J(\d)ᵢ\)", text)
    assert pairs == [("2", "0"), ("1", "2"), ("0", "1")] * 2
    assert "l'etichetta di stadio diventa P2xP1xP0" in text
    assert "dei tre Assi" in text  # riferimenti alle carte preservati


@pytest.mark.parametrize("stage", [1, 2, 3])
def test_d3_protocollo_separa_turno_ordinale_da_indice_algebrico(stage):
    triple = ("CDS_U", "SDC_U", "CSD_U")
    block = _ai_phase_html(triple, stage)
    assert f"FASE {stage}" in block  # fase fisica ordinale, senza cambiare le istruzioni
    assert f"A{stage - 1} = (CDS_U ⊗ SDC_U ⊗ CSD_U)" in block
    assert f"Cosa fa A{stage - 1}," in block
    assert "A3" not in block
    assert "f₂ = CDS_U" in block and "f₁ = SDC_U" in block and "f₀ = CSD_U" in block
    assert "f₃" not in block
    assert ("Fine del trucco" in block) == (stage == 3)


def test_d3_protocollo_completo_formule_e_istruzioni_coerenti():
    identity = ("SCD_U",) * 3
    output = generate_protocol_html(dict(perm=list(range(27)),
                                        decompositions=[(identity,) * 3]))
    assert re.findall(r"<strong>A(\d) =", output) == ["0", "1", "2"]
    assert "A2 ∘ MSC ∘ A1 ∘ MSC ∘ A0 ∘ MSC" in output
    assert "1ª distribuzione" in output and "1ª raccolta" in output
    assert "(f₂(i₂), f₁(i₁), f₀(i₀))" in output
    assert "A3" not in output
