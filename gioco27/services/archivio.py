"""Persistenza degli esperimenti e export interoperabili (compartimento J).

Salvataggio: serializza → file temporaneo accanto alla destinazione → replace
atomico, con la primitiva gia' usata da tutti gli export
(`core.parallel.atomic_write`). Un errore prima del replace lascia intatta la
destinazione precedente e cancella il temporaneo.

Caricamento: dimensione controllata prima di leggere, JSON rigoroso, poi
`esperimento.verifica_documento` (ricalcolo). Restituisce sempre un rapporto:
chi chiama decide se adottare il documento, e lo fa solo se VERIFIED.

CSV: solo dati tabellari (successione, replay, cronologia, verifiche I6,
mapping di T), separatore «;» come il resto del programma, sempre con un
manifesto accanto (``<file>.manifest.json``) che dichiara schema, convenzioni,
provenienza e digest del CSV. Un CSV non finge di essere una sessione.
"""

from __future__ import annotations

import csv
import io
import os
from pathlib import Path

from ..core.parallel import atomic_write
from . import esperimento as E

__all__ = [
    "salva_documento", "carica_documento", "scrivi_csv", "EXPORT_SCHEMA",
    "righe_successione", "righe_replay", "righe_cronologia", "righe_proprieta",
    "righe_mapping", "manifesto_export",
]

EXPORT_SCHEMA = "gioco27.export"


def salva_documento(doc: dict, percorso) -> str:
    """Scrive il documento (valido) in modo atomico; restituisce il digest del file."""
    E.valida_documento(doc)
    dati = E.json_canonico(doc)                  # serializza PRIMA di toccare il disco
    with atomic_write(percorso, "wb") as f:
        f.write(dati)
    return E.sha256(dati)


def carica_documento(percorso) -> E.RapportoVerifica:
    p = Path(percorso)
    try:
        dimensione = p.stat().st_size
    except OSError:
        return E.RapportoVerifica(E.Stato.CORRUPT, "file_non_leggibile")
    if dimensione > E.LIMITI["byte"]:
        return E.RapportoVerifica(E.Stato.CORRUPT, "troppo_grande")
    try:
        with open(p, "rb") as f:
            dati = f.read(E.LIMITI["byte"] + 1)
    except OSError:
        return E.RapportoVerifica(E.Stato.CORRUPT, "file_non_leggibile")
    return E.verifica_testo(dati)


# ═══════════════════════════════ CSV ═══════════════════════════════════════

def _lista(v):
    return " ".join(str(x) for x in v)


def righe_successione(s):
    intest = ("passo", "mescolamenti", "rovesciamenti", "numero_tavola", "identificatore",
              "T", "numero_cumulativo", "cumulativo", "disposizione")
    righe = [(p.indice, _lista(p.procedura.mescolamenti), _lista(p.procedura.rovesciamenti),
              p.numero_tavola, _lista(p.procedura.identificatore), _lista(p.T),
              p.numero_cumulativo, _lista(p.cumulativo), _lista(p.disposizione))
             for p in s.passi()]
    return intest, righe


def righe_replay(s):
    intest = ("tappa", "direzione", "disposizione")
    avanti = [(j, "avanti", _lista(v)) for j, v in enumerate(s.disposizioni())]
    n = s.lunghezza
    indietro = [(n - j, "indietro", _lista(v)) for j, v in enumerate(s.replay_inverso())]
    return intest, avanti + indietro


def righe_cronologia(eventi):
    intest = ("id", "tipo", "origine", "revisione", "reversibile")
    return intest, [(e["id"], e["tipo"], e["origine"], e["revisione"], e["reversibile"])
                    for e in eventi]


def righe_proprieta(voci):
    """Record I6 da voci di tipo 'proprieta' (gia' ricalcolate)."""
    intest = ("proprieta", "dominio", "metodo", "controllati", "totale", "esito",
              "controesempio", "seed", "convenzioni", "algoritmo", "digest")
    righe = []
    for v in voci:
        r = v["risultato"]
        righe.append((v["input"]["proprieta"], v["input"]["dominio"], r["metodo"],
                      r["controllati"], "" if r["totale"] is None else r["totale"],
                      r["esito"], "" if r["controesempio"] is None else
                      E.json_canonico(r["controesempio"]).decode("utf-8"),
                      "", E.CONVENTION_VERSION, v["algoritmo"], v["digest"]))
    return intest, righe


def righe_mapping(T):
    return ("origine", "destinazione"), [(i, t) for i, t in enumerate(T)]


def manifesto_export(contenuto: str, dati_csv: bytes, righe: int, fonti=()) -> dict:
    return {
        "schema": EXPORT_SCHEMA, "schema_version": 1, "formato": "csv",
        "separatore": ";", "contenuto": contenuto, "righe": righe,
        "sha256": E.sha256(dati_csv),
        "convenzioni": {"versione": E.CONVENTION_VERSION, "regole": dict(E.CONVENZIONI)},
        "programma": {"nome": "gioco27", "versione": E._VERSIONE_PROGRAMMA},
        "fonti": [dict(f) for f in fonti],
    }


def scrivi_csv(percorso, contenuto: str, intestazione, righe, fonti=()) -> dict:
    """Scrive CSV e manifesto (entrambi atomici); restituisce il manifesto."""
    buf = io.StringIO(newline="")
    w = csv.writer(buf, delimiter=";", lineterminator="\n")
    w.writerow(intestazione)
    w.writerows(righe)
    dati = buf.getvalue().encode("utf-8")
    manifesto = manifesto_export(contenuto, dati, len(righe), fonti)
    with atomic_write(percorso, "wb") as f:
        f.write(dati)
    with atomic_write(os.fspath(percorso) + ".manifest.json", "wb") as f:
        f.write(E.json_canonico(manifesto))
    return manifesto
