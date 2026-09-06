"""
Dati di dettaglio per l'export PDF "stile-C" (elenco_disposizioni).

Per ogni combinazione calcola, oltre alle matrici gia' note:
  - la disposizione fisica del mazzo dopo ogni mescolamento (iniziale, dopo
    stadio 1, dopo stadio 2, finale), usando la stessa codifica del programma C
    ("ABCDEFGHIJKLMNOPQRSTUVWXYZ0");
  - le posizioni dei 3 marcatori (Asso picche='A' pos 0, Asso fiori='N' pos 13,
    Asso cuori='0' pos 26) con il settore ternario (s/c/d);
  - il periodo della permutazione (minimo n con T^n = I);
  - la permutazione inversa (= trasposta della matrice) e il flag involutiva.

Convenzioni (verificate contro il motore Python):
  perm[i] = posizione di destinazione della carta che parte dalla posizione i,
  quindi  disposizione_finale[perm[i]] = mazzo_iniziale[i].
"""
import numpy as np

from .permutations import compute_stage, mat_to_perm27
from .analysis import order_of

# Codifica delle 27 carte, identica al programma C.
DECK = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0"

# Marcatori: (carattere, posizione iniziale, etichetta leggibile)
MARKERS = [
    ("A", 0,  "Asso di picche"),
    ("N", 13, "Asso di fiori"),
    ("0", 26, "Asso di cuori"),
]

_SECT = {0: "s", 1: "c", 2: "d"}


def num_to_sector(n):
    """
    Posizione 0-26 -> tripla ternaria di settori 's'/'c'/'d' (come NumToSector
    del programma C). Cifra piu' significativa = colonna di raccolta.
    Esempi: 0 -> 'sss', 13 -> 'ccc', 26 -> 'ddd'.
    """
    R = ["", "", ""]
    q = n
    for ctr in range(3):
        R[2 - ctr] = _SECT[q % 3]
        q //= 3
    return "".join(R)


def disposition_from_perm(perm):
    """
    Disposizione del mazzo (stringa di 27 caratteri) data la permutazione
    perm[i] = destinazione della carta di posizione i.
    """
    L = [None] * 27
    for i, dest in enumerate(perm):
        L[dest] = DECK[i]
    return "".join(L)


def inverse_perm(perm):
    """Permutazione inversa: inv[dest] = i  tale che perm[i] = dest."""
    inv = [0] * len(perm)
    for i, d in enumerate(perm):
        inv[d] = i
    return inv


def marker_positions(perm):
    """
    Per ogni marcatore restituisce (carattere, etichetta, posizione_finale, settore).
    La carta che parte dalla posizione `start` finisce in perm[start].
    """
    out = []
    for ch, start, label in MARKERS:
        pos = perm[start]
        out.append((ch, label, pos, num_to_sector(pos)))
    return out


def combination_detail(params):
    """
    Calcola tutti i dati di dettaglio per una combinazione.

    params: lista di 3 tuple (p1,p2,p3,j1,j2,j3) (uno per stadio).

    Ritorna un dict con:
      stage_mats   : [S1, S2, S3]  matrici 27x27 di stadio
      cum_perms    : [perm dopo stadio1, dopo stadio2, finale]
      dispositions : [iniziale, dopo1, dopo2, finale]  (stringhe di carte)
      T_matrix     : matrice finale 27x27
      T_perm       : permutazione finale
      inv_perm     : permutazione inversa (= trasposta)
      period       : periodo (minimo n con T^n = I)
      involutive   : True se la matrice e' il proprio inverso (T == T^T)
      markers      : marker_positions(T_perm)
    """
    stage_mats = [compute_stage(*p)[2] for p in params]   # [2] = Stage_27

    # Permutazioni cumulative: dopo stadio1 = S1, dopo2 = S2@S1, finale = S3@S2@S1
    cum = np.eye(27)
    cum_mats = []
    for S in stage_mats:
        cum = S @ cum
        cum_mats.append(cum)

    cum_perms = [mat_to_perm27(M) for M in cum_mats]
    T_matrix = cum_mats[-1]
    T_perm = cum_perms[-1]

    dispositions = [DECK] + [disposition_from_perm(p) for p in cum_perms]

    inv = inverse_perm(T_perm)
    involutive = (T_perm == inv)

    return {
        "stage_mats":   stage_mats,
        "cum_perms":    cum_perms,
        "dispositions": dispositions,
        "T_matrix":     T_matrix,
        "T_perm":       T_perm,
        "inv_perm":     inv,
        "period":       order_of(T_perm),
        "involutive":   involutive,
        "markers":      marker_positions(T_perm),
    }
