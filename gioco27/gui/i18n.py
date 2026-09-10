"""Minimal runtime localization support for the GUI.

The catalogs intentionally start small.  GUI code can use :func:`tr` for
common labels now, while the rest of the existing Italian UI remains
unchanged until it is migrated deliberately.
"""

from __future__ import annotations

from typing import Any, Mapping


_ITALIAN = {
    "app.title": "Gioco delle 27 carte  v{version}  —  Analisi combinazioni",
    "tab.start": "Inizia qui",
    "tab.stage": "Stadio {number}",
    "tab.simulator": "Simulatore",
    "tab.table": "Tavola 216",
    "tab.preview": "Anteprima",
    "tab.analysis": "Analisi",
    "tab.explorer": "Explorer",
    "tab.guide": "Guida",
    "tab.cycles": "Cicli",
    "tab.distribution": "Distribuzione",
    "button.count": "Conta",
    "button.generate": "Genera…",
    "button.reset_all": "Reset tutto",
    "button.beginner_mode": "Modalità principiante",
    "button.exit": "Esci",
    "button.settings": "Impostazioni",
    "button.verify": "Verifica",
    "button.presentation": "Presentazione",
    "button.protocol": "Protocollo",
    "button.conjugacy": "Coniugio",
    "button.quick_reset": "Reset filtri",
    "button.real_game": "Gioco Reale  (1 728 combinazioni)",
    "button.uniform_j": "J Uniformi per tutti gli stadi",
    "button.cancel_export": "Annulla",
    "menu.pdf_detailed": "PDF dettagliato (stile C: carte+matrici)",
    "label.combinations": "Combinazioni:",
    "label.quick_presets": "Preset rapidi:",
    "label.color_legend": "Legenda colori GEN3:",
    "label.legend_note": "(i nomi compaiono con questi colori nelle formule dell'Explorer)",
    "button.cancel": "Annulla",
    "button.close": "Chiudi",
    "button.save": "Salva",
    "button.calculate": "Calcola",
    "status.running": "In corso",
    "status.completed": "Completato",
    "status.real_game_preset": "Preset Gioco Reale: P2 = raccolta libera, P0=P1=identità, J uniformi — 1 728 combinazioni",
    "status.uniform_j_preset": "J Uniformi attivi per tutti gli stadi — J0=J1=J2 per ogni stadio",
    "status.count_summary": "{count} combinazioni  →  {count} pagine PDF / {count} righe CSV",
    "status.reset_complete": "Reset completo: filtri e tutti i tab azzerati.",
    "status.reset_with_problems": "Reset completato (problemi su: {tabs}).",
    "status.integrity_running": "Verifica di integrità in corso…",
    "status.integrity_completed": "Verifica completata.",
    "status.integrity_failed": "Verifica FALLITA!",
    "status.integrity_all_passed": "Tutte le verifiche superate:\n\n",
    "status.language_restart": "La nuova lingua sarà applicata al prossimo avvio.",
    "dialog.settings.title": "⚙️  Impostazioni",
    "dialog.integrity.title": "Verifica di integrità",
    "dialog.cache.title": "Cache",
    "settings.language": "Lingua:",
    "settings.italian": "Italiano",
    "settings.english": "English",
    "settings.workers": "Worker paralleli (decomposizioni):",
    "settings.logical_cpus_default": "(CPU logiche: {count}, default: {default})",
    "settings.parallel_search": "Usa ricerca parallela:",
    "settings.cache": "Cache decomposizioni:",
    "settings.cache_info": "{entries} file  ({size:.1f} MB)",
    "settings.clear_cache": "Cancella cache",
    "settings.help_font_size": "Dimensione testo aiuti:",
    "settings.scale.normal": "Normale (100%)",
    "settings.scale.large": "Grande (130%)",
    "settings.scale.very_large": "Molto grande (160%)",
    "settings.scale.huge": "Enorme (200%)",
    "status.cache_cleared": "Cache cancellata.",
    "status.saved": "Salvato: {filename} ({count})",
    "error.generic": "Errore",
}

_ENGLISH = {
    "app.title": "27-card trick  v{version}  —  Combination analysis",
    "tab.start": "Start here",
    "tab.stage": "Stage {number}",
    "tab.simulator": "Simulator",
    "tab.table": "Table 216",
    "tab.preview": "Preview",
    "tab.analysis": "Analysis",
    "tab.explorer": "Explorer",
    "tab.guide": "Guide",
    "tab.cycles": "Cycles",
    "tab.distribution": "Distribution",
    "button.count": "Count",
    "button.generate": "Generate…",
    "button.reset_all": "Reset all",
    "button.beginner_mode": "Beginner mode",
    "button.exit": "Exit",
    "button.settings": "Settings",
    "button.verify": "Verify",
    "button.presentation": "Presentation",
    "button.protocol": "Protocol",
    "button.conjugacy": "Conjugacy",
    "button.quick_reset": "Reset filters",
    "button.real_game": "Real Game  (1,728 combinations)",
    "button.uniform_j": "Uniform J for all stages",
    "button.cancel_export": "Cancel",
    "menu.pdf_detailed": "Detailed PDF (C-style: cards+matrices)",
    "label.combinations": "Combinations:",
    "label.quick_presets": "Quick presets:",
    "label.color_legend": "GEN3 color legend:",
    "label.legend_note": "(names use these colors in Explorer formulas)",
    "button.cancel": "Cancel",
    "button.close": "Close",
    "button.save": "Save",
    "button.calculate": "Calculate",
    "status.running": "Running",
    "status.completed": "Completed",
    "status.real_game_preset": "Real Game preset: P2 = free collection, P0=P1=identity, uniform J — 1,728 combinations",
    "status.uniform_j_preset": "Uniform J enabled for all stages — J0=J1=J2 for each stage",
    "status.count_summary": "{count} combinations  →  {count} PDF pages / {count} CSV rows",
    "status.reset_complete": "Complete reset: filters and all tabs cleared.",
    "status.reset_with_problems": "Reset completed (problems in: {tabs}).",
    "status.integrity_running": "Integrity check in progress…",
    "status.integrity_completed": "Integrity check completed.",
    "status.integrity_failed": "Integrity check FAILED!",
    "status.integrity_all_passed": "All checks passed:\n\n",
    "status.language_restart": "The new language will be applied at the next startup.",
    "dialog.settings.title": "⚙️  Settings",
    "dialog.integrity.title": "Integrity check",
    "dialog.cache.title": "Cache",
    "settings.language": "Language:",
    "settings.italian": "Italiano",
    "settings.english": "English",
    "settings.workers": "Parallel workers (decompositions):",
    "settings.logical_cpus_default": "(Logical CPUs: {count}, default: {default})",
    "settings.parallel_search": "Use parallel search:",
    "settings.cache": "Decomposition cache:",
    "settings.cache_info": "{entries} files  ({size:.1f} MB)",
    "settings.clear_cache": "Clear cache",
    "settings.help_font_size": "Help text size:",
    "settings.scale.normal": "Normal (100%)",
    "settings.scale.large": "Large (130%)",
    "settings.scale.very_large": "Very large (160%)",
    "settings.scale.huge": "Huge (200%)",
    "status.cache_cleared": "Cache cleared.",
    "status.saved": "Saved: {filename} ({count})",
    "error.generic": "Error",
}


# Public enough for focused catalog tests and future catalog extension, while
# keeping the individual dictionaries private to discourage direct lookups in
# GUI modules.
CATALOGS: Mapping[str, Mapping[str, str]] = {
    "it": _ITALIAN,
    "en": _ENGLISH,
}

_language = "it"


def get_language() -> str:
    """Return the currently selected language code."""

    return _language


def set_language(language: str) -> str:
    """Set and return the current language.

    Only catalog languages are accepted.  Configuration validation normally
    prevents invalid values from reaching this function, but rejecting them
    here makes direct callers fail clearly as well.
    """

    if language not in CATALOGS:
        raise ValueError(
            f"Unsupported language {language!r}; expected one of: "
            f"{', '.join(sorted(CATALOGS))}"
        )
    global _language
    _language = language
    return _language


def tr(key: str, **values: Any) -> str:
    """Translate *key*, falling back from English to Italian.

    Missing keys in the Italian catalog raise ``KeyError`` with a clear
    message.  Named values are applied only after the catalog fallback, so
    dynamic messages remain single templates instead of concatenated pieces.
    """

    catalog = CATALOGS[_language]
    template = catalog.get(key)
    if template is None and _language != "it":
        template = CATALOGS["it"].get(key)
    if template is None:
        raise KeyError(f"Missing i18n key in Italian catalog: {key!r}")
    if not values:
        return template
    try:
        return template.format(**values)
    except KeyError as exc:
        missing = exc.args[0]
        raise KeyError(
            f"Missing placeholder {missing!r} for i18n key {key!r}"
        ) from exc
