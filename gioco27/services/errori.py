"""Errori fisici, confronto piano/eseguito e recupero (compartimento I3).

Un piccolo service puro sopra le primitive fisiche del core
(`gioco_reale.distribuisci`, `raccogli`, `mescolamento_per_colonna`) e sopra
I1/I2 (`services.procedure`, `services.tabellone`). Niente Tk, niente I/O,
niente testo per l'utente: codici stabili (E1…E6) e dati immutabili.

Catalogo (docs/audits/V4_MATHEMATICAL_DIDACTIC_COVERAGE_AUDIT.md § 14.3; D-I3-1/2)
------------------------------------------------------------------------

E1  mescolamento usato come impilamento: solo CDS/DSC, si esegue l'inversa
E2  rovesciamento dell'intero mazzo DOPO la raccolta della fase
E3  ordine interno dei tre mazzetti invertito, fra distribuzione e raccolta
E4  colonna indicata diversa da quella reale della carta tracciata
E5  impilamento sbagliato che non e' E1
E6  taglio non registrato: solo catalogo e diagnostica, nessuna mossa

Ordine fisico di una fase (§ 4 del compito, deterministico)
-----------------------------------------------------------

1. distribuzione del mazzo corrente;
2. E3: ogni mazzetto invertito al suo interno;
3. osservazione della colonna reale della carta tracciata;
4. E4: l'esecutore usa la colonna indicata al posto di quella reale;
5. mescolamento inteso: quello del piano; con E4 in una sessione guidata dal
   bersaglio, la regola per fase di `risolvi_trucco`
   (`gioco_reale.mescolamento_per_colonna`) applicata alla colonna indicata;
6. impilamento scelto (per default quello corretto per il mescolamento inteso);
7. E1/E5 se l'impilamento differisce da quello corretto;
8. raccolta fisica: impilare la sigla X esegue il mescolamento inverso di X;
9. E2: rovesciamento del mazzo dopo la raccolta (alla fase 3 e' J ∘ T).

La sequenza fisica e' **una**: T_eseguita e' la permutazione che quella stessa
sequenza di gesti induce sull'intero mazzo. E2 non viene normalizzato in una
procedura canonica: la riga che realizza la stessa T si cerca dopo, a fini
diagnostici (`services.tabellone.numero_di`).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Optional, Tuple

from ..core import gioco_reale as _gr
from ..core.dominio import valida_indice
from . import tabellone as _tb
from .procedure import ProceduraGioco, servizio_procedure

__all__ = [
    "TipoErrore", "VoceCatalogo", "CATALOGO", "GestiFase", "EventoErrore",
    "SessioneErrori", "PassoEseguito", "StatoEsecuzione", "TracciaEseguita",
    "ConfrontoPianoEseguito", "OpzioneRecupero", "EsitoRitorno",
    "avvia", "esegui_fase", "esegui", "traccia", "confronta",
    "colonna_reale", "mescolamento_inteso", "cifre_cambiate", "traccia_prevista",
    "recuperi", "applica_recupero", "ritorno_eseguito",
]

Terna = Tuple[int, int, int]


class TipoErrore(str, Enum):
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"
    E6 = "E6"


@dataclass(frozen=True)
class VoceCatalogo:
    """Una voce del catalogo: dati, nessuna frase."""

    tipo: TipoErrore
    fasi: Tuple[int, ...]           # fasi in cui puo' accadere nella simulazione
    simulato: bool                  # applicato davvero al mazzo
    resta_nella_tavola: bool        # T resta fra le 216 disposizioni (misurato)


CATALOGO = {
    TipoErrore.E1: VoceCatalogo(TipoErrore.E1, (1, 2, 3), True, True),
    TipoErrore.E2: VoceCatalogo(TipoErrore.E2, (1, 2, 3), True, True),
    TipoErrore.E3: VoceCatalogo(TipoErrore.E3, (1, 2, 3), True, True),
    TipoErrore.E4: VoceCatalogo(TipoErrore.E4, (1, 2, 3), True, True),
    TipoErrore.E5: VoceCatalogo(TipoErrore.E5, (1, 2, 3), True, True),
    # E6: in generale fuori dalle 216 (le traslazioni di 9 e 18 fanno eccezione:
    # agiscono sulla sola cifra n2). Nessuna mossa di produzione (DP10 aperta).
    TipoErrore.E6: VoceCatalogo(TipoErrore.E6, (), False, False),
}


# ═══════════════════════════════ modelli ════════════════════════════════════

@dataclass(frozen=True)
class GestiFase:
    """Che cosa fa davvero l'esecutore in una fase (None = il gesto corretto)."""

    colonna_indicata: Optional[int] = None     # E4 se diversa dalla reale
    impilamento: Optional[str] = None          # E1/E5 se diverso dal corretto
    ordine_interno_invertito: bool = False     # E3
    rovesciamento_dopo: bool = False           # E2


@dataclass(frozen=True)
class EventoErrore:
    fase: int
    tipo: TipoErrore
    colonna_reale: Optional[int] = None
    colonna_indicata: Optional[int] = None
    impilamento_corretto: Optional[str] = None
    impilamento_eseguito: Optional[str] = None


@dataclass(frozen=True)
class SessioneErrori:
    """Carta tracciata, bersaglio e piano congelati.

    `guidata_dal_bersaglio`: il piano viene dal trucco (`risolvi_trucco`) e la
    scelta di una fase dipende dalla colonna creduta; con una disposizione
    fissata (D-I3-7) il piano non dipende dalla colonna.
    """

    carta: int
    bersaglio: int
    mescolamenti: Tuple[str, str, str]
    guidata_dal_bersaglio: bool = True

    @classmethod
    def da_trucco(cls, carta, bersaglio):
        carta = valida_indice(carta, 27, nome="carta")
        bersaglio = valida_indice(bersaglio, 27, nome="bersaglio")
        piano = _gr.risolvi_trucco(carta, bersaglio)
        return cls(carta, bersaglio, tuple(piano["mescolamenti"]), True)

    @classmethod
    def da_disposizione(cls, numero, carta):
        """Piano fissato dalla riga della Tavola: bersaglio = T[carta]."""
        riga = _gr.riga_tavola(valida_indice(numero, 216, nome="numero_tavola"))
        carta = valida_indice(carta, 27, nome="carta")
        return cls(carta, riga["T"][carta], tuple(riga["mescolamenti"]), False)

    @property
    def procedura(self) -> ProceduraGioco:
        return ProceduraGioco(self.mescolamenti)

    def cifra_bersaglio(self, fase: int) -> int:
        """La cifra che la fase deve scrivere: b0 alla fase 1, b2 alla fase 3."""
        return _gr.digits3(self.bersaglio)[3 - fase]


@dataclass(frozen=True)
class PassoEseguito:
    fase: int
    mazzo_prima: Tuple[int, ...]
    colonne: Tuple[Tuple[int, ...], ...]       # dopo l'eventuale E3
    colonna_reale: int
    colonna_indicata: int
    mescolamento_previsto: str                 # del piano (corrente)
    mescolamento_inteso: str                   # quello che l'esecutore vuole fare
    impilamento_corretto: str                  # per il mescolamento inteso
    impilamento_eseguito: str
    mescolamento_eseguito: str                 # effetto fisico dell'impilamento
    ordine_interno_invertito: bool
    rovesciamento_dopo: bool
    mazzo_dopo: Tuple[int, ...]
    posizione_prima: int
    posizione_dopo: int
    eventi: Tuple[EventoErrore, ...]


@dataclass(frozen=True)
class StatoEsecuzione:
    sessione: SessioneErrori
    piano_corrente: Tuple[str, str, str]       # cambia solo con un recupero
    mazzo: Tuple[int, ...]
    passi: Tuple[PassoEseguito, ...] = ()

    @property
    def fase_corrente(self) -> int:
        return len(self.passi) + 1

    @property
    def completata(self) -> bool:
        return len(self.passi) == 3

    @property
    def posizione_carta(self) -> int:
        return self.mazzo.index(self.sessione.carta)

    def colonne(self):
        """Le tre colonne della prossima distribuzione (per la vista)."""
        return tuple(tuple(c) for c in _gr.distribuisci(list(self.mazzo)))


@dataclass(frozen=True)
class TracciaEseguita:
    sessione: SessioneErrori
    piano_eseguito: Tuple[str, str, str]       # piano corrente alla fine
    passi: Tuple[PassoEseguito, ...]
    mazzo_finale: Tuple[int, ...]
    T_eseguita: Tuple[int, ...]

    @property
    def eventi(self) -> Tuple[EventoErrore, ...]:
        return tuple(e for p in self.passi for e in p.eventi)

    @property
    def posizione_carta(self) -> int:
        return self.T_eseguita[self.sessione.carta]


@dataclass(frozen=True)
class ConfrontoPianoEseguito:
    """Previsto contro eseguito, senza la parola «equivalente» (D-I3-6)."""

    carta: int
    bersaglio: int
    procedura_prevista: ProceduraGioco
    T_prevista: Tuple[int, ...]
    numero_previsto: int
    posizione_prevista: int
    gesti_eseguiti: Tuple[str, str, str]       # mescolamenti realmente eseguiti
    T_eseguita: Tuple[int, ...]
    numero_eseguito: Optional[int]             # None: fuori dalla Tavola
    posizione_eseguita: int
    mazzo_finale: Tuple[int, ...]
    bersaglio_raggiunto: bool
    stessa_trasformazione: bool
    stesso_effetto_carta: bool
    cifre_previste: Terna
    cifre_eseguite: Terna
    cifre_cambiate: Tuple[int, ...]            # indici fra 2, 1, 0 (n2, n1, n0)
    fasi_divergenti: Tuple[int, ...]
    eventi: Tuple[EventoErrore, ...]
    piano_modificato: bool                     # e' stato applicato un recupero

    @property
    def realizzabile_da_riga(self) -> Optional[int]:
        """La riga che realizza intenzionalmente T_eseguita, se esiste."""
        return self.numero_eseguito


@dataclass(frozen=True)
class OpzioneRecupero:
    dopo_fase: int
    suffisso: Tuple[str, ...]
    posizione_finale: int
    raggiunge_bersaglio: bool
    modifiche: int                             # fasi cambiate rispetto al piano
    raccolte_non_scd: int


@dataclass(frozen=True)
class EsitoRitorno:
    numero_eseguito: Optional[int]
    procedura: Optional[ProceduraGioco]        # None se T e' fuori dalla Tavola
    numero_ritorno: Optional[int]

    @property
    def disponibile(self) -> bool:
        return self.procedura is not None


# ═══════════════════════════════ esecuzione ═════════════════════════════════

def avvia(sessione: SessioneErrori) -> StatoEsecuzione:
    return StatoEsecuzione(sessione, tuple(sessione.mescolamenti),
                           tuple(range(27)))


def _valida_gesti(g: GestiFase) -> GestiFase:
    if not isinstance(g, GestiFase):
        raise TypeError("attesi GestiFase")
    if g.colonna_indicata is not None:
        valida_indice(g.colonna_indicata, 3, nome="colonna_indicata")
    if g.impilamento is not None and g.impilamento not in _gr.MESCOLAMENTO:
        raise ValueError(f"impilamento sconosciuto: {g.impilamento!r}")
    return g


def esegui_fase(stato: StatoEsecuzione, gesti: GestiFase = GestiFase()
                ) -> StatoEsecuzione:
    """Esegue la fase corrente con i gesti dati, nell'ordine fisico del modulo."""
    if stato.completata:
        raise ValueError("le tre fasi sono gia' state eseguite")
    g = _valida_gesti(gesti)
    s = stato.sessione
    fase = stato.fase_corrente
    eventi = []
    colonne = [list(c) for c in _gr.distribuisci(list(stato.mazzo))]   # 1
    if g.ordine_interno_invertito:                                      # 2
        colonne = [list(reversed(c)) for c in colonne]
        eventi.append(EventoErrore(fase, TipoErrore.E3))
    reale = next(k for k in range(3) if s.carta in colonne[k])          # 3
    indicata = reale if g.colonna_indicata is None else g.colonna_indicata
    previsto = stato.piano_corrente[fase - 1]
    if indicata != reale:                                               # 4
        eventi.append(EventoErrore(fase, TipoErrore.E4, colonna_reale=reale,
                                   colonna_indicata=indicata))
    inteso = mescolamento_inteso(stato, indicata)                       # 5
    corretto = _gr.IMPILAMENTO_DI[inteso]
    impilato = corretto if g.impilamento is None else g.impilamento     # 6
    if impilato != corretto:                                            # 7
        tipo = (TipoErrore.E1 if impilato == inteso and inteso != corretto
                else TipoErrore.E5)
        eventi.append(EventoErrore(fase, tipo, impilamento_corretto=corretto,
                                   impilamento_eseguito=impilato))
    eseguito = _gr.IMPILAMENTO_DI[impilato]                             # 8
    mazzo = _gr.raccogli(colonne, eseguito, bool(g.rovesciamento_dopo)) # 9
    if g.rovesciamento_dopo:
        eventi.append(EventoErrore(fase, TipoErrore.E2))
    passo = PassoEseguito(
        fase=fase, mazzo_prima=stato.mazzo,
        colonne=tuple(tuple(c) for c in colonne), colonna_reale=reale,
        colonna_indicata=indicata, mescolamento_previsto=previsto,
        mescolamento_inteso=inteso, impilamento_corretto=corretto,
        impilamento_eseguito=impilato, mescolamento_eseguito=eseguito,
        ordine_interno_invertito=bool(g.ordine_interno_invertito),
        rovesciamento_dopo=bool(g.rovesciamento_dopo), mazzo_dopo=tuple(mazzo),
        posizione_prima=stato.posizione_carta,
        posizione_dopo=mazzo.index(s.carta), eventi=tuple(eventi))
    return replace(stato, mazzo=tuple(mazzo), passi=stato.passi + (passo,))


def colonna_reale(stato: StatoEsecuzione) -> int:
    """La colonna in cui cade davvero la carta nella prossima distribuzione.

    L'eventuale E3 non la cambia: inverte l'ordine dentro i mazzetti, non il
    mazzetto in cui sta la carta.
    """
    carta = stato.sessione.carta
    return next(k for k, c in enumerate(stato.colonne()) if carta in c)


def mescolamento_inteso(stato: StatoEsecuzione, colonna_indicata=None) -> str:
    """Il mescolamento che l'esecutore adotta nella fase corrente.

    Quello del piano; se la colonna indicata differisce dalla reale (E4) e la
    sessione e' guidata dal bersaglio, la regola per fase del trucco
    (`gioco_reale.mescolamento_per_colonna`) applicata alla colonna indicata.
    Un piano fissato (D-I3-7) non dipende dalla colonna.
    """
    fase = stato.fase_corrente
    previsto = stato.piano_corrente[fase - 1]
    if colonna_indicata is None:
        return previsto
    indicata = valida_indice(colonna_indicata, 3, nome="colonna_indicata")
    s = stato.sessione
    if indicata != colonna_reale(stato) and s.guidata_dal_bersaglio:
        return _gr.mescolamento_per_colonna(indicata, s.cifra_bersaglio(fase))
    return previsto


def cifre_cambiate(prevista: int, eseguita: int) -> Tuple[int, ...]:
    """Indici (2 = n2, 1 = n1, 0 = n0) delle cifre ternarie che differiscono."""
    cp, ce = _gr.digits3(prevista), _gr.digits3(eseguita)
    return tuple(2 - i for i in range(3) if cp[i] != ce[i])


def traccia_prevista(sessione: SessioneErrori) -> TracciaEseguita:
    """La traccia del piano senza errori: il termine di confronto di ogni fase."""
    return esegui(sessione, (GestiFase(),) * 3)


def traccia(stato: StatoEsecuzione) -> TracciaEseguita:
    if not stato.completata:
        raise ValueError("la traccia e' definita dopo le tre fasi")
    mazzo = stato.mazzo
    return TracciaEseguita(stato.sessione, stato.piano_corrente, stato.passi,
                           mazzo, tuple(mazzo.index(c) for c in range(27)))


def esegui(sessione: SessioneErrori, gesti) -> TracciaEseguita:
    """Le tre fasi con i gesti dati (una GestiFase per fase)."""
    gesti = tuple(gesti)
    if len(gesti) != 3:
        raise ValueError("servono esattamente tre GestiFase")
    stato = avvia(sessione)
    for g in gesti:
        stato = esegui_fase(stato, g)
    return traccia(stato)


# ═══════════════════════════════ confronto ══════════════════════════════════

def confronta(tr: TracciaEseguita) -> ConfrontoPianoEseguito:
    s = tr.sessione
    procedura = s.procedura
    T_prevista = tuple(servizio_procedure().trasformazione(procedura))
    prevista = T_prevista[s.carta]
    eseguita = tr.posizione_carta
    cp, ce = _gr.digits3(prevista), _gr.digits3(eseguita)
    return ConfrontoPianoEseguito(
        carta=s.carta, bersaglio=s.bersaglio, procedura_prevista=procedura,
        T_prevista=T_prevista, numero_previsto=procedura.numero_tavola,
        posizione_prevista=prevista,
        gesti_eseguiti=tuple(p.mescolamento_eseguito for p in tr.passi),
        T_eseguita=tr.T_eseguita, numero_eseguito=_tb.numero_di(tr.T_eseguita),
        posizione_eseguita=eseguita, mazzo_finale=tr.mazzo_finale,
        bersaglio_raggiunto=eseguita == s.bersaglio,
        stessa_trasformazione=tr.T_eseguita == T_prevista,
        stesso_effetto_carta=eseguita == prevista,
        cifre_previste=cp, cifre_eseguite=ce,
        cifre_cambiate=cifre_cambiate(prevista, eseguita),
        fasi_divergenti=tuple(p.fase for p in tr.passi if p.eventi),
        eventi=tr.eventi,
        piano_modificato=tr.piano_eseguito != tuple(s.mescolamenti))


# ═══════════════════════════════ recupero ═══════════════════════════════════

def _prosegui(mazzo, suffisso):
    """Il mazzo dopo le fasi residue eseguite correttamente."""
    mazzo = list(mazzo)
    for sigla in suffisso:
        mazzo = _gr.raccogli(_gr.distribuisci(mazzo), sigla)
    return mazzo


def _suffissi(lunghezza):
    """Tutti i suffissi, nell'ordine stabile delle SIGLE del core."""
    if lunghezza == 0:
        return [()]
    return [(s,) + resto for s in _gr.SIGLE for resto in _suffissi(lunghezza - 1)]


def recuperi(stato: StatoEsecuzione) -> Tuple[OpzioneRecupero, ...]:
    """Recupero A: le continuazioni che portano ancora la carta al bersaglio.

    Ricerca esaustiva sulle sole fasi residue (36 o 6 suffissi), eseguite
    correttamente. Ordine: meno modifiche al piano residuo, meno raccolte
    diverse da SCD, poi l'ordine delle SIGLE. Non e' una strategia globale.
    """
    fatte = len(stato.passi)
    if fatte == 0 or stato.completata:
        return ()
    residuo = stato.piano_corrente[fatte:]
    s = stato.sessione
    opzioni = []
    for suffisso in _suffissi(3 - fatte):
        finale = _prosegui(stato.mazzo, suffisso).index(s.carta)
        if finale != s.bersaglio:
            continue
        opzioni.append(OpzioneRecupero(
            dopo_fase=fatte, suffisso=suffisso, posizione_finale=finale,
            raggiunge_bersaglio=True,
            modifiche=sum(a != b for a, b in zip(suffisso, residuo)),
            raccolte_non_scd=sum(x != "SCD" for x in suffisso)))
    return tuple(sorted(opzioni, key=lambda o: (
        o.modifiche, o.raccolte_non_scd,
        tuple(_gr.SIGLE.index(x) for x in o.suffisso))))


def applica_recupero(stato: StatoEsecuzione, opzione: OpzioneRecupero
                     ) -> StatoEsecuzione:
    """Sostituisce il piano delle fasi residue con il suffisso scelto."""
    fatte = len(stato.passi)
    if opzione.dopo_fase != fatte:
        raise ValueError("l'opzione non riguarda la fase corrente")
    piano = tuple(stato.piano_corrente[:fatte]) + tuple(opzione.suffisso)
    return replace(stato, piano_corrente=piano)


def ritorno_eseguito(tr: TracciaEseguita) -> EsitoRitorno:
    """Recupero B: la riga che realizza T_eseguita⁻¹ (I2), se T_eseguita e' in Tavola."""
    numero = _tb.numero_di(tr.T_eseguita)
    if numero is None:
        return EsitoRitorno(None, None, None)
    procedura = _tb.ritorno(numero)
    return EsitoRitorno(numero, procedura, procedura.numero_tavola)
