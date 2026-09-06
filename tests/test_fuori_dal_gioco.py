"""
Il PDF dettagliato deve restare leggibile anche fuori dalle 1728 del gioco.

Quando P1 o P2 non sono l'identità, o J non è uniforme, lo stadio non è una
raccolta singola ma un prodotto di Kronecker: l'etichetta passa da «CDS» a
«SCD×CSD×SDC», tre volte più lunga. A dimensione fissa le intestazioni dei
mazzi si sovrapponevano fra loro e la riga sotto la matrice sconfinava
nell'elenco delle trasposte.

C'era anche un difetto di merito: il PDF scriveva «M[SCD×CSD×SDC]». Nel
programma C `M[k]` è un INDICE nella tabella dei mescolamenti — un numero — e
per queste combinazioni quell'indice non esiste.
"""
import os
import re
import tempfile

import pytest

from gioco27.core.detail_pdf import _c_indices, _stage_label, adatta_testo


# ───────────────────────────── adattamento del testo ───────────────────────

def _misura(testo, corpo):
    """Misura finta: mezzo punto per carattere."""
    return len(testo) * corpo * 0.5


def test_testo_corto_resta_intatto():
    testo, corpo = adatta_testo("CDS", 78, _misura, size=6.6)
    assert (testo, corpo) == ("CDS", 6.6)


def test_testo_lungo_viene_rimpicciolito():
    testo, corpo = adatta_testo("SCD×CSD×SDC", 20, _misura,
                                size=6.6, min_size=3.0)
    assert testo.startswith("SCD"), "il testo non deve essere stravolto"
    assert corpo < 6.6, "doveva rimpicciolirsi"
    assert _misura(testo, corpo) <= 20


def test_testo_impossibile_viene_troncato():
    testo, corpo = adatta_testo("x" * 500, 20, _misura, size=6.6, min_size=4.0)
    assert testo.endswith("…"), "va troncato con l'ellissi"
    assert corpo == pytest.approx(4.0), "si ferma al corpo minimo"
    assert _misura(testo, corpo) <= 20


def test_adatta_testo_non_supera_mai_la_larghezza():
    for lunghezza in (1, 3, 11, 40, 200):
        for larghezza in (5, 20, 78, 150):
            testo, corpo = adatta_testo("a" * lunghezza, larghezza, _misura,
                                        size=8.0, min_size=4.0)
            assert _misura(testo, corpo) <= larghezza + 1e-9, \
                f"{lunghezza} caratteri in {larghezza} pt: sconfina"


# ─────────────────── etichette: indici M[] solo dove esistono ──────────────

GIOCO = [("SCD_U", "SCD_U", "CDS_U", "I_3", "I_3", "I_3")] * 3
FUORI = [("SDC_U", "CSD_U", "SCD_U", "I_3", "I_3", "I_3"),
         ("SDC_U", "CSD_U", "SCD_U", "I_3", "I_3", "I_3"),
         ("SCD_U", "SCD_U", "SCD_U", "I_3", "I_3", "I_3")]


def test_indici_c_solo_per_le_combinazioni_di_gioco():
    assert _c_indices(GIOCO) is not None
    assert _c_indices(FUORI) is None


def test_etichette_di_stadio():
    assert [_stage_label(p) for p in GIOCO] == ["CDS", "CDS", "CDS"]
    etichette = [_stage_label(p) for p in FUORI]
    assert etichette[0] == "SCD×CSD×SDC", "prodotto di Kronecker, non una sigla"
    assert etichette[2] == "SCD", "lo stadio 3 è di gioco: sigla corta"


def _testo_pagina(params_list):
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    from pypdf import PdfReader
    from gioco27.core.detail_pdf import _generate_sequential, annotate_like_c

    labels, transposes = annotate_like_c(params_list)
    d = tempfile.mkdtemp()
    p = os.path.join(d, "x.pdf")
    _generate_sequential(p, params_list, labels, transposes)
    return PdfReader(p).pages[0].extract_text()


def test_nessun_M_con_argomento_non_numerico():
    """
    «M[SCD×CSD×SDC]» era falso: l'argomento di M è per definizione un indice
    numerico nella tabella dei mescolamenti del programma C.
    """
    testo = _testo_pagina([FUORI])
    sospetti = re.findall(r"M\[[A-Za-z]", testo)
    assert not sospetti, f"M[] con argomento non numerico: {sospetti}"


def test_fuori_dal_gioco_lo_dichiara():
    testo = _testo_pagina([FUORI])
    assert "raccolte (P₂×P₁×P₀)" in testo
    assert "non definiti" in testo, \
        "va detto perché mancano gli indici M[]"
    assert "SCD×CSD×SDC" in testo, "l'etichetta vera dev'esserci"


def test_le_combinazioni_di_gioco_mantengono_gli_indici():
    """La correzione non deve togliere gli indici dove esistono davvero."""
    testo = _testo_pagina([GIOCO])
    assert re.search(r"M\[\s*\d+\]", testo), "gli indici M[k] devono restare"
    assert "mescolamenti [" in testo
    assert "impilamenti [" in testo
    assert "non definiti" not in testo


def test_intestazioni_dei_mazzi_su_due_righe():
    """
    Il titolo è ora separato dall'etichetta: «Mescolamento 1 =» su una riga e
    il prodotto di Kronecker sulla successiva, adattato alla colonna. Prima
    erano un'unica stringa che sconfinava sul mazzo accanto.
    """
    testo = _testo_pagina([FUORI])
    assert "Mescolamento 1 =" in testo
    assert "Mescolamento 1 = SCD×CSD×SDC" not in testo, \
        "titolo ed etichetta devono stare su righe distinte"
