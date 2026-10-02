"""
Ricerca vettorizzata delle decomposizioni Kronecker a tre stadi e test di
appartenenza ai gruppi H (216) e Gamma (648).

La funzione e' GENERALE: `find_all_kron_decompositions(target)` accetta un
qualunque bersaglio, cioe' una permutazione valida di 27 elementi, e trova
tutte le terne (A0, A1, A2) di elementi di H con

    A2 o MSC o A1 o MSC o A0 o MSC = target

(A0 agisce per primo: e' lo stadio h = 0, la fase 1 dell'interfaccia; A1 e'
lo stadio h = 1, fase 2; A2 lo stadio h = 2, fase 3).

Il bersaglio NON e' fissato qui. Per DEFAULT l'interfaccia (Explorer, pulsante
«🔍 Decomposizioni T⁻¹») passa T^-1, per la convenzione mazzo/trasformazione:
T[origine] = destinazione e il mazzo finale di un mazzo ordinato e' T^-1; il
dialogo delle decomposizioni permette di scegliere T al suo posto. Il
contesto (`decomposition_context`) registra sempre quale delle due (T o T^-1)
e' stata decomposta.

find_all_kron_decompositions(target_perm_27)
    -> lista di triple ((f2_0,f1_0,f0_0), (f2_1,f1_1,f0_1), (f2_2,f1_2,f0_2))
       nell'ordine degli stadi A0, A1, A2

Algoritmo vettorizzato (numpy puro, niente loop Python sul 46k):
  Per ogni A0 (216 possibilita):
    step0 = A0[MSC]                          shape (27,)
    Per ogni A1 (216):
      C = MSC[A1[MSC[step0]]]               shape (27,)
      A2_richiesta = target[argsort(C)]      shape (27,)
      lookup nel dict: e un Kronecker?

  Loop Python: 216 (outer) -- il loop su A1 e vettorizzato in batch.
  Costo reale: 216 iterazioni Python x matmul numpy 216x27.

Versione parallela:
  find_all_kron_decompositions_parallel(target, n_workers) e' un alias storico:
  delega sempre alla sequenziale, che a questi tempi e' piu' veloce.
"""
import os

import numpy as np

from .constants import PERM3, _MSC_PERM
from .dominio import valida_permutazione
from .log import get_logger

_log = get_logger(__name__)


# ------------------------------------------------------------------ table ---

def _build_kron_table():
    """
    Precalcola i 216 prodotti di Kronecker GEN3 x GEN3 x GEN3 come array 216x27.
    Restituisce (kron_arr, kron_names, kron_lookup).
      kron_arr   : np.int32 shape (216, 27)
      kron_names : list of (f2, f1, f0) strings, lunghezza 216
                   (fattori dei livelli 2, 1, 0: K = P2 ⊗ P1 ⊗ P0)
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
    for ia, f2n in enumerate(gnames):
        for ib, f1n in enumerate(gnames):
            for ic, f0n in enumerate(gnames):
                kron_arr[k] = (9 * gperms[ia][i2]
                               + 3 * gperms[ib][i1]
                               +     gperms[ic][i0])
                kron_names.append((f2n, f1n, f0n))
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


#: Decomposizioni di un bersaglio che appartiene a H: 216 scelte per A0 x 216
#: per A1, con A2 determinata. Verificato esaustivamente dalla baseline
#: matematica (`tests/test_baseline_matematica.py`).
DECOMPOSIZIONI_PER_TARGET_IN_H = 216 ** 2          # 46.656

#: Alias legacy (nome storico G = H, 216 elementi): stesso valore.
DECOMPOSIZIONI_PER_TARGET_IN_G = DECOMPOSIZIONI_PER_TARGET_IN_H


class DecomposizioniIncomplete(ValueError):
    """L'elenco e' internamente valido ma NON e' l'insieme completo atteso."""


def cardinalita_attesa(target):
    """Quante decomposizioni esistono per `target`: 46.656 se e' in H, 0 fuori.

    E' un fatto matematico, non un'euristica: si decide con `appartiene_a_H`,
    non contando i risultati gia' presenti in un elenco.
    """
    return DECOMPOSIZIONI_PER_TARGET_IN_H if appartiene_a_H(target) else 0


def validate_decompositions(target, results):
    """Valida struttura e bersaglio; restituisce triple immutabili di nomi.

    Controlla SOLO la validita' interna: ogni decomposizione presente ricostruisce
    il bersaglio. NON controlla la completezza, quindi un elenco parziale — o
    vuoto — e' legittimo qui: e' il contratto di una vista filtrata o di un
    contesto deliberatamente parziale.

    Per decidere se un elenco e' l'insieme COMPLETO (il caso della cache) si usa
    `validate_complete_decompositions`. Vedi B08.
    """
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


def validate_complete_decompositions(target, results):
    """Valida un elenco che pretende di essere COMPLETO (cache su disco).

    Oltre alla validita' interna di `validate_decompositions` pretende:

    * bersaglio che e' una permutazione valida di 27 elementi;
    * cardinalita' pari a quella matematicamente attesa per quel bersaglio
      (46.656 se il bersaglio e' in H, 0 se ne sta fuori);
    * unicita': nessuna decomposizione ripetuta.

    Solleva `DecomposizioniIncomplete` (sottoclasse di ValueError) se l'elenco e'
    internamente valido ma incompleto o con duplicati. E' quello che distingue
    «insieme parziale ma valido» da «cache completa e affidabile»: prima un
    elenco vuoto veniva accettato come risposta definitiva anche per un
    bersaglio che di decomposizioni ne ha 46.656 (B08).
    """
    checked = validate_decompositions(target, results)
    attese = cardinalita_attesa(target)
    if len(checked) != attese:
        raise DecomposizioniIncomplete(
            f"elenco incompleto: {len(checked)} decomposizioni su {attese} "
            f"attese per questo bersaglio")
    if len(set(checked)) != len(checked):
        raise DecomposizioniIncomplete(
            f"elenco con duplicati: {len(checked) - len(set(checked))} ripetizioni")
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
    Trova tutte le triple (A0, A1, A2) in (GEN3 x GEN3 x GEN3)^3
    tali che  A2 o MSC o A1 o MSC o A0 o MSC = target  (A0 agisce per primo).

    Il bersaglio e' generico: T, T^-1 o qualunque permutazione valida. Vedi la
    docstring del modulo per il default dell'interfaccia (T^-1).

    progress_cb(outer_i: int, found: int) chiamata dopo ogni iterazione esterna.

    Restituisce lista di tuple, nell'ordine degli stadi:
        ( (f2_0,f1_0,f0_0), (f2_1,f1_1,f0_1), (f2_2,f1_2,f0_2) )

    `target_perm_27` deve essere una permutazione valida di 27 elementi (R04).
    """
    target_perm_27 = valida_permutazione(target_perm_27, 27,
                                         nome="find_all_kron_decompositions")
    kron_arr, kron_names, kron_lookup = _get_kron_table()
    msc    = np.array(_MSC_PERM, dtype=np.int32)
    target = np.array(target_perm_27, dtype=np.int32)

    results = []
    seen    = set()

    for outer_i in range(216):

        A0    = kron_arr[outer_i]
        step0 = A0[msc]

        inner = kron_arr[:, msc[step0]]   # (216, 27)
        C_all = msc[inner]                # (216, 27)
        Cinv  = np.argsort(C_all, axis=1) # (216, 27)
        A2req = target[Cinv]              # (216, 27)

        for j in range(216):
            key = A2req[j].tobytes()
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

def find_all_kron_decompositions_parallel(target_perm_27,
                                          n_workers=None,
                                          progress_cb=None):
    """Nome storico della ricerca: oggi delega sempre alla sequenziale.

    La versione parallela distribuiva i 216 indici esterni su piu' processi.
    Dalle ottimizzazioni della 3.0.2 la ricerca completa costa ~0,025 s:
    avviare processi che re-importano numpy costa da dieci a cento volte
    tanto, e il parallelo risultava gia' piu' lento del sequenziale con due
    soli worker. La delega era stata messa come primo `return`, ma il corpo
    parallelo era rimasto sotto: quaranta righe irraggiungibili — pool,
    serializzazione, deduplicazione — piu' il worker `_worker_chunk` che solo
    loro usavano. Il compartimento F le ha rimosse.

    La firma resta invariata: `n_workers` viene accettato e ignorato, perche'
    i chiamanti (la scheda Decomposizioni, i test) lo passano.
    """
    if n_workers is None:
        n_workers = max(1, (os.cpu_count() or 2) - 1)
    if n_workers > 1:
        _log.debug("Ricerca decomposizioni: sequenziale (lavoro troppo breve "
                   "per giustificare il multiprocessing)")
    return find_all_kron_decompositions(target_perm_27, progress_cb=progress_cb)


# ─────────────────────────── single Kronecker decomposition ──────────────────

# Mappa inversa di PERM3: tuple-di-permutazione → nome GEN3
_GEN3_PERM_TO_NAME = {tuple(v): k for k, v in PERM3.items()}


def try_kron_decompose(perm27):
    """
    Tenta di estrarre i tre fattori Kronecker GEN3 dalla permutazione 27x27.

    Sfrutta la struttura a blocchi del prodotto di Kronecker GEN3^3:
        perm[col] = 9*f2[col//9] + 3*f1[(col%9)//3] + f0[col%3]

    Algoritmo:
      1. Legge f2[c2] = perm[9*c2] // 9            (quale blocco da 9 riceve il blocco c2)
      2. Legge f1[c1] = (perm[3*c1] % 9) // 3      (sottoblock interno, usando blocco c2=0)
      3. Legge f0[c0] = perm[c0] % 3               (cella interna, usando c2=0, c1=0)
      4. Verifica che la formula sia rispettata per tutti i 27 coloni.

    Ritorna (f2_name, f1_name, f0_name) se la permutazione e' un prodotto
    di Kronecker GEN3^3 (cioe' se appartiene a H), altrimenti None.

    `perm27` deve essere una permutazione valida di 27 elementi (R04): None
    significa "permutazione valida ma non in H", non "ingresso irriconoscibile".
    """
    p = list(valida_permutazione(perm27, 27, nome="try_kron_decompose"))

    # Estrai i tre fattori candidati
    f2 = [p[9 * c2] // 9           for c2 in range(3)]
    f1 = [(p[3 * c1] % 9) // 3     for c1 in range(3)]
    f0 = [p[c0] % 3                for c0 in range(3)]

    # Verifica che la formula sia soddisfatta per ogni colonna
    for col in range(27):
        c2, c1, c0 = col // 9, (col % 9) // 3, col % 3
        if p[col] != 9 * f2[c2] + 3 * f1[c1] + f0[c0]:
            return None     # non e' un prodotto di Kronecker GEN3^3

    # Mappa i vettori-permutazione ai nomi GEN3
    n2 = _GEN3_PERM_TO_NAME.get(tuple(f2))
    n1 = _GEN3_PERM_TO_NAME.get(tuple(f1))
    n0 = _GEN3_PERM_TO_NAME.get(tuple(f0))

    if n2 is None or n1 is None or n0 is None:
        return None

    return n2, n1, n0


# ──────────────────────────── appartenenza a H e Γ ───────────────────────────
#
# Nomenclatura del libro (DP2, Fase P):
#
# H = GEN3^3 ≅ S3^3         i 216 prodotti di Kronecker di tre permutazioni di
#                           S3: le trasformazioni complete (separabili)
# Γ = Γ_{3,3} = <H, MSC>    i 648 elementi h o MSC^r, r in {0,1,2}: il gruppo
#                           delle trasformazioni complete e intermedie,
#                           Γ = H ⊔ H∘MSC ⊔ H∘MSC²
#
# Sono insiemi propri di S27 (27! elementi): nessuna proprieta' di H o di Γ vale
# "per tutte le permutazioni di 27 elementi". Queste funzioni rendono esplicito
# un test di appartenenza che altrimenti resterebbe implicito nel codice
# chiamante.
#
# Migrazione dei nomi (compatibile):
#   appartiene_a_H      -> H, 216 elementi (nome canonico)
#   appartiene_a_Gamma  -> Γ, 648 elementi (nome canonico)
#   appartiene_a_G      -> alias legacy di appartiene_a_H (nome storico G = H,
#                          capitolo 6 del libro); resta per compatibilita'.
# Fino alla 4.0.0 RC2 `appartiene_a_H` indicava il gruppo di 648: chi lo usava
# in quel senso deve passare a `appartiene_a_Gamma`.

def appartiene_a_H(perm27):
    """True se `perm27` e' un prodotto di Kronecker GEN3^3, cioe' sta in H (|H| = 216)."""
    return try_kron_decompose(perm27) is not None


#: Alias legacy: nel core il gruppo di 216 si chiamava G. Stessa funzione di
#: `appartiene_a_H`; i nuovi chiamanti usino il nome canonico.
appartiene_a_G = appartiene_a_H


def appartiene_a_Gamma(perm27):
    """True se `perm27` e' della forma K o MSC^k con K in H, cioe' sta in Γ (|Γ| = 648).

    Equivale a: esiste k in {0,1,2} tale che perm o MSC^(-k) appartenga a H.
    """
    perm = valida_permutazione(perm27, 27, nome="appartiene_a_Gamma")
    msc_k = tuple(range(27))
    for _ in range(3):
        # perm o (MSC^k)^-1 : si toglie la potenza di MSC e si guarda se resta in H
        inversa = [0] * 27
        for posizione, valore in enumerate(msc_k):
            inversa[valore] = posizione
        candidata = [perm[inversa[i]] for i in range(27)]
        if try_kron_decompose(candidata) is not None:
            return True
        msc_k = tuple(_MSC_PERM[x] for x in msc_k)
    return False
