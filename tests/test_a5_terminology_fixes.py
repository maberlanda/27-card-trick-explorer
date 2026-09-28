"""Regressioni mirate per i due rilievi terminologici di A5-FIX."""

from gioco27 import i18n


IT = i18n.CATALOGS["it"]
EN = i18n.CATALOGS["en"]


def test_i_1728_oggetti_sono_procedure_nei_contesti_rilevati_da_a5():
    for catalog in (IT, EN):
        for key in ("guide.s10.count", "tooltip.verify"):
            text = catalog[key]
            assert "Procedure" in text
            assert not any(term in text.lower() for term in (
                "sequenz", "combinaz", "sequence", "combination",
            ))


def test_i_quattro_calchi_inglesi_usano_sequence():
    keys = (
        "glossary.long.return",
        "glossary.long.arrangement",
        "glossary.short.checkpoint",
        "cli.error.sequence",
    )
    for key in keys:
        assert "sequence" in EN[key].lower()
        assert "succession" not in EN[key].lower()


def test_i_termini_restano_disponibili_nei_contesti_distinti():
    assert "sequence" in EN["sequence.origin_vs_path"].lower()
    assert "combination" in EN["analysis.status.summary"].lower()
    assert EN["session.tab.sequence"] == "Succession (L90)"
