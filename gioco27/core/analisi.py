"""Pipeline dell'analisi: schema, validazione, piano, aggregazione.

Compartimento F. Prima di questo modulo l'analisi non aveva una fase di
ingresso: `analizza_righe` leggeva `T_permutazione` con un `int()` dentro un
`try/except ValueError: continue`, e `analizza_csv` cercava le colonne per
sottostringa. Le conseguenze erano due bug distinti:

* **B05** — una `T` come ``[0,0,99]`` (valori ripetuti, fuori intervallo, di
  lunghezza sbagliata) veniva accettata come risultato valido, e un file con
  intestazione ``foo;bar`` produceva ``[]``: un'analisi valida con zero
  risultati, indistinguibile da un dominio vuoto. Le righe corrotte sparivano
  senza lasciare traccia.
* **R01** — l'analisi materializzava ogni riga in una lista prima di
  aggregare. Con i filtri liberi sono 5.159.780.352 combinazioni: misurate a
  ~1 kB e ~59 µs ciascuna, sono 5,4 TB e 85 ore. L'unica difesa era una
  finestra «sei sicuro?».

La pipeline e' ora esplicita e ogni fase ha un esito dichiarato:

    ingresso
      │
      ├─ riconoscimento schema   riconosci_schema()   → SchemaNonRiconosciuto
      ├─ validazione riga        Aggregatore.aggiungi() → RigaScartata
      ├─ piano e budget          pianifica_analisi()  → AnalisiTroppoGrande
      ├─ enumerazione            core.combinations (contratto unico dei filtri)
      └─ aggregazione            Aggregatore          → risultati + diagnostica

Nessuna fase interpreta un ingresso invalido come «zero risultati», e il
conteggio che decide il piano e' lo stesso che descrive cio' che verra'
enumerato.

Il modulo non conosce Tk ne' la GUI. Usa i contratti gia' esistenti invece di
riscriverli: `core.dominio.valida_permutazione` (D) per la `T` e il parser
unico di `core.espressione` (E) per la formula.
"""

import csv as _csv
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Tuple

from .combinations import cardinalita, normalizza_filtri
from .dominio import PermutazioneNonValida, valida_permutazione

__all__ = [
    "SchemaNonRiconosciuto", "AnalisiTroppoGrande", "SchemaCsv", "RigaScartata",
    "RisultatiImport", "Aggregatore", "PianoAnalisi", "SCHEMI",
    "riconosci_schema", "pianifica_analisi", "importa_csv", "aggrega_righe",
    "LIMITE_GREZZI", "LIMITE_ANALISI", "N_CARTE",
]

#: Dimensione del mazzo: ogni `T` importata e' una permutazione di 27 elementi.
N_CARTE = 27


class SchemaNonRiconosciuto(ValueError):
    """L'intestazione del file non appartiene a nessuno schema supportato.

    Distinta da un'analisi senza risultati: un file che non si sa leggere non
    e' un dominio vuoto.
    """


class AnalisiTroppoGrande(ValueError):
    """Il dominio richiesto supera il budget dell'analisi in memoria."""

    def __init__(self, richieste, limite=None):
        self.richieste = richieste
        self.limite = LIMITE_ANALISI if limite is None else limite
        super().__init__(
            f"analisi di {richieste:,} combinazioni: oltre il limite di "
            f"{self.limite:,}. Il dominio va ristretto con i filtri.")


# ═══════════════════════════════ schema CSV ═════════════════════════════════
#
# Gli schemi non sono inventati qui: sono quelli che il programma stesso
# produce. `core.permutations.CSV_HEADER` genera il CSV COMBINAZIONI (una riga
# per combinazione) e `core.algebra.scrivi_output` il CSV ANALISI (una riga per
# T distinta). Le intestazioni reali portano una descrizione fra parentesi
# quadre — «T_permutazione  [lista 0..26]» — quindi il riconoscimento guarda il
# primo token, non l'intera cella.


@dataclass(frozen=True)
class SchemaCsv:
    """Uno schema di file riconosciuto, con i suoi campi."""

    nome: str
    obbligatorie: Tuple[str, ...]
    opzionali: Tuple[str, ...] = ()
    importabile: bool = True
    motivo: str = ""


SCHEMA_COMBINAZIONI = SchemaCsv(
    nome="combinazioni",
    obbligatorie=("t_permutazione",),
    opzionali=("#", "stage0", "stage1", "stage2", "a0", "a1", "a2",
               "t_simbolica"))

#: Export dell'analisi: una riga per T distinta, con l'elenco delle simboliche
#: gia' aggregate. Viene riconosciuto per poterlo **rifiutare con il suo nome**:
#: rileggerlo come se fosse un CSV combinazioni conterebbe una sola sequenza per
#: permutazione (molteplicita' 1 ovunque), un risultato plausibile e sbagliato.
SCHEMA_ANALISI = SchemaCsv(
    nome="analisi",
    obbligatorie=("t_permutazione", "t_simboliche_distinte"),
    opzionali=("n_sim_distinte",),
    importabile=False,
    motivo="e' l'export di un'analisi (una riga per T, simboliche gia' "
           "aggregate), non un CSV di combinazioni")

SCHEMI = (SCHEMA_ANALISI, SCHEMA_COMBINAZIONI)   # il piu' specifico per primo


def _campo(cella):
    """Primo token dell'intestazione, senza BOM e in minuscolo."""
    return cella.lstrip("﻿").strip().split()[0].lower() if cella.strip() else ""


def riconosci_schema(intestazione):
    """Riconosce lo schema di un'intestazione CSV.

    Restituisce `(schema, indici)` dove `indici` mappa il nome del campo alla
    sua colonna. Solleva `SchemaNonRiconosciuto` se nessuno schema corrisponde,
    o se quello riconosciuto non e' importabile.
    """
    if not intestazione:
        raise SchemaNonRiconosciuto("file senza intestazione")
    indici = {}
    for colonna, cella in enumerate(intestazione):
        nome = _campo(cella)
        if nome and nome not in indici:      # la prima colonna omonima vince
            indici[nome] = colonna
    for schema in SCHEMI:
        if all(campo in indici for campo in schema.obbligatorie):
            if not schema.importabile:
                raise SchemaNonRiconosciuto(
                    f"schema «{schema.nome}»: {schema.motivo}")
            return schema, {c: indici[c] for c in
                            schema.obbligatorie + schema.opzionali
                            if c in indici}
    raise SchemaNonRiconosciuto(
        "intestazione non riconosciuta: manca la colonna «T_permutazione». "
        f"Trovate {sorted(indici)[:8]}")


# ═════════════════════════ righe scartate e risultati ═══════════════════════

@dataclass(frozen=True)
class RigaScartata:
    """Una riga rifiutata, con dove e perche'."""

    numero: int
    campo: str
    motivo: str

    def __str__(self):
        return f"riga {self.numero}, {self.campo}: {self.motivo}"


class RisultatiImport(list):
    """I risultati aggregati, piu' la diagnostica di come sono stati ottenuti.

    E' una `list` perche' i risultati aggregati sono sempre stati una lista e
    ogni chiamante (GUI, export, test) continua a usarli come tale. Gli
    attributi portano cio' che prima andava perduto: quale schema e' stato
    letto, quante righe sono state lette e quali sono state scartate.

    Il modello condiviso dei risultati fra le schede appartiene a G: questa
    resta una lista con tre attributi, non una nuova gerarchia.
    """

    def __init__(self, risultati=(), *, schema=None, lette=0, scartate=()):
        super().__init__(risultati)
        self.schema = schema
        self.lette = lette
        self.scartate = tuple(scartate)

    @property
    def parziale(self):
        """True se qualcosa e' stato scartato: l'import non e' completo."""
        return bool(self.scartate)

    def diagnostica(self, massimo=3):
        """Riassunto leggibile, vuoto quando non c'e' nulla da segnalare."""
        if not self.scartate:
            return ""
        primi = "; ".join(str(s) for s in self.scartate[:massimo])
        resto = (f" (+{len(self.scartate) - massimo} altre)"
                 if len(self.scartate) > massimo else "")
        return (f"{len(self.scartate)} righe scartate su {self.lette}: "
                f"{primi}{resto}")


# ═══════════════════════════════ aggregazione ═══════════════════════════════

def _perm_da_stringa(testo):
    """«[0,1,...,26]» → tupla di 27 interi validata secondo il contratto D."""
    grezzo = (testo or "").strip()
    if not grezzo:
        raise PermutazioneNonValida("T_permutazione: campo vuoto")
    interno = grezzo.strip("[]").strip()
    if not interno:
        raise PermutazioneNonValida("T_permutazione: lista vuota")
    valori = []
    for pezzo in interno.split(","):
        pezzo = pezzo.strip()
        try:
            valori.append(int(pezzo))
        except ValueError:
            raise PermutazioneNonValida(
                f"T_permutazione: valore non intero {pezzo!r}") from None
    return valida_permutazione(valori, N_CARTE, nome="T_permutazione")


def _formula_di(riga):
    """La formula simbolica della riga, se il formato ne porta una."""
    s0, s1, s2 = (riga.get(f"Stage{i}", "") or "" for i in range(3))
    if s0 or s1 or s2:
        return f"T = [{s2}] o [{s1}] o [{s0}]"
    return (riga.get("T_simbolica", "") or "").strip()


@dataclass
class Aggregatore:
    """Aggrega le righe una per volta, validandole all'ingresso.

    Incrementale per costruzione: `aggiungi` aggiorna i gruppi e non richiede
    che le righe esistano tutte insieme. Le righe grezze vengono conservate
    **solo** se il piano lo consente (`tieni_grezzi`); quando non lo sono,
    `grezzi` resta vuoto e il modello di C disabilita da solo gli export che le
    richiedono — nessun export puo' presentare come completo cio' che non e'
    stato tenuto.

    `verifica_formula` accende il controllo di coerenza fra la formula
    simbolica e la `T` della riga, usando il parser unico di E. E' acceso
    sull'import (dati non fidati) e spento sull'analisi dai filtri, dove le
    righe le ha appena generate il programma (misurato: ~51 µs a formula).
    """

    tieni_grezzi: bool = True
    verifica_formula: bool = False
    #: Quando False l'aggregatore **trattiene soltanto**: niente gruppi e
    #: niente validazione, che verranno da `aggrega_righe` sulle righe
    #: trattenute. Serve a chi tiene comunque tutte le righe (analisi piccola)
    #: e non vuole ne' contarle ne' validarle due volte; l'implementazione
    #: dell'aggregazione e della validazione resta una sola, questa.
    aggrega: bool = True
    lette: int = 0
    _gruppi: dict = field(default_factory=lambda: defaultdict(
        lambda: {"simboliche": set(), "perm_str": ""}))
    _grezzi: list = field(default_factory=list)
    _scartate: list = field(default_factory=list)

    def aggiungi(self, riga, numero=None):
        """Valida e aggrega una riga. True se e' entrata nei risultati."""
        self.lette += 1
        n = self.lette if numero is None else numero
        if not self.aggrega:
            # sola raccolta: chi aggreghera' queste righe le validera' allora
            if self.tieni_grezzi:
                self._grezzi.append(riga)
            return True
        try:
            perm = _perm_da_stringa(riga.get("T_permutazione", ""))
        except PermutazioneNonValida as errore:
            self._scartate.append(RigaScartata(n, "T_permutazione", str(errore)))
            return False

        formula = _formula_di(riga)
        if self.verifica_formula and formula:
            problema = self._confronta(formula, perm)
            if problema:
                self._scartate.append(RigaScartata(n, "T_simbolica", problema))
                return False

        gruppo = self._gruppi[perm]
        gruppo["simboliche"].add(formula)
        gruppo["perm_str"] = riga.get("T_permutazione", "").strip()
        if self.tieni_grezzi:
            self._grezzi.append(riga)
        return True

    @staticmethod
    def _confronta(formula, perm):
        """None se la formula vale `perm`, altrimenti il motivo dello scarto."""
        # Import locale: `core.espressione` importa `core.algebra`, che importa
        # questo modulo. Il ciclo si spezza qui, alla prima chiamata.
        from .espressione import ParseError, permutazione_di
        try:
            calcolata = permutazione_di(formula)
        except ParseError as errore:
            return f"formula non valida ({errore})"
        except ValueError as errore:
            return f"formula non valutabile ({errore})"
        if tuple(calcolata) != tuple(perm):
            return ("la formula non produce la T della riga "
                    f"({formula[:60]})")
        return None

    @property
    def scartate(self):
        return tuple(self._scartate)

    @property
    def grezzi(self):
        return tuple(self._grezzi)

    def risultati(self):
        """I gruppi ordinati per molteplicita' decrescente, come sempre."""
        risultati = [{
            "perm_tuple": perm,
            "perm_str":   gruppo["perm_str"],
            "simboliche": sorted(gruppo["simboliche"]),
            "n_sim":      len(gruppo["simboliche"]),
        } for perm, gruppo in self._gruppi.items()]
        risultati.sort(key=lambda r: (-r["n_sim"], r["perm_tuple"]))
        return risultati

    def esito(self, schema=None):
        """I risultati con la loro diagnostica."""
        return RisultatiImport(self.risultati(), schema=schema,
                               lette=self.lette, scartate=self.scartate)


def aggrega_righe(righe, *, verifica_formula=False):
    """Aggrega un iterabile di righe gia' in memoria (percorso storico)."""
    aggregatore = Aggregatore(tieni_grezzi=False,
                              verifica_formula=verifica_formula)
    for riga in righe:
        aggregatore.aggiungi(riga)
    return aggregatore.esito()


# ══════════════════════════════ import da CSV ═══════════════════════════════

def importa_csv(percorso, *, verifica_formula=True):
    """Legge un CSV COMBINAZIONI e restituisce i risultati con la diagnostica.

    Solleva `SchemaNonRiconosciuto` se l'intestazione non appartiene a uno
    schema supportato: un file che non si sa leggere non e' un'analisi vuota.
    Le righe valide vengono aggregate, quelle invalide elencate in `scartate`
    con numero di riga, campo e motivo.

    `encoding="utf-8-sig"` toglie il BOM che Excel antepone ai CSV salvati in
    UTF-8; senza, la prima intestazione sarebbe «﻿T_permutazione».
    """
    aggregatore = Aggregatore(tieni_grezzi=False,
                              verifica_formula=verifica_formula)
    with open(percorso, newline="", encoding="utf-8-sig") as f:
        lettore = _csv.reader(f, delimiter=";", quotechar='"')
        try:
            intestazione = next(lettore)
        except StopIteration:
            raise SchemaNonRiconosciuto("file vuoto: nessuna intestazione") from None
        schema, indici = riconosci_schema(intestazione)

        for numero, riga in enumerate(lettore, start=2):   # 1 = intestazione
            if not riga or not any(c.strip() for c in riga):
                continue                                    # riga vuota
            def valore(campo):
                i = indici.get(campo)
                return riga[i].strip() if i is not None and i < len(riga) else ""
            aggregatore.aggiungi({
                "Stage0":         valore("stage0"),
                "Stage1":         valore("stage1"),
                "Stage2":         valore("stage2"),
                "T_simbolica":    valore("t_simbolica"),
                "T_permutazione": valore("t_permutazione"),
            }, numero=numero)
    return aggregatore.esito(schema=schema)


# ═══════════════════════ piano e budget dell'analisi ════════════════════════
#
# Le soglie sono misurate, non scelte a occhio (campione di 15.552 combinazioni,
# ambiente di riferimento):
#
#   riga grezza trattenuta      ~796 B     aggregati       ~220 B per riga
#   generazione + aggregazione  ~59 µs per riga
#
# da cui:
#
#   100.000 combinazioni   ~105 MB con i grezzi,  ~6 s
#   1.000.000              ~220 MB senza grezzi, ~59 s
#   5.159.780.352          ~5,4 TB e ~85 ore — il caso di R01
#
# Il limite di export (`MAX_EXPORT_ITEMS`, 20 milioni) resta un'altra cosa: un
# export scrive su disco e non trattiene nulla in memoria, quindi puo'
# permettersi molto di piu' di un'analisi che tiene in RAM gruppi e formule.

#: Oltre questo numero di combinazioni le righe grezze non vengono conservate:
#: restano gli aggregati, completi, e gli export che richiedono i grezzi si
#: disabilitano da soli (contratto di C: `grezzi=()`).
LIMITE_GREZZI = 100_000

#: Oltre questo numero l'analisi viene rifiutata **prima** di enumerare: gli
#: aggregati stessi non sarebbero piu' contenibili in memoria.
LIMITE_ANALISI = 1_000_000


@dataclass(frozen=True)
class PianoAnalisi:
    """Che cosa verra' fatto, deciso prima di enumerare qualunque cosa."""

    combinazioni: int
    grezzi: bool
    limite_grezzi: int = LIMITE_GREZZI
    limite_analisi: int = LIMITE_ANALISI

    @property
    def modalita(self):
        return "completa" if self.grezzi else "aggregata"


def pianifica_analisi(filtri):
    """Valida i filtri, conta il dominio e decide la modalita'.

    Non enumera nulla: la cardinalita' e' un prodotto di lunghezze. Solleva
    `FiltroNonValido` se i filtri non rispettano il contratto e
    `AnalisiTroppoGrande` se il dominio non e' analizzabile in sicurezza.
    """
    normalizzati = normalizza_filtri(filtri)
    n = cardinalita(normalizzati)
    if n > LIMITE_ANALISI:
        raise AnalisiTroppoGrande(n, LIMITE_ANALISI)
    return PianoAnalisi(combinazioni=n, grezzi=(n <= LIMITE_GREZZI))
