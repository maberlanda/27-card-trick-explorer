"""Compartimento I6 — service del laboratorio (catalogo, domini, verifiche)."""
import ast
from collections import Counter
from pathlib import Path

import pytest

from gioco27.core import gioco_reale as gr
from gioco27.core.group_theory import get_group_data
from gioco27.services import laboratorio as lab
from gioco27.services import riconoscimento as rc
from gioco27.services.laboratorio import Dominio, Esito, Metodo

ROOT = Path(__file__).resolve().parents[1]
N = 27
ID = tuple(range(N))


def comp(a, b):
    return tuple(a[x] for x in b)


def inv(p):
    q = [0] * len(p)
    for i, v in enumerate(p):
        q[v] = i
    return tuple(q)


def tutte():
    return [(p, d, p.verifica(d)) for p in lab.CATALOGO for d in p.domini]


# ═══════════════════════════ catalogo chiuso ═════════════════════════════════

def test_catalogo_chiuso_id_unici_domini_e_fonti():
    ids = [p.id for p in lab.CATALOGO]
    assert len(ids) == len(set(ids)) == 21
    assert isinstance(lab.CATALOGO, tuple)
    for p in lab.CATALOGO:
        assert p.fonte, p.id
        assert p.domini and all(isinstance(d, Dominio) for d in p.domini)
        assert len(set(p.domini)) == len(p.domini)
    with pytest.raises(lab.ProprietaSconosciuta):
        lab.proprieta("inventata")


def test_nessuna_estensione_tacita_di_dominio():
    for p in lab.CATALOGO:
        for d in Dominio:
            if d not in p.domini:
                with pytest.raises(lab.DominioNonPrevisto):
                    p.verifica(d)


def test_ogni_verifica_ha_esito_metodo_e_conteggi_coerenti():
    for p, d, v in tutte():
        assert v.proprieta == p.id and v.dominio is d
        assert v.esito in (Esito.VERA, Esito.FALSA)          # nessuna esplorazione aperta
        if v.metodo is Metodo.ESAUSTIVO:
            assert d is not Dominio.S27
            assert v.totale is not None and 0 < v.controllati <= v.totale
            if v.vera:
                assert v.controllati == v.totale
        if v.metodo is Metodo.TEOREMA_FONTE:
            assert v.vera and v.fonte and v.controllati == 0
        if v.esito is Esito.FALSA and p.id not in ("otto_procedure",):
            assert v.controesempio is not None, (p.id, d)


def test_s27_mai_enumerato_e_mai_legge_per_eredita_da_h():
    """Una proprieta' vera su H non diventa legge di S27: su S27 serve un
    teorema citato o e' falsa con un controesempio esplicito."""
    for p, d, v in tutte():
        if d is Dominio.S27:
            assert v.totale is None
            assert v.metodo in (Metodo.TEOREMA_FONTE, Metodo.CONTROESEMPIO)
            if v.metodo is Metodo.CONTROESEMPIO:
                assert v.esito is Esito.FALSA
    for pid in ("punti_fissi_potenze_di_3", "somma_guide_39", "ordini_1_2_3_6",
                "separabile"):
        assert lab.verifica(pid, Dominio.H).vera
        assert lab.verifica(pid, Dominio.S27).esito is Esito.FALSA


def test_h_e_gamma_esaustivi():
    assert len(lab.elementi(Dominio.H)) == len(set(lab.elementi(Dominio.H))) == 216
    assert len(lab.elementi(Dominio.GAMMA)) == len(set(lab.elementi(Dominio.GAMMA))) == 648
    assert set(lab.elementi(Dominio.H)) <= set(lab.elementi(Dominio.GAMMA))
    for pid in ("punti_fissi_potenze_di_3", "somma_guide_39", "somme_riconoscono_h"):
        for d, n in ((Dominio.H, 216), (Dominio.GAMMA, 648)):
            v = lab.verifica(pid, d)
            assert (v.metodo, v.controllati, v.totale) == (Metodo.ESAUSTIVO, n, n)
    assert lab.verifica("chiuso_composizione", Dominio.GAMMA).controllati == 648 ** 2
    assert lab.verifica("h_normale_in_gamma", Dominio.GAMMA).controllati == 648 * 216
    with pytest.raises(lab.DominioNonPrevisto):
        lab.elementi(Dominio.S27)


# ═════════════════════ risultati attesi, uno per proprieta' ══════════════════

ATTESI = {
    "separabile": {"h": True, "gamma": False, "s27": False},
    "chiuso_composizione": {"h": True, "gamma": True},
    "commutativo": {"s3": False, "h": False, "gamma": False, "s27": False},
    "centro_banale": {"h": True, "gamma": True, "s27": True},
    "ordini_1_2_3_6": {"h": True, "gamma": False, "s27": False},
    "punti_fissi_potenze_di_3": {"h": True, "gamma": True, "s27": False},
    "somma_guide_39": {"h": True, "gamma": True, "s27": False},
    "coniugati_stesso_tipo": {"h": True, "gamma": True, "s27": True},
    "stesso_tipo_coniugati": {"h": False, "gamma": False, "s27": True},
    "carta_bersaglio_otto": {"h": True, "gamma": False},
    "due_carte_forzabili": {"h": False, "gamma": False, "s27": True},
    "parita_prodotto_locale": {"h": True},
    "autoinversa_fattori_involutivi": {"h": True},
    "j_fissa_solo_13": {"h": True},
    "somme_riconoscono_h": {"h": True, "gamma": True, "s27": True},
    "h_normale_in_gamma": {"gamma": True},
    "forma_normale_unica": {"gamma": True},
    "stadi_classe_laterale": {"procedure": True},
    "otto_procedure": {"procedure": True},
    "tavola_quadrato_latino": {"s3": True},
    "decomposizioni_uniformi": {"s3": True, "h": True},
}


def test_ogni_proprieta_ha_il_suo_esito_atteso():
    assert set(ATTESI) == {p.id for p in lab.CATALOGO}
    for p in lab.CATALOGO:
        assert {d.value for d in p.domini} == set(ATTESI[p.id]), p.id
        for d in p.domini:
            assert p.verifica(d).vera == ATTESI[p.id][d.value], (p.id, d)


# ═════════════════════ controesempi: deterministici e minimi ═════════════════

def _lex_min(dominio, pred):
    return min(p for p in lab.elementi(dominio) if not pred(p))


def test_controesempi_minimi_su_h_e_gamma():
    v = lab.verifica("ordini_1_2_3_6", Dominio.GAMMA)
    atteso = _lex_min(Dominio.GAMMA, lambda p: lab.ordine(p) in (1, 2, 3, 6))
    assert v.controesempio.elementi == (atteso,) and v.controesempio.dato("ordine") == 9
    v = lab.verifica("separabile", Dominio.GAMMA)
    assert v.controesempio.elementi == (min(set(lab.elementi(Dominio.GAMMA))
                                           - set(lab.elementi(Dominio.H))),)
    assert v.controesempio.dato("dominio") == "gamma"
    v = lab.verifica("carta_bersaglio_otto", Dominio.GAMMA)
    assert v.controesempio.dati == (("carta", 0), ("posizione", 0), ("soluzioni", 24))


def test_controesempi_s27_primi_in_ordine_lessicografico():
    scambio = tuple(range(25)) + (26, 25)          # seconda permutazione lessicografica
    for pid, chiave, valore in (("punti_fissi_potenze_di_3", "punti_fissi", 25),
                                ("somma_guide_39", "somma", 38)):
        ce = lab.verifica(pid, Dominio.S27).controesempio
        assert ce.elementi == (scambio,) and ce.dato(chiave) == valore
    ce = lab.verifica("separabile", Dominio.S27).controesempio
    assert ce.elementi == (scambio,) and not rc.separabile(scambio).separabile
    ce = lab.verifica("ordini_1_2_3_6", Dominio.S27).controesempio
    assert ce.elementi == (tuple(range(23)) + (24, 25, 26, 23),) and ce.dato("ordine") == 4
    a, b = lab.verifica("commutativo", Dominio.S27).controesempio.elementi
    assert a == scambio and b == tuple(range(24)) + (25, 24, 26)
    assert comp(a, b) != comp(b, a)


def test_a4_due_carte_minimo_e_divergenza_dall_audit():
    ce = lab.verifica("due_carte_forzabili", Dominio.H).controesempio
    assert ce.dati == (("c1", 0), ("c2", 1), ("t1", 0), ("t2", 3))
    # l'audit citava (0,1) → (0,9): vero controesempio, ma non il minimo
    assert not any(p[0] == 0 and p[1] == 9 for p in lab.elementi(Dominio.H))
    assert lab.proprieta("due_carte_forzabili").nota(Dominio.H) == "nota_audit_0_9"


def test_commutativo_s3_coerente_con_tavola_8_2():
    a, b = lab.verifica("commutativo", Dominio.S3).controesempio.elementi
    assert a != b and comp(a, b) != comp(b, a)
    sig = {tuple(v): k for k, v in gr.MESCOLAMENTO.items()}
    assert lab.tavola_locale().celle[lab.ORDINE_TAVOLA_LOCALE.index(sig[a])][
        lab.ORDINE_TAVOLA_LOCALE.index(sig[b])] == sig[comp(a, b)]


def test_controesempi_riproducibili():
    lab._CACHE.clear()
    prima = [v.controesempio for _, _, v in tutte()]
    lab._CACHE.clear()
    assert [v.controesempio for _, _, v in tutte()] == prima


def test_stesso_tipo_non_coniugati_in_h():
    a, b = lab.verifica("stesso_tipo_coniugati", Dominio.H).controesempio.elementi
    assert lab.tipo_ciclico(a) == lab.tipo_ciclico(b)
    h = lab.elementi(Dominio.H)
    assert all(comp(comp(g, a), inv(g)) != b for g in h)


# ═════════════════════════ 27 classi → 7 tipi ════════════════════════════════

def test_27_classi_di_h():
    classi = lab.classi_h()
    assert len(classi) == 27 and [c.numero for c in classi] == list(range(1, 28))
    assert sorted(n for c in classi for n in c.elementi) == list(range(216))
    assert [c.cardinalita for c in classi] == [1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 6, 6, 6, 6,
                                               6, 6, 8, 9, 9, 9, 12, 12, 12, 18, 18, 18, 27]
    assert classi[26].tipo == "TTT" and classi[0].tipo == "III" and classi[16].tipo == "CCC"
    h = lab.elementi(Dominio.H)
    for c in classi:                                  # oracolo: coniugio esplicito
        x = h[c.elementi[0]]
        assert {comp(comp(g, x), inv(g)) for g in h} == {h[n] for n in c.elementi}


def test_fusione_27_in_7_tipi_con_molteplicita():
    f = lab.fusione_in_s27()
    assert len(f) == 7
    assert [t.cardinalita for t in f] == [1, 9, 27, 27, 26, 54, 72]
    assert [t.punti_fissi for t in f] == [27, 9, 3, 1, 0, 0, 0]
    assert [t.ordine for t in f] == [1, 2, 2, 2, 3, 6, 6]
    assert sorted(c for t in f for c in t.classi) == list(range(1, 28))
    assert [len(t.classi) for t in f] == [1, 3, 3, 1, 7, 3, 9]
    h = lab.elementi(Dominio.H)
    per_tipo = Counter(lab.tipo_ciclico(p) for p in h)            # tutti i 216
    assert {t.tipo: t.cardinalita for t in f} == dict(per_tipo)


def test_classi_legacy_concordano():
    legacy = get_group_data()
    assert len(legacy.classes) == 27
    adatt = lab._legacy()
    assert sorted(adatt.classi) == sorted(c.elementi for c in lab.classi_h())
    assert all(adatt.ordini[n] == lab.ordine(p) for n, p in enumerate(lab.elementi(Dominio.H)))


def test_ordini_e_punti_fissi_distribuzioni():
    h, g = lab.elementi(Dominio.H), lab.elementi(Dominio.GAMMA)
    assert Counter(map(lab.ordine, h)) == {1: 1, 2: 63, 3: 26, 6: 126}
    assert Counter(map(lab.ordine, g)) == {1: 1, 2: 63, 3: 98, 6: 342, 9: 144}
    assert Counter(len(lab.punti_fissi(p)) for p in h) == {0: 152, 1: 27, 3: 27, 9: 9, 27: 1}
    assert Counter(len(lab.punti_fissi(p)) for p in g) == {0: 296, 1: 243, 3: 99, 9: 9, 27: 1}
    assert len({lab.tipo_ciclico(p) for p in h}) == 7
    assert len({lab.tipo_ciclico(p) for p in g}) == 10
    assert Counter(map(lab.segno, h)) == {1: 108, -1: 108}


# ═════════════════════════════ centro e J ════════════════════════════════════

def test_centro_con_oracolo_indipendente():
    c = lab.centro()
    assert c.elementi == (0,) and c.commutazioni_controllate == 216 * 216
    assert c.legacy_concorda
    h = lab.elementi(Dominio.H)
    oracolo = [n for n, z in enumerate(h) if all(comp(z, g) == comp(g, z) for g in h)]
    assert oracolo == [0] and h[0] == ID


def test_scheda_j():
    j = lab.scheda_j()
    assert j.numero_tavola == 215 and j.sigle == ("DCS", "DCS", "DCS")
    assert j.permutazione == tuple(26 - i for i in range(N))
    assert j.ordine == 2 and j.tipo_ciclico == ((1, 1), (2, 13)) and j.punti_fissi == (13,)
    assert (j.classe, j.tipo_classe) == (27, "TTT")
    assert len(j.procedure) == 8 and (215, 0) in j.procedure
    assert tuple(gr.riga_tavola(215)["T"]) == j.permutazione


# ═══════════════════════ classi laterali e stadi ═════════════════════════════

def test_classi_laterali_partizionano_gamma():
    cl = lab.classi_laterali()
    assert [(c.r, c.cardinalita, c.contiene_h) for c in cl] == [
        (0, 216, True), (1, 216, False), (2, 216, False)]
    et = [lab.etichetta(g) for g in lab.elementi(Dominio.GAMMA)]
    assert [e.r for e in et] == [r for r in range(3) for _ in range(216)]
    assert [e.numero_tavola for e in et] == list(range(216)) * 3


def test_stadi_cardinalita_e_quattro_oggetti_distinti():
    righe = {r.j: r for r in lab.stadi()}
    assert (righe[1].prefissi_con, righe[1].trasformazioni_con, righe[1].classi_laterali) == (12, 12, (1,))
    assert (righe[2].prefissi_con, righe[2].trasformazioni_con, righe[2].molteplicita) == (144, 72, (2,))
    r3 = righe[3]
    assert (r3.prefissi_senza, r3.trasformazioni_senza) == (216, 216)
    assert (r3.prefissi_con, r3.trasformazioni_con, r3.molteplicita) == (1728, 216, (8,))
    assert r3.classi_laterali == (0,) and r3.configurazioni_uguali_a_procedure == 1728
    # 216 trasformazioni, 648 elementi di Γ, 1728 configurazioni, 1728 procedure
    assert lab.CARDINALITA[Dominio.H] == 216 and lab.CARDINALITA[Dominio.GAMMA] == 648
    assert len(lab.elementi(Dominio.PROCEDURE)) == 1728


# ═══════════════════ tavola 6×6 e decomposizioni locali ══════════════════════

def test_tavola_locale_36_su_36_con_la_fonte():
    t = lab.tavola_locale()
    assert t.celle_concordi == 36 and t.celle == lab.TAVOLA_LOCALE_FONTE
    assert t.ordine == ("SCD", "SDC", "CSD", "CDS", "DSC", "DCS")
    assert dict(t.inversi)["CDS"] == "DSC" and dict(t.inversi)["DSC"] == "CDS"
    assert dict(t.tipi) == {"SCD": "I", "SDC": "T", "CSD": "T", "DCS": "T",
                            "CDS": "C", "DSC": "C"}
    for i, p in enumerate(t.ordine):                        # (a∘b)[i] = a[b[i]]
        for k, q in enumerate(t.ordine):
            a, b = gr.MESCOLAMENTO[p], gr.MESCOLAMENTO[q]
            assert tuple(gr.MESCOLAMENTO[t.celle[i][k]]) == tuple(a[b[x]] for x in range(3))


def test_decomposizioni_locali_esaustive():
    tutte_ = []
    for r in lab.ORDINE_TAVOLA_LOCALE:
        d = lab.decomposizioni_locali(r)
        assert [p for p, _ in d] == list(lab.ORDINE_TAVOLA_LOCALE)
        t = lab.tavola_locale()
        for p, q in d:
            assert t.celle[t.ordine.index(p)][t.ordine.index(q)] == r
        tutte_ += d
    assert len(set(tutte_)) == 36
    assert lab.decomposizioni_locali("SCD")[3] == ("CDS", "DSC")
    assert lab.transizione_locale("SDC", "CDS") == "CSD"            # § 8.5
    for y in lab.ORDINE_TAVOLA_LOCALE:
        for x in lab.ORDINE_TAVOLA_LOCALE:
            r = lab.transizione_locale(y, x)
            assert (r, y) in lab.decomposizioni_locali(x)
    with pytest.raises(ValueError):
        lab.decomposizioni_locali("XYZ")


def test_esempio_8_4_composizione_per_livelli():
    idx = {s: i for i, s in enumerate(lab.ORDINE_TAVOLA_LOCALE)}
    t = lab.tavola_locale().celle
    P, Q = ("CDS", "SDC", "DCS"), ("DSC", "CSD", "DCS")
    assert tuple(t[idx[p]][idx[q]] for p, q in zip(P, Q)) == ("SCD", "DSC", "SCD")


# ═══════════════════════════════ grafi ═══════════════════════════════════════

def test_grafi_dichiarati():
    g = {x.id: x for x in lab.grafi()}
    assert set(g) == {"cayley_s3", "cayley_h", "raccolte"}
    s3 = g["cayley_s3"]
    assert (len(s3.vertici), len(s3.archi), s3.gradi, s3.diametro) == (6, 9, (3,), 2)
    assert s3.distribuzione == (1, 3, 2) and not s3.orientato
    hh = g["cayley_h"]
    assert (len(hh.vertici), len(hh.archi), hh.gradi, hh.diametro) == (216, 972, (9,), 6)
    assert hh.distribuzione == (1, 9, 33, 63, 66, 36, 8)          # (1 + 3x + 2x²)³
    rr = g["raccolte"]
    assert (len(rr.archi), rr.gradi, rr.diametro, rr.distribuzione) == (1620, (15,), 3, (1, 15, 75, 125))
    for x in g.values():
        assert x.dominio in (Dominio.S3, Dominio.H)
        assert all(a < b for a, b in x.archi)


def test_cammino_deterministico_tra_cronache():
    rr = lab.grafo("raccolte")
    c = lab.cammino(rr, 0, 215)
    assert c == lab.cammino(rr, 0, 215) and len(c) == 4 and c[0] == 0 and c[-1] == 215
    for a, b in zip(c, c[1:]):
        sa, sb = gr.mescolamenti_da_numero(a), gr.mescolamenti_da_numero(b)
        assert sum(x != y for x, y in zip(sa, sb)) == 1
    with pytest.raises(KeyError):
        lab.grafo("nessuno")


# ═══════════════════════ riuso di I5 e architettura ══════════════════════════

def test_etichetta_riusa_il_riconoscimento_i5():
    src = (ROOT / "gioco27" / "services" / "laboratorio.py").read_text(encoding="utf-8")
    assert "_rc.classe_estesa(" in src and "_rc.separabile(" in src
    assert "def separabile" not in src and "def classe_estesa" not in src
    e = lab.etichetta(gr.riga_tavola(100)["T"])
    assert (e.dominio, e.numero_tavola, e.r) == (Dominio.H, 100, 0)
    assert lab.etichetta(rc.traslazione(1)).dominio is Dominio.S27


def test_service_puro():
    tree = ast.parse((ROOT / "gioco27" / "services" / "laboratorio.py").read_text(encoding="utf-8"))
    moduli = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            moduli |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            moduli.add("." * n.level + (n.module or ""))
    assert not any("tkinter" in m or "gui" in m for m in moduli), moduli
