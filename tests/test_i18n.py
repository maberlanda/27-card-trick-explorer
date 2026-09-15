"""Focused tests for the first Italian/English localization block."""

import json
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def italian_i18n_default():
    from gioco27.gui import i18n

    i18n.set_language("it")
    yield
    i18n.set_language("it")


def test_italian_is_the_default_language():
    from gioco27.gui.i18n import get_language, tr

    assert get_language() == "it"
    assert tr("button.cancel") == "Annulla"


def test_english_translation():
    from gioco27.gui.i18n import set_language, tr

    set_language("en")
    assert tr("button.cancel") == "Cancel"
    assert tr("status.completed") == "Completed"


def test_english_falls_back_to_italian_for_a_missing_key(monkeypatch):
    from gioco27.gui import i18n

    monkeypatch.delitem(i18n.CATALOGS["en"], "button.save")
    i18n.set_language("en")
    assert i18n.tr("button.save") == "Salva"


def test_named_placeholders_are_formatted():
    from gioco27.gui.i18n import set_language, tr

    assert tr("status.saved", filename="risultati.csv", count=12) == \
        "Salvato: risultati.csv (12)"
    set_language("en")
    assert tr("status.saved", filename="results.csv", count=12) == \
        "Saved: results.csv (12)"


def test_missing_key_in_both_catalogs_is_clear(monkeypatch):
    from gioco27.gui import i18n

    monkeypatch.delitem(i18n.CATALOGS["it"], "temporary.missing", raising=False)
    monkeypatch.delitem(i18n.CATALOGS["en"], "temporary.missing", raising=False)
    i18n.set_language("en")
    with pytest.raises(KeyError, match="Missing i18n key in Italian catalog"):
        i18n.tr("temporary.missing")


def test_invalid_i18n_language_is_rejected():
    from gioco27.gui.i18n import set_language

    with pytest.raises(ValueError, match="Unsupported language"):
        set_language("fr")


def test_main_window_title_is_localized():
    from gioco27.gui import app as app_module
    from gioco27.gui.i18n import set_language

    assert app_module._window_title("3.1.2") == \
        "Gioco delle 27 carte  v3.1.2  —  Analisi combinazioni"
    set_language("en")
    assert app_module._window_title("3.1.2") == \
        "27-card trick  v3.1.2  —  Combination analysis"


def test_main_notebook_labels_and_common_controls_are_localized():
    from gioco27.gui import app as app_module
    from gioco27.gui.i18n import set_language, tr

    assert app_module._shell_tab_text("tab.preview", "🔍") == \
        "  🔍  Anteprima  "
    assert app_module._shell_tab_text("tab.stage", number=0) == \
        "  Stadio 0  "
    assert tr("button.settings") == "Impostazioni"
    set_language("en")
    assert app_module._shell_tab_text("tab.preview", "🔍") == \
        "  🔍  Preview  "
    assert app_module._shell_tab_text("tab.stage", number=0) == \
        "  Stage 0  "
    assert tr("button.settings") == "Settings"


def test_tab_alias_selection_works_with_english_shell_labels():
    from gioco27.gui import app as app_module
    from gioco27.gui.i18n import set_language

    class Notebook:
        def __init__(self):
            self.selected = None

        def tabs(self):
            return ("start", "preview")

        def tab(self, tab_id, option):
            return {"start": "  Start here  ",
                    "preview": "  🔍  Preview  "}[tab_id]

        def select(self, tab_id):
            self.selected = tab_id

    harness = SimpleNamespace(_nb=Notebook())
    select_tab = app_module.App._select_tab_by_text
    set_language("en")

    select_tab(harness, "Anteprima")
    assert harness._nb.selected == "preview"


def test_language_preference_saves_it_and_en(monkeypatch):
    from gioco27.gui import app as app_module

    messages = []
    monkeypatch.setattr(
        app_module.messagebox,
        "showinfo",
        lambda *args, **kwargs: messages.append((args, kwargs)),
    )

    class ConfigStub(dict):
        def __init__(self, language):
            super().__init__(language=language)
            self.saves = 0

        def save(self):
            self.saves += 1

    save_language = app_module.App._save_language_preference
    for old, new in (("it", "en"), ("en", "it")):
        harness = SimpleNamespace(_cfg=ConfigStub(old))
        assert save_language(harness, new, parent="dialog") is True
        assert harness._cfg["language"] == new
        assert harness._cfg.saves == 1
    assert len(messages) == 2


def test_language_change_message_is_available_in_both_languages():
    from gioco27.gui.i18n import set_language, tr

    assert "prossimo avvio" in tr("status.language_restart")
    set_language("en")
    assert "next startup" in tr("status.language_restart")


def test_mathematical_identifiers_remain_unchanged_in_localized_statuses():
    from gioco27.gui.i18n import set_language, tr

    set_language("en")
    status = tr("status.real_game_preset")
    assert "P2" in status and "P0=P1" in status and "J" in status
    assert "SCD_U" not in status  # no identifier was translated or injected


def test_third_block_short_tooltips_and_banner_labels_are_localized():
    from gioco27.gui.i18n import set_language, tr

    assert tr("tooltip.count") == \
        "Conta le combinazioni che soddisfano i filtri correnti."
    assert tr("banner.what_this_tab_does") == "Cosa fa questa scheda?"
    set_language("en")
    assert tr("tooltip.count") == \
        "Count the combinations matching the current filters."
    assert tr("banner.what_this_tab_does") == "What does this tab do?"
    assert tr("banner.show_more") == "Show more ▾"


def test_third_block_onboarding_labels_are_localized():
    from gioco27.gui.i18n import set_language, tr

    assert tr("onboarding.title") == "Inizia qui"
    assert tr("onboarding.button.open_guide") == "Apri la Guida completa"
    set_language("en")
    assert tr("onboarding.title") == "Start here"
    assert tr("onboarding.button.open_guide") == "Open the complete Guide"
    assert tr("onboarding.step1.title") == "Try the Simulator"


def test_third_block_glossary_short_labels_preserve_symbols():
    from gioco27.gui.i18n import set_language, tr

    keys = ("msc", "collection", "orientation", "total_transform")
    for key in keys:
        assert tr(f"glossary.term.{key}")
        assert tr(f"glossary.short.{key}")
    set_language("en")
    assert tr("glossary.term.msc") == "MSC"
    assert tr("glossary.term.collection") == "P (collection)"
    assert "MSC" in tr("glossary.short.stage")
    assert "T⁻¹" in tr("glossary.short.total_transform")


def test_third_block_catalogs_have_the_same_new_keys():
    from gioco27.gui import i18n

    new_namespaces = ("banner.", "onboarding.", "tooltip.", "glossary.")
    italian = set(i18n.CATALOGS["it"])
    english = set(i18n.CATALOGS["en"])
    new_keys = {key for key in italian | english
                if key.startswith(new_namespaces)}
    assert new_keys <= italian
    assert new_keys <= english


def test_third_block_wires_localized_labels_without_real_windows():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    banner_src = (root / "gioco27" / "gui" / "help_banner.py").read_text(
        encoding="utf-8")
    onboarding_src = (root / "gioco27" / "gui" / "onboarding_tab.py").read_text(
        encoding="utf-8")
    assert 'tr("banner.what_this_tab_does")' in banner_src
    assert "tr('onboarding.title')" in onboarding_src
    assert "tr('onboarding.glossary.title')" in onboarding_src


def test_fourth_block_tab_labels_are_localized_without_real_windows():
    from gioco27.gui.i18n import set_language, tr

    assert tr("distribution.title") == \
        "Distribuzione delle decomposizioni su tutti i T raggiungibili"
    assert tr("cycles.title") == "Analisi ciclica della permutazione T"
    assert tr("table.filter") == "Filtro:"
    set_language("en")
    assert tr("distribution.title") == \
        "Decomposition distribution across all reachable T"
    assert tr("cycles.title") == "Cyclic analysis of permutation T"
    assert tr("table.filter") == "Filter:"


def test_fourth_block_dynamic_text_preserves_math_and_permutation_symbols():
    from gioco27.gui.i18n import set_language, tr

    set_language("en")
    orbit = tr("cycles.orbit_summary", card=2, length=3, order=3)
    chart = tr("distribution.chart_title", total=216)
    table = tr("table.status_shown", visible=12)
    assert "C02" in orbit and "T^3" in orbit
    assert "216" in chart and "T" in chart
    assert "T" in table and "T⁻¹" in table


def test_fourth_block_tavola_values_keep_codes_and_localize_simple_values():
    from gioco27.gui.tavola_tab import TavolaFrame
    from gioco27.gui.i18n import set_language

    row = {
        "numero": 1,
        "mescolamenti": ["CDS", "SDC", "DCS"],
        "impilamenti": ["CDS", "SDC", "DCS"],
        "assi": (0, 13, 26),
        "periodo": 6,
        "punti_fissi": 3,
        "tipo_ciclo": (1, 2),
        "parita": 1,
        "autoinversa": True,
    }
    italian = TavolaFrame._valori(row)
    set_language("en")
    english = TavolaFrame._valori(row)
    assert italian[1:4] == english[1:4]
    assert italian[4:6] == english[4:6]
    assert italian[6:] != english[6:]
    assert english[6:] == ("2", "even", "yes")


def test_fourth_block_english_falls_back_to_italian(monkeypatch):
    from gioco27.gui import i18n

    monkeypatch.delitem(i18n.CATALOGS["en"], "cycles.reset_hint")
    i18n.set_language("en")
    assert i18n.tr("cycles.reset_hint") == \
        "Calcola una T (Explorer o Anteprima) per vedere i cicli."


def test_fifth_block_shuffle_controls_are_localized():
    from gioco27.gui.i18n import set_language, tr

    assert tr("shuffle.formula_active") == "Formula attiva:"
    assert tr("shuffle.load_explorer") == "Carica da Explorer"
    assert tr("shuffle.card_by_card") == "Carta per carta"
    set_language("en")
    assert tr("shuffle.formula_active") == "Active formula:"
    assert tr("shuffle.load_explorer") == "Load from Explorer"
    assert tr("shuffle.card_by_card") == "Card by card"
    assert tr("shuffle.next_step") == "Next step"


def test_fifth_block_shuffle_status_and_codes_preserve_math():
    from gioco27.gui.shuffle import ShuffleViewerFrame
    from gioco27.gui.i18n import set_language, tr

    set_language("en")
    loaded = tr("shuffle.formula_loaded", kron=1, msc=1, total=3)
    assert "Kronecker" in loaded and "MSC" in loaded
    assert "right to left" in loaded

    viewer = object.__new__(ShuffleViewerFrame)
    tokens = viewer._validate_and_parse(
        "(SCD_U x SCD_U x DCS_U) o MSC")
    assert tokens[0][2] == "(SCD_U x SCD_U x DCS_U)"
    assert tokens[1][2] == "MSC"
    viewer._build_steps(tokens)
    assert "MSC" in viewer._steps[1]["label"]
    assert "SCD_U" in viewer._steps[-1]["label"]
    assert "DCS_U" in viewer._steps[-1]["label"]
    assert "T⁻¹" in tr("shuffle.inverse_info")


def test_fifth_block_shuffle_fallback_and_catalog_consistency(monkeypatch):
    from gioco27.gui import i18n

    assert {key for key in i18n.CATALOGS["it"] if key.startswith("shuffle.")} == \
        {key for key in i18n.CATALOGS["en"] if key.startswith("shuffle.")}
    monkeypatch.delitem(i18n.CATALOGS["en"], "shuffle.pause")
    i18n.set_language("en")
    assert i18n.tr("shuffle.pause") == "Pausa"


def test_sixth_block_export_dialog_labels_are_localized():
    from gioco27.gui.i18n import set_language, tr

    assert tr("export.booklet_title") == "Esportazione per il libretto"
    assert tr("export.content") == "Contenuto da esportare"
    assert tr("export.export_all") == "Esporta tutto in una cartella…"
    assert tr("export.tab.permutation") == "LaTeX – Permutazione"
    set_language("en")
    assert tr("export.booklet_title") == "Booklet export"
    assert tr("export.content") == "Content to export"
    assert tr("export.export_all") == "Export all to a folder…"
    assert tr("export.tab.permutation") == "LaTeX – Permutation"


def test_sixth_block_export_format_names_and_math_symbols_are_preserved():
    from gioco27.gui.i18n import set_language, tr

    set_language("en")
    labels = (
        tr("export.option.permutation"),
        tr("export.option.cycles"),
        tr("export.option.svg_arrows"),
        tr("export.option.decompositions"),
        tr("export.option.text_summary"),
    )
    assert labels[0].startswith("LaTeX") and "T" in labels[0]
    assert labels[1].startswith("LaTeX")
    assert labels[2].startswith("SVG")
    assert labels[3].startswith("LaTeX")
    assert labels[4].startswith("TXT")
    assert "T⁻¹" in labels[0]


def test_sixth_block_export_catalog_fallback(monkeypatch):
    from gioco27.gui import i18n

    monkeypatch.delitem(i18n.CATALOGS["en"], "export.completed_title")
    i18n.set_language("en")
    assert i18n.tr("export.completed_title") == "Export completato"


def test_sixth_block_export_ui_uses_i18n_without_real_windows():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for name in ("export_dialog.py", "export_group_dialog.py"):
        source = (root / "gioco27" / "gui" / name).read_text(encoding="utf-8")
        assert "from .i18n import tr" in source
        assert "export.content" in source
        assert "export.export_all" in source
        assert "export.completed" in source


def test_sixth_block_export_catalogs_have_matching_keys():
    from gioco27.gui import i18n

    italian = {key for key in i18n.CATALOGS["it"] if key.startswith("export.")}
    english = {key for key in i18n.CATALOGS["en"] if key.startswith("export.")}
    assert italian == english


def test_seventh_block_explorer_labels_are_localized():
    from gioco27.gui.i18n import set_language, tr

    assert tr("explorer.title") == "Explorer Algebrico"
    assert tr("explorer.tab.rewrite") == "Traccia riscrittura"
    assert tr("explorer.normalized_form") == "Forma normalizzata"
    assert tr("explorer.decomposition.open") == "Apri nell'Explorer"

    set_language("en")
    assert tr("explorer.title") == "Algebraic Explorer"
    assert tr("explorer.tab.rewrite") == "Rewrite trace"
    assert tr("explorer.normalized_form") == "Normalized form"
    assert tr("explorer.decomposition.open") == "Open in Explorer"


def test_seventh_block_explorer_dynamic_text_uses_named_placeholders():
    from gioco27.gui.i18n import set_language, tr

    italian = tr("explorer.status.result", period=6, signature="(1, 2, 3)")
    assert italian == "Periodo: 6   Firma: (1, 2, 3)…"
    assert tr("explorer.decomposition.progress", done=120, found=17) == \
        "120 / 216 -- trovate: 17"

    set_language("en")
    english = tr("explorer.status.result", period=6, signature="(1, 2, 3)")
    assert english == "Period: 6   Signature: (1, 2, 3)…"
    assert tr("explorer.decomposition.loading", loaded=600, total=1200,
              percent=50) == "Loading... 600 / 1200 (50%)"


def test_seventh_block_explorer_preserves_mathematical_identifiers():
    from gioco27.gui import decomposition
    from gioco27.gui.i18n import set_language, tr

    set_language("en")
    values = [
        tr("explorer.status.prompt"),
        tr("explorer.canonical.subtitle"),
        tr("explorer.button.decompositions_inverse"),
        tr("explorer.decomposition.found", count=1, target="T⁻¹"),
    ]
    joined = " ".join(values)
    for identifier in ("P1", "MSC", "J1", "K ∘ MSCᵏ", "T⁻¹",
                       "A0", "A1", "A2", "GEN3"):
        assert identifier in joined
    assert decomposition._expr_triple(("SCD_U", "CDS_U", "DCS_U")) == \
        "(SCD_U x CDS_U x DCS_U)"


def test_seventh_block_explorer_fallback_and_language_switch(monkeypatch):
    from gioco27.gui import i18n

    i18n.set_language("en")
    assert i18n.tr("explorer.tab.matrix") == "Matrix"
    monkeypatch.delitem(i18n.CATALOGS["en"], "explorer.tab.matrix")
    assert i18n.tr("explorer.tab.matrix") == "Matrice"
    i18n.set_language("it")
    assert i18n.tr("explorer.decomposition.searching") == "Ricerca in corso..."
    i18n.set_language("en")
    assert i18n.tr("explorer.decomposition.searching") == "Searching..."


def test_seventh_block_explorer_ui_uses_i18n_without_real_windows():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    explorer = (root / "gioco27" / "gui" / "explorer_tab.py").read_text(
        encoding="utf-8")
    decomposition = (root / "gioco27" / "gui" / "decomposition.py").read_text(
        encoding="utf-8")
    assert "from .i18n import tr" in explorer
    assert "from .i18n import tr" in decomposition
    for key in ("explorer.title", "explorer.tab.numeric",
                "explorer.status.result", "explorer.canonical.calculated"):
        assert key in explorer
    for key in ("explorer.decomposition.title",
                "explorer.decomposition.progress",
                "explorer.decomposition.table_status"):
        assert key in decomposition
    for hardcoded in ("Explorer Algebrico", "Espressione T",
                      "Nessuna espressione inserita."):
        assert hardcoded not in explorer
    for hardcoded in ("Ricerca in corso...", "Apri nell'Explorer",
                      "A2  (doppio clic -> Explorer)"):
        assert hardcoded not in decomposition


def test_seventh_block_explorer_catalogs_have_matching_keys():
    from gioco27.gui import i18n

    italian = {key for key in i18n.CATALOGS["it"]
               if key.startswith("explorer.")}
    english = {key for key in i18n.CATALOGS["en"]
               if key.startswith("explorer.")}
    assert italian == english
    assert len(italian) == 91


def test_eighth_block_simulator_controls_are_localized():
    from gioco27.gui.i18n import set_language, tr

    assert tr("simulator.title") == "Simulatore del Trucco delle 27 Carte"
    assert tr("simulator.calculate_sequence") == "Calcola sequenza"
    assert tr("simulator.tab.instructions") == "Istruzioni per il mago"
    assert tr("simulator.practice.confirm_stacking") == "Conferma impilamento"

    set_language("en")
    assert tr("simulator.title") == "27-Card Trick Simulator"
    assert tr("simulator.calculate_sequence") == "Calculate sequence"
    assert tr("simulator.tab.instructions") == "Instructions for the magician"
    assert tr("simulator.practice.confirm_stacking") == "Confirm stacking"


def test_eighth_block_simulator_dynamic_statuses_preserve_codes():
    from gioco27.gui.i18n import set_language, tr

    assert tr("simulator.practice.step_target", phase=2, card=7) == \
        "Fase 2/3 — Carta bersaglio: C07"
    assert "SCD CDS DCS" in tr(
        "simulator.status.sequence", shuffles="SCD CDS DCS", number=42)

    set_language("en")
    status = tr("simulator.status.sequence",
                shuffles="SCD CDS DCS", number=42)
    position = tr("simulator.deck.card_position", card=7, position=13,
                  reading_column=2)
    assert status == "Sequence: SCD CDS DCS (arrangement #42 in the table)"
    assert "C07" in position and "13" in position and "2" in position


def test_eighth_block_simulator_gestures_are_localized_without_changing_codes():
    from gioco27.gui import simulator_tab
    from gioco27.gui.i18n import set_language, tr

    assert simulator_tab._gesto("SCD") == \
        "prima Sinistra (al dorso), poi Centro, infine Destra (al fondo)"
    assert set(simulator_tab._SIGLA_DESC) == \
        {"SCD", "SDC", "CSD", "CDS", "DSC", "DCS"}

    set_language("en")
    assert simulator_tab._gesto("SCD") == \
        "first Left (at the back), then Center, finally Right (at the bottom)"
    assert "S→C→D→S" in tr(simulator_tab._SIGLA_DESC["CDS"])
    assert "D,S,C" in tr(simulator_tab._SIGLA_DESC["CDS"])


def test_eighth_block_simulator_error_plural_is_explicit():
    from gioco27.gui.i18n import set_language, tr

    assert tr("simulator.summary.errors.one", count=1, maximum=6) == \
        "Errore commesso  : 1/6"
    assert tr("simulator.summary.errors.many", count=3, maximum=6) == \
        "Errori commessi : 3/6"
    set_language("en")
    assert tr("simulator.summary.errors.one", count=1, maximum=6) == \
        "Error made     : 1/6"
    assert tr("simulator.summary.errors.many", count=3, maximum=6) == \
        "Errors made    : 3/6"


def test_eighth_block_language_switch_and_fallback_do_not_change_simulation(
    monkeypatch,
):
    from gioco27.core import gioco_reale
    from gioco27.gui import i18n

    before = gioco_reale.risolvi_trucco(7, 19)
    i18n.set_language("en")
    after = gioco_reale.risolvi_trucco(7, 19)
    assert after == before
    monkeypatch.delitem(i18n.CATALOGS["en"], "simulator.photo")
    assert i18n.tr("simulator.photo") == "Fotografia:"
    assert gioco_reale.risolvi_trucco(7, 19) == before


def test_eighth_block_simulator_uses_i18n_without_major_hardcoded_strings():
    from pathlib import Path
    from gioco27.gui import i18n

    source = (Path(__file__).resolve().parents[1] / "gioco27" / "gui" /
              "simulator_tab.py").read_text(encoding="utf-8")
    assert "from .i18n import tr" in source
    for key in ("simulator.title", "simulator.status.sequence",
                "simulator.practice.question_column",
                "simulator.summary.score"):
        assert key in source
    for hardcoded in ("Simulatore del Trucco delle 27 Carte",
                      "Carta scelta dal pubblico (posizione iniziale, 0 = dorso):",
                      "Calcola prima una sequenza, poi torna qui per esercitarti.",
                      "Trucco completato! Vedi il riepilogo nel log."):
        assert hardcoded not in source

    italian = {key for key in i18n.CATALOGS["it"]
               if key.startswith("simulator.")}
    english = {key for key in i18n.CATALOGS["en"]
               if key.startswith("simulator.")}
    assert italian == english
    assert len(italian) == 82


def test_eighth_block_simulator_instruction_output_switches_language_without_ui():
    from gioco27.core import gioco_reale
    from gioco27.gui.i18n import set_language
    from gioco27.gui.simulator_tab import SimulatorFrame

    class Value:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    class TextCapture:
        def __init__(self):
            self.parts = []

        def configure(self, **_kwargs):
            pass

        def delete(self, *_args):
            self.parts.clear()

        def insert(self, _where, text, _tag):
            self.parts.append(text)

    simulator = object.__new__(SimulatorFrame)
    simulator._card_var = Value(7)
    simulator._target_var = Value(19)
    simulator._istr_txt = TextCapture()
    plan = gioco_reale.risolvi_trucco(7, 19)

    simulator._build_istruzioni(plan)
    italian = "".join(simulator._istr_txt.parts)
    set_language("en")
    simulator._build_istruzioni(plan)
    english = "".join(simulator._istr_txt.parts)

    assert "Istruzioni per il trucco" in italian
    assert "Carta del pubblico" in italian
    assert "Trick instructions" in english
    assert "Spectator's card" in english
    for code in plan["mescolamenti"] + plan["impilamenti"]:
        assert code in italian and code in english
    assert plan["T"] == gioco_reale.risolvi_trucco(7, 19)["T"]


def test_ninth_block_analysis_controls_and_columns_are_localized():
    from gioco27.gui.i18n import set_language, tr

    assert tr("analysis.title") == "Analisi Molteplicità delle Permutazioni"
    assert tr("analysis.generate") == "Genera & Analizza"
    assert tr("analysis.column.multiplicity") == "Molt."
    assert tr("analysis.open_explorer") == "Apri nel Explorer"

    set_language("en")
    assert tr("analysis.title") == "Permutation Multiplicity Analysis"
    assert tr("analysis.generate") == "Generate & Analyze"
    assert tr("analysis.column.multiplicity") == "Mult."
    assert tr("analysis.open_explorer") == "Open in Explorer"


def test_ninth_block_analysis_dynamic_statuses_use_named_placeholders():
    from gioco27.gui.i18n import set_language, tr

    italian = tr("analysis.status.summary", combinations="1.728",
                 permutations=216, minimum=2, maximum=12)
    assert "1.728 combinazioni" in italian
    assert "216 permutazioni distinte" in italian
    set_language("en")
    english = tr("analysis.status.summary", combinations="1,728",
                 permutations=216, minimum=2, maximum=12)
    assert "1,728 combinations" in english
    assert "216 distinct permutations" in english
    assert tr("analysis.status.reading_csv", filename="input.csv") == \
        "Reading CSV: input.csv…"


def test_ninth_block_analysis_multiplicity_plural_is_explicit():
    from gioco27.gui.i18n import set_language, tr

    assert "1 sequenza Stage distinta produce" in tr(
        "analysis.detail.multiplicity.one", count=1)
    assert "3 sequenze Stage distinte producono" in tr(
        "analysis.detail.multiplicity.many", count=3)
    set_language("en")
    assert "1 distinct Stage sequence produces" in tr(
        "analysis.detail.multiplicity.one", count=1)
    assert "3 distinct Stage sequences produce" in tr(
        "analysis.detail.multiplicity.many", count=3)


def test_ninth_block_analysis_preserves_exposed_identifiers_and_formats():
    from gioco27.gui.i18n import set_language, tr

    set_language("en")
    values = " ".join((
        tr("analysis.column.permutation"),
        tr("analysis.column.first_symbolic"),
        tr("analysis.detail.subtitle"),
        tr("analysis.detail.footer_hint"),
    ))
    for identifier in ("T_permutazione", "T_simbolica", "Stage",
                       "P₃×P₂×P₁", "J₃×J₂×J₁", "P o MSC o J"):
        assert identifier in values
    for format_name in ("CSV", "Excel", "HTML"):
        assert format_name in " ".join((
            tr("analysis.menu.summary_csv"),
            tr("analysis.menu.summary_excel"),
            tr("analysis.menu.summary_html"),
        ))


def test_ninth_block_language_switch_and_fallback_do_not_change_analysis(
    monkeypatch,
):
    from gioco27.core.algebra import analizza_righe
    from gioco27.gui import i18n

    rows = [
        {"Stage0": "SCD_U", "Stage1": "CDS_U", "Stage2": "DCS_U",
         "T_permutazione": "[0,1,2]"},
        {"Stage0": "DCS_U", "Stage1": "CDS_U", "Stage2": "SCD_U",
         "T_permutazione": "[0,1,2]"},
    ]
    before = analizza_righe(rows)
    i18n.set_language("en")
    assert analizza_righe(rows) == before
    monkeypatch.delitem(i18n.CATALOGS["en"], "analysis.status.prompt")
    assert i18n.tr("analysis.status.prompt") == \
        "Premi «Genera & Analizza» per avviare l'analisi."
    assert analizza_righe(rows) == before


def test_ninth_block_analysis_detail_switches_language_without_ui():
    from gioco27.gui.analysis_tab import AnalysisTabMixin
    from gioco27.gui.i18n import set_language

    symbolic = ("T = [SCD_U o MSC o I_3] o [CDS_U o MSC o R_U] o "
                "[DCS_U o MSC o I_3]")

    class Tree:
        def selection(self):
            return ("0",)

    class TextCapture:
        def __init__(self):
            self.parts = []

        def configure(self, **_kwargs):
            pass

        def delete(self, *_args):
            self.parts.clear()

        def insert(self, _where, text, *_tags):
            self.parts.append(str(text))

        def tag_names(self):
            return ()

        def tag_delete(self, *_args):
            pass

        def tag_configure(self, *_args, **_kwargs):
            pass

        def tag_bind(self, *_args, **_kwargs):
            pass

    analysis = object.__new__(AnalysisTabMixin)
    analysis._analisi_tv = Tree()
    analysis._analisi_detail_text = TextCapture()
    analysis._analisi_risultati = [{
        "simboliche": [symbolic], "perm_str": "[0,1,2]", "n_sim": 1,
    }]

    analysis._analisi_show_detail()
    italian = "".join(analysis._analisi_detail_text.parts)
    set_language("en")
    analysis._analisi_show_detail()
    english = "".join(analysis._analisi_detail_text.parts)
    assert "Molteplicità 1" in italian and "apri Explorer" in italian
    assert "Multiplicity 1" in english and "open Explorer" in english
    for identifier in ("SCD_U", "CDS_U", "DCS_U", "MSC", "I_3", "R_U"):
        assert identifier in italian and identifier in english


def test_ninth_block_analysis_uses_i18n_and_localizes_eta(monkeypatch):
    from pathlib import Path
    from gioco27.gui import common, i18n

    source = (Path(__file__).resolve().parents[1] / "gioco27" / "gui" /
              "analysis_tab.py").read_text(encoding="utf-8")
    assert "from .i18n import tr" in source
    for key in ("analysis.title", "analysis.status.summary",
                "analysis.detail.multiplicity.one", "analysis.no_data"):
        assert key in source
    for hardcoded in ("Analisi Molteplicità delle Permutazioni",
                      "Premi «Genera & Analizza» per avviare l'analisi.",
                      "Seleziona prima una riga."):
        assert hardcoded not in source

    times = iter((0.0, 2.0))
    monkeypatch.setattr(common.time, "time", lambda: next(times))
    eta = common.EtaEstimator(min_interval=0, min_span=0, min_samples=2)
    assert eta.text(10, 100) == ""
    i18n.set_language("en")
    assert eta.text(20, 100).endswith("remaining")

    italian = {key for key in i18n.CATALOGS["it"]
               if key.startswith("analysis.")}
    english = {key for key in i18n.CATALOGS["en"]
               if key.startswith("analysis.")}
    assert italian == english
    assert len(italian) == 52


def _use_config_file(monkeypatch, tmp_path):
    from gioco27.core import config as config_module

    config_file = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "_CONFIG_FILE", config_file)
    monkeypatch.setattr(config_module, "_CONFIG_DIR", tmp_path)
    return config_module, config_file


def test_old_configuration_without_language_uses_italian_and_preserves_options(
    monkeypatch, tmp_path
):
    config_module, config_file = _use_config_file(monkeypatch, tmp_path)
    config_file.write_text(
        json.dumps({"n_workers": 4, "use_parallel": False}),
        encoding="utf-8",
    )

    cfg = config_module.Config()

    assert cfg.get("language") == "it"
    assert cfg.get("n_workers") == 4
    assert cfg.get("use_parallel") is False


@pytest.mark.parametrize("language", ["it", "en"])
def test_configuration_accepts_supported_languages(
    monkeypatch, tmp_path, language
):
    config_module, config_file = _use_config_file(monkeypatch, tmp_path)
    config_file.write_text(json.dumps({"language": language}), encoding="utf-8")

    assert config_module.Config().get("language") == language


def test_configuration_rejects_invalid_language_with_italian_default(
    monkeypatch, tmp_path
):
    config_module, config_file = _use_config_file(monkeypatch, tmp_path)
    config_file.write_text(json.dumps({"language": "fr"}), encoding="utf-8")

    assert config_module.Config().get("language") == "it"


def test_configuration_round_trip_preserves_language_and_other_options(
    monkeypatch, tmp_path
):
    config_module, config_file = _use_config_file(monkeypatch, tmp_path)
    config_file.write_text(
        json.dumps(
            {
                "language": "en",
                "n_workers": 3,
                "use_parallel": False,
                "decomp_mode": "T",
                "help_font_scale": 1.3,
            }
        ),
        encoding="utf-8",
    )

    cfg = config_module.Config()
    cfg.save()
    reloaded = config_module.Config()

    assert reloaded.get("language") == "en"
    assert reloaded.get("n_workers") == 3
    assert reloaded.get("use_parallel") is False
    assert reloaded.get("decomp_mode") == "T"
    assert reloaded.get("help_font_scale") == 1.3
