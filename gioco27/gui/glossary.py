"""
Testi della scheda "Inizia qui" e del glossario, in italiano semplice.

Tenuti separati dalla GUI così si possono rivedere senza toccare il codice.
Ogni voce del glossario è (termine, descrizione_breve, descrizione_estesa):
la breve compare nella lista, l'estesa nel tooltip al passaggio del mouse.
"""

ONBOARD_INTRO = "onboarding.intro"

# (icona/numero, titolo, descrizione)
ONBOARD_STEPS = [
    ("1", "Prova il Simulatore",
     "onboarding.step1.desc"),
    ("2", "Sfoglia la Tavola 216",
     "onboarding.step2.desc"),
    ("3", "Approfondisci",
     "onboarding.step3.desc"),
]

    # (termine, breve, chiave della descrizione estesa nel catalogo i18n)
GLOSSARY = [
    ("MSC",
     "Il mescolamento di base: distribuisci le 27 carte in 3 colonne e le raccogli.",
     "glossary.long.msc"),
    ("Permutazione",
     "Un modo di rimescolare: a ogni posizione di partenza associa una posizione d'arrivo.",
     "glossary.long.permutation"),
    ("Stadio",
     "Una singola «mossa» del gioco: una raccolta P, il mescolamento MSC e un'orientazione J.",
     "glossary.long.stage"),
    ("P (raccolta)",
     "Come raccogli i tre pacchetti dopo averli messi in colonna.",
     "glossary.long.collection"),
    ("Mescolamento",
     "La sigla funzionale della raccolta: la cifra N va nella N-esima lettera.",
     "glossary.long.shuffle"),
    ("Impilamento",
     "Il gesto fisico: l'ordine dei mazzetti dal dorso verso il fondo.",
     "glossary.long.stacking"),
    ("J (orientazione)",
     "Come orienti o giri il mazzo prima del mescolamento.",
     "glossary.long.orientation"),
    ("Gioco Reale",
     "Un insieme pronto di 1 728 sequenze: l'esempio classico da cui partire.",
     "glossary.long.real_game"),
    ("T  /  T⁻¹",
     "La trasformazione totale delle 3 mosse (T) e la sua inversa (T⁻¹).",
     "glossary.long.total_transform"),
    ("Coniugio",
     "Due mosse «coniugate» fanno la stessa cosa, a meno di rinominare le posizioni.",
     "glossary.long.conjugacy"),
    ("Cayley (tavola)",
     "La tabella di tutti i prodotti possibili tra due mosse del gruppo.",
     "glossary.long.cayley"),
    ("Kronecker",
     "Scompone una mossa in tre pezzi indipendenti: pacchetti, terzine e carte.",
     "glossary.long.kronecker"),
    ("Ciclo",
     "Un gruppetto di posizioni che ruotano tra loro ripetendo la mossa.",
     "glossary.long.cycle"),
    ("Ordine",
     "Quante volte ripetere una mossa per tornare al punto di partenza.",
     "glossary.long.order"),
]


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
