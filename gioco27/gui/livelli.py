"""Livelli didattici (DP7, compartimento I7): chi vede che cosa.

Un unico mapping dichiarativo «vista → livello minimo». Il livello controlla
soltanto la VISIBILITA' di schede, sotto-schede e azioni: la matematica, i
dati e le sessioni in corso non cambiano. Salire di livello mostra piu'
strumenti; scendere li nasconde senza distruggere nulla.

    1. base         — gesto e base 3
    2. intermedio   — permutazioni e matrici
    3. avanzato     — struttura
    4. laboratorio  — verifica ed esplorazione

Niente Tk qui: `app.py` applica il mapping, i test lo controllano.
"""

from ..core.config import LIVELLI_DIDATTICI, migra_valore

__all__ = [
    "LIVELLI", "BASE", "INTERMEDIO", "AVANZATO", "LABORATORIO",
    "SCHEDE", "SOTTOSCHEDE_EXPLORER", "ORDINE_SOTTOSCHEDE_EXPLORER", "AZIONI",
    "PREREQUISITI", "normalizza", "indice", "visibile", "livello_di",
]

LIVELLI = LIVELLI_DIDATTICI
BASE, INTERMEDIO, AVANZATO, LABORATORIO = LIVELLI

#: Schede principali (chiavi stabili di `App._schede`) → livello minimo.
SCHEDE = {
    "inizio": BASE,
    "simulatore": BASE,          # istruzioni, mazzo, Pratica, Spettatore
    "tavola": BASE,              # Tavola 216, tabellone, pannello ternario, ritorno
    "guida": BASE,
    "anteprima": INTERMEDIO,     # una combinazione: T, T⁻¹, effetto sul mazzo
    "cicli": INTERMEDIO,         # cicli, ordine, orbite
    "explorer": AVANZATO,        # forma canonica, matrici, riconoscimento
    "analisi": LABORATORIO,      # insieme filtrato, molteplicità
    "distribuzione": LABORATORIO,
    "stadio0": LABORATORIO,      # i filtri servono ad Analisi / Distribuzione
    "stadio1": LABORATORIO,
    "stadio2": LABORATORIO,
}

#: Le nove sotto-schede dell'Explorer, nell'ordine in cui sono costruite.
ORDINE_SOTTOSCHEDE_EXPLORER = (
    "numerico", "riscrittura", "algebra", "passi", "canonica",
    "matrice", "mescolamento", "riconoscimento", "laboratorio",
)
SOTTOSCHEDE_EXPLORER = {k: AVANZATO for k in ORDINE_SOTTOSCHEDE_EXPLORER}
SOTTOSCHEDE_EXPLORER["laboratorio"] = LABORATORIO

#: Azioni della barra (chiavi di `App._azioni_livello`) → livello minimo.
AZIONI = {
    "conteggio": LABORATORIO,     # conta l'insieme filtrato dagli Stadi
    "genera": LABORATORIO,        # export dell'insieme filtrato
    "combinazioni": LABORATORIO,  # contatore dell'insieme filtrato
    "preset": LABORATORIO,        # la barra preset imposta i filtri degli Stadi
    "protocollo": AVANZATO,       # istruzioni dall'ultima T dell'Explorer
    "cayley": AVANZATO,
    "coniugio": AVANZATO,
}

#: Vista → viste da cui dipende. Nessuna vista sta sotto un suo prerequisito.
PREREQUISITI = {
    "analisi": ("stadio0", "stadio1", "stadio2"),
    "distribuzione": ("stadio0", "stadio1", "stadio2"),
    "conteggio": ("stadio0", "stadio1", "stadio2"),
    "genera": ("stadio0", "stadio1", "stadio2"),
    "preset": ("stadio0", "stadio1", "stadio2"),
    "cicli": ("tavola",),
    "explorer": ("anteprima", "cicli"),
    "protocollo": ("explorer",),
    "laboratorio": ("explorer",),
    "riconoscimento": ("explorer",),
}


def normalizza(valore):
    """Un livello valido; i valori delle versioni precedenti vengono migrati."""
    valore = migra_valore("livello", valore)
    return valore if valore in LIVELLI else BASE


def indice(valore):
    return LIVELLI.index(normalizza(valore))


def visibile(minimo, corrente):
    """True se una vista di livello `minimo` si vede al livello `corrente`."""
    return indice(minimo) <= indice(corrente)


def livello_di(chiave):
    """Livello minimo di una scheda, sotto-scheda o azione (KeyError se ignota)."""
    for tabella in (SCHEDE, SOTTOSCHEDE_EXPLORER, AZIONI):
        if chiave in tabella:
            return tabella[chiave]
    raise KeyError(chiave)
