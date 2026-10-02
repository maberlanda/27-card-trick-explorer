"""Esperimenti versionati, verificabili e riproducibili (compartimento J).

Un esperimento e' un documento JSON che fissa lo **stato scientifico** di una
sessione — per ogni strumento l'input e il risultato minimo — insieme alle
convenzioni con cui e' stato calcolato, alla provenienza e, se c'e', alla
cronologia applicativa. Niente Tk, niente testo: codici stabili e dati.

Principi
--------

* **Il caricamento ricalcola.** Un risultato non diventa vero perche' il JSON
  lo dice: `verifica_documento` rivalida lo schema, ricostruisce gli input e
  ricalcola ogni risultato con i servizi autorevoli (I1, I2, I5, I6, J/L90,
  parser del core), poi confronta. Esiti: VERIFIED, MISMATCH,
  INCOMPATIBLE_CONVENTION, UNSUPPORTED_SCHEMA, CORRUPT.
* **Due digest.** ``scientifico`` = SHA-256 del JSON canonico di schema,
  versione delle convenzioni, seed e voci (strumento, tipo, input,
  risultato), senza timestamp, identificativi, annotazioni, presentazione,
  cronologia o testo localizzato. ``documento`` = SHA-256 del documento intero
  meno il campo ``digest``: cambia anche per un titolo o una nota.
* **JSON canonico.** UTF-8, chiavi ordinate, separatori compatti,
  ``ensure_ascii=False``; l'ordine delle liste e' significativo (una
  successione di procedure non e' un insieme).
* **Sicurezza.** Nessun pickle, eval o import dinamico; limiti espliciti di
  dimensione; chiavi duplicate, NaN e campi sconosciuti rifiutati; i percorsi
  nel manifesto sono dati e non vengono mai aperti.

Convenzioni: ``CONVENZIONI`` le elenca una per una (non una stringa opaca), e
``CONVENTION_VERSION`` le identifica. Il loader confronta entrambe e riporta
quali regole differiscono. La versione del programma (``gioco27.__version__``)
e' solo informativa: non decide la compatibilita'.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from .. import __version__ as _VERSIONE_PROGRAMMA
from ..core import gioco_reale as _gr
from ..core.algebra import AlgebraEngine as _AE
from ..core.config import LIVELLI_DIDATTICI

__all__ = [
    "SCHEMA_ID", "SCHEMA_VERSION", "CONVENTION_VERSION", "CONVENZIONI", "ALGORITMI",
    "STRUMENTI", "LIMITI", "MIGRAZIONI", "Stato", "EsperimentoNonValido",
    "Discrepanza", "RapportoVerifica", "Confronto",
    "json_canonico", "sha256", "calcola_risultato", "crea_documento",
    "digest_scientifico", "digest_documento", "valida_documento", "migra",
    "verifica_documento", "verifica_testo", "confronta", "fonte",
    "procedura_in_dati", "procedura_da_dati", "adesso", "leggi_json",
]

SCHEMA_ID = "gioco27.esperimento"
SCHEMA_VERSION = 1
CONVENTION_VERSION = "J1"

#: Le convenzioni scientifiche, una per chiave: diagnosticabili una per una.
CONVENZIONI: Dict[str, str] = {
    "posizioni": "0..26, 0 = cima del mazzo",
    "trasformazione": "T[origine] = destinazione",
    "mazzo": "deck[posizione] = carta; il mazzo finale di un mazzo ordinato e' T^-1",
    "applicazione": "v'[T[i]] = v[i]",
    "composizione": "(a o b)[i] = a[b[i]]: prima agisce b",
    "rovesciamento": "DP3=A: il mazzo si rovescia prima della distribuzione dello stadio",
    "cifre": "n = 9*n2 + 3*n1 + n0; digits3(n) = (n2, n1, n0); livello i = cifra di peso 3^i",
    "msc": "core.algebra.AlgebraEngine.MSC_PERM: (a2 a1 a0) -> 9*a0 + 3*a2 + a1 = "
           + " ".join(str(x) for x in _AE.MSC_PERM),
    "gruppi": "H = 216 trasformazioni separabili; Gamma = 648 (esteso); S27 ambiente",
    "tavola": "# = k1 + 6*k2 + 36*k3 con SIGLE = " + ",".join(_gr.SIGLE),
    "procedura": "(mescolamenti M0 M1 M2 in ordine cronologico; rovesciamenti e1 e2 e3); m = 4e1 + 2e2 + e3",
}

#: Metadati degli algoritmi (informativi: il confronto li segnala, non bloccano).
ALGORITMI: Dict[str, str] = {
    "procedura": "I1", "trucco": "I1+risolvi_trucco", "riconoscimento": "I5",
    "proprieta": "I6", "successione": "J1-L90", "espressione": "core.algebra.Controller",
}

#: strumento → tipo di voce (una voce per strumento in un documento)
STRUMENTI: Dict[str, str] = {
    "explorer": "espressione", "simulatore": "trucco", "tavola": "procedura",
    "riconoscimento": "riconoscimento", "laboratorio": "proprieta",
    "successione": "successione",
}

LIMITI = {
    "byte": 5 * 1024 * 1024, "titolo": 200, "nota": 20000, "espressione": 4096,
    "procedure": 1000, "eventi": 2000, "fonti": 16, "voci": len(STRUMENTI),
}

#: versione → funzione che porta un documento alla versione successiva.
#: Vuoto: la versione 1 e' la prima ufficiale, non esiste un formato storico.
MIGRAZIONI: Dict[int, Callable[[dict], dict]] = {}

_SCHEDE = ("inizio", "simulatore", "tavola", "guida", "anteprima", "cicli", "explorer",
           "analisi", "distribuzione", "stadio0", "stadio1", "stadio2")


class Stato(str, Enum):
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    INCOMPATIBLE_CONVENTION = "INCOMPATIBLE_CONVENTION"
    UNSUPPORTED_SCHEMA = "UNSUPPORTED_SCHEMA"
    CORRUPT = "CORRUPT"


class EsperimentoNonValido(ValueError):
    """Documento rifiutato: `codice` stabile, `percorso` del campo, `dati`."""

    def __init__(self, codice, percorso="", **dati):
        super().__init__(f"{codice}: {percorso}")
        self.codice = codice
        self.percorso = percorso
        self.dati = dati


@dataclass(frozen=True)
class Discrepanza:
    voce: str               # id della voce, o "documento"
    campo: str
    registrato: Any
    ricalcolato: Any


@dataclass(frozen=True)
class RapportoVerifica:
    stato: Stato
    codice: str                                    # dettaglio stabile
    diagnosi: Tuple[Discrepanza, ...] = ()
    documento: Optional[dict] = None               # valido (anche se MISMATCH)

    @property
    def verificato(self) -> bool:
        return self.stato is Stato.VERIFIED


# ═════════════════════════ JSON canonico e digest ══════════════════════════

def json_canonico(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def sha256(dati: bytes) -> str:
    return hashlib.sha256(dati).hexdigest()


def _contenuto_scientifico(doc: dict) -> dict:
    voci = sorted(({k: v[k] for k in ("strumento", "tipo", "input", "risultato")}
                   for v in doc["voci"]), key=lambda v: v["strumento"])
    return {"schema": doc["schema"], "schema_version": doc["schema_version"],
            "convenzioni": doc["convenzioni"]["versione"], "seed": doc["seed"],
            "voci": voci}


def digest_scientifico(doc: dict) -> str:
    return sha256(json_canonico(_contenuto_scientifico(doc)))


def digest_documento(doc: dict) -> str:
    return sha256(json_canonico({k: v for k, v in doc.items() if k != "digest"}))


def _digest_voce(voce: dict) -> str:
    return sha256(json_canonico({k: voce[k] for k in
                                 ("strumento", "tipo", "algoritmo", "input", "risultato")}))


def adesso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ═══════════════════════ procedure ↔ dati JSON ═════════════════════════════

def procedura_in_dati(p) -> dict:
    return {"mescolamenti": list(p.mescolamenti), "rovesciamenti": list(p.rovesciamenti)}


def procedura_da_dati(d, percorso="procedura"):
    from .procedure import ProceduraGioco, ProceduraNonValida
    _chiavi(d, {"mescolamenti", "rovesciamenti"}, percorso)
    try:
        return ProceduraGioco(tuple(d["mescolamenti"]), tuple(d["rovesciamenti"]))
    except (ProceduraNonValida, TypeError) as e:
        raise EsperimentoNonValido("valore_non_valido", percorso,
                                   causa=getattr(e, "codice", "procedura")) from None


# ═══════════════════════ ricalcolo con i servizi autorevoli ════════════════

def _lista(p):
    return [int(x) for x in p]


def _jsonabile(x):
    """Tuple → liste, ricorsivamente (per confrontare dopo un round-trip JSON)."""
    if isinstance(x, (list, tuple)):
        return [_jsonabile(v) for v in x]
    if isinstance(x, dict):
        return {str(k): _jsonabile(v) for k, v in x.items()}
    return x


def _calcola_procedura(inp, seed):
    from .procedure import servizio_procedure
    p = procedura_da_dati(inp, "input")
    T = servizio_procedure().trasformazione(p)
    return {"T": _lista(T), "numero_tavola": p.numero_tavola,
            "identificatore": list(p.identificatore),
            "numero_trasformazione": _numero_di(T)}


def _numero_di(T):
    from . import tabellone
    return tabellone.numero_di(T)


def _calcola_espressione(inp, seed):
    from ..core.algebra import Controller
    r = Controller().process(inp["testo"])
    ok = bool(r["ok"]) and r.get("perm") is not None
    return {"ok": ok, "T": _lista(r["perm"]) if ok else None}


def _calcola_trucco(inp, seed):
    fissa = inp["disposizione_fissata"]
    if fissa is None:
        piano = _gr.risolvi_trucco(inp["carta"], inp["bersaglio"])
        mesc, numero, T = piano["mescolamenti"], piano["numero"], piano["T"]
        bersaglio = inp["bersaglio"]
    else:
        riga = _gr.riga_tavola(fissa)
        mesc, numero, T = riga["mescolamenti"], riga["numero"], riga["T"]
        bersaglio = T[inp["carta"]]
    return {"mescolamenti": list(mesc), "numero_tavola": int(numero), "T": _lista(T),
            "bersaglio": int(bersaglio)}


def _calcola_riconoscimento(inp, seed):
    from . import riconoscimento as rc
    p = rc.permutazione(inp["T"])
    sep = rc.separabile(p)
    ce = rc.classe_estesa(p)
    # "classe_estesa" e' la chiave tecnica dello schema 1 (file gia' salvati e
    # impronte): indica l'esponente k con T ∈ H∘MSC^k, cioe' l'appartenenza a Γ,
    # oppure None fuori da Γ. Nei testi per l'utente si chiama Γ.
    return {"separabile": sep.separabile, "numero_tavola": sep.numero_tavola,
            "classe_estesa": ce.k if ce.appartiene else None,
            "criterio_somme": rc.criterio_somme(p).vero}


def _calcola_proprieta(inp, seed):
    from . import laboratorio as lab
    try:
        v = lab.verifica(inp["proprieta"], lab.Dominio(inp["dominio"]))
    except (lab.ProprietaSconosciuta, lab.DominioNonPrevisto, ValueError):
        raise EsperimentoNonValido("valore_non_valido", "input",
                                   proprieta=inp["proprieta"], dominio=inp["dominio"]) from None
    ce = v.controesempio
    return {"esito": v.esito.value, "metodo": v.metodo.value, "controllati": v.controllati,
            "totale": v.totale, "fonte": v.fonte,
            "controesempio": None if ce is None else {
                "codice": ce.codice, "elementi": _jsonabile(ce.elementi),
                "dati": _jsonabile(dict(ce.dati))}}


def _successione_da_input(inp, seed):
    from .successione import Successione, procedure_casuali, IDENTITA
    procedure = tuple(procedura_da_dati(d, f"input.procedure[{i}]")
                      for i, d in enumerate(inp["procedure"]))
    gen = inp["generatore"]
    if gen is not None:
        if seed is None:
            raise EsperimentoNonValido("seed_mancante", "seed")
        attese = procedure_casuali(gen["n"], seed)
        if attese != procedure:
            raise _Discorde("input.procedure", [procedura_in_dati(p) for p in procedure],
                            [procedura_in_dati(p) for p in attese])
    mazzo = IDENTITA if inp["mazzo_iniziale"] is None else tuple(inp["mazzo_iniziale"])
    return Successione(procedure, mazzo)


class _Discorde(Exception):
    def __init__(self, campo, registrato, ricalcolato):
        super().__init__(campo)
        self.campo, self.registrato, self.ricalcolato = campo, registrato, ricalcolato


def _calcola_successione(inp, seed):
    s = _successione_da_input(inp, seed)
    C = s.cumulativo()
    return {"passi": [p.numero_tavola for p in s.passi()],
            "cumulativo": _lista(C), "numero_cumulativo": _numero_di(C),
            "ritorno": procedura_in_dati(s.ritorno_procedura()),
            "mazzo_finale": _lista(s.disposizione_finale())}


_CALCOLI = {
    "procedura": _calcola_procedura, "espressione": _calcola_espressione,
    "trucco": _calcola_trucco, "riconoscimento": _calcola_riconoscimento,
    "proprieta": _calcola_proprieta, "successione": _calcola_successione,
}


def calcola_risultato(tipo: str, inp: dict, seed=None) -> dict:
    """Il risultato minimo di una voce, dai soli input, con i servizi autorevoli."""
    return _jsonabile(_CALCOLI[tipo](inp, seed))


# ═══════════════════════════════ costruzione ═══════════════════════════════

def fonte(nome: str, ruolo: str, percorso=None) -> dict:
    """Voce di provenienza: sha256 solo se il file c'e' davvero (mai incorporato)."""
    disponibile, h = False, None
    if percorso is not None:
        p = Path(percorso)
        if p.is_file():
            digest = hashlib.sha256()
            with open(p, "rb") as f:
                for blocco in iter(lambda: f.read(1 << 20), b""):
                    digest.update(blocco)
            disponibile, h = True, digest.hexdigest()
    return {"nome": str(nome), "ruolo": str(ruolo), "sha256": h, "disponibile": disponibile}


def crea_documento(stato_scientifico: Dict[str, dict], *, seed=None, titolo="", nota="",
                   presentazione=None, cronologia=None, fonti=(), revisioni=None,
                   esperimento_id=None, creato=None, modificato=None) -> dict:
    """Documento completo dallo stato scientifico {strumento: input}.

    I risultati vengono SEMPRE calcolati qui: il chiamante non puo' passarne.
    """
    voci = []
    for n, strumento in enumerate(sorted(stato_scientifico), 1):
        tipo = STRUMENTI[strumento]
        inp = _jsonabile(stato_scientifico[strumento])
        voce = {"id": f"v{n}", "strumento": strumento, "tipo": tipo,
                "revisione": int((revisioni or {}).get(strumento, 0)),
                "algoritmo": ALGORITMI[tipo], "input": inp,
                "risultato": calcola_risultato(tipo, inp, seed)}
        voce["digest"] = _digest_voce(voce)
        voci.append(voce)
    ora = adesso()
    doc = {
        "schema": SCHEMA_ID, "schema_version": SCHEMA_VERSION,
        "convenzioni": {"versione": CONVENTION_VERSION, "regole": dict(CONVENZIONI)},
        "programma": {"nome": "gioco27", "versione": _VERSIONE_PROGRAMMA},
        "algoritmi": dict(ALGORITMI),
        "id": esperimento_id or uuid.uuid4().hex,
        "creato": creato or ora, "modificato": modificato or ora,
        "annotazioni": {"titolo": titolo, "nota": nota},
        "seed": seed,
        "voci": voci,
        "presentazione": presentazione,
        "cronologia": cronologia,
        "fonti": [dict(f) for f in fonti],
    }
    doc["digest"] = {"scientifico": digest_scientifico(doc), "documento": ""}
    doc["digest"]["documento"] = digest_documento(doc)
    valida_documento(doc)
    return doc


# ═══════════════════════════════ validazione ═══════════════════════════════

def _chiavi(d, attese, percorso, facoltative=()):
    if not isinstance(d, dict):
        raise EsperimentoNonValido("tipo_errato", percorso, atteso="oggetto")
    for k in attese:
        if k not in d:
            raise EsperimentoNonValido("campo_mancante", f"{percorso}.{k}")
    ammesse = set(attese) | set(facoltative)
    for k in d:
        if k not in ammesse:
            raise EsperimentoNonValido("campo_sconosciuto", f"{percorso}.{k}")


def _int(v, percorso, lo=None, hi=None, nullo=False):
    if v is None and nullo:
        return
    if not isinstance(v, int) or isinstance(v, bool):
        raise EsperimentoNonValido("tipo_errato", percorso, atteso="intero")
    if (lo is not None and v < lo) or (hi is not None and v > hi):
        raise EsperimentoNonValido("valore_non_valido", percorso, valore=v)


def _str(v, percorso, massimo, nullo=False, codice_lungo="valore_non_valido"):
    if v is None and nullo:
        return
    if not isinstance(v, str):
        raise EsperimentoNonValido("tipo_errato", percorso, atteso="stringa")
    if len(v) > massimo:
        raise EsperimentoNonValido(codice_lungo, percorso, lunghezza=len(v), massimo=massimo)


def _bool(v, percorso):
    if not isinstance(v, bool):
        raise EsperimentoNonValido("tipo_errato", percorso, atteso="booleano")


def _hex(v, percorso, nullo=False):
    if v is None and nullo:
        return
    if not (isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdef" for c in v)):
        raise EsperimentoNonValido("valore_non_valido", percorso, atteso="sha256")


def _perm(v, percorso, nullo=False):
    if v is None and nullo:
        return
    if not isinstance(v, list) or len(v) != 27:
        raise EsperimentoNonValido("tipo_errato", percorso, atteso="lista di 27 interi")
    for i, x in enumerate(v):
        _int(x, f"{percorso}[{i}]", 0, 26)
    if len(set(v)) != 27:
        raise EsperimentoNonValido("valore_non_valido", percorso, atteso="permutazione")


def _valida_input(tipo, inp, p, seed):
    if tipo == "procedura":
        procedura_da_dati(inp, p)
    elif tipo == "espressione":
        _chiavi(inp, {"testo"}, p)
        _str(inp["testo"], f"{p}.testo", LIMITI["espressione"])
    elif tipo == "trucco":
        _chiavi(inp, {"carta", "bersaglio", "disposizione_fissata", "modalita_pratica"}, p)
        _int(inp["carta"], f"{p}.carta", 0, 26)
        _int(inp["bersaglio"], f"{p}.bersaglio", 0, 26)
        _int(inp["disposizione_fissata"], f"{p}.disposizione_fissata", 0, 215, nullo=True)
        if inp["modalita_pratica"] not in ("valutazione", "conseguenze"):
            raise EsperimentoNonValido("valore_non_valido", f"{p}.modalita_pratica")
    elif tipo == "riconoscimento":
        _chiavi(inp, {"T"}, p)
        _perm(inp["T"], f"{p}.T")
    elif tipo == "proprieta":
        _chiavi(inp, {"proprieta", "dominio"}, p)
        _str(inp["proprieta"], f"{p}.proprieta", 64)
        _str(inp["dominio"], f"{p}.dominio", 32)
    elif tipo == "successione":
        _chiavi(inp, {"procedure", "mazzo_iniziale", "generatore"}, p)
        if not isinstance(inp["procedure"], list):
            raise EsperimentoNonValido("tipo_errato", f"{p}.procedure", atteso="lista")
        if len(inp["procedure"]) > LIMITI["procedure"]:
            raise EsperimentoNonValido("sequenza_troppo_lunga", f"{p}.procedure",
                                       lunghezza=len(inp["procedure"]))
        for i, d in enumerate(inp["procedure"]):
            procedura_da_dati(d, f"{p}.procedure[{i}]")
        _perm(inp["mazzo_iniziale"], f"{p}.mazzo_iniziale", nullo=True)
        gen = inp["generatore"]
        if gen is not None:
            _chiavi(gen, {"n"}, f"{p}.generatore")
            _int(gen["n"], f"{p}.generatore.n", 0, LIMITI["procedure"])
            if seed is None:
                raise EsperimentoNonValido("seed_mancante", "seed")


def _valida_evento(e, p):
    _chiavi(e, {"id", "tipo", "origine", "revisione", "reversibile", "prima", "dopo", "dati"}, p)
    _int(e["id"], f"{p}.id", 1)
    _str(e["tipo"], f"{p}.tipo", 64)
    _str(e["origine"], f"{p}.origine", 64)
    _int(e["revisione"], f"{p}.revisione", 0)
    _bool(e["reversibile"], f"{p}.reversibile")
    for k in ("prima", "dopo", "dati"):
        if e[k] is not None and not isinstance(e[k], dict):
            raise EsperimentoNonValido("tipo_errato", f"{p}.{k}", atteso="oggetto")


def valida_documento(doc) -> dict:
    """Validazione completa di un documento gia' alla versione corrente."""
    _chiavi(doc, {"schema", "schema_version", "convenzioni", "programma", "algoritmi", "id",
                  "creato", "modificato", "annotazioni", "seed", "voci", "presentazione",
                  "cronologia", "fonti", "digest"}, "$")
    _chiavi(doc["convenzioni"], {"versione", "regole"}, "$.convenzioni")
    if not isinstance(doc["convenzioni"]["regole"], dict):
        raise EsperimentoNonValido("tipo_errato", "$.convenzioni.regole")
    _chiavi(doc["programma"], {"nome", "versione"}, "$.programma")
    _str(doc["programma"]["nome"], "$.programma.nome", 64)
    _str(doc["programma"]["versione"], "$.programma.versione", 64)
    if not isinstance(doc["algoritmi"], dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in doc["algoritmi"].items()):
        raise EsperimentoNonValido("tipo_errato", "$.algoritmi")
    _str(doc["id"], "$.id", 64)
    _str(doc["creato"], "$.creato", 64)
    _str(doc["modificato"], "$.modificato", 64)
    _chiavi(doc["annotazioni"], {"titolo", "nota"}, "$.annotazioni")
    _str(doc["annotazioni"]["titolo"], "$.annotazioni.titolo", LIMITI["titolo"],
         codice_lungo="annotazione_troppo_grande")
    _str(doc["annotazioni"]["nota"], "$.annotazioni.nota", LIMITI["nota"],
         codice_lungo="annotazione_troppo_grande")
    _int(doc["seed"], "$.seed", 0, 2 ** 63 - 1, nullo=True)
    voci = doc["voci"]
    if not isinstance(voci, list) or len(voci) > LIMITI["voci"]:
        raise EsperimentoNonValido("tipo_errato", "$.voci", atteso="lista (<= 6)")
    visti = set()
    for i, v in enumerate(voci):
        p = f"$.voci[{i}]"
        _chiavi(v, {"id", "strumento", "tipo", "revisione", "algoritmo", "input",
                    "risultato", "digest"}, p)
        if v["strumento"] not in STRUMENTI:
            raise EsperimentoNonValido("valore_non_valido", f"{p}.strumento")
        if v["strumento"] in visti:
            raise EsperimentoNonValido("valore_non_valido", f"{p}.strumento", doppio=True)
        visti.add(v["strumento"])
        if v["tipo"] != STRUMENTI[v["strumento"]]:
            raise EsperimentoNonValido("valore_non_valido", f"{p}.tipo")
        _str(v["id"], f"{p}.id", 16)
        _int(v["revisione"], f"{p}.revisione", 0)
        _str(v["algoritmo"], f"{p}.algoritmo", 64)
        _hex(v["digest"], f"{p}.digest")
        if not isinstance(v["risultato"], dict):
            raise EsperimentoNonValido("tipo_errato", f"{p}.risultato", atteso="oggetto")
        _valida_input(v["tipo"], v["input"], f"{p}.input", doc["seed"])
    pres = doc["presentazione"]
    if pres is not None:
        _chiavi(pres, {"livello", "scheda", "sottoscheda"}, "$.presentazione")
        if pres["livello"] not in LIVELLI_DIDATTICI:
            raise EsperimentoNonValido("valore_non_valido", "$.presentazione.livello",
                                       valore=pres["livello"])
        if pres["scheda"] is not None and pres["scheda"] not in _SCHEDE:
            raise EsperimentoNonValido("valore_non_valido", "$.presentazione.scheda")
        _str(pres["sottoscheda"], "$.presentazione.sottoscheda", 32, nullo=True)
    cr = doc["cronologia"]
    if cr is not None:
        _chiavi(cr, {"eventi", "annullati", "esterni", "revisione"}, "$.cronologia")
        _int(cr["revisione"], "$.cronologia.revisione", 0)
        totale = 0
        for nome in ("eventi", "annullati", "esterni"):
            if not isinstance(cr[nome], list):
                raise EsperimentoNonValido("tipo_errato", f"$.cronologia.{nome}")
            totale += len(cr[nome])
            for i, e in enumerate(cr[nome]):
                _valida_evento(e, f"$.cronologia.{nome}[{i}]")
        if totale > LIMITI["eventi"]:
            raise EsperimentoNonValido("cronologia_troppo_lunga", "$.cronologia", eventi=totale)
    if not isinstance(doc["fonti"], list) or len(doc["fonti"]) > LIMITI["fonti"]:
        raise EsperimentoNonValido("tipo_errato", "$.fonti")
    for i, f in enumerate(doc["fonti"]):
        p = f"$.fonti[{i}]"
        _chiavi(f, {"nome", "ruolo", "sha256", "disponibile"}, p)
        _str(f["nome"], f"{p}.nome", 256)
        if f["ruolo"] not in ("libro", "articolo", "altro"):
            raise EsperimentoNonValido("valore_non_valido", f"{p}.ruolo")
        _hex(f["sha256"], f"{p}.sha256", nullo=True)
        _bool(f["disponibile"], f"{p}.disponibile")
        if f["disponibile"] != (f["sha256"] is not None):
            raise EsperimentoNonValido("valore_non_valido", f"{p}.disponibile")
    _chiavi(doc["digest"], {"scientifico", "documento"}, "$.digest")
    _hex(doc["digest"]["scientifico"], "$.digest.scientifico")
    _hex(doc["digest"]["documento"], "$.digest.documento")
    return doc


# ═════════════════════════════════ migrazioni ══════════════════════════════

def migra(doc: dict) -> dict:
    """Porta il documento alla versione corrente, o solleva UNSUPPORTED."""
    if not isinstance(doc, dict):
        raise EsperimentoNonValido("tipo_errato", "$", atteso="oggetto")
    if doc.get("schema") != SCHEMA_ID:
        raise EsperimentoNonValido("schema_sconosciuto", "$.schema", valore=doc.get("schema"))
    if "schema_version" not in doc:
        raise EsperimentoNonValido("versione_mancante", "$.schema_version")
    v = doc["schema_version"]
    if not isinstance(v, int) or isinstance(v, bool) or v < 1:
        raise EsperimentoNonValido("versione_mancante", "$.schema_version", valore=v)
    if v > SCHEMA_VERSION:
        raise EsperimentoNonValido("schema_futuro", "$.schema_version", valore=v)
    while v < SCHEMA_VERSION:
        passo = MIGRAZIONI.get(v)
        if passo is None:
            raise EsperimentoNonValido("migrazione_assente", "$.schema_version", valore=v)
        doc = passo(dict(doc))
        v = doc["schema_version"]
    return doc


# ═══════════════════════════════ verifica al load ══════════════════════════

def _rifiuta_costante(nome):
    raise ValueError(f"costante JSON non ammessa: {nome}")


def _senza_duplicati(coppie):
    d = {}
    for k, v in coppie:
        if k in d:
            raise ValueError(f"chiave duplicata: {k}")
        d[k] = v
    return d


def leggi_json(testo) -> Any:
    """JSON rigoroso: niente NaN/Infinity, niente chiavi duplicate."""
    if isinstance(testo, (bytes, bytearray)):
        if len(testo) > LIMITI["byte"]:
            raise EsperimentoNonValido("troppo_grande", "$", byte=len(testo))
        testo = testo.decode("utf-8")
    if len(testo.encode("utf-8")) > LIMITI["byte"]:
        raise EsperimentoNonValido("troppo_grande", "$")
    try:
        return json.loads(testo, parse_constant=_rifiuta_costante,
                          object_pairs_hook=_senza_duplicati)
    except (ValueError, RecursionError) as e:
        raise EsperimentoNonValido("json_invalido", "$", causa=str(e)[:200]) from None


def verifica_testo(testo) -> RapportoVerifica:
    try:
        obj = leggi_json(testo)
    except UnicodeDecodeError:
        return RapportoVerifica(Stato.CORRUPT, "json_invalido")
    except EsperimentoNonValido as e:
        return RapportoVerifica(Stato.CORRUPT, e.codice,
                                (Discrepanza("documento", e.percorso, None, None),))
    return verifica_documento(obj)


def _confronta_voce(v, seed):
    try:
        atteso = calcola_risultato(v["tipo"], v["input"], seed)
    except _Discorde as d:
        return [Discrepanza(v["id"], d.campo, d.registrato, d.ricalcolato)]
    diffs = []
    reg = v["risultato"]
    for campo in sorted(set(reg) | set(atteso)):
        if reg.get(campo, "∅") != atteso.get(campo, "∅"):
            diffs.append(Discrepanza(v["id"], f"risultato.{campo}", reg.get(campo),
                                     atteso.get(campo)))
    return diffs


def verifica_documento(obj) -> RapportoVerifica:
    """Schema → convenzioni → struttura → digest → ricalcolo indipendente."""
    try:
        doc = migra(obj)
    except EsperimentoNonValido as e:
        stato = Stato.CORRUPT if e.codice == "tipo_errato" else Stato.UNSUPPORTED_SCHEMA
        return RapportoVerifica(stato, e.codice, (Discrepanza("documento", e.percorso, None, None),))
    conv = doc.get("convenzioni")
    if not isinstance(conv, dict) or not isinstance(conv.get("regole"), dict):
        return RapportoVerifica(Stato.CORRUPT, "campo_mancante",
                                (Discrepanza("documento", "$.convenzioni", None, None),))
    diverse = [Discrepanza("documento", f"convenzioni.regole.{k}",
                           conv["regole"].get(k), CONVENZIONI.get(k))
               for k in sorted(set(conv["regole"]) | set(CONVENZIONI))
               if conv["regole"].get(k) != CONVENZIONI.get(k)]
    if conv.get("versione") != CONVENTION_VERSION or diverse:
        if conv.get("versione") != CONVENTION_VERSION:
            diverse.insert(0, Discrepanza("documento", "convenzioni.versione",
                                          conv.get("versione"), CONVENTION_VERSION))
        return RapportoVerifica(Stato.INCOMPATIBLE_CONVENTION, "convenzione_diversa",
                                tuple(diverse))
    try:
        valida_documento(doc)
    except EsperimentoNonValido as e:
        return RapportoVerifica(Stato.CORRUPT, e.codice,
                                (Discrepanza("documento", e.percorso, None, None),))
    diagnosi = []
    for v in doc["voci"]:
        try:
            diagnosi += _confronta_voce(v, doc["seed"])
        except EsperimentoNonValido as e:
            return RapportoVerifica(Stato.CORRUPT, e.codice,
                                    (Discrepanza(v["id"], e.percorso, None, None),))
        dv = _digest_voce(v)
        if dv != v["digest"]:
            diagnosi.append(Discrepanza(v["id"], "digest", v["digest"], dv))
    ds = digest_scientifico(doc)
    if ds != doc["digest"]["scientifico"]:
        diagnosi.append(Discrepanza("documento", "digest.scientifico",
                                    doc["digest"]["scientifico"], ds))
    dd = digest_documento(doc)
    if dd != doc["digest"]["documento"]:
        diagnosi.append(Discrepanza("documento", "digest.documento",
                                    doc["digest"]["documento"], dd))
    if diagnosi:
        return RapportoVerifica(Stato.MISMATCH, "risultato_diverso", tuple(diagnosi), doc)
    return RapportoVerifica(Stato.VERIFIED, "verificato", (), doc)


# ═══════════════════════════════ confronto ═════════════════════════════════

@dataclass(frozen=True)
class Confronto:
    codici: Tuple[str, ...]                 # classificazione stabile
    dettagli: Tuple[Tuple[str, Any, Any], ...] = ()   # (campo, a, b)

    def __contains__(self, codice):
        return codice in self.codici


def confronta(a: dict, b: dict) -> Confronto:
    """Confronto strutturato di due documenti gia' validati (non un diff testuale)."""
    codici, dettagli = [], []

    def diff(campo, x, y):
        if x != y:
            dettagli.append((campo, x, y))
            return True
        return False

    if diff("schema_version", a["schema_version"], b["schema_version"]):
        codici.append("DIFFERENT_SCHEMA")
    if diff("convenzioni", a["convenzioni"], b["convenzioni"]):
        codici.append("DIFFERENT_CONVENTION")
    if diff("algoritmi", a["algoritmi"], b["algoritmi"]):
        codici.append("DIFFERENT_ALGORITHM_METADATA")
    if diff("programma", a["programma"], b["programma"]):
        codici.append("DIFFERENT_PROGRAM_VERSION")       # informativo, non incompatibile
    fa = sorted((f["ruolo"], f["nome"], f["sha256"]) for f in a["fonti"])
    fb = sorted((f["ruolo"], f["nome"], f["sha256"]) for f in b["fonti"])
    if diff("fonti", fa, fb):
        codici.append("DIFFERENT_SOURCE_HASHES")
    if diff("seed", a["seed"], b["seed"]):
        codici.append("DIFFERENT_SEED")
    va = {v["strumento"]: v for v in a["voci"]}
    vb = {v["strumento"]: v for v in b["voci"]}
    for s in sorted(set(va) | set(vb)):
        x, y = va.get(s), vb.get(s)
        if x is None or y is None:
            dettagli.append((f"voci.{s}", x is not None, y is not None))
            codici.append("DIFFERENT_INPUT")
            continue
        stesso_input = x["input"] == y["input"]
        stesso_risultato = x["risultato"] == y["risultato"]
        if not stesso_input:
            dettagli.append((f"voci.{s}.input", x["input"], y["input"]))
        if not stesso_risultato:
            dettagli.append((f"voci.{s}.risultato", x["risultato"], y["risultato"]))
        if stesso_input and not stesso_risultato:
            codici.append("RESULT_MISMATCH")
        elif not stesso_input and _stesso_esito(x, y):
            codici.append("SAME_RESULT_DIFFERENT_HISTORY")
        elif not stesso_input:
            codici.append("DIFFERENT_INPUT")
    if a["digest"]["scientifico"] == b["digest"]["scientifico"]:
        codici.append("SAME_SCIENTIFIC_CONTENT")
        if a["annotazioni"] != b["annotazioni"]:
            codici.append("ANNOTATIONS_ONLY")
    return Confronto(tuple(dict.fromkeys(codici)), tuple(dettagli))


def _stesso_esito(x, y):
    """Stessa T (o stesso cumulativo) raggiunta con input diversi."""
    for campo in ("T", "cumulativo"):
        if campo in x["risultato"] and x["risultato"].get(campo) == y["risultato"].get(campo):
            return True
    return False

