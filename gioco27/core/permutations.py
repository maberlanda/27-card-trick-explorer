"""
Utilità sulle permutazioni: perm_to_mat3, build_P27, build_J27,
compute_stage, compute_R, compute_T_full, make_csv_row, write_csv.
"""
import numpy as np
import csv

from .constants import (PERM3, PERM3_J, PERM3_COLORS, _MSC_PERM)
from .log import get_logger

_log = get_logger(__name__)

# Cache del pattern compilato (popolata al primo uso da _compile_perm3_pat).
# NB: definita QUI, non importata da constants: e' un dettaglio interno.
_PERM3_PAT = None

def _compile_perm3_pat():
    global _PERM3_PAT
    if _PERM3_PAT is None:
        import re as _re
        _PERM3_PAT = _re.compile(
            "(" + "|".join(_re.escape(n) for n in PERM3_COLORS) + ")")
    return _PERM3_PAT

def configure_matrix_tags(txt_widget, base_font=("Courier New", 9)):
    """Configura tag-colore bold per tutti i nomi di matrice su un tk.Text."""
    for name, color in PERM3_COLORS.items():
        txt_widget.tag_configure(
            f"mx_{name}", foreground=color,
            font=(base_font[0], base_font[1], "bold"))

def insert_colored(txt_widget, text, base_tags=()):
    """Inserisce testo colorando i nomi di matrice (SCD_U, CDS_U ...) in bold."""
    if isinstance(base_tags, str):
        base_tags = (base_tags,)
    pat = _compile_perm3_pat()
    parts = pat.split(str(text))
    for part in parts:
        if not part:
            continue
        if part in PERM3_COLORS:
            txt_widget.insert("end", part, (f"mx_{part}",) + tuple(base_tags))
        elif base_tags:
            txt_widget.insert("end", part, tuple(base_tags))
        else:
            txt_widget.insert("end", part)


def perm_to_mat3(perm):
    """
    Converte una permutazione [p0,p1,p2] nella matrice 3×3 corrispondente.
    Convenzione: M[row, col] = 1  se perm[col] = row.
    Garantisce che il prodotto matriciale A @ B corrisponda alla composizione A ∘ B.
    """
    M = np.zeros((3, 3), dtype=float)
    for col, row in enumerate(perm):
        M[row, col] = 1.0
    return M

# Matrici 3×3 precalcolate per evitare ricalcoli durante la generazione
MAT3_P = {n: perm_to_mat3(p) for n, p in PERM3.items()}
MAT3_J = {n: perm_to_mat3(p) for n, p in PERM3_J.items()}


MSC = np.zeros((27, 27), dtype=float)
for _col, _row in enumerate(_MSC_PERM):
    MSC[_row, _col] = 1.0


# ─────────────────────────────────────────────────────────────────────────────
# CALCOLO MATRICI
# ─────────────────────────────────────────────────────────────────────────────

def build_P27(p1n, p2n, p3n):
    """
    Costruisce P = P3 ⊗ P2 ⊗ P1 come matrice 27×27.
    np.kron applicato due volte: kron(kron(P3,P2),P1) → 27×27.
    Multi-indice: (i₂,i₁,i₀) codificato come 9·i₂ + 3·i₁ + i₀.
    """
    return np.kron(np.kron(MAT3_P[p3n], MAT3_P[p2n]), MAT3_P[p1n])

def build_J27(j1n, j2n, j3n):
    """Costruisce J = J3 ⊗ J2 ⊗ J1 come matrice 27×27. Stesso schema di build_P27."""
    return np.kron(np.kron(MAT3_J[j3n], MAT3_J[j2n]), MAT3_J[j1n])

def compute_stage(p1n, p2n, p3n, j1n, j2n, j3n):
    """
    Calcola Stage = P ∘ MSC ∘ J  =  P @ MSC @ J.
    A @ B = composizione A ∘ B (prima B, poi A).
    Ritorna (P_27, J_27, Stage_27).
    """
    P = build_P27(p1n, p2n, p3n)
    J = build_J27(j1n, j2n, j3n)
    S = P @ MSC @ J
    return P, J, S

def compute_R(stages):
    """
    Calcola T = Stage3 ∘ Stage2 ∘ Stage1  =  S3 @ S2 @ S1.
    stages = lista di 3 tuple (P27, J27, Stage27). Usa l'indice [2] per Stage.
    La composizione è da destra a sinistra: Stage1 agisce prima, Stage3 per ultima.
    """
    return stages[2][2] @ stages[1][2] @ stages[0][2]

# ─────────────────────────────────────────────────────────────────────────────
# NOTAZIONE SIMBOLICA — etichette per PDF
# ─────────────────────────────────────────────────────────────────────────────

def kron_label(a, b, c):
    return f"({a} x {b} x {c})"

def stage_label(i, p1, p2, p3, j1, j2, j3):
    lp = kron_label(p3, p2, p1)
    lj = kron_label(j3, j2, j1)
    return f"Stage{i} = {lp} o MSC o {lj}"

def R_label(params):
    parts = []
    for i, (p1,p2,p3,j1,j2,j3) in enumerate(params):
        lp = kron_label(p3, p2, p1)
        lj = kron_label(j3, j2, j1)
        parts.append(f"[{lp} o MSC o {lj}]")
    return "T = " + " o ".join(reversed(parts))

# ─────────────────────────────────────────────────────────────────────────────
# MOTORE DI SEMPLIFICAZIONE ALGEBRICA SU {0,1,2}
# ─────────────────────────────────────────────────────────────────────────────
#
# Regole:
#   SCD_U = I_3          (identità)
#   SDC_U, CSD_U, DCS_U  sono involuzioni  (X∘X = I)
#   CDS_U = DSC_U^{-1}   (e viceversa DSC_U = CDS_U^{-1})
#   I_3   = I_3          (identità per J)
#   R_U   è un'involuzione
#
# La composizione f∘g su {0,1,2}: result[i] = f[g[i]]
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────
# NOMI DOPPI: due permutazioni su {0,1,2} hanno due nomi ciascuna.
#
#     [0,1,2]  =  SCD_U  (raccolta identica)   =  I_3  (nessuna inversione)
#     [2,1,0]  =  DCS_U  (raccolta S↔D)        =  R_U  (inversione completa)
#
# I nomi P e i nomi J descrivono la stessa permutazione da due punti di vista:
# i primi dicono COME si raccoglie, i secondi SE si capovolge. Sono alias, non
# elementi distinti.
#
# CONVENZIONE IN USCITA da compose3, deliberata e verificata da un test:
#
#     identita'   ->  I_3      (nome J,  via simplify3)
#     inversione  ->  DCS_U    (nome P,  primo match nella tavola)
#
# Non e' uniforme, ed e' una scelta: `compose3` vede solo il RISULTATO, non da
# dove viene. Una raccolta P genuinamente DCS_U e una inversione J danno la
# stessa permutazione, quindi nessuna regola basata sul solo risultato puo'
# distinguerle. Uniformare avrebbe un costo in entrambe le direzioni:
#
#   * sempre nomi GEN3  ->  l'identita' diventerebbe SCD_U invece di I_3,
#                           cambiando moltissime etichette gia' prodotte;
#   * sempre nomi J     ->  una raccolta DCS_U verrebbe mostrata come R_U,
#                           che non e' falso ma e' inusuale per una raccolta.
#
# Si e' quindi scelto di NON toccare le etichette e di documentare l'alias.
# Vedi tests/test_alias_nomi.py.
# ─────────────────────────────────────────────────────────────────────────
_ALL3 = {**PERM3, "I_3": [0,1,2], "R_U": [2,1,0]}

def _compose3(an, bn):
    """Componi due permutazioni su {0,1,2} e restituisce il nome canonico."""
    a, b = _ALL3[an], _ALL3[bn]
    result = tuple(a[b[i]] for i in range(3))
    for name, perm in _ALL3.items():
        if tuple(perm) == result:
            return name
    raise ValueError(f"Permutazione {result} non trovata nella tavola")

# Precalcola la tavola completa nome×nome → nome
_MULT3 = {}
for _a in _ALL3:
    for _b in _ALL3:
        _MULT3[(_a, _b)] = _compose3(_a, _b)

def simplify3(name):
    """
    Normalizza un nome: SCD_U → I_3.

    NB: l'alias simmetrico DCS_U → R_U NON viene applicato, di proposito.
    Vedi la nota sui NOMI DOPPI sopra la definizione di _ALL3.
    """
    if name == "SCD_U":
        return "I_3"
    return name

def compose3(an, bn):
    """
    Componi e semplifica: restituisce il nome ridotto di an ∘ bn.

    L'identita' esce come I_3 e l'inversione come DCS_U: convenzione
    deliberata, vedi la nota sui NOMI DOPPI sopra _ALL3.
    """
    an = simplify3(an)
    bn = simplify3(bn)
    result = _MULT3[(an, bn)]
    return simplify3(result)

# ─────────────────────────────────────────────────────────────────────────────
# CALCOLO DI A_i E SEMPLIFICAZIONE SIMBOLICA
# ─────────────────────────────────────────────────────────────────────────────
#
# Dalla teoria (vedi intestazione del modulo):
#   Stage_i  =  P_i ∘ MSC ∘ J_i
#            =  (P₂⊗P₁⊗P₀) ∘ MSC ∘ (J₂⊗J₁⊗J₀)
#
# Applicando la relazione fondamentale di commutazione a MSC ∘ (J3⊗J2⊗J1):
#   MSC ∘ (J₂⊗J₁⊗J₀)  =  (J₀⊗J₂⊗J₁) ∘ MSC
#
# Si ottiene:
#   Stage_i  =  (P₂⊗P₁⊗P₀) ∘ (J₀⊗J₂⊗J₁) ∘ MSC
#            =  [(P₂∘J₀) ⊗ (P₁∘J₂) ⊗ (P₀∘J₁)]  ∘  MSC
#            =  A_i ∘ MSC
#
# con:
#   A_i  =  (P₂∘J₀) ⊗ (P₁∘J₂) ⊗ (P₀∘J₁)     cioè   f_k = P_k ∘ J_(k+1 mod 3)
#
# INDICI INCROCIATI — lettura dalla rotazione (i₂,i₁,i₀) -> (i₀,i₂,i₁):
#   il fattore di grado k riceve la J della cifra (k+1) mod 3.
# Con i vecchi nomi P1/P2/P3 la stessa regola si leggeva come tre casi
# separati (P3←J1, P2←J3, P1←J2): era la numerazione a nasconderla.
# ─────────────────────────────────────────────────────────────────────────────

def compute_Ai_symbolic(p1n, p2n, p3n, j1n, j2n, j3n):
    """
    Calcola i tre fattori simbolici di A_i, in numerazione a BASE 0:

        f₂ = P₂ ∘ J₀
        f₁ = P₁ ∘ J₂
        f₀ = P₀ ∘ J₁

    cioè, in forma chiusa,   f_k = P_k ∘ J_(k+1 mod 3).

    Restituisce (f₂_name, f₁_name, f₀_name) già ridotti — l'ordine dei valori
    di ritorno è dal fattore più significativo al meno, come nel Kronecker
    P₂⊗P₁⊗P₀.

    Gli indici sono INCROCIATI per effetto della commutazione con MSC: la
    rotazione (i₂,i₁,i₀) -> (i₀,i₂,i₁) porta la cifra k+1 al posto k.

    NB: i nomi dei parametri (p1n, p2n, p3n) sono rimasti a base 1 per non
    toccare le firme interne; posizionalmente p1n è P₀, p2n è P₁, p3n è P₂.
    """
    f3 = compose3(p3n, j1n)   # f₂ = P₂ ∘ J₀
    f2 = compose3(p2n, j3n)   # f₁ = P₁ ∘ J₂
    f1 = compose3(p1n, j2n)   # f₀ = P₀ ∘ J₁
    return f3, f2, f1

def Ai_label(f3, f2, f1):
    """Etichetta simbolica di A_i = f3 ⊗ f2 ⊗ f1."""
    return f"({f3} x {f2} x {f1})"

def build_Ai_matrix(f3, f2, f1):
    """Matrice 27×27 di A_i = f3 ⊗ f2 ⊗ f1."""
    m3 = _ALL3[f3]
    m2 = _ALL3[f2]
    m1 = _ALL3[f1]
    M3 = perm_to_mat3(m3)
    M2 = perm_to_mat3(m2)
    M1 = perm_to_mat3(m1)
    return np.kron(np.kron(M3, M2), M1)

# ─────────────────────────────────────────────────────────────────────────────
# PERMUTAZIONE FINALE T = A2∘MSC∘A1∘MSC∘A0∘MSC  come lista {0..26}
# ─────────────────────────────────────────────────────────────────────────────

def mat_to_perm27(M):
    """Converte una matrice di permutazione 27×27 nella lista perm[col]=row."""
    # Un solo argmax vettorizzato lungo le righe invece di 27 argmax su slice.
    return np.argmax(np.asarray(M), axis=0).astype(int).tolist()


def perm27_to_mat(perm):
    """Matrice 27×27 (float) della permutazione perm[col] = row."""
    M = np.zeros((27, 27), dtype=float)
    M[np.asarray(perm, dtype=int), np.arange(27)] = 1.0
    return M


# ─────────────────────────────────────────────────────────────────────────────
# T SU VETTORI DI PERMUTAZIONE (percorso veloce, usato dagli export)
#
# compute_T_full costruiva, per OGNI combinazione, tre prodotti di Kronecker
# 27×27 (np.kron due volte ciascuno) e poi cinque moltiplicazioni di matrici
# 27×27 in float64: circa 95 us per combinazione. Ma T è una permutazione, e
# comporre permutazioni è un'indicizzazione di liste: 27 letture per passo.
#
# Qui sotto: A_i memoizzato per parametri di stadio (al massimo 6³·2³ = 1728
# chiavi distinte, quindi la cache è naturalmente limitata) e T ottenuto con
# cinque composizioni di liste. Misurato: 95 us -> 13 us per combinazione,
# cioè ~7x sull'export CSV, a parità di risultato.
# ─────────────────────────────────────────────────────────────────────────────

_MSC_VEC = tuple(_MSC_PERM)

#: (p1,p2,p3,j1,j2,j3) -> (etichetta_A_i, permutazione_A_i)
#: Dimensione massima 1728: una entry per ogni stadio possibile.
_STAGE_CACHE = {}


def _compose_vec(a, b):
    """(a ∘ b)[i] = a[b[i]] — prima b, poi a."""
    return [a[x] for x in b]


def _kron_vec(f3, f2, f1):
    """Vettore di permutazione di f3 ⊗ f2 ⊗ f1 con l'indice 9·i₂+3·i₁+i₀."""
    a, b, c = _ALL3[f3], _ALL3[f2], _ALL3[f1]
    return [9 * a[i // 9] + 3 * b[(i % 9) // 3] + c[i % 3] for i in range(27)]


def _stage_Ai(params_stage):
    """(etichetta, permutazione) di A_i per uno stadio, memoizzati."""
    hit = _STAGE_CACHE.get(params_stage)
    if hit is None:
        f3, f2, f1 = compute_Ai_symbolic(*params_stage)
        hit = (Ai_label(f3, f2, f1), _kron_vec(f3, f2, f1))
        _STAGE_CACHE[params_stage] = hit
    return hit


def compute_T_perm(params):
    """
    Come compute_T_full ma senza costruire matrici: restituisce
    (ai_labels, T_label, T_perm).

    T = A2 ∘ MSC ∘ A1 ∘ MSC ∘ A0 ∘ MSC, composto da destra a sinistra.
    """
    ai_labels = []
    ai_perms  = []
    for stage in params:
        label, perm = _stage_Ai(tuple(stage))
        ai_labels.append(label)
        ai_perms.append(perm)

    T = list(_MSC_VEC)
    T = _compose_vec(ai_perms[0], T)
    T = _compose_vec(_MSC_VEC, T)
    T = _compose_vec(ai_perms[1], T)
    T = _compose_vec(_MSC_VEC, T)
    T = _compose_vec(ai_perms[2], T)

    a1l, a2l, a3l = ai_labels
    T_label = f"T = {a3l} o MSC o {a2l} o MSC o {a1l} o MSC"
    return ai_labels, T_label, T

def compute_T_full(params):
    """
    Calcola T = A2∘MSC∘A1∘MSC∘A0∘MSC numericamente e simbolicamente.
    params: lista di 3 tuple (p0,p1,p2,j0,j1,j2)
    Restituisce:
        ai_labels  : lista di 3 stringhe simboliche per A0,A1,A2
        T_label    : stringa simbolica completa di T
        T_perm     : lista [0..26] della permutazione finale
        T_matrix   : matrice numpy 27×27

    Implementata sopra compute_T_perm: la matrice viene costruita UNA volta
    dalla permutazione finale, invece di moltiplicare cinque matrici 27×27.
    Chi non ha bisogno della matrice (gli export CSV) usi compute_T_perm.
    """
    ai_labels, T_label, T_perm = compute_T_perm(params)
    return ai_labels, T_label, T_perm, perm27_to_mat(T_perm)


# ─────────────────────────────────────────────────────────────────────────────
# CSV — separatore ";" con campi tra virgolette
# ─────────────────────────────────────────────────────────────────────────────

# NOTA: le intestazioni A0/A1/A2 rispecchiano la formula corretta:
#   A_i = (P2∘J0) ⊗ (P1∘J2) ⊗ (P0∘J1)
# Numerazione a BASE 0, allineata alle cifre ternarie: il fattore P_k agisce
# sulla cifra i_k. Con i vecchi nomi P1/P2/P3 lo sfasamento di uno costringeva
# a una conversione mentale a ogni lettura.
CSV_HEADER = [
    "#",
    "Stage0  [P2xP1xP0 o MSC o J2xJ1xJ0]",
    "Stage1  [P2xP1xP0 o MSC o J2xJ1xJ0]",
    "Stage2  [P2xP1xP0 o MSC o J2xJ1xJ0]",
    "A0  [(P2oJ0) x (P1oJ2) x (P0oJ1)]",
    "A1  [(P2oJ0) x (P1oJ2) x (P0oJ1)]",
    "A2  [(P2oJ0) x (P1oJ2) x (P0oJ1)]",
    "T_simbolica  [A2 o MSC o A1 o MSC o A0 o MSC]",
    "T_permutazione  [lista 0..26]",
]

def make_csv_row(combo_idx, params):
    """
    Costruisce la riga CSV completa con:
      #, Stage0, Stage1, Stage2, A0, A1, A2, T_simbolica, T_permutazione
    """
    # Colonne Stage
    stage_cols = []
    for p1,p2,p3,j1,j2,j3 in params:
        lp = kron_label(p3, p2, p1)
        lj = kron_label(j3, j2, j1)
        stage_cols.append(f"{lp} o MSC o {lj}")

    # Colonne A_i e T
    ai_labels, T_label, T_perm = compute_T_perm(params)

    perm_str = "[" + ",".join(str(x) for x in T_perm) + "]"

    return [str(combo_idx)] + stage_cols + ai_labels + [T_label, perm_str]

def write_csv(path, filters, progress_cb=None, annullato=None):
    """
    Scrive il CSV con separatore ; e campi tra doppi apici.

    `annullato()` viene interrogata ogni 200 righe: se vera, solleva
    ExportAnnullato e — grazie alla scrittura atomica — non lascia alcun file.
    """
    # Import locale per evitare un import circolare con combinations.py
    from .combinations import iter_combinations_ex
    from .parallel import ExportAnnullato, atomic_write, mai_annullato, _check_cancelled
    if annullato is None:
        annullato = mai_annullato
    count = 0
    with atomic_write(path, "w", annullato=annullato,
                      newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";", quotechar='"',
                       quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow(CSV_HEADER)
        for params in iter_combinations_ex(filters):
            count += 1
            w.writerow(make_csv_row(count, params))
            if progress_cb:
                progress_cb(count)
            if count % 200 == 0 and annullato():
                raise ExportAnnullato(count, 0)
        _check_cancelled(annullato, count)
    return count

# ─────────────────────────────────────────────────────────────────────────────
# GENERATORE DI COMBINAZIONI CON FILTRO
# ─────────────────────────────────────────────────────────────────────────────




# ─────────────────────────────────────────────────────────────────────────────
# CSV — versione parallela (multiprocessing)
#
# Il costo per riga è in make_csv_row -> compute_T_full (CPU-bound). I processi
# figli calcolano blocchi di righe; la scrittura su file resta ordinata nel
# processo principale. pool.map preserva l'ordine di sottomissione.
# ─────────────────────────────────────────────────────────────────────────────

def _csv_rows_chunk(task):
    """
    Worker top-level (picklable): calcola le righe CSV di un blocco.
    `task` = (start_index, blocco_di_params) — l'ordine dei due elementi
    è quello richiesto da parallel.run_export.
    """
    start_index, params_chunk = task
    return [make_csv_row(start_index + k, params)
            for k, params in enumerate(params_chunk)]


def _csv_chunk_worker(start_index, params_chunk):
    """Adattatore per run_export: (start, blocco) -> righe."""
    return _csv_rows_chunk((start_index, params_chunk))


def write_csv_parallel(path, filters, n_workers=None, progress_cb=None,
                       annullato=None):
    """
    Scrive il CSV calcolando le righe in parallelo su n_workers processi.
    La scrittura su disco resta sequenziale e ordinata.

    Le combinazioni NON vengono materializzate in una lista: `run_export`
    consuma il generatore a blocchi con una finestra limitata di task in volo.
    Con i filtri di default sarebbero 5.159.780.352 righe, e il vecchio
    `list(iter_combinations_ex(filters))` esauriva la RAM prima di scrivere
    un byte.

    Fallback automatico al sequenziale (write_csv) se: n_workers<=1, poche
    righe, o errore di multiprocessing.
    Solleva ExportTooLarge se il numero di righe supera il limite di sicurezza.
    """
    from .combinations import count_combinations_ex, iter_combinations_ex
    from .parallel import (COSTO_RIGA_CSV, ExportAnnullato, atomic_write,
                           check_export_size, mai_annullato, run_export,
                           _check_cancelled)
    if annullato is None:
        annullato = mai_annullato

    _check_cancelled(annullato)
    total = count_combinations_ex(filters)
    # Il controllo va fatto PRIMA di aprire il file: se l'export e' rifiutato
    # non deve restare in giro un CSV con la sola intestazione.
    check_export_size(total)

    with atomic_write(path, "w", annullato=annullato,
                      newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";", quotechar='"',
                       quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow(CSV_HEADER)

        state = {"written": 0, "fallback": False}

        def consume(rows, _n):
            for row in rows:
                w.writerow(row)
                state["written"] += 1

        def sequential():
            # Il file è già aperto con l'intestazione scritta: continuiamo qui
            # invece di riaprirlo, così il fallback non perde l'header.
            _check_cancelled(annullato, 0, total)
            state["fallback"] = True
            count = 0
            for params in iter_combinations_ex(filters):
                count += 1
                w.writerow(make_csv_row(count, params))
                if progress_cb and count % 500 == 0:
                    progress_cb(count)
                if count % 200 == 0 and annullato():
                    raise ExportAnnullato(count, total)
            _check_cancelled(annullato, count, total)
            return count

        n = run_export(total=total,
                       items_iter=iter_combinations_ex(filters),
                       sequential=sequential,
                       parallel_worker=_csv_chunk_worker,
                       consume=consume,
                       n_workers=n_workers, cost_per_item=COSTO_RIGA_CSV,
                       progress_cb=progress_cb, annullato=annullato,
                       what="Export CSV")

        if progress_cb:
            progress_cb(n)
        _check_cancelled(annullato, n, total)
    return n
