"""Contratti del dominio matematico: validazione degli ingressi e glossario.

Questo modulo e' il punto unico in cui il dominio decide che cosa sia una
permutazione valida. Non dipende da Tk, dalla GUI, dal filesystem, dagli export
ne' dall'i18n: solleva errori di dominio neutri, che i livelli superiori possono
tradurre o presentare come preferiscono.

Perche' esiste (R04)
--------------------
Diverse API matematiche pubbliche presumevano di ricevere gia' una permutazione
valida. Con un ingresso non fidato il risultato andava dal silenzio (un numero
privo di significato) al blocco: `orbit_of([1, 1], 0)` non terminava affatto.
La validazione vive qui una volta sola; le funzioni interne che ricevono oggetti
gia' validati non la ripetono.

Contratto di una permutazione di dimensione n
---------------------------------------------
* lunghezza esattamente n (quando n e' richiesto);
* ogni elemento e' un intero secondo la politica sotto;
* ogni elemento e' compreso in 0..n-1;
* gli elementi sono distinti — quindi la mappa e' una bigezione.

Politica sui tipi
-----------------
* `int` di Python e interi NumPy (`numbers.Integral`): ACCETTATI, convertiti con
  `int(...)`.
* `bool` (True/False): RIFIUTATI, benche' siano `Integral`. Un flag usato come
  indice e' quasi sempre un errore del chiamante, e accettarlo lo maschererebbe.
* `float`, `Decimal`, stringhe numeriche: RIFIUTATI anche quando il valore e'
  intero (`3.0`, `"3"`). Convertirli con `int(...)` nasconderebbe un errore di
  rappresentazione invece di segnalarlo.
* contenitori: liste, tuple, `range`, array NumPy monodimensionali e qualunque
  iterabile finito. RIFIUTATI `str`, `bytes` e `dict` (iterabili, ma mai una
  permutazione) e gli array con piu' di una dimensione.

Glossario degli indici (M02)
----------------------------
Il programma usa tre numerazioni diverse; qui sono fissate una volta per tutte.

* `stage_index` — quale dei tre stadi del gioco: **0, 1, 2** (lo stadio 0 agisce
  per primo).  `T = S2 o S1 o S0`.
* `digit_index` — quale cifra in base 3 della posizione `n = 9*n2 + 3*n1 + n0`:
  **0 = meno significativa, 2 = piu' significativa**.  Le chiavi dei filtri
  `p0/p1/p2` e `j0/j1/j2` seguono questa numerazione: `p_k` agisce sulla cifra
  `k`, e il prodotto di Kronecker si scrive `P = P2 x P1 x P0`.
* numerazione storica **a base 1** (`stadio 1/2/3`, `P1/P2/P3`): sopravvive nei
  moduli che riproducono il formato del programma C originale
  (`core/detail.py`, `core/detail_pdf.py`) e nelle intestazioni esportate. NON
  va "corretta": e' un formato storico. Vale `stadio_storico = stage_index + 1`
  e `P_storico_k = P_(k-1)`.

Sono invece convenzioni matematiche gia' verificate in modo esaustivo (si veda
`tests/test_baseline_matematica.py`) e non vanno toccate:

    T[carta] = posizione di destinazione        deck[posizione] = carta
    M[T[i], i] = 1                              (a o b)[i] = a[b[i]]
"""
import numbers

__all__ = ["PermutazioneNonValida", "valida_permutazione", "valida_indice"]


class PermutazioneNonValida(ValueError):
    """L'ingresso non rispetta il contratto di permutazione del dominio."""


def _come_intero(valore, nome, posizione):
    if isinstance(valore, bool):
        raise PermutazioneNonValida(
            f"{nome}: valore booleano {valore!r} in posizione {posizione}; "
            "True/False non sono indici validi")
    if isinstance(valore, numbers.Integral):
        return int(valore)
    raise PermutazioneNonValida(
        f"{nome}: valore non intero {valore!r} in posizione {posizione} "
        f"(tipo {type(valore).__name__})")


def valida_permutazione(perm, n=None, *, nome="permutazione"):
    """Verifica il contratto e restituisce la permutazione come tupla di int.

    Parameters
    ----------
    perm : sequenza di interi
        La permutazione da validare, in convenzione `perm[i] = destinazione`.
    n : int, opzionale
        Dimensione attesa. Se omessa, viene dedotta dalla lunghezza (e la
        sequenza vuota e' rifiutata).
    nome : str
        Nome usato nei messaggi d'errore, di norma quello dell'API chiamante.

    Raises
    ------
    PermutazioneNonValida
        Con un messaggio che indica il primo problema trovato e dove.
    """
    if isinstance(perm, (str, bytes, bytearray, dict)):
        raise PermutazioneNonValida(
            f"{nome}: tipo non ammesso {type(perm).__name__}")
    forma = getattr(perm, "shape", None)
    if forma is not None and len(forma) != 1:
        raise PermutazioneNonValida(
            f"{nome}: attesa una sequenza monodimensionale, ricevuto shape {forma}")
    try:
        valori = list(perm)
    except TypeError:
        raise PermutazioneNonValida(
            f"{nome}: oggetto non iterabile ({type(perm).__name__})") from None

    if n is None:
        n = len(valori)
        if n == 0:
            raise PermutazioneNonValida(f"{nome}: sequenza vuota")
    elif len(valori) != n:
        raise PermutazioneNonValida(
            f"{nome}: lunghezza {len(valori)}, attesa {n}")

    interi = tuple(_come_intero(v, nome, i) for i, v in enumerate(valori))
    visti = set()
    for posizione, valore in enumerate(interi):
        if not 0 <= valore < n:
            raise PermutazioneNonValida(
                f"{nome}: valore {valore} fuori dall'intervallo 0..{n - 1} "
                f"(posizione {posizione})")
        if valore in visti:
            raise PermutazioneNonValida(
                f"{nome}: valore {valore} ripetuto (posizione {posizione}): "
                "non e' una bigezione")
        visti.add(valore)
    return interi


def valida_indice(valore, n, *, nome="indice"):
    """Verifica che `valore` sia un intero utilizzabile come indice in 0..n-1."""
    intero = _come_intero(valore, nome, 0)
    if not 0 <= intero < n:
        raise PermutazioneNonValida(
            f"{nome}: valore {intero} fuori dall'intervallo 0..{n - 1}")
    return intero
