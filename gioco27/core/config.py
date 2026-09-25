"""
Configurazione persistente salvata in ~/.gioco27/config.json.
Usare get_config() per ottenere l'istanza singleton.
"""
import json
import pathlib
import re

from .log import get_logger
from .parallel import atomic_write

#: "LARGHEZZAxALTEZZA" con eventuale offset "+X+Y" (formato geometry di Tk)
_GEOMETRY_RE = re.compile(r"^\d{3,5}x\d{3,5}([+-]\d+[+-]\d+)?$")

_log = get_logger(__name__)

_CONFIG_DIR  = pathlib.Path.home() / ".gioco27"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

_DEFAULTS: dict = {
    "n_workers":        None,   # None -> cpu_count()-1
    "use_parallel":     True,
    "last_expression":  "",
    "window_geometry":  "1280x800",
    "decomp_mode":      "T_inv", # "T_inv" | "T"
    "sim_show_errors":  True,
    "livello":          "base",           # uno di LIVELLI_DIDATTICI (DP7)
    "language":         "it",             # "it" | "en"
    "ui_intro_done":    False,             # migrazione una-tantum UI guidata
    "help_font_scale":  1.0,               # scala testo aiuti/note (1.0 = 100%)
}

#: DP7 (I7): i quattro livelli didattici, dal meno al piu' ampio. Il livello
#: decide solo quali strumenti sono VISIBILI (gui/livelli.py), non la
#: matematica.
LIVELLI_DIDATTICI = ("base", "intermedio", "avanzato", "laboratorio")

#: Migrazione esplicita dei valori salvati dalle versioni precedenti.
#: «principiante» mostrava le schede essenziali → Base; «esperto» mostrava
#: tutto → Laboratorio, cosi' chi aveva gia' tutto continua ad averlo.
MIGRAZIONI = {
    "livello": {"principiante": "base", "esperto": "laboratorio"},
}


def migra_valore(chiave, valore):
    """Il valore aggiornato al formato corrente (invariato se non va migrato)."""
    tabella = MIGRAZIONI.get(chiave, {})
    try:
        return tabella.get(valore, valore)
    except TypeError:                 # valore non hashable: lo giudica il validatore
        return valore


#: Validatori per le chiavi il cui valore guida il comportamento del programma.
#:
#: config.json e' un file di testo nella home dell'utente: puo' essere
#: modificato a mano, restare da una versione precedente, o essere copiato tra
#: macchine diverse. Prima un valore fuori range (per esempio
#: `"help_font_scale": 0` o `"livello": "esperto "` con uno spazio) veniva
#: accettato e propagato nella GUI, dove produceva font invisibili o schede
#: mancanti. Ogni valore non valido viene ora scartato in favore del default,
#: con una riga nel log.
def _is_finite_scale(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) \
        and 0.5 <= float(v) <= 3.0

_VALIDATORS = {
    "n_workers":       lambda v: v is None or (isinstance(v, int)
                                               and not isinstance(v, bool)
                                               and 0 < v <= 256),
    "use_parallel":    lambda v: isinstance(v, bool),
    "last_expression": lambda v: isinstance(v, str) and len(v) <= 4096,
    "window_geometry": lambda v: isinstance(v, str)
                                 and bool(_GEOMETRY_RE.match(v)),
    "decomp_mode":     lambda v: v in ("T_inv", "T"),
    "sim_show_errors": lambda v: isinstance(v, bool),
    "livello":         lambda v: v in LIVELLI_DIDATTICI,
    "language":        lambda v: v in ("it", "en"),
    "ui_intro_done":   lambda v: isinstance(v, bool),
    "help_font_scale": _is_finite_scale,
}


class ConfigNonSalvata(OSError):
    """Il salvataggio della configurazione non e' riuscito (R07).

    Prima di G2 `save()` registrava il traceback nel log e tornava come se
    avesse salvato: il dialogo delle impostazioni si chiudeva e la preferenza
    di lingua annunciava «riavvia», cioe' la GUI presentava un fallimento come
    un successo. Il contratto e' ora quello gia' usato nel resto del
    programma — un'eccezione applicativa esplicita, come `FiltroNonValido`,
    `SchemaNonRiconosciuto` o `ExportTooLarge` — e non un valore di ritorno
    che nessuno controllerebbe.

    Porta con se' le tre informazioni che servono a chi deve riferirlo
    all'utente (la formulazione localizzata resta un problema della
    presentation): quale operazione, quale destinazione, quale causa.
    E' un `OSError` perche' cio' che fallisce e' sempre un'operazione di I/O:
    chi oggi intercetta `OSError` attorno a un salvataggio continua a
    funzionare.
    """

    def __init__(self, percorso, causa,
                 operazione="salvataggio della configurazione"):
        self.percorso = percorso
        self.causa = causa
        self.operazione = operazione
        super().__init__(f"{operazione}: {percorso} — {causa}")


class Config:
    """Configurazione chiave-valore con persistenza JSON."""

    def __init__(self) -> None:
        self._data: dict = dict(_DEFAULTS)
        self._load()

    # ---------------------------------------------------------------- I/O ---

    def _load(self) -> None:
        try:
            if _CONFIG_FILE.exists():
                with open(_CONFIG_FILE, encoding="utf-8") as f:
                    loaded = json.load(f)
                if not isinstance(loaded, dict):
                    raise ValueError("config.json non contiene un oggetto JSON")
                # aggiorna solo le chiavi conosciute (ignora chiavi obsolete)
                # e solo se il valore supera la validazione
                for k in _DEFAULTS:
                    if k not in loaded:
                        continue
                    v = migra_valore(k, loaded[k])
                    check = _VALIDATORS.get(k)
                    if check is not None and not check(v):
                        _log.warning("config: valore non valido per %r (%r): "
                                     "uso il default %r", k, v, _DEFAULTS[k])
                        continue
                    self._data[k] = v
        except Exception:
            _log.exception("Errore in lettura config %s (uso i default)",
                           _CONFIG_FILE)

    def save(self) -> None:
        """Salva la configurazione, o solleva `ConfigNonSalvata`.

        La pubblicazione resta atomica — `parallel.atomic_write`, la stessa
        primitiva di tutti gli export: temporaneo accanto alla destinazione e
        `os.replace` a scrittura conclusa, quindi un guasto a meta' lascia
        intatto il config.json precedente invece di troncarlo.

        Cio' che cambia in G2 e' soltanto l'esito: l'errore viene ancora
        registrato nel log, ma non si ferma li'.
        """
        try:
            _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            # Scrittura atomica: file temporaneo + replace, così un crash a
            # metà scrittura non lascia mai un config.json troncato/corrotto.
            with atomic_write(_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as causa:
            _log.exception("Errore in salvataggio config %s", _CONFIG_FILE)
            raise ConfigNonSalvata(_CONFIG_FILE, causa) from causa

    # ----------------------------------------------------------- accessors ---

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value

    def __getitem__(self, key: str):
        return self._data[key]

    def __setitem__(self, key: str, value) -> None:
        self._data[key] = value

    # ------------------------------------------------- computed properties ---

    @property
    def effective_n_workers(self) -> int:
        """Numero reale di worker da usare.

        Default (n_workers non impostato): tutti i core logici meno uno
        (uno resta libero per la GUI).

        Il valore passa da `parallel.default_workers`, che applica il tetto
        della piattaforma: su Windows ProcessPoolExecutor non accetta piu' di
        61 worker, e chiederne di piu' faceva fallire l'intero pool con un
        ripiego silenzioso sul sequenziale.
        """
        from .parallel import default_workers
        n = self._data.get("n_workers")
        if n is None or n <= 0:
            return default_workers(None)
        return default_workers(int(n))


# Singleton -------------------------------------------------------------------

_instance: "Config | None" = None


def get_config() -> Config:
    global _instance
    if _instance is None:
        _instance = Config()
    return _instance
