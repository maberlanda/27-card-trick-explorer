"""Compartimento I3 — errori fisici, conseguenze e recupero.

Catalogo autorevole: V4_MATHEMATICAL_DIDACTIC_COVERAGE_AUDIT.md § 14.3
(E1–E6). Decisioni D-I3-1…7 del prompt di I3.

Prima parte — **caratterizzazione**: i fatti fisici provati con un oracolo
diretto scritto qui (distribuzione e raccolta del core, inversione dei
mazzetti e del mazzo fatte a mano), senza il service di I3.
Seconda parte — contratti del service `services.errori`.

Convenzioni: T[carta] = posizione finale; cifre (n2, n1, n0); la fase k
scrive la cifra di livello k−1 (fase 1 → n0, fase 3 → n2).
"""
from gioco27.core import gioco_reale as gr

RIGHE = {tuple(gr.riga_tavola(n)["T"]): n for n in range(216)}


# ═════════════════════════════ oracoli diretti ══════════════════════════════

def _cifre(n):
    return (n // 9, (n // 3) % 3, n % 3)


def _esegui(eseguiti, e2=(), e3=()):
    """Una sola sequenza fisica sull'intero mazzo; restituisce (T, mazzo).

    `eseguiti` sono i mescolamenti realmente compiuti (gia' con E1/E4/E5);
    e3: fasi in cui ogni mazzetto e' invertito dopo la distribuzione;
    e2: fasi dopo la cui raccolta il mazzo intero e' rovesciato.
    """
    deck = list(range(27))
    for k, s in enumerate(eseguiti, 1):
        cols = gr.distribuisci(deck)
        if k in e3:
            cols = [list(reversed(c)) for c in cols]
        deck = gr.raccogli(cols, s)
        if k in e2:
            deck = list(reversed(deck))
    return tuple(deck.index(c) for c in range(27)), tuple(deck)


def _cambiate(a, b):
    return tuple(i for i, (x, y) in zip((2, 1, 0), zip(_cifre(a), _cifre(b)))
                 if x != y)


# ═══════════════════ CARATTERIZZAZIONE (solo core esistente) ════════════════

def test_la_regola_per_fase_e_quella_di_risolvi_trucco():
    """mescolamento_per_colonna ripete la scelta di risolvi_trucco (729 × 3)."""
    uguali = 0
    for c in range(27):
        for t in range(27):
            piano = gr.risolvi_trucco(c, t)
            cifre = _cifre(t)[::-1]                     # (b0, b1, b2)
            uguali += all(gr.mescolamento_per_colonna(col, cifre[k]) == s
                          for k, (col, s) in enumerate(zip(piano["colonne"],
                                                           piano["mescolamenti"])))
    assert uguali == 729


def test_e1_casi_dell_audit():
    piano = ("DSC", "SCD", "DSC")
    assert gr.numero_tavola(piano) == 111
    assert _esegui(piano)[0][0] == 20
    # E1 alla fase 1: si impila DSC, cioe' si esegue la sua inversa CDS
    T, _ = _esegui(("CDS", "SCD", "DSC"))
    assert T[0] == 19 and RIGHE[T] == 112
    T, _ = _esegui(("DSC", "SCD", "CDS"))
    assert T[0] == 11 and RIGHE[T] == 147


def test_e1_esaustivo_localizza_la_cifra_della_fase():
    casi = localizzati = 0
    for n in range(216):
        piano = gr.mescolamenti_da_numero(n)
        T0, _ = _esegui(piano)
        for k, s in enumerate(piano, 1):
            if gr.IMPILAMENTO_DI[s] == s:
                continue                                  # E1 solo CDS/DSC
            eseguiti = list(piano)
            eseguiti[k - 1] = gr.IMPILAMENTO_DI[s]
            T, _ = _esegui(tuple(eseguiti))
            assert T in RIGHE
            casi += 1
            localizzati += all(_cambiate(T[c], T0[c]) in ((), (k - 1,))
                               for c in range(27))
    assert casi == 216 and localizzati == casi


def test_e2_e3_casi_dell_audit_e_periodi():
    piano = ("CSD", "CSD", "CSD")
    assert gr.periodo(list(_esegui(piano)[0])) == 2
    for k, attesa in ((1, 25), (2, 22), (3, 13)):
        t2, _ = _esegui(piano, e2=(k,))
        t3, _ = _esegui(piano, e3=(k,))
        assert t2[0] == attesa and t3[0] == attesa
        assert gr.periodo(list(t2)) == 3 and gr.periodo(list(t3)) == 6
        assert t2 in RIGHE and t3 in RIGHE
    t_finale, _ = _esegui(piano, e2=(3,))
    assert t_finale != _esegui(piano)[0]                 # carta in 13, T diversa


def test_e2_esaustivo_e_fase_3_uguale_a_J_dopo_T():
    casi = in_tavola = finale_J = 0
    for n in range(216):
        piano = gr.mescolamenti_da_numero(n)
        T0, _ = _esegui(piano)
        for k in (1, 2, 3):
            T, _ = _esegui(piano, e2=(k,))
            casi += 27
            in_tavola += 27 * (T in RIGHE)
            if k == 3:
                finale_J += all(T[c] == 26 - T0[c] for c in range(27))
    assert (casi, in_tavola, finale_J) == (17496, 17496, 216)   # 216 × 3 × 27


def test_e3_esaustivo_resta_nella_tavola():
    assert sum(_esegui(gr.mescolamenti_da_numero(n), e3=(k,))[0] in RIGHE
               for n in range(216) for k in (1, 2, 3)) == 648


def test_e2_e3_possono_cambiare_piu_cifre():
    """L'audit («una sola cifra») vale per E1/E4/E5, non per E2/E3."""
    massimo = {2: 0, 3: 0}
    for n in range(216):
        piano = gr.mescolamenti_da_numero(n)
        T0, _ = _esegui(piano)
        for k in (1, 2, 3):
            for tipo, T in ((2, _esegui(piano, e2=(k,))[0]),
                            (3, _esegui(piano, e3=(k,))[0])):
                massimo[tipo] = max(massimo[tipo],
                                    max(len(_cambiate(T[c], T0[c]))
                                        for c in range(27)))
    assert massimo == {2: 3, 3: 2}


def test_e4_caso_dell_audit():
    """0 → 13, colonna indicata sbagliata alla fase 1: SCD e carta in 12."""
    piano = gr.risolvi_trucco(0, 13)["mescolamenti"]
    assert piano == ("CSD", "CSD", "CSD")
    reale = 0                                             # la carta 0 e' in S
    indicata = 1                                          # l'esecutore crede C
    scelta = gr.mescolamento_per_colonna(indicata, 1)     # b0 di 13 = 1
    assert scelta == "SCD"
    T, _ = _esegui((scelta, "CSD", "CSD"))
    assert T[0] == 12
    assert reale != indicata


def test_e4_esaustivo_sulle_729_coppie():
    casi = localizzati = 0
    for c in range(27):
        for t in range(27):
            piano = gr.risolvi_trucco(c, t)
            T0, _ = _esegui(piano["mescolamenti"])
            cifre = _cifre(t)[::-1]
            for k in (1, 2, 3):
                reale = piano["colonne"][k - 1]
                for indicata in range(3):
                    if indicata == reale:
                        continue
                    eseguiti = list(piano["mescolamenti"])
                    eseguiti[k - 1] = gr.mescolamento_per_colonna(indicata,
                                                                   cifre[k - 1])
                    T, _ = _esegui(tuple(eseguiti))
                    casi += 1
                    localizzati += _cambiate(T[c], T0[c]) in ((), (k - 1,))
    assert casi == 729 * 3 * 2 and localizzati == casi


def test_e5_esaustivo_impilamenti_alternativi():
    casi = localizzati = in_tavola = 0
    for n in range(216):
        piano = gr.mescolamenti_da_numero(n)
        T0, _ = _esegui(piano)
        for k, s in enumerate(piano, 1):
            corretto = gr.IMPILAMENTO_DI[s]
            for imp in gr.SIGLE:
                if imp == corretto or (imp == s and gr.IMPILAMENTO_DI[s] != s):
                    continue                              # corretto o E1
                eseguiti = list(piano)
                eseguiti[k - 1] = gr.IMPILAMENTO_DI[imp]  # impilare imp esegue inv(imp)
                T, _ = _esegui(tuple(eseguiti))
                casi += 1
                in_tavola += T in RIGHE
                localizzati += all(_cambiate(T[c], T0[c]) in ((), (k - 1,))
                                   for c in range(27))
    assert casi == 216 * 3 * 5 - 216        # 5 alternative, meno i 216 casi E1
    assert in_tavola == casi and localizzati == casi


def test_e6_traslazioni_mod_27():
    """Il taglio (traslazione) resta fuori dalla Tavola, tranne k = 9 e 18.

    Il fatto misurato restringe l'audit («esce da G»): C_9 e C_18 agiscono
    solo sulla cifra n2 (n2 → n2 + 1 mod 3) e sono disposizioni della Tavola.
    """
    dentro = [k for k in range(1, 27)
              if tuple((i + k) % 27 for i in range(27)) in RIGHE]
    assert dentro == [9, 18]


# ═══════════════════ CONTRATTI: service services.errori ═════════════════════

import dataclasses  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

import pytest  # noqa: E402

from gioco27.services import errori as er  # noqa: E402

G = er.GestiFase
OK = G()


def _gesti(**per_fase):
    """_gesti(f1=G(...), f3=G(...)) → tre GestiFase, corretti dove non dati."""
    return tuple(per_fase.get(f"f{k}", OK) for k in (1, 2, 3))


def test_il_service_e_puro():
    codice = ("import sys; import gioco27.services.errori as e; "
              "s = e.SessioneErrori.da_trucco(0, 13); e.esegui(s, (e.GestiFase(),)*3); "
              "print(any(k == 'tkinter' or k.startswith('gioco27.gui') for k in sys.modules))")
    out = subprocess.run([sys.executable, "-c", codice], capture_output=True,
                         text=True, check=True).stdout.strip()
    assert out == "False"
    sorgente = (__import__("pathlib").Path(er.__file__)).read_text(encoding="utf-8")
    for narrativo in ("Seldon", "Giullare", "Gaia", "Cronaca"):
        assert narrativo not in sorgente


def test_catalogo_e1_e6():
    assert [t.value for t in er.TipoErrore] == ["E1", "E2", "E3", "E4", "E5", "E6"]
    for t in er.TipoErrore:
        voce = er.CATALOGO[t]
        assert voce.tipo is t
        assert voce.simulato == (t is not er.TipoErrore.E6)
    assert er.CATALOGO[er.TipoErrore.E6].fasi == ()
    assert not er.CATALOGO[er.TipoErrore.E6].resta_nella_tavola
    assert all(er.CATALOGO[t].resta_nella_tavola for t in er.TipoErrore
               if t is not er.TipoErrore.E6)
    assert not hasattr(er, "taglio") and not hasattr(er, "esegui_taglio")


def test_senza_errori_la_traccia_coincide_col_piano():
    s = er.SessioneErrori.da_trucco(0, 13)
    tr_ = er.esegui(s, _gesti())
    assert tr_.eventi == ()
    assert tr_.T_eseguita == _esegui(s.mescolamenti)[0]
    c = er.confronta(tr_)
    assert c.stessa_trasformazione and c.bersaglio_raggiunto and c.cifre_cambiate == ()
    assert c.numero_previsto == c.numero_eseguito == 86


def test_e1_via_service():
    s = er.SessioneErrori.da_trucco(0, 20)
    assert s.mescolamenti == ("DSC", "SCD", "DSC")
    for fase, attesa, riga in ((1, 19, 112), (3, 11, 147)):
        tr_ = er.esegui(s, _gesti(**{f"f{fase}": G(impilamento="DSC")}))
        assert [e.tipo for e in tr_.eventi] == [er.TipoErrore.E1]
        assert tr_.eventi[0].fase == fase
        c = er.confronta(tr_)
        assert c.posizione_eseguita == attesa and c.numero_eseguito == riga
        assert c.cifre_cambiate == (fase - 1,)
        assert not c.bersaglio_raggiunto and not c.stessa_trasformazione


def test_e1_solo_per_cds_dsc():
    s = er.SessioneErrori.da_trucco(0, 13)                  # CSD CSD CSD
    tr_ = er.esegui(s, _gesti(f1=G(impilamento="CSD")))     # e' quello corretto
    assert tr_.eventi == ()
    tr_ = er.esegui(s, _gesti(f1=G(impilamento="SCD")))
    assert [e.tipo for e in tr_.eventi] == [er.TipoErrore.E5]


def test_e2_fase_3_carta_al_bersaglio_ma_T_diversa():
    s = er.SessioneErrori.da_trucco(0, 13)
    for fase, attesa in ((1, 25), (2, 22), (3, 13)):
        tr_ = er.esegui(s, _gesti(**{f"f{fase}": G(rovesciamento_dopo=True)}))
        assert tr_.posizione_carta == attesa
        assert [e.tipo for e in tr_.eventi] == [er.TipoErrore.E2]
    c = er.confronta(er.esegui(s, _gesti(f3=G(rovesciamento_dopo=True))))
    assert c.bersaglio_raggiunto and c.stesso_effetto_carta
    assert not c.stessa_trasformazione
    assert c.numero_eseguito == 172 and c.numero_previsto == 86
    assert c.T_eseguita == tuple(26 - x for x in c.T_prevista)     # J ∘ T


def test_e3_via_service_e_periodo():
    s = er.SessioneErrori.da_trucco(0, 13)
    for fase, attesa in ((1, 25), (2, 22), (3, 13)):
        tr_ = er.esegui(s, _gesti(**{f"f{fase}": G(ordine_interno_invertito=True)}))
        assert tr_.posizione_carta == attesa
        assert gr.periodo(list(tr_.T_eseguita)) == 6
        assert [e.tipo for e in tr_.eventi] == [er.TipoErrore.E3]


def test_e4_via_service():
    s = er.SessioneErrori.da_trucco(0, 13)
    tr_ = er.esegui(s, _gesti(f1=G(colonna_indicata=1)))
    passo = tr_.passi[0]
    assert (passo.colonna_reale, passo.colonna_indicata) == (0, 1)
    assert passo.mescolamento_previsto == "CSD"
    assert passo.mescolamento_inteso == "SCD"
    assert passo.mescolamento_eseguito == "SCD"
    assert tr_.posizione_carta == 12
    assert [e.tipo for e in tr_.eventi] == [er.TipoErrore.E4]


def test_e4_in_un_piano_fissato_non_cambia_la_scelta():
    s = er.SessioneErrori.da_disposizione(86, 0)
    assert not s.guidata_dal_bersaglio and s.bersaglio == 13
    tr_ = er.esegui(s, _gesti(f1=G(colonna_indicata=1)))
    assert [e.tipo for e in tr_.eventi] == [er.TipoErrore.E4]
    assert tr_.passi[0].mescolamento_eseguito == "CSD" and tr_.posizione_carta == 13


def test_e2_e3_esaustivi_contro_l_oracolo():
    uguali = 0
    for n in range(216):
        s = er.SessioneErrori.da_disposizione(n, 0)
        for k in (1, 2, 3):
            for chiave, kw in (("e2", "rovesciamento_dopo"),
                               ("e3", "ordine_interno_invertito")):
                tr_ = er.esegui(s, _gesti(**{f"f{k}": G(**{kw: True})}))
                uguali += tr_.T_eseguita == _esegui(s.mescolamenti,
                                                    **{chiave: (k,)})[0]
    assert uguali == 216 * 3 * 2


def test_e4_esaustivo_contro_l_oracolo():
    uguali = 0
    for c in range(27):
        for t in range(27):
            s = er.SessioneErrori.da_trucco(c, t)
            piano = gr.risolvi_trucco(c, t)
            cifre = _cifre(t)[::-1]
            for k in (1, 2, 3):
                for ind in range(3):
                    if ind == piano["colonne"][k - 1]:
                        continue
                    tr_ = er.esegui(s, _gesti(**{f"f{k}": G(colonna_indicata=ind)}))
                    eseguiti = list(s.mescolamenti)
                    eseguiti[k - 1] = gr.mescolamento_per_colonna(ind, cifre[k - 1])
                    uguali += tr_.T_eseguita == _esegui(tuple(eseguiti))[0]
    assert uguali == 729 * 6


def test_e5_esaustivo_contro_l_oracolo():
    uguali = casi = 0
    for n in range(216):
        s = er.SessioneErrori.da_disposizione(n, 0)
        for k, m in enumerate(s.mescolamenti, 1):
            corretto = gr.IMPILAMENTO_DI[m]
            for imp in gr.SIGLE:
                if imp == corretto:
                    continue
                tr_ = er.esegui(s, _gesti(**{f"f{k}": G(impilamento=imp)}))
                atteso = er.TipoErrore.E1 if imp == m else er.TipoErrore.E5
                eseguiti = list(s.mescolamenti)
                eseguiti[k - 1] = gr.IMPILAMENTO_DI[imp]
                casi += 1
                uguali += (tr_.T_eseguita == _esegui(tuple(eseguiti))[0]
                           and [e.tipo for e in tr_.eventi] == [atteso])
    assert casi == 216 * 3 * 5 and uguali == casi


def test_eventi_multipli_nello_stesso_ordine_fisico():
    s = er.SessioneErrori.da_trucco(0, 13)
    g = G(colonna_indicata=2, impilamento="SCD", ordine_interno_invertito=True,
          rovesciamento_dopo=True)
    tr_ = er.esegui(s, _gesti(f1=g))
    assert [e.tipo for e in tr_.eventi] == [er.TipoErrore.E3, er.TipoErrore.E4,
                                            er.TipoErrore.E5, er.TipoErrore.E2]
    inteso = gr.mescolamento_per_colonna(2, 1)                     # SDC
    assert tr_.passi[0].mescolamento_inteso == inteso
    atteso, _ = _esegui((gr.IMPILAMENTO_DI["SCD"], "CSD", "CSD"), e2=(1,), e3=(1,))
    assert tr_.T_eseguita == atteso
    # E3 alla fase 1 + E2 alla fase 2
    tr_ = er.esegui(s, _gesti(f1=G(ordine_interno_invertito=True),
                              f2=G(rovesciamento_dopo=True)))
    assert tr_.T_eseguita == _esegui(s.mescolamenti, e2=(2,), e3=(1,))[0]
    assert [(e.fase, e.tipo) for e in tr_.eventi] == [(1, er.TipoErrore.E3),
                                                     (2, er.TipoErrore.E2)]


def test_e4_con_e1_nella_stessa_fase():
    """La colonna indicata cambia il mescolamento inteso; l'impilamento
    sbagliato si giudica rispetto a quello inteso, non a quello del piano."""
    s = er.SessioneErrori.da_trucco(0, 20)                 # DSC SCD DSC
    tr_ = er.esegui(s, _gesti(f1=G(colonna_indicata=2)))   # col 2 → cifra 2 → SCD
    assert tr_.passi[0].mescolamento_inteso == "SCD"
    s = er.SessioneErrori.da_trucco(2, 2)                  # fase 1: colonna 2, cifra 2
    assert s.mescolamenti[0] == "SCD"
    tr_ = er.esegui(s, _gesti(f1=G(colonna_indicata=0, impilamento="DSC")))
    inteso = gr.mescolamento_per_colonna(0, 2)
    assert tr_.passi[0].mescolamento_inteso == inteso == "DSC"
    assert tr_.passi[0].impilamento_corretto == "CDS"
    assert [e.tipo for e in tr_.eventi] == [er.TipoErrore.E4, er.TipoErrore.E1]


def test_una_sola_sequenza_globale():
    s = er.SessioneErrori.da_trucco(5, 21)
    tr_ = er.esegui(s, _gesti(f2=G(colonna_indicata=0 if
                                   gr.risolvi_trucco(5, 21)["colonne"][1] else 1)))
    assert tr_.T_eseguita == tuple(tr_.mazzo_finale.index(c) for c in range(27))
    eseguiti = tuple(p.mescolamento_eseguito for p in tr_.passi)
    assert tr_.T_eseguita == _esegui(eseguiti)[0]
    assert sorted(tr_.T_eseguita) == list(range(27))


def test_il_confronto_e_strutturato_e_senza_testo():
    c = er.confronta(er.esegui(er.SessioneErrori.da_trucco(0, 20),
                               _gesti(f1=G(impilamento="DSC"))))
    assert (c.carta, c.bersaglio) == (0, 20)
    assert c.cifre_previste == (2, 0, 2) and c.cifre_eseguite == (2, 0, 1)
    assert c.fasi_divergenti == (1,)
    assert c.realizzabile_da_riga == 112
    for campo in dataclasses.fields(c):
        assert not isinstance(getattr(c, campo.name), str)


def test_gesti_non_validi():
    s = er.SessioneErrori.da_trucco(0, 13)
    with pytest.raises(ValueError):
        er.esegui(s, _gesti(f1=G(colonna_indicata=3)))
    with pytest.raises(ValueError):
        er.esegui(s, _gesti(f1=G(impilamento="XYZ")))
    with pytest.raises(ValueError):
        er.esegui(s, (OK, OK))
