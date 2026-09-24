"""Presenter del tabellone e del livello ternario (compartimento I2).

Dati strutturati e immutabili per le viste della Tavola: nessun testo per
l'utente (le frasi le compone la GUI con il catalogo i18n), nessun Tk, nessun
I/O, nessuno stato globale. Non c'e' un motore matematico nuovo: ogni valore
viene da un'autorita' gia' esistente.

    cifre, parole         core.gioco_reale.digits3, parola
    righe del tabellone   core.gioco_reale.riga_tavola, MESCOLAMENTO, IMPILAMENTO_DI
    T e T⁻¹               riga_tavola(n)["T"] e ["T_inv"]
    flusso di una carta   core.gioco_reale.esegui_partita (traccia fisica),
                          raggiunta per le procedure con rovesciamenti tramite
                          services.procedure.adattamento_fisico (DP3 = A)
    (R) e ritorno         services.procedure.servizio_procedure().classe_trasformazione

Convenzioni che la GUI non deve ricostruire (V4_PRE_I2_VIEW_DECISIONS.md):

* **T** (`destinazioni`): ``T[carta] = posizione finale``; e' la lettura
  gerarchica del tabellone **diretto**.
* **T⁻¹** (`mazzo_finale`): ``T⁻¹[posizione] = carta che la occupa``; e' la
  lettura del tabellone **inverso**. I due coincidono solo se T e' auto-inversa.
* **Cronologia** (`cronologia`): fase 1 → fase 2 → fase 3.
* **Griglia** (`righe`): dall'alto fase 3 (peso 9, cifra n2), fase 2 (peso 3,
  n1), fase 1 (peso 1, n0). Il tabellone inverso usa lo **stesso** ordine delle
  fasi con la sigla locale inversa (CDS ↔ DSC; le altre quattro invariate).
* **Rovesciamenti**: solo quelli canonici di una `ProceduraGioco` (J prima della
  distribuzione dello stadio). Nessun rovesciamento finale, nessun errore, e
  nessun elenco delle procedure che realizzano la stessa T (DP11 aperta).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from ..core import gioco_reale as _gr
from ..core.dominio import valida_indice
from .procedure import ProceduraGioco, adattamento_fisico, servizio_procedure

__all__ = [
    "FaseCronologica", "RigaTabellone", "ColonnaAsso", "Tabellone",
    "AzioneCifra", "LetturaCifre", "PassoFlusso", "FlussoCarta",
    "tabellone", "lettura_cifre", "tabella_posizioni", "flusso_carta",
    "flussi_procedura", "realizza", "ritorno", "numero_di",
    "disposizione_realizzata",
]

Terna = Tuple[int, int, int]

#: (fase, peso, indice della cifra) delle righe della griglia, dall'alto.
_RIGHE_VISIVE = ((3, 9, 2), (2, 3, 1), (1, 1, 0))
#: posizioni iniziali delle tre carte guida: la colonna d e' la carta (d,d,d)
_ASSI = (0, 13, 26)


# ═══════════════════════════════ modelli ════════════════════════════════════

@dataclass(frozen=True)
class FaseCronologica:
    """Una fase nell'ordine del tempo: il mescolamento e il gesto che lo esegue."""

    fase: int                 # 1, 2, 3
    mescolamento: str         # sigla funzionale (riga del tabellone)
    impilamento: str          # gesto fisico, dal dorso


@dataclass(frozen=True)
class RigaTabellone:
    """Una riga della griglia: la permutazione locale di una fase su una cifra."""

    fase: int                 # 3 in alto, 1 in basso
    peso: int                 # 9, 3, 1
    indice_cifra: int         # 2, 1, 0: la riga agisce sulla cifra n_indice
    sigla: str
    valori: Terna             # valori[d] = immagine della cifra d


@dataclass(frozen=True)
class ColonnaAsso:
    """Una colonna del tabellone letta dall'alto: la carta guida (d,d,d)."""

    colonna: int              # d = 0, 1, 2 (S, C, D)
    carta: int                # tabellone diretto: la carta 13·d …
    posizione: int            # … e la sua posizione finale.  Inverso: la
                              # posizione 13·d e la carta che vi arriva.


@dataclass(frozen=True)
class Tabellone:
    """Tabellone diretto e inverso di una disposizione della Tavola."""

    numero: int
    cronologia: Tuple[FaseCronologica, ...]
    righe: Tuple[RigaTabellone, ...]
    righe_inverse: Tuple[RigaTabellone, ...]
    colonne_assi: Tuple[ColonnaAsso, ...]
    colonne_inverse: Tuple[ColonnaAsso, ...]
    destinazioni: Tuple[int, ...]           # T
    mazzo_finale: Tuple[int, ...]           # T⁻¹
    autoinversa: bool


@dataclass(frozen=True)
class AzioneCifra:
    """Una delle tre leggi delle posizioni applicata a una cifra (§ 2.4.7)."""

    fase: int
    peso: int
    indice_cifra: int
    riga_visiva: int          # 0 in alto … 2 in basso
    sigla: str
    cifra_iniziale: int       # e' anche la colonna della cella letta
    cifra_finale: int


@dataclass(frozen=True)
class LetturaCifre:
    """Lettura cifra per cifra di una carta su un tabellone."""

    numero: int
    carta: int
    cifre_iniziali: Terna                   # (n2, n1, n0)
    parola_iniziale: str
    azioni: Tuple[AzioneCifra, ...]         # nell'ordine della griglia
    cifre_finali: Terna                     # (b2, b1, b0)
    parola_finale: str
    destinazione: int                       # n' = T[carta]

    @property
    def celle(self) -> Tuple[Tuple[int, int], ...]:
        """Le tre celle (riga visiva, colonna) da evidenziare nella griglia."""
        return tuple((a.riga_visiva, a.cifra_iniziale) for a in self.azioni)


@dataclass(frozen=True)
class PassoFlusso:
    """Una fase della macchina che dimentica, per una carta (§ 1.6, § 5.1.5)."""

    fase: int
    mescolamento: str
    impilamento: str
    rovesciamento: int                      # ε della fase (0/1), DP3 = A
    posizione_prima: int                    # P_k
    cifre_prima: Terna
    posizione_distribuita: int              # J^ε(P_k): la posizione che si distribuisce
    cifre_distribuite: Terna
    colonna: int                            # mazzetto in cui cade (cifra che esce)
    altezza: int                            # posto nel mazzetto: ⌊J^ε(P_k)/3⌋
    destinazione_blocco: int                # s_k: blocco assegnato al mazzetto
    posizione_dopo: int                     # P_{k+1}
    cifre_dopo: Terna
    complementata: bool                     # parita' di ε1+…+ε_fase dispari
    parola_prima: str
    parola_distribuita: str
    parola_dopo: str

    @property
    def lettera_colonna(self) -> str:
        """Nome del mazzetto (S, C, D): l'ultima lettera dell'indirizzo distribuito."""
        return self.parola_distribuita[2]

    @property
    def cifra_uscente(self) -> int:
        return self.colonna

    @property
    def cifra_entrante(self) -> int:
        return self.destinazione_blocco


@dataclass(frozen=True)
class FlussoCarta:
    """La carta attraverso le tre fasi di una procedura canonica."""

    procedura: ProceduraGioco
    carta: int
    cifre_iniziali: Terna
    parola_iniziale: str
    passi: Tuple[PassoFlusso, ...]
    posizione_finale: int
    cifre_finali: Terna
    parola_finale: str

    @property
    def storia_distribuzioni(self) -> Terna:
        """Colonne osservate nel tempo (= rev ω(n) se non ci sono rovesciamenti)."""
        return tuple(p.colonna for p in self.passi)

    @property
    def storia_raccolte(self) -> Terna:
        """(s0, s1, s2): scrivono l'indirizzo finale (s2, s1, s0)."""
        return tuple(p.destinazione_blocco for p in self.passi)

    @property
    def cifre_origine_nel_tempo(self) -> Terna:
        """(n0, n1, n2): le cifre dell'origine nell'ordine in cui escono."""
        n2, n1, n0 = self.cifre_iniziali
        return (n0, n1, n2)


# ═══════════════════════════════ tabellone ══════════════════════════════════

def _numero(numero) -> int:
    return valida_indice(numero, 216, nome="numero_tavola")


def _riga(fase, peso, indice, sigla) -> RigaTabellone:
    return RigaTabellone(fase, peso, indice, sigla,
                         tuple(_gr.MESCOLAMENTO[sigla]))


def tabellone(numero) -> Tabellone:
    """Tabellone diretto e inverso della disposizione `numero` (0..215)."""
    riga = _gr.riga_tavola(_numero(numero))
    mesc, imp = riga["mescolamenti"], riga["impilamenti"]
    T, Tinv = tuple(riga["T"]), tuple(riga["T_inv"])
    cronologia = tuple(FaseCronologica(i + 1, m, s)
                       for i, (m, s) in enumerate(zip(mesc, imp)))
    righe = tuple(_riga(f, p, i, mesc[f - 1]) for f, p, i in _RIGHE_VISIVE)
    inverse = tuple(_riga(f, p, i, imp[f - 1]) for f, p, i in _RIGHE_VISIVE)
    return Tabellone(
        numero=riga["numero"], cronologia=cronologia, righe=righe,
        righe_inverse=inverse,
        colonne_assi=tuple(ColonnaAsso(d, a, T[a]) for d, a in enumerate(_ASSI)),
        colonne_inverse=tuple(ColonnaAsso(d, Tinv[a], a)
                              for d, a in enumerate(_ASSI)),
        destinazioni=T, mazzo_finale=Tinv, autoinversa=riga["autoinversa"])


def lettura_cifre(numero, carta) -> LetturaCifre:
    """T(n2,n1,n0) = (B(n2), B(n1), B(n0)) letto sulla griglia, con le celle."""
    t = tabellone(numero)
    carta = valida_indice(carta, 27, nome="carta")
    cifre = _gr.digits3(carta)
    azioni = []
    for rv, r in enumerate(t.righe):
        d = cifre[2 - r.indice_cifra]
        azioni.append(AzioneCifra(r.fase, r.peso, r.indice_cifra, rv, r.sigla,
                                  d, r.valori[d]))
    destinazione = t.destinazioni[carta]
    return LetturaCifre(
        numero=t.numero, carta=carta, cifre_iniziali=cifre,
        parola_iniziale=_gr.parola(carta), azioni=tuple(azioni),
        cifre_finali=_gr.digits3(destinazione),
        parola_finale=_gr.parola(destinazione), destinazione=destinazione)


def tabella_posizioni(numero) -> Tuple[LetturaCifre, ...]:
    """Le 27 righe n → Π(n) → n', in ordine 0..26."""
    numero = _numero(numero)
    return tuple(lettura_cifre(numero, n) for n in range(27))


# ═══════════════════════════ macchina che dimentica ═════════════════════════

def flussi_procedura(procedura: ProceduraGioco) -> Tuple[FlussoCarta, ...]:
    """Il flusso di tutte le 27 carte, da una sola traccia fisica.

    La traccia e' quella di `gioco_reale.esegui_partita` sui parametri di
    `adattamento_fisico` (convenzione fisica B come oracolo): il mazzo che si
    distribuisce allo stadio k e' gia' quello capovolto da J^ε_k, e la
    posizione dopo la raccolta (prima di un eventuale ε successivo) e' quella
    di `gioco_reale.raccogli` senza rovesciamento.
    """
    if not isinstance(procedura, ProceduraGioco):
        raise TypeError("attesa una ProceduraGioco")
    a = adattamento_fisico(procedura)
    _, fasi = _gr.esegui_partita(a.mescolamenti, a.rovesciamenti_dopo_raccolta)
    colonne = [f["cols"] for f in fasi if f["tipo"] == "colonne"]
    distribuiti = [fasi[0]["deck"]] + [f["deck"] for f in fasi
                                      if f["tipo"] == "raccolta"][:2]
    raccolti = [_gr.raccogli(c, s) for c, s in zip(colonne, a.mescolamenti)]
    eps = procedura.rovesciamenti
    flussi = []
    for carta in range(27):
        # nell'oracolo la carta equivalente e' J(carta) se ε1 (T_A = T_B ∘ J)
        cb = distribuiti[0][26 - carta] if a.rovescia_mazzo_iniziale else carta
        prima = carta
        passi = []
        for k in range(3):
            q = distribuiti[k].index(cb)
            col = next(g for g in range(3) if cb in colonne[k][g])
            dopo = raccolti[k].index(cb)
            sigla = procedura.mescolamenti[k]
            passi.append(PassoFlusso(
                fase=k + 1, mescolamento=sigla,
                impilamento=_gr.IMPILAMENTO_DI[sigla], rovesciamento=eps[k],
                posizione_prima=prima, cifre_prima=_gr.digits3(prima),
                posizione_distribuita=q, cifre_distribuite=_gr.digits3(q),
                colonna=col, altezza=colonne[k][col].index(cb),
                destinazione_blocco=_gr.MESCOLAMENTO[sigla][col],
                posizione_dopo=dopo, cifre_dopo=_gr.digits3(dopo),
                complementata=bool(sum(eps[:k + 1]) % 2),
                parola_prima=_gr.parola(prima), parola_distribuita=_gr.parola(q),
                parola_dopo=_gr.parola(dopo)))
            prima = dopo
        flussi.append(FlussoCarta(
            procedura=procedura, carta=carta,
            cifre_iniziali=_gr.digits3(carta), parola_iniziale=_gr.parola(carta),
            passi=tuple(passi), posizione_finale=prima,
            cifre_finali=_gr.digits3(prima), parola_finale=_gr.parola(prima)))
    return tuple(flussi)


def flusso_carta(procedura: ProceduraGioco, carta) -> FlussoCarta:
    """Il flusso di una carta attraverso le tre fasi della procedura."""
    carta = valida_indice(carta, 27, nome="carta")
    return flussi_procedura(procedura)[carta]


# ═══════════════════════════════ (R) e ritorno ══════════════════════════════

def realizza(trasformazione) -> ProceduraGioco:
    """(R): l'unica procedura senza rovesciamenti che realizza T (I1).

    Solleva `PermutazioneNonValida` se T non e' una permutazione di 27
    elementi, `TrasformazioneFuoriDominio` se nessuna procedura la realizza.
    Nessun solutore: e' una lettura della classe della trasformazione.
    """
    classe = servizio_procedure().classe_trasformazione(trasformazione)
    semplici = [p for p in classe if p.semplice]
    if len(semplici) != 1:                   # I1-G9: non deve mai accadere
        raise AssertionError("classe senza un'unica procedura semplice")
    return semplici[0]


def ritorno(numero) -> ProceduraGioco:
    """La procedura che riporta indietro la disposizione: (R) applicata a T⁻¹.

    I suoi mescolamenti sono gli impilamenti della disposizione, nello stesso
    ordine delle fasi (libro, § 4.10 e § 7.1.2 (R)).
    """
    return realizza(_gr.riga_tavola(_numero(numero))["T_inv"])


def disposizione_realizzata(procedura: ProceduraGioco) -> int:
    """# della disposizione della Tavola che ha la stessa T della procedura.

    Con rovesciamenti canonici la T resta fra le 216 (J e' nel gruppo delle
    disposizioni semplici): e' (R) applicata a T(procedura).
    """
    return realizza(servizio_procedure().trasformazione(procedura)).numero_tavola


def numero_di(trasformazione) -> Optional[int]:
    """# della disposizione che realizza T, o None se T non e' fra le 216."""
    from .procedure import TrasformazioneFuoriDominio
    try:
        return realizza(trasformazione).numero_tavola
    except TrasformazioneFuoriDominio:
        return None
