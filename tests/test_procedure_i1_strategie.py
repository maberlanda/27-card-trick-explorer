"""Compartimento I1 — fibre carta→bersaglio, solutore storico e variante sicura.

Contratti di regressione (DP4, DP5 approvate; memo pre-I1 §§ 7–9):

* ogni fibra carta→bersaglio ha 64 procedure = 8 trasformazioni × 8, con
  8 procedure semplici, una per trasformazione;
* la procedura storica, argmin di (k1, #) fra le semplici, coincide con
  `risolvi_trucco` in 729/729 coppie, e il suo k1 e' la distanza di Hamming
  fra le cifre ternarie di carta e bersaglio;
* la variante sicura, argmin di (k3, k2, k1, m, #), ha k2 = 0 ovunque,
  differisce dalla storica in 386 coppie ed elimina 486 raccolte CDS/DSC;
* con i rovesciamenti k1 scende in 242 coppie (174 di 1, 60 di 2, 8 di 3):
  «senza rovesciamenti» non vuol dire «sempre piu' semplice».

Gli oracoli (fibra per forza bruta, chiave, distanza) sono scritti qui.
"""
import pathlib
from collections import Counter

import pytest

from gioco27.core import gioco_reale as gr
from gioco27.services.procedure import ProceduraGioco, servizio_procedure

COPPIE = [(c, t) for c in range(27) for t in range(27)]
R = (2, 1, 0)
I3 = (0, 1, 2)


def _c3(a, b):
    return tuple(a[b[i]] for i in range(3))


def _T_libro(mesc, eps):
    s1, s2, s3 = (gr.MESCOLAMENTO[s] for s in mesc)
    r1, r2, r3 = (R if e else I3 for e in eps)
    m2 = _c3(s3, _c3(r3, _c3(r2, r1)))
    m1 = _c3(r3, _c3(s2, _c3(r2, r1)))
    m0 = _c3(r3, _c3(r2, _c3(s1, r1)))
    return tuple(9 * m2[n // 9] + 3 * m1[(n // 3) % 3] + m0[n % 3]
                 for n in range(27))


def _cifre(n):
    return (n % 3, (n // 3) % 3, n // 9)


def _hamming(a, b):
    return sum(x != y for x, y in zip(_cifre(a), _cifre(b)))


def _k(mesc, eps):
    """(k1, k2, k3) calcolati qui, senza il modello."""
    return (sum(s != "SCD" for s in mesc),
            sum(s in ("CDS", "DSC") for s in mesc),
            sum(eps))


@pytest.fixture(scope="module")
def servizio():
    return servizio_procedure()


@pytest.fixture(scope="module")
def forza_bruta():
    """(c, t) → lista di (mesc, eps, T) per forza bruta sulla formula del libro."""
    fibre = {}
    for n in range(216):
        mesc = gr.mescolamenti_da_numero(n)
        for m in range(8):
            eps = ((m >> 2) & 1, (m >> 1) & 1, m & 1)
            T = _T_libro(mesc, eps)
            for c in range(27):
                fibre.setdefault((c, T[c]), []).append((mesc, eps, T, n, m))
    return fibre


# ═══════════════════════════ fibre carta → bersaglio ════════════════════════

def test_struttura_delle_729_fibre(servizio, forza_bruta):
    for c, t in COPPIE:
        fibra = servizio.fibra_bersaglio(c, t)
        assert (fibra.carta, fibra.bersaglio) == (c, t)
        assert len(fibra.procedure) == 64
        assert len(fibra.gruppi) == 8
        assert len({g.trasformazione for g in fibra.gruppi}) == 8
        for g in fibra.gruppi:
            assert len(g.procedure) == 8
            assert g.trasformazione[c] == t
            assert all(servizio.trasformazione(p) == g.trasformazione
                       for p in g.procedure)
            assert sum(p.semplice for p in g.procedure) == 1
            assert g.semplice.semplice
        assert len(fibra.semplici) == 8 and all(p.semplice for p in fibra.semplici)
        # ogni classe di trasformazione della fibra e' inclusa per intero
        for g in fibra.gruppi:
            assert g.procedure == servizio.classe_trasformazione(g.trasformazione)
        # stesso insieme dell'oracolo per forza bruta
        attesi = {(n, m) for _, _, _, n, m in forza_bruta[(c, t)]}
        assert {p.identificatore for p in fibra.procedure} == attesi


def test_ordine_dei_gruppi_dichiarato(servizio):
    fibra = servizio.fibra_bersaglio(0, 13)
    numeri = [g.semplice.numero_tavola for g in fibra.gruppi]
    assert numeri == sorted(numeri)


# ═══════════════════════════════ solutore storico ═══════════════════════════

def test_la_storica_coincide_con_risolvi_trucco(servizio):
    for c, t in COPPIE:
        storica = servizio.procedura_storica(c, t)
        piano = gr.risolvi_trucco(c, t)
        assert storica.semplice
        assert storica.mescolamenti == piano["mescolamenti"]
        assert storica.impilamenti == piano["impilamenti"]
        assert storica.numero_tavola == piano["numero"]
        assert servizio.trasformazione(storica) == tuple(piano["T"])


def test_k1_della_storica_e_la_distanza_di_hamming(servizio, forza_bruta):
    for c, t in COPPIE:
        assert servizio.procedura_storica(c, t).costo.k1 == _hamming(c, t)
        minimo = min(_k(mesc, eps)[0] for mesc, eps, *_ in forza_bruta[(c, t)]
                     if not any(eps))
        assert minimo == _hamming(c, t)


# ═══════════════════════════════ variante sicura ════════════════════════════

def test_la_sicura_e_l_argmin_dichiarato(servizio, forza_bruta):
    for c, t in COPPIE:
        attesa = min(forza_bruta[(c, t)],
                     key=lambda r: (_k(r[0], r[1])[2], _k(r[0], r[1])[1],
                                    _k(r[0], r[1])[0], r[4], r[3]))
        sicura = servizio.procedura_sicura(c, t)
        assert (sicura.mescolamenti, sicura.rovesciamenti) == attesa[:2]


def test_regressione_storica_contro_sicura(servizio):
    differenze, eliminate = 0, 0
    for c, t in COPPIE:
        storica = servizio.procedura_storica(c, t)
        sicura = servizio.procedura_sicura(c, t)
        assert sicura.costo.k3 == 0 and sicura.semplice
        assert sicura.costo.k2 == 0 and sicura.sicura
        assert sicura.costo.k1 == storica.costo.k1
        assert servizio.trasformazione(sicura)[c] == t
        differenze += sicura != storica
        eliminate += storica.costo.k2 - sicura.costo.k2
    assert differenze == 386
    assert eliminate == 486


def test_la_sicura_non_sostituisce_la_storica(servizio):
    # 0 → 26: la storica resta DSC DSC DSC (#129), la sicura e' DCS DCS DCS (#215)
    assert servizio.procedura_storica(0, 26).numero_tavola == 129
    assert servizio.procedura_sicura(0, 26).numero_tavola == 215
    assert gr.risolvi_trucco(0, 26)["mescolamenti"] == ("DSC", "DSC", "DSC")


# ═══════════════════════════ rovesciamenti e k1 ═════════════════════════════

def test_i_rovesciamenti_possono_ridurre_k1(servizio):
    miglioramenti = Counter()
    for c, t in COPPIE:
        fibra = servizio.fibra_bersaglio(c, t)
        con = min(p.costo.k1 for p in fibra.procedure)
        senza = min(p.costo.k1 for p in fibra.semplici)
        assert con == min(_hamming(c, t), _hamming(26 - c, t))
        if con < senza:
            miglioramenti[senza - con] += 1
    assert sum(miglioramenti.values()) == 242
    assert dict(miglioramenti) == {1: 174, 2: 60, 3: 8}


# ═══════════════════════════════ casi leggibili ═════════════════════════════

CASI = [
    # c,  t, storica,        #,   k1,k2, sicura,          #,  k1,k2
    (0, 13, "CSD CSD CSD", 86, 3, 0, "CSD CSD CSD", 86, 3, 0),
    (13, 13, "SCD SCD SCD", 0, 0, 0, "SCD SCD SCD", 0, 0, 0),
    (0, 2, "DSC SCD SCD", 3, 1, 1, "DCS SCD SCD", 5, 1, 0),
    (26, 24, "CDS SCD SCD", 4, 1, 1, "DCS SCD SCD", 5, 1, 0),
    (0, 20, "DSC SCD DSC", 111, 2, 2, "DCS SCD DCS", 185, 2, 0),
    (7, 19, "SCD CDS DSC", 132, 2, 2, "SCD DCS DCS", 210, 2, 0),
    (0, 26, "DSC DSC DSC", 129, 3, 3, "DCS DCS DCS", 215, 3, 0),
    (26, 0, "CDS CDS CDS", 172, 3, 3, "DCS DCS DCS", 215, 3, 0),
]


@pytest.mark.parametrize("c,t,st,nst,k1s,k2s,si,nsi,k1i,k2i", CASI,
                         ids=[f"{c}->{t}" for c, t, *_ in CASI])
def test_casi_del_memo(servizio, c, t, st, nst, k1s, k2s, si, nsi, k1i, k2i):
    storica = servizio.procedura_storica(c, t)
    sicura = servizio.procedura_sicura(c, t)
    assert storica == ProceduraGioco(tuple(st.split()))
    assert (storica.numero_tavola, storica.costo.k1, storica.costo.k2) == (nst, k1s, k2s)
    assert sicura == ProceduraGioco(tuple(si.split()))
    assert (sicura.numero_tavola, sicura.costo.k1, sicura.costo.k2) == (nsi, k1i, k2i)


def test_0_verso_13_stesso_bersaglio_trasformazioni_diverse(servizio):
    fibra = servizio.fibra_bersaglio(0, 13)
    numeri = {g.semplice.numero_tavola for g in fibra.gruppi}
    assert {86, 158} <= numeri


def test_un_rovesciamento_sostituisce_tre_raccolte(servizio):
    """0 → 26: con un solo capovolgimento basta SCD SCD SCD (k1 = 0)."""
    fibra = servizio.fibra_bersaglio(0, 26)
    migliore = min(fibra.procedure, key=lambda p: (p.costo.k1, p.costo.k3,
                                                  p.indice_rovesciamenti,
                                                  p.numero_tavola))
    assert migliore == ProceduraGioco(("SCD", "SCD", "SCD"), (0, 0, 1))


# ═══════════════════════════════ compatibilita' ═════════════════════════════

def test_nessuna_vista_usa_ancora_il_servizio_delle_procedure():
    gui = pathlib.Path(__file__).resolve().parents[1] / "gioco27" / "gui"
    usi = [f.name for f in gui.rglob("*.py")
           if "procedura_sicura" in f.read_text(encoding="utf-8")
           or "services.procedure" in f.read_text(encoding="utf-8")]
    assert usi == []
