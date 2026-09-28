"""Export CSV del dominio delle combinazioni: orchestrazione, non matematica.

Compartimento G2. Queste due funzioni stavano in `core.permutations`, e sono
la ragione per cui il grafo delle importazioni aveva un ciclo::

    core.combinations ──► core.permutations      (compute_stage, kron_label…)
    core.permutations ──► core.combinations      (l'enumeratore, dentro write_csv)

La seconda freccia non e' matematica: `permutations` costruisce **una riga**
(`make_csv_row`, `CSV_HEADER`) e non ha bisogno di sapere quante righe
esistono ne' da dove vengono. Chi lo sa e' l'orchestrazione dell'export, che
mette in fila preflight, enumerazione, costruzione delle righe, parallelismo e
pubblicazione atomica. Portandola in un modulo suo il ciclo sparisce senza
spostare un solo pezzo di matematica: `compute_stage`, `compose3`, le matrici
e il prodotto di Kronecker restano dove sono.

    core.combinations ─┐
                       ├──► core.export_combinazioni ──► core.parallel
    core.permutations ─┘

I nomi storici `permutations.write_csv` e `permutations.write_csv_parallel`
restano importabili da li' tramite una facciata differita (PEP 562): il
modulo vecchio non importa questo, lo risolve solo se qualcuno chiede quel
nome, quindi la compatibilita' non ricrea la freccia.
"""

import csv

# I due moduli si usano per nome e non «da»: `make_csv_row` e l'enumeratore
# sono i punti in cui i test infilano una sentinella o un guasto, e legare il
# nome all'import lo congelerebbe alla prima importazione.
from . import combinations, permutations

__all__ = ["write_csv", "write_csv_parallel"]


def write_csv(path, filters, progress_cb=None, annullato=None):
    """
    Scrive il CSV con separatore ; e campi tra doppi apici.

    `annullato()` viene interrogata ogni 200 righe: se vera, solleva
    ExportAnnullato e — grazie alla scrittura atomica — non lascia alcun file.

    Solleva ExportTooLarge se il numero di righe supera il limite di sicurezza
    (B11): la stessa policy di `write_csv_parallel` e delle rotte della GUI,
    applicata con lo stesso `check_export_size` e PRIMA di aprire il file o di
    avviare l'enumerazione. Con i filtri tutti liberi sarebbero 5.159.780.352
    righe, e questo percorso ci entrava dentro senza alcun preflight.
    """
    from .parallel import (ExportAnnullato, atomic_write, check_export_size,
                           mai_annullato, _check_cancelled)
    if annullato is None:
        annullato = mai_annullato
    # Preflight: nessun file aperto, nessun elemento enumerato se e' troppo.
    check_export_size(combinations.count_combinations_ex(filters))
    count = 0
    with atomic_write(path, "w", annullato=annullato,
                      newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";", quotechar='"',
                       quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow(permutations.localized_csv_header())
        for params in combinations.iter_combinations_ex(filters):
            count += 1
            w.writerow(permutations.make_csv_row(count, params))
            if progress_cb:
                progress_cb(count)
            if count % 200 == 0 and annullato():
                raise ExportAnnullato(count, 0)
        _check_cancelled(annullato, count)
    return count


# ─────────────────────────────────────────────────────────────────────────────
# CSV — versione parallela (multiprocessing)
#
# Il costo per riga è in make_csv_row -> compute_T_full (CPU-bound). I processi
# figli calcolano blocchi di righe; la scrittura su file resta ordinata nel
# processo principale. pool.map preserva l'ordine di sottomissione.
# ─────────────────────────────────────────────────────────────────────────────

def _csv_rows_chunk(task):
    """
    Worker top-level (picklable): calcola le righe CSV di un blocco.
    `task` = (start_index, blocco_di_params) — l'ordine dei due elementi
    è quello richiesto da parallel.run_export.
    """
    start_index, params_chunk = task
    return [permutations.make_csv_row(start_index + k, params)
            for k, params in enumerate(params_chunk)]


def _csv_chunk_worker(start_index, params_chunk):
    """Adattatore per run_export: (start, blocco) -> righe."""
    return _csv_rows_chunk((start_index, params_chunk))


def write_csv_parallel(path, filters, n_workers=None, progress_cb=None,
                       annullato=None):
    """
    Scrive il CSV calcolando le righe in parallelo su n_workers processi.
    La scrittura su disco resta sequenziale e ordinata.

    Le combinazioni NON vengono materializzate in una lista: `run_export`
    consuma il generatore a blocchi con una finestra limitata di task in volo.
    Con i filtri di default sarebbero 5.159.780.352 righe, e il vecchio
    `list(iter_combinations_ex(filters))` esauriva la RAM prima di scrivere
    un byte.

    Fallback automatico al sequenziale (write_csv) se: n_workers<=1, poche
    righe, o errore di multiprocessing.
    Solleva ExportTooLarge se il numero di righe supera il limite di sicurezza.
    """
    from .parallel import (COSTO_RIGA_CSV, ExportAnnullato, atomic_write,
                           check_export_size, mai_annullato, run_export,
                           _check_cancelled)
    if annullato is None:
        annullato = mai_annullato

    _check_cancelled(annullato)
    total = combinations.count_combinations_ex(filters)
    # Il controllo va fatto PRIMA di aprire il file: se l'export e' rifiutato
    # non deve restare in giro un CSV con la sola intestazione.
    check_export_size(total)

    with atomic_write(path, "w", annullato=annullato,
                      newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";", quotechar='"',
                       quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow(permutations.localized_csv_header())

        state = {"written": 0, "fallback": False}

        def consume(rows, _n):
            for row in rows:
                w.writerow(row)
                state["written"] += 1

        def sequential():
            # Il file è già aperto con l'intestazione scritta: continuiamo qui
            # invece di riaprirlo, così il fallback non perde l'header.
            _check_cancelled(annullato, 0, total)
            state["fallback"] = True
            count = 0
            for params in combinations.iter_combinations_ex(filters):
                count += 1
                w.writerow(permutations.make_csv_row(count, params))
                if progress_cb and count % 500 == 0:
                    progress_cb(count)
                if count % 200 == 0 and annullato():
                    raise ExportAnnullato(count, total)
            _check_cancelled(annullato, count, total)
            return count

        n = run_export(total=total,
                       items_iter=combinations.iter_combinations_ex(filters),
                       sequential=sequential,
                       parallel_worker=_csv_chunk_worker,
                       consume=consume,
                       n_workers=n_workers, cost_per_item=COSTO_RIGA_CSV,
                       progress_cb=progress_cb, annullato=annullato,
                       what="Export CSV")

        if progress_cb:
            progress_cb(n)
        _check_cancelled(annullato, n, total)
    return n
