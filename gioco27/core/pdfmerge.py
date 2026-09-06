"""
Fusione dei PDF parziali prodotti dai processi figli.

Il problema delle risorse duplicate
-----------------------------------
Ogni processo figlio genera un PDF completo e autonomo, quindi vi incorpora la
propria copia dei font. Unendo N blocchi si ottengono N copie identiche dello
stesso programma font, tutte con lo stesso nome (`/AAAAAA+DejaVuSans`).

Misurato sull'export dettagliato del Gioco Reale (864 pagine, 87 blocchi):

    senza deduplicazione   11,1 MB   87 copie di ciascun font
    con deduplicazione      6,0 MB    1 copia               (sequenziale: 7,4 MB)

Oltre al peso, decine di risorse font che condividono lo stesso nome sono una
situazione che alcuni lettori PDF gestiscono male. La deduplicazione elimina
il problema alla radice.

Strategia, in ordine di preferenza:
  1. pikepdf (libqpdf): deduplica gli stream identici per hash del contenuto e
     ricollega i riferimenti dei FontDescriptor; riscrive con object stream.
  2. pypdf.compress_identical_objects(): meno efficace (non tocca i font
     incorporati) e lento — 26 s su un export da 13 824 pagine — quindi viene
     tentato solo sotto MAX_MB_RIPIEGO_PYPDF.
  3. nessuna deduplicazione: il file resta valido, solo piu' grande.

Attenzione su Windows: chi deduplica deve CHIUDERE il file di origine prima di
sostituirlo. `PdfReader(path)` e `pikepdf.open(path)` lo tengono aperto per la
lettura pigra, e `os.replace` fallisce con «PermissionError: [WinError 5]
Accesso negato». Su Linux la stessa sequenza funziona, quindi il difetto e'
invisibile fuori da Windows: vedi `_sostituisci`.

Nessuno dei tre e' obbligatorio: la fusione funziona comunque.
"""
import hashlib
import io
import os

from .log import get_logger
from .parallel import atomic_write  # noqa: F401 — usato da unisci()

_log = get_logger(__name__)


def _sostituisci(tmp, path):
    """
    Sostituisce `path` con `tmp`, dopo che ogni handle su `path` e' stato
    chiuso.

    Su Windows `os.replace` fallisce con PermissionError se la destinazione e'
    ancora aperta da qualcuno — ed e' esattamente quello che succedeva:
    `PdfReader(path)` e `pikepdf.open(path)` tengono il file aperto per la
    lettura pigra, quindi la deduplicazione moriva con

        PermissionError: [WinError 5] Accesso negato

    Su Linux la stessa sequenza funziona (POSIX consente di rinominare sopra un
    file aperto), quindi il difetto non poteva emergere fuori da Windows.
    """
    os.replace(tmp, path)


def _dedup_pikepdf(path):
    """
    Deduplica gli stream identici e ricollega i font. Restituisce True se ha
    lavorato, False se pikepdf non e' disponibile o qualcosa e' andato storto.
    """
    try:
        import pikepdf
    except ImportError:
        return False

    tmp = f"{path}.dedup"
    try:
        prima = os.path.getsize(path)
        # `allow_overwriting_input` fa leggere pikepdf in memoria invece di
        # tenere il file aperto: senza, il salvataggio successivo su Windows
        # troverebbe la destinazione bloccata.
        with pikepdf.open(path, allow_overwriting_input=True) as pdf:
            # hash del contenuto -> primo stream incontrato con quel contenuto
            canonico = {}
            for obj in pdf.objects:
                if not isinstance(obj, pikepdf.Stream):
                    continue
                try:
                    h = hashlib.sha256(bytes(obj.read_raw_bytes())).hexdigest()
                except Exception:
                    continue
                canonico.setdefault(h, obj)

            ricollegati = 0
            for obj in pdf.objects:
                if not isinstance(obj, pikepdf.Dictionary):
                    continue
                for chiave in ("/FontFile", "/FontFile2", "/FontFile3"):
                    if chiave not in obj:
                        continue
                    try:
                        h = hashlib.sha256(
                            bytes(obj[chiave].read_raw_bytes())).hexdigest()
                    except Exception:
                        continue
                    c = canonico.get(h)
                    if c is not None and c.objgen != obj[chiave].objgen:
                        obj[chiave] = c
                        ricollegati += 1

            pdf.save(tmp,
                     object_stream_mode=pikepdf.ObjectStreamMode.generate,
                     compress_streams=True)
        # il `with` ha chiuso il PDF: ora la sostituzione e' lecita anche su Windows
        _sostituisci(tmp, path)
        _log.info("PDF deduplicato con pikepdf: %d font ricollegati, "
                  "%.1f MB -> %.1f MB", ricollegati, prima / 1e6,
                  os.path.getsize(path) / 1e6)
        return True
    except Exception:
        _log.exception("Deduplicazione pikepdf fallita: il PDF resta valido")
        _pulisci(tmp)
        return False


#: Oltre questa dimensione la compattazione di ripiego con pypdf non viene
#: nemmeno tentata: costa decine di secondi e non deduplica i font incorporati
#: (misurato: 26 s su un export da 13 824 pagine, per un guadagno modesto).
#: Meglio suggerire pikepdf, che fa un lavoro migliore in meno tempo.
MAX_MB_RIPIEGO_PYPDF = 20


def _pulisci(tmp):
    try:
        os.unlink(tmp)
    except OSError:
        pass


def _dedup_pypdf(path):
    """Ripiego senza dipendenze aggiuntive: compress_identical_objects()."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return False

    prima = os.path.getsize(path)
    if prima > MAX_MB_RIPIEGO_PYPDF * 1e6:
        _log.info("Compattazione pypdf saltata: %.1f MB oltre il limite di "
                  "%d MB (installa pikepdf per deduplicare anche i file grandi)",
                  prima / 1e6, MAX_MB_RIPIEGO_PYPDF)
        return False

    tmp = f"{path}.dedup"
    try:
        # Il file viene letto INTERAMENTE in memoria e chiuso subito: tenere
        # aperto `path` impedirebbe di sostituirlo su Windows.
        with open(path, "rb") as fh:
            dati = fh.read()

        lettore = PdfReader(io.BytesIO(dati))
        scrittore = PdfWriter()
        for pagina in lettore.pages:
            scrittore.add_page(pagina)
        if not hasattr(scrittore, "compress_identical_objects"):
            return False
        scrittore.compress_identical_objects()

        with open(tmp, "wb") as f:
            scrittore.write(f)
        _sostituisci(tmp, path)
        _log.info("PDF compattato con pypdf: %.1f MB -> %.1f MB",
                  prima / 1e6, os.path.getsize(path) / 1e6)
        return True
    except Exception:
        _log.exception("Compattazione pypdf fallita: il PDF resta valido")
        _pulisci(tmp)
        return False


def deduplica(path):
    """
    Deduplica le risorse del PDF `path`, in-place e in modo sicuro.

    Non solleva mai: se nessuna strategia e' disponibile il file resta com'e',
    valido ma piu' grande. Restituisce il nome della strategia usata, o None.
    """
    if _dedup_pikepdf(path):
        return "pikepdf"
    if _dedup_pypdf(path):
        return "pypdf"
    _log.info("Nessuna deduplicazione disponibile (installa pikepdf per "
              "ridurre la dimensione dei PDF uniti)")
    return None


def unisci(blocchi_iter, path, progress_cb=None):
    """
    Unisce in ordine i PDF parziali (bytes) in `path`, poi deduplica.

    `blocchi_iter` produce coppie (bytes_del_pdf, n_elementi). La scrittura e'
    atomica: la destinazione o non esiste, o e' un PDF completo.

    Restituisce il numero di elementi totali.
    """
    from pypdf import PdfReader, PdfWriter

    scrittore = PdfWriter()
    fatti = 0
    for blob, n in blocchi_iter:
        for pagina in PdfReader(io.BytesIO(blob)).pages:
            scrittore.add_page(pagina)
        fatti += n
        if progress_cb:
            progress_cb(fatti)

    if not len(scrittore.pages):
        return fatti
    with atomic_write(path) as f:
        scrittore.write(f)
    deduplica(path)
    return fatti
