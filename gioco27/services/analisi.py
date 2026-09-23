"""Servizio applicativo dell'analisi: orchestrazione, non algoritmi.

Compartimento G1. Il calcolo dell'analisi era distribuito su tre livelli: gli
algoritmi in `core.analisi` e `core.combinations` (F), l'ingresso da CSV in
`core.algebra`, e l'orchestrazione — piano, ciclo di enumerazione,
costruzione della riga, aggregazione, composizione del risultato e della
diagnostica — dentro `gui.analysis_tab`. La scheda conosceva
`iter_combinations_ex`, `make_csv_row`, `Aggregatore` e `analizza_righe`, e
costruiva il risultato in tre punti diversi, uno per provenienza.

Qui quell'orchestrazione diventa un servizio: ingresso esplicito, uscita
esplicita, nessun widget, nessun thread. Gli algoritmi non vengono riscritti —
sono quelli di F, chiamati da qui.

    filtri ────────┐
                   ├──► ServizioAnalisi ──► RisultatoAnalisi
    CSV / pipeline ┘

Il servizio e' **sincrono**. Non sa di essere chiamato da un thread e non
decide se il suo risultato vada pubblicato: quella e' la revisione della
vista (C). Chi lo chiama da un worker gli passa `ancora_valida`, e il
servizio si limita a smettere e a restituire `None` quando quella dice di no.
Il gestore generale dei lavori resta un problema di G2.
"""

import os

from ..core.analisi import (Aggregatore, PianoAnalisi, importa_csv,
                            pianifica_analisi)
from ..core.combinations import iter_combinations_ex
from ..core.export_analisi import scrivi_excel, scrivi_output
from ..core.permutations import make_csv_row
from .modelli import Provenienza, RisultatoAnalisi

__all__ = ["ServizioAnalisi", "servizio_analisi"]

#: Ogni quante combinazioni il servizio riporta l'avanzamento e ricontrolla se
#: il lavoro e' ancora voluto. E' il passo storico della scheda.
PASSO_AVANZAMENTO = 200


class ServizioAnalisi:
    """Orchestra validazione, piano, enumerazione, aggregazione e risultato.

    Senza stato: puo' essere istanziato ovunque, e l'istanza condivisa
    `servizio_analisi()` esiste solo per comodita' dei chiamanti.
    """

    # ── piano ────────────────────────────────────────────────────────────────

    def pianifica(self, filtri) -> PianoAnalisi:
        """Valida i filtri e decide il lavoro senza enumerare nulla.

        Solleva `FiltroNonValido` se i filtri non rispettano il contratto e
        `AnalisiTroppoGrande` se il dominio supera il budget: sono le stesse
        eccezioni di F, non tradotte e non rimpacchettate.
        """
        return pianifica_analisi(filtri)

    # ── analisi dal dominio dei filtri ───────────────────────────────────────

    def da_filtri(self, filtri, *, piano=None, progresso=None,
                  ancora_valida=None):
        """Enumera il dominio, aggrega e costruisce il risultato.

        `progresso(fatte, totale)` viene chiamata ogni `PASSO_AVANZAMENTO`
        combinazioni; `ancora_valida()` viene interrogata con la stessa
        cadenza e prima di concludere. Se dice di no il servizio smette e
        restituisce `None`: nessun risultato a meta' viene costruito.
        """
        piano = self.pianifica(filtri) if piano is None else piano
        valida = ancora_valida or (lambda: True)

        # In modalita' completa le righe restano comunque tutte: l'aggregatore
        # si limita a trattenerle e i gruppi li costruisce dopo, una volta
        # sola. Sopra il limite non trattiene nulla e conta al volo.
        aggregatore = Aggregatore(tieni_grezzi=piano.grezzi,
                                  aggrega=not piano.grezzi)
        for fatte, params in enumerate(iter_combinations_ex(filtri), 1):
            if not valida():
                return None
            riga = make_csv_row(fatte, params)
            aggregatore.aggiungi({
                "Stage0": riga[1], "Stage1": riga[2], "Stage2": riga[3],
                "A0": riga[4], "A1": riga[5], "A2": riga[6],
                "T_simbolica": riga[7], "T_permutazione": riga[8],
            })
            if progresso is not None and fatte % PASSO_AVANZAMENTO == 0:
                progresso(fatte, piano.combinazioni)
        if not valida():
            return None

        if piano.grezzi:
            esito = _aggrega(aggregatore.grezzi)
            aggregati, scartate, lette = tuple(esito), esito.scartate, esito.lette
        else:
            aggregati = tuple(aggregatore.risultati())
            scartate, lette = aggregatore.scartate, aggregatore.lette
        if not valida():
            return None

        return RisultatoAnalisi(
            origine=Provenienza.FILTRI, aggregati=aggregati,
            totale=piano.combinazioni, grezzi=aggregatore.grezzi,
            grezzi_scartati=not piano.grezzi, lette=lette, scartate=scartate)

    # ── analisi da un file ───────────────────────────────────────────────────

    def da_csv(self, percorso) -> RisultatoAnalisi:
        """Importa un CSV COMBINAZIONI e aggrega.

        Solleva `SchemaNonRiconosciuto` quando il file non appartiene a uno
        schema importabile: un file che non si sa leggere non e' un'analisi
        vuota, e l'export dell'analisi resta deliberatamente non importabile
        (F).
        """
        esito = importa_csv(percorso)
        return _da_import(esito, Provenienza.CSV, percorso)

    def pipeline_csv(self, ingresso, csv_uscita, excel_uscita, *,
                     ancora_valida=None) -> RisultatoAnalisi:
        """Importa, scrive il CSV e l'Excel di analisi, e restituisce il risultato.

        Le due scritture restano quelle di B (`core.export_analisi`): qui non
        c'e' nessun nuovo livello di export, solo l'ordine in cui accadono.
        """
        valida = ancora_valida or (lambda: True)
        esito = importa_csv(ingresso)
        if not valida():
            return None
        scrivi_output(esito, csv_uscita)
        if not valida():
            return None
        scrivi_excel(esito, excel_uscita)
        if not valida():
            return None
        return _da_import(esito, Provenienza.PIPELINE, ingresso)


def _aggrega(righe):
    """Aggrega righe gia' trattenute riusando l'implementazione di F."""
    from ..core.analisi import aggrega_righe
    return aggrega_righe(righe)


def _da_import(esito, origine, percorso) -> RisultatoAnalisi:
    """Traduce l'esito di un import nel modello applicativo condiviso."""
    note = [os.path.basename(str(percorso))]
    riassunto = esito.diagnostica()
    if riassunto:
        note.append(riassunto)
    return RisultatoAnalisi(
        origine=origine, aggregati=tuple(esito),
        totale=sum(r["n_sim"] for r in esito),
        grezzi=(), grezzi_scartati=False,
        lette=esito.lette, scartate=esito.scartate,
        nota="   —   ".join(note))


_SERVIZIO = ServizioAnalisi()


def servizio_analisi() -> ServizioAnalisi:
    """L'istanza condivisa. Il servizio e' senza stato: e' solo comodita'."""
    return _SERVIZIO
