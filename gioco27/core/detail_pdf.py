"""Detailed A3 card/matrix report, with measured indivisible configurations.

The complete three-stage P/J table identifies every allowed configuration.
Historical P[...] and R[m] aliases are additional classical/core annotations.
The mathematical core, C ordering and inverse-transformation matching remain
unchanged. Layout and fixed-size text planning live in detail_layout.
"""
import os
from dataclasses import dataclass

from .detail import combination_detail
from .combinations import count_combinations_ex, iter_combinations_ex
from .gioco_reale import IMPILAMENTO_DI, SIGLE
from .detail_layout import LAYOUT
from .log import get_logger
from .parallel import (COSTO_COMBO_DETTAGLIO, ExportAnnullato, ExportTooLarge,
                       atomic_write, cronometro, imap_ordered, plan_workers,
                       _check_cancelled)
from .permutations import compute_stage, mat_to_perm27
from ..i18n import get_language, set_language, tr

_log = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Corrispondenza con gli indici del programma C.
#
# Il C usa DUE tabelle di permutazioni su {S,C,D}:
#   M[6] (mescolamenti, righe del tabellone): SCD SDC CSD DSC CDS DCS
#   W[6] (impilamenti, gesto fisico dal dorso): SCD SDC CSD CDS DSC DCS
# I loop i, j, k del C e le etichette P[i][j][k][m] usano l'indice di M.
# Il fattore Python corrispondente al mescolamento fisico è P3 (v3, verificato
# contro la tavola del libro), con sigla identica a nome_mescolamento(idx).
# ─────────────────────────────────────────────────────────────────────────────
_SIGLE_M = SIGLE                     # ordine canonico M del C/libro
_MESC_IDX = {s + "_U": i for i, s in enumerate(_SIGLE_M)}
_J_IDX = {"I_3": 0, "R_U": 1}



def _strip(s):
    return s.replace("_U", "")


def _is_game_stage(p):
    """Classical family: P0 = P1 = identity and uniform J.

    Membership does not classify general configurations' physical feasibility.
    """
    return p[0] == "SCD_U" and p[1] == "SCD_U" and p[3] == p[4] == p[5]


def _stage_label(p):
    """Etichetta di raccolta di uno stadio (come 'CDS' nel C); per stadi non
    di gioco mostra i tre fattori P₂×P₁×P₀ (numerazione a base 0)."""
    if _is_game_stage(p):
        return _strip(p[2])
    return _strip(p[2]) + "×" + _strip(p[1]) + "×" + _strip(p[0])


def _stage_impilamento(p):
    """Sigla d'impilamento (gesto dal dorso) per uno stadio di gioco,
    None quando non e' definito questo alias classico."""
    if _is_game_stage(p):
        return IMPILAMENTO_DI[_strip(p[2])]
    return None


def adatta_testo(testo, max_w, misura, size=7.0, min_size=4.0, passo=0.25):
    """
    Riduce `testo` finche' non sta in `max_w`, e in ultima istanza lo tronca.

    `misura(testo, corpo) -> larghezza` e' iniettata dal chiamante (di norma
    `canvas.stringWidth` con il font scelto), cosi' la logica resta una
    funzione pura e verificabile senza un canvas PDF.

    Restituisce (testo_finale, corpo_finale).

    Serve per le combinazioni fuori dalle 1728 del gioco: li' l'etichetta di
    stadio non e' una sigla di tre lettere ma un prodotto di Kronecker come
    «SCD×CSD×SDC», tre volte piu' lungo, e a dimensione fissa sconfinava sul
    mazzo o sulla colonna accanto.
    """
    corpo = float(size)
    while corpo > min_size and misura(testo, corpo) > max_w:
        # `max` evita di scendere SOTTO il minimo dichiarato: senza, l'ultimo
        # decremento poteva portare 4,1 a 3,85 con min_size=4,0.
        corpo = max(min_size, corpo - passo)
    if misura(testo, corpo) <= max_w:
        return testo, corpo
    # non basta rimpicciolire: si tronca
    while testo and misura(testo + "\u2026", corpo) > max_w:
        testo = testo[:-1]
    return testo + "\u2026", corpo


def righe_tabellone(markers):
    """
    Le tre righe del tabellone, lette dalla griglia A_1/A_2/A_3.

    `markers` è d["markers"]: per ogni Asso (carattere, etichetta, posizione,
    settore ternario di 3 lettere s/c/d). La griglia ha una colonna per Asso e
    una riga per cifra ternaria, quindi la riga r si ottiene prendendo la
    r-esima lettera del settore di ciascun Asso.

    Lette da sinistra a destra, queste righe sono le sigle del TABELLONE di T,
    in ordine cronologico inverso: riga 0 in alto, riga 2 in basso, secondo la
    convenzione di core/gioco_reale.py («i tre mescolamenti impilati, il primo
    in basso»). Rileggendole con T_da_tabellone si riottiene esattamente T.

    PERCHÉ FUNZIONA SEMPRE. I tre Assi partono dalle posizioni 0, 13 e 26, cioè
    (0,0,0), (1,1,1) e (2,2,2): la diagonale ternaria. Se T = B₂ ⊗ B₁ ⊗ B₀
    agisce cifra per cifra, allora T(j,j,j) = (B₂(j), B₁(j), B₀(j)), quindi la
    colonna dell'Asso j è (B₂(j), B₁(j), B₀(j)) e la riga r, letta per intero,
    è la sigla completa di B₂₋ᵣ.

    La griglia dipende dunque SOLO da T, non dai parametri che l'hanno
    prodotta, e ogni T del modello è un prodotto di Kronecker GEN3³. Ne segue
    che i due tabelloni valgono per TUTTE le 1728³ = 5.159.780.352
    combinazioni: anche col rovesciamento di un solo mazzetto (J non uniforme),
    o con P0/P1 diversi dall'identità, senza giudizi sulla realizzabilità
    fisica. Verificato esaustivamente sui 216 T possibili in
    tests/test_tabellone_inverso.py.

    ATTENZIONE — le righe non sono sempre i mescolamenti stampati sulla pagina.
    Lo sono solo quando NON c'è alcun rovesciamento (216 combinazioni su 1728
    fra quelle di gioco). Un rovesciamento è un'inversione su ogni cifra e si
    fonde nelle righe, quindi le sigle effettive cambiano: in D#122 i
    mescolamenti sono DSC/CSD/SCD ma le righe risultano DCS/DSC/SDC. Restano un
    tabellone valido — le sigle di un gioco equivalente senza rovesciamenti che
    dà la stessa T — ma chiamarle «mescolamenti» sarebbe falso.

    Verificato sull'ancora #100 del libro (senza rovesciamenti): mescolamenti
    (CDS, CDS, CSD), Assi in 13/8/18 → settori ccc/sdd/dss → righe CSD, CDS, CDS.
    """
    return ["".join(markers[a][3][r] for a in range(3)).upper()
            for r in range(3)]


def righe_impilamenti(markers):
    """
    Le stesse righe con ogni sigla sostituita dalla propria inversa.

    La conversione è quella di IMPILAMENTO_DI: scambia CDS↔DSC e lascia ferme
    le altre quattro sigle, che coincidono con la propria inversa (la «Prima
    Crisi di Seldon»).

    Questo è il TABELLONE DI T⁻¹, non solo una curiosità notazionale. Il
    tabellone agisce cifra per cifra — T = B₂ ⊗ B₁ ⊗ B₀ — e l'inversa di un
    prodotto di Kronecker è il prodotto delle inverse:

        T⁻¹ = B₂⁻¹ ⊗ B₁⁻¹ ⊗ B₀⁻¹

    Invertire ogni singola riga inverte quindi l'intera permutazione. Poiché
    la sigla d'impilamento È l'inversa di quella di mescolamento, la stessa
    tabella si legge in due modi: il gesto fisico da eseguire, e il tabellone
    della permutazione inversa. Verificato su tutte e 216 le sequenze del
    gioco (vedi tests/test_tabellone_inverso.py).

    Una riga sintetica che non sia una sigla valida, i cui settori non formano
    una permutazione, viene lasciata invariata invece di far fallire l'export.
    """
    return [IMPILAMENTO_DI.get(riga, riga) for riga in righe_tabellone(markers)]


def _reversed_stage(p):
    """Lo stadio inverte il mazzo? (J di gioco = R_U uniforme)."""
    return all(j == "R_U" for j in p[3:])


def _r_index(params):
    """Indice R[m] nella convenzione del C: stadio 1 = bit più significativo
    (m = r1*4 + r2*2 + r3).

    "stadio 1/2/3" e' qui la numerazione STORICA a base 1 del programma C
    (stadio_storico = stage_index + 1): `params` resta invece nell'ordine del
    dominio, con `params[0]` = stage_index 0. Vedi `core/dominio.py` (M02)."""
    if not all(_is_game_stage(p) for p in params):
        return None
    return sum((1 << (2 - k)) for k, p in enumerate(params) if _reversed_stage(p))


def _c_indices(params):
    """Indici (i, j, k, m) del C per una combinazione di gioco (etichetta
    P[i][j][k][m]); None se la combinazione non è nella forma del gioco."""
    if not all(_is_game_stage(p) for p in params):
        return None
    s1, s2, s3 = params
    return (_MESC_IDX[s3[2]], _MESC_IDX[s2[2]], _MESC_IDX[s1[2]], _r_index(params))


# ─────────────────────────────────────────────────────────────────────────────
# Ordinamento di stampa identico al programma C: cicli annidati i, j, k, m con
#   stadio 3 = i (esterno), stadio 2 = j, stadio 1 = k, inversioni = m,
# dove i, j, k sono indici della tabella M (mescolamenti) del C. Si
# generalizza a parametri più ampi usando le triple complete di ogni stadio.
#
# NUMERAZIONE (M02): "stadio 1/2/3" e' la numerazione STORICA del C, a base 1
# (stadio_storico = stage_index + 1). L'ordine di stampa e' quindi dallo stadio
# con stage_index 2 (il piu' esterno) allo stage_index 0. Le triple di ogni
# stadio restano nell'ordine del dominio, a cifra crescente: (p0,p1,p2) e
# (j0,j1,j2). Vedi il glossario in `core/dominio.py`.
# ─────────────────────────────────────────────────────────────────────────────

def _p_key(s):
    return (_MESC_IDX.get(s[2], 0), _MESC_IDX.get(s[1], 0), _MESC_IDX.get(s[0], 0))


def _j_key(s):
    return (_J_IDX.get(s[3], 0), _J_IDX.get(s[4], 0), _J_IDX.get(s[5], 0))


def _order_key(combo):
    s1, s2, s3 = combo
    # stadio 3 (i) più esterno, poi stadio 2 (j), stadio 1 (k), infine inversioni (m).
    return (_p_key(s3), _p_key(s2), _p_key(s1), _j_key(s1), _j_key(s2), _j_key(s3))


def order_like_c(params_list, annullato=None):
    """Ordina le combinazioni come le stampa il programma C (i, j, k, m)."""
    def key(combo):
        _check_cancelled(annullato)
        return _order_key(combo)
    result = sorted(params_list, key=key)
    _check_cancelled(annullato)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Etichette ed «Elenco matrici trasposte» (come findAllTransposesInResults
# del C, ma sull'insieme filtrato dell'export).
# ─────────────────────────────────────────────────────────────────────────────

def _perm_of(params, _cache={}):
    """Permutazione totale T (perm[i] = destinazione della carta i) di una
    combinazione, componendo le permutazioni di stadio (memoizzate)."""
    perm = list(range(27))
    for p in params:
        key = tuple(p)
        sp = _cache.get(key)
        if sp is None:
            sp = mat_to_perm27(compute_stage(*p)[2])
            _cache[key] = sp
        perm = [sp[v] for v in perm]
    return tuple(perm)


@dataclass(frozen=True)
class TransposeReferences:
    """Only the printable references plus the exact global inverse count."""
    shown: tuple
    total: int

    def __iter__(self):
        return iter(self.shown)

    def __len__(self):
        return len(self.shown)


def annotate_like_c(all_params, annullato=None, *, compact=False):
    """Per la lista ordinata di combinazioni calcola:
      labels[n]     — etichetta stile C: "P[i][j][k][m]" per le combinazioni
                      di gioco, altrimenti "D#n" (numerazione da 0 come Cntr);
      transposes[n] — elenco delle etichette delle combinazioni dell'export la
                      cui matrice è la TRASPOSTA di quella di n (per una
                      matrice di permutazione: la permutazione inversa).
    """
    labels, perms = [], []
    for n, params in enumerate(all_params):
        _check_cancelled(annullato)
        perms.append(_perm_of(params))
        ci = _c_indices(params)
        labels.append("P[%d][%d][%d][%d]" % ci if ci else "D#%d" % n)

    by_perm = {}
    for lb, pm in zip(labels, perms):
        _check_cancelled(annullato)
        by_perm.setdefault(pm, []).append(lb)

    if compact:
        # One small shared summary per transformation, instead of shipping a
        # complete inverse group in every worker task.
        by_perm = {pm: TransposeReferences(tuple(refs[:LAYOUT.max_transposes]), len(refs))
                   for pm, refs in by_perm.items()}
    transposes = []
    for pm in perms:
        _check_cancelled(annullato)
        inv = [0] * 27
        for i, d in enumerate(pm):
            inv[d] = i
        transposes.append(by_perm.get(tuple(inv),
                                      TransposeReferences((), 0) if compact else []))
    _check_cancelled(annullato)
    return labels, transposes


# ─────────────────────────────────────────────────────────────────────────────
# Font e decodifica carte (identica a DispDECH del C: X=10, semi ♠/♣/♥)
# ─────────────────────────────────────────────────────────────────────────────

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
_FONTS_READY = None   # ("DV","DVB")  oppure  ("Helvetica","Helvetica-Bold")

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "X", "J", "Q", "K"]


#: Fallback sempre disponibile: i font base sono incorporati in ReportLab.
_FONTS_FALLBACK = ("Helvetica", "Helvetica-Bold")


def _ensure_fonts():
    """Registra (una volta per processo) il font DejaVu coi glifi dei semi.

    Ritorna (font_regular, font_bold): i nomi DejaVu SOLO se la registrazione e'
    davvero riuscita, altrimenti il fallback Helvetica.

    B10: prima l'eccezione di `registerFont` veniva ingoiata e i nomi DV/DVB
    erano restituiti comunque. Il chiamante li passava a `setFont` e l'export
    moriva molto piu' tardi, con un errore che non parlava di font. Un fallback
    che non e' realmente utilizzabile non e' un fallback.
    """
    global _FONTS_READY
    if _FONTS_READY is not None:
        return _FONTS_READY
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        reg = os.path.join(_ASSETS, "DejaVuSans.ttf")
        bold = os.path.join(_ASSETS, "DejaVuSans-Bold.ttf")
        if not (os.path.exists(reg) and os.path.exists(bold)):
            _log.info("Font DejaVu non presenti negli asset: uso %s",
                      _FONTS_FALLBACK[0])
            _FONTS_READY = _FONTS_FALLBACK
            return _FONTS_READY
        try:
            pdfmetrics.registerFont(TTFont("DV", reg))
            pdfmetrics.registerFont(TTFont("DVB", bold))
        except Exception:
            # Anche una registrazione PARZIALE (il primo font passa, il secondo
            # no) finisce qui: non si mescolano i due insiemi.
            _log.exception("Registrazione dei font DejaVu fallita: uso %s",
                           _FONTS_FALLBACK[0])
            _FONTS_READY = _FONTS_FALLBACK
            return _FONTS_READY
        _FONTS_READY = ("DV", "DVB")
    except Exception:
        _log.exception("Font DejaVu non utilizzabili: uso %s", _FONTS_FALLBACK[0])
        _FONTS_READY = _FONTS_FALLBACK
    return _FONTS_READY


def _card(ch):
    """Carattere interno -> (testo carta con seme, is_red)."""
    if ch == "0":
        return ("A♥", True)            # Asso di cuori (rosso)
    if "A" <= ch <= "M":
        return (RANKS[ord(ch) - 65] + "♠", False)   # picche
    return (RANKS[ord(ch) - 78] + "♣", False)        # fiori


# ─────────────────────────────────────────────────────────────────────────────
# Rendering
# ─────────────────────────────────────────────────────────────────────────────

#: lato della cella della matrice 27x27 nel PDF dettagliato
DETAIL_CELL = LAYOUT.matrix_cell

def _detail_painter(c):
    """
    GridPainter per il PDF dettagliato: griglia NERA fine, come le <td>
    dell'HTML del programma C (nessun separatore di blocco spesso).

    Va costruito subito dopo la Canvas: reportlab non consente di definire un
    Form XObject mentre si sta disegnando una pagina.
    """
    from reportlab.lib import colors
    from .pdfgrid import GridPainter, GridSpec
    return GridPainter(c, [GridSpec("mdet", DETAIL_CELL, 27,
                                    thin_w=0.25, thin_c=colors.black)])


def _new_detail_canvas(target):
    """Canvas A3 orizzontale + painter per il PDF dettagliato."""
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A3, landscape
    c = rl_canvas.Canvas(target, pagesize=landscape(A3))
    c.setTitle(tr("export.document.pdf.detail_title"))
    return c, _detail_painter(c)


def _page_plan(params_list, transposes, annullato=None):
    from reportlab.lib.pagesizes import A3, landscape
    from .detail_layout import plan_pages
    return plan_pages(params_list, transposes, fonts=_ensure_fonts(),
                      indices=_c_indices, impilamenti=_stage_impilamento,
                      page_height=landscape(A3)[1], annullato=annullato)


def _filter_summary(filters):
    from .combinations import normalizza_filtri
    stages = normalizza_filtri(filters)
    classical = all(s.p[0] == ('SCD_U',) and s.p[1] == ('SCD_U',)
                    and (s.j_uniform or s.j[0] == s.j[1] == s.j[2]
                         and len(s.j[0]) == 1) for s in stages)
    if classical:
        return tr('export.document.detail.classic_filter')
    return tr('export.document.detail.general_filter',
              counts=' / '.join(str(s.cardinalita()) for s in stages))


def render_detail_pages(c, params_list, start_index=1, progress_cb=None,
                        labels=None, transposes=None, painter=None,
                        annullato=None, *, page_plan=None, page_start=1,
                        total_pages=None, total_configurations=None,
                        filter_summary=''):
    """One measured layout; whole blocks spill to a new page without scaling.

    Page ranges can be supplied by the parent for page-aligned parallel work.
    Returns the number of configurations, retaining the existing export API.
    """
    from .detail_layout import LAYOUT, measure_config, draw_config, draw_page_chrome
    params_list = list(params_list)
    if labels is None or transposes is None:
        labels, transposes = annotate_like_c(params_list, annullato, compact=True)
    if len(labels) != len(params_list) or len(transposes) != len(params_list):
        raise ValueError('annotations are not aligned with configurations')
    if painter is None:
        painter = _detail_painter(c)
    fonts = _ensure_fonts()
    if page_plan is None:
        page_plan = _page_plan(params_list, transposes, annullato)
    total_pages = total_pages if total_pages is not None else len(page_plan)
    total_configurations = (total_configurations if total_configurations is not None
                            else start_index - 1 + len(params_list))
    for page_number, page in enumerate(page_plan, page_start):
        _check_cancelled(annullato)
        draw_page_chrome(c, total=total_configurations, summary=filter_summary,
                         page=page_number, pages=total_pages, fonts=fonts)
        top = LAYOUT.content_top
        for pos in range(page.start, page.end):
            _check_cancelled(annullato, start_index - 1 + pos, len(params_list))
            params = params_list[pos]
            ci = _c_indices(params)
            plan = measure_config(params, transposes[pos], fonts=fonts,
                                  classic_indices=ci,
                                  impilamenti=tuple(_stage_impilamento(p) for p in params))
            d = combination_detail(params)
            draw_config(c, plan, d, top=top, number=start_index - 1 + pos,
                        total=total_configurations, params=params,
                        classic_indices=ci, painter=painter, fonts=fonts,
                        card=_card, inverse_rows=righe_impilamenti(d['markers']))
            top += plan.height + LAYOUT.config_gap
            if progress_cb:
                progress_cb(start_index + pos)
            _check_cancelled(annullato, start_index + pos, len(params_list))
        c.showPage()
    return len(params_list)


# ─────────────────────────────────────────────────────────────────────────────
# Generazione (sequenziale e parallela)
# ─────────────────────────────────────────────────────────────────────────────

#: Existing safety ceiling: preparation still sorts all parameters in memory.
#: Compact inverse summaries and page-aligned tasks avoid unused reference
#: transfers; ReportLab/PdfWriter still retain document resources in memory.
MAX_DETAIL_COMBOS = 200_000


def _prepare(filters, annullato=None):
    """
    Ordina le combinazioni come il C e calcola etichette + trasposte.

    Solleva ExportTooLarge se le combinazioni superano MAX_DETAIL_COMBOS:
    meglio un messaggio chiaro subito che un MemoryError dopo dieci minuti.
    """
    _check_cancelled(annullato)
    total = count_combinations_ex(filters)
    if total > MAX_DETAIL_COMBOS:
        raise ExportTooLarge(total, MAX_DETAIL_COMBOS)
    # Fase interamente seriale, e con molte combinazioni non e' trascurabile:
    # ordinamento globale + calcolo delle trasposte su tutto l'insieme.
    def params_checked():
        for params in iter_combinations_ex(filters):
            _check_cancelled(annullato)
            yield params

    with cronometro("PDF dettagliato: ordinamento e trasposte"):
        all_params = order_like_c(list(params_checked()), annullato=annullato)
        labels, transposes = annotate_like_c(all_params, annullato=annullato, compact=True)
    return all_params, labels, transposes


def _generate_sequential(path, all_params, labels, transposes, progress_cb=None,
                         annullato=None, *, filter_summary=""):
    _check_cancelled(annullato)
    with atomic_write(path, annullato=annullato) as f:
        c, painter = _new_detail_canvas(f)
        n = render_detail_pages(c, all_params, 1, progress_cb,
                                labels=labels, transposes=transposes,
                                painter=painter, annullato=annullato,
                                filter_summary=filter_summary)
        c.save()
    return n


def generate_detail_pdf(path, filters, progress_cb=None, annullato=None):
    """Export PDF dettagliato fedele (sequenziale)."""
    all_params, labels, transposes = _prepare(filters, annullato=annullato)
    return _generate_sequential(path, all_params, labels, transposes,
                                progress_cb, annullato,
                                filter_summary=_filter_summary(filters))


def _detail_chunk_to_bytes(task):
    """
    Worker top-level (picklable): rende un blocco su PDF in memoria.
    `task` carries the parameters and global page/filter context; references
    are compact summaries, not full inverse groups.
    """
    import io
    (start_index, params_chunk, labels_chunk, trans_chunk, language,
     page_start, total_pages, total_configurations, summary) = task
    set_language(language)
    buf = io.BytesIO()
    c, painter = _new_detail_canvas(buf)
    render_detail_pages(c, params_chunk, start_index,
                        labels=labels_chunk, transposes=trans_chunk,
                        painter=painter, page_start=page_start,
                        total_pages=total_pages,
                        total_configurations=total_configurations,
                        filter_summary=summary)
    c.save()
    return buf.getvalue(), len(params_chunk)


def generate_detail_pdf_parallel(path, filters, n_workers=None,
                                 progress_cb=None, annullato=None):
    """
    Export PDF dettagliato in parallelo: blocchi resi nei processi figli e
    uniti in ordine con pypdf.

    The parent measures configurations and partitions complete pages. Worker
    chunks follow those boundaries, preserving adaptive pagination and global
    page numbers. No full matrix plans are retained by the parent.

    Fallback automatico al sequenziale (pochi elementi, pypdf assente, errori
    di multiprocessing). Solleva ExportTooLarge oltre MAX_DETAIL_COMBOS.
    """
    all_params, labels, transposes = _prepare(filters, annullato=annullato)
    total = len(all_params)
    summary = _filter_summary(filters)

    def sequential():
        return _generate_sequential(path, all_params, labels, transposes,
                                    progress_cb, annullato, filter_summary=summary)

    plan = plan_workers(total, n_workers, min_chunk=1,
                        cost_per_item=COSTO_COMBO_DETTAGLIO)
    if plan is None:
        return sequential()
    n_workers, size = plan
    pages = _page_plan(all_params, transposes, annullato)

    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        _log.warning("pypdf non disponibile: export dettagliato sequenziale")
        return sequential()

    def tasks():
        start_page = 0
        while start_page < len(pages):
            _check_cancelled(annullato)
            end_page = start_page + 1
            s = pages[start_page].start
            while (end_page < len(pages)
                   and pages[end_page].end - s <= size):
                end_page += 1
            e = pages[end_page - 1].end
            yield (s + 1, all_params[s:e], labels[s:e], transposes[s:e],
                   get_language(), start_page + 1, len(pages), total, summary)
            start_page = end_page

    try:
        import io
        from .pdfmerge import deduplica
        writer = PdfWriter()
        done = 0
        _log.info("PDF dettagliato: %d combinazioni, %d worker, blocchi da %d",
                  total, n_workers, size)
        for pdf_bytes, nconfigs in imap_ordered(_detail_chunk_to_bytes, tasks(),
                                              n_workers, annullato=annullato):
            if annullato is not None and annullato():
                raise ExportAnnullato(done, total)
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                writer.add_page(page)
            done += nconfigs
            if progress_cb:
                progress_cb(done)
        _check_cancelled(annullato, done, total)
        with cronometro("PDF dettagliato: scrittura del PDF finale"):
            with atomic_write(path, annullato=annullato) as f:
                writer.write(f)
        with cronometro("PDF dettagliato: deduplicazione risorse"):
            deduplica(path)
        _log.info("PDF dettagliato: completato, %d combinazioni -> %s",
                  total, path)
        return total
    except ExportAnnullato:
        _log.info("PDF dettagliato annullato dall'utente")
        raise
    except Exception:
        _log.exception("Export dettagliato parallelo fallito: "
                       "fallback sequenziale")
        return sequential()
