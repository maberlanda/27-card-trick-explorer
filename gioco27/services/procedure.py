"""Procedure del gioco, relazioni fra procedure e strategie (compartimento I1).

Un piccolo modello applicativo immutabile sopra la matematica del core. Non
reimplementa MSC, prodotti di Kronecker, J o composizioni: la trasformazione di
una procedura e' calcolata da `core.permutations.compute_T_perm` sul preset
«Gioco Reale» (P0 = P1 = identita', P2 = raccolta, J uniforme); le sigle, il
numero di tavola, l'impilamento e il solutore storico vengono da
`core.gioco_reale`; i validatori di indici e permutazioni da `core.dominio`.

Decisioni applicate (docs/decisions/V4_PRE_I1_PRODUCT_DECISIONS.md, approvate)
---------------------------------------------------------------

DP3 — una procedura canonica e' ``(S1, S2, S3 ; e1, e2, e3)``: ``S_i`` e' la
    sigla di **mescolamento** (funzionale, riga del tabellone) dello stadio i,
    ``e_i`` il rovesciamento dell'intero mazzo **prima della distribuzione**
    dello stadio i::

        T_i = (S_i ⊗ I3 ⊗ I3) ∘ MSC ∘ J^e_i          T = T3 ∘ T2 ∘ T1

    Identificatori stabili: ``# = k1 + 6·k2 + 36·k3`` (ordine delle sigle di
    `gioco_reale.SIGLE`) e ``m = 4·e1 + 2·e2 + e3``; la coppia ``(#, m)``
    identifica la procedura. La simulazione fisica di `gioco_reale`
    (rovesciamento DOPO la raccolta) resta un oracolo, raggiunto con
    `adattamento_fisico`: non esiste un secondo modello di procedura. Un
    rovesciamento dopo l'ultima raccolta e' fuori da questa famiglia.

DP4 — nessuna «equivalenza» generica: il servizio espone relazioni nominate
    (identita', stessa trasformazione globale, stesso effetto su una carta),
    la classe di una trasformazione (8 procedure) e la fibra carta→bersaglio
    (64 procedure raggruppate in 8 trasformazioni).

DP5 — tre costi separati: ``k1`` = raccolte diverse da SCD, ``k2`` = raccolte
    cicliche CDS/DSC, ``k3`` = rovesciamenti. La procedura storica e'
    l'argmin di ``(k1, #)`` fra le procedure senza rovesciamenti e coincide
    con `risolvi_trucco`; la variante sicura e' l'argmin di
    ``(k3, k2, k1, m, #)`` sull'intera fibra e NON la sostituisce.

Terminologia: i nomi sono tecnici e neutrali; il lessico narrativo del libro e
i nomi dei gruppi restano da decidere (DP2, DP8). Nessun testo per l'utente:
i risultati sono dati, gli errori portano un `codice` stabile.
"""

from __future__ import annotations

import numbers
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Optional, Tuple

from ..core import gioco_reale as _gr
from ..core.constants import PERM3
from ..core.dominio import valida_indice, valida_permutazione
from ..core.permutations import compute_T_perm

__all__ = [
    "ProceduraGioco", "ProceduraNonValida", "TrasformazioneFuoriDominio",
    "Costo", "FamigliaGesti", "FAMIGLIA_TUTTE", "FAMIGLIA_SEMPLICE",
    "FAMIGLIA_SICURA", "FAMIGLIA_SEMPLICE_SICURA", "AdattamentoFisico",
    "adattamento_fisico", "GruppoTrasformazione", "FibraBersaglio",
    "ConfrontoProcedure", "chiave_storica", "chiave_sicura", "chiave_costo",
    "ServizioProcedure", "servizio_procedure", "parametri_gioco_reale",
]

Trasformazione = Tuple[int, ...]          # T[carta] = posizione finale

#: raccolte che differiscono dal proprio impilamento (CDS ↔ DSC)
_CICLICHE = frozenset(s for s in _gr.SIGLE if _gr.IMPILAMENTO_DI[s] != s)
_IDENTITA = _gr.SIGLE[0]                  # "SCD"


class ProceduraNonValida(ValueError):
    """Dati che non descrivono una procedura canonica.

    Come `core.dominio.PermutazioneNonValida`: messaggio neutro e `codice`
    stabile, perche' chi lo mostra all'utente componga la frase nella sua
    lingua.
    """

    def __init__(self, messaggio, *, codice, **dati):
        super().__init__(messaggio)
        self.codice = codice
        self.dati = dati


class TrasformazioneFuoriDominio(ValueError):
    """Permutazione valida di 27 elementi che nessuna procedura realizza."""

    codice = "trasformazione_fuori_dominio"


# ═══════════════════════════════ modello ════════════════════════════════════

def _bit(valore, posizione):
    if isinstance(valore, bool):
        return int(valore)
    if isinstance(valore, numbers.Integral) and int(valore) in (0, 1):
        return int(valore)
    raise ProceduraNonValida(
        f"rovesciamenti: valore {valore!r} in posizione {posizione} non binario",
        codice="rovesciamento_non_binario", valore=valore, posizione=posizione)


def _terna(valori, nome):
    if isinstance(valori, (str, bytes)):
        raise ProceduraNonValida(f"{nome}: attesa una sequenza di tre elementi",
                                 codice="tipo_non_ammesso", nome=nome)
    try:
        terna = tuple(valori)
    except TypeError:
        raise ProceduraNonValida(f"{nome}: oggetto non iterabile",
                                 codice="non_iterabile", nome=nome) from None
    if len(terna) != 3:
        raise ProceduraNonValida(f"{nome}: {len(terna)} stadi, attesi 3",
                                 codice="numero_stadi", nome=nome,
                                 ricevuti=len(terna))
    return terna


@dataclass(frozen=True)
class Costo:
    """I tre costi di una procedura, separati e mai compressi in un punteggio.

    k1  raccolte diverse da SCD
    k2  raccolte cicliche CDS/DSC (mescolamento ≠ impilamento)
    k3  rovesciamenti del mazzo
    """

    k1: int
    k2: int
    k3: int


@dataclass(frozen=True)
class ProceduraGioco:
    """Procedura canonica (DP3 = A): tre raccolte e tre rovesciamenti.

    `mescolamenti` sono le sigle funzionali in ordine cronologico (stadio 1
    per primo); `rovesciamenti[i]` vale 1 se il mazzo va capovolto prima della
    distribuzione dello stadio i+1. L'impilamento fisico e' derivato.
    """

    mescolamenti: Tuple[str, str, str]
    rovesciamenti: Tuple[int, int, int] = (0, 0, 0)

    def __post_init__(self):
        mesc = _terna(self.mescolamenti, "mescolamenti")
        for i, s in enumerate(mesc):
            if not isinstance(s, str) or s not in _gr.MESCOLAMENTO:
                raise ProceduraNonValida(
                    f"mescolamenti: sigla {s!r} sconosciuta in posizione {i}",
                    codice="sigla_sconosciuta", valore=s, posizione=i)
        eps = tuple(_bit(v, i) for i, v in
                    enumerate(_terna(self.rovesciamenti, "rovesciamenti")))
        object.__setattr__(self, "mescolamenti", mesc)
        object.__setattr__(self, "rovesciamenti", eps)

    @classmethod
    def da_identificatore(cls, numero_tavola, indice_rovesciamenti):
        """Ricostruisce la procedura dalla coppia (#, m)."""
        for valore, nome, n in ((numero_tavola, "numero_tavola", 216),
                                (indice_rovesciamenti, "indice_rovesciamenti", 8)):
            if isinstance(valore, bool) or not isinstance(valore, numbers.Integral) \
                    or not 0 <= valore < n:
                raise ProceduraNonValida(
                    f"{nome}: valore {valore!r} fuori da 0..{n - 1}",
                    codice="identificatore_fuori_intervallo", nome=nome,
                    valore=valore)
        m = int(indice_rovesciamenti)
        return cls(_gr.mescolamenti_da_numero(int(numero_tavola)),
                   ((m >> 2) & 1, (m >> 1) & 1, m & 1))

    @property
    def numero_tavola(self) -> int:
        return _gr.numero_tavola(self.mescolamenti)

    @property
    def indice_rovesciamenti(self) -> int:
        e1, e2, e3 = self.rovesciamenti
        return 4 * e1 + 2 * e2 + e3

    @property
    def identificatore(self) -> Tuple[int, int]:
        """(#, m): identifica univocamente la procedura."""
        return self.numero_tavola, self.indice_rovesciamenti

    @property
    def impilamenti(self) -> Tuple[str, str, str]:
        return tuple(_gr.IMPILAMENTO_DI[s] for s in self.mescolamenti)

    @property
    def costo(self) -> Costo:
        return Costo(k1=sum(s != _IDENTITA for s in self.mescolamenti),
                     k2=sum(s in _CICLICHE for s in self.mescolamenti),
                     k3=sum(self.rovesciamenti))

    @property
    def semplice(self) -> bool:
        """Nessun rovesciamento (k3 = 0)."""
        return not any(self.rovesciamenti)

    @property
    def sicura(self) -> bool:
        """Nessuna raccolta ciclica CDS/DSC (k2 = 0)."""
        return not any(s in _CICLICHE for s in self.mescolamenti)


@dataclass(frozen=True)
class FamigliaGesti:
    """Famiglia di gesti dichiarata: un filtro esplicito, mai implicito."""

    senza_rovesciamenti: bool = False
    senza_raccolte_cicliche: bool = False

    def contiene(self, procedura: ProceduraGioco) -> bool:
        return ((not self.senza_rovesciamenti or procedura.semplice) and
                (not self.senza_raccolte_cicliche or procedura.sicura))


FAMIGLIA_TUTTE = FamigliaGesti()
FAMIGLIA_SEMPLICE = FamigliaGesti(senza_rovesciamenti=True)
FAMIGLIA_SICURA = FamigliaGesti(senza_raccolte_cicliche=True)
FAMIGLIA_SEMPLICE_SICURA = FamigliaGesti(senza_rovesciamenti=True,
                                         senza_raccolte_cicliche=True)


# ═════════════════════════ oracolo fisico (DP3) ═════════════════════════════

@dataclass(frozen=True)
class AdattamentoFisico:
    """Come eseguire una procedura canonica con la simulazione di `gioco_reale`.

    ``T_A(S; e1,e2,e3) = T_B(S; e2,e3,0) ∘ J^e1``: il rovesciamento prima della
    distribuzione dello stadio i+1 e' quello dopo la raccolta dello stadio i;
    il rovesciamento prima dello stadio 1 capovolge il mazzo iniziale.
    """

    rovescia_mazzo_iniziale: bool
    mescolamenti: Tuple[str, str, str]
    rovesciamenti_dopo_raccolta: Tuple[bool, bool, bool]


def adattamento_fisico(procedura: ProceduraGioco) -> AdattamentoFisico:
    e1, e2, e3 = procedura.rovesciamenti
    return AdattamentoFisico(bool(e1), procedura.mescolamenti,
                             (bool(e2), bool(e3), False))


# ═══════════════════════════════ chiavi ═════════════════════════════════════

_METRICHE = {"k1": lambda p: p.costo.k1,
             "k2": lambda p: p.costo.k2,
             "k3": lambda p: p.costo.k3}


def chiave_costo(*metriche: str) -> Callable[[ProceduraGioco], tuple]:
    """Chiave lessicografica sulle metriche dichiarate, chiusa da (m, #).

    La coda (m, #) rende la chiave un ordine totale sul dominio: nessun
    pareggio dipende da dict, set, hash o ordine di enumerazione.
    """
    for nome in metriche:
        if nome not in _METRICHE:
            raise ValueError(f"metrica sconosciuta: {nome!r}")
    funzioni = tuple(_METRICHE[n] for n in metriche)

    def chiave(p: ProceduraGioco) -> tuple:
        return tuple(f(p) for f in funzioni) + (p.indice_rovesciamenti,
                                                p.numero_tavola)
    return chiave


def chiave_storica(p: ProceduraGioco) -> tuple:
    """(k1, #): chiave del solutore storico, definita sulle procedure semplici."""
    return p.costo.k1, p.numero_tavola


chiave_sicura = chiave_costo("k3", "k2", "k1")
chiave_sicura.__doc__ = "(k3, k2, k1, m, #): chiave della variante sicura."


# ═══════════════════════════ risultati strutturati ══════════════════════════

@dataclass(frozen=True)
class GruppoTrasformazione:
    """Le 8 procedure di una fibra che realizzano la stessa trasformazione."""

    trasformazione: Trasformazione
    procedure: Tuple[ProceduraGioco, ...]          # ordinate per (m, #)

    @property
    def semplice(self) -> ProceduraGioco:
        """L'unica procedura del gruppo senza rovesciamenti."""
        return self.procedure[0]


@dataclass(frozen=True)
class FibraBersaglio:
    """Procedure che portano `carta` in `bersaglio`, raggruppate per T.

    I gruppi sono ordinati per numero di tavola della loro procedura semplice.
    """

    carta: int
    bersaglio: int
    gruppi: Tuple[GruppoTrasformazione, ...]

    @property
    def procedure(self) -> Tuple[ProceduraGioco, ...]:
        return tuple(p for g in self.gruppi for p in g.procedure)

    @property
    def semplici(self) -> Tuple[ProceduraGioco, ...]:
        return tuple(g.semplice for g in self.gruppi)


@dataclass(frozen=True)
class ConfrontoProcedure:
    """Esito del confronto di due procedure: solo dati, nessun testo."""

    stessa_procedura: bool
    stessa_trasformazione: bool
    carta: Optional[int]
    stesso_effetto_carta: Optional[bool]
    costi: Tuple[Costo, Costo]
    semplici: Tuple[bool, bool]
    sicure: Tuple[bool, bool]


# ═══════════════════════════════ servizio ═══════════════════════════════════

def _nome_perm3(perm):
    """Nome del core (`PERM3`) della permutazione su {0,1,2}."""
    for nome, valori in PERM3.items():
        if tuple(valori) == tuple(perm):
            return nome
    raise KeyError(perm)


_IDENTITA_NOME = _nome_perm3((0, 1, 2))


def parametri_gioco_reale(p: ProceduraGioco):
    """Parametri (p0,p1,p2,j0,j1,j2) del preset «Gioco Reale» per ogni stadio.

    Sono i parametri di stadio del core (`compute_T_perm`, Explorer): una
    procedura canonica li determina senza ambiguita' (J uniforme = ε, P2 =
    raccolta, P1 = P0 = identita').
    """
    return _parametri_gioco_reale(p)


def _parametri_gioco_reale(p: ProceduraGioco):
    """Implementazione di `parametri_gioco_reale`."""
    stadi = []
    for sigla, e in zip(p.mescolamenti, p.rovesciamenti):
        j = "R_U" if e else "I_3"
        stadi.append((_IDENTITA_NOME, _IDENTITA_NOME,
                      _nome_perm3(_gr.MESCOLAMENTO[sigla]), j, j, j))
    return stadi


class ServizioProcedure:
    """Dominio delle 1728 procedure canoniche e relazioni fra procedure.

    Costruito una volta, immutabile: le 1728 trasformazioni sono precalcolate
    dal core (qualche decina di millisecondi) e ogni interrogazione e' una
    lettura o una scansione di 1728 elementi.
    """

    def __init__(self):
        procedure = tuple(ProceduraGioco.da_identificatore(n, m)
                          for m in range(8) for n in range(216))
        trasf = tuple(tuple(compute_T_perm(_parametri_gioco_reale(p))[2])
                      for p in procedure)
        self._procedure = procedure
        self._T = dict(zip(procedure, trasf))
        classi = {}
        for p, T in zip(procedure, trasf):      # procedure gia' in ordine (m, #)
            classi.setdefault(T, []).append(p)
        self._classi = {T: tuple(ps) for T, ps in classi.items()}
        self._trasformazioni = tuple(self._T[p] for p in procedure[:216])

    # ── dominio ──────────────────────────────────────────────────────────────
    @property
    def procedure(self) -> Tuple[ProceduraGioco, ...]:
        """Le 1728 procedure in ordine (m, #) crescente."""
        return self._procedure

    @property
    def trasformazioni(self) -> Tuple[Trasformazione, ...]:
        """Le 216 trasformazioni, nell'ordine # delle procedure semplici."""
        return self._trasformazioni

    def trasformazione(self, procedura: ProceduraGioco) -> Trasformazione:
        """T(procedura): T[carta] = posizione finale."""
        return self._T[procedura]

    def classe_trasformazione(self, trasformazione) -> Tuple[ProceduraGioco, ...]:
        """Le 8 procedure che realizzano T, in ordine (m, #)."""
        T = valida_permutazione(trasformazione, 27, nome="trasformazione")
        try:
            return self._classi[T]
        except KeyError:
            raise TrasformazioneFuoriDominio(
                "nessuna procedura realizza la trasformazione") from None

    # ── relazioni ────────────────────────────────────────────────────────────
    def stessa_trasformazione(self, p: ProceduraGioco, q: ProceduraGioco) -> bool:
        return self._T[p] == self._T[q]

    def stesso_effetto_carta(self, p: ProceduraGioco, q: ProceduraGioco,
                             carta: int) -> bool:
        c = valida_indice(carta, 27, nome="carta")
        return self._T[p][c] == self._T[q][c]

    def confronta(self, p: ProceduraGioco, q: ProceduraGioco,
                  carta: Optional[int] = None) -> ConfrontoProcedure:
        effetto = None if carta is None else self.stesso_effetto_carta(p, q, carta)
        return ConfrontoProcedure(
            stessa_procedura=p == q,
            stessa_trasformazione=self.stessa_trasformazione(p, q),
            carta=None if carta is None else valida_indice(carta, 27, nome="carta"),
            stesso_effetto_carta=effetto,
            costi=(p.costo, q.costo),
            semplici=(p.semplice, q.semplice),
            sicure=(p.sicura, q.sicura))

    # ── fibre e ordinamenti ──────────────────────────────────────────────────
    def fibra_bersaglio(self, carta: int, bersaglio: int) -> FibraBersaglio:
        """Tutte le procedure con T[carta] = bersaglio, raggruppate per T."""
        c = valida_indice(carta, 27, nome="carta")
        t = valida_indice(bersaglio, 27, nome="bersaglio")
        gruppi = tuple(GruppoTrasformazione(T, self._classi[T])
                       for T in self._trasformazioni if T[c] == t)
        return FibraBersaglio(c, t, gruppi)

    @staticmethod
    def ordina(procedure, chiave) -> Tuple[ProceduraGioco, ...]:
        """Ordina secondo una chiave dichiarata (usare chiavi chiuse da (m, #))."""
        return tuple(sorted(procedure, key=chiave))

    def procedura_storica(self, carta: int, bersaglio: int) -> ProceduraGioco:
        """argmin di (k1, #) fra le procedure semplici della fibra (DP5).

        Coincide con `gioco_reale.risolvi_trucco`, che resta il solutore
        usato dall'interfaccia.
        """
        semplici = self.fibra_bersaglio(carta, bersaglio).semplici
        return min(semplici, key=chiave_storica)

    def procedura_sicura(self, carta: int, bersaglio: int) -> ProceduraGioco:
        """argmin di (k3, k2, k1, m, #) sull'intera fibra: variante distinta."""
        return min(self.fibra_bersaglio(carta, bersaglio).procedure,
                   key=chiave_sicura)


@lru_cache(maxsize=1)
def servizio_procedure() -> ServizioProcedure:
    """Istanza condivisa, costruita al primo uso."""
    return ServizioProcedure()
