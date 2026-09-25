"""Compartimento I5 — caratterizzazione di decodifica e riconoscimento.

Solo oracoli indipendenti dal service I5: la Def. 4.1 riscritta qui, aritmetica
esatta e i numeri delle fonti (letti in LIBRO_MAIN.pdf e Articolo.pdf):

* Articolo / App. D, Def. 4.1 e Teor. 4.2; Teor. 5.1 / 6.1 (somme di fibra);
  App. D Teor. 6.4 (criterio per una permutazione arbitraria); Es. 6.1 / 7.1;
* § 1.10 Prop. 1.7 (36, 117, 198); § 2.4.8 (lettura del vettore finale);
* § 7.1.1 A1 (finale = P · iniziale; #100); § 7.1.8 A8 (T_B T_A⁻¹);
* § 7.1.13 A13 e I3 (traslazioni); § 10.2.1 / 10.2.2 (due carte guida).
"""
import itertools
import random
from fractions import Fraction

import pytest

from gioco27.core import gioco_reale as gr
from gioco27.core.algebra import AlgebraEngine, CanonicalForm
from gioco27.services import tabellone as tb

N = 27


def cifra(x, i):
    return (x // 3 ** i) % 3


def separabile_oracolo(p):
    """Def. 4.1: d_i(p(x)) dipende solo da d_i(x), per ogni livello."""
    for i in range(3):
        visto = {}
        for x in range(N):
            if visto.setdefault(cifra(x, i), cifra(p[x], i)) != cifra(p[x], i):
                return False
    return True


def somme(p):
    return [[sum(p[x] for x in range(N) if cifra(x, i) == t) for t in range(3)]
            for i in range(3)]


C = [108, 90, 36]


def candidati(p):
    return [[Fraction(s - C[i], 3 ** (2 + i)) for s in riga]
            for i, riga in enumerate(somme(p))]


def inversa(p):
    q = [0] * N
    for x, y in enumerate(p):
        q[y] = x
    return q


TAVOLA = [tuple(gr.riga_tavola(n)["T"]) for n in range(216)]


# ═════════════════════════ costanti e somme delle fonti ═════════════════════

def test_costanti_c_i_dalla_formula():
    b, m = 3, 3
    for i in range(3):
        c = Fraction(b ** (m - 2) * b * (b - 1), 2) * sum(b ** j for j in range(m) if j != i)
        assert c == C[i]


def test_tabella_dei_valori_app_d_7():
    assert [[C[i] + 3 ** (2 + i) * r for r in range(3)] for i in range(3)] == [
        [108, 117, 126], [90, 117, 144], [36, 117, 198]]


def test_prop_1_7_somme_dei_blocchi():
    assert [sum(range(9 * j, 9 * j + 9)) for j in range(3)] == [36, 117, 198]
    assert somme(list(range(N)))[2] == [36, 117, 198]      # fibre del livello 2


def test_esempio_7_1_app_d_e_6_1_articolo():
    r0, r1, r2 = (1, 2, 0), (2, 1, 0), (1, 0, 2)          # (0 1 2), (0 2), (0 1)
    p = [9 * r2[x // 9] + 3 * r1[(x // 3) % 3] + r0[x % 3] for x in range(N)]
    s = somme(p)
    assert s[0] == [117, 126, 108]                         # riga 0 della fonte
    assert s == [[117, 126, 108], [144, 117, 90], [117, 36, 198]]
    assert candidati(p) == [list(r0), list(r1), list(r2)]


# ═════════════════ Teor. 4.2 e Teor. 6.4 sul caso b = m = 3 ═════════════════

def test_la_tavola_e_la_classe_separabile():
    assert len(set(TAVOLA)) == 216
    assert all(separabile_oracolo(p) for p in TAVOLA)


def test_i_fattori_della_tavola_sono_le_sigle():
    for n, p in enumerate(TAVOLA):
        attesi = [list(gr.MESCOLAMENTO[s]) for s in gr.mescolamenti_da_numero(n)]
        assert [[int(v) for v in c] for c in candidati(p)] == attesi


def test_indietro_da_gli_inversi_in_152_righe_diversi():
    diverse = 0
    for p in TAVOLA:
        avanti, indietro = candidati(p), candidati(inversa(p))
        for a, b in zip(avanti, indietro):
            assert [a.index(t) for t in range(3)] == [int(v) for v in b]
        diverse += avanti != indietro
    assert diverse == 152 == 216 - 4 ** 3


# ════════════════════════ classe estesa (core: K ∘ MSC^k) ═══════════════════

def _classe_estesa_dal_core():
    elementi = {}
    for n in range(216):
        fattori = [list(gr.MESCOLAMENTO[s]) for s in gr.mescolamenti_da_numero(n)]
        for k in range(3):
            # CanonicalForm vuole (P1, P2, P3) = fattori dal livello 2 al livello 0
            cf = CanonicalForm(kron_factors=[fattori[2], fattori[1], fattori[0]], msc_exp=k)
            elementi[tuple(cf.to_perm())] = (n, k)
    return elementi


def test_la_classe_estesa_ha_648_elementi_e_216_separabili():
    el = _classe_estesa_dal_core()
    assert len(el) == 648
    assert sum(separabile_oracolo(p) for p in el) == 216
    assert all((k == 0) == separabile_oracolo(p) for p, (_, k) in el.items())


def test_orientazione_di_msc_nel_core():
    msc = AlgebraEngine.MSC_PERM
    assert msc == [9 * (x % 3) + 3 * (x // 9) + (x // 3) % 3 for x in range(N)]
    comp = AlgebraEngine.compose
    for p, (n, k) in _classe_estesa_dal_core().items():
        mk = list(range(N))
        for _ in range(k):
            mk = comp(msc, mk)
        inv_mk = inversa(mk)
        assert tuple(comp(list(p), inv_mk)) == TAVOLA[n]   # K = π ∘ MSC^{-k}


# ═══════════════ Teor. 6.4: accordo con l'oracolo diretto ═══════════════════

def _criterio(p):
    return all(sorted(c) == [0, 1, 2] for c in candidati(p))


def test_criterio_e_oracolo_concordano_sulla_classe_estesa():
    assert all(_criterio(p) == separabile_oracolo(p) for p in _classe_estesa_dal_core())


def test_criterio_e_oracolo_concordano_su_s27_campione():
    rnd = random.Random(2026)
    for _ in range(3000):
        p = list(range(N))
        rnd.shuffle(p)
        assert _criterio(p) == separabile_oracolo(p)


def test_negativo_somme_equilibrate():
    """PRE-I5: candidati interi (1,1,1) su ogni livello, non permutazioni."""
    p = [20, 4, 17, 23, 8, 3, 16, 0, 26, 5, 12, 13, 11, 25, 14, 6, 21, 10,
         15, 22, 9, 2, 7, 24, 19, 18, 1]
    assert sorted(p) == list(range(N))
    assert candidati(p) == [[1, 1, 1]] * 3
    assert not separabile_oracolo(p) and not _criterio(p)


# ═════════════════════════════ traslazioni C_k ══════════════════════════════

def test_traslazioni():
    dentro = [k for k in range(27) if separabile_oracolo([(x + k) % N for x in range(N)])]
    assert dentro == [0, 9, 18]
    assert tb.numero_di([(x + 9) % N for x in range(N)]) == 144
    assert tb.numero_di([(x + 18) % N for x in range(N)]) == 108
    estesa = _classe_estesa_dal_core()
    fuori = [k for k in range(1, 27) if tuple((x + k) % N for x in range(N)) not in estesa]
    assert len(fuori) == 24 and 9 not in fuori and 18 not in fuori
    c1 = candidati([(x + 1) % N for x in range(N)])
    assert c1 == [[1, 2, 0], [Fraction(1, 3), Fraction(4, 3), Fraction(4, 3)],
                  [Fraction(1, 9), Fraction(10, 9), Fraction(16, 9)]]


# ════════════════════════ § 2.4.8: il vettore finale ════════════════════════

V_FINALE = [22, 23, 21, 19, 20, 18, 25, 26, 24, 13, 14, 12, 10, 11, 9, 16, 17, 15,
            4, 5, 3, 1, 2, 0, 7, 8, 6]


def test_2_4_8_si_legge_il_tabellone_inverso():
    """Il vettore finale e' il mazzo finale, cioe' T⁻¹ (T[carta] = posizione)."""
    assert [sum(V_FINALE[9 * j:9 * j + 9]) for j in range(3)] == [198, 117, 36]
    T = inversa(V_FINALE)
    assert tb.numero_di(T) == 195
    # righe del tabellone inverso lette dal libro: (D,C,S), (C,S,D), (C,D,S)
    indietro = candidati(V_FINALE)              # somme sul mazzo finale
    assert indietro == [[1, 2, 0], [1, 0, 2], [2, 1, 0]]
    # = impilamenti della riga 195 (il libro li chiama «mescolamenti»)
    assert [gr.MESCOLAMENTO[gr.IMPILAMENTO_DI[s]]
            for s in gr.mescolamenti_da_numero(195)] == [(1, 2, 0), (1, 0, 2), (2, 1, 0)]
    # leggere il mazzo finale come se fosse T da' un'altra riga: la trappola
    assert tb.numero_di(V_FINALE) == 196


# ══════════════════════════ § 7.1.1 A1, § 7.1.8 A8 ══════════════════════════

def test_a1_esempio_100():
    """T = (M2, M1, M0) = (CSD, CDS, CDS); finale = P · iniziale."""
    assert gr.mescolamenti_da_numero(100) == ("CDS", "CDS", "CSD")
    iniziale = list(range(N))
    finale, _ = gr.esegui_partita(gr.mescolamenti_da_numero(100))
    T = gr.riga_tavola(100)["T"]
    assert all(finale[T[i]] == iniziale[i] for i in range(N))


def test_a8_mazzi_gemelli():
    rnd = random.Random(8)
    for _ in range(200):
        a, b = rnd.randrange(216), rnd.randrange(216)
        mazzo_a, _ = gr.esegui_partita(gr.mescolamenti_da_numero(a))
        mazzo_b, _ = gr.esegui_partita(gr.mescolamenti_da_numero(b))
        ta, tb_ = gr.riga_tavola(a)["T"], gr.riga_tavola(b)["T"]
        rel = [mazzo_b.index(mazzo_a[p]) for p in range(N)]
        assert rel == [tb_[inversa(ta)[p]] for p in range(N)]       # T_B T_A⁻¹
        assert separabile_oracolo(rel)


# ════════════════════════ § 10.2.1 due carte guida ══════════════════════════

def test_10_2_1_esempio_del_libro():
    q0, q2 = 2, 22
    u, v = gr.digits3(q0), gr.digits3(q2)                  # (n2, n1, n0)
    assert u == (0, 0, 2) and v == (2, 1, 1)
    righe = []
    for h in range(3):
        tau = [None] * 3
        tau[u[h]], tau[v[h]] = 0, 2
        tau[tau.index(None)] = 1
        righe.append(tuple(tau))
    assert righe == [(0, 1, 2), (0, 2, 1), (1, 2, 0)]    # τ2 SCD, τ1 SDC, τ0 CDS
    R = [9 * righe[0][x // 9] + 3 * righe[1][(x // 3) % 3] + righe[2][x % 3]
         for x in range(N)]
    assert R[:3] == [1, 2, 0]
    assert 39 - q0 - q2 == 15                              # la terza guida


def test_10_2_1_il_ritorno_e_l_inverso_del_cumulativo():
    for n in range(216):
        T = gr.riga_tavola(n)["T"]
        u, v = gr.digits3(T[0]), gr.digits3(T[26])
        assert all(a != b for a, b in zip(u, v))
        righe = []
        for h in range(3):
            tau = [None] * 3
            tau[u[h]], tau[v[h]] = 0, 2
            tau[tau.index(None)] = 1
            righe.append(tau)
        R = [9 * righe[0][x // 9] + 3 * righe[1][(x // 3) % 3] + righe[2][x % 3]
             for x in range(N)]
        assert R == inversa(T)
        assert T[0] + T[13] + T[26] == 39


def test_10_2_2_guide_con_cifre_uguali_escludono():
    """Se in una riga le cifre coincidono, nessun tabellone porta v in w."""
    casi = 0
    for q0, q2 in itertools.permutations(range(N), 2):
        u, v = gr.digits3(q0), gr.digits3(q2)
        if any(a == b for a, b in zip(u, v)):
            casi += 1
    assert casi == 27 * 26 - 27 * 8                       # 8 posizioni compatibili per q0
