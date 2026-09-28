"""Regressioni A4-FIX per inglese, equivalenza IT/EN e contratti stabili."""

from __future__ import annotations

import csv
import re

import pytest

from gioco27 import i18n


@pytest.fixture(autouse=True)
def _italian_default():
    i18n.set_language("it")
    yield
    i18n.set_language("it")


def test_type3_e_riga_tavola_sono_espliciti_e_equivalenti():
    i18n.set_language("en")
    message = i18n.tr("explorer.error.type3_result")
    assert "permutation of 3 elements" in message
    assert "27 positions" in message
    assert "Kronecker product with three factors" in message
    assert "type 3" not in message and "type-27" not in message
    assert i18n.tr("nav.in_table", number=17) == "Table row #17"


def test_diciotto_template_dinamici_restano_naturali_per_0_1_2():
    i18n.set_language("en")
    cases = {
        "status.count_summary": lambda n: dict(count=n),
        "settings.cache_info": lambda n: dict(entries=n, size=1.0),
        "explorer.decomposition.found_cache": lambda n: dict(count=n, target="T⁻¹"),
        "explorer.decomposition.found": lambda n: dict(count=n, target="T⁻¹"),
        "explorer.decomposition.combinations": lambda n: dict(count=n),
        "explorer.decomposition.table_status": lambda n: dict(count=n),
        "explorer.decomposition.exported": lambda n: dict(count=n, path="out.csv"),
        "export.document.more_decompositions": lambda n: dict(count=n),
        "export.completed": lambda n: dict(count=n, folder="out", files="x"),
        "export.confirm.pdf": lambda n: dict(count=n),
        "export.confirm.pdf_detailed": lambda n: dict(count=n),
        "export.confirm.csv": lambda n: dict(count=n),
        "status.generation_workers": lambda n: dict(count=n),
        "practice.real.recovery.count": lambda n: dict(count=n),
        "practice.real.recovery.option": lambda n: dict(
            shuffles="SCD", changes=n, non_scd=n),
        "cli.replay.steps": lambda n: dict(n=n),
        "cli.sequence": lambda n: dict(n=n, row=0, back="SCD SCD SCD"),
        "sequence.return": lambda n: dict(
            n=n, codes="SCD SCD SCD", row=0, stages=n),
    }
    bad = re.compile(
        r"\b1\s+(?:combinations|files|decompositions|rows|processes|"
        r"procedures|Procedures|stages|changes|collections|pickups)\b"
    )
    assert len(cases) == 18
    for key, values in cases.items():
        for count in (0, 1, 2):
            rendered = i18n.tr(key, **values(count))
            assert "{" not in rendered, (key, count, rendered)
            assert not bad.search(rendered), (key, count, rendered)


def test_american_english_numeri_virgolette_e_notazione_ricca():
    text = "\n".join(i18n.CATALOGS["en"].values())
    forbidden = re.compile(
        r"\b(?:centre|analyse|analysed|colour|recognise|recognised|"
        r"realise|realised|catalogue|factorisation)\b",
        re.IGNORECASE,
    )
    assert not forbidden.search(text)
    assert "«" not in text and "»" not in text
    assert not re.search(r"\b\d{1,3}(?: \d{3})+\b", text)
    for rich in ("S₂₇", "S₃", "MSCᵏ", "3²⁺ⁱ", "⊗", "∘"):
        assert rich in text
    assert "Fibre" in text or "fibre" in text  # termine matematico motivato


def test_vincoli_semantici_restano_distinti():
    en = i18n.CATALOGS["en"]
    assert "During phase i" in en["guide.s19.intro"]
    assert "original stage count" in en["sequence.return"]
    assert "checkpoints can be reconstructed" in en["sequence.origin_vs_path"]
    assert "pickup permutation" in en["glossary.term.collection"]
    assert "three transformations Aᵢ" in en["explorer.decomposition.help_long"]
    assert "A Procedure is" in en["guide.i1.intro"]
    assert "physical procedure" in en["guide.s01.intro"]


def test_source_terms_sono_preservati():
    text = "\n".join(i18n.CATALOGS["en"].values())
    for term in (
        "simple arrangement", "Gaia", "Chronicle", "Jester", "Deck-World",
        "Seldon", "Psychohistory", "First Crisis", "Second Crisis",
    ):
        assert term.lower() in text.lower()


def test_csv_localizza_solo_le_descrizioni_e_preserva_lo_schema(tmp_path):
    from gioco27.core.analisi import SchemaNonRiconosciuto, riconosci_schema
    from gioco27.core.export_analisi import scrivi_output
    from gioco27.core.export_combinazioni import localized_csv_header
    from gioco27.core.permutations import CSV_HEADER

    stable_names = [value.split("  [", 1)[0] for value in CSV_HEADER]
    i18n.set_language("en")
    localized = localized_csv_header()
    assert [value.split("  [", 1)[0] for value in localized] == stable_names
    assert localized[-1] == "T_permutazione  [list 0..26]"
    assert CSV_HEADER[-1] == "T_permutazione  [lista 0..26]"

    path = tmp_path / "analysis.csv"
    scrivi_output([], path)
    with path.open(encoding="utf-8", newline="") as stream:
        header = next(csv.reader(stream, delimiter=";"))
    assert header == [
        "T_permutazione  [list 0..26]",
        "T_simboliche_distinte  [separated by , ]",
        "n_sim_distinte  [permutation multiplicity]",
    ]
    with pytest.raises(SchemaNonRiconosciuto) as caught:
        riconosci_schema(header)
    assert caught.value.codice == "non_importabile"
    assert caught.value.dati["schema"] == "analisi"


def test_cli_spiega_i_token_stabili_senza_rinominarli():
    from gioco27.cli import _parser

    i18n.set_language("en")
    parser = _parser()
    subparsers = parser._subparsers._group_actions[0].choices
    help_text = subparsers["export"].format_help()
    for token in ("successione", "replay", "cronologia", "proprieta", "mapping"):
        assert token in help_text
    assert "stable export token" in help_text
    assert "sequence" in help_text and "history" in help_text


def test_pdf_dettagliato_inglese_non_contiene_etichette_italiane(tmp_path):
    pytest.importorskip("reportlab")
    pypdf = pytest.importorskip("pypdf")
    from gioco27.core.detail_pdf import _new_detail_canvas, render_detail_pages

    i18n.set_language("en")
    params = [("SCD_U", "SCD_U", "SCD_U", "I_3", "I_3", "I_3")] * 3
    path = tmp_path / "detail-en.pdf"
    canvas, painter = _new_detail_canvas(str(path))
    render_detail_pages(
        canvas, [params], start_index=1, painter=painter,
        labels=["D#0"], transposes=[[]],
    )
    canvas.save()
    text = "\n".join(
        page.extract_text() or "" for page in pypdf.PdfReader(str(path)).pages
    )
    for expected in ("Shuffle 0", "stacking", "BOARD", "OF T"):
        assert expected in text
    for forbidden in ("Mescolamento", "impilamento", "TABELLONE"):
        assert forbidden not in text


def test_cataloghi_placeholder_e_identificatori_macchina_restano_stabili():
    from string import Formatter
    from gioco27.core.permutations import CSV_HEADER

    it, en = i18n.CATALOGS["it"], i18n.CATALOGS["en"]
    assert set(it) == set(en)
    formatter = Formatter()
    for key in it:
        it_fields = {name for _, name, _, _ in formatter.parse(it[key]) if name}
        en_fields = {name for _, name, _, _ in formatter.parse(en[key]) if name}
        assert it_fields == en_fields, key
    assert CSV_HEADER[0] == "#"
    assert CSV_HEADER[-1].startswith("T_permutazione  [")
