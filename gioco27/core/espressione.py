"""Linguaggio delle espressioni: un solo ingresso da testo ad AST e a traccia.

Compartimento E. Prima di questo modulo esistevano **due** grammatiche per lo
stesso testo: quella dell'Explorer (`core.algebra`: Lexer, Parser, AST
`SymbolicExpr`) e una seconda, a espressioni regolari, dentro il visualizzatore
Mescolamento (`gui.shuffle._validate_and_parse`). La seconda era piu'
permissiva in un verso — cancellava l'operatore finale, buttava via le
parentesi spaiate — e piu' povera nell'altro — non conosceva `I`, `J`, ne' i
fattori Kronecker composti. Da qui nasceva B07.

Qui non c'e' un parser nuovo: c'e' **l'unico** parser, quello di
`core.algebra`, piu' il contratto che mancava per farlo usare anche da chi
simula invece di calcolare.

    testo
      │
      ▼
    analizza()            ← Lexer + Parser di core.algebra (grammatica unica)
      │
      ▼
    SymbolicExpr (AST)
      ├──► permutazione_di()      valutazione matematica → T
      └──► traccia_simulazione()  sequenza cronologica dei passi → Mescolamento

Convenzioni matematiche (invariate, protette dal compartimento D):

* ``T[carta] = posizione di destinazione``;
* ``mazzo[posizione] = carta``;
* ``(a ∘ b)[i] = a[b[i]]``: in ``A ∘ B`` si applica **prima B**, poi A.

Da cui la relazione fra i due mondi, che la traccia rende verificabile:
partendo dal mazzo ordinato e applicando i passi in ordine cronologico
(da destra a sinistra rispetto al testo) si ottiene ``mazzo finale =
inversa(T)``, perche' la carta ``c`` finisce in posizione ``T[c]``.

Il modulo non importa tkinter, non tocca il filesystem e non conosce la GUI.
"""

from dataclasses import dataclass
from typing import List, Tuple, Union

from ..i18n import tr
from .algebra import (AlgebraEngine, Evaluator, ParseError, Parser,
                      SymbolicExpr)

__all__ = ["ParseError", "EspressioneNonSimulabile", "PassoEsecuzione",
           "TracciaEsecuzione", "analizza", "permutazione_di",
           "traccia_simulazione"]


class EspressioneNonSimulabile(ValueError):
    """L'espressione e' sintatticamente valida ma non descrive un mazzo di 27.

    Distinta da `ParseError`: la grammatica non e' stata violata, e' il
    risultato a non appartenere al dominio della simulazione (per esempio
    `SCD_U`, che e' una permutazione di tre elementi). Chi presenta l'errore
    puo' cosi' distinguere «non e' una formula» da «e' una formula, ma non di
    un mazzo».
    """


@dataclass(frozen=True)
class PassoEsecuzione:
    """Un passo della simulazione: una sola trasformazione applicata al mazzo.

    Contiene soltanto cio' che serve a chi anima o chi verifica:

    * `indice` / `totale`: posizione nell'ordine **cronologico** di
      applicazione (0 = primo passo eseguito = fattore piu' a destra);
    * `operazione`: `"MSC"`, `"KRON"` o `"ATOMO"` — l'unica classificazione
      che la vista usa per scegliere colore ed etichetta;
    * `etichetta`: come il fattore appare nel testo, alias storici compresi
      (`R_U`, `I_3` restano tali e non diventano `DCS_U`, `SCD_U`);
    * `permutazione`: la permutazione di 27 elementi del solo fattore, nella
      convenzione `perm[carta] = destinazione`;
    * `mazzo`: lo stato del mazzo **dopo** il passo, `mazzo[posizione] = carta`.
    """

    indice: int
    totale: int
    operazione: str
    etichetta: str
    permutazione: Tuple[int, ...]
    mazzo: Tuple[int, ...]

    # Compatibilita' con la forma storica dei token del visualizzatore,
    # (tipo, valore, etichetta): alcuni test e il log leggono per indice.
    def __getitem__(self, i):
        return (self.operazione, self.permutazione, self.etichetta)[i]


@dataclass(frozen=True)
class TracciaEsecuzione:
    """La storia completa dell'esecuzione di **una** espressione.

    Non e' la cronologia dell'utente (quella appartiene a J) e non e' un bus di
    eventi (quello, se mai servira', appartiene a G): e' la cronologia
    matematica di una singola valutazione, derivata dall'AST.
    """

    passi: Tuple[PassoEsecuzione, ...]
    mazzo_iniziale: Tuple[int, ...]
    permutazione: Tuple[int, ...]

    def __len__(self):
        return len(self.passi)

    def __iter__(self):
        return iter(self.passi)

    def __getitem__(self, i):
        return self.passi[i]

    @property
    def mazzo_finale(self) -> Tuple[int, ...]:
        return self.passi[-1].mazzo if self.passi else self.mazzo_iniziale


_PARSER = Parser(AlgebraEngine())
_EVALUATOR = Evaluator(AlgebraEngine())


def analizza(testo: str) -> SymbolicExpr:
    """Testo → AST. Unico ingresso sintattico del programma.

    Solleva `ParseError` su qualunque violazione della grammatica: nessun
    recupero silenzioso, nessuna coda ignorata, nessuna parentesi spaiata
    tollerata.
    """
    return _PARSER.parse(testo)


def permutazione_di(espressione: Union[str, SymbolicExpr]) -> List[int]:
    """AST (o testo) → permutazione risultante."""
    if isinstance(espressione, str):
        espressione = analizza(espressione)
    return _EVALUATOR.evaluate(espressione)


def _etichetta_fattore(nodo: SymbolicExpr) -> str:
    """Come il fattore appariva nel testo, per quanto l'AST lo conservi."""
    if nodo.kind in ("atom", "value"):
        return nodo.origine or nodo.name or repr(nodo)
    if nodo.kind == "kron":
        return "(" + " x ".join(_etichetta_fattore(c) for c in nodo.children) + ")"
    return repr(nodo)


def _fattori(nodo: SymbolicExpr) -> List[Tuple[str, str, List[int]]]:
    """Appiattisce l'AST nei fattori applicati al mazzo, in ordine testuale.

    La composizione e' associativa, quindi `(A ∘ B) ∘ C` e `A ∘ (B ∘ C)`
    producono la stessa sequenza: il raggruppamento non cambia ne' la
    matematica ne' la simulazione. Un nodo Kronecker resta **un solo** passo,
    anche quando i suoi fattori sono a loro volta composizioni di tipo 3.
    """
    if nodo.kind == "compose":
        fattori = []
        for figlio in nodo.children:
            fattori.extend(_fattori(figlio))
        return fattori

    if nodo.ptype != 27:
        raise EspressioneNonSimulabile(tr("explorer.error.type3_result"))

    if nodo.kind == "kron":
        return [("KRON", _etichetta_fattore(nodo), _EVALUATOR.evaluate(nodo))]
    if nodo.kind in ("atom", "value"):
        nome = nodo.name or _etichetta_fattore(nodo)
        operazione = "MSC" if nome == "MSC" else "ATOMO"
        return [(operazione, _etichetta_fattore(nodo), list(nodo.value))]

    raise EspressioneNonSimulabile(tr("explorer.error.type3_result"))


def _applica(mazzo: Tuple[int, ...], perm: List[int]) -> Tuple[int, ...]:
    """La carta in posizione `i` va in posizione `perm[i]`."""
    nuovo = [0] * len(mazzo)
    for posizione, carta in enumerate(mazzo):
        nuovo[perm[posizione]] = carta
    return tuple(nuovo)


def traccia_simulazione(espressione: Union[str, SymbolicExpr]) -> TracciaEsecuzione:
    """AST (o testo) → traccia cronologica dei passi.

    Solleva `ParseError` se il testo non e' una formula, e
    `EspressioneNonSimulabile` se lo e' ma non descrive un mazzo di 27 carte.
    """
    if isinstance(espressione, str):
        espressione = analizza(espressione)
    if espressione.ptype != 27:
        raise EspressioneNonSimulabile(tr("explorer.error.type3_result"))

    # ordine testuale → ordine cronologico: il fattore piu' a destra e' il
    # primo a toccare il mazzo, perche' (a ∘ b) applica prima b.
    fattori = list(reversed(_fattori(espressione)))

    mazzo_iniziale = tuple(range(27))
    mazzo = mazzo_iniziale
    passi = []
    for indice, (operazione, etichetta, perm) in enumerate(fattori):
        mazzo = _applica(mazzo, perm)
        passi.append(PassoEsecuzione(
            indice=indice, totale=len(fattori), operazione=operazione,
            etichetta=etichetta, permutazione=tuple(perm), mazzo=mazzo))

    return TracciaEsecuzione(
        passi=tuple(passi), mazzo_iniziale=mazzo_iniziale,
        permutazione=tuple(permutazione_di(espressione)))
