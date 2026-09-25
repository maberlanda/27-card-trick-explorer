"""Successione di Procedure, tabellone cumulativo e ritorno (J, riga L90).

Libro, cap. 10 § 10.1–10.2. Con N Procedure complete, di tabelloni
T(1), …, T(N), il mazzo attraversa le disposizioni v0 → v1 → … → vN con
vj = T(j)(vj−1), e l'intera successione confluisce nel tabellone cumulativo

    C_N = T(N) ∘ … ∘ T(2) ∘ T(1)          (prima agisce T(1))

Il ritorno pone due problemi distinti, e questo modulo li tiene distinti:

* **origine** — basta il cumulativo: R = C_N⁻¹ riporta vN in v0, e, poiche'
  C_N sta nel gruppo H delle 216 trasformazioni, lo realizza una sola
  Procedura (3N stadi diretti → 3 stadi di ritorno);
* **cammino** — serve la successione conservata: applicando gli inversi
  individuali dall'ultimo, vN → vN−1 → … → v0, riemergono le tappe.

C_N non conserva la storia: successioni diverse possono avere lo stesso
cumulativo. Ogni elemento conserva la Procedura I1 intera (mescolamenti e
rovesciamenti), non solo la sua T: due procedure della stessa classe restano
distinguibili.

Convenzioni (quelle del programma): ``T[carta] = posizione finale``;
``mazzo[posizione] = carta``; applicare T a un mazzo v da'
``v′[T[i]] = v[i]``; ``(a∘b)[i] = a[b[i]]``. Nessuna matematica nuova: le T
vengono dal servizio delle procedure (I1), (R) dal tabellone (I2).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional, Tuple

from . import tabellone as _tb
from .procedure import ProceduraGioco, servizio_procedure

__all__ = [
    "MAX_PROCEDURE", "SuccessioneNonValida", "Passo", "Successione",
    "applica", "componi", "inversa", "procedure_casuali", "IDENTITA",
]

N = 27
IDENTITA = tuple(range(N))
#: limite di sicurezza per una successione caricata o generata
MAX_PROCEDURE = 1000

Permutazione = Tuple[int, ...]
Mazzo = Tuple[object, ...]


class SuccessioneNonValida(ValueError):
    """Codice stabile e dati, come `ProceduraNonValida`."""

    def __init__(self, messaggio, *, codice, **dati):
        super().__init__(messaggio)
        self.codice = codice
        self.dati = dati


def componi(a, b) -> Permutazione:
    """(a ∘ b)[i] = a[b[i]]: prima agisce b."""
    return tuple(a[x] for x in b)


def inversa(p) -> Permutazione:
    q = [0] * len(p)
    for i, v in enumerate(p):
        q[v] = i
    return tuple(q)


def applica(T, mazzo) -> Mazzo:
    """La disposizione dopo T: la carta in posizione i va in posizione T[i]."""
    nuovo = [None] * N
    for i, carta in enumerate(mazzo):
        nuovo[T[i]] = carta
    return tuple(nuovo)


@dataclass(frozen=True)
class Passo:
    """Il passo j (1…N): la Procedura, la sua T, il cumulativo C_j e v_j."""
    indice: int
    procedura: ProceduraGioco
    T: Permutazione
    numero_tavola: int                  # riga della Tavola con la stessa T
    cumulativo: Permutazione            # C_j
    numero_cumulativo: int
    disposizione: Mazzo                 # v_j


@dataclass(frozen=True)
class Successione:
    """P1, …, PN (immutabile) con la disposizione iniziale v0."""
    procedure: Tuple[ProceduraGioco, ...] = ()
    mazzo_iniziale: Mazzo = IDENTITA

    def __post_init__(self):
        proc = tuple(self.procedure)
        if len(proc) > MAX_PROCEDURE:
            raise SuccessioneNonValida("successione troppo lunga",
                                       codice="troppo_lunga", lunghezza=len(proc),
                                       massimo=MAX_PROCEDURE)
        for i, p in enumerate(proc):
            if not isinstance(p, ProceduraGioco):
                raise SuccessioneNonValida("elemento non e' una Procedura",
                                           codice="procedura_non_valida", posizione=i)
        mazzo = tuple(self.mazzo_iniziale)
        if len(mazzo) != N or len(set(mazzo)) != N:
            raise SuccessioneNonValida("il mazzo iniziale deve avere 27 carte distinte",
                                       codice="mazzo_non_valido", lunghezza=len(mazzo))
        object.__setattr__(self, "procedure", proc)
        object.__setattr__(self, "mazzo_iniziale", mazzo)

    # ── modifiche: restituiscono una nuova successione ──────────────────────
    def aggiungi(self, procedura: ProceduraGioco, posizione: Optional[int] = None):
        proc = list(self.procedure)
        proc.insert(len(proc) if posizione is None else posizione, procedura)
        return Successione(tuple(proc), self.mazzo_iniziale)

    def rimuovi(self, posizione: int):
        proc = list(self.procedure)
        if not 0 <= posizione < len(proc):
            raise SuccessioneNonValida("posizione fuori dalla successione",
                                       codice="posizione_non_valida", posizione=posizione)
        del proc[posizione]
        return Successione(tuple(proc), self.mazzo_iniziale)

    def sposta(self, da: int, a: int):
        proc = list(self.procedure)
        if not (0 <= da < len(proc) and 0 <= a < len(proc)):
            raise SuccessioneNonValida("posizione fuori dalla successione",
                                       codice="posizione_non_valida", da=da, a=a)
        proc.insert(a, proc.pop(da))
        return Successione(tuple(proc), self.mazzo_iniziale)

    # ── letture ─────────────────────────────────────────────────────────────
    @property
    def lunghezza(self) -> int:
        return len(self.procedure)

    def trasformazioni(self) -> Tuple[Permutazione, ...]:
        s = servizio_procedure()
        return tuple(tuple(s.trasformazione(p)) for p in self.procedure)

    def passi(self) -> Tuple[Passo, ...]:
        passi, C, v = [], IDENTITA, self.mazzo_iniziale
        for j, (p, T) in enumerate(zip(self.procedure, self.trasformazioni()), 1):
            C = componi(T, C)                     # C_j = T(j) ∘ C_{j−1}
            v = applica(T, v)                     # v_j = T(j)(v_{j−1})
            passi.append(Passo(j, p, T, _tb.numero_di(T), C, _tb.numero_di(C), v))
        return tuple(passi)

    def cumulativo(self) -> Permutazione:
        """C_N (l'identita' per N = 0)."""
        C = IDENTITA
        for T in self.trasformazioni():
            C = componi(T, C)
        return C

    def disposizioni(self) -> Tuple[Mazzo, ...]:
        """(v0, v1, …, vN)."""
        return (self.mazzo_iniziale,) + tuple(p.disposizione for p in self.passi())

    def disposizione_finale(self) -> Mazzo:
        return applica(self.cumulativo(), self.mazzo_iniziale)

    # ── ritorno ─────────────────────────────────────────────────────────────
    def ritorno(self) -> Permutazione:
        """R = C_N⁻¹: riporta vN in v0 (l'origine, non il cammino)."""
        return inversa(self.cumulativo())

    def ritorno_procedura(self) -> ProceduraGioco:
        """Una sola Procedura (3 stadi) che realizza R: (R) di I2 applicata a C_N⁻¹."""
        return _tb.realizza(self.ritorno())

    def ritorno_compresso(self, mazzo_finale=None) -> Mazzo:
        """vN --R--> v0."""
        vN = self.disposizione_finale() if mazzo_finale is None else tuple(mazzo_finale)
        return applica(self.ritorno(), vN)

    def replay_inverso(self, mazzo_finale=None) -> Tuple[Mazzo, ...]:
        """(vN, vN−1, …, v0): gli inversi individuali, l'ultimo per primo."""
        v = self.disposizione_finale() if mazzo_finale is None else tuple(mazzo_finale)
        cammino = [v]
        for T in reversed(self.trasformazioni()):
            v = applica(inversa(T), v)
            cammino.append(v)
        return tuple(cammino)


def procedure_casuali(n: int, seed: int) -> Tuple[ProceduraGioco, ...]:
    """n procedure scelte con un generatore esplicito (mai lo stato globale)."""
    if not isinstance(n, int) or isinstance(n, bool) or not 0 <= n <= MAX_PROCEDURE:
        raise SuccessioneNonValida("numero di procedure non valido",
                                   codice="troppo_lunga", lunghezza=n, massimo=MAX_PROCEDURE)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise SuccessioneNonValida("seed non valido", codice="seed_non_valido")
    rng = random.Random(seed)
    return tuple(ProceduraGioco.da_identificatore(rng.randrange(216), rng.randrange(8))
                 for _ in range(n))
