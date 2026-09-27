"""Regressioni mirate per la revisione linguistica italiana A3-FIX."""

from pathlib import Path
import re

import pytest

from gioco27 import i18n


ROOT = Path(__file__).resolve().parents[1]
IT = i18n.CATALOGS["it"]


def test_reggenza_istruzioni_e_titolo_dell_analisi_sono_naturali():
    assert IT["analysis.open_explorer"] == "Apri in Explorer"
    assert IT["analysis.title"] == "Analisi della molteplicità delle permutazioni"
    assert "Fai doppio clic" in IT["analysis.status.summary"]
    assert "Fai clic" in IT["distribution.placeholder_chart"]
    italiano = "\n".join(IT.values())
    for residuo in ("Apri nel Explorer", "doppio-click", "Clicca", "Clic su",
                    "Si preme", "Analisi Molteplicità"):
        assert residuo not in italiano


def test_accordi_rimedio_parser_e_operando_gen3_sono_espliciti():
    assert "La terna" in IT["guide.s02.coordinates"]
    assert "rappresenta" in IT["guide.s02.coordinates"]
    assert "Questa è la conseguenza diretta" in IT["guide.s07.rotation"]
    assert "A₂ appartiene a GEN3⊗GEN3⊗GEN3" in IT[
        "guide.s16.decompositions.body"]
    errore = IT["explorer.error.type3_result"]
    assert "permutazione su 3 elementi" in errore
    assert "prodotto di Kronecker con tre fattori" in errore


@pytest.mark.parametrize("count", [0, 1, 2])
def test_messaggi_dinamici_sono_grammaticali_per_zero_uno_due(count):
    i18n.set_language("it")
    testi = [
        i18n.tr("status.count_summary", count=count),
        i18n.tr("explorer.decomposition.found", count=count, target="T"),
        i18n.tr("explorer.decomposition.found_cache", count=count, target="T"),
        i18n.tr("explorer.parse.kron_count", count=count),
        i18n.tr("export.completed", count=count, folder="C:/tmp", files="x"),
        i18n.tr("practice.real.recovery.count", count=count),
        i18n.tr("cli.replay.steps", n=count),
        i18n.tr("cli.sequence", n=count, row=0, back="SCD SCD SCD"),
    ]
    sbagliati = re.compile(
        r"\b1 (?:procedure|combinazioni|pagine|decomposizioni|file|"
        r"continuazioni|fattori)\b", re.IGNORECASE)
    assert all(not sbagliati.search(testo) for testo in testi)


def test_notazione_ricca_e_numeri_italiani_sono_uniformi():
    i18n.set_language("it")
    assert i18n.format_integer(1_728) == "1 728"
    assert "S₂₇" in IT["guide.i6.domains"] and "S₃" in IT["guide.i6.domains"]
    assert "3²⁺ⁱ" in IT["recognition.sums.formula"]
    assert "T⁻¹" in IT["guide.s17.inverse_formula"]
    assert "0,2 s" in IT["guide.s16.decompositions.body"]
    assert "1 728³ = 5 159 780 352" in (ROOT / "README.md").read_text(
        encoding="utf-8")


def test_stadio_tappa_inversa_rovesciamento_carta_e_posizione_restano_distinti():
    assert IT["glossary.term.stage"] == "Stadio"
    assert IT["sequence.stage"] == "Tappa v{k} su {n}"
    assert "disposizione intermedia v_k" in IT["glossary.long.checkpoint"]
    assert "T⁻¹" in IT["glossary.long.inverse"]
    assert IT["guide.s05.row.R_U"].startswith("Rovesciamento")
    assert IT["simulator.practice.step_target"].endswith("Carta scelta: C{card:02d}")
    assert IT["spectator.target"] == "Posizione bersaglio:"


def test_identificatori_csv_e_json_restano_stabili():
    from gioco27.core.permutations import CSV_HEADER
    from gioco27.services import esperimento as E

    assert [voce.split("  [", 1)[0] for voce in CSV_HEADER] == [
        "#", "Stage0", "Stage1", "Stage2", "A0", "A1", "A2",
        "T_simbolica", "T_permutazione",
    ]
    documento = E.crea_documento({}, seed=None, titolo="", nota="")
    assert documento["schema"] == "gioco27.esperimento"
    assert documento["schema_version"] == 1
    assert set(documento) == {
        "schema", "schema_version", "convenzioni", "programma", "algoritmi",
        "id", "creato", "modificato", "annotazioni", "seed", "voci",
        "presentazione", "cronologia", "fonti", "digest",
    }


def test_etichette_umane_degli_export_non_riusano_lo_schema():
    assert IT["export.document.pdf.stage"].startswith("Stadio ")
    assert IT["export.document.pdf.initial_arrangement"] == "Disposizione iniziale"
    assert IT["common.yes"] == "sì" and IT["common.no"] == "no"
    standard = (ROOT / "gioco27/core/combinations.py").read_text(encoding="utf-8")
    dettaglio = (ROOT / "gioco27/core/detail_pdf.py").read_text(encoding="utf-8")
    assert 'txt("R:"' not in standard
    assert '"Stage_i  (27x27)"' not in standard
    assert 'draw_deck(d["dispositions"][0], x, yB, "DISP_INIZIO")' not in dettaglio
    assert "'TRUE' if _reversed_stage" not in dettaglio


def test_il_calco_ordine_pubblico_non_ricompare_nelle_superfici_correnti():
    correnti = [
        ROOT / "README.md",
        ROOT / "gioco27/i18n.py",
        ROOT / "docs/release/NOTE_VERSIONE_4.0.0.md",
        ROOT / "docs/audits/A1_FINAL_MATHEMATICAL_AUDIT.md",
        ROOT / "docs/audits/A1_FINAL_MATHEMATICAL_AUDIT.csv",
        ROOT / "docs/audits/A3_FINAL_ITALIAN_LANGUAGE_AUDIT.md",
    ]
    for percorso in correnti:
        assert "ordine pubblico" not in percorso.read_text(encoding="utf-8")


def test_prestiti_rimasti_sono_tecnici_o_nomi_dell_interfaccia():
    italiano = re.sub(r"\{[^}]+\}", "", "\n".join(IT.values()))
    for residuo in ("How-To", "Target", "Step", "Play", "Replay", "len ",
                    "workflow", "worker"):
        assert residuo not in italiano
    for ammesso in ("Explorer", "NumPy", "PDF", "CSV", "JSON", "HTML"):
        assert ammesso in italiano
