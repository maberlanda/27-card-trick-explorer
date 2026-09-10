"""
Cache su disco per le decomposizioni Kronecker.

Salva i risultati in ~/.gioco27/cache/dec_<hash>.json in modo che la stessa
T^-1 (o T) non venga ricalcolata due volte.

Formato
-------
Un oggetto JSON: {"version": N, "results": [[[f3,f2,f1], ...], ...]}
Le entry con `version` diversa da CACHE_FORMAT_VERSION vengono scartate e
rigenerate automaticamente.

Perche' JSON e non pickle
-------------------------
La versione precedente usava `pickle.load` su file presi dal disco.
`pickle` puo' eseguire codice arbitrario in fase di deserializzazione: un file
modificato in ~/.gioco27/cache/ diventava un vettore di esecuzione. I dati qui
sono solo liste di stringhe (nomi GEN3), quindi JSON e' sufficiente, sicuro e
in piu' rende i file leggibili a occhio per il debug.

Pulizia
-------
Le entry piu' vecchie di _MAX_AGE_DAYS vengono eliminate alla lettura. In piu'
`prune()` tiene la cache sotto _MAX_TOTAL_MB eliminando le entry meno recenti:
prima esisteva solo il limite d'eta', e una cache molto usata poteva crescere
senza tetto.
"""
import hashlib
import json
import pathlib
import time
from typing import Optional

from .log import get_logger
from .parallel import atomic_write
from .kronecker import validate_decompositions

_log = get_logger(__name__)

_CACHE_DIR = pathlib.Path.home() / ".gioco27" / "cache"
_MAX_AGE_DAYS = 30     # invalida cache piu' vecchia di N giorni
_MAX_TOTAL_MB = 200    # tetto complessivo della cartella cache

#: Versione del formato dei dati in cache. Incrementare quando cambia la
#: struttura dei risultati delle decomposizioni: le entry con versione diversa
#: vengono scartate al caricamento.
#: 2 = passaggio da pickle a JSON.
CACHE_FORMAT_VERSION = 2

_GLOB = "dec_*.json"


def _cache_key(perm) -> str:
    """Hash SHA-256 (16 hex chars) della permutazione."""
    # bytes(perm) funziona solo per valori 0..255 e per liste Python; passando
    # per la rappresentazione testuale la chiave e' definita anche per array
    # numpy e per permutazioni piu' grandi di 27.
    raw = ",".join(str(int(x)) for x in perm).encode("ascii")
    return hashlib.sha256(raw).hexdigest()[:16]


def _cache_path(perm) -> pathlib.Path:
    return _CACHE_DIR / f"dec_{_cache_key(perm)}.json"


def load_decompositions(perm) -> "Optional[list]":
    """
    Restituisce i risultati cached per `perm`, oppure None se non presenti,
    troppo vecchi, corrotti o con versione di formato diversa da quella corrente.
    """
    path = _cache_path(perm)
    try:
        if not path.exists():
            return None
        age_days = (time.time() - path.stat().st_mtime) / 86400
        if age_days > _MAX_AGE_DAYS:
            path.unlink(missing_ok=True)
            return None

        with open(path, encoding="utf-8") as f:
            payload = json.load(f)

        if not isinstance(payload, dict):
            # entry pre-versioning o file estraneo: scarta
            path.unlink(missing_ok=True)
            return None
        if payload.get("version") != CACHE_FORMAT_VERSION:
            _log.info("Cache %s scartata: versione %s != %s", path.name,
                      payload.get("version"), CACHE_FORMAT_VERSION)
            path.unlink(missing_ok=True)
            return None

        data = payload.get("results")
        if not isinstance(data, list):
            return None
        # JSON non ha tuple: ricostruiamo la struttura attesa dal chiamante
        # (lista di triple di triple di stringhe).
        return validate_decompositions(perm, data)
    except Exception:
        _log.exception("Errore in lettura cache %s", path)
        return None


def save_decompositions(perm, results: list) -> None:
    """Salva `results` su disco per la chiave `perm` (col formato corrente)."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _cache_path(perm)
        payload = {"version": CACHE_FORMAT_VERSION,
                   "results": [[list(factor) for factor in triple]
                               for triple in results]}
        # Scrittura atomica: un crash a metà non lascia un JSON troncato che
        # verrebbe poi letto come cache corrotta.
        for attempt in range(3):
            try:
                with atomic_write(path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, separators=(",", ":"))
                break
            except PermissionError:
                # Su Windows un'altra istanza può trattenere brevemente
                # il file durante la lettura o il controllo della cache.
                if attempt == 2:
                    raise
                time.sleep(0.01 * (attempt + 1))
        prune()
    except Exception:
        _log.exception("Errore in scrittura cache per perm %s",
                       list(perm)[:6])


def prune(max_total_mb: float = _MAX_TOTAL_MB) -> int:
    """
    Mantiene la cache sotto `max_total_mb` eliminando le entry meno recenti.
    Restituisce il numero di file eliminati.
    """
    removed = 0
    try:
        files = [(p.stat().st_mtime, p.stat().st_size, p)
                 for p in _CACHE_DIR.glob(_GLOB)]
        total = sum(sz for _, sz, _ in files)
        limit = max_total_mb * 1024 * 1024
        if total <= limit:
            return 0
        files.sort()                      # dal piu' vecchio
        for _mtime, size, p in files:
            if total <= limit:
                break
            p.unlink(missing_ok=True)
            total -= size
            removed += 1
        if removed:
            _log.info("Cache: eliminate %d entry per rientrare in %s MB",
                      removed, max_total_mb)
    except Exception:
        _log.exception("Errore durante il pruning della cache")
    return removed


def clear_cache() -> int:
    """Elimina tutti i file cache. Restituisce il numero di file eliminati."""
    count = 0
    try:
        # Include i vecchi .pkl: cosi' «svuota cache» pulisce davvero tutto
        # anche dopo l'aggiornamento del formato.
        for pattern in (_GLOB, "dec_*.pkl"):
            for p in _CACHE_DIR.glob(pattern):
                p.unlink(missing_ok=True)
                count += 1
    except Exception:
        _log.exception("Errore durante la pulizia della cache")
    return count


def cache_size_mb() -> float:
    """Dimensione totale della cache in MB."""
    try:
        total = sum(p.stat().st_size for p in _CACHE_DIR.glob(_GLOB))
        return total / (1024 * 1024)
    except Exception:
        return 0.0


def cache_entries() -> int:
    """Numero di entry nella cache."""
    try:
        return sum(1 for _ in _CACHE_DIR.glob(_GLOB))
    except Exception:
        return 0
