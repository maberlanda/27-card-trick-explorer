"""Sessione di lavoro J: stato scientifico, annotazioni, presentazione, cronologia.

Lo **stato scientifico** e' ``{strumento: input}`` per gli strumenti di
`esperimento.STRUMENTI` (Explorer, Simulatore/Pratica, Tavola,
Riconoscimento, Laboratorio, Successione L90). I risultati non stanno nella
sessione: li ricalcola `esperimento.crea_documento` quando si salva, e
`verifica_documento` quando si carica.

La **presentazione** (livello didattico, scheda, sotto-scheda) e' salvata ma
non entra ne' nel digest scientifico ne' nella cronologia.

Il caricamento e' transazionale: `carica` restituisce una NUOVA sessione
solo se il documento e' VERIFIED; altrimenti nessuna sessione e il rapporto.
Chi chiama sostituisce la sessione corrente in un solo passo.
"""

from __future__ import annotations

import copy
import uuid
from typing import Optional

from . import archivio, esperimento as E
from .cronologia import Cronologia, stato_vuoto

__all__ = ["SessioneLavoro"]


class SessioneLavoro:
    def __init__(self, *, seed=None):
        self.id = uuid.uuid4().hex
        self.creato = E.adesso()
        self.seed = seed
        self.presentazione = None
        self.percorso = None
        self.cronologia = Cronologia(stato_vuoto())
        self._bozza_annotazioni = None

    # ── lettura ─────────────────────────────────────────────────────────────
    @property
    def stato_scientifico(self) -> dict:
        return self.cronologia.stato["scientifico"]

    @property
    def annotazioni(self) -> dict:
        return self.cronologia.stato["annotazioni"]

    @property
    def modificata(self) -> bool:
        return self.cronologia.modificata or (
            self._bozza_annotazioni is not None
            and self._bozza_annotazioni != self.annotazioni)

    @property
    def annotazioni_visibili(self) -> dict:
        """Bozza dell'editor, conservata anche quando la finestra viene chiusa."""
        return copy.deepcopy(self._bozza_annotazioni or self.annotazioni)

    def imposta_bozza_annotazioni(self, titolo, nota):
        ann = {"titolo": str(titolo), "nota": str(nota)}
        self._bozza_annotazioni = None if ann == self.annotazioni else ann

    def sincronizza_annotazioni(self):
        ann = self.annotazioni_visibili
        return self.imposta_annotazioni(ann["titolo"], ann["nota"])

    def input_di(self, strumento) -> Optional[dict]:
        return copy.deepcopy(self.stato_scientifico.get(strumento))

    # ── modifiche ───────────────────────────────────────────────────────────
    def registra(self, strumento: str, inp: Optional[dict], tipo="modifica"):
        """Nuovo input di uno strumento (None = strumento azzerato)."""
        if strumento not in E.STRUMENTI:
            raise KeyError(strumento)
        stato = self.cronologia.stato
        if inp is None:
            stato["scientifico"].pop(strumento, None)
        else:
            stato["scientifico"][strumento] = E._jsonabile(inp)
        return self.cronologia.registra(tipo, strumento, stato)

    def imposta_annotazioni(self, titolo: str, nota: str):
        stato = self.cronologia.stato
        stato["annotazioni"] = {"titolo": str(titolo), "nota": str(nota)}
        evento = self.cronologia.registra("annotazione", "sessione", stato)
        self._bozza_annotazioni = None
        return evento

    def imposta_presentazione(self, livello, scheda=None, sottoscheda=None):
        self.presentazione = {"livello": livello, "scheda": scheda, "sottoscheda": sottoscheda}

    def registra_export(self, formato, nome, digest, successo=True):
        return self.cronologia.registra_esterno(
            "esportato", "export", {"formato": formato, "nome": str(nome),
                                    "digest": digest, "successo": bool(successo)})

    # ── documento e file ────────────────────────────────────────────────────
    def documento(self, fonti=()) -> dict:
        ann = self.annotazioni
        return E.crea_documento(
            self.stato_scientifico, seed=self.seed, titolo=ann["titolo"], nota=ann["nota"],
            presentazione=self.presentazione, cronologia=self.cronologia.a_dati(),
            fonti=fonti, esperimento_id=self.id, creato=self.creato)

    def salva(self, percorso, fonti=()) -> str:
        self.sincronizza_annotazioni()
        doc = self.documento(fonti)
        digest = archivio.salva_documento(doc, percorso)
        self.percorso = str(percorso)
        self.cronologia.segna_salvato()
        return digest

    @classmethod
    def da_documento(cls, doc: dict) -> "SessioneLavoro":
        """Sessione da un documento GIA' verificato (VERIFIED)."""
        s = cls(seed=doc["seed"])
        s.id, s.creato = doc["id"], doc["creato"]
        s.presentazione = copy.deepcopy(doc["presentazione"])
        stato = {"scientifico": {v["strumento"]: copy.deepcopy(v["input"]) for v in doc["voci"]},
                 "annotazioni": copy.deepcopy(doc["annotazioni"])}
        if doc["cronologia"] is not None:
            s.cronologia = Cronologia.da_dati(doc["cronologia"], stato)
        else:
            s.cronologia = Cronologia(stato)
        s.cronologia.registra_esterno("caricato", "sessione",
                                      {"id": doc["id"], "digest": doc["digest"]["scientifico"]})
        s.cronologia.segna_salvato()
        return s

    @classmethod
    def carica(cls, percorso):
        """(nuova sessione | None, rapporto). Nessun effetto se non VERIFIED."""
        rapporto = archivio.carica_documento(percorso)
        if not rapporto.verificato:
            return None, rapporto
        try:
            s = cls.da_documento(rapporto.documento)
        except (ValueError, KeyError) as e:
            codice = getattr(e, "codice", "cronologia_non_valida")
            return None, E.RapportoVerifica(E.Stato.CORRUPT, codice)
        s.percorso = str(percorso)
        return s, rapporto
