"""Come dire all'utente cio' che il core ha constatato.

Compartimento H1. D, E, F e G hanno lasciato di proposito messaggi **neutri**
nelle eccezioni del core: un'eccezione descrive che cosa e' successo, non come
raccontarlo, e il suo testo non deve cambiare con la lingua dell'interfaccia —
finisce nel log, nei test e nei rapporti, dove una frase tradotta sarebbe un
danno. Il prezzo era che la GUI li mostrasse con `str(exc)`: in modalita'
inglese l'utente leggeva testo tecnico italiano.

Questo modulo e' il confine dove quel testo diventa una frase. Riceve
l'eccezione (o una riga scartata) e restituisce titolo e messaggio nella
lingua attiva, componendoli dai **dati strutturati** che il core porta con
se' — codice stabile, campo, valore, intervallo, lunghezza — e non leggendo il
messaggio. Il messaggio neutro resta la rete di sicurezza: quando un codice
non e' previsto, e' cio' che viene mostrato, e il dettaglio tecnico finisce
comunque nel log.

Non e' un framework: due funzioni e tre tabelle. Non modifica le eccezioni,
non le rimpacchetta, non cambia il flusso; il core non lo importa e non sa che
esiste.
"""

from ..core.analisi import AnalisiTroppoGrande, SchemaNonRiconosciuto
from ..core.combinations import FiltroNonValido
from ..core.config import ConfigNonSalvata
from ..core.dominio import PermutazioneNonValida
from ..core.log import get_logger
from .i18n import tr

__all__ = ["per_utente", "per_file", "motivo_di", "diagnostica_import"]

_log = get_logger(__name__)

#: Quante righe scartate si elencano prima di dire «e altre N».
MASSIMO_SCARTI_MOSTRATI = 3


# ─────────────────────────── tabelle di traduzione ──────────────────────────
#
# Codice stabile del core → chiave del catalogo. Un codice che non compare qui
# non e' un errore di programmazione: e' un percorso che non e' stato ancora
# raccontato, e l'utente vedra' il messaggio neutro invece di niente.

_SCHEMA = {
    "senza_intestazione": "errore.schema.senza_intestazione",
    "file_vuoto":         "errore.schema.file_vuoto",
    "non_importabile":    "errore.schema.non_importabile",
    "sconosciuto":        "errore.schema.sconosciuto",
}

_PERMUTAZIONE = {
    "campo_vuoto":       "errore.permutazione.campo_vuoto",
    "lista_vuota":       "errore.permutazione.lista_vuota",
    "sequenza_vuota":    "errore.permutazione.lista_vuota",
    "non_intero_testo":  "errore.permutazione.non_intero",
    "non_intero":        "errore.permutazione.non_intero",
    "booleano":          "errore.permutazione.non_intero",
    "lunghezza":         "errore.permutazione.lunghezza",
    "fuori_intervallo":  "errore.permutazione.fuori_intervallo",
    "indice_fuori_intervallo": "errore.permutazione.fuori_intervallo",
    "valore_ripetuto":   "errore.permutazione.valore_ripetuto",
}

_FORMULA = {
    "formula_non_valida":      "errore.formula.non_valida",
    "formula_non_valutabile":  "errore.formula.non_valutabile",
    "formula_discorde":        "errore.formula.discorde",
}


def _testo(chiave, neutro, **dati):
    """Traduce, e se qualcosa non torna mostra il testo neutro del core.

    Un errore secondario — una chiave mancante, un segnaposto che non c'e' —
    non deve trasformarsi in un guasto mentre si sta gia' riferendo un guasto.
    """
    try:
        return tr(chiave, **dati)
    except (KeyError, IndexError, ValueError):
        _log.exception("i18n: non e' stato possibile comporre %r", chiave)
        return neutro


def _per_codice(tabella, codice, neutro, dati):
    chiave = tabella.get(codice or "")
    if chiave is None:
        return neutro
    return _testo(chiave, neutro, **dati)


# ───────────────────────────── eccezioni ────────────────────────────────────

def per_utente(exc):
    """`(titolo, messaggio)` localizzati per un'eccezione applicativa.

    Il dettaglio tecnico non sparisce: quando la frase mostrata non lo
    contiene, finisce nel log, che e' il posto giusto per leggerlo.
    """
    dati = dict(getattr(exc, "dati", {}) or {})
    codice = getattr(exc, "codice", "")
    neutro = str(exc)

    if isinstance(exc, SchemaNonRiconosciuto):
        return (tr("analysis.csv_read_error_title"),
                _per_codice(_SCHEMA, codice, neutro, dati))

    if isinstance(exc, AnalisiTroppoGrande):
        return (tr("analysis.too_large_title"),
                _testo("analysis.too_large", neutro,
                       count=f"{exc.richieste:,}", limit=f"{exc.limite:,}"))

    if isinstance(exc, ConfigNonSalvata):
        return (tr("config.save_failed.title"),
                _testo("config.save_failed", neutro,
                       path=exc.percorso, detail=exc.causa))

    if isinstance(exc, PermutazioneNonValida):
        nome = dati.get("nome", "")
        # Senza il nome dell'API la frase generica direbbe «: non e' una
        # permutazione valida», che e' peggio del testo neutro.
        ripiego = (_testo("errore.permutazione.generico", neutro, nome=nome)
                   if nome else neutro)
        return (tr("error.generic"),
                _per_codice(_PERMUTAZIONE, codice, ripiego, dati))

    if isinstance(exc, FiltroNonValido):
        # I filtri costruiti dal pannello non possono essere invalidi: dopo
        # M01 nemmeno un livello vuoto ci arriva. Quando questa eccezione
        # compare, viene da un filtro costruito a mano o da un'API, e il
        # dettaglio interessa a chi legge il log, non a chi guarda la finestra.
        _log.warning("filtro non valido mostrato all'utente: %s", neutro)
        return tr("analysis.error_title"), tr("errore.filtro.generico")

    return tr("error.generic"), neutro


def per_file(exc, percorso, titolo=None):
    """`(titolo, messaggio)` per un errore del sistema operativo su un file.

    Compartimento H2. Il messaggio del sistema operativo non si traduce — e'
    suo, ed e' l'unica cosa che dice davvero che cosa e' andato storto — ma da
    solo non dice a *quale* file si riferisce ne' che cosa si stava tentando.
    La cornice aggiunge quelle due cose nella lingua dell'utente e lascia il
    dettaglio cosi' com'e'.

    `percorso` vuoto: l'operazione riguardava una cartella o piu' file (un
    export multiplo, la pulizia della cache) e nominarne uno sarebbe falso;
    resta la cornice generica. `titolo` permette a una rotta che ha gia' il
    suo titolo localizzato — «Errore di esportazione» — di conservarlo.
    """
    import os

    dettaglio = str(exc)
    nome = os.path.basename(str(percorso)) if percorso else ""
    if nome:
        messaggio = _testo("errore.file.scrittura", dettaglio,
                           nome=nome, dettaglio=dettaglio)
    else:
        messaggio = _testo("errore.file.generico", dettaglio,
                           dettaglio=dettaglio)
    return (titolo or tr("errore.file.titolo")), messaggio


# ─────────────────────── righe scartate e diagnostica ───────────────────────

def motivo_di(scarto):
    """Il motivo di una `RigaScartata`, nella lingua attiva."""
    dati = dict(getattr(scarto, "dati", {}) or {})
    codice = getattr(scarto, "codice", "")
    neutro = getattr(scarto, "motivo", str(scarto))
    tabella = _FORMULA if codice in _FORMULA else _PERMUTAZIONE
    dati.setdefault("nome", getattr(scarto, "campo", ""))
    return _per_codice(tabella, codice, neutro, dati)


def diagnostica_import(esito, massimo=MASSIMO_SCARTI_MOSTRATI):
    """Che cosa e' stato letto, accettato e scartato — in una riga.

    Accetta sia il `RisultatoAnalisi` dei servizi sia il `RisultatiImport` del
    core: di entrambi servono soltanto `lette`, `scartate` e la nota neutra
    (il nome del file), che il core e i servizi lasciano cosi' com'e'.
    """
    parti = []
    nota = (getattr(esito, "nota", "") or "").strip()
    if nota:
        parti.append(nota)

    scartate = tuple(getattr(esito, "scartate", ()) or ())
    lette = int(getattr(esito, "lette", 0) or 0)
    if scartate:
        parti.append(tr("errore.import.riepilogo",
                        lette=f"{lette:,}",
                        accettate=f"{max(lette - len(scartate), 0):,}",
                        scartate=f"{len(scartate):,}"))
        dettagli = [tr("errore.import.riga", numero=s.numero, campo=s.campo,
                       motivo=motivo_di(s)) for s in scartate[:massimo]]
        resto = len(scartate) - massimo
        if resto == 1:
            dettagli.append(tr("errore.import.altre_una"))
        elif resto > 1:
            dettagli.append(tr("errore.import.altre", count=f"{resto:,}"))
        parti.append("; ".join(dettagli))

    return "   —   ".join(parti)
