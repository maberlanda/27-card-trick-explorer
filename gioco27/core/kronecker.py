"""
Ricerca vettorizzata di tutte le decomposizioni Kronecker di T^-1.

find_all_kron_decompositions(target_perm_27)
    -> lista di triple ((f3_1,f2_1,f1_1), (f3_2,f2_2,f1_2), (f3_3,f2_3,f1_3))

Algoritmo vettorizzato (numpy puro, niente loop Python sul 46k):
  Per ogni A1 (216 possibilita):
    step1 = A1[MSC]                          shape (27,)
    Per ogni A2 (216):
      C = MSC[A2[MSC[step1]]]               shape (27,)
      A3_required = target[argsort(C)]       shape (27,)
      lookup nel dict: e un Kronecker?

  Loop Python: 216 (outer) -- il loop su A2 e vettorizzato in batch.
  Costo reale: 216 iterazioni Python x matmul numpy 216x27.

Versione parallela:
  find_all_kron_decompositions_parallel(target, n_workers)
  usa ProcessPoolExecutor con worker top-level _worker_chunk.
"""
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

from .constants import PERM3, _MSC_PERM
from .log import get_logger

_log = get_logger(__name__)


# ------------------------------------------------------------------ table ---

def _build_kron_table():
    """
    Precalcola i 216 prodotti di Kronecker GEN3 x GEN3 x GEN3 come array 216x27.
    Restituisce (kron_arr, kron_names, kron_lookup).
      kron_arr   : np.int32 shape (216, 27)
      kron_names : list of (f3, f2, f1) strings, lunghezza 216
      kron_lookup: dict {bytes(row): index}
    """
    gnames = list(PERM3.keys())
    gperms = [np.array(PERM3[n], dtype=np.int32) for n in gnames]

    idx = np.arange(27, dtype=np.int32)
    i2  = idx // 9
    i1  = (idx % 9) // 3
    i0  = idx % 3

    kron_arr   = np.empty((216, 27), dtype=np.int32)
    kron_names = []
    k = 0
    for ia, f3n in enumerate(gnames):
        for ib, f2n in enumerate(gnames):
            for ic, f1n in enumerate(gnames):
                kron_arr[k] = (9 * gperms[ia][i2]
                               + 3 * gperms[ib][i1]
                               +     gperms[ic][i0])
                kron_names.append((f3n, f2n, f1n))
                k += 1

    kron_lookup = {kron_arr[i].tobytes(): i for i in range(216)}
    return kron_arr, kron_names, kron_lookup


# Cache modulo-level (costruita una sola volta)
_KRON_ARR    = None
_KRON_NAMES  = None
_KRON_LOOKUP = None


def _get_kron_table():
    global _KRON_ARR, _KRON_NAMES, _KRON_LOOKUP
    if _KRON_ARR is None:
        _KRON_ARR, _KRON_NAMES, _KRON_LOOKUP = _build_kron_table()
    return _KRON_ARR, _KRON_NAMES, _KRON_LOOKUP


def decomposition_perm(decomposition):
    """Valuta tre stadi GEN3: A2 o MSC o A1 o MSC o A0 o MSC."""
    if not isinstance(decomposition, (list, tuple)) or len(decomposition) != 3:
        raise ValueError("Una decomposizione richiede tre stadi")
    stages = []
    for stage in decomposition:
        if (not isinstance(stage, (list, tuple)) or len(stage) != 3
                or any(not isinstance(name, str) or name not in PERM3
                       for name in stage)):
            raise ValueError("Ogni stadio richiede tre nomi GEN3 validi")
        stages.append(tuple(stage))
    arr, names, _ = _get_kron_table()
    msc = np.asarray(_MSC_PERM, dtype=np.int32)
    perm = np.arange(27, dtype=np.int32)
    for stage in stages:
        perm = arr[names.index(stage)][msc[perm]]
    return perm.tolist()


def validate_decompositions(target, results):
    """Valida struttura e bersaglio; restituisce triple immutabili di nomi."""
    target = tuple(target)
    if len(target) != 27 or sorted(target) != list(range(27)):
        raise ValueError("Bersaglio non valido")
    if not isinstance(results, (list, tuple)):
        raise ValueError("Elenco decomposizioni non valido")
    checked = []
    for decomposition in results:
        if tuple(decomposition_perm(decomposition)) != target:
            raise ValueError("Decomposizione incompatibile con il bersaglio")
        checked.append(tuple(tuple(stage) for stage in decomposition))
    return checked


def decomposition_context(data, perm, inverse_perm):
    """Associa risultati verificati a T/T^-1; scarta dati incoerenti.

    Accetta anche le vecchie liste, inferendone il bersaglio numericamente.
    """
    if not data:
        return None
    try:
        if isinstance(data, dict):
            target = tuple(data["target"])
            results = data["results"]
            inverse = data["inverse"]
            if not isinstance(inverse, bool):
                return None
            if target != tuple(inverse_perm if inverse else perm):
                return None
        else:
            results = data
            target = tuple(decomposition_perm(results[0]))
            if target == tuple(perm):
                inverse = False
            elif target == tuple(inverse_perm):
                inverse = True
            else:
                return None
        checked = validate_decompositions(target, results)
        return {"target": target, "inverse": inverse, "results": checked}
    except (ValueError, TypeError, KeyError, IndexError):
        return None


# -------------------------------------------------------- sequential search --

def find_all_kron_decompositions(target_perm_27, progress_cb=None):
    """
    Trova tutte le triple (A1, A2, A3) in (GEN3 x GEN3 x GEN3)^3
    tali che  A3 o MSC o A2 o MSC o A1 o MSC = target.

    progress_cb(outer_i: int, found: int) chiamata dopo ogni iterazione esterna.

    Restituisce lista di tuple:
        ( (f3_1,f2_1,f1_1), (f3_2,f2_2,f1_2), (f3_3,f2_3,f1_3) )
    """
    kron_arr, kron_names, kron_lookup = _get_kron_table()
    msc    = np.array(_MSC_PERM, dtype=np.int32)
    target = np.array(target_perm_27, dtype=np.int32)

    results = []
    seen    = set()

    for outer_i in range(216):

        A1    = kron_arr[outer_i]
        step1 = A1[msc]

        inner = kron_arr[:, msc[step1]]   # (216, 27)
        C_all = msc[inner]                # (216, 27)
        Cinv  = np.argsort(C_all, axis=1) # (216, 27)
        A3req = target[Cinv]              # (216, 27)

        for j in range(216):
            key = A3req[j].tobytes()
            if key in kron_lookup:
                triple = (kron_names[outer_i],
                          kron_names[j],
                          kron_names[kron_lookup[key]])
                if triple not in seen:
                    seen.add(triple)
                    results.append(triple)

        if progress_cb is not None:
            progress_cb(outer_i, len(results))

    return results


# --------------------------------------------------------- parallel search ---

def _worker_chunk(outer_indices, target_bytes, kron_arr_bytes, kron_names, msc_bytes):
    """
    Worker top-level per ProcessPoolExecutor.
    Riceve dati come bytes per evitare problemi di serializzazione numpy.
    """
    import numpy as np
    target   = np.frombuffer(target_bytes,   dtype=np.int32).copy()
    kron_arr = np.frombuffer(kron_arr_bytes, dtype=np.int32).reshape(216, 27).copy()
    msc      = np.frombuffer(msc_bytes,      dtype=np.int32).copy()

    kron_lookup = {kron_arr[i].tobytes(): i for i in range(216)}

    results = []
    for outer_i in outer_indices:
        A1    = kron_arr[outer_i]
        step1 = A1[msc]
        inner = kron_arr[:, msc[step1]]
        C_all = msc[inner]
        Cinv  = np.argsort(C_all, axis=1)
        A3req = target[Cinv]
        for j in range(216):
            key = A3req[j].tobytes()
            if key in kron_lookup:
                results.append((kron_names[outer_i],
                                kron_names[j],
                                kron_names[kron_lookup[key]]))
    return results


def find_all_kron_decompositions_parallel(target_perm_27,
                                          n_workers=None,
                                          progress_cb=None):
    """
    Versione parallela della ricerca Kronecker.
    Distribuisce i 216 indici outer su n_workers processi.

    n_workers=None -> tutti i core logici meno uno
    Fallback automatico a sequenziale se n_workers==1 o spawn fallisce.

    progress_cb(completed_outer: int, found: int)
    """
    if n_workers is None:
        n_workers = max(1, (os.cpu_count() or 2) - 1)
    if n_workers <= 1:
        return find_all_kron_decompositions(target_perm_27, progress_cb=progress_cb)

    # La ricerca completa costa ~0,025 s: avviare dei processi che
    # re-importano numpy costerebbe da dieci a cento volte tanto. Misurato:
    # il parallelo e' gia' piu' lento del sequenziale con due soli worker.
    # (Prima delle ottimizzazioni della 3.0.2 questa ricerca durava secondi e
    # il parallelo aveva senso; ora non piu'.)
    _log.debug("Ricerca decomposizioni: sequenziale (lavoro troppo breve "
               "per giustificare il multiprocessing)")
    return find_all_kron_decompositions(target_perm_27, progress_cb=progress_cb)

    kron_arr, kron_names, kron_lookup = _get_kron_table()
    msc    = np.array(_MSC_PERM, dtype=np.int32)
    target = np.array(target_perm_27, dtype=np.int32)

    # Serializza come bytes per IPC
    target_bytes   = target.tobytes()
    kron_arr_bytes = kron_arr.tobytes()
    msc_bytes      = msc.tobytes()

    # Distribuisce gli indici in n_workers chunk (round-robin per bilanciare)
    chunks = [list(range(i, 216, n_workers)) for i in range(n_workers)]
    chunks = [c for c in chunks if c]   # rimuovi chunk vuoti

    results   = []
    completed = 0

    try:
        with ProcessPoolExecutor(max_workers=n_workers) as pool:
            future_to_size = {
                pool.submit(_worker_chunk, chunk,
                            target_bytes, kron_arr_bytes, kron_names, msc_bytes): len(chunk)
                for chunk in chunks
            }
            for future in as_completed(future_to_size):
                chunk_results = future.result()
                results.extend(chunk_results)
                completed += future_to_size[future]
                if progress_cb is not None:
                    progress_cb(completed, len(results))
    except Exception:
        # Fallback sequenziale in caso di errore multiprocessing
        _log.exception("Ricerca decomposizioni parallela fallita: fallback sequenziale")
        return find_all_kron_decompositions(target_perm_27, progress_cb=progress_cb)

    # Deduplicazione (improbabile ma sicura)
    seen    = set()
    deduped = []
    for t in results:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


# ─────────────────────────── single Kronecker decomposition ──────────────────

# Mappa inversa di PERM3: tuple-di-permutazione → nome GEN3
_GEN3_PERM_TO_NAME = {tuple(v): k for k, v in PERM3.items()}


def try_kron_decompose(perm27):
    """
    Tenta di estrarre i tre fattori Kronecker GEN3 dalla permutazione 27x27.

    Sfrutta la struttura a blocchi del prodotto di Kronecker GEN3^3:
        perm[col] = 9*f3[col//9] + 3*f2[(col%9)//3] + f1[col%3]

    Algoritmo:
      1. Legge f3[c3] = perm[9*c3] // 9            (quale blocco da 9 riceve il blocco c3)
      2. Legge f2[c2] = (perm[3*c2] % 9) // 3      (sottoblock interno, usando blocco c3=0)
      3. Legge f1[c1] = perm[c1] % 3               (cella interna, usando c3=0, c2=0)
      4. Verifica che la formula sia rispettata per tutti i 27 coloni.

    Ritorna (f3_name, f2_name, f1_name) se la permutazione e' un prodotto
    di Kronecker GEN3^3, altrimenti None.
    """
    p = list(perm27)

    # Estrai i tre fattori candidati
    f3 = [p[9 * c3] // 9           for c3 in range(3)]
    f2 = [(p[3 * c2] % 9) // 3     for c2 in range(3)]
    f1 = [p[c1] % 3                for c1 in range(3)]

    # Verifica che la formula sia soddisfatta per ogni colonna
    for col in range(27):
        c3, c2, c1 = col // 9, (col % 9) // 3, col % 3
        if p[col] != 9 * f3[c3] + 3 * f2[c2] + f1[c1]:
            return None     # non e' un prodotto di Kronecker GEN3^3

    # Mappa i vettori-permutazione ai nomi GEN3
    n3 = _GEN3_PERM_TO_NAME.get(tuple(f3))
    n2 = _GEN3_PERM_TO_NAME.get(tuple(f2))
    n1 = _GEN3_PERM_TO_NAME.get(tuple(f1))

    if n3 is None or n2 is None or n1 is None:
        return None

    return n3, n2, n1
