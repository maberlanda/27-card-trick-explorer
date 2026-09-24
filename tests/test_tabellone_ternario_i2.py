"""Compartimento I2 — tabellone, livello ternario e flusso delle cifre.

Specifica: V4_PRE_I2_VIEW_DECISIONS.md (decisioni D-I2-1…8 approvate).

Il file ha due parti.

* **Caratterizzazione** — i fatti V1–V11 e i casi F1–F13 del memo, provati
  sul core esistente con oracoli indipendenti: aritmetica diretta, formule
  del libro, simulazione fisica carta per carta (`esegui_partita`), inversa
  per ricerca. Nessuna di queste verifiche passa per il presenter di I2.
* **Contratti del presenter** — `services.tabellone` e le funzioni di parola
  del core, confrontati con gli stessi oracoli.

Convenzioni: T[carta] = posizione finale; T⁻¹[posizione] = carta che la
occupa (il mazzo finale). DP3 = A: il rovesciamento dello stadio i avviene
PRIMA della distribuzione.
"""
import dataclasses
import subprocess
import sys

import pytest

from gioco27.core import gioco_reale as gr
from gioco27.core.dominio import PermutazioneNonValida
from gioco27.services.procedure import (ProceduraGioco, adattamento_fisico,
                                        servizio_procedure)

LETTERE = "SCD"


# ═════════════════════════════ oracoli di test ══════════════════════════════

def _cifre(n):
    """(n2, n1, n0) per divisioni successive, indipendente da digits3."""
    return (n // 9, (n // 3) % 3, n % 3)


def _parola_oracolo(n):
    return "".join(LETTERE[d] for d in _cifre(n))


def _T_fisica(mesc):
    """T[carta] = posizione finale, dalla simulazione carta per carta."""
    deck, _ = gr.esegui_partita(mesc)
    return [deck.index(c) for c in range(27)]


def _mazzo_fisico(mesc):
    deck, _ = gr.esegui_partita(mesc)
    return list(deck)


def _inversa(T):
    return [list(T).index(q) for q in range(27)]


def _comp(a, b):
    return [a[b[i]] for i in range(27)]


def _lettura(righe_alto_basso):
    """Lettura gerarchica: riga alta piu' lenta, bassa piu' rapida (§ 2.4.3)."""
    alto, centro, basso = righe_alto_basso
    return [9 * alto[a] + 3 * centro[b] + basso[c]
            for a in range(3) for b in range(3) for c in range(3)]


def _righe_dirette(mesc):
    """Righe del tabellone dall'alto: fase 3, fase 2, fase 1 (§ 2.4.1)."""
    s1, s2, s3 = mesc
    return [gr.MESCOLAMENTO[s] for s in (s3, s2, s1)]


def _traccia_A(proc, carta):
    """Oracolo DP3 = A dalla sola aritmetica del libro (§ 1.6, § 5.1.5).

    Restituisce, per ogni stadio: (P prima, Q dopo J^e, colonna, P dopo).
    """
    P, passi = carta, []
    for s, e in zip(proc.mescolamenti, proc.rovesciamenti):
        Q = 26 - P if e else P
        dopo = Q // 3 + 9 * gr.MESCOLAMENTO[s][Q % 3]
        passi.append((P, Q, Q % 3, dopo))
        P = dopo
    return passi


# ═══════════════════ CARATTERIZZAZIONE (solo core esistente) ════════════════

def test_v1_numero_cifre_numero():
    assert sum(9 * a + 3 * b + c == n and gr.digits3(n) == _cifre(n)
               for n in range(27)
               for a, b, c in [gr.digits3(n)]) == 27


def test_v3_v4_v5_tabellone_diretto_contro_la_fisica():
    lette = colonne = celle = 0
    for n in range(216):
        riga = gr.riga_tavola(n)
        T = _T_fisica(riga["mescolamenti"])
        righe = _righe_dirette(riga["mescolamenti"])
        lette += _lettura(righe) == T == list(riga["T"])
        colonne += ([9 * righe[0][d] + 3 * righe[1][d] + righe[2][d]
                     for d in range(3)] == [T[0], T[13], T[26]]
                    == list(riga["assi"]))
        for x in range(27):
            a, b, c = _cifre(x)
            celle += 9 * righe[0][a] + 3 * righe[1][b] + righe[2][c] == T[x]
    assert (lette, colonne, celle) == (216, 216, 5832)


def test_v6_tabellone_inverso_e_il_mazzo_finale():
    esatti = 0
    for n in range(216):
        riga = gr.riga_tavola(n)
        inverse = [gr.MESCOLAMENTO[gr.IMPILAMENTO_DI[s]]
                   for s in reversed(riga["mescolamenti"])]
        mazzo = _mazzo_fisico(riga["mescolamenti"])
        esatti += (_lettura(inverse) == mazzo == _inversa(riga["T"])
                   == list(riga["T_inv"]))
    assert esatti == 216


def test_diretto_e_inverso_coincidono_solo_se_auto_inversa():
    coincidenti = [n for n in range(216)
                   if gr.riga_tavola(n)["T"] == gr.riga_tavola(n)["T_inv"]]
    assert len(coincidenti) == 64
    assert 78 in coincidenti and 56 not in coincidenti


def test_v8b_le_scorciatoie_sbagliate_del_ritorno():
    solo_ordine = ordine_e_sigle = stesso_ordine_sigle_inverse = 0
    for n in range(216):
        riga = gr.riga_tavola(n)
        s1, s2, s3 = riga["mescolamenti"]
        Tinv = _inversa(_T_fisica(riga["mescolamenti"]))
        inv = gr.IMPILAMENTO_DI
        solo_ordine += _T_fisica((s3, s2, s1)) == Tinv
        ordine_e_sigle += _T_fisica((inv[s3], inv[s2], inv[s1])) == Tinv
        stesso_ordine_sigle_inverse += _T_fisica((inv[s1], inv[s2], inv[s3])) == Tinv
    assert (solo_ordine, ordine_e_sigle, stesso_ordine_sigle_inverse) == (24, 36, 216)


def test_v9_v10_macchina_che_dimentica_sulla_traccia_fisica():
    storia = ricorrenza = registro = 0
    for n in range(216):
        mesc = gr.mescolamenti_da_numero(n)
        _, fasi = gr.esegui_partita(mesc)
        colonne = [f["cols"] for f in fasi if f["tipo"] == "colonne"]
        mazzi = [f["deck"] for f in fasi if f["tipo"] == "raccolta"]
        for c in range(27):
            n2, n1, n0 = _cifre(c)
            osservate = tuple(next(g for g in range(3) if c in colonne[k][g])
                              for k in range(3))
            storia += osservate == (n0, n1, n2)
            P, ok, reg, s = c, True, [(n2, n1, n0)], []
            for k in range(3):
                s.append(gr.MESCOLAMENTO[mesc[k]][P % 3])
                P = P // 3 + 9 * s[-1]
                ok &= mazzi[k].index(c) == P
                reg.append(_cifre(P))
            ricorrenza += ok
            registro += reg == [(n2, n1, n0), (s[0], n2, n1), (s[1], s[0], n2),
                                (s[2], s[1], s[0])]
    assert (storia, ricorrenza, registro) == (5832, 5832, 5832)


def test_v11_flusso_con_rovesciamenti_canonici():
    servizio = servizio_procedure()
    finali = intermedi = colonne = corretta = letterale = 0
    for p in servizio.procedure:
        a = adattamento_fisico(p)
        _, fasi = gr.esegui_partita(a.mescolamenti, a.rovesciamenti_dopo_raccolta)
        cols = [f["cols"] for f in fasi if f["tipo"] == "colonne"]
        mazzi = [f["deck"] for f in fasi if f["tipo"] == "raccolta"]
        T = servizio.trasformazione(p)
        e = p.rovesciamenti
        for c in range(27):
            passi = _traccia_A(p, c)
            cb = 26 - c if a.rovescia_mazzo_iniziale else c
            finali += passi[-1][3] == T[c]
            ok = True
            for k, (_, _, col, dopo) in enumerate(passi):
                reg = mazzi[k].index(cb)
                ok &= dopo == (26 - reg if k < 2 and e[k + 1] else reg)
                colonne += next(g for g in range(3) if cb in cols[k][g]) == col
            intermedi += ok
            origine = _cifre(c)[::-1]                       # (n0, n1, n2)
            storia = [x[2] for x in passi]
            corretta += storia == [2 - origine[k] if sum(e[:k + 1]) % 2
                                   else origine[k] for k in range(3)]
            letterale += storia == list(origine)
    assert (finali, intermedi, colonne) == (46656, 46656, 139968)
    assert corretta == 46656
    assert letterale == 13824


# ─────────────────────────── casi fissi (fonte) ─────────────────────────────

def test_f3_f4_f7_f9_f12_f13_righe_della_tavola():
    assert gr.riga_tavola(78)["mescolamenti"] == ("SCD", "SDC", "CSD")
    assert gr.riga_tavola(78)["assi"] == (9, 7, 23)
    assert gr.riga_tavola(78)["autoinversa"]
    assert gr.riga_tavola(56)["assi"] == (7, 18, 14)
    assert gr.riga_tavola(62)["assi"] == (4, 24, 11)
    assert gr.riga_tavola(56)["T"] == gr.riga_tavola(62)["T_inv"]
    assert not gr.riga_tavola(56)["autoinversa"]
    # § 2.4.5: il mazzo dell'esecuzione corretta di #56
    assert _mazzo_fisico(("CSD", "DSC", "SDC"))[:9] == [4, 3, 5, 7, 6, 8, 1, 0, 2]
    T100 = gr.riga_tavola(100)["T"]
    assert gr.riga_tavola(100)["assi"] == (13, 8, 18)
    assert T100[10] == 5 and T100.index(10) == 6
    assert gr.riga_tavola(91)["T"][:3] == [15, 17, 16]
    assert gr.riga_tavola(82)["assi"] == (10, 8, 21)
    assert gr.riga_tavola(0)["T"] == list(range(27))


def test_f5_tabella_del_paragrafo_4_9_1():
    T = _T_fisica(("SDC", "CSD", "DCS"))
    assert gr.numero_tavola(("SDC", "CSD", "DCS")) == 193
    assert T == [21, 23, 22, 18, 20, 19, 24, 26, 25, 12, 14, 13, 9, 11, 10,
                 15, 17, 16, 3, 5, 4, 0, 2, 1, 6, 8, 7]
    assert T[1] == 23


def test_f6_ritorno_del_paragrafo_4_10_1():
    assert gr.numero_tavola(("DSC", "DCS", "CDS")) == 177
    assert gr.numero_tavola(("CDS", "DCS", "DSC")) == 142
    T, Q = _T_fisica(("DSC", "DCS", "CDS")), _T_fisica(("CDS", "DCS", "DSC"))
    assert T[10] == 24 and Q[24] == 10
    assert _comp(Q, T) == list(range(27))


def test_f10_f11_rovesciamenti_canonici():
    servizio = servizio_procedure()
    T = servizio.trasformazione(ProceduraGioco(("SCD", "DCS", "SCD"), (0, 0, 1)))
    assert (T[0], T[13], T[26]) == (20, 13, 6)
    assert list(T) == gr.riga_tavola(185)["T"]
    csd = ("CSD", "CSD", "CSD")
    a = servizio.trasformazione(ProceduraGioco(csd, (1, 0, 0)))
    b = servizio.trasformazione(ProceduraGioco(csd, (0, 1, 0)))
    assert (a[0], a[13], a[26]) == (26, 0, 13)
    assert (b[0], b[13], b[26]) == (25, 2, 12)


# ═══════════════════ CONTRATTI: numero ↔ cifre ↔ parola (core) ═════════════

def test_v2_parola_e_inversa_27_su_27():
    assert sum(gr.parola(n) == _parola_oracolo(n)
               and gr.posizione_da_parola(_parola_oracolo(n)) == n
               for n in range(27)) == 27


def test_f1_f2_parole_indirizzo_del_libro():
    assert gr.parola(19) == "DSC" and gr.digits3(19) == (2, 0, 1)
    assert gr.posizione_da_parola("DSC") == 19
    assert (gr.parola(0), gr.parola(13), gr.parola(26)) == ("SSS", "CCC", "DDD")
    assert [gr.posizione_da_parola(w) for w in ("SCD", "DSC", "CDS")] == [5, 19, 15]


def test_ordine_numerico_e_lessicografico_con_S_C_D():
    parole = [gr.parola(n) for n in range(27)]
    assert parole == sorted(parole, key=lambda w: [LETTERE.index(x) for x in w])


@pytest.mark.parametrize("valore", [-1, 27, True, 1.0, "3", None])
def test_parola_rifiuta_posizioni_non_valide(valore):
    with pytest.raises(ValueError):
        gr.parola(valore)


@pytest.mark.parametrize("valore", ["dsc", "DS", "DSCC", "DXC", "", 19, None,
                                    ("D", "S", "C")])
def test_posizione_da_parola_rifiuta_parole_non_valide(valore):
    with pytest.raises(ValueError):
        gr.posizione_da_parola(valore)


def test_num_to_sector_delega_con_uscita_invariata():
    from gioco27.core import detail
    atteso = ["".join("scd"[d] for d in _cifre(n)) for n in range(27)]
    assert [detail.num_to_sector(n) for n in range(27)] == atteso
    assert detail.num_to_sector(0) == "sss" and detail.num_to_sector(19) == "dsc"


def test_una_sola_conversione_nel_core():
    """Presenter e GUI non riscrivono numero → parola (D-I2-4).

    Chiamare una cifra per nome («colonna 1 = C») resta lecito: e' la
    conversione di una posizione intera in tre lettere che ha un solo padrone.
    """
    import pathlib
    import re
    radice = pathlib.Path(__file__).resolve().parents[1] / "gioco27"
    vietati = re.compile(r"join\(.*digits3|_SECT\s*=|num_to_sector\(")
    sospetti = []
    for f in list((radice / "services").glob("*.py")) + list((radice / "gui").glob("*.py")):
        for riga in f.read_text(encoding="utf-8").splitlines():
            if vietati.search(riga):
                sospetti.append(f"{f.name}: {riga.strip()}")
    assert sospetti == []


# ═══════════════════ CONTRATTI: presenter services.tabellone ════════════════

from gioco27.services import tabellone as tb  # noqa: E402


def test_il_presenter_e_puro():
    codice = ("import sys; import gioco27.services.tabellone as t; "
              "t.tabellone(100); t.flusso_carta(t.realizza(list(range(27))), 5); "
              "print(any(k == 'tkinter' or k.startswith('gioco27.gui') "
              "for k in sys.modules))")
    out = subprocess.run([sys.executable, "-c", codice], capture_output=True,
                         text=True, check=True).stdout.strip()
    assert out == "False"


def test_i_modelli_sono_congelati():
    t = tb.tabellone(100)
    with pytest.raises(dataclasses.FrozenInstanceError):
        t.numero = 1
    assert isinstance(t.destinazioni, tuple) and isinstance(t.righe, tuple)


def test_cronologia_e_griglia_sono_ordini_separati():
    t = tb.tabellone(100)                       # (CDS, CDS, CSD)
    assert [f.fase for f in t.cronologia] == [1, 2, 3]
    assert [f.mescolamento for f in t.cronologia] == ["CDS", "CDS", "CSD"]
    assert [f.impilamento for f in t.cronologia] == ["DSC", "DSC", "CSD"]
    assert [(r.fase, r.peso, r.indice_cifra) for r in t.righe] == \
        [(3, 9, 2), (2, 3, 1), (1, 1, 0)]
    assert [r.sigla for r in t.righe] == ["CSD", "CDS", "CDS"]
    # inverso: stesso ordine delle fasi, sigle inverse (CDS <-> DSC)
    assert [(r.fase, r.sigla) for r in t.righe_inverse] == \
        [(3, "CSD"), (2, "DSC"), (1, "DSC")]


def test_v3_v4_v5_v6_tramite_il_presenter():
    lette = colonne = inverse = celle = 0
    for n in range(216):
        t = tb.tabellone(n)
        mesc = gr.mescolamenti_da_numero(n)
        T, mazzo = _T_fisica(mesc), _mazzo_fisico(mesc)
        lette += _lettura([r.valori for r in t.righe]) == T == list(t.destinazioni)
        inverse += (_lettura([r.valori for r in t.righe_inverse]) == mazzo
                    == list(t.mazzo_finale))
        colonne += ([(c.colonna, c.carta, c.posizione) for c in t.colonne_assi]
                    == [(0, 0, T[0]), (1, 13, T[13]), (2, 26, T[26])])
        colonne += ([(c.colonna, c.posizione, c.carta) for c in t.colonne_inverse]
                    == [(0, 0, mazzo[0]), (1, 13, mazzo[13]), (2, 26, mazzo[26])])
        assert t.autoinversa == (T == mazzo)
        for x in range(27):
            lettura = tb.lettura_cifre(n, x)
            celle += lettura.destinazione == T[x]
            for az in lettura.azioni:
                riga = t.righe[az.riga_visiva]
                assert (riga.fase, riga.indice_cifra) == (az.fase, az.indice_cifra)
                assert riga.valori[az.cifra_iniziale] == az.cifra_finale
    assert (lette, inverse, colonne, celle) == (216, 216, 432, 5832)


def test_T_e_mazzo_finale_non_si_confondono():
    t56 = tb.tabellone(56)
    assert t56.destinazioni[:9] == (7, 6, 8, 1, 0, 2, 4, 3, 5)
    assert t56.mazzo_finale[:9] == (4, 3, 5, 7, 6, 8, 1, 0, 2)
    assert not t56.autoinversa
    t78 = tb.tabellone(78)
    assert t78.autoinversa and t78.destinazioni == t78.mazzo_finale
    campi = {f.name for f in dataclasses.fields(t56)}
    assert "configurazione_finale" not in campi


def test_lettura_cifre_del_paragrafo_7_1_2():
    lettura = tb.lettura_cifre(100, 10)
    assert lettura.cifre_iniziali == (1, 0, 1)
    assert [(a.fase, a.peso, a.cifra_iniziale, a.cifra_finale)
            for a in lettura.azioni] == [(3, 9, 1, 0), (2, 3, 0, 1), (1, 1, 1, 2)]
    assert lettura.cifre_finali == (0, 1, 2) and lettura.destinazione == 5
    assert lettura.celle == ((0, 1), (1, 0), (2, 1))
    assert (lettura.parola_iniziale, lettura.parola_finale) == ("CSC", "SCD")


def test_f5_tabella_delle_27_posizioni():
    righe = tb.tabella_posizioni(193)
    assert len(righe) == 27 and [r.carta for r in righe] == list(range(27))
    assert righe[1].cifre_iniziali == (0, 0, 1)
    assert righe[1].cifre_finali == (2, 1, 2) and righe[1].destinazione == 23
    assert [r.destinazione for r in righe] == _T_fisica(("SDC", "CSD", "DCS"))
    assert righe[19] == tb.lettura_cifre(193, 19)


def test_v7_realizza_senza_nuovo_solutore(monkeypatch):
    from gioco27.services import procedure as sp

    def vietato(*a, **k):
        raise AssertionError("(R) non deve usare un solutore")
    monkeypatch.setattr(gr, "risolvi_trucco", vietato)
    monkeypatch.setattr(sp.ServizioProcedure, "procedura_sicura", vietato)
    monkeypatch.setattr(sp.ServizioProcedure, "procedura_storica", vietato)
    esatte = 0
    for n in range(216):
        riga = gr.riga_tavola(n)
        p = tb.realizza(riga["T"])
        esatte += (p.semplice and p.numero_tavola == n
                   and p.mescolamenti == riga["mescolamenti"]
                   and _T_fisica(p.mescolamenti) == list(riga["T"])
                   and gr.tabellone_da_assi(*riga["assi"])[0] == p.mescolamenti)
    assert esatte == 216


def test_realizza_su_T_con_rovesciamenti_e_fuori_dominio():
    from gioco27.services.procedure import TrasformazioneFuoriDominio
    T = servizio_procedure().trasformazione(
        ProceduraGioco(("SCD", "DCS", "SCD"), (0, 0, 1)))
    assert tb.realizza(T).numero_tavola == 185               # F10
    scambio = list(range(27))
    scambio[0], scambio[1] = 1, 0
    with pytest.raises(TrasformazioneFuoriDominio):
        tb.realizza(scambio)
    with pytest.raises(PermutazioneNonValida):
        tb.realizza([0] * 27)


def test_v8_ritorno():
    esatti = 0
    for n in range(216):
        riga = gr.riga_tavola(n)
        q = tb.ritorno(n)
        T, Q = _T_fisica(riga["mescolamenti"]), _T_fisica(q.mescolamenti)
        esatti += (q.semplice and Q == _inversa(T)
                   and _comp(Q, T) == list(range(27))
                   and _comp(T, Q) == list(range(27))
                   and q.mescolamenti == riga["impilamenti"])
    assert esatti == 216


def test_f6_f7_ritorni_del_libro():
    assert tb.ritorno(100).numero_tavola == 93
    assert tb.ritorno(100).mescolamenti == ("DSC", "DSC", "CSD")
    assert tb.ritorno(56).numero_tavola == 62
    assert tb.ritorno(177).numero_tavola == 142
    assert [tb.ritorno(n).numero_tavola for n in (78, 193, 0)] == [78, 193, 0]


def test_v9_v10_flusso_del_presenter_senza_rovesciamenti():
    storia = ricorrenza = registro = 0
    for n in range(216):
        p = ProceduraGioco.da_identificatore(n, 0)
        for flusso in tb.flussi_procedura(p):
            c = flusso.carta
            n2, n1, n0 = _cifre(c)
            storia += flusso.storia_distribuzioni == (n0, n1, n2)
            ok = all(ps.posizione_dopo == ps.posizione_prima // 3
                     + 9 * ps.destinazione_blocco for ps in flusso.passi)
            ricorrenza += ok and flusso.posizione_finale == _T_fisica(p.mescolamenti)[c]
            s = flusso.storia_raccolte
            registro += [flusso.passi[0].cifre_prima] + \
                [ps.cifre_dopo for ps in flusso.passi] == \
                [(n2, n1, n0), (s[0], n2, n1), (s[1], s[0], n2), (s[2], s[1], s[0])]
    assert (storia, ricorrenza, registro) == (5832, 5832, 5832)


def test_v11_flusso_del_presenter_con_rovesciamenti():
    servizio = servizio_procedure()
    finali = intermedi = colonne = corretta = letterale = 0
    for p in servizio.procedure:
        T = servizio.trasformazione(p)
        for flusso in tb.flussi_procedura(p):
            c = flusso.carta
            oracolo = _traccia_A(p, c)
            finali += flusso.posizione_finale == T[c]
            intermedi += all(
                (ps.posizione_prima, ps.posizione_distribuita, ps.posizione_dopo)
                == (o[0], o[1], o[3]) for ps, o in zip(flusso.passi, oracolo))
            colonne += sum(ps.colonna == o[2] and ps.cifra_uscente == o[2]
                           for ps, o in zip(flusso.passi, oracolo))
            origine = _cifre(c)[::-1]
            e = p.rovesciamenti
            corretta += flusso.storia_distribuzioni == tuple(
                2 - origine[k] if sum(e[:k + 1]) % 2 else origine[k]
                for k in range(3))
            corretta_flag = all(ps.complementata == bool(sum(e[:k + 1]) % 2)
                                for k, ps in enumerate(flusso.passi))
            assert corretta_flag
            letterale += flusso.storia_distribuzioni == flusso.cifre_origine_nel_tempo
    assert (finali, intermedi, colonne) == (46656, 46656, 139968)
    assert corretta == 46656 and letterale == 13824


def test_f8_macchina_che_dimentica_carta_19_in_100():
    f = tb.flusso_carta(ProceduraGioco.da_identificatore(100, 0), 19)
    assert f.parola_iniziale == "DSC"
    assert [f.cifre_iniziali] + [ps.cifre_dopo for ps in f.passi] == \
        [(2, 0, 1), (2, 2, 0), (1, 2, 2), (2, 1, 2)]
    assert f.posizione_finale == 23
    assert f.storia_distribuzioni == (1, 0, 2)
    assert [(ps.cifra_uscente, ps.cifra_entrante) for ps in f.passi] == \
        [(1, 2), (0, 1), (2, 2)]
    assert [ps.altezza for ps in f.passi] == [6, 8, 5]
    assert all(ps.rovesciamento == 0 and ps.posizione_distribuita == ps.posizione_prima
               for ps in f.passi)


def test_f10_flusso_con_rovesciamento_canonico():
    p = ProceduraGioco(("SCD", "DCS", "SCD"), (0, 0, 1))
    f = tb.flusso_carta(p, 0)
    assert f.posizione_finale == 20
    terzo = f.passi[2]
    assert terzo.rovesciamento == 1
    assert terzo.posizione_distribuita == 26 - terzo.posizione_prima
    assert terzo.cifre_distribuite == tuple(2 - d for d in terzo.cifre_prima)
    assert [ps.complementata for ps in f.passi] == [False, False, True]


def test_validazione_del_presenter():
    with pytest.raises(ValueError):
        tb.tabellone(216)
    with pytest.raises(ValueError):
        tb.lettura_cifre(0, 27)
    with pytest.raises(ValueError):
        tb.flusso_carta(ProceduraGioco.da_identificatore(0, 0), -1)
    with pytest.raises(ValueError):
        tb.ritorno(-1)


def test_nessun_elenco_delle_procedure_equivalenti():
    """DP11 aperta: il presenter non espone le 8 procedure di una classe."""
    pubblici = [n for n in dir(tb) if not n.startswith("_")]
    assert not [n for n in pubblici if "classe" in n or "fibra" in n
                or "equivalent" in n]


def test_parole_nei_passi_e_disposizione_realizzata():
    p = ProceduraGioco(("SCD", "DCS", "SCD"), (0, 0, 1))
    f = tb.flusso_carta(p, 19)
    for ps in f.passi:
        assert ps.parola_prima == gr.parola(ps.posizione_prima)
        assert ps.parola_distribuita == gr.parola(ps.posizione_distribuita)
        assert ps.parola_dopo == gr.parola(ps.posizione_dopo)
        assert ps.lettera_colonna == LETTERE[ps.colonna]
    assert tb.disposizione_realizzata(p) == 185
    assert tb.disposizione_realizzata(ProceduraGioco.da_identificatore(100, 0)) == 100
