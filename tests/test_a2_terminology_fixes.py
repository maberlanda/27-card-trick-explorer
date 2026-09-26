"""Regressioni mirate per il vocabolario controllato di A2-FIX."""

import re

import pytest

from gioco27 import i18n
from gioco27.gui.glossary import GLOSSARIO_MATEMATICO, GLOSSARIO_NARRATIVO


IT = i18n.CATALOGS["it"]
EN = i18n.CATALOGS["en"]


def test_tavola_usa_trasformazione_e_disposizione_resta_lo_stato_vk():
    assert "216 trasformazioni" in IT["table.status_shown"]
    assert "216 transformations" in EN["table.status_shown"]
    assert IT["table.detail.heading"].startswith("Trasformazione #")
    assert EN["table.detail.heading"].startswith("Transformation #")
    assert IT["sequence.col.disposizione"] == "Disposizione vⱼ"
    assert EN["sequence.col.disposizione"] == "Arrangement vⱼ"
    assert "disposizione semplice" in IT["glossary.long.arrangement"].lower()
    assert "simple arrangement" in EN["glossary.long.arrangement"].lower()


@pytest.mark.parametrize("key", [
    "glossary.long.group_gamma", "glossary.long.coset", "guide.i6.sections",
    "lab.legacy_note", "lab.note.nota_gamma_r", "lab.cosets.intro",
])
def test_gamma_usa_msc_e_non_un_bare_r(key):
    for catalog in (IT, EN):
        value = catalog[key]
        assert "MSC" in value
        assert not re.search(r"H\s*∘\s*R(?:\b|[²³^])", value)


def test_rovesciamento_locale_e_ritorno_compresso_non_riusano_bare_r():
    assert "R_U" in IT["guide.i1.reversals"]
    assert "R_U" in EN["guide.i1.reversals"]
    for catalog in (IT, EN):
        assert "R = C" not in catalog["sequence.return"]
        assert "R = C" not in catalog["guide.s29.session.body"]
        assert "C{n}⁻¹" in catalog["sequence.return"]


def test_vettore_forma_canonica_e_firma_di_blocco_sono_distinti():
    assert IT["explorer.canonical_signature"] == "Vettore della permutazione"
    assert EN["explorer.canonical_signature"] == "Permutation vector"
    assert IT["glossary.term.canonical_form"] == "Forma canonica"
    assert EN["glossary.term.canonical_form"] == "Canonical form"
    assert IT["glossary.term.block_signature"] == "Firma di blocco"
    assert EN["glossary.term.block_signature"] == "Block signature"


@pytest.mark.parametrize("key", [
    "button.real_game", "status.real_game_preset", "tooltip.real_game",
    "guide.s10.title", "guide.s10.activate", "guide.s13.real_game.body",
    "guide.s25.real_game.steps", "guide.s29.verify.items", "guide.s31.steps",
    "guide.s33.a3",
])
def test_dominio_gioco_reale_e_1728_procedure(key):
    assert "Procedure" in IT[key]
    assert "Procedure" in EN[key]


def test_ordine_e_il_termine_principale_periodo_solo_alias_dichiarato():
    assert IT["table.col.period"] == "Ordine"
    assert EN["table.col.period"] == "Order"
    assert IT["explorer.period"] == "Ordine della permutazione"
    assert EN["explorer.period"] == "Permutation order"
    assert "alias" in IT["glossary.long.order"]
    assert "alias" in EN["glossary.long.order"]


def test_carta_scelta_e_posizione_bersaglio_sono_separate():
    assert IT["simulator.practice.step_target"].endswith("Carta scelta: C{card:02d}")
    assert EN["simulator.practice.step_target"].endswith("Chosen card: C{card:02d}")
    assert IT["spectator.target"] == "Posizione bersaglio:"
    assert EN["spectator.target"] == "Target position:"
    assert "carta scelta" in IT["practice.real.summary.card_target"].lower()
    assert "target position" in EN["practice.real.summary.card_target"].lower()


def test_inversa_e_rovesciamento_sono_distinti():
    assert IT["guide.s05.row.R_U"].startswith("Rovesciamento")
    assert EN["guide.s05.row.R_U"].startswith("Reversal")
    assert "T⁻¹" in IT["glossary.long.inverse"]
    assert "T⁻¹" in EN["glossary.long.inverse"]


def test_l90_usa_tappa_checkpoint_e_j_fissa_la_posizione_13():
    assert IT["sequence.stage"] == "Tappa v{k} su {n}"
    assert EN["sequence.stage"] == "Checkpoint v{k} of {n}"
    assert "posizione 13" in IT["lab.prop.j_fissa_solo_13"]
    assert "position 13" in EN["lab.prop.j_fissa_solo_13"]
    assert "carta 13" not in IT["lab.prop.j_fissa_solo_13"]
    assert "card 13" not in EN["lab.prop.j_fissa_solo_13"]


def test_glossario_a2_copre_le_lacune_in_entrambe_le_lingue():
    richiesti = {
        "index", "arrangement", "chosen_card", "target_position", "phase",
        "checkpoint", "column_pile", "cumulative_transform", "relative_transform",
        "twin_decks", "cycle_type", "cycle_structure", "orbit", "history",
        "path_replay", "block_signature", "recognition", "cut", "translation",
        "rotation",
    }
    assert richiesti <= set(GLOSSARIO_MATEMATICO)
    assert len(GLOSSARIO_MATEMATICO) == 56
    assert len(GLOSSARIO_NARRATIVO) == 7
    for term in richiesti:
        for field in ("term", "short", "long"):
            key = f"glossary.{field}.{term}"
            assert IT[key] and EN[key]


def test_source_terms_restano_disponibili_nei_contesti_marcati():
    italian = "\n".join(IT.values()).lower()
    english = "\n".join(EN.values()).lower()
    for term in ("disposizione semplice", "Gaia", "Cronaca", "Giullare",
                 "Mondo-di-Mazzo", "Seldon", "Psicostoria", "Prima Crisi",
                 "Seconda Crisi"):
        assert term.lower() in italian
    for term in ("simple arrangement", "Gaia", "Chronicle", "Jester",
                 "Deck-World", "Seldon", "Psychohistory", "First Crisis",
                 "Second Crisis"):
        assert term.lower() in english


def test_cronaca_non_e_il_nome_tecnico_del_grafo_delle_216():
    assert "216 trasformazioni" in IT["lab.graph.raccolte.meaning"]
    assert "216 transformations" in EN["lab.graph.raccolte.meaning"]
    assert "Cronache" not in IT["lab.graph.raccolte.meaning"]
    assert "Chronicles" not in EN["lab.graph.raccolte.meaning"]
