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
