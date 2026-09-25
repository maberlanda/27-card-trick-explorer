"""
Generazione e conteggio combinazioni filtrate; export PDF/CSV.
"""
from dataclasses import dataclass
from itertools import product as iproduct
from typing import Tuple

from .constants import P_OPTS, J_OPTS, ANY
from .log import get_logger
from .parallel import (COSTO_PAGINA_PDF, ExportAnnullato, check_export_size,
                       run_export, _check_cancelled)
from .permutations import (compute_stage, compute_R, kron_label, stage_label,
                            R_label, MAT3_P, MAT3_J)
from ..i18n import get_language, set_language, tr

_log = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────
# Chiavi dei dizionari-filtro.
#
# Sono a BASE 0, come le cifre ternarie su cui agiscono: p0 riordina le carte
# dentro la terzina (cifra i₀), p1 le terzine dentro il pacchetto (i₁), p2 i
# pacchetti (i₂). Fino alla 3.0.3 si chiamavano p1/p2/p3, sfasate di uno
# rispetto alla cifra: leggere «p3 agisce su i₂» richiedeva una conversione
# mentale a ogni riga.
#
# ATTENZIONE alla migrazione: la vecchia chiave `p2` (terzine) corrisponde
# alla nuova `p1`, quindi un filtro scritto con i nomi vecchi verrebbe
# interpretato in modo SILENZIOSAMENTE diverso. Per questo `valida_filtri`
# rifiuta esplicitamente le chiavi legacy invece di ignorarle.
CHIAVI_P = ('p0', 'p1', 'p2')
CHIAVI_J = ('j0', 'j1', 'j2')
CHIAVI_FILTRO = CHIAVI_P + CHIAVI_J

_CHIAVI_LEGACY = {'p3', 'j3'}

#: Numero di stadi del gioco. Non e' un parametro: la matematica del mazzo di
#: 27 carte e' definita su tre stadi (T = S2 o S1 o S0), tutti gli export hanno
#: tre colonne Stage e il dominio verificato in `tests/test_baseline_matematica`
#: conta 1.728 configurazioni **per stadio**. Generalizzare a N stadi sarebbe un
#: gioco diverso: qui il numero viene reso esplicito e imposto.
N_STADI = 3

#: Chiave booleana opzionale: vincola le triple J alla forma (v, v, v).
CHIAVE_UNIFORME = 'j_uniform'


class FiltroNonValido(ValueError):
    """Il filtro non rispetta il contratto: stadi, chiavi, valori o tipi.

    Sottoclasse di ValueError perche' `valida_filtri` sollevava gia' ValueError
    per le chiavi legacy e i chiamanti la intercettano cosi'.
    """


@dataclass(frozen=True)
class FiltroStadio:
    """Il filtro di **uno** stadio, gia' validato e normalizzato.

    Un solo oggetto alimenta conteggio, enumerazione, export e analisi: e' il
    rimedio a B06, dove `valida_filtri`, `count_combinations_ex` e
    `iter_combinations_ex` descrivevano tre domini diversi — il conteggio
    percorreva tutti gli stadi ricevuti, l'enumerazione solo i primi tre, e la
    validazione non guardava ne' il numero di stadi ne' i valori. Con quattro
    stadi il conteggio diceva 6 e l'iteratore ne produceva 1.

    `p` e `j` sono triple di tuple di nomi ammissibili, gia' espanse: `ANY` e'
    diventato l'elenco completo delle opzioni, un valore singolo una tupla di
    uno. Da qui in poi non esistono piu' wildcard da interpretare.
    """

    p: Tuple[Tuple[str, ...], ...]
    j: Tuple[Tuple[str, ...], ...]
    j_uniform: bool = False

    def cardinalita(self) -> int:
        """Quante combinazioni produce questo stadio. Non enumera nulla."""
        totale = 1
        for scelte in self.p:
            totale *= len(scelte)
        if self.j_uniform:
            # solo le triple (v, v, v): tante quante i valori ammissibili di j0
            totale *= len(self.j[0])
        else:
            for scelte in self.j:
                totale *= len(scelte)
        return totale

    def combinazioni(self):
        """Le tuple (p0, p1, p2, j0, j1, j2) dello stadio, in ordine stabile.

        L'ordine e' quello storico — il fattore piu' a destra varia piu'
        rapidamente — perche' la numerazione «Combinazione #N» di CSV e PDF ci
        si appoggia.
        """
        if self.j_uniform:
            for p in iproduct(*self.p):
                for v in self.j[0]:
                    yield p + (v, v, v)
        else:
            for p in iproduct(*self.p):
                for j in iproduct(*self.j):
                    yield p + j


def _scelte(valore, opzioni, stadio, chiave):
    """Normalizza il valore di una chiave nella tupla dei nomi ammessi."""
    if valore == ANY:
        return tuple(opzioni)
    if isinstance(valore, str):
        candidati = (valore,)
    elif isinstance(valore, (list, tuple)):
        candidati = tuple(valore)
    else:
        raise FiltroNonValido(
            f"stadio {stadio}, {chiave}: tipo non ammesso "
            f"{type(valore).__name__}; attesi {ANY!r}, un nome o una lista di nomi")
    if not candidati:
        raise FiltroNonValido(
            f"stadio {stadio}, {chiave}: elenco vuoto; nessun valore "
            "selezionabile non e' un filtro, e' un dominio impossibile")
    visti = set()
    for nome in candidati:
        if not isinstance(nome, str):
            raise FiltroNonValido(
                f"stadio {stadio}, {chiave}: valore non testuale {nome!r} "
                f"(tipo {type(nome).__name__})")
        if nome not in opzioni:
            raise FiltroNonValido(
                f"stadio {stadio}, {chiave}: nome sconosciuto {nome!r}; "
                f"ammessi {sorted(opzioni)}")
        if nome in visti:
            raise FiltroNonValido(
                f"stadio {stadio}, {chiave}: valore {nome!r} ripetuto; "
                "enumererebbe due volte le stesse combinazioni")
        visti.add(nome)
    return candidati


def normalizza_filtri(filtri) -> Tuple[FiltroStadio, ...]:
    """Valida i filtri e li restituisce come contratto immutabile.

    Unico ingresso di conteggio, enumerazione, export e analisi. Controlla, in
    quest'ordine: il numero di stadi, le chiavi (legacy, mancanti, sconosciute),
    il tipo di `j_uniform` e infine il dominio di ogni valore.
    """
    if isinstance(filtri, dict) or isinstance(filtri, (str, bytes)):
        raise FiltroNonValido(
            f"attesa una sequenza di {N_STADI} filtri, ricevuto "
            f"{type(filtri).__name__}")
    try:
        stadi = list(filtri)
    except TypeError:
        raise FiltroNonValido(
            f"attesa una sequenza di {N_STADI} filtri, ricevuto "
            f"{type(filtri).__name__}") from None

    if len(stadi) != N_STADI:
        raise FiltroNonValido(
            f"attesi esattamente {N_STADI} stadi, ricevuti {len(stadi)}. "
            "Il gioco delle 27 carte e' definito su tre stadi: un numero "
            "diverso non descrive un dominio enumerabile.")

    normalizzati = []
    for n, f in enumerate(stadi):
        if not isinstance(f, dict):
            raise FiltroNonValido(
                f"stadio {n}: atteso un dizionario, ricevuto {type(f).__name__}")
        legacy = _CHIAVI_LEGACY & set(f)
        if legacy:
            raise FiltroNonValido(
                f"stadio {n}: chiavi filtro obsolete {sorted(legacy)}. "
                f"La numerazione e' passata a base 0: usa {CHIAVI_FILTRO}. "
                "Attenzione, non e' una semplice rinomina: la vecchia p2 "
                "(terzine) e' la nuova p1.")
        mancanti = set(CHIAVI_FILTRO) - set(f)
        if mancanti:
            raise FiltroNonValido(
                f"stadio {n}: chiavi filtro mancanti {sorted(mancanti)}")
        sconosciute = set(f) - set(CHIAVI_FILTRO) - {CHIAVE_UNIFORME}
        if sconosciute:
            raise FiltroNonValido(
                f"stadio {n}: chiavi filtro sconosciute {sorted(sconosciute)}; "
                f"ammesse {CHIAVI_FILTRO + (CHIAVE_UNIFORME,)}")
        uniforme = f.get(CHIAVE_UNIFORME, False)
        if not isinstance(uniforme, bool):
            raise FiltroNonValido(
                f"stadio {n}, {CHIAVE_UNIFORME}: atteso un booleano, "
                f"ricevuto {uniforme!r} ({type(uniforme).__name__})")
        normalizzati.append(FiltroStadio(
            p=tuple(_scelte(f[k], P_OPTS, n, k) for k in CHIAVI_P),
            j=tuple(_scelte(f[k], J_OPTS, n, k) for k in CHIAVI_J),
            j_uniform=uniforme))
    return tuple(normalizzati)


def valida_filtri(filtri):
    """Valida i filtri e scarta il risultato: conservata come nome storico."""
    normalizza_filtri(filtri)


def _combinazioni(filtri):
    """Enumera le combinazioni dei tre stadi a partire dal contratto.

    Ordine storico: lo stadio 0 varia piu' lentamente. Le combinazioni di ogni
    stadio vengono materializzate (al massimo 6³·2³ = 1.728 per stadio) perche'
    i cicli annidati le riattraversano; il prodotto fra stadi resta pigro.
    """
    per_stadio = [list(f.combinazioni()) for f in filtri]
    for s0 in per_stadio[0]:
        for s1 in per_stadio[1]:
            for s2 in per_stadio[2]:
                yield [s0, s1, s2]


def cardinalita(filtri) -> int:
    """Quante combinazioni producono i filtri gia' normalizzati. Non enumera."""
    totale = 1
    for f in filtri:
        totale *= f.cardinalita()
    return totale


def iter_combinations(filters):
    """Combinazioni filtrate, una lista di tre tuple per volta.

    Nome storico: fino al compartimento F questa variante ignorava le liste di
    valori e `j_uniform`, che invece la variante `_ex` rispettava. Due
    semantiche per lo stesso filtro erano meta' di B06; ora c'e' un solo
    contratto (`normalizza_filtri`) e le due coppie di funzioni sono la stessa
    cosa, conservate con entrambi i nomi per i chiamanti esistenti.

    L'ordine di emissione e' invariato — il fattore piu' a destra varia piu'
    rapidamente — quindi la numerazione «Combinazione #N» nei PDF e nei CSV non
    cambia.
    """
    return _combinazioni(normalizza_filtri(filters))


def count_combinations(filters):
    """Quante combinazioni producono i filtri. Non enumera nulla."""
    return cardinalita(normalizza_filtri(filters))


# ─────────────────────────────────────────────────────────────────────────────
# PDF GENERATION (filtro base)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# RENDERING PDF — funzione di disegno riusabile (sequenziale e parallela)
# ─────────────────────────────────────────────────────────────────────────────

def _make_painter(c, cell3, cell27, thin3, thin27, thick27):
    """
    GridPainter per una pagina con matrici 3×3 e 27×27.

    Va chiamata subito dopo la creazione della Canvas: reportlab non permette
    di definire un Form XObject mentre si sta disegnando una pagina.
    """
    from .pdfgrid import GridPainter, GridSpec
    return GridPainter(c, [
        GridSpec("m3",  cell3,  3,  thin_w=thin3),
        GridSpec("m27", cell27, 27, thin_w=thin27,
                 thick_at=(9, 18), thick_w=thick27),
    ])


def _new_canvas(target, ex=False):
    """
    Canvas A3 orizzontale + GridPainter pronto (griglie già registrate).

    `target` è un path o un file-like. Restituisce (canvas, painter).
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A3, landscape
    c = rl_canvas.Canvas(target, pagesize=landscape(A3))
    c.setTitle(tr("presentation.title"))
    if ex:
        painter = _make_painter(c, 7.5, 4.4, thin3=0.25, thin27=0.12,
                               thick27=0.75)
    else:
        painter = _make_painter(c, 9.5, 5.2, thin3=0.3, thin27=0.15,
                               thick27=0.9)
    return c, painter


def _render_combinations(c, params_list, start_index=1, progress_cb=None,
                        painter=None, annullato=None):
    """
    Disegna una sequenza di combinazioni sul canvas reportlab `c` (una pagina
    ciascuna). `start_index` è il numero della prima combinazione, per mantenere
    la numerazione globale «Combinazione #N» anche quando si rende a blocchi.
    Non chiama c.save(): lo fa il chiamante. Ritorna il numero di pagine rese.

    `painter` è un GridPainter già costruito sulla Canvas (le griglie vanno
    registrate come Form XObject PRIMA di disegnare la prima pagina). Se è
    None viene creato qui: comodo per l'uso diretto, purché la Canvas sia
    ancora vergine.
    """
    from reportlab.lib.pagesizes import A3, landscape
    from reportlab.lib import colors

    PAGE_W, PAGE_H = landscape(A3)

    BLUE   = colors.Color(0.10, 0.25, 0.60)
    RED    = colors.Color(0.60, 0.08, 0.08)
    GREEN2 = colors.Color(0.00, 0.38, 0.08)
    GRAY   = colors.Color(0.40, 0.40, 0.40)

    C3  = 9.5    # cella 3×3
    C27 = 5.2    # cella 27×27
    W3  = 3*C3
    W27 = 27*C27
    H27 = 27*C27
    ML  = 16     # margine sinistro
    MT  = PAGE_H - 18

    if painter is None:
        painter = _make_painter(c, C3, C27, thin3=0.3, thin27=0.15, thick27=0.9)

    def draw3(M, x0, y0):
        painter.draw("m3", M, x0, y0)

    def draw27(M, x0, y0):
        painter.draw("m27", M, x0, y0)

    def txt(s, x, y, size=6, bold=False, col=None):
        c.setFillColor(col or GRAY)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, y, s)

    idx = start_index - 1
    for params in params_list:
        idx += 1

        stages = [compute_stage(*p) for p in params]
        R = compute_R(stages)

        y = MT

        txt(tr("export.document.pdf.combination", number=idx), ML, y, size=7, bold=True,
            col=colors.Color(0.25,0.25,0.25))
        y -= 13

        x_p3  = ML
        x_j3  = x_p3 + W3 + 6
        x_sep = x_j3 + W3 + 12

        x_P27 = x_sep + 4
        x_J27 = x_P27 + W27 + 8
        x_S27 = x_J27 + W27 + 8

        txt("P_i  (27x27)", x_P27, y, size=5.5, bold=True, col=BLUE)
        txt("J_i  (27x27)", x_J27, y, size=5.5, bold=True, col=BLUE)
        txt("Stage_i  (27x27)", x_S27, y, size=5.5, bold=True, col=BLUE)
        txt("P_i (3x3)  J_i (3x3)", x_p3, y, size=5.5, bold=True, col=BLUE)
        y -= 8

        c.setStrokeColor(colors.Color(0.7,0.7,0.7))
        c.setLineWidth(0.5)
        c.line(x_sep, y+6, x_sep, y - 3*(H27+14) - 20)

        for i, ((p1,p2,p3,j1,j2,j3), (P27,J27,S27)) in enumerate(
                zip(params, stages)):

            sl = stage_label(i, p1,p2,p3, j1,j2,j3)
            txt(tr("export.document.pdf.stage", number=i, label=sl), ML, y, size=5.8, bold=True, col=RED)
            y -= 8

            for k, nm in enumerate([p1, p2, p3]):
                txt(nm, x_p3 + k*(W3/3+1), y, size=4.5, col=BLUE)
            for k, nm in enumerate([j1, j2, j3]):
                txt(nm, x_j3 + k*(W3/3+1), y, size=4.5, col=BLUE)
            y -= 5

            x_off = x_p3
            for nm in [p1, p2, p3]:
                draw3(MAT3_P[nm], x_off, y)
                x_off += W3/3 + 2
            x_off = x_j3
            for nm in [j1, j2, j3]:
                draw3(MAT3_J[nm], x_off, y)
                x_off += W3/3 + 2

            lp = kron_label(p3, p2, p1)
            lj = kron_label(j3, j2, j1)
            txt(lp, x_p3, y - W3 - 4, size=4, col=GRAY)
            txt(lj, x_j3, y - W3 - 4, size=4, col=GRAY)

            txt(lp,            x_P27, y, size=4.2, col=BLUE)
            txt(lj,            x_J27, y, size=4.2, col=BLUE)
            txt(f"P{i} o MSC o J{i}", x_S27, y, size=4.2, col=BLUE)
            y -= 7

            draw27(P27, x_P27, y)
            draw27(J27, x_J27, y)
            draw27(S27, x_S27, y)

            y -= H27 + 14

        c.setStrokeColor(colors.Color(0.45,0.45,0.45))
        c.setLineWidth(0.6)
        c.line(ML, y+8, PAGE_W-ML, y+8)
        y -= 2

        rl = R_label(params)
        txt("R:", ML, y, size=6, bold=True, col=GREEN2)
        txt(rl, ML+18, y, size=5, col=GREEN2)
        y -= 8

        draw27(R, x_S27, y)

        c.showPage()
        if progress_cb:
            progress_cb(idx)
        # Controllo per pagina: e' l'unita' di lavoro piu' piccola, quindi
        # l'annullamento e' percepito come immediato.
        if annullato is not None and annullato():
            raise ExportAnnullato(idx - (start_index - 1), 0)

    return idx - (start_index - 1)


def generate_pdf(path, filters, progress_cb=None, annullato=None):
    """Genera il PDF in modo sequenziale (un'unica Canvas)."""
    _check_cancelled(annullato)
    check_export_size(count_combinations(filters))
    from .parallel import atomic_write
    with atomic_write(path, annullato=annullato) as f:
        c, painter = _new_canvas(f, ex=False)
        n = _render_combinations(c, iter_combinations(filters), 1, progress_cb,
                                 painter=painter, annullato=annullato)
        c.save()
    return n


def _render_chunk_to_bytes(start_index, params_chunk, language=None):
    """
    Worker top-level (picklable): rende un blocco di combinazioni su un PDF in
    memoria e ne restituisce i byte. Eseguito nei processi figli.
    """
    import io
    if language is not None:
        set_language(language)
    buf = io.BytesIO()
    c, painter = _new_canvas(buf, ex=False)
    _render_combinations(c, params_chunk, start_index, painter=painter)
    c.save()
    return buf.getvalue()


def generate_pdf_parallel(path, filters, n_workers=None, progress_cb=None,
                          annullato=None):
    """
    Genera il PDF in parallelo: i processi figli rendono blocchi contigui di
    combinazioni in PDF separati (in memoria), poi uniti in ordine con pypdf.
    Contenuto e numerazione identici al sequenziale.

    Fallback automatico al sequenziale se: n_workers<=1, poche combinazioni,
    pypdf assente, o errore di multiprocessing.
    """
    from functools import partial
    return _pdf_parallel(path, filters,
                         total=count_combinations(filters),
                         items_iter=iter_combinations(filters),
                         sequential=lambda: generate_pdf(path, filters,
                                                         progress_cb,
                                                         annullato),
                         worker=partial(_render_chunk_to_bytes,
                                        language=get_language()),
                         n_workers=n_workers, progress_cb=progress_cb,
                         annullato=annullato,
                         what="Export PDF", cost_per_item=COSTO_PAGINA_PDF)


def _pdf_parallel(path, filters, *, total, items_iter, sequential, worker,
                  n_workers, progress_cb, what, cost_per_item,
                  annullato=None):
    """
    Motore comune degli export PDF paralleli (variante base ed estesa).

    Le combinazioni NON vengono materializzate: `items_iter` resta un
    generatore e `run_export` sottomette i blocchi con una finestra limitata.
    Con i filtri di default sarebbero 5.159.780.352 elementi: il vecchio
    `list(iter_combinations_ex(filters))` esauriva la RAM prima di scrivere
    un byte.

    L'unione dei blocchi passa da core/pdfmerge: scrittura atomica e
    deduplicazione delle risorse (ogni blocco incorpora la propria copia dei
    font, e senza deduplicazione il file finisce per pesare il 50% in piu' del
    sequenziale).
    """
    _check_cancelled(annullato, 0, total)
    check_export_size(total)

    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        _log.warning("pypdf non disponibile: export PDF sequenziale")
        return sequential()

    import io
    from .pdfmerge import deduplica
    from .parallel import atomic_write, cronometro

    scrittore = PdfWriter()

    def consume(pdf_bytes, _npages):
        # I risultati arrivano in ordine di sottomissione: le pagine si
        # accodano direttamente, senza tenere in RAM tutti i blocchi.
        for pagina in PdfReader(io.BytesIO(pdf_bytes)).pages:
            scrittore.add_page(pagina)

    n = run_export(total=total, items_iter=items_iter, sequential=sequential,
                   parallel_worker=worker, consume=consume,
                   n_workers=n_workers, cost_per_item=cost_per_item,
                   progress_cb=progress_cb, annullato=annullato, what=what)

    # `run_export` può aver fatto fallback al sequenziale: in quel caso il file
    # è già scritto e non c'è nulla da unire.
    if len(scrittore.pages):
        with cronometro(f"{what}: scrittura del PDF finale"):
            with atomic_write(path, annullato=annullato) as f:
                scrittore.write(f)
        with cronometro(f"{what}: deduplicazione risorse"):
            deduplica(path)
    _log.info("%s: completato, %d elementi -> %s", what, n, path)
    return n


def iter_combinations_ex(filters):
    """Combinazioni filtrate (nome esteso: stessa semantica di `iter_combinations`).

    Ogni filtro (uno per stadio) e' un dict con chiavi:
        p0, p1, p2  → ANY | nome | lista di nomi
        j0, j1, j2  → ANY | nome | lista di nomi
        j_uniform   → bool  (default False)

    Con `j_uniform=True` le triple (j0, j1, j2) dello stadio sono solo quelle
    della forma (v, v, v), con v preso dal filtro su j0; j1 e j2 vengono
    ignorate. Il contratto e' validato una sola volta da `normalizza_filtri`, e
    il conteggio usa lo stesso oggetto: non possono piu' descrivere domini
    diversi (B06).
    """
    return _combinazioni(normalizza_filtri(filters))


def count_combinations_ex(filters):
    """Conta le combinazioni senza generarle, dal contratto validato."""
    return cardinalita(normalizza_filtri(filters))


# ─────────────────────────────────────────────────────────────────────────────
# GUI — PANNELLO FILTRO PER UNO STADIO
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# RENDERING PDF ESTESO (_ex) — supporta filtri estesi (liste, j_uniform)
# ─────────────────────────────────────────────────────────────────────────────

def _render_combinations_ex(c, params_list, start_index=1, progress_cb=None,
                           painter=None, annullato=None):
    """Come _render_combinations ma col layout esteso usato dalla GUI."""
    from reportlab.lib.pagesizes import A3, landscape
    from reportlab.lib import colors

    PAGE_W, PAGE_H = landscape(A3)

    BLUE   = colors.Color(0.10, 0.25, 0.60)
    RED    = colors.Color(0.60, 0.08, 0.08)
    GREEN2 = colors.Color(0.00, 0.38, 0.08)
    GRAY   = colors.Color(0.40, 0.40, 0.40)

    C3   = 7.5
    C27  = 4.4
    W3   = 3 * C3
    GAP3 = 5
    W27  = 27 * C27
    H27  = 27 * C27

    ML = 12
    MT = PAGE_H - 16

    SX_W = 3 * W3 + 2 * GAP3
    x_sx = ML

    x_sep = x_sx + SX_W + 22
    x_P27 = x_sep + 10
    x_J27 = x_P27 + W27 + 6
    x_S27 = x_J27 + W27 + 6

    if painter is None:
        painter = _make_painter(c, C3, C27, thin3=0.25, thin27=0.12,
                                thick27=0.75)

    def draw3(M, x0, y0):
        painter.draw("m3", M, x0, y0)

    def draw27(M, x0, y0):
        painter.draw("m27", M, x0, y0)

    def txt(s, x, y, size=6, bold=False, col=None):
        c.setFillColor(col or GRAY)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, y, s)

    SX_STAGE_H = 8 + 4 + 3*C3 + 5 + 4 + 3*C3 + 11
    DX_STAGE_H = 8 + 8 + H27
    INTER      = 14
    STAGE_H    = max(SX_STAGE_H, DX_STAGE_H) + INTER

    idx = start_index - 1
    for params in params_list:
        idx += 1
        stages = [compute_stage(*p) for p in params]
        R = compute_R(stages)

        y = MT

        txt(f"#{idx}", ML, y, size=7, bold=True,
            col=colors.Color(0.28, 0.28, 0.28))
        txt("P_i  (27x27)",       x_P27, y, size=5.5, bold=True, col=BLUE)
        txt("J_i  (27x27)",       x_J27, y, size=5.5, bold=True, col=BLUE)
        txt("Stage_i  (27x27)",   x_S27, y, size=5.5, bold=True, col=BLUE)
        y -= 12

        sep_top = y + 8
        sep_bot = y - 3 * STAGE_H - H27 - 30
        c.setStrokeColor(colors.Color(0.70, 0.70, 0.70))
        c.setLineWidth(0.5)
        c.line(x_sep, sep_top, x_sep, sep_bot)

        for i, ((p1, p2, p3, j1, j2, j3), (P27, J27, S27)) in enumerate(
                zip(params, stages)):

            y_stage = y

            lp = kron_label(p3, p2, p1)
            lj = kron_label(j3, j2, j1)

            sl = stage_label(i, p1, p2, p3, j1, j2, j3)
            txt(tr("export.document.pdf.stage", number=i, label=sl), x_sx, y_stage, size=5.6,
                bold=True, col=RED)

            y_pnames = y_stage - 8
            for k, nm in enumerate([p1, p2, p3]):
                txt(nm, x_sx + k * (W3 + GAP3), y_pnames, size=4.0, col=BLUE)

            y_pmats = y_pnames - 4
            for k, nm in enumerate([p1, p2, p3]):
                draw3(MAT3_P[nm], x_sx + k * (W3 + GAP3), y_pmats)

            y_jnames = y_pmats - 3*C3 - 5
            for k, nm in enumerate([j1, j2, j3]):
                txt(nm, x_sx + k * (W3 + GAP3), y_jnames, size=4.0, col=BLUE)

            y_jmats = y_jnames - 4
            for k, nm in enumerate([j1, j2, j3]):
                draw3(MAT3_J[nm], x_sx + k * (W3 + GAP3), y_jmats)

            y_klabel = y_jmats - 3*C3 - 2
            txt(lp, x_sx, y_klabel,     size=3.6, col=GRAY)
            txt(lj, x_sx, y_klabel - 5, size=3.6, col=GRAY)

            y_27lbl = y_stage - 8
            txt(lp,                   x_P27, y_27lbl, size=3.8, col=BLUE)
            txt(lj,                   x_J27, y_27lbl, size=3.8, col=BLUE)
            txt(f"P{i} o MSC o J{i}", x_S27, y_27lbl, size=3.8, col=BLUE)

            y_27top = y_27lbl - 8
            draw27(P27, x_P27, y_27top)
            draw27(J27, x_J27, y_27top)
            draw27(S27, x_S27, y_27top)

            y -= STAGE_H

        c.setStrokeColor(colors.Color(0.45, 0.45, 0.45))
        c.setLineWidth(0.6)
        c.line(ML, y + 6, PAGE_W - ML, y + 6)
        y -= 4

        rl = R_label(params)
        txt("R:", ML, y, size=6, bold=True, col=GREEN2)
        txt(rl, ML + 18, y, size=5, col=GREEN2)
        y -= 8

        draw27(R, x_S27, y)

        c.showPage()
        if progress_cb:
            progress_cb(idx)
        # Controllo per pagina: e' l'unita' di lavoro piu' piccola, quindi
        # l'annullamento e' percepito come immediato.
        if annullato is not None and annullato():
            raise ExportAnnullato(idx - (start_index - 1), 0)

    return idx - (start_index - 1)


def generate_pdf_ex(path, filters, progress_cb=None, annullato=None):
    """Genera il PDF esteso in modo sequenziale (un'unica Canvas)."""
    _check_cancelled(annullato)
    check_export_size(count_combinations_ex(filters))
    from .parallel import atomic_write
    with atomic_write(path, annullato=annullato) as f:
        c, painter = _new_canvas(f, ex=True)
        n = _render_combinations_ex(c, iter_combinations_ex(filters), 1,
                                    progress_cb, painter=painter,
                                    annullato=annullato)
        c.save()
    return n


def _render_chunk_ex_to_bytes(start_index, params_chunk, language=None):
    """Worker top-level (picklable): rende un blocco esteso su PDF in memoria."""
    import io
    if language is not None:
        set_language(language)
    buf = io.BytesIO()
    c, painter = _new_canvas(buf, ex=True)
    _render_combinations_ex(c, params_chunk, start_index, painter=painter)
    c.save()
    return buf.getvalue()


def generate_pdf_ex_parallel(path, filters, n_workers=None, progress_cb=None,
                             annullato=None):
    """
    Versione parallela di generate_pdf_ex: blocchi resi nei processi figli e
    uniti in ordine con pypdf. Contenuto e numerazione identici al sequenziale.
    Fallback automatico al sequenziale (poche pagine, pypdf assente, errori MP).

    Nota sul dimensionamento: con il disegno ottimizzato (griglie come Form
    XObject) il sequenziale è già veloce, quindi il parallelo conviene solo per
    export grandi — su Windows lo spawn di N processi che re-importano numpy e
    reportlab ha un costo non trascurabile. `plan_workers` limita i worker al
    carico effettivo (almeno 80 pagine ciascuno).
    """
    from functools import partial
    return _pdf_parallel(path, filters,
                         total=count_combinations_ex(filters),
                         items_iter=iter_combinations_ex(filters),
                         sequential=lambda: generate_pdf_ex(path, filters,
                                                            progress_cb,
                                                            annullato),
                         worker=partial(_render_chunk_ex_to_bytes,
                                        language=get_language()),
                         n_workers=n_workers, progress_cb=progress_cb,
                         annullato=annullato,
                         what="Export PDF esteso",
                         cost_per_item=COSTO_PAGINA_PDF)
