"""Cronologia dell'applicazione e undo/redo (compartimento J).

Tre cronologie diverse, da non confondere:

A. cronologia **matematica** — la successione di Procedure del mazzo
   (`services.successione`, riga L90);
B. cronologia **dell'applicazione** — le modifiche dello stato di lavoro
   dell'utente, per undo/redo: questo modulo;
C. **lifecycle dei job** — revisioni e annullamento dei lavori asincroni
   (`services.lavoro`, `core.parallel`): nessun legame con questo modulo.

Lo stato di lavoro e' un dizionario JSON immutabile per convenzione
``{"scientifico": {strumento: input}, "annotazioni": {"titolo", "nota"}}``.
La presentazione (livello, scheda, focus, ridimensionamenti) non ci entra:
per costruzione non genera eventi.

Contratti:

* ``registra`` con uno stato uguale al corrente non crea eventi;
* dopo ``annulla`` una nuova modifica tronca il ramo di redo;
* ``annulla``/``ripristina`` sono deterministici e restituiscono lo stato
  da applicare;
* gli eventi **esterni** (export, caricamenti) si registrano ma non sono
  reversibili: undo non tocca mai file, email o lavori;
* «modificata» confronta il digest dello stato con quello dell'ultimo
  salvataggio, non un booleano: tornare con undo allo stato salvato torna
  «pulito».
"""

from __future__ import annotations

import copy
from typing import List, Optional

from .esperimento import LIMITI, json_canonico, sha256

__all__ = ["Cronologia", "stato_vuoto", "CronologiaNonValida"]


class CronologiaNonValida(ValueError):
    def __init__(self, codice, **dati):
        super().__init__(codice)
        self.codice = codice
        self.dati = dati


def stato_vuoto() -> dict:
    return {"scientifico": {}, "annotazioni": {"titolo": "", "nota": ""}}


def _digest(stato) -> str:
    return sha256(json_canonico(stato))


class Cronologia:
    def __init__(self, stato_iniziale: Optional[dict] = None, *, revisione: int = 0):
        self._corrente = copy.deepcopy(stato_iniziale or stato_vuoto())
        self._eventi: List[dict] = []          # applicati (pila di undo)
        self._annullati: List[dict] = []       # ramo di redo
        self._esterni: List[dict] = []         # export, caricamenti: non reversibili
        self._revisione_base = revisione
        self._prossimo = 1
        self._salvato = _digest(self._corrente)

    # ── lettura ─────────────────────────────────────────────────────────────
    @property
    def stato(self) -> dict:
        return copy.deepcopy(self._corrente)

    @property
    def revisione(self) -> int:
        return self._eventi[-1]["revisione"] if self._eventi else self._revisione_base

    @property
    def numero_eventi(self) -> int:
        return len(self._eventi) + len(self._annullati) + len(self._esterni)

    @property
    def eventi(self):
        return tuple(copy.deepcopy(self._eventi))

    @property
    def esterni(self):
        return tuple(copy.deepcopy(self._esterni))

    def puo_annullare(self) -> bool:
        return bool(self._eventi)

    def puo_ripristinare(self) -> bool:
        return bool(self._annullati)

    @property
    def modificata(self) -> bool:
        return _digest(self._corrente) != self._salvato

    def segna_salvato(self):
        self._salvato = _digest(self._corrente)

    # ── modifiche ───────────────────────────────────────────────────────────
    def registra(self, tipo: str, origine: str, nuovo_stato: dict) -> Optional[dict]:
        nuovo = copy.deepcopy(nuovo_stato)
        if _digest(nuovo) == _digest(self._corrente):
            return None
        cambia_scienza = nuovo["scientifico"] != self._corrente["scientifico"]
        evento = {"id": self._prossimo, "tipo": str(tipo), "origine": str(origine),
                  "revisione": self.revisione + (1 if cambia_scienza else 0),
                  "reversibile": True, "prima": self._corrente, "dopo": nuovo,
                  "dati": None}
        self._prossimo += 1
        self._eventi.append(evento)
        self._annullati.clear()
        self._corrente = copy.deepcopy(nuovo)
        self._limita()
        return copy.deepcopy(evento)

    def registra_esterno(self, tipo: str, origine: str, dati: dict) -> dict:
        evento = {"id": self._prossimo, "tipo": str(tipo), "origine": str(origine),
                  "revisione": self.revisione, "reversibile": False,
                  "prima": None, "dopo": None, "dati": copy.deepcopy(dati)}
        self._prossimo += 1
        self._esterni.append(evento)
        self._limita()
        return copy.deepcopy(evento)

    def annulla(self) -> Optional[dict]:
        if not self._eventi:
            return None
        evento = self._eventi.pop()
        self._annullati.append(evento)
        self._corrente = copy.deepcopy(evento["prima"])
        return self.stato

    def ripristina(self) -> Optional[dict]:
        if not self._annullati:
            return None
        evento = self._annullati.pop()
        self._eventi.append(evento)
        self._corrente = copy.deepcopy(evento["dopo"])
        return self.stato

    def _limita(self):
        while self.numero_eventi > LIMITI["eventi"]:
            (self._esterni if len(self._esterni) > len(self._eventi) else self._eventi).pop(0)

    # ── persistenza ─────────────────────────────────────────────────────────
    def a_dati(self) -> dict:
        return {"eventi": copy.deepcopy(self._eventi),
                "annullati": copy.deepcopy(self._annullati),
                "esterni": copy.deepcopy(self._esterni),
                "revisione": self._revisione_base}

    @classmethod
    def da_dati(cls, dati: dict, stato_corrente: dict):
        """Ricostruisce la cronologia e controlla che sia coerente con lo stato."""
        c = cls(stato_corrente, revisione=dati["revisione"])
        eventi, annullati = dati["eventi"], dati["annullati"]
        tutti = eventi + annullati + dati["esterni"]
        ids = [e["id"] for e in tutti]
        if len(set(ids)) != len(ids):
            raise CronologiaNonValida("id_duplicati")
        for e in eventi + annullati:
            if not e["reversibile"] or e["prima"] is None or e["dopo"] is None:
                raise CronologiaNonValida("evento_non_reversibile", id=e["id"])
        for e in dati["esterni"]:
            if e["reversibile"]:
                raise CronologiaNonValida("evento_esterno_reversibile", id=e["id"])
        if eventi and _digest(eventi[-1]["dopo"]) != _digest(stato_corrente):
            raise CronologiaNonValida("stato_incoerente")
        if not eventi and annullati and _digest(annullati[-1]["prima"]) != _digest(stato_corrente):
            raise CronologiaNonValida("stato_incoerente")
        c._eventi = copy.deepcopy(eventi)
        c._annullati = copy.deepcopy(annullati)
        c._esterni = copy.deepcopy(dati["esterni"])
        c._prossimo = max(ids, default=0) + 1
        c._salvato = _digest(stato_corrente)
        return c
