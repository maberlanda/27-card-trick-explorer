"""Identita' delle richieste: cio' che distingue «obsoleto» da tutto il resto.

Compartimento G2. L'inventario dei lavori asincroni del programma — analisi,
export massivi, selftest, ricerca delle decomposizioni, distribuzione — ha
trovato cinque esecuzioni diverse (thread + `ui_call`, thread + coda +
`after`, pool di processi) e **due sole** nozioni davvero condivise:

* **obsolescenza** — una richiesta piu' nuova ha sostituito quella in volo. Il
  lavoro vecchio puo' ancora terminare tecnicamente, ma non deve pubblicare.
  Era scritta due volte a mano, come contatore monotono: `_analisi_revisione`
  nella scheda Analisi (compartimento C) e `_search_id` nella finestra delle
  decomposizioni. E' la duplicazione che questo modulo elimina;
* **annullamento** — a un lavoro viene chiesto di fermarsi. Ha gia' un
  contratto unico, e sta nel core: la callable `annullato() -> bool` di
  `core.parallel`, con `mai_annullato` come sentinella ed `ExportAnnullato`
  come esito. G2 non ne scrive un secondo.

Le due nozioni restano separate di proposito. Annullare e' una richiesta che
arriva **al** lavoro; diventare obsoleti e' una decisione che riguarda **il
suo risultato**, presa altrove e senza che il lavoro ne sappia nulla. Fonderle
in un unico booleano perderebbe esattamente la distinzione che C ha
introdotto: una richiesta superata continua e viene scartata, non viene
interrotta.

Qui non c'e' un gestore dei lavori, ne' una coda, ne' priorita': oggi nessun
flusso del programma ha una semantica di priorita' fra lavori, e nessuno
memorizza o interroga uno stato del lavoro. Introdurre `JobState`,
`JobManager` o uno scheduler significherebbe progettare un futuro invece di
consolidare il presente.

Il modulo non conosce Tk, la GUI, il filesystem o il resto dei servizi: usa
solo `threading`.
"""

import threading

__all__ = ["Revisioni"]


class Revisioni:
    """Contatore monotono delle richieste di un pannello.

    Ogni azione che cambia cio' che si sta calcolando apre una nuova
    revisione, e con cio' rende obsolete tutte le risposte ancora in volo::

        revisioni = Revisioni()
        mia = revisioni.nuova()
        ...                                   # lavoro in un thread
        if revisioni.e_corrente(mia):
            pubblica(risultato)

    `nuova()` e' un incremento **letto e scritto** sotto lock: e' un'operazione
    composta, e il GIL non la rende atomica. In pratica oggi la si chiama solo
    dal thread Tk, ma il contratto non lo impone e un lettore che interroga
    `e_corrente` da un worker deve comunque vedere un valore coerente.

    Il valore restituito e' un intero: chi lo riceve non ha bisogno di
    conoscere questa classe, e puo' portarselo dietro in una chiusura, in una
    coda o in un `after`.
    """

    __slots__ = ("_lock", "_corrente")

    def __init__(self, iniziale=0):
        self._lock = threading.Lock()
        self._corrente = int(iniziale)

    @property
    def corrente(self) -> int:
        """La revisione attualmente valida."""
        with self._lock:
            return self._corrente

    def nuova(self) -> int:
        """Apre una nuova richiesta: le precedenti diventano obsolete."""
        with self._lock:
            self._corrente += 1
            return self._corrente

    def e_corrente(self, revisione) -> bool:
        """`revisione` e' ancora quella valida?

        Non dice nulla sulla vita della finestra o sulla chiusura del
        programma: quelle sono condizioni della presentation, che le compone
        con questa.
        """
        with self._lock:
            return revisione == self._corrente

    def __repr__(self):
        return f"Revisioni(corrente={self.corrente})"
