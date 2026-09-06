"""
Analisi matematica del gruppo: cicli, ordine, orbite, distribuzione.
"""
import numpy as np
from .constants import PERM3, _MSC_PERM
from .log import get_logger

_log = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────
# Analisi ciclica
# ─────────────────────────────────────────────────────────────────

def cycle_decomposition(perm):
    """
    Restituisce la decomposizione in cicli disgiunti di una permutazione.

    Parameters
    ----------
    perm : array-like of int, length 27
        perm[i] = posizione in cui va la carta i

    Returns
    -------
    list of list of int
        Ogni sotto-lista è un ciclo; i punti fissi (cicli di lunghezza 1)
        sono inclusi.  I cicli sono ordinati per elemento minimo.
    """
    perm = list(perm)
    n = len(perm)
    visited = [False] * n
    cycles = []
    for start in range(n):
        if visited[start]:
            continue
        cycle = []
        cur = start
        while not visited[cur]:
            visited[cur] = True
            cycle.append(cur)
            cur = perm[cur]
        cycles.append(cycle)
    cycles.sort(key=lambda c: c[0])
    return cycles


def order_of(perm):
    """
    Ordine di una permutazione nel gruppo S_27:
    minimo n > 0 tale che perm^n = identità.
    Equivalente a mcm delle lunghezze dei cicli.
    """
    from math import gcd
    cycles = cycle_decomposition(perm)
    result = 1
    for c in cycles:
        l = len(c)
        result = result * l // gcd(result, l)
    return result


def orbit_of(perm, card):
    """
    Sequenza di posizioni percorse dalla carta `card` sotto iterazione di perm.
    Termina quando si ritorna al punto di partenza.
    """
    perm = list(perm)
    orbit = [card]
    cur = perm[card]
    while cur != card:
        orbit.append(cur)
        cur = perm[cur]
    return orbit


def cycle_type(perm):
    """
    Tipo di ciclo: dizionario {lunghezza: conteggio}.
    Es. {1: 3, 2: 6, 3: 6} per una permutazione in S_27.
    """
    from collections import Counter
    cycles = cycle_decomposition(perm)
    return dict(Counter(len(c) for c in cycles))


# ─────────────────────────────────────────────────────────────────
# Distribuzione globale
# ─────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────
# Distribuzione globale delle decomposizioni
#
# NOTA STORICA — codice rimosso in questa revisione
# -------------------------------------------------
# Qui vivevano `_all_reachable_T()` e `compute_distribution()`. Nessuna delle
# due era chiamata da alcun punto del programma (la GUI usa da sempre
# `compute_distribution_parallel`), ed entrambe contenevano un triplo ciclo
# Python su 216³ = 10.077.696 iterazioni con indicizzazione numpy elemento per
# elemento: ore di calcolo per un risultato che si ottiene in un decimo di
# secondo (vedi sotto). Sono state eliminate invece di essere ottimizzate,
# perche' erano semplicemente morte.
#
# STRUTTURA DEL PROBLEMA
# ----------------------
# Cerchiamo, per ogni T raggiungibile, quante terne (A0, A1, A2) di prodotti
# di Kronecker GEN3³ soddisfano
#
#     T = A2 ∘ MSC ∘ A1 ∘ MSC ∘ A0 ∘ MSC.
#
# La relazione di trasporto MSC ∘ K = rot₂(K) ∘ MSC permette di spostare tutti
# gli MSC a destra:
#
#     A2 ∘ MSC ∘ A1 ∘ MSC ∘ A0 ∘ MSC
#       = A2 ∘ rot₂(A1) ∘ MSC² ∘ A0 ∘ MSC
#       = A2 ∘ rot₂(A1) ∘ rot₁(A0) ∘ MSC³
#       = A2 ∘ rot₂(A1) ∘ rot₁(A0)                (MSC³ = I)
#
# quindi ogni T raggiungibile e' esso stesso un prodotto di Kronecker: i T
# distinti sono esattamente 216, non 10 milioni. E poiche' per (A1, A2) fissati
# la mappa A3 ↦ A3 ∘ C e' una biiezione del gruppo, ciascuno dei 216 T riceve
# esattamente un contributo da ogni coppia (A1, A2): 216² = 46.656
# decomposizioni a testa, per un totale di 216³.
#
# Il calcolo qui sotto NON assume questo risultato: verifica per tutte le
# 46.656 coppie (A1, A2) che C = MSC∘A2∘MSC∘A1∘MSC sia davvero un Kronecker
# (se non lo fosse, `_KronNotFound` verrebbe sollevata) e conta con la tabella
# di Cayley. Costa 46.656 iterazioni invece di 10.077.696: stesso risultato,
# ~200x piu' veloce, e verifica un'affermazione in piu'.
# ─────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────
# Distribuzione — versione parallela (multiprocessing)
#
# Il calcolo itera sui 216 indici esterni A1, indipendenti tra loro:
# si distribuiscono sui core con ProcessPoolExecutor. In Python il GIL
# impedisce ai thread di accelerare codice CPU-bound, quindi qui serve
# il multiprocessing (un processo per core), non il multithreading.
# ─────────────────────────────────────────────────────────────────
import os as _os
from concurrent.futures import ProcessPoolExecutor, as_completed


class _KronNotFound(RuntimeError):
    """
    C = MSC∘A2∘MSC∘A1∘MSC non risulta un prodotto di Kronecker.

    Non deve mai accadere: significherebbe che la relazione di trasporto
    MSC ∘ K = rot₂(K) ∘ MSC e' violata, cioe' che MSC_PERM non e' piu'
    coerente con la codifica ternaria degli indici. E' un allarme, non un
    caso da gestire.
    """


def _build_kron_table_27():
    """Array (216, 27) dei prodotti di Kronecker GEN3⊗GEN3⊗GEN3 + permutazione MSC."""
    msc = np.array(_MSC_PERM, dtype=np.int32)
    gperms = [np.array(PERM3[n], dtype=np.int32) for n in PERM3]
    idx = np.arange(27, dtype=np.int32)
    i2 = idx // 9
    i1 = (idx % 9) // 3
    i0 = idx % 3
    K = np.empty((216, 27), dtype=np.int32)
    k = 0
    for a in gperms:
        for b in gperms:
            for c in gperms:
                K[k] = 9 * a[i2] + 3 * b[i1] + c[i0]
                k += 1
    return K, msc


def _build_cayley216(K):
    """
    Tabella di Cayley del gruppo dei 216 Kronecker: cayley[a, b] = indice di
    K[a] ∘ K[b]. Costruita una volta per processo (46.656 lookup, ~50 ms).
    """
    lookup = {K[i].tobytes(): i for i in range(216)}
    cayley = np.empty((216, 216), dtype=np.int32)
    for a in range(216):
        rows = K[a][K]                    # (216, 27): K[a] ∘ K[b] per ogni b
        for b in range(216):
            cayley[a, b] = lookup[rows[b].tobytes()]
    return cayley, lookup


#: cache per-processo di (K, msc, cayley, lookup)
_G216 = None


def _get_g216():
    global _G216
    if _G216 is None:
        K, msc = _build_kron_table_27()
        cayley, lookup = _build_cayley216(K)
        _G216 = (K, msc, cayley, lookup)
    return _G216


def _distribution_partial(outer_indices):
    """
    Worker top-level (picklable) per ProcessPoolExecutor.
    Conta le decomposizioni Kronecker per gli indici A1 in `outer_indices`.
    Ritorna dict {bytes(T): count}.

    Per ogni coppia (A1, A2):
      1. calcola C = MSC ∘ A2 ∘ MSC ∘ A1 ∘ MSC;
      2. VERIFICA che C sia un prodotto di Kronecker e ne prende l'indice c
         (se non lo fosse, la relazione di trasporto sarebbe rotta);
      3. i 216 A3 danno i T di indice cayley[:, c] — un colpo vettorizzato
         invece di 216 indicizzazioni numpy separate.

    Costo: 46.656 iterazioni invece di 216³ = 10.077.696.
    """
    K, msc, cayley, lookup = _get_g216()

    counts = np.zeros(216, dtype=np.int64)
    for outer_i in outer_indices:
        step1 = K[outer_i][msc]
        C_all = msc[K[:, msc[step1]]]      # (216,27): C per ogni A2
        for j in range(216):
            key = C_all[j].tobytes()
            c = lookup.get(key)
            if c is None:
                raise _KronNotFound(
                    "C = MSC∘A2∘MSC∘A1∘MSC non e' un Kronecker "
                    f"(A1={outer_i}, A2={j}): relazione di trasporto violata")
            counts += np.bincount(cayley[:, c], minlength=216)

    return {K[t].tobytes(): int(counts[t])
            for t in range(216) if counts[t]}


def _finalize_distribution(count_map):
    from collections import Counter
    counts = list(count_map.values())
    return {
        "count_map"   : count_map,
        "histogram"   : dict(Counter(count_map.values())),
        "total_T"     : len(count_map),
        "total_decomp": sum(counts),
        "max_count"   : max(counts) if counts else 0,
        "min_count"   : min(counts) if counts else 0,
    }


def compute_distribution_parallel(n_workers=None, progress_cb=None):
    """
    Distribuzione delle decomposizioni, parallelizzata sui 216 indici esterni A1.

    n_workers=None  -> tutti i core logici meno uno
    n_workers<=1    -> esecuzione sequenziale (con progressi a batch)
    Fallback automatico al sequenziale se il multiprocessing fallisce.

    progress_cb(completati:int, totale:int=216)
    """
    if n_workers is None:
        n_workers = max(1, (_os.cpu_count() or 2) - 1)

    # Il calcolo completo costa ~0,09 s da quando il conteggio usa la tabella
    # di Cayley invece di iterare su 216³ terne: distribuirlo su N processi che
    # re-importano numpy costerebbe piu' del calcolo stesso. Si resta in-process
    # a meno che il chiamante non chieda esplicitamente il contrario.
    if n_workers > 1 and not _os.environ.get("GIOCO27_FORZA_DISTRIB_PARALLELA"):
        _log.debug("Distribuzione: sequenziale (lavoro troppo breve per il "
                   "multiprocessing)")
        n_workers = 1

    # ---- Sequenziale (anche fallback) ----
    if n_workers <= 1:
        cm = {}
        batch = 8
        for start in range(0, 216, batch):
            idxs = list(range(start, min(start + batch, 216)))
            for k, v in _distribution_partial(idxs).items():
                cm[k] = cm.get(k, 0) + v
            if progress_cb:
                progress_cb(min(start + batch, 216), 216)
        return _finalize_distribution(cm)

    # ---- Parallelo ----
    from .parallel import default_workers
    n_workers = default_workers(n_workers)      # tetto di piattaforma
    chunks = [list(range(i, 216, n_workers)) for i in range(n_workers)]
    chunks = [c for c in chunks if c]
    merged = {}
    completed = 0
    try:
        with ProcessPoolExecutor(max_workers=n_workers) as pool:
            futs = {pool.submit(_distribution_partial, c): len(c) for c in chunks}
            for fut in as_completed(futs):
                for k, v in fut.result().items():
                    merged[k] = merged.get(k, 0) + v
                completed += futs[fut]
                if progress_cb:
                    progress_cb(completed, 216)
        return _finalize_distribution(merged)
    except Exception:
        _log.exception("Distribuzione parallela fallita: fallback sequenziale")
        return compute_distribution_parallel(n_workers=1, progress_cb=progress_cb)
