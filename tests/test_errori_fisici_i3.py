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
