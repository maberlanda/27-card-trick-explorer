"""
Testi della scheda «Inizia qui», glossario e aiuti delle schede.

Qui restano solo chiavi e struttura: ogni testo leggibile sta nei cataloghi
di `gioco27/i18n.py` (IT/EN). Il glossario ha due sezioni (DP8, I7):

* **matematico** — i termini tecnici usati nei controlli e nei risultati;
* **narrativo** — i nomi del libro (Gaia, Cronaca, Giullare, …) come alias:
  ogni voce rimanda al termine matematico che il libro stesso indica.

Ogni voce ha le chiavi ``glossary.term.<k>``, ``glossary.short.<k>`` e
``glossary.long.<k>``.
"""

from .i18n import tr

ONBOARD_INTRO = "onboarding.intro"

#: (icona/numero, chiave del titolo, chiave della descrizione)
ONBOARD_STEPS = [
    ("1", "onboarding.step1.title", "onboarding.step1.desc"),
    ("2", "onboarding.step2.title", "onboarding.step2.desc"),
    ("3", "onboarding.step3.title", "onboarding.step3.desc"),
]

#: Glossario matematico, in ordine didattico (dal gesto alla struttura).
GLOSSARIO_MATEMATICO = (
    "card", "position", "msc", "stage", "collection", "shuffle", "stacking",
    "orientation", "board", "inverse_board", "forgetting_machine",
    "procedure", "transformation", "permutation", "total_transform", "inverse",
    "cycle", "order", "fixed_point", "return", "guide_cards", "recovery",
    "real_game", "kronecker", "local_factor", "separability", "fiber",
    "fiber_sum", "canonical_form", "conjugacy", "center", "cayley",
    "group_h", "group_gamma", "s27", "coset",
)

#: Nomi narrativi del libro (alias, non sostituti dei termini tecnici).
GLOSSARIO_NARRATIVO = (
    "gaia", "cronaca", "giullare", "mondo_di_mazzo", "seldon", "prima_crisi",
    "seconda_crisi",
)

GLOSSARIO = GLOSSARIO_MATEMATICO + GLOSSARIO_NARRATIVO

#: Compatibilita': (chiave del termine, chiave breve, chiave estesa)
GLOSSARY = [(f"glossary.term.{k}", f"glossary.short.{k}", f"glossary.long.{k}")
            for k in GLOSSARIO]


# Testi dei banner d'aiuto in cima a ciascuna scheda: chiave -> (breve, esteso)
TAB_HELP = {
    "stadio": (
        "help.tab.stadio.short", "help.tab.stadio.long"),
    "anteprima": (
        "help.tab.anteprima.short", "help.tab.anteprima.long"),
    "analisi": (
        "help.tab.analisi.short", "help.tab.analisi.long"),
    "explorer": (
        "help.tab.explorer.short", "help.tab.explorer.long"),
    "cicli": (
        "help.tab.cicli.short", "help.tab.cicli.long"),
    "distribuzione": (
        "help.tab.distribuzione.short", "help.tab.distribuzione.long"),
    "simulatore": (
        "help.tab.simulatore.short", "help.tab.simulatore.long"),
    "tavola": (
        "help.tab.tavola.short", "help.tab.tavola.long"),
}

#: I7: sotto-schede di ogni scheda → (chiave dell'etichetta, chiave dell'aiuto).
#: L'aiuto esteso della scheda elenca le sue sotto-schede con una riga ciascuna.
SOTTOSCHEDE_HELP = {
    "simulatore": (
        ("simulator.tab.instructions", "help.sub.istruzioni"),
        ("simulator.tab.deck", "help.sub.mazzo"),
        ("simulator.tab.practice", "help.sub.pratica"),
        ("spectator.tab", "help.sub.spettatore"),
    ),
    "tavola": (
        ("ternary.tab.board", "help.sub.tabellone"),
        ("ternary.tab.card", "help.sub.una_carta"),
        ("ternary.tab.positions", "help.sub.posizioni"),
    ),
    "explorer": (
        ("explorer.tab.numeric", "help.sub.numerico"),
        ("explorer.tab.rewrite", "help.sub.riscrittura"),
        ("explorer.tab.algebra", "help.sub.algebra"),
        ("explorer.tab.partial_steps", "help.sub.passi"),
        ("explorer.tab.canonical", "help.sub.canonica"),
        ("explorer.tab.matrix", "help.sub.matrice"),
        ("explorer.tab.shuffle", "help.sub.mescolamento"),
        ("recognition.tab", "help.sub.riconoscimento"),
        ("lab.tab", "help.sub.laboratorio"),
    ),
    "cicli": (
        ("cycles.tab.disjoint", "help.sub.cicli_disgiunti"),
        ("cycles.tab.orbits", "help.sub.orbite"),
    ),
}


def testo_aiuto_scheda(chiave):
    """Aiuto esteso della scheda, con una riga per ogni sotto-scheda."""
    _breve, esteso = TAB_HELP[chiave]
    testo = tr(esteso)
    sotto = SOTTOSCHEDE_HELP.get(chiave)
    if not sotto:
        return testo
    righe = [tr("help.sub.heading", count=len(sotto))]
    righe += [f"•  {tr(etichetta)} — {tr(aiuto)}" for etichetta, aiuto in sotto]
    return testo + "\n\n" + "\n".join(righe)
