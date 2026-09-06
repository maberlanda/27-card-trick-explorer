"""
Test delle proprietà matematiche del motore di Gioco delle 27 carte.

Questi test verificano invarianti algebriche note (non dipendono dalla GUI):
struttura di MSC, di P/J, equivalenza dei due modelli di calcolo di T,
proprietà delle permutazioni e coerenza dei conteggi di combinazioni.

Esecuzione:
    pip install pytest numpy
    pytest -q
"""
import itertools
import random

import numpy as np
import pytest

from gioco27.core.constants import P_OPTS, J_OPTS, ANY, PERM3, _MSC_PERM
from gioco27.core.permutations import (
    MSC, perm_to_mat3, build_P27, build_J27,
    compute_stage, compute_R, compute_T_full,
    compose3, _compose3,
)
from gioco27.core.analysis import cycle_decomposition, order_of
from gioco27.core.combinations import (
    iter_combinations, count_combinations,
    iter_combinations_ex, count_combinations_ex,
)

I3 = np.eye(3)
I27 = np.eye(27)


def is_perm_matrix(M, n):
    """True se M è una matrice di permutazione n×n (0/1, una sola 1 per riga e colonna)."""
    M = np.asarray(M)
    if M.shape != (n, n):
        return False
    if not np.all((M == 0) | (M == 1)):
        return False
    return np.all(M.sum(axis=0) == 1) and np.all(M.sum(axis=1) == 1)


# ───────────────────────────── MSC ──────────────────────────────────────────

def test_msc_perm_is_bijection():
    assert sorted(_MSC_PERM) == list(range(27))


def test_msc_is_permutation_matrix():
    assert is_perm_matrix(MSC, 27)


def test_msc_matrix_matches_perm():
    # MSC[row, col] = 1  <=>  _MSC_PERM[col] = row
    expected = np.zeros((27, 27))
    for col, row in enumerate(_MSC_PERM):
        expected[row, col] = 1.0
    assert np.allclose(MSC, expected)


def test_msc_has_order_three():
    # Proprietà fondamentale del gioco: MSC^3 = I (vedi Guida, sez. 3)
    assert np.allclose(MSC @ MSC @ MSC, I27)
    assert not np.allclose(MSC @ MSC, I27)


# ──────────────────────── PERM3 / matrici 3×3 ───────────────────────────────

def test_perm_to_mat3_identity():
    assert np.allclose(perm_to_mat3(PERM3["SCD_U"]), I3)


@pytest.mark.parametrize("name", list(PERM3))
def test_perm_to_mat3_is_permutation_matrix(name):
    assert is_perm_matrix(perm_to_mat3(PERM3[name]), 3)


def test_perm_to_mat3_composition_is_matmul():
    # perm_to_mat3(a∘b) == mat(a) @ mat(b)
    for a, b in itertools.product(PERM3, repeat=2):
        A, B = PERM3[a], PERM3[b]
        comp = [A[B[i]] for i in range(3)]
        assert np.allclose(perm_to_mat3(comp), perm_to_mat3(A) @ perm_to_mat3(B))


@pytest.mark.parametrize("name", ["SDC_U", "CSD_U", "DCS_U"])
def test_perm3_involutions(name):
    # Queste tre permutazioni sono involuzioni: X∘X = identità.
    assert compose3(name, name) == "I_3"
    assert _compose3(name, name) == "SCD_U"


def test_cds_dsc_are_inverses():
    assert compose3("CDS_U", "DSC_U") == "I_3"
    assert compose3("DSC_U", "CDS_U") == "I_3"


# ──────────────────────── P27 / J27 (Kronecker) ─────────────────────────────

def test_build_P27_identity_is_I():
    assert np.allclose(build_P27("SCD_U", "SCD_U", "SCD_U"), I27)


def test_build_J27_identity_is_I():
    assert np.allclose(build_J27("I_3", "I_3", "I_3"), I27)


def test_build_P27_is_permutation_matrix():
    assert is_perm_matrix(build_P27("CDS_U", "SDC_U", "DCS_U"), 27)


def test_build_J27_full_reversal_is_involution():
    J = build_J27("R_U", "R_U", "R_U")
    assert is_perm_matrix(J, 27)
    assert np.allclose(J @ J, I27)


# ──────────────────────── Stage e modello di T ──────────────────────────────

def _random_params(rng):
    return [
        (rng.choice(P_OPTS), rng.choice(P_OPTS), rng.choice(P_OPTS),
         rng.choice(J_OPTS), rng.choice(J_OPTS), rng.choice(J_OPTS))
        for _ in range(3)
    ]


def test_compute_stage_returns_permutation_matrix():
    _, _, S = compute_stage("CDS_U", "SCD_U", "DSC_U", "I_3", "R_U", "I_3")
    assert is_perm_matrix(S, 27)


def test_two_models_of_T_agree():
    """
    Cross-check chiave: T calcolata col modello a stadi (Pᵢ∘MSC∘Jᵢ) deve
    coincidere con T calcolata col modello ridotto simbolico (Aᵢ∘MSC).
    Se i due percorsi divergono, c'è un bug in compute_Ai_symbolic o nelle matrici.
    """
    rng = random.Random(12345)
    for _ in range(50):
        params = _random_params(rng)
        stages = [compute_stage(*p) for p in params]
        T_stage = compute_R(stages)
        _, _, _, T_full = compute_T_full(params)
        assert np.allclose(T_stage, T_full)


def test_T_is_permutation_and_invertible():
    rng = random.Random(7)
    for _ in range(20):
        params = _random_params(rng)
        _, _, T_perm, T = compute_T_full(params)
        assert is_perm_matrix(T, 27)
        # Matrice di permutazione: ortogonale, quindi T ∘ T⁻¹ = I
        assert np.allclose(T @ T.T, I27)
        # La permutazione restituita è una bigezione di 0..26
        assert sorted(T_perm) == list(range(27))


def test_identity_params_give_identity_when_msc_cubed():
    # Con tutti i fattori identità: T = MSC^3 = I (tre stadi, ciascuno = MSC).
    params = [("SCD_U", "SCD_U", "SCD_U", "I_3", "I_3", "I_3")] * 3
    _, _, T_perm, T = compute_T_full(params)
    assert np.allclose(T, I27)
    assert T_perm == list(range(27))


# ──────────────────────── Permutazioni: cicli e ordine ──────────────────────

def test_cycle_decomposition_partitions_all_elements():
    rng = random.Random(99)
    params = _random_params(rng)
    _, _, T_perm, _ = compute_T_full(params)
    cycles = cycle_decomposition(T_perm)
    flat = [x for c in cycles for x in c]
    assert sorted(flat) == list(range(27))          # copre tutti gli elementi
    assert len(flat) == len(set(flat))              # cicli disgiunti


def test_order_of_identity_is_one():
    assert order_of(list(range(27))) == 1


def test_order_of_transposition_is_two():
    perm = list(range(27))
    perm[0], perm[1] = perm[1], perm[0]
    assert order_of(perm) == 2


def test_order_equals_lcm_of_cycle_lengths():
    from math import gcd
    rng = random.Random(2024)
    for _ in range(20):
        params = _random_params(rng)
        _, _, T_perm, _ = compute_T_full(params)
        lengths = [len(c) for c in cycle_decomposition(T_perm)]
        lcm = 1
        for l in lengths:
            lcm = lcm * l // gcd(lcm, l)
        assert order_of(T_perm) == lcm


# ──────────────────────── Conteggi delle combinazioni ───────────────────────

def test_count_combinations_matches_iteration():
    # Filtro piccolo: p1 libero (6) al primo stadio, tutto il resto fisso.
    fixed = {"p0": "SCD_U", "p1": "SCD_U", "p2": "SCD_U",
             "j0": "I_3", "j1": "I_3", "j2": "I_3"}
    f0 = dict(fixed, p0=ANY)
    filters = [f0, dict(fixed), dict(fixed)]
    assert count_combinations(filters) == 6
    assert sum(1 for _ in iter_combinations(filters)) == 6


def test_count_ex_matches_iteration():
    fixed = {"p0": "SCD_U", "p1": "SCD_U", "p2": "SCD_U",
             "j0": "I_3", "j1": "I_3", "j2": "I_3", "j_uniform": False}
    f0 = dict(fixed, p0=ANY, j0=ANY)          # 6 * 2 = 12 al primo stadio
    filters = [f0, dict(fixed), dict(fixed)]
    assert count_combinations_ex(filters) == 12
    assert sum(1 for _ in iter_combinations_ex(filters)) == 12


def test_real_game_has_1728_canonical_sequences():
    """
    Il «Gioco Reale» (Guida, sez. 10): P2=P3=identità, P1 libero (6 opzioni),
    J uniforme (2 opzioni) per ciascuno dei 3 stadi  ->  (6*2)^3 = 1728.
    """
    stage = {"p0": ANY, "p1": "SCD_U", "p2": "SCD_U",
             "j0": ANY, "j1": ANY, "j2": ANY, "j_uniform": True}
    filters = [dict(stage), dict(stage), dict(stage)]
    assert count_combinations_ex(filters) == 1728
    assert sum(1 for _ in iter_combinations_ex(filters)) == 1728


def test_j_uniform_only_yields_uniform_triples():
    stage = {"p0": "SCD_U", "p1": "SCD_U", "p2": "SCD_U",
             "j0": ANY, "j1": ANY, "j2": ANY, "j_uniform": True}
    filters = [dict(stage), dict(stage), dict(stage)]
    for combo in iter_combinations_ex(filters):
        for (_p1, _p2, _p3, j1, j2, j3) in combo:
            assert j1 == j2 == j3      # solo triple (v, v, v)


# ──────────────────── Parallelismo: parallelo == sequenziale ────────────────

def test_distribution_parallel_invariants():
    """La distribuzione (parallela) deve dare 216 T, ciascuno con 216² decomp."""
    from gioco27.core.analysis import compute_distribution_parallel
    d = compute_distribution_parallel(n_workers=2)
    assert d["total_T"] == 216
    assert d["total_decomp"] == 216 ** 3
    assert d["histogram"] == {216 * 216: 216}


def test_distribution_parallel_matches_sequential_small():
    """Su un sottoinsieme di indici, parziale parallelo == parziale sequenziale."""
    from gioco27.core.analysis import _distribution_partial
    a = _distribution_partial([0, 1, 2, 3])
    b = _distribution_partial([0, 1]) 
    c = _distribution_partial([2, 3])
    merged = dict(b)
    for k, v in c.items():
        merged[k] = merged.get(k, 0) + v
    assert a == merged


def test_csv_parallel_identical_to_sequential():
    import tempfile, os, filecmp
    from gioco27.core.permutations import write_csv, write_csv_parallel
    base = {"p0": "SCD_U", "p1": "SCD_U", "p2": "SCD_U",
            "j0": "I_3", "j1": "I_3", "j2": "I_3", "j_uniform": False}
    filters = [dict(base, p0=ANY), dict(base, p0=ANY),
               dict(base, j_uniform=True, j0=ANY)]   # 6*6*2 = 72 righe
    d = tempfile.mkdtemp()
    try:
        seq = os.path.join(d, "seq.csv")
        par = os.path.join(d, "par.csv")
        n1 = write_csv(seq, filters)
        n2 = write_csv_parallel(par, filters, n_workers=2)
        assert n1 == n2 == 72
        assert filecmp.cmp(seq, par, shallow=False)
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


def test_pdf_parallel_matches_sequential():
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    import tempfile, os, re, shutil
    from pypdf import PdfReader
    from gioco27.core.combinations import generate_pdf_ex, generate_pdf_ex_parallel
    base = {"p0": "SCD_U", "p1": "SCD_U", "p2": "SCD_U",
            "j0": "I_3", "j1": "I_3", "j2": "I_3", "j_uniform": False}
    filters = [dict(base, p0=ANY), dict(base, p0=ANY), dict(base, p0=ANY)]  # 6^3 = 216 (attiva il parallelo)
    d = tempfile.mkdtemp()
    try:
        seq = os.path.join(d, "seq.pdf")
        par = os.path.join(d, "par.pdf")
        n1 = generate_pdf_ex(seq, filters)
        n2 = generate_pdf_ex_parallel(par, filters, n_workers=2)
        assert n1 == n2
        rs, rp = PdfReader(seq), PdfReader(par)
        assert len(rs.pages) == len(rp.pages) == n1

        def doc_text(reader):
            joined = "".join((pg.extract_text() or "") for pg in reader.pages)
            return re.sub(r"\s+", "", joined)

        ts, tp = doc_text(rs), doc_text(rp)
        assert ts == tp
        labels = sorted(int(m) for m in re.findall(r"#(\d+)", ts))
        assert labels == list(range(1, n1 + 1))
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ──────────────────── Export PDF dettagliato (stile-C) ──────────────────────

def test_num_to_sector():
    from gioco27.core.detail import num_to_sector
    assert num_to_sector(0) == "sss"
    assert num_to_sector(13) == "ccc"
    assert num_to_sector(26) == "ddd"
    # coerenza con la decomposizione ternaria 9*a+3*b+c
    for n in range(27):
        a, b, c = n // 9, (n % 9) // 3, n % 3
        assert num_to_sector(n) == "".join("scd"[x] if False else {0:"s",1:"c",2:"d"}[x]
                                           for x in (a, b, c))


def test_detail_identity():
    from gioco27.core.detail import combination_detail, DECK
    idp = [("SCD_U", "SCD_U", "SCD_U", "I_3", "I_3", "I_3")] * 3
    d = combination_detail(idp)
    assert d["dispositions"][-1] == DECK       # identita': mazzo invariato
    assert d["period"] == 1
    assert d["involutive"] is True
    assert [p for _, _, p, _ in d["markers"]] == [0, 13, 26]


def test_detail_matches_engine():
    from gioco27.core.detail import combination_detail, DECK
    rng = random.Random(123)
    for _ in range(30):
        params = _random_params(rng)
        d = combination_detail(params)
        _, _, T_perm, _ = compute_T_full(params)
        assert d["T_perm"] == T_perm                       # stesso motore
        assert sorted(d["dispositions"][-1]) == sorted(DECK)
        # involutiva <=> permutazione == sua inversa
        assert d["involutive"] == (d["T_perm"] == d["inv_perm"])
        # periodo 2 implica involutiva
        if d["period"] == 2:
            assert d["involutive"] is True


def test_detail_pdf_parallel_matches_sequential():
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    import tempfile, os, re, shutil
    from pypdf import PdfReader
    from gioco27.core.detail_pdf import (generate_detail_pdf,
                                         generate_detail_pdf_parallel)
    base = {"p0": "SCD_U", "p1": "SCD_U", "p2": "SCD_U",
            "j0": "I_3", "j1": "I_3", "j2": "I_3", "j_uniform": False}
    filters = [dict(base, p0=ANY), dict(base, p0=ANY), dict(base, p0=ANY)]  # 216
    d = tempfile.mkdtemp()
    try:
        seq = os.path.join(d, "s.pdf"); par = os.path.join(d, "p.pdf")
        n1 = generate_detail_pdf(seq, filters)
        n2 = generate_detail_pdf_parallel(par, filters, n_workers=2)
        assert n1 == n2 == 216
        rs, rp = PdfReader(seq), PdfReader(par)
        # due combinazioni per pagina -> 108 pagine
        assert len(rs.pages) == len(rp.pages) == 108
        def doc(r):
            return re.sub(r"\s+", "", "".join((pg.extract_text() or "") for pg in r.pages))
        assert doc(rs) == doc(rp)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_detail_order_matches_c_numbering():
    """L'ordinamento stile-C riproduce la numerazione D# = ((i*6+j)*6+k)*8+m
    del programma C su tutte le 1728 sequenze del gioco reale (v3: preset
    con P3 libero; i, j, k sono indici della tabella M dei MESCOLAMENTI del
    C — SCD SDC CSD DSC CDS DCS — non della tabella W degli impilamenti)."""
    from gioco27.core.detail_pdf import order_like_c, _c_indices
    from gioco27.core.combinations import iter_combinations_ex
    M_IDX = {n + "_U": i for i, n in enumerate(
        ("SCD", "SDC", "CSD", "DSC", "CDS", "DCS"))}
    stage = {"p0": "SCD_U", "p1": "SCD_U", "p2": ANY,
             "j0": ANY, "j1": ANY, "j2": ANY, "j_uniform": True}
    combos = order_like_c(list(iter_combinations_ex([dict(stage)] * 3)))
    assert len(combos) == 1728
    for n, (s1, s2, s3) in enumerate(combos):
        i, j, k = M_IDX[s3[2]], M_IDX[s2[2]], M_IDX[s1[2]]
        r0 = 1 if s1[3] == "R_U" else 0
        r1 = 1 if s2[3] == "R_U" else 0
        r2 = 1 if s3[3] == "R_U" else 0
        m = (r0 << 2) | (r1 << 1) | r2
        assert ((i * 6 + j) * 6 + k) * 8 + m == n
        # l'etichetta P[i][j][k][m] usata nel PDF coincide con gli indici C
        assert _c_indices((s1, s2, s3)) == (i, j, k, m)


def test_detail_annotations():
    """Etichette stile C ed elenco trasposte: la trasposta di una matrice di
    permutazione e' l'inversa, quindi ogni matrice deve comparire nell'elenco
    trasposte della propria inversa (insieme di gioco chiuso per inversione)."""
    from gioco27.core.detail_pdf import (order_like_c, annotate_like_c,
                                         _perm_of)
    from gioco27.core.detail import combination_detail
    from gioco27.core.combinations import iter_combinations_ex
    stage = {"p0": "SCD_U", "p1": "SCD_U", "p2": ANY,
             "j0": "I_3", "j1": "I_3", "j2": "I_3", "j_uniform": True}
    combos = order_like_c(list(iter_combinations_ex([dict(stage)] * 3)))
    assert len(combos) == 216
    labels, transposes = annotate_like_c(combos)
    # _perm_of coincide con combination_detail
    for prm in combos[:12]:
        assert tuple(combination_detail(prm)["T_perm"]) == _perm_of(prm)
    # ogni combinazione ha almeno una trasposta nell'insieme (chiusura)
    assert all(len(t) >= 1 for t in transposes)
    # una matrice autoinversa (identita': D#0) elenca se stessa
    assert labels[0] in transposes[0]


def test_compile_perm3_pat():
    """Regressione v2.8.0→v2.8.1: _PERM3_PAT deve essere definito nel modulo
    permutations (cache del pattern), non importato da constants."""
    from gioco27.core.permutations import _compile_perm3_pat
    pat = _compile_perm3_pat()
    assert pat.search("SCD_U o MSC o CDS_U")
    assert pat is _compile_perm3_pat()   # cache: stesso oggetto


# ─── Regressioni v2.8.2: parser / normalizzazione Explorer ───────────────────

def test_normalize_con_identita_frapposta():
    """Bug v2.8.1: «K1 ∘ MSC ∘ I ∘ K2» non veniva normalizzata del tutto e
    la forma algebrica/canonica riportava fattori Kronecker ERRATI
    (K1∘K2 fusi ignorando l'MSC in mezzo)."""
    from gioco27.core.algebra import Controller
    ctrl = Controller()
    s = "(DSC_U ⊗ SCD_U ⊗ DCS_U) ∘ MSC ∘ I ∘ (DCS_U ⊗ DSC_U ⊗ DSC_U)"
    r = ctrl.process(s)
    assert r["ok"]
    # la forma normalizzata deve essere completa: un solo kron + MSC
    r2 = ctrl.process(r["normalized_str"])
    assert r2["perm"] == r["perm"]
    assert r["normalized_str"].count("⊗") == 2, \
        f"normalizzazione incompleta: {r['normalized_str']}"
    # la forma canonica, se dichiarata disponibile, DEVE essere coerente
    cf = r.get("canonical_form")
    assert r.get("canonical_available") and cf is not None
    assert cf.to_perm() == r["perm"]


def test_analyze_normal_form_non_fonde_kron_attraverso_msc():
    """La NormalFormInfo non deve mai dichiarare una forma K∘MSC^k con
    fattori che non rivalutano alla permutazione originale."""
    from gioco27.core.algebra import Controller
    ctrl = Controller()
    import random
    random.seed(123)
    names = ["SCD_U", "SDC_U", "CSD_U", "CDS_U", "DSC_U", "DCS_U"]
    for _ in range(50):
        parts = []
        for _ in range(3):
            t = [random.choice(names) for _ in range(3)]
            parts.append(f"({t[0]} x {t[1]} x {t[2]})")
            parts.append(random.choice(["MSC", "I", "MSC o I"]))
        r = ctrl.process(" o ".join(parts))
        assert r["ok"]
        cf = r.get("canonical_form")
        if r.get("canonical_available") and cf is not None:
            assert cf.to_perm() == r["perm"]


def test_parser_catene_lunghe_no_recursionerror():
    """Bug v2.8.1: il parse binario annidato a sinistra causava
    RecursionError oltre ~190 termini. Col nodo compose n-ario non più."""
    from gioco27.core.algebra import Controller
    ctrl = Controller()
    r = ctrl.process(" o ".join(["MSC"] * 3000))
    assert r["ok"] and r["perm"] == list(range(27))   # 3000 ≡ 0 (mod 3)


# ─── Regressioni v2.8.3: notazione di gioco nell'Explorer ────────────────────

def test_parser_accetta_fattori_J_di_gioco():
    """R_U e I_3 (fattori J della notazione Stage) devono essere accettati
    come atomi di tipo 3, equivalenti a DCS_U e SCD_U."""
    import itertools
    from gioco27.core.algebra import Controller
    from gioco27.core.permutations import compute_stage, mat_to_perm27
    from gioco27.core.constants import P_OPTS, J_OPTS
    ctrl = Controller()
    # campione: tutte le 64 combinazioni J con P fissi + 20 P casuali
    import random
    random.seed(8)
    casi = [("SCD_U", "SCD_U", "DCS_U") + js
            for js in itertools.product(J_OPTS, repeat=3)]
    casi += [tuple(random.choice(P_OPTS) for _ in range(3)) +
             tuple(random.choice(J_OPTS) for _ in range(3)) for _ in range(20)]
    for (p1, p2, p3, j1, j2, j3) in casi:
        s = f"({p3} x {p2} x {p1}) o MSC o ({j3} x {j2} x {j1})"
        r = ctrl.process(s)
        assert r["ok"], (s, r.get("error"))
        _, _, S = compute_stage(p1, p2, p3, j1, j2, j3)
        assert r["perm"] == mat_to_perm27(S), s


def test_parser_accetta_stage_string_completa():
    """Le Stage string dell'Analisi (parentesi quadre, prefisso «T = »)
    devono essere incollabili nell'Explorer tal quali."""
    from gioco27.core.algebra import Controller
    ctrl = Controller()
    stage = ("T = [(DCS_U x SCD_U x SCD_U) o MSC o (R_U x I_3 x R_U)] o "
             "[(DCS_U x DCS_U x DCS_U) o MSC o (I_3 x I_3 x I_3)] o "
             "[(DCS_U x SCD_U x SCD_U) o MSC o (R_U x R_U x I_3)]")
    r = ctrl.process(stage)
    assert r["ok"], r.get("error")
    assert sorted(r["perm"]) == list(range(27))
    # senza prefisso e con sole tonde deve dare la stessa permutazione
    plain = stage[4:].replace("[", "(").replace("]", ")")
    r2 = ctrl.process(plain)
    assert r2["ok"] and r2["perm"] == r["perm"]


def test_tre_turni_di_gioco_equivalenti_a_compute_T_full():
    """Espressione a 3 turni in notazione di gioco == compute_T_full."""
    import random
    from gioco27.core.algebra import Controller
    from gioco27.core.permutations import compute_T_full
    from gioco27.core.constants import P_OPTS, J_OPTS
    ctrl = Controller()
    random.seed(21)
    for _ in range(20):
        params = [tuple(random.choice(P_OPTS) for _ in range(3)) +
                  tuple(random.choice(J_OPTS) for _ in range(3))
                  for _ in range(3)]
        sparts = [f"({p3} x {p2} x {p1}) o MSC o ({j3} x {j2} x {j1})"
                  for (p1, p2, p3, j1, j2, j3) in reversed(params)]
        r = ctrl.process(" o ".join(sparts))
        _, _, T_perm, _ = compute_T_full(params)
        assert r["ok"] and r["perm"] == T_perm


def test_stage_string_analisi_explorer_stessa_perm():
    """Regressione v2.8.4: l'Analisi invia all'Explorer la Stage string
    completa (P o MSC o J, con R_U/I_3); deve dare la stessa permutazione
    della riga di provenienza."""
    from gioco27.core.constants import ANY
    from gioco27.core.combinations import iter_combinations_ex
    from gioco27.core.permutations import make_csv_row
    from gioco27.core.algebra import analizza_righe, _prep_explorer_expr, Controller
    filt = [{"p0": "SCD_U", "p1": "SCD_U", "p2": ANY,
             "j0": ANY, "j1": ANY, "j2": ANY, "j_uniform": True}
            for _ in range(3)]
    righe = []
    for i, params in enumerate(iter_combinations_ex(filt), 1):
        rd = make_csv_row(i, params)
        righe.append({"Stage1": rd[1], "Stage2": rd[2], "Stage3": rd[3],
                      "A1": rd[4], "A2": rd[5], "A3": rd[6],
                      "T_simbolica": rd[7], "T_permutazione": rd[8]})
    ctrl = Controller()
    for r in analizza_righe(righe):
        attesa = [int(x) for x in r["perm_str"].strip("[]").split(",")]
        for ts in r["simboliche"]:
            res = ctrl.process(_prep_explorer_expr(ts))
            assert res["ok"] and res["perm"] == attesa, ts


def _ensure_tkinter_stub():
    """Su macchine senza tkinter (CI/sandbox) installa o completa uno stub
    minimale sufficiente a importare i moduli GUI nei test headless."""
    import sys, types
    import importlib.util
    try:
        if importlib.util.find_spec("tkinter") is not None:
            return          # tkinter reale disponibile
    except ValueError:
        pass                # stub parziale gia' in sys.modules: completalo

    class _W:
        def __init__(self, *a, **k): pass

    tk_stub  = sys.modules.get("tkinter")     or types.ModuleType("tkinter")
    ttk_stub = sys.modules.get("tkinter.ttk") or types.ModuleType("tkinter.ttk")
    for n in ("Frame", "Label", "Button", "Scale", "Checkbutton",
              "LabelFrame", "Scrollbar", "Canvas", "Spinbox",
              "Radiobutton", "Separator", "Style"):
        if not hasattr(ttk_stub, n):
            setattr(ttk_stub, n, _W)
    for n in ("Toplevel", "Frame", "Label", "Canvas", "Text", "StringVar",
              "IntVar", "BooleanVar", "DoubleVar", "Menu", "Menubutton",
              "Widget"):
        if not hasattr(tk_stub, n):
            setattr(tk_stub, n, _W)
    if not hasattr(tk_stub, "TclError"):
        tk_stub.TclError = Exception
    tk_stub.ttk = ttk_stub
    mb = sys.modules.get("tkinter.messagebox") \
         or types.ModuleType("tkinter.messagebox")
    if not hasattr(mb, "showerror"):
        mb.showerror = lambda *a, **k: None
        mb.showinfo  = lambda *a, **k: None
    tk_stub.messagebox = mb
    fd = sys.modules.get("tkinter.filedialog") \
         or types.ModuleType("tkinter.filedialog")
    if not hasattr(fd, "asksaveasfilename"):
        fd.asksaveasfilename = lambda *a, **k: ""
        fd.askopenfilename   = lambda *a, **k: ""
    tk_stub.filedialog = fd
    for extra in ("Combobox", "Treeview", "LabelFrame", "PanedWindow",
                  "Notebook", "Progressbar", "Entry"):
        if not hasattr(ttk_stub, extra):
            setattr(ttk_stub, extra, _W)
    sys.modules["tkinter"] = tk_stub
    sys.modules["tkinter.ttk"] = ttk_stub
    sys.modules["tkinter.messagebox"] = mb
    sys.modules["tkinter.filedialog"] = fd


def test_mescolamento_accetta_notazione_di_gioco():
    """Regressione v2.8.6: il tab Mescolamento deve accettare la formula
    in notazione di gioco che l'Explorer riceve dall'Analisi (quadre,
    R_U/I_3, blocco J dopo MSC) e simulare la stessa permutazione."""
    import numpy as np
    _ensure_tkinter_stub()

    from gioco27.gui.shuffle import ShuffleViewerFrame
    from gioco27.core.algebra import Controller

    sv = object.__new__(ShuffleViewerFrame)
    ctrl = Controller()
    formule = [
        # notazione di gioco completa (caso segnalato)
        "[(SCD_U x SCD_U x DCS_U) o MSC o (I_3 x I_3 x I_3)] o "
        "[(SCD_U x SCD_U x CDS_U) o MSC o (I_3 x I_3 x I_3)] o "
        "[(SCD_U x SCD_U x CDS_U) o MSC o (R_U x R_U x R_U)]",
        # vecchia forma A-level
        "(SCD_U x DCS_U x SDC_U) o MSC o (CDS_U x CSD_U x DCS_U) o MSC",
        # varianti
        "T = [(SCD_U x SCD_U x DCS_U) o MSC o (R_U x R_U x R_U)]",
        "((SCD_U ⊗ SCD_U ⊗ DCS_U) ∘ MSC) ∘ (R_U ⊗ R_U ⊗ R_U)",
        "MSC o MSC o MSC",
    ]
    for f in formule:
        tokens = sv._validate_and_parse(f)
        sv._build_steps(tokens)
        final_deck = list(sv._steps[-1]["deck"])
        r = ctrl.process(f)
        assert r["ok"], (f, r.get("error"))
        # la carta i finisce in posizione T[i] → mazzo finale = argsort(T)
        assert final_deck == list(np.argsort(r["perm"])), f


def test_protocollo_html_didattico():
    """Regressione v2.8.7: il protocollo HTML contiene tutte le sezioni,
    la verifica pratica riproduce T o T⁻¹, e viene preferita una
    decomposizione a raccolta semplice se esiste."""
    _ensure_tkinter_stub()

    from gioco27.core.algebra import Controller
    from gioco27.core.kronecker import find_all_kron_decompositions
    from gioco27.gui.protocol_dialog import generate_protocol_html, _protocol_perm

    ctrl = Controller()
    r = ctrl.process("(SCD_U x SCD_U x CDS_U) o MSC o "
                     "(DCS_U x SCD_U x SCD_U) o MSC o "
                     "(SCD_U x DCS_U x SCD_U) o MSC")
    assert r["ok"]
    decs = find_all_kron_decompositions(r["inverse_perm"])
    T_data = {"perm": r["perm"], "inverse_perm": r["inverse_perm"],
              "label": "T di prova", "period": r["period"],
              "decompositions": decs, "canonical_sym": None}
    html = generate_protocol_html(T_data)
    for sec in ["1 · Il trucco in sintesi", "2 · Legenda", "3 · Le tre fasi",
                "4 · Verifica pratica", "5 · Struttura ciclica",
                "6 · Tabelle", "7 · Matrice", "8 · Perché funziona", "<svg"]:
        assert sec in html, sec
    # ogni decomposizione, eseguita come protocollo, dà T o T⁻¹
    assert _protocol_perm(decs[0]) in (r["perm"], r["inverse_perm"])
    # le opzioni disattivano le sezioni
    html2 = generate_protocol_html(T_data, {"matrice": False, "cicli": False})
    assert "7 · Matrice" not in html2 and "5 · Struttura ciclica" not in html2


# ─── Regressioni v2.8.8: Coniugio/Cayley didattici e Reset tutto ─────────────

def test_tipo_classi_coniugio_s3():
    """_class_type: per ognuna delle 27 classi il tipo S3³ è unico, condiviso
    da tutti gli elementi, e la dimensione è il prodotto delle classi S₃."""
    _ensure_tkinter_stub()
    from gioco27.gui.conjugacy_dialog import _class_type
    from gioco27.core.group_theory import get_group_data
    gd = get_group_data()
    tipi = set()
    for c in gd.classes:
        tipo, size = _class_type(gd.kron_names[c[0]])
        assert size == len(c)
        assert all(_class_type(gd.kron_names[e])[0] == tipo for e in c)
        tipi.add(tipo)
    assert len(tipi) == 27


def test_reset_api_presente():
    """Regressione v2.8.8: ogni tab espone il metodo di reset usato da
    App._reset."""
    _ensure_tkinter_stub()
    from gioco27.gui.cycles_tab import CyclesFrame
    from gioco27.gui.simulator_tab import SimulatorFrame
    from gioco27.gui.shuffle import ShuffleViewerFrame
    from gioco27.gui.analysis_tab import AnalysisTabMixin
    from gioco27.gui.preview_tab import PreviewTabMixin
    from gioco27.gui.explorer_tab import ExplorerTabMixin
    assert callable(getattr(CyclesFrame, "reset"))
    assert callable(getattr(SimulatorFrame, "reset"))
    assert callable(getattr(ShuffleViewerFrame, "clear_all"))
    assert callable(getattr(AnalysisTabMixin, "_reset_analisi"))
    assert callable(getattr(PreviewTabMixin, "_reset_anteprima"))
    assert callable(getattr(ExplorerTabMixin, "_explorer_clear"))
