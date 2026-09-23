"""Modelli applicativi condivisi: il risultato di un'analisi.

Compartimento G1. Fino a F ogni compartimento aveva lasciato il proprio
modello dove serviva: `RisultatoAnalisi` dentro il tab (C), `RisultatiImport`
e `PianoAnalisi` dentro il core (F). Erano scelte deliberate — nessuno dei due
aveva ancora due consumatori — ma il prezzo era che la scheda dovesse
ricostruire il significato dell'analisi da attributi indipendenti: «se le
righe grezze sono vuote allora forse l'origine e' un CSV, oppure forse il
piano le ha scartate».

Qui quel significato diventa un contratto solo. Il modello non e' la somma
degli attributi di prima: porta cio' che serve a decidere, e niente altro.

Che cosa distingue
------------------

    zero risultati validi      aggregati == ()          lo schema era valido,
                               e nessuno scarto         il dominio no

    nessun grezzo conservato   grezzi_scartati = True   il piano ha deciso di
                                                        non trattenerli

    origine senza grezzi       grezzi_scartati = False  un CSV di aggregati non
                               e grezzi == ()           ne produce affatto

    risultato parziale         scartate != ()           qualche riga e' stata
                                                        rifiutata, e si sa quale

    richiesta fallita          nessun risultato         e' un'eccezione
                                                        (SchemaNonRiconosciuto,
                                                        AnalisiTroppoGrande,
                                                        FiltroNonValido)

Che cosa **non** porta: la revisione della richiesta. Chi decide se un
risultato vada ancora pubblicato e' il ciclo di vita della vista (C), non il
risultato: un servizio non ha modo di sapere quale richiesta sia corrente, e
mettergli quel campo in mano lo obbligherebbe a inventarselo. La revisione
resta quindi accanto al risultato, al momento della pubblicazione.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple

__all__ = ["Provenienza", "RisultatoAnalisi"]


class Provenienza(str, Enum):
    """Da dove vengono i dati aggregati.

    Sottoclasse di `str` di proposito: il valore continua a confrontarsi con
    le stringhe storiche (`"filtri"`, `"csv"`, `"pipeline"`) usate da viste e
    test, ma l'insieme dei valori ammessi e' ora chiuso e nominato.
    """

    FILTRI = "filtri"          # enumerazione dal dominio dei filtri
    CSV = "csv"                # import di un CSV COMBINAZIONI
    PIPELINE = "pipeline"      # import + scrittura di CSV ed Excel di analisi

    def __str__(self):         # per i messaggi: «filtri», non «Provenienza.FILTRI»
        return self.value


@dataclass(frozen=True)
class RisultatoAnalisi:
    """Il risultato di **una** analisi, qualunque sia la sua provenienza.

    Congelato: una volta pubblicato non puo' cambiare significato. Le
    sequenze sono tuple per la stessa ragione.

    Campi
    -----
    origine
        `Provenienza`: filtri, CSV o pipeline.
    aggregati
        Le righe aggregate, una per permutazione distinta, nella forma
        stabilita da F (`perm_tuple`, `perm_str`, `simboliche`, `n_sim`).
    totale
        Il numero di sequenze rappresentate: le combinazioni del dominio per
        l'analisi dai filtri, la somma delle molteplicita' per un import.
    grezzi
        Le righe di partenza, quando sono state conservate.
    grezzi_scartati
        True se il piano ha deciso di non trattenerle: distingue «non ci
        sono» da «non le abbiamo tenute».
    lette
        Quante righe sono state esaminate (import).
    scartate
        Le `RigaScartata` di F: numero di riga, campo, motivo.
    nota
        Testo libero gia' pronto per l'utente (il nome del file importato, il
        motivo per cui i grezzi non sono stati tenuti).
    """

    origine: Provenienza
    aggregati: Tuple[dict, ...] = ()
    totale: int = 0
    grezzi: Tuple[dict, ...] = ()
    grezzi_scartati: bool = False
    lette: int = 0
    scartate: Tuple[object, ...] = field(default_factory=tuple)
    nota: str = ""

    # ── stati, come proprieta' derivate (niente enum in piu' del necessario) ──

    @property
    def grezzi_disponibili(self) -> bool:
        """Gli export che richiedono le righe grezze possono partire?"""
        return bool(self.grezzi)

    @property
    def vuoto(self) -> bool:
        """Nessun aggregato: il dominio era vuoto o tutte le righe scartate."""
        return not self.aggregati

    @property
    def parziale(self) -> bool:
        """Qualche riga e' stata rifiutata: il risultato non copre l'ingresso."""
        return bool(self.scartate)

    @property
    def completo(self) -> bool:
        """Copre tutto l'ingresso e conserva tutto quello che poteva."""
        return not self.parziale and not self.grezzi_scartati

    @property
    def diagnostica(self) -> str:
        """Tutto cio' che l'utente deve sapere sul come, in una riga.

        E' una proprieta' e non un campo: il testo si ricava dallo stato, e
        cosi' non puo' contraddirlo. Resta una stringa perche' e' esattamente
        quello che la vista accoda al riepilogo.
        """
        return self.nota

    def con_nota(self, nota: str) -> "RisultatoAnalisi":
        """Copia con una nota diversa (il modello resta congelato)."""
        return RisultatoAnalisi(
            origine=self.origine, aggregati=self.aggregati, totale=self.totale,
            grezzi=self.grezzi, grezzi_scartati=self.grezzi_scartati,
            lette=self.lette, scartate=self.scartate, nota=nota)
