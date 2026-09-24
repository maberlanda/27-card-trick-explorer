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
from gioco27.core import gioco_reale as gr
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
