"""Compartimento I6 — caratterizzazione del laboratorio (oracoli e fonte).

Le tabelle sono trascritte da LIBRO_MAIN.pdf e verificate con oracoli scritti
qui, senza il service I6:

* § 6.7 e fig. 6.8: le 27 classi di coniugio di H (#, card, ord, tipo);
* App. B.9: i 7 tipi ciclici con le loro molteplicita' e i punti fissi;
* § 6.9 centro banale; § 6.10 J = DCS ⊗ DCS ⊗ DCS;
* § 8.2 tavola locale 6×6 (riga P, colonna Q, cella P ∘ Q: prima Q);
* § 8.5 decomposizioni locali (sei per ogni risultato);
* § 11.7.6 classi laterali H ∘ R^r percorse dagli stadi; Prop. 9.58 (8:1);
* A4 (limite di Kronecker), A5, A6, A10, § 10.2.1 (somma delle guide).

Notazione DP2: H = 216 (separabili), Γ = 648 (estesa), S27 ambiente.
"""
from collections import Counter
from itertools import product

from gioco27.core import gioco_reale as gr
from gioco27.core.algebra import AlgebraEngine
from gioco27.services.procedure import ProceduraGioco, servizio_procedure

N = 27
ID = tuple(range(N))
ORDINE_LIBRO = ("SCD", "SDC", "CSD", "CDS", "DSC", "DCS")      # § 8.2, § 8.5


def comp(a, b):
    return tuple(a[b[x]] for x in range(N))


def inv(p):
    q = [0] * len(p)
    for i, v in enumerate(p):
        q[v] = i
    return tuple(q)


def ordine(p):
    q, k = p, 1
    while q != tuple(range(len(p))):
        q, k = tuple(p[x] for x in q), k + 1
    return k


def tipo_ciclico(p):
    visti, c = set(), Counter()
    for i in range(len(p)):
        if i not in visti:
            j, l = i, 0
            while j not in visti:
                visti.add(j)
                j, l = p[j], l + 1
            c[l] += 1
    return tuple(sorted(c.items()))


def kron(s2, s1, s0):
    return tuple(9 * s2[x // 9] + 3 * s1[(x // 3) % 3] + s0[x % 3] for x in range(N))


LOC = {s: gr.MESCOLAMENTO[s] for s in ORDINE_LIBRO}
H = [kron(LOC[a], LOC[b], LOC[c]) for a, b, c in product(ORDINE_LIBRO, repeat=3)]
MSC = tuple(AlgebraEngine.MSC_PERM)
GAMMA = H + [comp(h, MSC) for h in H] + [comp(h, comp(MSC, MSC)) for h in H]


def tipo_locale(s):
    return {1: "I", 2: "T", 3: "C"}[ordine(LOC[s])]


# ════════════════════════ § 6.7: le 27 classi ═══════════════════════════════

CLASSI_LIBRO = [   # (#, card, ord, (f2, f1, f0))
    (1, 1, 1, "III"), (2, 2, 3, "IIC"), (3, 2, 3, "ICI"), (4, 2, 3, "CII"),
    (5, 3, 2, "IIT"), (6, 3, 2, "ITI"), (7, 3, 2, "TII"), (8, 4, 3, "ICC"),
    (9, 4, 3, "CIC"), (10, 4, 3, "CCI"), (11, 6, 6, "ITC"), (12, 6, 6, "ICT"),
    (13, 6, 6, "TIC"), (14, 6, 6, "TCI"), (15, 6, 6, "CIT"), (16, 6, 6, "CTI"),
    (17, 8, 3, "CCC"), (18, 9, 2, "ITT"), (19, 9, 2, "TIT"), (20, 9, 2, "TTI"),
    (21, 12, 6, "TCC"), (22, 12, 6, "CTC"), (23, 12, 6, "CCT"), (24, 18, 6, "TTC"),
    (25, 18, 6, "TCT"), (26, 18, 6, "CTT"), (27, 27, 2, "TTT"),
]


def test_27_classi_come_nel_libro():
    classi = {}
    for a, b, c in product(ORDINE_LIBRO, repeat=3):
        t = tipo_locale(a) + tipo_locale(b) + tipo_locale(c)
        classi.setdefault(t, []).append(kron(LOC[a], LOC[b], LOC[c]))
    assert len(classi) == 27
    for num, card, ordn, t in CLASSI_LIBRO:
        assert len(classi[t]) == card, (num, t)
        assert {ordine(p) for p in classi[t]} == {ordn}, (num, t)
    # equazione delle classi (fig. 6.8)
    assert sum(card for _, card, _, _ in CLASSI_LIBRO) == 216


def test_le_classi_per_tipo_sono_classi_di_coniugio():
    """Oracolo: coniugio esaustivo in H (216 × 216)."""
    hs = set(H)
    classi = []
    visti = set()
    for x in H:
        if x in visti:
            continue
        cl = {comp(comp(g, x), inv(g)) for g in H}
        assert cl <= hs
        visti |= cl
        classi.append(cl)
    assert sorted(len(c) for c in classi) == sorted(card for _, card, _, _ in CLASSI_LIBRO)


# ═══════════════════ App. B.9: 7 tipi ciclici, punti fissi ══════════════════

TIPI_LIBRO = {          # tipo ciclico: numero di trasformazioni
    ((1, 27),): 1, ((1, 9), (2, 9)): 9, ((1, 3), (2, 12)): 27,
    ((1, 1), (2, 13)): 27, ((3, 9),): 26, ((3, 1), (6, 4)): 54, ((3, 3), (6, 3)): 72,
}


def test_7_tipi_ciclici_e_fusione():
    assert Counter(tipo_ciclico(p) for p in H) == TIPI_LIBRO
    fusione = {}
    for num, _, _, t in CLASSI_LIBRO:
        simboli = {"I": "SCD", "T": "SDC", "C": "CDS"}
        rappresentante = kron(*(LOC[simboli[x]] for x in t))
        fusione.setdefault(tipo_ciclico(rappresentante), []).append(num)
    assert len(fusione) == 7 and sum(len(v) for v in fusione.values()) == 27


def test_punti_fissi_app_b9():
    assert Counter(sum(1 for i, v in enumerate(p) if i == v) for p in H) == {
        0: 152, 1: 27, 3: 27, 9: 9, 27: 1}


def test_ordini():
    assert Counter(ordine(p) for p in H) == {1: 1, 2: 63, 3: 26, 6: 126}
    assert Counter(ordine(p) for p in GAMMA) == {1: 1, 2: 63, 3: 98, 6: 342, 9: 144}


# ════════════════════════ § 6.9 centro, § 6.10 J ════════════════════════════

def test_centro_banale():
    centro = [z for z in H if all(comp(z, g) == comp(g, z) for g in H)]
    assert centro == [ID]


def test_j():
    J = kron(LOC["DCS"], LOC["DCS"], LOC["DCS"])
    assert J == tuple(26 - i for i in range(N))
    assert gr.numero_tavola(("DCS", "DCS", "DCS")) == 215
    assert ordine(J) == 2 and tipo_ciclico(J) == ((1, 1), (2, 13))
    assert [i for i in range(N) if J[i] == i] == [13]
    assert tipo_locale("DCS") == "T"                        # classe (T, T, T) = #27


# ═════════════════════════ § 8.2 tavola locale 6×6 ═════════════════════════

TAVOLA_6X6 = {   # riga P, colonna Q → P ∘ Q (prima Q, poi P)
    "SCD": "SCD SDC CSD CDS DSC DCS", "SDC": "SDC SCD DSC DCS CSD CDS",
    "CSD": "CSD CDS SCD SDC DCS DSC", "CDS": "CDS CSD DCS DSC SCD SDC",
    "DSC": "DSC DCS SDC SCD CDS CSD", "DCS": "DCS DSC CDS CSD SDC SCD",
}


def test_tavola_6x6_36_celle():
    nome = {v: k for k, v in LOC.items()}
    celle = 0
    for p, riga in TAVOLA_6X6.items():
        for q, atteso in zip(ORDINE_LIBRO, riga.split()):
            a, b = LOC[p], LOC[q]
            assert nome[tuple(a[b[i]] for i in range(3))] == atteso, (p, q)
            celle += 1
    assert celle == 36


def test_inversi_e_non_commutativita_8_2():
    assert TAVOLA_6X6["SDC"].split()[ORDINE_LIBRO.index("CSD")] == "DSC"
    assert TAVOLA_6X6["CSD"].split()[ORDINE_LIBRO.index("SDC")] == "CDS"
    auto = [s for s in ORDINE_LIBRO if TAVOLA_6X6[s].split()[ORDINE_LIBRO.index(s)] == "SCD"]
    assert auto == ["SCD", "SDC", "CSD", "DCS"]


DECOMPOSIZIONI = {   # § 8.5: risultato → coppie (P, Q) con P ∘ Q = risultato
    "SCD": "SCD∘SCD SDC∘SDC CSD∘CSD CDS∘DSC DSC∘CDS DCS∘DCS",
    "SDC": "SCD∘SDC SDC∘SCD CSD∘CDS CDS∘DCS DSC∘CSD DCS∘DSC",
    "CSD": "SCD∘CSD SDC∘DSC CSD∘SCD CDS∘SDC DSC∘DCS DCS∘CDS",
    "CDS": "SCD∘CDS SDC∘DCS CSD∘SDC CDS∘SCD DSC∘DSC DCS∘CSD",
    "DSC": "SCD∘DSC SDC∘CSD CSD∘DCS CDS∘CDS DSC∘SCD DCS∘SDC",
    "DCS": "SCD∘DCS SDC∘CDS CSD∘DSC CDS∘CSD DSC∘SDC DCS∘SCD",
}


def test_decomposizioni_8_5():
    tutte = []
    for r, coppie in DECOMPOSIZIONI.items():
        lista = [tuple(c.split("∘")) for c in coppie.split()]
        assert len(lista) == 6
        assert [p for p, _ in lista] == list(ORDINE_LIBRO)       # una per fattore
        assert sorted(q for _, q in lista) == sorted(ORDINE_LIBRO)
        for p, q in lista:
            assert TAVOLA_6X6[p].split()[ORDINE_LIBRO.index(q)] == r
        tutte += lista
    assert len(set(tutte)) == 36


# ══════════════════ § 11.7.6: stadi e classi laterali ═══════════════════════

def _stadio(sigla, rov=False):
    deck = list(range(N))[::-1] if rov else list(range(N))
    d = gr.raccogli(gr.distribuisci(deck), sigla)
    return tuple(d.index(c) for c in range(N))


def _coset(p):
    for r in range(3):
        mr = ID
        for _ in range(r):
            mr = comp(MSC, mr)
        if comp(p, inv(mr)) in set(H):
            return r
    return None


def test_stadi_percorrono_le_classi_laterali():
    attesi = {1: (6, 12, 12), 2: (36, 144, 72), 3: (216, 1728, 216)}
    for j, (senza, prefissi, distinte) in attesi.items():
        tr_senza = set()
        conteggio = Counter()
        for sig in product(gr.SIGLE, repeat=j):
            for eps in product((0, 1), repeat=j):
                T = ID
                for s, e in zip(sig, eps):
                    T = comp(_stadio(s, bool(e)), T)
                conteggio[T] += 1
                if not any(eps):
                    tr_senza.add(T)
        assert len(tr_senza) == senza
        assert sum(conteggio.values()) == prefissi and len(conteggio) == distinte
        assert {_coset(T) for T in conteggio} == {j % 3}
    assert sorted(Counter(_coset(g) for g in GAMMA).values()) == [216, 216, 216]


def test_prop_9_58_otto_procedure_per_trasformazione():
    s = servizio_procedure()
    conteggio = Counter()
    for n in range(216):
        for m in range(8):
            conteggio[tuple(s.trasformazione(ProceduraGioco.da_identificatore(n, m)))] += 1
    assert len(conteggio) == 216 and set(conteggio.values()) == {8}
    assert set(conteggio) == set(H)


# ════════════════════════ proprieta' del § 18.4 ═════════════════════════════

def test_a4_limite_di_kronecker_controesempio_minimo():
    def forzabile(c1, c2, t1, t2):
        return any(p[c1] == t1 and p[c2] == t2 for p in H)
    primo = next((c1, c2, t1, t2) for c1 in range(N) for c2 in range(N) if c2 != c1
                 for t1 in range(N) for t2 in range(N)
                 if t2 != t1 and not forzabile(c1, c2, t1, t2))
    assert primo == (0, 1, 0, 3)
    assert not forzabile(0, 1, 0, 9)                    # l'esempio dell'audit, non minimo


def test_somma_guide_39_in_h_e_gamma():
    assert all(p[0] + p[13] + p[26] == 39 for p in GAMMA)


def test_punti_fissi_in_gamma_restano_potenze_di_3():
    assert {sum(1 for i, v in enumerate(p) if i == v) for p in GAMMA} == {0, 1, 3, 9, 27}


def test_parita_a10():
    def segno(p):
        return (-1) ** sum(1 for i in range(len(p)) for j in range(i + 1, len(p)) if p[i] > p[j])
    conteggio = Counter()
    for a, b, c in product(ORDINE_LIBRO, repeat=3):
        p = kron(LOC[a], LOC[b], LOC[c])
        assert segno(p) == segno(LOC[a]) * segno(LOC[b]) * segno(LOC[c])
        conteggio[segno(p)] += 1
    assert conteggio == {1: 108, -1: 108}


def test_prop_5_53_auto_inversa_se_righe_involutive():
    for a, b, c in product(ORDINE_LIBRO, repeat=3):
        p = kron(LOC[a], LOC[b], LOC[c])
        righe = all(ordine(LOC[s]) <= 2 for s in (a, b, c))
        assert (comp(p, p) == ID) == righe
