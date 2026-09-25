"""Decodifica e riconoscimento (compartimento I5).

Dal mazzo alla legge: data una permutazione, un mazzo iniziale e uno finale,
oppure due mazzi, il service ricostruisce T e dice a quale struttura
appartiene. Niente Tk, niente testo: dati immutabili e codici stabili.

Convenzioni (le stesse del programma e del libro, § 2.2 e § 7.1.1 A1)
-----------------------------------------------------------------------

* ``T[x]`` = posizione finale della carta che parte in x: ``T`` e' π;
* un mazzo e' una sequenza ``mazzo[posizione] = carta``; il mazzo finale di
  un mazzo iniziale ordinato e' T⁻¹. Nessuna inversione implicita: le
  funzioni dicono sempre quale delle due cose ricevono;
* A1: ``finale = P · iniziale``, cioe' ``finale[T[i]] = iniziale[i]``;
* cifre: ``gioco_reale.digits3`` (n2, n1, n0); il livello i e' la cifra di
  peso 3^i, e il fattore ρ_i coincide col mescolamento M_i (A1: B_i = M_i).

Due riconoscitori indipendenti (DP1 = C)
----------------------------------------

* **diretto** (`separabile`): Def. 4.1 / Teor. 4.2 dell'Articolo e di App. D —
  la cifra di livello i di π(x) dipende solo dalla cifra di livello i di x;
* **somme** (`criterio_somme`): App. D Teor. 6.4 — ρ̂_i(t) =
  (Σ_{i,t} − C_i) / 3^(2+i) e' una permutazione di {0,1,2} a ogni livello.
  L'Oss. 5.3 dell'Articolo non nega il teorema: non lo assume.

Il criterio per somme non chiama `separabile`: i due si confrontano nei test.

Classe estesa (nome neutro, DP2 aperta): π = K ∘ MSC^k con K separabile e
MSC la permutazione del core (`AlgebraEngine.MSC_PERM`), come nella forma
canonica del programma; il classificatore cerca k con π ∘ MSC^{-k} separabile.

Traslazioni (DP10a = C): nessuna operazione nuova; C_k e' solo un input.
Mazzi gemelli (DP10b, A8): `trasformazione_relativa(A, B) = T_B ∘ T_A⁻¹`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Hashable, Optional, Sequence, Tuple

from ..core import gioco_reale as _gr
from ..core.algebra import AlgebraEngine as _AE
from ..core.dominio import valida_indice, valida_permutazione

__all__ = [
    "IngressoNonValido", "Permutazione", "Terna", "Conflitto", "EsitoLivello",
    "Separabilita", "LivelloSomme", "CriterioSomme", "ClasseEstesa",
    "RitornoDaGuide", "Raggiungibilita", "EffettoPosizione", "EsitoA1",
    "AVANTI", "INDIETRO", "COSTANTI_C", "LEGGI_A1",
    "permutazione", "inversa", "da_mazzi", "trasformazione_relativa",
    "separabile", "fattori_locali", "somme_di_fibra", "criterio_somme",
    "classe_estesa", "ritorno_da_guide", "ritorno_da_mazzi", "raggiungibile",
    "effetto", "nota_due", "traslazione",
]

N = 27
Permutazione = Tuple[int, ...]
Terna = Tuple[int, int, int]
AVANTI, INDIETRO = "avanti", "indietro"

#: le quattro forme di A1 (finale = P · iniziale), come codici
LEGGI_A1 = ("trasformazione_da_mazzi", "finale_da_iniziale",
            "iniziale_da_finale", "verifica")

#: C_i = b^{m−2} · b(b−1)/2 · Σ_{j≠i} b^j (Teor. 5.1 / 6.1), b = m = 3
COSTANTI_C: Tuple[int, int, int] = tuple(
    3 ** (3 - 2) * (3 * 2 // 2) * sum(3 ** j for j in range(3) if j != i)
    for i in range(3))

_SIGLA_DI = {v: k for k, v in _gr.MESCOLAMENTO.items()}


class IngressoNonValido(ValueError):
    """Dato che non rispetta il contratto I5, con `codice` stabile e `dati`.

    Come `procedure.ProceduraNonValida`: il messaggio e' neutro, la frase per
    l'utente si compone nella GUI dal codice. Codici: ``mazzo_lunghezza``,
    ``mazzo_duplicato``, ``mazzi_diversi``, ``verso``, ``a1_dati_insufficienti``,
    ``a1_incoerente``.
    """

    def __init__(self, messaggio, *, codice, **dati):
        super().__init__(messaggio)
        self.codice = codice
        self.dati = dati


# ════════════════════════════════ ingressi ══════════════════════════════════

def permutazione(valori) -> Permutazione:
    """Valida ``T[origine] = destinazione``: 27 interi 0..26 senza ripetizioni.

    Gli errori sono `core.dominio.PermutazioneNonValida`, gia' tipizzati con
    `codice` (lunghezza, valore_ripetuto, fuori_intervallo, …).
    """
    return valida_permutazione(valori, N, nome="permutazione")


def inversa(p) -> Permutazione:
    q = [0] * N
    for x, y in enumerate(p):
        q[y] = x
    return tuple(q)


def _componi(a, b) -> Permutazione:
    """(a ∘ b)(x) = a(b(x)), la composizione del core."""
    return tuple(_AE.compose(list(a), list(b)))


def _mazzo(mazzo, nome) -> Tuple[Hashable, ...]:
    carte = tuple(mazzo)
    if len(carte) != N:
        raise IngressoNonValido(f"{nome}: attese 27 carte, ricevute {len(carte)}",
                                codice="mazzo_lunghezza", nome=nome,
                                lunghezza=len(carte))
    visti = set()
    for pos, c in enumerate(carte):
        if c in visti:
            raise IngressoNonValido(f"{nome}: carta ripetuta {c!r}",
                                    codice="mazzo_duplicato", nome=nome,
                                    carta=c, posizione=pos)
        visti.add(c)
    return carte


def da_mazzi(iniziale, finale) -> Permutazione:
    """T da un mazzo iniziale e uno finale: ``T[i] = finale.index(iniziale[i])``.

    ``T[i]`` e' la posizione finale della carta che stava in i (A1).
    """
    a = _mazzo(iniziale, "iniziale")
    b = _mazzo(finale, "finale")
    if set(a) != set(b):
        raise IngressoNonValido("i due mazzi non contengono le stesse carte",
                                codice="mazzi_diversi",
                                solo_iniziale=sorted(map(str, set(a) - set(b))),
                                solo_finale=sorted(map(str, set(b) - set(a))))
    dove = {c: pos for pos, c in enumerate(b)}
    return tuple(dove[c] for c in a)


def trasformazione_relativa(mazzo_a, mazzo_b) -> Permutazione:
    """A8: la carta in posizione p nel mazzo A sta in ``T_B T_A⁻¹(p)`` nel mazzo B.

    Con due mazzi gemelli (stesso ordine iniziale) coincide con T_B ∘ T_A⁻¹;
    e' la stessa lettura di `da_mazzi` con A come partenza.
    """
    return da_mazzi(mazzo_a, mazzo_b)


def traslazione(k: int) -> Permutazione:
    """C_k: x ↦ x + k mod 27 (un taglio di k carte, A13). Solo un input."""
    k = valida_indice(k, N, nome="traslazione")
    return tuple((x + k) % N for x in range(N))


def _cifra(x: int, livello: int) -> int:
    return _gr.digits3(x)[2 - livello]


# ═════════════════════════ riconoscitore diretto ════════════════════════════

@dataclass(frozen=True)
class Conflitto:
    """Due posizioni con la stessa cifra al livello, immagini con cifre diverse."""

    livello: int
    cifra: int                     # d_i(x1) = d_i(x2)
    x1: int
    x2: int
    immagine1: int
    immagine2: int
    cifra_immagine1: int
    cifra_immagine2: int


@dataclass(frozen=True)
class EsitoLivello:
    livello: int
    passa: bool
    fattore: Optional[Terna]       # ρ_i se il livello passa
    conflitto: Optional[Conflitto]


@dataclass(frozen=True)
class Separabilita:
    permutazione: Permutazione
    livelli: Tuple[EsitoLivello, EsitoLivello, EsitoLivello]

    @property
    def separabile(self) -> bool:
        return all(l.passa for l in self.livelli)

    @property
    def fattori(self) -> Optional[Tuple[Terna, Terna, Terna]]:
        """(ρ_0, ρ_1, ρ_2) se separabile."""
        if not self.separabile:
            return None
        return tuple(l.fattore for l in self.livelli)

    @property
    def sigle(self) -> Optional[Tuple[str, str, str]]:
        """(M_0, M_1, M_2): i mescolamenti in ordine cronologico."""
        f = self.fattori
        return None if f is None else tuple(_SIGLA_DI[r] for r in f)

    @property
    def numero_tavola(self) -> Optional[int]:
        s = self.sigle
        return None if s is None else _gr.numero_tavola(s)


def separabile(p) -> Separabilita:
    """Def. 4.1 / Teor. 4.2, livello per livello, con il primo conflitto."""
    p = permutazione(p)
    livelli = []
    for i in range(3):
        rho = [None, None, None]
        testimone = [None, None, None]
        conflitto = None
        for x in range(N):
            t, u = _cifra(x, i), _cifra(p[x], i)
            if rho[t] is None:
                rho[t], testimone[t] = u, x
            elif rho[t] != u:
                x1 = testimone[t]
                conflitto = Conflitto(i, t, x1, x, p[x1], p[x], rho[t], u)
                break
        passa = conflitto is None
        livelli.append(EsitoLivello(i, passa, tuple(rho) if passa else None,
                                    conflitto))
    return Separabilita(p, tuple(livelli))


def fattori_locali(p) -> Optional[Tuple[Terna, Terna, Terna]]:
    """(ρ_0, ρ_1, ρ_2) di una π separabile, altrimenti None."""
    return separabile(p).fattori


# ════════════════════ somme di fibra e Teor. 6.4 (App. D) ════════════════════

@dataclass(frozen=True)
class LivelloSomme:
    livello: int
    somme: Tuple[int, int, int]                   # Σ_{i,0}, Σ_{i,1}, Σ_{i,2}
    candidati: Tuple[Fraction, Fraction, Fraction]

    @property
    def interi(self) -> bool:
        return all(c.denominator == 1 for c in self.candidati)

    @property
    def in_dominio(self) -> bool:
        return self.interi and all(0 <= c <= 2 for c in self.candidati)

    @property
    def distinti(self) -> bool:
        return len(set(self.candidati)) == 3

    @property
    def permutazione(self) -> bool:
        return self.in_dominio and self.distinti

    @property
    def fattore(self) -> Optional[Terna]:
        return tuple(int(c) for c in self.candidati) if self.permutazione else None


@dataclass(frozen=True)
class CriterioSomme:
    verso: str                                    # "avanti" (π) o "indietro" (π⁻¹)
    analizzata: Permutazione                      # π o π⁻¹, quella sommata
    livelli: Tuple[LivelloSomme, LivelloSomme, LivelloSomme]
    ricostruita: Optional[Permutazione]           # Σ b^i ρ̂_i(d_i(x)) se vero

    @property
    def vero(self) -> bool:
        return all(l.permutazione for l in self.livelli)

    @property
    def fattori(self) -> Optional[Tuple[Terna, Terna, Terna]]:
        return tuple(l.fattore for l in self.livelli) if self.vero else None

    @property
    def coincide(self) -> Optional[bool]:
        """La π ricostruita e' proprio quella analizzata (dimostrazione del 6.4)."""
        return None if self.ricostruita is None else self.ricostruita == self.analizzata


def somme_di_fibra(p, verso: str = AVANTI) -> Tuple[Terna, Terna, Terna]:
    """Σ_{i,t} = Σ_{x: d_i(x)=t} π(x) (avanti) o lo stesso su π⁻¹ (indietro).

    Avanti: fibre di posizioni iniziali, somme delle immagini → fattori di T.
    Indietro: fibre di posizioni finali, somme delle preimmagini → fattori di T⁻¹.
    """
    q = _orientata(p, verso)
    return tuple(tuple(sum(q[x] for x in range(N) if _cifra(x, i) == t)
                       for t in range(3)) for i in range(3))


def _orientata(p, verso):
    p = permutazione(p)
    if verso == AVANTI:
        return p
    if verso == INDIETRO:
        return inversa(p)
    raise IngressoNonValido(f"verso sconosciuto: {verso!r}", codice="verso",
                            verso=verso)


def criterio_somme(p, verso: str = AVANTI) -> CriterioSomme:
    """App. D Teor. 6.4, aritmetica esatta; indipendente da `separabile`."""
    q = _orientata(p, verso)
    tutte = somme_di_fibra(q, AVANTI)
    livelli = tuple(
        LivelloSomme(i, tutte[i], tuple(Fraction(s - COSTANTI_C[i], 3 ** (2 + i))
                                        for s in tutte[i]))
        for i in range(3))
    ricostruita = None
    if all(l.permutazione for l in livelli):
        r0, r1, r2 = (l.fattore for l in livelli)
        ricostruita = tuple(9 * r2[x // 9] + 3 * r1[(x // 3) % 3] + r0[x % 3]
                            for x in range(N))
    return CriterioSomme(verso, q, livelli, ricostruita)


# ══════════════════════════════ classe estesa ═══════════════════════════════

@dataclass(frozen=True)
class ClasseEstesa:
    appartiene: bool
    k: Optional[int]                               # π = K ∘ MSC^k
    componente: Optional[Permutazione]             # K = π ∘ MSC^{-k}
    separabilita: Optional[Separabilita]           # della componente

    @property
    def fattori(self):
        return None if self.separabilita is None else self.separabilita.fattori


def _msc_potenza(k: int) -> Permutazione:
    m = tuple(range(N))
    for _ in range(k % 3):
        m = _componi(_AE.MSC_PERM, m)
    return m


def classe_estesa(p) -> ClasseEstesa:
    """L'unico k ∈ {0,1,2} con π ∘ MSC^{-k} separabile, se esiste (App. D § 5.3)."""
    p = permutazione(p)
    for k in range(3):
        comp = _componi(p, inversa(_msc_potenza(k)))
        esito = separabile(comp)
        if esito.separabile:
            return ClasseEstesa(True, k, comp, esito)
    return ClasseEstesa(False, None, None, None)


# ════════════════════════ due carte guida (§ 10.2) ══════════════════════════

def _completa(zero: int, due: int) -> Optional[Terna]:
    """La permutazione di {0,1,2} con 0 ↦ zero, 2 ↦ due (None se zero = due)."""
    if zero == due:
        return None
    tau = [None, None, None]
    tau[0], tau[2] = zero, due
    tau[1] = ({0, 1, 2} - {zero, due}).pop()
    return tuple(tau)


def _da_righe(righe_alto_basso) -> Permutazione:
    s2, s1, s0 = righe_alto_basso
    return tuple(9 * s2[x // 9] + 3 * s1[(x // 3) % 3] + s0[x % 3] for x in range(N))


@dataclass(frozen=True)
class RitornoDaGuide:
    """§ 10.2.1: le posizioni attuali delle carte partite da 0 e da 26."""

    q0: int
    q2: int
    cifre_q0: Terna                               # (u2, u1, u0)
    cifre_q2: Terna                               # (v2, v1, v0)
    livelli_validi: Tuple[bool, bool, bool]       # u_h ≠ v_h, dall'alto
    andata: Optional[Tuple[Terna, Terna, Terna]]  # σ2, σ1, σ0 (tabellone diretto)
    ritorno: Optional[Tuple[Terna, Terna, Terna]]  # τ2, τ1, τ0 = σ_h⁻¹
    verifica: Optional[bool] = None               # sulle 27 carte, se note
    primo_scarto: Optional[int] = None            # posizione in B che non torna

    @property
    def valide(self) -> bool:
        return all(self.livelli_validi)

    @property
    def terza_guida(self) -> Optional[int]:
        """Posizione della carta partita da 13: 39 − q0 − q2."""
        return 39 - self.q0 - self.q2 if self.valide else None

    @property
    def permutazione_andata(self) -> Optional[Permutazione]:
        return None if self.andata is None else _da_righe(self.andata)

    @property
    def permutazione_ritorno(self) -> Optional[Permutazione]:
        return None if self.ritorno is None else _da_righe(self.ritorno)

    @property
    def numero_andata(self) -> Optional[int]:
        return _numero(self.andata)

    @property
    def numero_ritorno(self) -> Optional[int]:
        return _numero(self.ritorno)


def _numero(righe):
    if righe is None:
        return None
    s2, s1, s0 = righe
    return _gr.numero_tavola((_SIGLA_DI[s0], _SIGLA_DI[s1], _SIGLA_DI[s2]))


def ritorno_da_guide(q0: int, q2: int) -> RitornoDaGuide:
    """Il tabellone di ritorno dalle posizioni attuali delle due guide."""
    q0 = valida_indice(q0, N, nome="q0")
    q2 = valida_indice(q2, N, nome="q2")
    u, v = _gr.digits3(q0), _gr.digits3(q2)
    validi = tuple(a != b for a, b in zip(u, v))
    if not all(validi):
        return RitornoDaGuide(q0, q2, u, v, validi, None, None)
    andata = tuple(_completa(a, b) for a, b in zip(u, v))       # σ_h(0), σ_h(2)
    ritorno = tuple(tuple(s.index(t) for t in range(3)) for s in andata)
    return RitornoDaGuide(q0, q2, u, v, validi, andata, ritorno)


def ritorno_da_mazzi(iniziale, attuale) -> RitornoDaGuide:
    """§ 10.2.1 con i mazzi: guide = iniziale[0] e iniziale[26]; poi il controllo
    sulle 27 carte («il tabellone e' valido soltanto se ricostruisce A»)."""
    T = da_mazzi(iniziale, attuale)
    esito = ritorno_da_guide(T[0], T[26])
    if not esito.valide:
        return esito
    R = esito.permutazione_ritorno                # posizione in B → posizione in A
    a, b = tuple(iniziale), tuple(attuale)
    scarto = next((n for n in range(N) if a[R[n]] != b[n]), None)
    return RitornoDaGuide(esito.q0, esito.q2, esito.cifre_q0, esito.cifre_q2,
                          esito.livelli_validi, esito.andata, esito.ritorno,
                          scarto is None, scarto)


@dataclass(frozen=True)
class Raggiungibilita:
    """§ 10.2.2: esiste un tabellone del Gioco che porta v in w?"""

    relativa: Permutazione                        # T_{v→w}, sempre definita
    guide: RitornoDaGuide                         # guide di v cercate in w
    posizione_attesa_13: Optional[int]            # controllo immediato
    posizione_reale_13: int
    primo_scarto: Optional[int]                   # prima etichetta fuori posto

    @property
    def raggiungibile(self) -> bool:
        return self.guide.valide and self.primo_scarto is None

    @property
    def candidato(self) -> Optional[Permutazione]:
        return self.guide.permutazione_andata

    @property
    def numero(self) -> Optional[int]:
        return self.guide.numero_andata if self.raggiungibile else None


def raggiungibile(v, w) -> Raggiungibilita:
    """Guide in v alle posizioni 0 e 26, cercate in w; poi le altre 25 carte."""
    rel = trasformazione_relativa(v, w)
    guide = ritorno_da_guide(rel[0], rel[26])
    attesa = scarto = None
    if guide.valide:
        cand = guide.permutazione_andata
        attesa = cand[13]
        scarto = next((a for a in range(N) if cand[a] != rel[a]), None)
    return Raggiungibilita(rel, guide, attesa, rel[13], scarto)


@dataclass(frozen=True)
class EffettoPosizione:
    """L'effetto di una π gia' data su una posizione (non l'esistenza di una π)."""

    posizione: int
    immagine: int          # dove va la carta che parte da `posizione`
    preimmagine: int       # da dove arriva la carta che finisce in `posizione`


def effetto(p, posizione: int) -> EffettoPosizione:
    p = permutazione(p)
    posizione = valida_indice(posizione, N, nome="posizione")
    return EffettoPosizione(posizione, p[posizione], p.index(posizione))


# ═════════════════════ A1: note due, calcola la terza ═══════════════════════

@dataclass(frozen=True)
class EsitoA1:
    """§ 7.1.1: finale = P · iniziale, cioe' finale[T[i]] = iniziale[i]."""

    iniziale: Tuple[Hashable, ...]
    finale: Tuple[Hashable, ...]
    trasformazione: Permutazione
    calcolato: Optional[str]    # "iniziale" | "finale" | "trasformazione" | None
    legge: str                  # codice della forma usata: LEGGI_A1


def nota_due(iniziale: Optional[Sequence] = None, finale: Optional[Sequence] = None,
             trasformazione: Optional[Sequence] = None) -> EsitoA1:
    """Note due fra iniziale, finale e T, calcola la terza; con tre, le verifica."""
    dati = sum(x is not None for x in (iniziale, finale, trasformazione))
    if dati < 2:
        raise IngressoNonValido("servono almeno due dei tre dati",
                                codice="a1_dati_insufficienti", dati=dati)
    if trasformazione is not None:
        T = permutazione(trasformazione)
    if iniziale is not None and finale is not None:
        T_letta = da_mazzi(iniziale, finale)
        if trasformazione is not None and T_letta != T:
            raise IngressoNonValido("i tre dati non soddisfano finale = P · iniziale",
                                    codice="a1_incoerente",
                                    posizione=next(i for i in range(N)
                                                   if T_letta[i] != T[i]))
        calcolato = None if trasformazione is not None else "trasformazione"
        return EsitoA1(tuple(iniziale), tuple(finale), T_letta, calcolato,
                       "trasformazione_da_mazzi" if calcolato else "verifica")
    if iniziale is not None:
        a = _mazzo(iniziale, "iniziale")
        fin = [None] * N
        for i in range(N):
            fin[T[i]] = a[i]
        return EsitoA1(a, tuple(fin), T, "finale", "finale_da_iniziale")
    b = _mazzo(finale, "finale")
    return EsitoA1(tuple(b[T[i]] for i in range(N)), b, T, "iniziale",
                   "iniziale_da_finale")
