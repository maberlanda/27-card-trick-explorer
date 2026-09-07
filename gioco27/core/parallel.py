"""
Infrastruttura comune per gli export massivi (CSV, PDF, PDF dettagliato).

Perche' questo modulo esiste
----------------------------
Le versioni parallele degli export erano quattro funzioni quasi identiche, e
tutte cominciavano con:

    all_params = list(iter_combinations_ex(filters))

Con i filtri di default (tutto su "*") il numero di combinazioni e'
1728^3 = 5.159.780.352: quel `list()` prova a materializzare cinque miliardi
di tuple in RAM e fa morire il processo prima di scrivere un solo byte.

Qui la generazione resta un *flusso*: i blocchi vengono creati e sottomessi in
modo incrementale, con una finestra limitata di task pendenti (`max_pending`),
quindi la memoria occupata non dipende dal totale.

API
---
chunked(iterable, size)
    Spezza un iterabile pigro in liste di `size` elementi. Non materializza
    l'intero iterabile.

imap_ordered(worker, tasks, n_workers, max_pending)
    Come ProcessPoolExecutor.map, ma consuma `tasks` in modo pigro, tiene al
    massimo `max_pending` future in volo e restituisce i risultati
    NELL'ORDINE DI SOTTOMISSIONE (serve per l'ordine deterministico delle
    righe CSV e delle pagine PDF).

plan_workers(total, n_workers, min_per_worker)
    Decide quanti worker usare e la dimensione dei blocchi; None se conviene
    il sequenziale (lo spawn costa troppo per pochi elementi).

run_export(...)
    Schema comune: controllo del limite, piano, streaming, consumo ordinato,
    fallback sequenziale su qualunque errore.
"""
import contextlib
from collections import deque
from itertools import islice
import math
import os
import sys
import time

from .log import get_logger

_log = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────
# Taratura del parallelismo
#
# I valori di soglia precedenti (80 elementi per worker per il PDF, 400 per il
# CSV) erano tarati su macchine da 4-8 core, dove non mordono mai. Su una
# macchina a 128 core mordevano sempre: l'export standard del Gioco Reale
# (1728 combinazioni) otteneva 21 worker per il PDF e 4 per il CSV, cioe' il
# 16% e il 3% della CPU disponibile.
#
# Il modello corretto e' questo: i processi figli vengono avviati in
# parallelo, quindi il costo di spawn e' una LATENZA quasi costante (~1-2 s su
# Windows, dove ogni figlio re-importa numpy e reportlab), non un costo per
# worker. Conviene quindi usare piu' worker possibile, con due sole
# limitazioni:
#
#   1. se il lavoro totale stimato e' inferiore a LAVORO_MINIMO_S, il
#      parallelo non ripaga nemmeno la latenza di avvio: si resta in-process;
#   2. ogni worker deve avere almeno MIN_ITEMS_PER_WORKER elementi, altrimenti
#      si pagano N avvii per briciole di lavoro.
#
# In piu' i blocchi sono ora UNO PER WORKER (prima quattro): le pagine hanno
# tutte lo stesso costo, quindi la suddivisione statica e' gia' bilanciata, e
# ogni blocco in piu' e' un PDF in piu' da unire, con la sua copia dei font.

#: Costo medio per elemento, misurato su questa base di codice. Serve solo a
#: decidere SE parallelizzare, quindi basta l'ordine di grandezza.
COSTO_PAGINA_PDF        = 0.0033    # PDF standard, per pagina
COSTO_COMBO_DETTAGLIO   = 0.0057    # PDF dettagliato, per combinazione
COSTO_RIGA_CSV          = 0.000009  # CSV, per riga

#: Sotto questo lavoro stimato (secondi) si resta sequenziali: avviare dei
#: processi costerebbe piu' del calcolo.
LAVORO_MINIMO_S = 0.5

#: Lavoro utile minimo per worker (secondi). Ogni blocco costa qualcosa oltre
#: al calcolo — un PDF parziale da unire, con la sua copia dei font — quindi
#: non ha senso spezzettare oltre: se ogni worker fa meno di questo, i blocchi
#: si allargano invece di moltiplicarsi.
LAVORO_PER_WORKER_S = 0.20

#: Elementi minimi per worker quando il costo per elemento non e' noto.
MIN_ITEMS_PER_WORKER = 8


#: Numero massimo di elementi che un export si permette di produrre.
#: Non e' arbitrario: e' la soglia oltre la quale l'operazione non finirebbe in
#: tempi umani (a ~1 ms per elemento, 20 milioni sono circa 6 ore) e il file
#: risultante sarebbe comunque inutilizzabile.
MAX_EXPORT_ITEMS = 20_000_000


class ExportAnnullato(Exception):
    """
    L'utente ha annullato l'export.

    Non e' un errore: viene sollevata per srotolare il lavoro in corso e va
    intercettata dal chiamante, che NON deve mostrarla come un guasto.

    Grazie alla scrittura atomica (`atomic_write`) un export annullato non
    lascia nulla: il file di destinazione resta com'era, e il temporaneo viene
    rimosso.
    """

    def __init__(self, fatti=0, totale=0):
        self.fatti = fatti
        self.totale = totale
        super().__init__(f"Export annullato dopo {fatti:,} di {totale:,} elementi")


def mai_annullato():
    """Sentinella predefinita: nessun annullamento richiesto."""
    return False


def _check_cancelled(annullato, fatti=0, totale=0):
    if annullato is not None and annullato():
        raise ExportAnnullato(fatti, totale)


class ExportTooLarge(RuntimeError):
    """L'export richiesto supera MAX_EXPORT_ITEMS: rifiutato prima di iniziare."""

    def __init__(self, requested, limit=MAX_EXPORT_ITEMS):
        self.requested = requested
        self.limit = limit
        super().__init__(
            "L'export richiederebbe {:,} elementi, oltre il limite di sicurezza "
            "di {:,}.\n\nRestringi i filtri: fissa qualche fattore P o J invece "
            "di lasciarlo su «*».".format(requested, limit))


def check_export_size(total):
    """Solleva ExportTooLarge se `total` supera il limite di sicurezza."""
    if total > MAX_EXPORT_ITEMS:
        raise ExportTooLarge(total)


def chunked(iterable, size):
    """
    Yield liste di al massimo `size` elementi presi da `iterable`.

    Pigro: consuma `iterable` un blocco alla volta, quindi funziona anche su
    generatori con miliardi di elementi.
    """
    if size <= 0:
        raise ValueError("size deve essere > 0")
    it = iter(iterable)
    while True:
        block = list(islice(it, size))
        if not block:
            return
        yield block


#: Tetto imposto dalla piattaforma al numero di processi di un pool.
#:
#: Su Windows `ProcessPoolExecutor` NON accetta piu' di 61 worker: solleva
#: `ValueError: max_workers must be <= 61`. Il limite viene da
#: WaitForMultipleObjects, che gestisce al massimo 64 handle.
#:
#: Era un guasto silenzioso e grave: su una macchina a 128 core il programma
#: chiedeva 127 worker, riceveva ValueError alla creazione del pool, e il
#: blocco `except Exception` faceva ripiegare sul sequenziale registrandolo
#: solo nel log. Risultato: su quelle macchine il parallelismo non ha MAI
#: funzionato, per nessun export, e l'utente vedeva l'1-2% di CPU senza
#: capirne il motivo.
def max_workers_piattaforma():
    """Numero massimo di worker che un ProcessPoolExecutor accetta, o None."""
    if sys.platform == "win32":
        try:
            from concurrent.futures.process import _MAX_WINDOWS_WORKERS
            return int(_MAX_WINDOWS_WORKERS)
        except Exception:
            return 61
    return None


def default_workers(n_workers=None):
    """
    n_workers esplicito, oppure tutti i core logici meno uno, comunque entro
    il tetto della piattaforma.
    """
    if n_workers is None:
        n_workers = max(1, (os.cpu_count() or 2) - 1)
    n_workers = int(n_workers)

    tetto = max_workers_piattaforma()
    if tetto is not None and n_workers > tetto:
        _log.info("Worker richiesti %d, ridotti a %d: limite di %s "
                  "(ProcessPoolExecutor non ne accetta di piu')",
                  n_workers, tetto, sys.platform)
        n_workers = tetto
    return max(1, n_workers)


def plan_workers(total, n_workers=None, min_per_worker=None,
                 min_chunk=1, chunks_per_worker=1, cost_per_item=None):
    """
    Decide la strategia di parallelizzazione.

    Restituisce (n_workers, chunk_size) oppure None se conviene il sequenziale.

    Si resta sequenziali quando:
      * c'e' un solo core disponibile;
      * il lavoro stimato (`total * cost_per_item`) e' sotto LAVORO_MINIMO_S;
      * non ci sono abbastanza elementi per almeno due worker.

    Altrimenti si usano piu' worker possibile, con il vincolo che ciascuno
    abbia almeno LAVORO_PER_WORKER_S di lavoro utile: i processi si avviano in
    parallelo, quindi lo spawn e' una latenza quasi costante e conviene
    distribuire — ma ogni blocco in piu' e' un file parziale in piu' da unire,
    quindi spezzettare all'infinito peggiora.

    Un blocco per worker (`chunks_per_worker=1`): le pagine hanno costo
    uniforme, la suddivisione statica e' gia' bilanciata.
    """
    n_workers = default_workers(n_workers)
    if n_workers <= 1:
        return None

    if cost_per_item is not None:
        if total * cost_per_item < LAVORO_MINIMO_S:
            _log.debug("parallelo saltato: lavoro stimato %.3f s < %.1f s",
                       total * cost_per_item, LAVORO_MINIMO_S)
            return None
        if min_per_worker is None:
            min_per_worker = max(MIN_ITEMS_PER_WORKER,
                                 math.ceil(LAVORO_PER_WORKER_S / cost_per_item))
    if min_per_worker is None:
        min_per_worker = MIN_ITEMS_PER_WORKER

    if total < 2 * min_per_worker:
        return None

    n_workers = max(2, min(n_workers, total // min_per_worker))
    chunk = max(min_chunk, math.ceil(total / (n_workers * chunks_per_worker)))
    return n_workers, chunk


def imap_ordered(worker, tasks, n_workers, max_pending=None,
                 executor_factory=None, annullato=None, attesa=0.2):
    """
    Applica `worker` a ogni elemento di `tasks` su n_workers processi,
    restituendo i risultati nell'ordine di sottomissione.

    A differenza di ProcessPoolExecutor.map non consuma tutto `tasks` in
    anticipo: tiene al massimo `max_pending` future in volo (default 3x
    n_workers), quindi la memoria dipende dalla finestra, non dal totale.

    `worker` deve essere picklable (funzione top-level o oggetto di classe
    top-level con __call__).

    `executor_factory` permette di iniettare un esecutore diverso da
    ProcessPoolExecutor: serve ai test per verificare il ripiego sul tetto di
    piattaforma senza avviare processi veri.

    `annullato()` viene interrogata ogni `attesa` secondi mentre si aspettano i
    risultati. All'annullamento le future non ancora avviate vengono cancellate
    e il pool viene chiuso SENZA attenderlo: i processi che stanno gia'
    macinando un blocco lo finiscono per conto loro e il risultato viene
    buttato, ma il chiamante torna subito. Senza questo, con un blocco per
    worker si sarebbe aspettato il completamento di un blocco intero — minuti,
    su un export grande.
    """
    from concurrent.futures import ProcessPoolExecutor, FIRST_COMPLETED, wait

    if executor_factory is None:
        executor_factory = ProcessPoolExecutor

    if max_pending is None:
        max_pending = max(2, n_workers * 3)

    if annullato is None:
        annullato = mai_annullato

    task_iter = iter(tasks)
    try:
        pool_ctx = executor_factory(max_workers=n_workers)
    except ValueError:
        # Rete di sicurezza: se la piattaforma rifiuta comunque il numero di
        # worker, si riprova col tetto invece di far fallire tutto l'export.
        tetto = max_workers_piattaforma() or 8
        _log.warning("Pool con %d worker rifiutato: riprovo con %d",
                     n_workers, tetto)
        n_workers = min(n_workers, tetto)
        max_pending = max(2, n_workers * 3)
        pool_ctx = executor_factory(max_workers=n_workers)

    pool = pool_ctx
    annullamento = False
    try:
        pending = deque()

        def fill():
            while len(pending) < max_pending:
                _check_cancelled(annullato)
                try:
                    t = next(task_iter)
                except StopIteration:
                    return
                _check_cancelled(annullato)
                pending.append(pool.submit(worker, t))

        fill()
        while pending:
            # Si aspetta a piccoli passi per poter reagire all'annullamento
            # senza attendere il completamento di un blocco intero.
            while not pending[0].done():
                if annullato():
                    annullamento = True
                    raise ExportAnnullato()
                wait(list(pending), timeout=attesa,
                     return_when=FIRST_COMPLETED)
            while pending and pending[0].done():
                _check_cancelled(annullato)
                yield pending.popleft().result()
            fill()
        _check_cancelled(annullato)
    except ExportAnnullato:
        annullamento = True
        raise
    finally:
        if annullamento or annullato():
            # Niente attesa: i figli finiscono il blocco in corso per conto
            # loro e il risultato viene scartato.
            pool.shutdown(wait=False, cancel_futures=True)
        else:
            pool.shutdown(wait=True)


class _SizedWorker:
    """
    Callable picklable: (start, blocco) -> (worker(start, blocco), len(blocco)).

    Serve perche' il chiamante sappia quanti elementi ha prodotto ogni blocco
    senza doverlo dedurre dal risultato (che puo' essere un blob di byte PDF).
    """

    def __init__(self, worker):
        self.worker = worker

    def __call__(self, task):
        start, block = task
        return self.worker(start, block), len(block)


def run_export(*, total, items_iter, sequential, parallel_worker, consume,
               n_workers=None, min_per_worker=None,
               min_chunk=1, cost_per_item=None,
               progress_cb=None, annullato=None, what="export"):
    """
    Schema comune degli export paralleli, con fallback al sequenziale.

    Parametri
    ---------
    total            elementi previsti (da count_combinations_ex)
    items_iter       iteratore PIGRO sulle combinazioni
    sequential       callable() -> int : esegue l'export in-process
    parallel_worker  funzione top-level (start_index, blocco) -> risultato
    consume          callable(risultato, n_elementi) : integra un risultato nel
                     file finale; viene chiamata sempre IN ORDINE
    progress_cb      callback(elementi_fatti)
    annullato        callable() -> bool, interrogata dopo ogni blocco

    Restituisce il numero di elementi processati.
    Solleva ExportAnnullato se `annullato()` diventa vera.
    Solleva ExportTooLarge se `total` supera il limite di sicurezza.
    """
    _check_cancelled(annullato, 0, total)
    check_export_size(total)

    plan = plan_workers(total, n_workers, min_per_worker, min_chunk,
                        cost_per_item=cost_per_item)
    if plan is None:
        return sequential()
    n_workers, chunk = plan
    _log.info("%s: %d elementi, %d worker, blocchi da %d "
              "(%d blocchi, ~%.1f s di lavoro stimato per worker)",
              what, total, n_workers, chunk,
              math.ceil(total / chunk),
              chunk * (cost_per_item or 0))

    def tasks():
        start = 1
        for block in chunked(items_iter, chunk):
            yield (start, block)
            start += len(block)

    if annullato is None:
        annullato = mai_annullato

    done = 0
    consumption_started = False
    try:
        with cronometro(f"{what}: calcolo+unione blocchi"):
            for res, npieces in imap_ordered(_SizedWorker(parallel_worker),
                                             tasks(), n_workers,
                                             annullato=annullato):
                # Si controlla PRIMA di consumare: cosi' un annullamento non
                # lascia a meta' l'unione del blocco appena arrivato.
                if annullato():
                    raise ExportAnnullato(done, total)
                # Anche un consume che fallisce può avere già scritto dati.
                consumption_started = True
                consume(res, npieces)
                done += npieces
                if progress_cb:
                    progress_cb(done)
        _check_cancelled(annullato, done, total)
        return done
    except ExportAnnullato:
        _log.info("%s annullato dall'utente dopo %d elementi", what, done)
        raise
    except Exception:
        if consumption_started:
            _log.exception("%s: errore dopo l'inizio della scrittura, "
                           "nessun fallback sequenziale", what)
            raise
        # Il ripiego sul sequenziale era invisibile all'utente: su una macchina
        # a 128 core OGNI export falliva qui (ValueError sul numero di worker) e
        # si vedeva solo l'1-2% di CPU, senza alcun messaggio. Ora il motivo
        # finisce nel log come WARNING, con il numero di worker richiesto.
        _log.warning("%s: parallelo fallito con %d worker, ripiego sul "
                     "sequenziale. Dettagli qui sotto.", what, n_workers)
        _log.exception("Causa del ripiego di %s", what)
        _check_cancelled(annullato, done, total)
        return sequential()


# ─────────────────────────────────────────────────────────────────────────
# Scrittura atomica
# ─────────────────────────────────────────────────────────────────────────

@contextlib.contextmanager
def cronometro(nome, soglia_s=0.05):
    """
    Registra nel log quanto e' durata una fase dell'export.

    Serve a rispondere alla domanda «dove se ne va il tempo?» senza dover
    riprodurre il problema: le fasi (rendering, unione, scrittura,
    deduplicazione) finiscono nel log con i loro tempi, e chi segnala una
    lentezza puo' semplicemente allegare quelle righe.
    """
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dt = time.perf_counter() - t0
        if dt >= soglia_s:
            _log.info("tempi: %-28s %8.2f s", nome, dt)


@contextlib.contextmanager
def atomic_write(path, mode="wb", *, annullato=None, **kwargs):
    """
    Scrive su un file temporaneo accanto alla destinazione e lo rinomina solo
    a scrittura conclusa.

    Un export interrotto — errore, chiusura della finestra, disco pieno — non
    deve lasciare al posto del file buono un PDF o un CSV troncato, che poi
    Acrobat o Excel segnalano come corrotto. Con `os.replace` la destinazione
    o non esiste, o e' completa: non ci sono stati intermedi visibili.

    Uso:
        with atomic_write(path) as f:
            writer.write(f)
    """
    _check_cancelled(annullato)
    path = os.fspath(path)
    tmp = f"{path}.parziale"
    f = open(tmp, mode, **kwargs)
    try:
        yield f
        f.close()
        _check_cancelled(annullato)
        os.replace(tmp, path)
    except BaseException:
        try:
            f.close()
        except Exception:
            pass
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
