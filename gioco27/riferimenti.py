"""Riferimenti alle fonti in un solo punto (Fase P, iterazioni 2 e 3).

Il programma cita due fonti DISTINTE, che non vanno confuse:

1. **il libro** (``LIBRO_MAIN``), compresa la sua Appendice D, cioe'
   l'articolo cosi' come e' incorporato nel libro;
2. **l'articolo originale** come pubblicazione autonoma, nella versione
   effettivamente letta durante lo sviluppo della 4.0 (``Articolo.pdf`` del
   10 settembre 2026), con la sua numerazione, oggi superata.

Libro
-----

La numerazione editoriale di teoremi, proposizioni e figure cambia quando il
libro viene riorganizzato. Prima della Fase G del libro i contatori non si
azzeravano a ogni capitolo (per esempio la forma normale delle trasformazioni
intermedie risultava 11.68 perche' contava tutti gli enunciati precedenti); dalla
Fase G si azzerano. Per non disseminare numeri fragili nel codice:

* ogni risultato citato ha una CHIAVE SEMANTICA stabile (per esempio
  ``"forma_normale_intermedie"``), usata da codice, servizi e test;
* titolo, etichetta LaTeX e sezione identificano il risultato in modo
  indipendente dal numero;
* il NUMERO CORRENTE sta soltanto in `RIFERIMENTI_LIBRO`; i testi
  dell'interfaccia (cataloghi di `gioco27.i18n`) contengono il segnaposto
  ``⟦rif:chiave⟧``, risolto qui all'import nella forma della lingua
  (per esempio «Teor. n.m» / «Thm. n.m»).

Quando il libro cambia numerazione si aggiorna solo questa tabella. I numeri
sono stati verificati sul sorgente LaTeX del libro (contatore ``definition``
condiviso da definizioni, proposizioni, teoremi, corollari, osservazioni ed
esempi; contatore ``figure``; entrambi azzerati a ogni capitolo) e confrontati
con ``LIBRO_MAIN.aux`` dove l'oggetto ha un'etichetta.

Le citazioni dell'Appendice D (numerazione propria per sezione, identica a
quella dell'articolo autonomo corrente: Def. 4.1, Teor. 4.2, Teor. 6.4,
Es. 7.1, ...) non dipendono dalla numerazione dei capitoli del libro e restano
nei testi come «App. D, …».

Articolo originale
------------------

Alcuni testi citano di proposito l'articolo nella versione letta per le
decisioni della 4.0 (`docs/decisions/V4_PRE_I5_DECISIONS.md`, DP1 = C:
entrambe le fonti, ciascuna citata dove sta). Quella versione ha una
numerazione diversa dall'Appendice D (§ 5 = fibre, § 6 = ventisette carte).
I numeri restano quelli di quella versione, ma stanno solo in
`RIFERIMENTI_ARTICOLO_ORIGINALE`; i cataloghi usano ``⟦art:chiave⟧``.

Modulo senza dipendenze: lo importano la i18n e, se serve, core e servizi.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional

__all__ = [
    "RiferimentoLibro", "RIFERIMENTI_LIBRO", "riferimento",
    "VersioneArticolo", "ARTICOLO_ORIGINALE",
    "RiferimentoArticolo", "RIFERIMENTI_ARTICOLO_ORIGINALE", "riferimento_articolo",
    "risolvi_riferimenti",
]


# ═══════════════════════════════════ libro ═══════════════════════════════════

@dataclass(frozen=True)
class RiferimentoLibro:
    """Un enunciato o una figura del libro, identificato in modo stabile."""

    tipo: str           # "teorema" | "proposizione" | "figura"
    numero: str         # numero CORRENTE nel libro (unico punto in cui compare)
    titolo: str         # titolo dell'enunciato o didascalia (o, se manca, sezione)
    etichetta: str      # \label LaTeX; "" se l'oggetto non ne ha una
    sezione: str        # sezione che lo contiene


#: Chiave semantica -> oggetto del libro (verificato sul sorgente LaTeX,
#: libro HEAD 8401b37, «Fase G: bonifica notazionale e riferimenti dinamici»).
RIFERIMENTI_LIBRO: Dict[str, RiferimentoLibro] = {
    # Ogni elemento di Γ si scrive in un solo modo come h ∘ MSC^r
    "forma_normale_intermedie": RiferimentoLibro(
        "teorema", "11.10", "Forma normale delle trasformazioni intermedie",
        "thm:formanormale-bm", "§ 11.7.4"),
    # Le somme di fibra ricostruiscono il tabellone
    "ricostruzione_fibre": RiferimentoLibro(
        "teorema", "11.12", "Ricostruzione mediante le fibre digitali",
        "thm:ricostruzione-fibre", "§ 11.9.5"),
    # 1728 procedure, otto per ciascuna delle 216 trasformazioni
    "uniformita_gioco_ordinario": RiferimentoLibro(
        "proposizione", "9.5", "Uniformità del Gioco ordinario",
        "prop:uniformita_gioco_ordinario", "§ 9.4"),
    # T auto-inversa ⟺ M_2² = M_1² = M_0² = I_3
    "autoinversa_tabellone": RiferimentoLibro(
        "proposizione", "5.2",
        "Condizione di auto-inversività della trasformazione globale",
        "", "§ 5.1.15"),
    # La griglia delle 27 classi di coniugio di G ≅ S3³ (prima della Fase G:
    # «fig. 6.8», contatore non azzerato per capitolo). I dati numerici
    # (#, card, ord, tipo) stanno nella tabella senza numero che la segue.
    "griglia_classi_coniugio": RiferimentoLibro(
        "figura", "6.3", "Griglia delle 27 classi di coniugio di G ≅ S₃³",
        "fig:coniugio-griglia", "§ 6.7"),
}


# ════════════════════════════ articolo originale ═════════════════════════════

@dataclass(frozen=True)
class VersioneArticolo:
    """Identificazione della versione dell'articolo citata dal programma."""

    titolo: str
    data: str
    sorgente: str
    pdf: str
    pubblicazione: str


#: La versione citata come «Articolo» nei testi della 4.0. Non esiste una
#: pubblicazione formale (nessun DOI, nessun tag): la si identifica con il
#: PDF letto e con il commit del repository dell'articolo il cui sorgente
#: coincide con quel PDF.
ARTICOLO_ORIGINALE = VersioneArticolo(
    titolo=("Permutazioni digitalmente separabili nei giochi di carte su b^m "
            "posizioni — Prodotti di Kronecker e ricostruzione da fibre digitali"),
    data="10 settembre 2026",
    sorgente=("github.com/maberlanda/27-card-tensor-structure, commit 8a2e41a "
              "(«Recepisce le osservazioni del referee»; sorgente identico fino a "
              "6f3cd03, poi la sezione sui rovesciamenti ha rinumerato tutto)"),
    pdf="Articolo.pdf, pdfTeX, CreationDate 2026-09-10 22:20:26 UTC, 11 pagine",
    pubblicazione="non pubblicato formalmente (CITATION.cff: «unpublished»)",
)


@dataclass(frozen=True)
class RiferimentoArticolo:
    """Un enunciato dell'articolo originale (numerazione di quella versione)."""

    tipo: str                    # "teorema" | "osservazione" | "esempio"
    numero: str                  # numero nella versione ARTICOLO_ORIGINALE
    contenuto: str               # titolo o sintesi dell'enunciato
    equivalente_app_d: Optional[str]   # enunciato identico in App. D, se esiste


RIFERIMENTI_ARTICOLO_ORIGINALE: Dict[str, RiferimentoArticolo] = {
    "statistiche_fibra": RiferimentoArticolo(
        "teorema", "5.1", "Formula delle statistiche di fibra",
        "App. D, Teor. 6.1"),
    # Nessun equivalente identico: l'App. D sostituisce questa cautela con il
    # criterio dimostrato (Teor. 6.4); la sua Oss. 6.3 parla d'altro
    # (non minimalita' delle statistiche).
    "somme_non_criterio": RiferimentoArticolo(
        "osservazione", "5.3",
        "le somme ricostruiscono i fattori entro la classe separabile; la sola "
        "compatibilità numerica non è assunta come criterio per una permutazione "
        "arbitraria",
        None),
    "ricostruzione_codice": RiferimentoArticolo(
        "esempio", "6.1", "Ricostruzione di un codice", "App. D, Es. 7.1"),
}


# ═════════════════════════════════ forma breve ═══════════════════════════════

_ABBREVIAZIONI = {
    "it": {"teorema": "Teor.", "proposizione": "Prop.", "figura": "Fig.",
           "osservazione": "Oss.", "esempio": "Es."},
    "en": {"teorema": "Thm.", "proposizione": "Prop.", "figura": "Fig.",
           "osservazione": "Obs.", "esempio": "Ex."},
}

_SEGNAPOSTO = re.compile(r"⟦(rif|art):([a-z0-9_]+)⟧")


def _breve(tipo: str, numero: str, lingua: str) -> str:
    abbreviazioni = _ABBREVIAZIONI.get(lingua, _ABBREVIAZIONI["it"])
    return f"{abbreviazioni[tipo]} {numero}"


def riferimento(chiave: str, lingua: str = "it") -> str:
    """Libro: abbreviazione della lingua + numero corrente della tabella."""
    r = RIFERIMENTI_LIBRO[chiave]
    return _breve(r.tipo, r.numero, lingua)


def riferimento_articolo(chiave: str, lingua: str = "it") -> str:
    """Articolo originale: abbreviazione della lingua + numero di quella versione."""
    r = RIFERIMENTI_ARTICOLO_ORIGINALE[chiave]
    return _breve(r.tipo, r.numero, lingua)


def risolvi_riferimenti(testo: str, lingua: str = "it") -> str:
    """Sostituisce ``⟦rif:chiave⟧`` (libro) e ``⟦art:chiave⟧`` (articolo originale).

    Una chiave sconosciuta solleva KeyError: un segnaposto non risolto non
    deve mai arrivare all'utente.
    """
    def _sostituisci(m):
        fonte, chiave = m.group(1), m.group(2)
        if fonte == "rif":
            return riferimento(chiave, lingua)
        return riferimento_articolo(chiave, lingua)
    return _SEGNAPOSTO.sub(_sostituisci, testo)
