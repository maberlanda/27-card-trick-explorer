"""
Export PDF dettagliato — riproduzione fedele del layout HTML del programma C
(elenco_disposizioni.html), alimentata dal motore Python (quindi non limitata
alle 1728 sequenze del gioco reale: copre tutti i parametri filtrati).

Due combinazioni per pagina A3 orizzontale (meta' superiore e inferiore,
come l'elenco continuo del C); ogni combinazione mostra, da sinistra a destra:
  - DISP_INIZIO e i tre blocchi "Mescolamento N = sigla (impilamento: sigla)":
    il mazzo iniziale e dopo ogni mescolamento, reso come nel C (9 righe x
    4 colonne: tripla impilata + 3 carte singole), semi reali;
  - DISP INIZIALE / DISP FINALE come tabella bordata (stile C);
  - ROVESCIAMENTO (testo verticale) con R[m] e i flag M0/M1/M2;
    Per le combinazioni fuori dalle 1728 del gioco (P1/P2 non identita', o J
    non uniforme) gli indici M[k] NON vengono stampati: nel C sono indici
    numerici nella tabella dei mescolamenti e qui non esistono. Al loro posto
    l'elenco delle raccolte P2xP1xP0 con una nota esplicita.
  - MOLTIPLICAZIONE (testo verticale) con M[k]xM[j]xM[i] (indici numerici del
    C), la riga dei mescolamenti in grassetto e quella degli impilamenti in
    piccolo — esattamente come l'HTML del C v3;
  - POSIZIONE ASSO #1/#2/#3 con posizione e settore ternario, e un riquadro
    con DUE griglie: il TABELLONE DI T (i settori ternari cosi' come sono,
    minuscoli, colonne A_1/A_2/A_3 = i tre Assi, come nel C) e sotto il
    TABELLONE DI T^-1, cioe' le stesse righe con ogni sigla sostituita dalla
    propria inversa (CDS<->DSC), in maiuscolo, con le etichette di riga
    M_2/M_1/M_0 perche' si legge in orizzontale. Rileggendole con
    T_da_tabellone si riottengono esattamente T e T^-1, in tutte e 1728 le
    combinazioni. NB: le righe coincidono con i mescolamenti stampati sopra
    solo se non c'e' alcun rovesciamento; vedi righe_tabellone();
  - la matrice di permutazione 27x27 (verde/bianco, griglia nera come le celle
    HTML del C) con intestazione "Matrice: P[i][j][k][m]" e, sotto, i
    mescolamenti, il periodo e l'«Elenco matrici trasposte» (le combinazioni
    dell'export la cui matrice è la trasposta di questa, come nel C).

I dati provengono da gioco27.core.detail.combination_detail, verificato
coerente con la simulazione fisica del C. La numerazione D# parte da 0 come
il contatore Cntr del C.
"""
import os

from .detail import combination_detail
from .combinations import count_combinations_ex, iter_combinations_ex
from .gioco_reale import IMPILAMENTO_DI
from .log import get_logger
from .parallel import (COSTO_COMBO_DETTAGLIO, ExportAnnullato, ExportTooLarge,
                       atomic_write, cronometro, imap_ordered, plan_workers,
                       _check_cancelled)
from .permutations import compute_stage, mat_to_perm27

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
_SIGLE_M = ("SCD", "SDC", "CSD", "DSC", "CDS", "DCS")   # ordine M del C
_MESC_IDX = {s + "_U": i for i, s in enumerate(_SIGLE_M)}
_J_IDX = {"I_3": 0, "R_U": 1}

#: combinazioni per pagina A3 (metà superiore/inferiore)
COMBOS_PER_PAGE = 2


def _strip(s):
    return s.replace("_U", "")


def _is_game_stage(p):
    """Stadio eseguibile come gesto fisico del gioco: P1 = P2 = identità
    (la raccolta agisce al livello dei blocchi, P3) e J uniforme."""
    return p[0] == "SCD_U" and p[1] == "SCD_U" and p[3] == p[4] == p[5]


def _stage_label(p):
    """Etichetta di raccolta di uno stadio (come 'CDS' nel C); per stadi non
    di gioco mostra i tre fattori P₂×P₁×P₀ (numerazione a base 0)."""
    if _is_game_stage(p):
        return _strip(p[2])
    return _strip(p[2]) + "×" + _strip(p[1]) + "×" + _strip(p[0])


def _stage_impilamento(p):
    """Sigla d'impilamento (gesto dal dorso) per uno stadio di gioco,
    None per stadi non eseguibili con un solo gesto."""
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
    o con P1/P2 diversi dall'identità, cioè per combinazioni che non sono
    nemmeno eseguibili a mano. Verificato esaustivamente sui 216 T possibili in
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

    Una riga che non sia una sigla valida — può capitare con combinazioni non
    eseguibili fisicamente, dove i settori degli Assi non formano una
    permutazione — viene lasciata invariata invece di far fallire l'export.
    """
    return [IMPILAMENTO_DI.get(riga, riga) for riga in righe_tabellone(markers)]


def _reversed_stage(p):
    """Lo stadio inverte il mazzo? (J di gioco = R_U uniforme)."""
    return p[3] == "R_U"


def _r_index(params):
    """Indice R[m] nella convenzione del C: stadio 1 = bit più significativo
    (m = r1*4 + r2*2 + r3)."""
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
# generalizza a parametri più ampi usando le triple complete (P3,P2,P1) e
# (J1,J2,J3) per ogni stadio.
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


def annotate_like_c(all_params, annullato=None):
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

    transposes = []
    for pm in perms:
        _check_cancelled(annullato)
        inv = [0] * 27
        for i, d in enumerate(pm):
            inv[d] = i
        transposes.append(by_perm.get(tuple(inv), []))
    _check_cancelled(annullato)
    return labels, transposes


# ─────────────────────────────────────────────────────────────────────────────
# Font e decodifica carte (identica a DispDECH del C: X=10, semi ♠/♣/♥)
# ─────────────────────────────────────────────────────────────────────────────

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
_FONTS_READY = None   # ("DV","DVB")  oppure  ("Helvetica","Helvetica-Bold")

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "X", "J", "Q", "K"]


def _ensure_fonts():
    """Registra (una volta per processo) il font DejaVu coi glifi dei semi.
    Ritorna (font_regular, font_bold). Fallback a Helvetica se il font manca."""
    global _FONTS_READY
    if _FONTS_READY is not None:
        return _FONTS_READY
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        reg = os.path.join(_ASSETS, "DejaVuSans.ttf")
        bold = os.path.join(_ASSETS, "DejaVuSans-Bold.ttf")
        if os.path.exists(reg) and os.path.exists(bold):
            try:
                pdfmetrics.registerFont(TTFont("DV", reg))
                pdfmetrics.registerFont(TTFont("DVB", bold))
            except Exception:
                pass
            _FONTS_READY = ("DV", "DVB")
        else:
            _FONTS_READY = ("Helvetica", "Helvetica-Bold")
    except Exception:
        _FONTS_READY = ("Helvetica", "Helvetica-Bold")
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
DETAIL_CELL = 6.5

# ─────────────────────────────────────────────────────────────────────────
# Layout della colonna centrale, in punti RELATIVI a yB (il bordo superiore
# dei mazzi). Dall'alto in basso:
#
#   1. riquadro dei due TABELLONI     — allineato in cima come i mazzi
#   2. ROVESCIAMENTO                  — R[m] e i flag M0/M1/M2
#   3. MOLTIPLICAZIONE                — indici M[...], mescolamenti, Assi
#
# Prima i tabelloni stavano a metà altezza, sotto la tabella degli Assi: il
# blocco più recente finiva nel punto meno visibile della pagina, e sopra
# restava spazio inutilizzato.
#
# Sono costanti di modulo e non numeri sparsi nel renderer perché i test ne
# verificano l'ordine e l'ingombro: la metà inferiore della pagina ha poco
# margine, e un blocco spostato di troppo uscirebbe dal foglio.
OFF_TABELLONI = +20
OFF_ROVESCIAMENTO = -45
OFF_MOLTIPLICAZIONE = -166

#: ingombro verticale del riquadro dei tabelloni (calcolato in `griglia`)
ALTEZZA_TABELLONI = 164

#: Altezza dei due blocchi con l'etichetta verticale, misurata da OFF_*.
#: ROVESCIAMENTO: R[m] piu' i tre flag M0/M1/M2, 13 pt di passo.
#: MOLTIPLICAZIONE: indici, mescolamenti, impilamenti e le tre righe
#: POSIZIONE ASSO (che partono 44 pt sotto e occupano 2x13+4).
ALTEZZA_ROVESCIAMENTO = 16 + 2 * 13
ALTEZZA_MOLTIPLICAZIONE = 44 + 2 * 13 + 4
# ─────────────────────────────────────────────────────────────────────────


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
    c.setTitle("Gioco delle 27 carte — dettaglio disposizioni")
    return c, _detail_painter(c)


def render_detail_pages(c, params_list, start_index=1, progress_cb=None,
                        labels=None, transposes=None, painter=None,
                        annullato=None):
    """Disegna le combinazioni sul canvas `c`: DUE per pagina A3 orizzontale
    (metà superiore e metà inferiore, separate da una linea), nello stile
    dell'elenco continuo del C. `labels`/`transposes` (opzionali) sono le
    liste allineate al blocco prodotte da annotate_like_c sull'INTERO export;
    se assenti vengono calcolate sul blocco locale. Non chiama c.save().

    `painter` è un GridPainter già registrato sulla Canvas; se None viene
    creato qui (valido solo se la Canvas è ancora vergine)."""
    from reportlab.lib.pagesizes import A3, landscape
    from reportlab.lib import colors

    FR, FB = _ensure_fonts()
    PAGE_W, PAGE_H = landscape(A3)
    BLACK = colors.black
    RED = colors.Color(0.75, 0, 0)
    GREEN = colors.Color(0.0, 0.5, 0.0)          # 'green' HTML del C
    WHITE = colors.white
    BORDER = colors.black                        # bordi 1px neri come nel C
    if painter is None:
        painter = _detail_painter(c)
    BLUE = colors.Color(0.10, 0.25, 0.60)
    GRAY = colors.Color(0.35, 0.35, 0.35)

    params_list = list(params_list)
    if labels is None or transposes is None:
        # Fallback: annotazioni calcolate sul solo blocco locale (i chiamanti
        # del modulo passano sempre le liste globali, allineate al blocco).
        labels, transposes = annotate_like_c(params_list)

    def Tt(s, x, y, size=7, bold=False, col=BLACK, center=False):
        c.setFillColor(col)
        c.setFont(FB if bold else FR, size)
        (c.drawCentredString if center else c.drawString)(x, y, s)

    def Tt_fit(s, x, y, max_w, size=7, min_size=4.0, bold=False, col=BLACK):
        """Come Tt, ma adatta il testo a `max_w` (vedi adatta_testo)."""
        font = FB if bold else FR
        testo, corpo = adatta_testo(
            s, max_w, lambda t, dim: c.stringWidth(t, font, dim),
            size=size, min_size=min_size)
        Tt(testo, x, y, size=corpo, bold=bold, col=col)
        return corpo

    def vtext(s, x, y, size=9):
        c.saveState()
        c.translate(x, y)
        c.rotate(90)
        c.setFont(FB, size)
        c.setFillColor(BLACK)
        c.drawCentredString(0, 0, s)
        c.restoreState()

    def cell(x, y, w, h):
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.rect(x, y, w, h, fill=0, stroke=1)

    def draw_deck(deck, x0, y0, title, subtitle=None, etichetta=None):
        """
        Disegna un mazzo con intestazione.

        `etichetta`, se data, va su una riga propria sotto il titolo e viene
        ridotta per stare nella larghezza della colonna: con le combinazioni
        fuori dal gioco è un prodotto di Kronecker, non una sigla di tre
        lettere, e a dimensione fissa sconfinava sul mazzo successivo.
        """
        w1, wc, rowH = 24, 18, 26
        larghezza = w1 + 3 * wc
        if etichetta:
            Tt(title, x0, y0 + 23, size=6.6, bold=True, col=BLUE)
            Tt_fit(etichetta, x0, y0 + 15, larghezza, size=6.6, bold=True,
                   col=BLUE)
        else:
            Tt_fit(title, x0, y0 + 16, larghezza, size=6.6, bold=True,
                   col=BLUE)
        if subtitle:
            Tt_fit(subtitle, x0, y0 + 6, larghezza, size=5.5, col=GRAY)
        for n in range(9):
            ry = y0 - n * rowH
            trip = [deck[3 * n], deck[3 * n + 1], deck[3 * n + 2]]
            cell(x0, ry - rowH, w1, rowH)
            for ci in range(3):
                cell(x0 + w1 + ci * wc, ry - rowH, wc, rowH)
            for li, ch in enumerate(trip):
                t, red = _card(ch)
                Tt(t, x0 + 4, ry - 9 - li * 7, size=7, col=RED if red else BLACK)
            for ci, ch in enumerate(trip):
                t, red = _card(ch)
                Tt(t, x0 + w1 + ci * wc + wc / 2, ry - rowH / 2 - 3, size=8,
                   col=RED if red else BLACK, center=True)
        return w1 + 3 * wc

    def draw_matrix(M, x0, y0, cell_sz=DETAIL_CELL):
        # Celle verdi/bianche con griglia nera 1px: come le <td> dell'HTML C.
        # La griglia (56 linee, identica su ogni matrice del documento) e' un
        # Form XObject registrato una volta sola: vedi core/pdfgrid.py.
        painter.draw("mdet", M, x0, y0, fill=GREEN, background=WHITE)
        return 27 * cell_sz

    ML = 26
    # Due combinazioni per pagina: metà superiore e metà inferiore.
    Y_TOPS = (PAGE_H - 14, PAGE_H / 2 - 10)
    Y_SEP = PAGE_H / 2 + 4          # linea di separazione fra le due metà

    def draw_combo(yTop, dnum, params, label, trans):
        d = combination_detail(params)

        Tt(f"D#{dnum:4d}", ML, yTop - 10, size=12, bold=True)

        # DISP INIZIALE / DISP FINALE — tabella bordata come nel C
        yI, yF = yTop - 26, yTop - 40
        lab_w, row_h = 84, 13
        s_ini = "  ".join(_card(ch)[0] for ch in d["dispositions"][0])
        s_fin = "  ".join(_card(ch)[0] for ch in d["dispositions"][-1])
        val_w = max(c.stringWidth(s_ini, FR, 8), c.stringWidth(s_fin, FR, 8)) + 10
        for yy, lab, val in ((yI, "DISP INIZIALE", s_ini),
                             (yF, "DISP FINALE", s_fin)):
            cell(ML, yy - 4, lab_w, row_h)
            cell(ML + lab_w, yy - 4, val_w, row_h)
            Tt(lab, ML + 3, yy, size=8, bold=True)
            Tt(val, ML + lab_w + 5, yy, size=8)

        # Blocchi mazzo: DISP_INIZIO + i tre mescolamenti (titoli stile C)
        yB = yTop - 76
        x = ML
        w = draw_deck(d["dispositions"][0], x, yB, "DISP_INIZIO")
        x += w + 20
        for n, p in enumerate(params):
            imp = _stage_impilamento(p)
            w = draw_deck(d["dispositions"][n + 1], x, yB,
                          f"Mescolamento {n} =",
                          f"(impilamento: {imp})" if imp else None,
                          etichetta=_stage_label(p))
            x += w + 20

        # Layout della colonna centrale: vedi le costanti OFF_* di modulo.
        Y_TABELLONI = yB + OFF_TABELLONI
        Y_ROVESC    = yB + OFF_ROVESCIAMENTO
        Y_MOLT      = yB + OFF_MOLTIPLICAZIONE
        # ─────────────────────────────────────────────────────────────

        # ROVESCIAMENTO — R[m] e flag M0/M1/M2 (TRUE/FALSE) come IsREVERSE
        xi = x + 10
        # `vtext` centra il testo ruotato sulla y data: si passa il punto medio
        # del blocco, così l'etichetta resta allineata anche se il blocco si
        # sposta. Prima erano due scostamenti fissi, e le etichette finivano
        # sotto il testo che dovevano etichettare.
        vtext("ROVESCIAMENTO", xi, Y_ROVESC - ALTEZZA_ROVESCIAMENTO / 2)
        m_idx = _r_index(params)
        Tt(f"R[{m_idx:4d}]", xi + 18, Y_ROVESC, size=8, bold=True)
        for n, p in enumerate(params):
            Tt(f"M{n} = {'TRUE' if _reversed_stage(p) else 'FALSE'}",
               xi + 18, Y_ROVESC - 16 - n * 13, size=8)

        # MOLTIPLICAZIONE — "M[k]xM[j]xM[i]" numerico + mescolamenti in
        # grassetto + impilamenti in piccolo, come l'HTML del C v3.
        vtext("MOLTIPLICAZIONE", xi, Y_MOLT - ALTEZZA_MOLTIPLICAZIONE / 2)
        xm2 = xi + 18
        ci = _c_indices(params)
        mesc = [_stage_label(p) for p in params]
        # larghezza utile: da xm2 fino alla tabella dei tabelloni
        W_MOLT = 150
        if ci is not None:
            i_c, j_c, k_c = ci[0], ci[1], ci[2]
            Tt(f"M[{k_c}]xM[{j_c}]xM[{i_c}]", xm2, Y_MOLT, size=8)
            imp = [_stage_impilamento(p) for p in params]
            Tt_fit("mescolamenti [" + "]x[".join(mesc) + "]",
                   xm2, Y_MOLT - 12, W_MOLT, size=8, bold=True)
            Tt_fit("impilamenti [" + "]x[".join(imp) + "]",
                   xm2, Y_MOLT - 22, W_MOLT, size=6.5, col=GRAY)
        else:
            # Combinazione fuori dalle 1728 del gioco: NON esiste un indice
            # M[k] nella tabella dei mescolamenti del C, perché lo stadio non
            # è una raccolta singola ma un prodotto di Kronecker P3×P2×P1.
            # Scrivere «M[SCD×SCD×SCD]» era falso: l'argomento di M è per
            # definizione un numero, e chi legge il PDF si aspetta l'indice.
            Tt("raccolte (P₂×P₁×P₀):", xm2, Y_MOLT, size=7, col=GRAY)
            Tt_fit("[" + "]x[".join(mesc) + "]",
                   xm2, Y_MOLT - 11, W_MOLT, size=8, bold=True)
            Tt_fit("indici M[...] non definiti: fuori dalle 1728 del gioco",
                   xm2, Y_MOLT - 21, W_MOLT, size=6, col=GRAY)

        # POSIZIONE ASSO #1/#2/#3 — celle bordate come nel C
        yy = Y_MOLT - 44
        for ai, (ch, mlabel, mpos, sect) in enumerate(d["markers"], 1):
            cell(xm2, yy - 4, 104, 12)
            cell(xm2 + 104, yy - 4, 22, 12)
            cell(xm2 + 126, yy - 4, 30, 12)
            Tt(f"POSIZIONE ASSO #{ai}", xm2 + 3, yy, size=8)
            Tt(f"{mpos:2d}", xm2 + 108, yy, size=8, bold=True)
            Tt(sect, xm2 + 130, yy, size=8, bold=True)
            yy -= 13

        # Griglia A_1 / A_2 / A_3 — celle bordate.
        # Sotto, la stessa griglia con ogni sigla sostituita dalla propria
        # inversa (CDS↔DSC). Le righe lette da sinistra a destra sono le sigle
        # dei mescolamenti, quindi la prima griglia è il tabellone di T e la
        # seconda quello di T⁻¹ — che è anche, letta come gesto, la sequenza
        # degli impilamenti da eseguire.
        # Le due griglie stanno dentro un'unica cornice e si leggono come una
        # sola tabella.
        #
        # Le colonne A_1/A_2/A_3 hanno senso solo per la griglia superiore: lì
        # ogni colonna è un Asso e, letta dall'alto in basso, dà il suo settore
        # ternario (come nell'HTML del programma C). La griglia inferiore si
        # legge invece in ORIZZONTALE — ogni riga è una sigla — quindi al posto
        # delle intestazioni di colonna porta le etichette di riga M_2/M_1/M_0,
        # dove M_0 è in basso: è la convenzione del tabellone di
        # core/gioco_reale.py, «i tre mescolamenti impilati, il primo in basso».
        #
        # PERCHÉ LE DIDASCALIE DICONO «T» E NON «MESCOLAMENTI»
        # ---------------------------------------------------
        # Le righe della griglia superiore coincidono con i mescolamenti
        # stampati poco sopra SOLO quando non c'è alcun rovesciamento (216
        # combinazioni su 1728). Un rovesciamento è a sua volta un'inversione
        # su ogni cifra, quindi si fonde nelle righe del tabellone e le sigle
        # effettive diventano altre: nella combinazione D#122 i mescolamenti
        # sono DSC/CSD/SCD ma le righe risultano DCS/DSC/SDC.
        #
        # Quelle righe restano un tabellone valido — sono le sigle di un gioco
        # EQUIVALENTE SENZA ROVESCIAMENTI che produce la stessa T — ma
        # chiamarle «mescolamenti» le metterebbe in contraddizione con la riga
        # scritta sopra. Le didascalie parlano quindi di T e T⁻¹, che è vero in
        # tutte e 1728 le combinazioni (vedi tests/test_tabellone_inverso.py).
        #
        # La colonna delle etichette è larga LAB_W; la griglia superiore viene
        # rientrata della stessa quantità, così le colonne dei dati delle due
        # griglie restano incolonnate.
        cw, chh = 20, 11
        LAB_W    = 16
        GRID_W   = 3 * cw
        TOT_W    = LAB_W + GRID_W
        TIT_H    = 18                 # titolo su due righe
        GRID_H   = 5 * chh            # intestazione + 3 righe
        GAP      = 10
        PAD_X, PAD_TOP, PAD_BOT = 8, 6, 8

        # Blocco centrato nel corridoio fra POSIZIONE ASSO (che finisce a
        # xm2+156) e la matrice 27x27 (che inizia a xm2+260): 104 pt.
        # La cornice è larga TOT_W + 2*PAD_X = 92 pt, quindi resta a 6 pt da
        # entrambe. `xg` è l'inizio delle CELLE, la cornice sta PAD_X più a
        # sinistra: sbagliare questo faceva mordere il bordo della tabella
        # POSIZIONE ASSO.
        xg = xm2 + 170
        yg = Y_TABELLONI - TIT_H - PAD_TOP
        xd = xg + LAB_W               # x delle colonne dei dati

        def griglia(y0, lettere_per_riga, titolo, col_titolo=BLUE,
                    intestazioni=True, etichette_riga=None):
            """
            Disegna una griglia 3x3 con titolo su due righe corte.

            intestazioni    : se True, la riga di testa A_1/A_2/A_3
            etichette_riga  : se data, 3 etichette (dall'alto) in una colonna
                              a sinistra, al posto delle intestazioni

            Il titolo deve stare dentro la larghezza del blocco: più a destra
            c'è la matrice 27x27, disegnata dopo, che riempie il proprio sfondo
            di bianco e coprirebbe il testo che deborda.

            Restituisce la y del bordo inferiore.
            """
            for k, riga in enumerate(reversed(titolo)):
                Tt(riga, xg, y0 + 7 + k * 6, size=5, bold=True, col=col_titolo)

            if intestazioni:
                for col_n, h in enumerate(("A_1", "A_2", "A_3")):
                    cell(xd + col_n * cw, y0 - chh + 3, cw, chh)
                    Tt(h, xd + col_n * cw + cw / 2, y0 - 5,
                       size=7, bold=True, center=True)

            for r in range(3):
                if etichette_riga is not None:
                    cell(xg, y0 - (r + 2) * chh + 3, LAB_W, chh)
                    Tt(etichette_riga[r], xg + LAB_W / 2,
                       y0 - (r + 1) * chh - 5, size=6, bold=True,
                       center=True, col=col_titolo)
                for a in range(3):
                    cell(xd + a * cw, y0 - (r + 2) * chh + 3, cw, chh)
                    Tt(lettere_per_riga[r][a], xd + a * cw + cw / 2,
                       y0 - (r + 1) * chh - 5, size=8, bold=True, center=True)
            return y0 - GRID_H + 3

        # Geometria calcolata prima, per poter tracciare la cornice attorno.
        y_bot_1 = yg - GRID_H + 3
        yg2     = y_bot_1 - GAP - TIT_H
        y_bot_2 = yg2 - GRID_H + 3

        c.setStrokeColor(BORDER)
        c.setLineWidth(1.1)
        c.rect(xg - PAD_X, y_bot_2 - PAD_BOT,
               TOT_W + 2 * PAD_X,
               (yg + TIT_H + PAD_TOP) - (y_bot_2 - PAD_BOT),
               fill=0, stroke=1)

        # 1) tabellone dei mescolamenti: i settori ternari così come sono
        #    (minuscoli, come le <td> dell'HTML del programma C)
        righe_mesc = [[d["markers"][a][3][r] for a in range(3)] for r in range(3)]
        griglia(yg, righe_mesc, ("TABELLONE", "DI T"))

        # 2) tabellone di T⁻¹: stesse righe con ogni sigla sostituita dalla
        #    propria inversa (CDS↔DSC), in MAIUSCOLO, da leggere per righe
        righe_imp = [list(sig) for sig in righe_impilamenti(d["markers"])]
        griglia(yg2, righe_imp,
                ("TABELLONE", "DI T\u207b\u00b9"), col_titolo=RED,
                intestazioni=False, etichette_riga=("M_2", "M_1", "M_0"))

        # Matrice 27x27 con intestazione stile C e info sotto
        xM = xm2 + 260
        Tt(f"Matrice: {label}", xM, yB + 8, size=10, bold=True)
        tot = draw_matrix(d["T_matrix"], xM, yB - 4)

        yU = yB - 4 - tot - 12
        # `tot` è la larghezza della matrice: oltre comincia l'elenco delle
        # trasposte, e con le etichette lunghe delle combinazioni fuori dal
        # gioco la scritta ci finiva sopra.
        Tt_fit(("Mescolamenti " if ci is not None else "Raccolte ")
               + " x ".join(mesc), xM, yU, tot, size=8, bold=True)
        Tt(f"Periodo: {d['period']:3d}", xM, yU - 11, size=8)

        # Elenco matrici trasposte — a destra della matrice, su più colonne
        # (così il blocco resta dentro mezza pagina).
        xT = xM + tot + 16
        yT0 = yB - 8
        Tt("Elenco matrici trasposte", xT, yT0, size=8)
        Tt("------------------------", xT, yT0 - 8, size=8)
        if trans:
            ROWS, COL_W, N_COLS = 20, 82, 3
            max_shown = ROWS * N_COLS
            shown = trans[:max_shown]
            for k, t in enumerate(shown):
                col_n, row_n = divmod(k, ROWS)
                Tt(t, xT + col_n * COL_W, yT0 - 19 - row_n * 9.5, size=7.5)
            if len(trans) > max_shown:
                Tt(f"... (+{len(trans) - max_shown} altre)",
                   xT, yT0 - 19 - ROWS * 9.5, size=7.5, col=GRAY)
        else:
            Tt("Trasposta non trovata.", xT, yT0 - 19, size=7.5)

    slot = 0
    idx = start_index - 1
    for pos, params in enumerate(params_list):
        idx += 1
        if slot == 1:
            c.setStrokeColor(colors.Color(0.55, 0.55, 0.55))
            c.setLineWidth(0.6)
            c.line(ML, Y_SEP, PAGE_W - ML, Y_SEP)
        draw_combo(Y_TOPS[slot], idx - 1, params, labels[pos], transposes[pos])
        slot += 1
        if slot == COMBOS_PER_PAGE:
            c.showPage()
            slot = 0
        if progress_cb:
            progress_cb(idx)
        # Controllo per combinazione: e' l'unita' di lavoro piu' piccola,
        # quindi l'annullamento e' percepito come immediato.
        if annullato is not None and annullato():
            raise ExportAnnullato(idx, len(params_list))
    if slot:
        c.showPage()
    return len(params_list)


# ─────────────────────────────────────────────────────────────────────────────
# Generazione (sequenziale e parallela)
# ─────────────────────────────────────────────────────────────────────────────

#: Limite del PDF dettagliato.
#:
#: A differenza degli altri export, questo NON puo' essere calcolato in
#: streaming: `order_like_c` ordina globalmente e `annotate_like_c` deve
#: conoscere TUTTE le combinazioni per trovare, per ognuna, quelle la cui
#: matrice e' la trasposta. E' un vincolo intrinseco del formato (riproduce
#: l'«Elenco matrici trasposte» del programma C), non un dettaglio
#: implementativo: la lista completa deve stare in RAM.
#:
#: 200.000 combinazioni sono circa 250 MB di strutture Python e ~2 ore di
#: rendering: oltre, l'export va rifiutato subito invece di far morire il
#: processo a meta' lavoro.
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
        labels, transposes = annotate_like_c(all_params, annullato=annullato)
    return all_params, labels, transposes


def _generate_sequential(path, all_params, labels, transposes, progress_cb=None,
                         annullato=None):
    _check_cancelled(annullato)
    import io as _io
    buf = _io.BytesIO()
    c, painter = _new_detail_canvas(buf)
    n = render_detail_pages(c, all_params, 1, progress_cb,
                            labels=labels, transposes=transposes,
                            painter=painter, annullato=annullato)
    c.save()
    with atomic_write(path, annullato=annullato) as f:
        f.write(buf.getvalue())
    return n


def generate_detail_pdf(path, filters, progress_cb=None, annullato=None):
    """Export PDF dettagliato fedele (sequenziale)."""
    all_params, labels, transposes = _prepare(filters, annullato=annullato)
    return _generate_sequential(path, all_params, labels, transposes,
                                progress_cb, annullato)


def _detail_chunk_to_bytes(task):
    """
    Worker top-level (picklable): rende un blocco su PDF in memoria.
    `task` = (start_index, params, labels, transposes).
    """
    import io
    start_index, params_chunk, labels_chunk, trans_chunk = task
    buf = io.BytesIO()
    c, painter = _new_detail_canvas(buf)
    render_detail_pages(c, params_chunk, start_index,
                        labels=labels_chunk, transposes=trans_chunk,
                        painter=painter)
    c.save()
    return buf.getvalue(), len(params_chunk)


def generate_detail_pdf_parallel(path, filters, n_workers=None,
                                 progress_cb=None, annullato=None):
    """
    Export PDF dettagliato in parallelo: blocchi resi nei processi figli e
    uniti in ordine con pypdf.

    I blocchi sono ~4x i worker (bilanciamento e progressi piu' fluidi) e di
    dimensione PARI: ogni blocco inizia a pagina nuova e, con 2 combinazioni
    per pagina, un blocco dispari lascerebbe una mezza pagina bianca in mezzo
    al documento.

    Fallback automatico al sequenziale (pochi elementi, pypdf assente, errori
    di multiprocessing). Solleva ExportTooLarge oltre MAX_DETAIL_COMBOS.
    """
    all_params, labels, transposes = _prepare(filters, annullato=annullato)
    total = len(all_params)

    def sequential():
        return _generate_sequential(path, all_params, labels, transposes,
                                    progress_cb, annullato)

    plan = plan_workers(total, n_workers, min_chunk=COMBOS_PER_PAGE,
                        cost_per_item=COSTO_COMBO_DETTAGLIO)
    if plan is None:
        return sequential()
    n_workers, size = plan
    size += size % COMBOS_PER_PAGE          # dimensione pari

    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        _log.warning("pypdf non disponibile: export dettagliato sequenziale")
        return sequential()

    def tasks():
        s = 0
        while s < total:
            _check_cancelled(annullato)
            e = min(s + size, total)
            yield (s + 1, all_params[s:e], labels[s:e], transposes[s:e])
            s = e

    try:
        import io
        from .pdfmerge import deduplica
        writer = PdfWriter()
        done = 0
        _log.info("PDF dettagliato: %d combinazioni, %d worker, blocchi da %d",
                  total, n_workers, size)
        for pdf_bytes, npages in imap_ordered(_detail_chunk_to_bytes, tasks(),
                                              n_workers, annullato=annullato):
            if annullato is not None and annullato():
                raise ExportAnnullato(done, total)
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                writer.add_page(page)
            done += npages
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
