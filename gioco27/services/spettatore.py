"""Lo spettatore con la carta ignota: dinamica informativa (compartimento I4).

Due dinamiche distinte (libro § 11.11.5; articolo, App. A):

* **fisica** — il mazzo: a ogni fase una distribuzione e una raccolta, cioe'
  una permutazione biiettiva delle 27 posizioni. Nulla si perde: la
  trasformazione eseguita resta invertibile;
* **informativa** — cio' che l'esecutore sa: l'insieme delle **posizioni
  iniziali** compatibili con le risposte ricevute si restringe 27 → 9 → 3 → 1.

Nel 27 le risposte rivelano le cifre della posizione iniziale dalla fine
(Prop. 1.6, A11): la risposta k e' ``n_{k-1}``, e dopo tre risposte
``n = a1 + 3 a2 + 9 a3`` (§ 7.1.11). La storia non dipende dalle raccolte;
la destinazione invece si': e' il protocollo **adattivo** che, dopo ogni
risposta, colloca il mazzetto indicato nella sede della cifra del bersaglio,
con l'unica regola per fase del programma
(`gioco_reale.mescolamento_per_colonna`, estratta da `risolvi_trucco` in I3).

Il service non conosce la carta pensata: la raccolta dipende soltanto da
bersaglio, fase e risposta (`scelta_raccolta`). Niente Tk, niente testo.

Modalita' (§ 7.2.2 B1 e § 7.2.13 B12)
-------------------------------------

* ordine iniziale **noto** (B1): dopo tre risposte si conoscono la posizione
  iniziale e, leggendo il mazzo iniziale, la carta;
* ordine iniziale **ignoto** (B12): tre raccolte osservate, riavvolte con
  T⁻¹ realizzato come (R) (`tabellone.ritorno`); poi tre interrogazioni con
  il mazzetto indicato al centro, bersaglio 13. Si determinano la posizione
  della carta nel mazzo riavvolto e la sua posizione finale (13), **non** la
  sua identita'.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import FrozenSet, Optional, Tuple

from ..core import gioco_reale as _gr
from ..core.dominio import valida_indice, valida_permutazione
from . import tabellone as _tb
from .procedure import ProceduraGioco

__all__ = [
    "Modalita", "CENTRO", "RispostaNonAccettata", "SessioneSpettatore",
    "PassoInformativo", "Ricostruzione", "RiavvolgimentoB12",
    "avvia_spettatore", "avvia_b12", "scelta_raccolta", "rispondi",
    "risposte_possibili", "esegui_raccolta", "ordine_corrente",
    "distribuzione_corrente", "posizioni_iniziali_candidate",
    "posizione_iniziale_determinata", "carta_determinata",
    "posizioni_correnti_dei_candidati", "storia_informativa", "esito",
    "lettera_mazzetto",
]

Terna = Tuple[int, int, int]

#: B12: «raccolgo in mezzo il mazzetto che contiene la carta» → posizione 13
CENTRO = 13


class Modalita(str, Enum):
    ORDINE_NOTO = "ordine_noto"          # B1
    ORDINE_IGNOTO = "ordine_ignoto"      # B12


class RispostaNonAccettata(ValueError):
    """Un passo che il protocollo non accetta, con `codice` stabile.

    Come `procedure.ProceduraNonValida`: messaggio neutro, `codice` e `dati`
    per chi compone la frase nella lingua dell'interfaccia. Codici:
    ``risposta_fuori_dominio``, ``risposta_incoerente`` (eliminerebbe tutti
    i candidati), ``raccolta_in_sospeso``, ``risposta_mancante``,
    ``sessione_conclusa``, ``raccolta_fuori_dominio``.
    """

    def __init__(self, messaggio, *, codice, **dati):
        super().__init__(messaggio)
        self.codice = codice
        self.dati = dati


# ═══════════════════════════════ sessione ═══════════════════════════════════

@dataclass(frozen=True)
class SessioneSpettatore:
    """Solo i fatti: bersaglio, risposte, raccolte eseguite, mazzo iniziale.

    Tutto il resto (mazzo corrente, candidati, posizione determinata, carta)
    si **deriva** da questi campi. Nessun campo contiene la carta pensata.

    `mazzo_iniziale[p]` e' la carta in posizione p all'inizio; None se
    l'ordine iniziale non e' noto (B12). `raccolte` sono i mescolamenti
    eseguiti (sigla funzionale), uno per fase conclusa.
    """

    bersaglio: int
    mazzo_iniziale: Optional[Tuple[int, ...]] = None
    risposte: Tuple[int, ...] = ()
    raccolte: Tuple[str, ...] = ()

    @property
    def modalita(self) -> Modalita:
        return (Modalita.ORDINE_IGNOTO if self.mazzo_iniziale is None
                else Modalita.ORDINE_NOTO)

    @property
    def fase(self) -> int:
        """Fasi concluse (0..3): distribuzione, risposta e raccolta."""
        return len(self.raccolte)

    @property
    def in_attesa_della_raccolta(self) -> bool:
        return len(self.risposte) > len(self.raccolte)

    @property
    def conclusa(self) -> bool:
        return len(self.raccolte) == 3

    def cifra_bersaglio(self, fase: int) -> int:
        """La sede della fase (1..3): t0, t1, t2 nell'ordine del tempo."""
        return _gr.digits3(self.bersaglio)[3 - fase]


def avvia_spettatore(bersaglio, mazzo_iniziale=None) -> SessioneSpettatore:
    """Sessione con X0 = {0, …, 26}. `mazzo_iniziale` None = ordine ignoto."""
    bersaglio = valida_indice(bersaglio, 27, nome="bersaglio")
    if mazzo_iniziale is not None:
        mazzo_iniziale = valida_permutazione(mazzo_iniziale, 27,
                                             nome="mazzo_iniziale")
    return SessioneSpettatore(bersaglio=bersaglio, mazzo_iniziale=mazzo_iniziale)


# ═══════════════════════════ dinamica fisica ════════════════════════════════

def ordine_corrente(s: SessioneSpettatore) -> Tuple[int, ...]:
    """Il mazzo dopo le raccolte eseguite, per **posizione iniziale**.

    ``ordine_corrente(s)[p]`` = posizione iniziale della carta che ora sta in
    p. E' una permutazione: la dinamica fisica non perde nulla.
    """
    deck = list(range(27))
    for m in s.raccolte:
        deck = _gr.raccogli(_gr.distribuisci(deck), m)
    return tuple(deck)


def distribuzione_corrente(s: SessioneSpettatore):
    """I tre mazzetti della distribuzione della fase in corso (None a fine)."""
    if s.conclusa:
        return None
    return tuple(tuple(c) for c in _gr.distribuisci(ordine_corrente(s)))


def _distribuzione_della_fase(s, fase):
    deck = list(range(27))
    for m in s.raccolte[:fase - 1]:
        deck = _gr.raccogli(_gr.distribuisci(deck), m)
    return _gr.distribuisci(deck)


# ═════════════════════════ dinamica informativa ═════════════════════════════

def posizioni_iniziali_candidate(s: SessioneSpettatore) -> FrozenSet[int]:
    """X_k: le posizioni **iniziali** compatibili con le k risposte.

    Si calcola dalla fisica — le carte del mazzetto indicato alla fase k,
    lette per posizione iniziale — non dall'aritmetica delle cifre.
    """
    x = frozenset(range(27))
    for k, a in enumerate(s.risposte, start=1):
        x &= frozenset(_distribuzione_della_fase(s, k)[a])
    return x


def posizione_iniziale_determinata(s: SessioneSpettatore) -> Optional[int]:
    x = posizioni_iniziali_candidate(s)
    return next(iter(x)) if len(x) == 1 else None


def carta_determinata(s: SessioneSpettatore) -> Optional[int]:
    """La carta, se la posizione e' unica **e** l'ordine iniziale e' noto."""
    n = posizione_iniziale_determinata(s)
    if n is None or s.mazzo_iniziale is None:
        return None
    return s.mazzo_iniziale[n]


def posizioni_correnti_dei_candidati(s: SessioneSpettatore) -> FrozenSet[int]:
    """Dove stanno ORA le carte candidate: l'immagine biiettiva di X_k."""
    x = posizioni_iniziali_candidate(s)
    return frozenset(p for p, n in enumerate(ordine_corrente(s)) if n in x)


def risposte_possibili(s: SessioneSpettatore) -> Tuple[int, ...]:
    """Le risposte che non svuotano l'insieme dei candidati."""
    if s.conclusa or s.in_attesa_della_raccolta:
        return ()
    x = posizioni_iniziali_candidate(s)
    return tuple(a for a in range(3)
                 if x & frozenset(distribuzione_corrente(s)[a]))


# ═════════════════════════ protocollo adattivo ══════════════════════════════

def scelta_raccolta(bersaglio: int, fase: int, risposta: int) -> str:
    """Il mescolamento che colloca il mazzetto indicato nella sede t_{fase}.

    Dipende solo da bersaglio, fase e risposta: la carta pensata non entra.
    E' la regola per fase di `risolvi_trucco` (una sola regola autorevole).
    """
    bersaglio = valida_indice(bersaglio, 27, nome="bersaglio")
    if fase not in (1, 2, 3):
        raise ValueError(f"fase fuori da 1..3: {fase!r}")
    return _gr.mescolamento_per_colonna(risposta, _gr.digits3(bersaglio)[3 - fase])


def rispondi(s: SessioneSpettatore, risposta) -> SessioneSpettatore:
    """Registra il mazzetto (0 = S, 1 = C, 2 = D) indicato dallo spettatore."""
    if s.conclusa:
        raise RispostaNonAccettata("sessione conclusa", codice="sessione_conclusa")
    if s.in_attesa_della_raccolta:
        raise RispostaNonAccettata("prima va eseguita la raccolta",
                                   codice="raccolta_in_sospeso", fase=s.fase + 1)
    if isinstance(risposta, bool) or risposta not in (0, 1, 2):
        raise RispostaNonAccettata(f"risposta fuori da 0..2: {risposta!r}",
                                   codice="risposta_fuori_dominio",
                                   risposta=risposta)
    if risposta not in risposte_possibili(s):
        raise RispostaNonAccettata(
            "la risposta non lascia alcuna posizione iniziale candidata",
            codice="risposta_incoerente", risposta=risposta, fase=s.fase + 1)
    return replace(s, risposte=s.risposte + (int(risposta),))


def esegui_raccolta(s: SessioneSpettatore, mescolamento: Optional[str] = None
                    ) -> SessioneSpettatore:
    """Il gesto fisico della fase. Senza argomento: la scelta adattiva.

    Un mescolamento esplicito e' ammesso (per osservare che l'identificazione
    non dipende dalle raccolte), ma allora il bersaglio non e' garantito.
    """
    if s.conclusa:
        raise RispostaNonAccettata("sessione conclusa", codice="sessione_conclusa")
    if not s.in_attesa_della_raccolta:
        raise RispostaNonAccettata("manca la risposta della fase",
                                   codice="risposta_mancante", fase=s.fase + 1)
    fase = s.fase + 1
    if mescolamento is None:
        mescolamento = scelta_raccolta(s.bersaglio, fase, s.risposte[-1])
    elif mescolamento not in _gr.MESCOLAMENTO:
        raise RispostaNonAccettata(f"sigla sconosciuta: {mescolamento!r}",
                                   codice="raccolta_fuori_dominio",
                                   mescolamento=mescolamento)
    return replace(s, raccolte=s.raccolte + (mescolamento,))


# ═══════════════════════════════ letture ════════════════════════════════════

@dataclass(frozen=True)
class PassoInformativo:
    """Una fase vista dall'esecutore: risposta, candidati, cifra, gesto."""

    fase: int                               # 1..3
    risposta: int                           # a_fase
    indice_cifra: int                       # 0 → n0, 1 → n1, 2 → n2
    candidati_prima: FrozenSet[int]         # posizioni iniziali
    candidati_dopo: FrozenSet[int]
    sede: int                               # cifra del bersaglio della fase
    raccolta: Optional[str]                 # mescolamento eseguito, se c'e'
    adattiva: Optional[bool]                # e' la scelta del protocollo?

    @property
    def impilamento(self) -> Optional[str]:
        return None if self.raccolta is None else _gr.IMPILAMENTO_DI[self.raccolta]


def storia_informativa(s: SessioneSpettatore) -> Tuple[PassoInformativo, ...]:
    passi = []
    prima = frozenset(range(27))
    for k, a in enumerate(s.risposte, start=1):
        parziale = replace(s, risposte=s.risposte[:k], raccolte=s.raccolte[:k - 1])
        dopo = posizioni_iniziali_candidate(parziale)
        raccolta = s.raccolte[k - 1] if len(s.raccolte) >= k else None
        passi.append(PassoInformativo(
            fase=k, risposta=a, indice_cifra=k - 1, candidati_prima=prima,
            candidati_dopo=dopo, sede=s.cifra_bersaglio(k), raccolta=raccolta,
            adattiva=(None if raccolta is None
                      else raccolta == scelta_raccolta(s.bersaglio, k, a))))
        prima = dopo
    return tuple(passi)


def lettera_mazzetto(colonna: int) -> str:
    """Nome del mazzetto: l'ultima lettera della parola-indirizzo (I2)."""
    return _gr.parola(colonna)[-1]


@dataclass(frozen=True)
class Ricostruzione:
    """Identificazione (dalle risposte) e controllo della destinazione."""

    modalita: Modalita
    risposte: Terna                         # (a1, a2, a3) nel tempo
    storia: str                             # parola delle risposte nel tempo
    posizione_iniziale: int                 # n
    cifre: Terna                            # (n2, n1, n0) = digits3(n)
    parola: str                             # ω(n) = rev(storia)
    carta: Optional[int]                    # None se l'ordine iniziale e' ignoto
    raccolte: Tuple[str, str, str]
    procedura: ProceduraGioco
    numero_disposizione: int
    bersaglio: int
    posizione_finale: int                   # dove si trova ora la carta
    bersaglio_raggiunto: bool
    protocollo_adattivo: bool               # tutte le raccolte erano la scelta?


def esito(s: SessioneSpettatore) -> Optional[Ricostruzione]:
    """La ricostruzione finale; None finche' la sessione non e' conclusa."""
    if not s.conclusa:
        return None
    storia = "".join(lettera_mazzetto(a) for a in s.risposte)
    n = _gr.posizione_da_parola(storia[::-1])            # I2: ω⁻¹
    if posizioni_iniziali_candidate(s) != frozenset((n,)):
        raise AssertionError("fisica e ricostruzione ternaria divergono")
    finale = ordine_corrente(s).index(n)
    return Ricostruzione(
        modalita=s.modalita, risposte=tuple(s.risposte), storia=storia,
        posizione_iniziale=n, cifre=_gr.digits3(n), parola=_gr.parola(n),
        carta=carta_determinata(s), raccolte=tuple(s.raccolte),
        procedura=ProceduraGioco(tuple(s.raccolte)),
        numero_disposizione=_gr.numero_tavola(s.raccolte),
        bersaglio=s.bersaglio, posizione_finale=finale,
        bersaglio_raggiunto=(finale == s.bersaglio),
        protocollo_adattivo=all(p.adattiva for p in storia_informativa(s)))


# ═══════════════════════════════ B12 ════════════════════════════════════════

@dataclass(frozen=True)
class RiavvolgimentoB12:
    """§ 7.2.13: dalle raccolte osservate al mazzo riavvolto.

    Si osservano gli impilamenti R0, R1, R2; i mescolamenti sono
    ``M_i = R_i⁻¹``; la disposizione osservata ha tabellone T; il
    riavvolgimento esegue la procedura (R) di T⁻¹ (`tabellone.ritorno`).
    """

    impilamenti_osservati: Tuple[str, str, str]

    @property
    def mescolamenti_osservati(self) -> Tuple[str, str, str]:
        return tuple(_gr.IMPILAMENTO_DI[r] for r in self.impilamenti_osservati)

    @property
    def numero_osservato(self) -> int:
        return _gr.numero_tavola(self.mescolamenti_osservati)

    @property
    def ritorno(self) -> ProceduraGioco:
        return _tb.ritorno(self.numero_osservato)

    @property
    def numero_ritorno(self) -> int:
        return self.ritorno.numero_tavola

    @property
    def impilamenti_di_ritorno(self) -> Tuple[str, str, str]:
        return tuple(_gr.IMPILAMENTO_DI[m] for m in self.ritorno.mescolamenti)


def avvia_b12(impilamenti_osservati):
    """Riavvolgimento e sessione d'interrogazione (ordine ignoto, bersaglio 13).

    Le posizioni «iniziali» della sessione sono quelle del mazzo riavvolto,
    cioe' del mazzo com'era prima delle raccolte osservate.
    """
    oss = tuple(impilamenti_osservati)
    if len(oss) != 3 or any(r not in _gr.MESCOLAMENTO for r in oss):
        raise RispostaNonAccettata(f"impilamenti osservati non validi: {oss!r}",
                                   codice="raccolta_fuori_dominio",
                                   impilamenti=oss)
    return RiavvolgimentoB12(oss), avvia_spettatore(CENTRO)
