"""Laboratorio matematico (compartimento I6).

Un catalogo CHIUSO di proprieta' del gioco, ognuna con il suo dominio, la
sua fonte e una verifica: esaustiva dove il dominio e' finito e piccolo,
per teorema citato o controesempio esplicito dove non lo e' (S27 non si
enumera: 27! elementi). Niente Tk, niente testo: codici stabili e dati
immutabili; le parole stanno nell'i18n della GUI.

Notazione (DP2, decisa prima di I6)
-----------------------------------

* **H** = il gruppo delle 216 trasformazioni separabili (§ 6, § 11.7, App. B);
* **Γ** = il gruppo esteso di 648 elementi, Γ = H ⊔ H∘MSC ⊔ H∘MSC² (Teor. 11.68);
* **S27** = il gruppo ambiente di tutte le permutazioni delle 27 posizioni.

Nel codice legacy il gruppo di 216 si chiama ancora ``G``
(`core.group_theory`, capitolo 6 del libro) e altrove ``H`` indica 648:
questo modulo legge quei dati solo tramite l'adattatore `_Adattatore` e non
rinomina nulla (la migrazione dei nomi e' K0). ``R`` e' la permutazione MSC
del core (`AlgebraEngine.MSC_PERM`), come nella forma canonica K ∘ MSC^k e
in `riconoscimento.classe_estesa` (I5), che qui viene riusata.

Convenzioni: ``T[carta] = posizione finale``; ``(a∘b)[x] = a[b[x]]`` (prima
b); cifre ``gioco_reale.digits3`` = (n2, n1, n0); il fattore del livello i
e' il mescolamento M_i. L'ordine dichiarato per i controesempi e' quello
lessicografico sulla lista T (per le coppie, sulla coppia; per le carte,
sulla quaterna (c1, c2, t1, t2)): il controesempio restituito e' il minimo.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from itertools import islice, permutations, product
from typing import Callable, Dict, Optional, Tuple

import numpy as np

from ..core import gioco_reale as _gr
from ..core.algebra import AlgebraEngine as _AE
from ..core.group_theory import get_group_data as _legacy_gruppo_216
from . import riconoscimento as _rc
from .procedure import ProceduraGioco, servizio_procedure

__all__ = [
    "Dominio", "Metodo", "Esito", "Controesempio", "Verifica", "Proprieta",
    "DominioNonPrevisto", "ProprietaSconosciuta", "CATALOGO",
    "ORDINE_TAVOLA_LOCALE", "TAVOLA_LOCALE_FONTE", "CARDINALITA",
    "proprieta", "verifica", "elementi", "etichetta", "Etichetta",
    "ClasseH", "TipoCiclico", "classi_h", "fusione_in_s27", "Centro", "centro",
    "SchedaJ", "scheda_j", "RigaStadio", "stadi", "ClasseLaterale",
    "classi_laterali", "TavolaLocale", "tavola_locale", "decomposizioni_locali",
    "transizione_locale", "Grafo", "grafi", "grafo", "cammino",
    "tipo_ciclico", "ordine", "punti_fissi", "segno",
]

N = 27
ID = tuple(range(N))
Permutazione = Tuple[int, ...]


# ══════════════════════════════ enumerazioni ═════════════════════════════════

class Dominio(Enum):
    """Dove una proprieta' viene enunciata e verificata."""
    S3 = "s3"                  # i 6 mescolamenti locali (tavola 6×6, § 8.2)
    H = "h"                    # 216 trasformazioni separabili
    GAMMA = "gamma"            # 648 elementi del gruppo esteso
    S27 = "s27"                # gruppo ambiente, 27!
    PROCEDURE = "procedure"    # 1728 procedure / configurazioni di stadio


class Metodo(Enum):
    ESAUSTIVO = "esaustivo"            # tutti i casi del dominio finito
    TEOREMA_FONTE = "teorema_fonte"    # teorema citato, nessuna enumerazione
    CONTROESEMPIO = "controesempio"    # primo caso falso nell'ordine dichiarato
    ESPLORAZIONE = "esplorazione"      # campione iniziale: NON e' una prova


class Esito(Enum):
    VERA = "vera"
    FALSA = "falsa"
    NON_DECISA = "non_decisa"          # solo per ESPLORAZIONE


CARDINALITA = {Dominio.S3: 6, Dominio.H: 216, Dominio.GAMMA: 648,
               Dominio.PROCEDURE: 1728, Dominio.S27: None}   # 27! non enumerato


class DominioNonPrevisto(ValueError):
    """La proprieta' non e' enunciata su quel dominio (nessuna estensione tacita)."""


class ProprietaSconosciuta(KeyError):
    pass


@dataclass(frozen=True)
class Controesempio:
    """Un caso falso, minimo nell'ordine lessicografico dichiarato."""
    codice: str                                  # forma del caso (i18n)
    elementi: Tuple[Permutazione, ...] = ()      # uno o due elementi del dominio
    dati: Tuple[Tuple[str, object], ...] = ()    # valori da mostrare

    def dato(self, chiave):
        return dict(self.dati)[chiave]


@dataclass(frozen=True)
class Verifica:
    proprieta: str
    dominio: Dominio
    esito: Esito
    metodo: Metodo
    controllati: int                 # casi effettivamente esaminati
    totale: Optional[int]            # casi del dominio (None: S27, non enumerato)
    controesempio: Optional[Controesempio] = None
    fonte: str = ""                  # per TEOREMA_FONTE: il teorema citato

    @property
    def vera(self) -> bool:
        return self.esito is Esito.VERA


@dataclass(frozen=True)
class Proprieta:
    id: str
    fonte: str                                   # riferimento al libro/articolo
    domini: Tuple[Dominio, ...]
    _verifiche: Tuple[Tuple[Dominio, Callable[[], Verifica]], ...]
    note: Tuple[Tuple[Dominio, str], ...] = ()   # codici di nota per dominio

    def verifica(self, dominio: Dominio) -> Verifica:
        for d, f in self._verifiche:
            if d is dominio:
                return f()
        raise DominioNonPrevisto(f"{self.id}: {dominio.value}")

    def nota(self, dominio: Dominio) -> Optional[str]:
        return dict(self.note).get(dominio)


# ═════════════════════════════ permutazioni ══════════════════════════════════

def _comp(a, b) -> Permutazione:
    return tuple(a[x] for x in b)


def _inv(p) -> Permutazione:
    q = [0] * len(p)
    for i, v in enumerate(p):
        q[v] = i
    return tuple(q)


def tipo_ciclico(p) -> Tuple[Tuple[int, int], ...]:
    """((lunghezza, quanti cicli), ...) in ordine di lunghezza."""
    visti, c = [False] * len(p), Counter()
    for i in range(len(p)):
        if not visti[i]:
            j, l = i, 0
            while not visti[j]:
                visti[j], j, l = True, p[j], l + 1
            c[l] += 1
    return tuple(sorted(c.items()))


def ordine(p) -> int:
    from math import gcd
    o = 1
    for l, _ in tipo_ciclico(p):
        o = o * l // gcd(o, l)
    return o


def punti_fissi(p) -> Tuple[int, ...]:
    return tuple(i for i, v in enumerate(p) if i == v)


def segno(p) -> int:
    return -1 if sum(c * (l - 1) for l, c in tipo_ciclico(p)) % 2 else 1


def _msc(k: int) -> Permutazione:
    m = ID
    for _ in range(k % 3):
        m = _comp(_AE.MSC_PERM, m)
    return m


# ═══════════════════════════════ i domini ════════════════════════════════════

ORDINE_TAVOLA_LOCALE = ("SCD", "SDC", "CSD", "CDS", "DSC", "DCS")    # § 8.2


@lru_cache(maxsize=None)
def _h() -> Tuple[Permutazione, ...]:
    """H per numero di Tavola: l'elemento n e' la riga n."""
    return tuple(tuple(_gr.riga_tavola(n)["T"]) for n in range(216))


@lru_cache(maxsize=None)
def _gamma() -> Tuple[Permutazione, ...]:
    """Γ in forma normale h ∘ R^r (Teor. 11.68): indice r·216 + n."""
    return tuple(_comp(h, _msc(r)) for r in range(3) for h in _h())


@lru_cache(maxsize=None)
def _s3() -> Tuple[Tuple[int, int, int], ...]:
    return tuple(tuple(_gr.MESCOLAMENTO[s]) for s in ORDINE_TAVOLA_LOCALE)


def elementi(dominio: Dominio):
    """Gli elementi di un dominio finito, nell'ordine del programma."""
    if dominio is Dominio.S3:
        return _s3()
    if dominio is Dominio.H:
        return _h()
    if dominio is Dominio.GAMMA:
        return _gamma()
    if dominio is Dominio.PROCEDURE:
        return tuple(ProceduraGioco.da_identificatore(n, m)
                     for n in range(216) for m in range(8))
    raise DominioNonPrevisto("S27 non si enumera (27!)")


@lru_cache(maxsize=None)
def _indice_h() -> Dict[Permutazione, int]:
    return {p: n for n, p in enumerate(_h())}


@dataclass(frozen=True)
class Etichetta:
    """Dove sta una permutazione: H (con numero di Tavola), Γ (h ∘ R^r) o S27."""
    dominio: Dominio
    numero_tavola: Optional[int]      # di p (H) o della componente h (Γ)
    r: Optional[int]                  # esponente di R in Γ
    sigle: Optional[Tuple[str, str, str]]


def etichetta(p) -> Etichetta:
    """Riusa il riconoscimento I5 (classe_estesa), senza duplicarlo."""
    ce = _rc.classe_estesa(p)
    if not ce.appartiene:
        return Etichetta(Dominio.S27, None, None, None)
    sep = ce.separabilita
    dom = Dominio.H if ce.k == 0 else Dominio.GAMMA
    return Etichetta(dom, sep.numero_tavola, ce.k, sep.sigle)


# ════════════════════════ adattatore dei dati legacy ═════════════════════════

class _Adattatore:
    """Dati di `core.group_theory` (legacy «G» = il nostro H) sugli indici di Tavola."""

    def __init__(self):
        g = _legacy_gruppo_216()
        idx = _indice_h()
        self.da_legacy = tuple(idx[tuple(int(x) for x in r)] for r in g.kron_arr)
        self.classi = tuple(tuple(sorted(self.da_legacy[i] for i in c))
                            for c in g.classes)
        self.centro = tuple(sorted(self.da_legacy[i] for i in g.center))
        self.ordini = tuple(int(g.orders[self.da_legacy.index(n)]) for n in range(216))


@lru_cache(maxsize=None)
def _legacy() -> _Adattatore:
    return _Adattatore()


# ═══════════════════════ strumenti di verifica ═══════════════════════════════

def _dati(**kv):
    return tuple(kv.items())


def _esaustiva_elementi(pid, dominio, pred, codice, dati_ce):
    """Tutti gli elementi; se falsa, il minimo lessicografico che la nega."""
    els = sorted(elementi(dominio))
    for i, p in enumerate(els):
        if not pred(p):
            return Verifica(pid, dominio, Esito.FALSA, Metodo.ESAUSTIVO, i + 1,
                            len(els), Controesempio(codice, (p,), dati_ce(p)))
    return Verifica(pid, dominio, Esito.VERA, Metodo.ESAUSTIVO, len(els), len(els))


def _primo_in_s27(pid, pred, codice, dati_ce, limite=40320):
    """Scorre S27 in ordine lessicografico (itertools lo garantisce) fino al primo
    caso falso: e' il controesempio minimo. Se entro `limite` non c'e', l'esito
    e' NON_DECISA: un'esplorazione, mai una prova."""
    for i, p in enumerate(islice(permutations(range(N)), limite)):
        if not pred(p):
            return Verifica(pid, Dominio.S27, Esito.FALSA, Metodo.CONTROESEMPIO,
                            i + 1, None, Controesempio(codice, (p,), dati_ce(p)))
    return Verifica(pid, Dominio.S27, Esito.NON_DECISA, Metodo.ESPLORAZIONE,
                    limite, None)


def _teorema(pid, dominio, fonte):
    return Verifica(pid, dominio, Esito.VERA, Metodo.TEOREMA_FONTE, 0,
                    CARDINALITA[dominio], fonte=fonte)


def _coppie(pid, dominio, pred, codice, dati_ce, els=None):
    """∀ (a, b): pred(a, b); controesempio = coppia minima (a, poi b)."""
    els = sorted(els if els is not None else elementi(dominio))
    n = 0
    for a in els:
        for b in els:
            n += 1
            if not pred(a, b):
                return Verifica(pid, dominio, Esito.FALSA, Metodo.ESAUSTIVO, n,
                                len(els) ** 2,
                                Controesempio(codice, (a, b), dati_ce(a, b)))
    return Verifica(pid, dominio, Esito.VERA, Metodo.ESAUSTIVO, n, n)


# ═══════════════════ strutture: classi, centro, Γ (numpy) ════════════════════

@lru_cache(maxsize=None)
def _classi_di(dominio: Dominio) -> Tuple[frozenset, ...]:
    """Classi di coniugio calcolate qui (g ∘ x ∘ g⁻¹, tutti i g)."""
    els = elementi(dominio)
    arr = np.asarray(els, dtype=np.int16)
    inv = np.argsort(arr, axis=1)
    visti, classi = set(), []
    for x in els:
        if x in visti:
            continue
        xa = np.asarray(x, dtype=np.int16)
        coniugati = np.take_along_axis(arr, xa[inv], axis=1)
        cl = frozenset(tuple(int(v) for v in r) for r in coniugati)
        visti |= cl
        classi.append(cl)
    return tuple(classi)


def _stesso_tipo_non_coniugati(dominio):
    """Minimo (a, b) con lo stesso tipo ciclico ma in classi diverse."""
    classe_di = {}
    for i, cl in enumerate(_classi_di(dominio)):
        for x in cl:
            classe_di[x] = i
    els = sorted(elementi(dominio))
    n = 0
    for a in els:
        ta = tipo_ciclico(a)
        for b in els:
            n += 1
            if tipo_ciclico(b) == ta and classe_di[a] != classe_di[b]:
                return n, (a, b)
    return n, None


# ═════════════════════════════ le proprieta' ═════════════════════════════════

_POTENZE_DI_3 = {0, 1, 3, 9, 27}


def _p_punti_fissi(p):
    return len(punti_fissi(p)) in _POTENZE_DI_3


def _ce_punti_fissi(p):
    return _dati(punti_fissi=len(punti_fissi(p)))


def _p_ordini(p):
    return ordine(p) in (1, 2, 3, 6)


def _ce_ordini(p):
    return _dati(ordine=ordine(p))


def _p_guide(p):
    return p[0] + p[13] + p[26] == 39


def _ce_guide(p):
    return _dati(somma=p[0] + p[13] + p[26])


def _ce_etichetta(p):
    e = etichetta(p)
    return _dati(dominio=e.dominio.value, r=e.r, numero=e.numero_tavola)


def _v_separabile(pid, dominio):
    if dominio is Dominio.S27:
        return _primo_in_s27(pid, lambda p: _rc.separabile(p).separabile,
                             "non_separabile", _ce_etichetta)
    return _esaustiva_elementi(pid, dominio, lambda p: _rc.separabile(p).separabile,
                               "non_separabile", _ce_etichetta)


def _v_chiuso(pid, dominio):
    """∀ a, b ∈ D: a ∘ b ∈ D (numpy: righe composte, confronto con l'insieme)."""
    els = elementi(dominio)
    arr = np.asarray(els, dtype=np.int16)
    insieme = {r.tobytes() for r in arr}
    for i, a in enumerate(arr):
        righe = a[arr]
        if any(r.tobytes() not in insieme for r in righe):     # pragma: no cover
            return Verifica(pid, dominio, Esito.FALSA, Metodo.ESAUSTIVO,
                            (i + 1) * len(els), len(els) ** 2)
    return Verifica(pid, dominio, Esito.VERA, Metodo.ESAUSTIVO, len(els) ** 2,
                    len(els) ** 2)


def _v_commutativo(pid, dominio):
    if dominio is Dominio.S27:
        # le prime 6 permutazioni lessicografiche muovono solo 24, 25, 26:
        # il minimo (a, b) non commutante sta tra loro (a = id commuta con tutti)
        primi = tuple(islice(permutations(range(N)), 6))
        v = _coppie(pid, dominio, lambda a, b: _comp(a, b) == _comp(b, a),
                    "non_commutano", _ce_coppia, els=primi)
        return Verifica(pid, dominio, v.esito, Metodo.CONTROESEMPIO,
                        v.controllati, None, v.controesempio)
    return _coppie(pid, dominio, lambda a, b: _comp(a, b) == _comp(b, a),
                   "non_commutano", _ce_coppia)


def _ce_coppia(a, b):
    return _dati(ab=_comp(a, b), ba=_comp(b, a))


def _v_centro(pid, dominio):
    if dominio is Dominio.S27:
        return _teorema(pid, dominio, "teorema_centro_sn")
    els = elementi(dominio)
    arr = np.asarray(els, dtype=np.int16)
    centrali = [x for x in els
                if np.array_equal(np.asarray(x, dtype=np.int16)[arr],
                                  np.take_along_axis(arr, np.broadcast_to(
                                      np.asarray(x, dtype=np.int16), arr.shape), axis=1))]
    n = len(els) ** 2
    if centrali == [ID]:
        return Verifica(pid, dominio, Esito.VERA, Metodo.ESAUSTIVO, n, n)
    altro = min(c for c in centrali if c != ID)                # pragma: no cover
    return Verifica(pid, dominio, Esito.FALSA, Metodo.ESAUSTIVO, n, n,  # pragma: no cover
                    Controesempio("centrale", (altro,)))


def _v_coniugati_stesso_tipo(pid, dominio):
    if dominio is Dominio.S27:
        return _teorema(pid, dominio, "teorema_classi_sn")
    classi = _classi_di(dominio)
    n = sum(len(c) for c in classi)
    for c in classi:
        if len({tipo_ciclico(x) for x in c}) != 1:          # pragma: no cover
            return Verifica(pid, dominio, Esito.FALSA, Metodo.ESAUSTIVO, n, n)
    return Verifica(pid, dominio, Esito.VERA, Metodo.ESAUSTIVO, n, n)


def _v_tipo_implica_coniugati(pid, dominio):
    if dominio is Dominio.S27:
        return _teorema(pid, dominio, "teorema_classi_sn")
    n, coppia = _stesso_tipo_non_coniugati(dominio)
    tot = CARDINALITA[dominio] ** 2
    if coppia is None:                                       # pragma: no cover
        return Verifica(pid, dominio, Esito.VERA, Metodo.ESAUSTIVO, n, tot)
    a, b = coppia
    return Verifica(pid, dominio, Esito.FALSA, Metodo.ESAUSTIVO, n, tot,
                    Controesempio("stesso_tipo_non_coniugati", coppia,
                                  _dati(tipo=tipo_ciclico(a))))


def _v_due_carte(pid, dominio):
    if dominio is Dominio.S27:
        return _teorema(pid, dominio, "teorema_transitivita_sn")
    els = elementi(dominio)
    tot = (27 * 26) ** 2
    n = 0
    for c1 in range(N):
        for c2 in range(N):
            if c2 == c1:
                continue
            immagini = {(p[c1], p[c2]) for p in els}
            for t1 in range(N):
                for t2 in range(N):
                    if t2 == t1:
                        continue
                    n += 1
                    if (t1, t2) not in immagini:
                        return Verifica(pid, dominio, Esito.FALSA, Metodo.ESAUSTIVO,
                                        n, tot, Controesempio(
                                            "due_carte", (),
                                            _dati(c1=c1, c2=c2, t1=t1, t2=t2)))
    return Verifica(pid, dominio, Esito.VERA, Metodo.ESAUSTIVO, n, tot)  # pragma: no cover


def _v_carta_otto(pid, dominio):
    els = elementi(dominio)
    n = 0
    for c in range(N):
        conta = Counter(p[c] for p in els)
        for t in range(N):
            n += 1
            if conta[t] != 8:
                return Verifica(pid, dominio, Esito.FALSA, Metodo.ESAUSTIVO, n, 729,
                                Controesempio("carta_bersaglio", (),
                                              _dati(carta=c, posizione=t,
                                                    soluzioni=conta[t])))
    return Verifica(pid, dominio, Esito.VERA, Metodo.ESAUSTIVO, n, 729)


def _v_parita(pid, dominio):
    loc = {s: segno(_gr.MESCOLAMENTO[s]) for s in _gr.SIGLE}

    def pred(p):
        s = _rc.separabile(p).sigle
        return segno(p) == loc[s[0]] * loc[s[1]] * loc[s[2]]
    return _esaustiva_elementi(pid, dominio, pred, "parita", lambda p: ())


def _v_autoinversa(pid, dominio):
    def pred(p):
        invol = all(ordine(_gr.MESCOLAMENTO[s]) <= 2 for s in _rc.separabile(p).sigle)
        return (_comp(p, p) == ID) == invol
    return _esaustiva_elementi(pid, dominio, pred, "autoinversa", lambda p: ())


def _v_j(pid, dominio):
    j = _h()[scheda_j().numero_tavola]
    fissi = punti_fissi(j)
    esito = Esito.VERA if fissi == (13,) else Esito.FALSA
    return Verifica(pid, dominio, esito, Metodo.ESAUSTIVO, N, N)


def _v_normale(pid, dominio):
    """∀ g ∈ Γ, h ∈ H: g ∘ h ∘ g⁻¹ ∈ H (648 × 216 coniugi)."""
    hs = set(_h())
    n = 0
    for g in _gamma():
        gi = _inv(g)
        for h in _h():
            n += 1
            if _comp(_comp(g, h), gi) not in hs:              # pragma: no cover
                return Verifica(pid, dominio, Esito.FALSA, Metodo.ESAUSTIVO, n,
                                648 * 216)
    return Verifica(pid, dominio, Esito.VERA, Metodo.ESAUSTIVO, n, n)


def _v_forma_normale(pid, dominio):
    """Ogni g ∈ Γ ha esattamente una scrittura h ∘ R^r (h ∈ H, r ∈ {0,1,2})."""
    hs = set(_h())
    n = 0
    for g in _gamma():
        n += 1
        scritture = [r for r in range(3) if _comp(g, _inv(_msc(r))) in hs]
        if len(scritture) != 1:                               # pragma: no cover
            return Verifica(pid, dominio, Esito.FALSA, Metodo.ESAUSTIVO, n, 648)
    return Verifica(pid, dominio, Esito.VERA, Metodo.ESAUSTIVO, n, 648)


def _v_somme(pid, dominio):
    """Il criterio per somme (App. D Teor. 6.4, I5) coincide col riconoscitore diretto."""
    if dominio is Dominio.S27:
        return _teorema(pid, dominio, "teorema_6_4_app_d")

    def pred(p):
        return _rc.criterio_somme(p).vero == _rc.separabile(p).separabile
    return _esaustiva_elementi(pid, dominio, pred, "somme", lambda p: ())


def _v_otto_procedure(pid, dominio):
    s = servizio_procedure()
    conta = Counter(tuple(s.trasformazione(p)) for p in elementi(Dominio.PROCEDURE))
    ok = len(conta) == 216 and set(conta.values()) == {8} and set(conta) == set(_h())
    return Verifica(pid, dominio, Esito.VERA if ok else Esito.FALSA,
                    Metodo.ESAUSTIVO, 1728, 1728)


def _v_stadi(pid, dominio):
    righe = stadi()
    n = sum(r.prefissi_con for r in righe)
    ok = all(r.classi_laterali == (r.j % 3,) for r in righe)
    return Verifica(pid, dominio, Esito.VERA if ok else Esito.FALSA,
                    Metodo.ESAUSTIVO, n, n)


def _v_quadrato_latino(pid, dominio):
    t = tavola_locale()
    ok = all(sorted(r) == sorted(ORDINE_TAVOLA_LOCALE) for r in t.celle) and all(
        sorted(c) == sorted(ORDINE_TAVOLA_LOCALE) for c in zip(*t.celle))
    return Verifica(pid, dominio, Esito.VERA if ok else Esito.FALSA,
                    Metodo.ESAUSTIVO, 36, 36)


def _v_decomposizioni(pid, dominio):
    """Ogni risultato ha lo stesso numero di decomposizioni P ∘ Q: 6 in S3, 216 in H."""
    els = elementi(dominio)
    conta = Counter(_comp(a, b) for a in els for b in els)
    atteso = len(els)
    ok = len(conta) == len(els) and set(conta.values()) == {atteso}
    return Verifica(pid, dominio, Esito.VERA if ok else Esito.FALSA,
                    Metodo.ESAUSTIVO, len(els) ** 2, len(els) ** 2)


def _voce(pid, fonte, verifiche, note=()):
    dom = tuple(d for d, _ in verifiche)
    return Proprieta(pid, fonte, dom,
                     tuple((d, (lambda f=f, d=d: _memo(pid, d, f))) for d, f in verifiche),
                     tuple(note))


_CACHE: Dict[Tuple[str, Dominio], Verifica] = {}


def _memo(pid, dominio, f):
    chiave = (pid, dominio)
    if chiave not in _CACHE:
        _CACHE[chiave] = f(pid, dominio)
    return _CACHE[chiave]


def _el(pred, codice, dati):
    return lambda pid, d: _esaustiva_elementi(pid, d, pred, codice, dati)


def _s27(pred, codice, dati):
    return lambda pid, d: _primo_in_s27(pid, pred, codice, dati)


H, G, S, P, L = Dominio.H, Dominio.GAMMA, Dominio.S27, Dominio.PROCEDURE, Dominio.S3

#: Il catalogo chiuso (§ 18.4 dell'audit, con le fonti del libro).
CATALOGO: Tuple[Proprieta, ...] = (
    _voce("separabile", "articolo_def_4_1",
          [(H, _v_separabile), (G, _v_separabile), (S, _v_separabile)],
          [(G, "nota_gamma_r")]),
    _voce("chiuso_composizione", "libro_8_4",
          [(H, _v_chiuso), (G, _v_chiuso)]),
    _voce("commutativo", "libro_8_2",
          [(L, _v_commutativo), (H, _v_commutativo), (G, _v_commutativo),
           (S, _v_commutativo)]),
    _voce("centro_banale", "libro_6_9",
          [(H, _v_centro), (G, _v_centro), (S, _v_centro)]),
    _voce("ordini_1_2_3_6", "libro_6_7",
          [(H, _el(_p_ordini, "ordine", _ce_ordini)),
           (G, _el(_p_ordini, "ordine", _ce_ordini)),
           (S, _s27(_p_ordini, "ordine", _ce_ordini))],
          [(G, "nota_ordine_9")]),
    _voce("punti_fissi_potenze_di_3", "libro_b9_a5",
          [(H, _el(_p_punti_fissi, "punti_fissi", _ce_punti_fissi)),
           (G, _el(_p_punti_fissi, "punti_fissi", _ce_punti_fissi)),
           (S, _s27(_p_punti_fissi, "punti_fissi", _ce_punti_fissi))]),
    _voce("somma_guide_39", "libro_10_2_1",
          [(H, _el(_p_guide, "somma_guide", _ce_guide)),
           (G, _el(_p_guide, "somma_guide", _ce_guide)),
           (S, _s27(_p_guide, "somma_guide", _ce_guide))]),
    _voce("coniugati_stesso_tipo", "libro_b9",
          [(H, _v_coniugati_stesso_tipo), (G, _v_coniugati_stesso_tipo),
           (S, _v_coniugati_stesso_tipo)]),
    _voce("stesso_tipo_coniugati", "libro_6_7_b9",
          [(H, _v_tipo_implica_coniugati), (G, _v_tipo_implica_coniugati),
           (S, _v_tipo_implica_coniugati)],
          [(H, "nota_27_classi_7_tipi")]),
    _voce("carta_bersaglio_otto", "libro_a4",
          [(H, _v_carta_otto), (G, _v_carta_otto)]),
    _voce("due_carte_forzabili", "libro_a4",
          [(H, _v_due_carte), (G, _v_due_carte), (S, _v_due_carte)],
          [(H, "nota_audit_0_9")]),
    _voce("parita_prodotto_locale", "libro_a10", [(H, _v_parita)]),
    _voce("autoinversa_fattori_involutivi", "libro_prop_5_53", [(H, _v_autoinversa)]),
    _voce("j_fissa_solo_13", "libro_6_10", [(H, _v_j)]),
    _voce("somme_riconoscono_h", "appendice_d_teor_6_4",
          [(H, _v_somme), (G, _v_somme), (S, _v_somme)]),
    _voce("h_normale_in_gamma", "libro_11_7", [(G, _v_normale)]),
    _voce("forma_normale_unica", "libro_teor_11_68", [(G, _v_forma_normale)]),
    _voce("stadi_classe_laterale", "libro_11_7_6", [(P, _v_stadi)]),
    _voce("otto_procedure", "libro_prop_9_58", [(P, _v_otto_procedure)]),
    _voce("tavola_quadrato_latino", "libro_8_2", [(L, _v_quadrato_latino)]),
    _voce("decomposizioni_uniformi", "libro_8_5",
          [(L, _v_decomposizioni), (H, _v_decomposizioni)]),
)
del H, G, S, P, L


def proprieta(pid: str) -> Proprieta:
    for p in CATALOGO:
        if p.id == pid:
            return p
    raise ProprietaSconosciuta(pid)


def verifica(pid: str, dominio: Dominio) -> Verifica:
    return proprieta(pid).verifica(dominio)


# ═══════════════════ classi di H e fusione in S27 (§ 6.7, B.9) ═══════════════

_TIPO_LOCALE = {1: "I", 2: "T", 3: "C"}      # identita', trasposizione, 3-ciclo
_ORDINE_TIPO = {"I": 0, "T": 1, "C": 2}


@dataclass(frozen=True)
class ClasseH:
    numero: int                          # numerazione del libro (§ 6.7), 1..27
    tipo: str                            # (f2, f1, f0), es. "TIC"
    elementi: Tuple[int, ...]            # numeri di Tavola
    ordine: int
    tipo_ciclico: Tuple[Tuple[int, int], ...]
    punti_fissi: int

    @property
    def cardinalita(self) -> int:
        return len(self.elementi)

    @property
    def centrale(self) -> bool:
        return self.cardinalita == 1


def _tipo_locale_di(n: int) -> str:
    sig = _gr.mescolamenti_da_numero(n)          # (M0, M1, M2)
    return "".join(_TIPO_LOCALE[ordine(_gr.MESCOLAMENTO[s])] for s in reversed(sig))


@lru_cache(maxsize=None)
def classi_h() -> Tuple[ClasseH, ...]:
    """Le 27 classi di coniugio di H, dai dati legacy tramite l'adattatore."""
    h = _h()
    classi = []
    for cl in _legacy().classi:
        tipi = {_tipo_locale_di(n) for n in cl}
        assert len(tipi) == 1
        p = h[cl[0]]
        classi.append((len(cl), tuple(_ORDINE_TIPO[c] for c in next(iter(tipi))),
                       next(iter(tipi)), cl, p))
    classi.sort(key=lambda c: (c[0], c[1]))
    return tuple(ClasseH(i + 1, t, cl, ordine(p), tipo_ciclico(p), len(punti_fissi(p)))
                 for i, (_, _, t, cl, p) in enumerate(classi))


@dataclass(frozen=True)
class TipoCiclico:
    numero: int                          # 1..7 (App. B.9)
    tipo: Tuple[Tuple[int, int], ...]
    classi: Tuple[int, ...]              # numeri delle classi di H che vi confluiscono
    cardinalita: int
    ordine: int
    punti_fissi: int
    segno: int


@lru_cache(maxsize=None)
def fusione_in_s27() -> Tuple[TipoCiclico, ...]:
    """27 classi di H → 7 tipi ciclici (= 7 classi di S27 toccate da H)."""
    per_tipo: Dict[tuple, list] = {}
    for c in classi_h():
        per_tipo.setdefault(c.tipo_ciclico, []).append(c)
    righe = []
    for t, cs in per_tipo.items():
        p = _h()[cs[0].elementi[0]]
        righe.append((ordine(p), -len(punti_fissi(p)), sum(c.cardinalita for c in cs),
                      t, cs, p))
    righe.sort(key=lambda r: r[:3])
    return tuple(TipoCiclico(i + 1, t, tuple(c.numero for c in cs), card, o, -fp, segno(p))
                 for i, (o, fp, card, t, cs, p) in enumerate(righe))


# ═════════════════════════════ centro (§ 6.9) ════════════════════════════════

@dataclass(frozen=True)
class Centro:
    elementi: Tuple[int, ...]            # numeri di Tavola
    commutazioni_controllate: int        # 216 × 216
    legacy_concorda: bool                # `core.group_theory` dice lo stesso


@lru_cache(maxsize=None)
def centro() -> Centro:
    h = _h()
    arr = np.asarray(h, dtype=np.int16)
    el = []
    for n, z in enumerate(h):
        za = np.asarray(z, dtype=np.int16)
        zg = za[arr]                                      # z ∘ g
        gz = np.take_along_axis(arr, np.broadcast_to(za, arr.shape), axis=1)  # g ∘ z
        if np.array_equal(zg, gz):
            el.append(n)
    return Centro(tuple(el), 216 * 216, tuple(el) == _legacy().centro)


# ═══════════════════════════════ J (§ 6.10) ══════════════════════════════════

@dataclass(frozen=True)
class SchedaJ:
    numero_tavola: int
    sigle: Tuple[str, str, str]                  # (M0, M1, M2)
    permutazione: Permutazione
    ordine: int
    tipo_ciclico: Tuple[Tuple[int, int], ...]
    punti_fissi: Tuple[int, ...]
    classe: int                                  # numero di classe di H
    tipo_classe: str
    procedure: Tuple[Tuple[int, int], ...]       # le 8 procedure che la realizzano


@lru_cache(maxsize=None)
def scheda_j() -> SchedaJ:
    """J = DCS ⊗ DCS ⊗ DCS, i ↦ 26 − i: una permutazione finale di H.

    Il rovesciamento (gesto, DP3) e' un'altra cosa: agisce dentro uno stadio e
    le procedure che lo usano realizzano comunque uno dei 216 elementi di H."""
    n = _gr.numero_tavola(("DCS", "DCS", "DCS"))
    j = _h()[n]
    cl = next(c for c in classi_h() if n in c.elementi)
    s = servizio_procedure()
    proc = tuple(sorted(p.identificatore for p in s.classe_trasformazione(j)))
    return SchedaJ(n, tuple(_gr.mescolamenti_da_numero(n)), j, ordine(j),
                   tipo_ciclico(j), punti_fissi(j), cl.numero, cl.tipo, proc)


# ═════════════════════ classi laterali e stadi (§ 11.7) ══════════════════════

@dataclass(frozen=True)
class ClasseLaterale:
    r: int                          # H ∘ MSC^r
    cardinalita: int
    contiene_h: bool


@lru_cache(maxsize=None)
def classi_laterali() -> Tuple[ClasseLaterale, ...]:
    conta = Counter(etichetta(g).r for g in _gamma())
    return tuple(ClasseLaterale(r, conta[r], r == 0) for r in range(3))


@dataclass(frozen=True)
class RigaStadio:
    j: int                                   # stadi eseguiti
    prefissi_senza: int                      # 6^j configurazioni senza rovesci
    trasformazioni_senza: int
    prefissi_con: int                        # 12^j configurazioni
    trasformazioni_con: int
    molteplicita: Tuple[int, ...]            # quante configurazioni per trasformazione
    classi_laterali: Tuple[int, ...]         # r dei risultati (atteso: j mod 3)
    configurazioni_uguali_a_procedure: Optional[int] = None   # solo j = 3


def _stadio(sigla: str, rovescio: bool) -> Permutazione:
    mazzo = list(range(N))[::-1] if rovescio else list(range(N))
    d = _gr.raccogli(_gr.distribuisci(mazzo), sigla)
    return tuple(d.index(c) for c in range(N))


@lru_cache(maxsize=None)
def stadi() -> Tuple[RigaStadio, ...]:
    """Configurazioni di stadio (core) vs procedure (I1), j = 1, 2, 3."""
    st = {(s, e): _stadio(s, bool(e)) for s in _gr.SIGLE for e in (0, 1)}
    serv = servizio_procedure()
    righe = []
    for j in (1, 2, 3):
        conta, senza = Counter(), set()
        uguali = 0
        for sig in product(_gr.SIGLE, repeat=j):
            for eps in product((0, 1), repeat=j):
                t = ID
                for s, e in zip(sig, eps):
                    t = _comp(st[(s, e)], t)
                conta[t] += 1
                if not any(eps):
                    senza.add(t)
                if j == 3:
                    proc = ProceduraGioco(mescolamenti=sig, rovesciamenti=eps)
                    uguali += tuple(serv.trasformazione(proc)) == t
        righe.append(RigaStadio(
            j, 6 ** j, len(senza), 12 ** j, len(conta),
            tuple(sorted(set(conta.values()))),
            tuple(sorted({etichetta(t).r for t in conta})),
            uguali if j == 3 else None))
    return tuple(righe)


# ═══════════════════ tavola locale 6×6 e decomposizioni (cap. 8) ══════════════

#: § 8.2, trascritta: riga P, colonna Q, cella P ∘ Q (prima Q, poi P)
TAVOLA_LOCALE_FONTE = (
    ("SCD", "SDC", "CSD", "CDS", "DSC", "DCS"),
    ("SDC", "SCD", "DSC", "DCS", "CSD", "CDS"),
    ("CSD", "CDS", "SCD", "SDC", "DCS", "DSC"),
    ("CDS", "CSD", "DCS", "DSC", "SCD", "SDC"),
    ("DSC", "DCS", "SDC", "SCD", "CDS", "CSD"),
    ("DCS", "DSC", "CDS", "CSD", "SDC", "SCD"),
)

_SIGLA_DI = {tuple(v): k for k, v in _gr.MESCOLAMENTO.items()}


def _comp_locale(p: str, q: str) -> str:
    a, b = _gr.MESCOLAMENTO[p], _gr.MESCOLAMENTO[q]
    return _SIGLA_DI[tuple(a[b[i]] for i in range(3))]


@dataclass(frozen=True)
class TavolaLocale:
    ordine: Tuple[str, ...]
    celle: Tuple[Tuple[str, ...], ...]           # calcolate dal core
    celle_concordi: int                          # confronto con la fonte, su 36
    inversi: Tuple[Tuple[str, str], ...]
    tipi: Tuple[Tuple[str, str], ...]            # sigla → I / T / C


@lru_cache(maxsize=None)
def tavola_locale() -> TavolaLocale:
    o = ORDINE_TAVOLA_LOCALE
    celle = tuple(tuple(_comp_locale(p, q) for q in o) for p in o)
    concordi = sum(celle[i][k] == TAVOLA_LOCALE_FONTE[i][k]
                   for i in range(6) for k in range(6))
    inversi = tuple((p, next(q for q in o if _comp_locale(p, q) == "SCD")) for p in o)
    tipi = tuple((p, _TIPO_LOCALE[ordine(_gr.MESCOLAMENTO[p])]) for p in o)
    return TavolaLocale(o, celle, concordi, inversi, tipi)


def decomposizioni_locali(risultato: str) -> Tuple[Tuple[str, str], ...]:
    """§ 8.5: le 6 coppie (P, Q) con P ∘ Q = risultato, P nell'ordine della tavola."""
    if risultato not in _gr.MESCOLAMENTO:
        raise ValueError(risultato)
    inv = dict(tavola_locale().inversi)
    return tuple((p, _comp_locale(inv[p], risultato)) for p in ORDINE_TAVOLA_LOCALE)


def transizione_locale(da: str, a: str) -> str:
    """§ 8.5: l'unico R con R ∘ da = a, cioe' R = a ∘ da⁻¹."""
    inv = dict(tavola_locale().inversi)
    return _comp_locale(a, inv[da])


# ═════════════════════════ piccoli grafi (§ 18.3) ════════════════════════════

@dataclass(frozen=True)
class Grafo:
    id: str
    dominio: Dominio
    orientato: bool
    vertici: Tuple[object, ...]
    archi: Tuple[Tuple[int, int], ...]           # indici di vertici, i < k
    radice: int                                  # vertice di partenza delle distanze

    @property
    def adiacenza(self) -> Tuple[Tuple[int, ...], ...]:
        adj = [[] for _ in self.vertici]
        for a, b in self.archi:
            adj[a].append(b)
            adj[b].append(a)
        return tuple(tuple(sorted(v)) for v in adj)

    @property
    def gradi(self) -> Tuple[int, ...]:
        return tuple(sorted({len(v) for v in self.adiacenza}))

    def distanze(self, da: Optional[int] = None) -> Tuple[int, ...]:
        da = self.radice if da is None else da
        adj = self.adiacenza
        dist = [-1] * len(self.vertici)
        dist[da] = 0
        coda = deque([da])
        while coda:
            v = coda.popleft()
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    coda.append(w)
        return tuple(dist)

    @property
    def distribuzione(self) -> Tuple[int, ...]:
        """Quanti vertici a distanza 0, 1, 2, ... dalla radice."""
        c = Counter(self.distanze())
        return tuple(c[k] for k in range(max(c) + 1))

    @property
    def diametro(self) -> int:
        return max(max(self.distanze(v)) for v in range(len(self.vertici)))


def _grafo_s3() -> Grafo:
    """Cayley di S3 rispetto alle 3 trasposizioni (classe T): K_{3,3}."""
    o = ORDINE_TAVOLA_LOCALE
    t = [s for s in o if ordine(_gr.MESCOLAMENTO[s]) == 2]
    archi = {tuple(sorted((o.index(x), o.index(_comp_locale(g, x))))) for x in o for g in t}
    return Grafo("cayley_s3", Dominio.S3, False, o, tuple(sorted(archi)), 0)


def _grafo_h() -> Grafo:
    """H = S3 × S3 × S3: un arco cambia il fattore di UN livello con una trasposizione."""
    h = _h()
    idx = _indice_h()
    t = [s for s in _gr.SIGLE if ordine(_gr.MESCOLAMENTO[s]) == 2]
    archi = set()
    for n in range(216):
        sig = list(_gr.mescolamenti_da_numero(n))
        for liv in range(3):
            for g in t:
                nuovo = list(sig)
                nuovo[liv] = _comp_locale(g, sig[liv])
                m = _gr.numero_tavola(tuple(nuovo))
                archi.add(tuple(sorted((n, m))))
    assert all(idx[h[n]] == n for n in range(216))
    return Grafo("cayley_h", Dominio.H, False, tuple(range(216)), tuple(sorted(archi)), 0)


def _grafo_raccolte() -> Grafo:
    """Le 216 trasformazioni: arco = cambiare una sola raccolta (Hamming su 6³)."""
    archi = set()
    for n in range(216):
        sig = _gr.mescolamenti_da_numero(n)
        for liv in range(3):
            for s in _gr.SIGLE:
                if s != sig[liv]:
                    nuovo = list(sig)
                    nuovo[liv] = s
                    archi.add(tuple(sorted((n, _gr.numero_tavola(tuple(nuovo))))))
    return Grafo("raccolte", Dominio.H, False, tuple(range(216)), tuple(sorted(archi)), 0)


@lru_cache(maxsize=None)
def grafi() -> Tuple[Grafo, ...]:
    return (_grafo_s3(), _grafo_h(), _grafo_raccolte())


def grafo(gid: str) -> Grafo:
    for g in grafi():
        if g.id == gid:
            return g
    raise KeyError(gid)


def cammino(g: Grafo, da: int, a: int) -> Tuple[int, ...]:
    """Un cammino minimo, deterministico: a parita' si sceglie il vicino minore."""
    dist = g.distanze(a)
    adj = g.adiacenza
    cammino_ = [da]
    while cammino_[-1] != a:
        v = cammino_[-1]
        cammino_.append(min(w for w in adj[v] if dist[w] == dist[v] - 1))
    return tuple(cammino_)
