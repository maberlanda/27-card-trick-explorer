"""Compartimento I5 — service `services.riconoscimento`.

Oracoli indipendenti: la Def. 4.1 riscritta qui (`_sep`), le 216 righe e la
forma canonica del core, `try_kron_decompose`, `numero_di`. Il criterio per
somme e' confrontato col test diretto, mai derivato da esso.
"""
import ast
import itertools
import pathlib
import random
from fractions import Fraction

import pytest

from gioco27.core import gioco_reale as gr
from gioco27.core.algebra import CanonicalForm
from gioco27.core.dominio import PermutazioneNonValida
from gioco27.core.kronecker import try_kron_decompose
from gioco27.services import riconoscimento as rc
from gioco27.services import tabellone as tb

N = 27
SORGENTE = pathlib.Path(rc.__file__)
TAVOLA = [tuple(gr.riga_tavola(n)["T"]) for n in range(216)]


def _sep(p):
    for i in range(3):
        visto = {}
        for x in range(N):
            a, b = (x // 3 ** i) % 3, (p[x] // 3 ** i) % 3
            if visto.setdefault(a, b) != b:
                return False
    return True


def _estesa():
    out = {}
    for n in range(216):
        f = [list(gr.MESCOLAMENTO[s]) for s in gr.mescolamenti_da_numero(n)]
        for k in range(3):
            out[tuple(CanonicalForm(kron_factors=[f[2], f[1], f[0]], msc_exp=k).to_perm())] = (n, k)
    return out


ESTESA = _estesa()


def _campione(seme=2026, quanti=2000):
    rnd = random.Random(seme)
    for _ in range(quanti):
        p = list(range(N))
        rnd.shuffle(p)
        yield tuple(p)


# ═════════════════════════════════ ingressi ═════════════════════════════════

@pytest.mark.parametrize("valori,codice", [
    (list(range(26)), "lunghezza"),
    ([0] * 27, "valore_ripetuto"),
    (list(range(1, 28)), "fuori_intervallo"),
])
def test_permutazione_validata_con_codici(valori, codice):
    with pytest.raises(PermutazioneNonValida) as e:
        rc.permutazione(valori)
    assert e.value.codice == codice


def test_da_mazzi_non_inverte_di_nascosto():
    for n in (0, 100, 195, 215):
        iniziale = list(range(N))
        finale, _ = gr.esegui_partita(gr.mescolamenti_da_numero(n))
        T = rc.da_mazzi(iniziale, finale)
        assert T == TAVOLA[n]                            # T[carta] = posizione finale
        assert all(finale[T[i]] == iniziale[i] for i in range(N))


def test_da_mazzi_round_trip_con_carte_qualsiasi():
    rnd = random.Random(5)
    for _ in range(500):
        carte = [f"K{c}" for c in range(N)]
        rnd.shuffle(carte)
        p = list(range(N))
        rnd.shuffle(p)
        finale = [None] * N
        for i in range(N):
            finale[p[i]] = carte[i]
        assert rc.da_mazzi(carte, finale) == tuple(p)


@pytest.mark.parametrize("a,b,codice", [
    (list(range(26)), list(range(27)), "mazzo_lunghezza"),
    ([0] * 27, list(range(27)), "mazzo_duplicato"),
    (list(range(27)), list(range(1, 28)), "mazzi_diversi"),
])
def test_mazzi_non_validi(a, b, codice):
    with pytest.raises(rc.IngressoNonValido) as e:
        rc.da_mazzi(a, b)
    assert e.value.codice == codice and isinstance(e.value, ValueError)


def test_trasformazione_relativa_a8():
    rnd = random.Random(8)
    for _ in range(300):
        a, b = rnd.randrange(216), rnd.randrange(216)
        ma, _ = gr.esegui_partita(gr.mescolamenti_da_numero(a))
        mb, _ = gr.esegui_partita(gr.mescolamenti_da_numero(b))
        rel = rc.trasformazione_relativa(ma, mb)
        assert rel == tuple(TAVOLA[b][rc.inversa(TAVOLA[a])[p]] for p in range(N))
        assert rc.separabile(rel).separabile


# ═════════════════════════ riconoscitore diretto ════════════════════════════

def test_216_separabili_con_fattori_e_riga():
    for n, p in enumerate(TAVOLA):
        esito = rc.separabile(p)
        assert esito.separabile and all(l.passa for l in esito.livelli)
        assert esito.sigle == gr.mescolamenti_da_numero(n)
        assert esito.numero_tavola == n == tb.numero_di(p)
        f3, f2, f1 = try_kron_decompose(p)            # nomi dei fattori, livello 2 → 0
        assert tuple(s + "_U" for s in reversed(esito.sigle)) == (f3, f2, f1)
        assert rc.fattori_locali(p) == tuple(gr.MESCOLAMENTO[s] for s in esito.sigle)


def test_648_classe_estesa_e_solo_216_separabili():
    diretti = 0
    for p, (n, k) in ESTESA.items():
        e = rc.classe_estesa(p)
        assert e.appartiene and e.k == k
        assert e.componente == TAVOLA[n] and e.separabilita.numero_tavola == n
        diretti += rc.separabile(p).separabile
    assert len(ESTESA) == 648 and diretti == 216


def test_campione_s27_diretto_uguale_all_oracolo():
    for p in _campione():
        assert rc.separabile(p).separabile == _sep(p)
        assert rc.classe_estesa(p).appartiene == (p in ESTESA)


def test_diagnostica_del_conflitto():
    p = rc.traslazione(1)
    esito = rc.separabile(p)
    assert [l.passa for l in esito.livelli] == [True, False, False]
    c = esito.livelli[1].conflitto
    assert (c.x1 // 3) % 3 == (c.x2 // 3) % 3 == c.cifra
    assert c.cifra_immagine1 != c.cifra_immagine2
    assert (p[c.x1] // 3) % 3 == c.cifra_immagine1 and (p[c.x2] // 3) % 3 == c.cifra_immagine2
    assert esito.fattori is None and esito.numero_tavola is None
    assert esito.livelli[0].fattore == (1, 2, 0)


# ═════════════════════════ somme di fibra, Teor. 6.4 ════════════════════════

def test_costanti_e_tabella():
    assert rc.COSTANTI_C == (108, 90, 36)


def test_somme_avanti_e_indietro_sulle_216():
    diverse = 0
    for n, p in enumerate(TAVOLA):
        av = rc.criterio_somme(p, rc.AVANTI)
        ind = rc.criterio_somme(p, rc.INDIETRO)
        assert av.vero and ind.vero and av.coincide and ind.coincide
        assert av.fattori == rc.fattori_locali(p)
        assert ind.fattori == tuple(tuple(f.index(t) for t in range(3))
                                    for f in av.fattori)
        assert ind.analizzata == rc.inversa(p)
        diverse += av.fattori != ind.fattori
    assert diverse == 152


def test_criterio_uguale_al_diretto_su_tutti_i_domini():
    domini = list(ESTESA) + list(_campione(seme=99, quanti=3000))
    domini += [rc.traslazione(k) for k in range(N)]
    rnd = random.Random(11)
    for p in rnd.sample(TAVOLA, 40):                     # negativi mirati
        for x, y in itertools.combinations(range(N), 2):
            q = list(p)
            q[x], q[y] = q[y], q[x]
            domini.append(tuple(q))
    for p in domini:
        for verso in (rc.AVANTI, rc.INDIETRO):
            assert rc.criterio_somme(p, verso).vero == rc.separabile(p).separabile == _sep(p)


def test_il_criterio_non_usa_il_test_diretto():
    albero = ast.parse(SORGENTE.read_text(encoding="utf-8"))
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.FunctionDef) and nodo.name in ("criterio_somme",
                                                              "somme_di_fibra"):
            chiamate = {getattr(c.func, "id", getattr(c.func, "attr", ""))
                        for c in ast.walk(nodo) if isinstance(c, ast.Call)}
            assert not chiamate & {"separabile", "fattori_locali", "classe_estesa",
                                   "try_kron_decompose", "numero_di"}, chiamate


def test_esempio_7_1():
    r0, r1, r2 = (1, 2, 0), (2, 1, 0), (1, 0, 2)
    p = [9 * r2[x // 9] + 3 * r1[(x // 3) % 3] + r0[x % 3] for x in range(N)]
    assert rc.somme_di_fibra(p) == ((117, 126, 108), (144, 117, 90), (117, 36, 198))
    assert rc.criterio_somme(p).fattori == (r0, r1, r2)


def test_somme_dei_blocchi_identita():
    assert rc.somme_di_fibra(list(range(N)))[2] == (36, 117, 198)


def test_2_4_8_indietro_riproduce_il_libro():
    v = [22, 23, 21, 19, 20, 18, 25, 26, 24, 13, 14, 12, 10, 11, 9, 16, 17, 15,
         4, 5, 3, 1, 2, 0, 7, 8, 6]
    T = rc.da_mazzi(list(range(N)), v)                   # v e' il mazzo finale
    ind = rc.criterio_somme(T, rc.INDIETRO)
    assert ind.livelli[2].somme == (198, 117, 36)
    assert ind.fattori == ((1, 2, 0), (1, 0, 2), (2, 1, 0))  # righe del tabellone inverso
    assert rc.separabile(T).numero_tavola == 195


def test_negativo_interi_ma_non_permutazione():
    p = [20, 4, 17, 23, 8, 3, 16, 0, 26, 5, 12, 13, 11, 25, 14, 6, 21, 10,
         15, 22, 9, 2, 7, 24, 19, 18, 1]
    c = rc.criterio_somme(p)
    for l in c.livelli:
        assert l.candidati == (1, 1, 1)
        assert l.interi and l.in_dominio and not l.distinti and not l.permutazione
    assert not c.vero and c.ricostruita is None and c.coincide is None
    assert not rc.separabile(p).separabile


def test_traslazioni():
    for k in range(N):
        p = rc.traslazione(k)
        dentro = k in (0, 9, 18)
        assert rc.separabile(p).separabile == dentro
        assert rc.criterio_somme(p).vero == dentro
        assert rc.classe_estesa(p).appartiene == dentro
    assert rc.separabile(rc.traslazione(9)).numero_tavola == 144
    assert rc.separabile(rc.traslazione(18)).numero_tavola == 108
    c1 = rc.criterio_somme(rc.traslazione(1))
    assert [l.permutazione for l in c1.livelli] == [True, False, False]
    assert not c1.livelli[1].interi and not c1.livelli[2].interi
    assert c1.livelli[1].candidati == (Fraction(1, 3), Fraction(4, 3), Fraction(4, 3))


def test_verso_non_valido():
    with pytest.raises(rc.IngressoNonValido) as e:
        rc.criterio_somme(list(range(N)), "laterale")
    assert e.value.codice == "verso"


# ═══════════════════════════ due guide, v → w ═══════════════════════════════

def test_ritorno_da_guide_esempio_10_2_1():
    g = rc.ritorno_da_guide(2, 22)
    assert g.valide and g.cifre_q0 == (0, 0, 2) and g.cifre_q2 == (2, 1, 1)
    assert g.ritorno == ((0, 1, 2), (0, 2, 1), (1, 2, 0))       # SCD, SDC, CDS
    assert g.permutazione_ritorno[:3] == (1, 2, 0)
    assert g.terza_guida == 15
    assert g.numero_ritorno == 10
    assert [gr.IMPILAMENTO_DI[s] for s in gr.mescolamenti_da_numero(10)] == [
        "DSC", "SDC", "SCD"]                                     # ordini fisici del libro


def test_ritorno_da_mazzi_su_216_e_guide_non_valide():
    rnd = random.Random(3)
    for n in range(216):
        carte = list(range(100, 127))
        rnd.shuffle(carte)                                       # A qualsiasi
        attuale = [None] * N
        for i in range(N):
            attuale[TAVOLA[n][i]] = carte[i]
        g = rc.ritorno_da_mazzi(carte, attuale)
        assert g.valide and g.verifica and g.primo_scarto is None
        assert g.permutazione_ritorno == rc.inversa(TAVOLA[n])
        assert g.numero_andata == n
    g = rc.ritorno_da_guide(0, 1)                                # cifre alte uguali
    assert not g.valide and g.livelli_validi == (False, False, True)
    assert g.ritorno is None and g.terza_guida is None


def test_ritorno_da_mazzi_rileva_una_provenienza_non_garantita():
    carte = list(range(N))
    attuale = list(rc.inversa(TAVOLA[37]))          # mazzo finale della riga 37
    i, j = [pos for pos in range(N) if attuale[pos] not in (0, 26)][:2]
    attuale[i], attuale[j] = attuale[j], attuale[i]   # uno scambio estraneo
    g = rc.ritorno_da_mazzi(carte, attuale)
    assert g.valide                                    # le guide non sono toccate
    assert g.verifica is False and g.primo_scarto in (i, j)


def test_raggiungibilita_uguale_alla_separabilita_relativa():
    rnd = random.Random(12)
    for _ in range(400):
        v = list(range(N))
        rnd.shuffle(v)
        if rnd.random() < 0.5:                                   # w raggiungibile
            T = TAVOLA[rnd.randrange(216)]
            w = [None] * N
            for a in range(N):
                w[T[a]] = v[a]
        else:
            w = list(v)
            rnd.shuffle(w)
        r = rc.raggiungibile(v, w)
        assert r.raggiungibile == rc.separabile(r.relativa).separabile
        if r.raggiungibile:
            assert r.candidato == r.relativa and r.numero == tb.numero_di(r.relativa)
            assert r.posizione_attesa_13 == r.posizione_reale_13


def test_raggiungibilita_controllo_immediato_della_carta_13():
    v = list(range(N))
    w = list(rc.inversa(TAVOLA[50]))
    i, j = w.index(13), w.index(14)                  # la carta 13 fuori posto
    w[i], w[j] = w[j], w[i]
    r = rc.raggiungibile(v, w)
    assert r.guide.valide and not r.raggiungibile
    assert r.posizione_attesa_13 != r.posizione_reale_13


def test_effetto_di_una_permutazione_data():
    p = TAVOLA[100]
    e = rc.effetto(p, 0)
    assert e.immagine == p[0] and p[e.preimmagine] == 0


# ═════════════════════════════════════ A1 ═══════════════════════════════════

def test_a1_note_due_calcola_la_terza():
    ini = [f"c{i}" for i in range(N)]
    T = TAVOLA[100]
    fin = rc.nota_due(iniziale=ini, trasformazione=T)
    assert fin.calcolato == "finale" and fin.legge == "finale_da_iniziale"
    assert all(fin.finale[T[i]] == ini[i] for i in range(N))
    back = rc.nota_due(finale=fin.finale, trasformazione=T)
    assert back.calcolato == "iniziale" and back.iniziale == tuple(ini)
    t = rc.nota_due(iniziale=ini, finale=fin.finale)
    assert t.calcolato == "trasformazione" and t.trasformazione == T
    ok = rc.nota_due(iniziale=ini, finale=fin.finale, trasformazione=T)
    assert ok.calcolato is None and ok.legge == "verifica"
    assert {fin.legge, back.legge, t.legge, ok.legge} == set(rc.LEGGI_A1)


def test_a1_rifiuta():
    with pytest.raises(rc.IngressoNonValido) as e:
        rc.nota_due(iniziale=list(range(N)))
    assert e.value.codice == "a1_dati_insufficienti"
    with pytest.raises(rc.IngressoNonValido) as e:
        rc.nota_due(list(range(N)), list(range(N)), TAVOLA[1])
    assert e.value.codice == "a1_incoerente"
    with pytest.raises(PermutazioneNonValida):
        rc.nota_due(iniziale=list(range(N)), trasformazione=[0] * N)


# ═════════════════════════════ architettura ═════════════════════════════════

def test_il_service_e_puro_e_non_estende_il_linguaggio():
    testo = SORGENTE.read_text(encoding="utf-8")
    for vietato in ("tkinter", "from ..gui", "i18n", "print("):
        assert vietato not in testo
    import gioco27.core.algebra as alg
    assert not hasattr(alg, "taglio") and "taglio" not in alg.__dict__
