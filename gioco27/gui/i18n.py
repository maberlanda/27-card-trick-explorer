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
    "banner.what_this_tab_does": "Cosa fa questa scheda?",
    "banner.open_guide": "Apri Guida",
    "banner.show_more": "Mostra di più ▾",
    "banner.show_less": "Mostra meno ▴",
    "onboarding.title": "Inizia qui",
    "onboarding.subtitle": "Una mappa rapida per orientarti, anche se non conosci la teoria.",
    "onboarding.intro": "Questa scheda ti accompagna nei primi passi: parti da un preset, guarda l'Anteprima, poi esplora il resto quando vuoi.",
    "onboarding.step1.title": "Prova il Simulatore",
    "onboarding.step1.desc": "Nella scheda Simulatore esegui il trucco come col mazzo vero: istruzioni, fotografie del mazzo e pratica guidata.",
    "onboarding.step2.title": "Sfoglia la Tavola 216",
    "onboarding.step2.desc": "Le 216 disposizioni semplici del libro: mescolamenti, impilamenti, posizioni degli Assi e proprietà di ogni sequenza.",
    "onboarding.step3.title": "Approfondisci",
    "onboarding.step3.desc": "Carica il preset «Gioco Reale», guarda l'Anteprima e, quando te la senti, attiva la modalità Esperto per Stadi, Explorer, Cicli e Distribuzione.",
    "onboarding.quick_actions": "Azioni rapide",
    "onboarding.glossary.title": "Glossario",
    "onboarding.glossary.subtitle": "i termini in parole semplici (passa il mouse per i dettagli)",
    "onboarding.button.try_simulator": "Prova il Simulatore",
    "onboarding.button.load_real_game": "Carica «Gioco Reale»",
    "onboarding.button.go_preview": "Vai all'Anteprima",
    "onboarding.button.open_guide": "Apri la Guida completa",
    "tooltip.count": "Conta le combinazioni che soddisfano i filtri correnti.",
    "tooltip.generate": "Genera ed esporta i risultati.",
    "tooltip.reset_all": "Azzera tutti i filtri P e J di tutti gli stadi.",
    "tooltip.exit": "Chiudi il programma (le impostazioni vengono salvate).",
    "tooltip.settings": "Numero di processi, opzioni di calcolo e preferenze.",
    "tooltip.presentation": "Apre la finestra di presentazione a schermo intero.",
    "tooltip.real_game": "Imposta i filtri sull'esempio standard di 1 728 sequenze.",
    "tooltip.uniform_j": "Imposta la stessa orientazione J su tutti e tre gli stadi.",
    "tooltip.quick_reset": "Azzera tutti i filtri P e J.",
    "tooltip.cancel_export": "Interrompe l'export in corso.",
    "tooltip.load_real_game": "Imposta i filtri sull'esempio standard di 1 728 sequenze.",
    "tooltip.try_simulator": "Esegui il trucco passo per passo, come col mazzo vero.",
    "tooltip.preview": "Mostra cosa succede alle carte per una singola combinazione.",
    "glossary.term.msc": "MSC",
    "glossary.term.permutation": "Permutazione",
    "glossary.term.stage": "Stadio",
    "glossary.term.collection": "P (raccolta)",
    "glossary.term.shuffle": "Mescolamento",
    "glossary.term.stacking": "Impilamento",
    "glossary.term.orientation": "J (orientazione)",
    "glossary.term.real_game": "Gioco Reale",
    "glossary.term.total_transform": "T  /  T⁻¹",
    "glossary.term.conjugacy": "Coniugio",
    "glossary.term.cayley": "Cayley (tavola)",
    "glossary.term.kronecker": "Kronecker",
    "glossary.term.cycle": "Ciclo",
    "glossary.term.order": "Ordine",
    "glossary.short.msc": "Il mescolamento di base: distribuisci le 27 carte in 3 colonne e le raccogli.",
    "glossary.short.permutation": "Un modo di rimescolare: a ogni posizione di partenza associa una posizione d'arrivo.",
    "glossary.short.stage": "Una singola «mossa» del gioco: una raccolta P, il mescolamento MSC e un'orientazione J.",
    "glossary.short.collection": "Come raccogli i tre pacchetti dopo averli messi in colonna.",
    "glossary.short.shuffle": "La sigla funzionale della raccolta: la cifra N va nella N-esima lettera.",
    "glossary.short.stacking": "Il gesto fisico: l'ordine dei mazzetti dal dorso verso il fondo.",
    "glossary.short.orientation": "Come orienti o giri il mazzo prima del mescolamento.",
    "glossary.short.real_game": "Un insieme pronto di 1 728 sequenze: l'esempio classico da cui partire.",
    "glossary.short.total_transform": "La trasformazione totale delle 3 mosse (T) e la sua inversa (T⁻¹).",
    "glossary.short.conjugacy": "Due mosse «coniugate» fanno la stessa cosa, a meno di rinominare le posizioni.",
    "glossary.short.cayley": "La tabella di tutti i prodotti possibili tra due mosse del gruppo.",
    "glossary.short.kronecker": "Scompone una mossa in tre pezzi indipendenti: pacchetti, terzine e carte.",
    "glossary.short.cycle": "Un gruppetto di posizioni che ruotano tra loro ripetendo la mossa.",
    "glossary.short.order": "Quante volte ripetere una mossa per tornare al punto di partenza.",
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
    "banner.what_this_tab_does": "What does this tab do?",
    "banner.open_guide": "Open Guide",
    "banner.show_more": "Show more ▾",
    "banner.show_less": "Show less ▴",
    "onboarding.title": "Start here",
    "onboarding.subtitle": "A quick map to help you get oriented, even if you do not know the theory.",
    "onboarding.intro": "This tab guides you through the first steps: start from a preset, view the Preview, then explore the rest whenever you like.",
    "onboarding.step1.title": "Try the Simulator",
    "onboarding.step1.desc": "In the Simulator tab, perform the trick as you would with a real deck: instructions, deck photos, and guided practice.",
    "onboarding.step2.title": "Browse Table 216",
    "onboarding.step2.desc": "The book's 216 simple arrangements: shuffles, stackings, Ace positions, and the properties of each sequence.",
    "onboarding.step3.title": "Go deeper",
    "onboarding.step3.desc": "Load the Real Game preset, view the Preview, and, when you are ready, enable Expert mode for Stages, Explorer, Cycles, and Distribution.",
    "onboarding.quick_actions": "Quick actions",
    "onboarding.glossary.title": "Glossary",
    "onboarding.glossary.subtitle": "simple terms (hover for details)",
    "onboarding.button.try_simulator": "Try the Simulator",
    "onboarding.button.load_real_game": "Load “Real Game”",
    "onboarding.button.go_preview": "Go to Preview",
    "onboarding.button.open_guide": "Open the complete Guide",
    "tooltip.count": "Count the combinations matching the current filters.",
    "tooltip.generate": "Generate and export the results.",
    "tooltip.reset_all": "Clear all P and J filters for every stage.",
    "tooltip.exit": "Close the program (settings are saved).",
    "tooltip.settings": "Number of workers, calculation options, and preferences.",
    "tooltip.presentation": "Open the full-screen presentation window.",
    "tooltip.real_game": "Set the filters to the standard 1,728-sequence example.",
    "tooltip.uniform_j": "Use the same J orientation for all three stages.",
    "tooltip.quick_reset": "Clear all P and J filters.",
    "tooltip.cancel_export": "Stop the export in progress.",
    "tooltip.load_real_game": "Set the filters to the standard 1,728-sequence example.",
    "tooltip.try_simulator": "Perform the trick step by step, as with a real deck.",
    "tooltip.preview": "Show what happens to the cards for one combination.",
    "glossary.term.msc": "MSC",
    "glossary.term.permutation": "Permutation",
    "glossary.term.stage": "Stage",
    "glossary.term.collection": "P (collection)",
    "glossary.term.shuffle": "Shuffle",
    "glossary.term.stacking": "Stacking",
    "glossary.term.orientation": "J (orientation)",
    "glossary.term.real_game": "Real Game",
    "glossary.term.total_transform": "T  /  T⁻¹",
    "glossary.term.conjugacy": "Conjugacy",
    "glossary.term.cayley": "Cayley table",
    "glossary.term.kronecker": "Kronecker",
    "glossary.term.cycle": "Cycle",
    "glossary.term.order": "Order",
    "glossary.short.msc": "The basic shuffle: deal the 27 cards into 3 columns and collect them.",
    "glossary.short.permutation": "A way to rearrange things: each starting position is assigned an ending position.",
    "glossary.short.stage": "One game “move”: a collection P, the MSC shuffle, and a J orientation.",
    "glossary.short.collection": "How you collect the three packets after placing them in columns.",
    "glossary.short.shuffle": "The functional code for the collection: digit N goes to the Nth letter.",
    "glossary.short.stacking": "The physical action: the order of the packets from back to bottom.",
    "glossary.short.orientation": "How you orient or turn the deck before the shuffle.",
    "glossary.short.real_game": "A ready-made set of 1,728 sequences: the classic example to start with.",
    "glossary.short.total_transform": "The total transformation of the 3 moves (T) and its inverse (T⁻¹).",
    "glossary.short.conjugacy": "Two conjugate moves do the same thing, up to renaming positions.",
    "glossary.short.cayley": "The table of all possible products of two group moves.",
    "glossary.short.kronecker": "Splits a move into three independent pieces: packets, triples, and cards.",
    "glossary.short.cycle": "A small group of positions that rotate among themselves as the move repeats.",
    "glossary.short.order": "How many times a move must be repeated to return to the starting point.",
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
