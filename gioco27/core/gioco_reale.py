"""
gioco_reale.py — Il gioco fisico delle 27 carte.

Modello canonico (allineato al libro e al programma C v3):

* Il mazzo è tenuto a faccia in giù; la posizione 0 è la carta del DORSO.
* Distribuzione (MSC): le 27 carte si distribuiscono una alla volta in
  3 colonne, a rotazione (round-robin). La colonna della carta in
  posizione p è p mod 3. Le prime carte finiscono in BASSO alla colonna.
* MESCOLAMENTO (sigla funzionale, es. CDS): "la cifra N va nella
  N-esima lettera" — è la riga del tabellone. S=0, C=1, D=2.
* IMPILAMENTO (gesto fisico): ordine dei mazzetti dal dorso verso il
  fondo. È l'INVERSA del mescolamento: CDS↔DSC si scambiano, le altre
  quattro sigle coincidono con la propria inversa (Prima Crisi di Seldon).
* ROVESCIAMENTO: capovolgimento dell'intero mazzo dopo la raccolta.

Il tabellone T sono i tre mescolamenti impilati: il primo in basso
(B0), l'ultimo in alto (B2). T agisce cifra per cifra:
T(n) con n=(n2,n1,n0)_3 ha cifre (B2(n2), B1(n1), B0(n0)).
Numerazione della tavola: # = i1 + 6·i2 + 36·i3 con gli indici dei
mescolamenti cronologici nell'ordine SCD,SDC,CSD,DSC,CDS,DCS.
"""
from __future__ import annotations
import itertools

# ─── Sigle ────────────────────────────────────────────────────────────────────

#: ordine canonico delle sigle (stesso del programma C e della tavola)
SIGLE = ("SCD", "SDC", "CSD", "DSC", "CDS", "DCS")

#: sigla → permutazione funzionale su {0,1,2} (mescolamento: cifra N → N-esima lettera)
#: S=0, C=1, D=2.   Es. CDS: S→C, C→D, D→S  ↔  [1, 2, 0]
MESCOLAMENTO = {
    "SCD": (0, 1, 2), "SDC": (0, 2, 1), "CSD": (1, 0, 2),
    "DSC": (2, 0, 1), "CDS": (1, 2, 0), "DCS": (2, 1, 0),
}

_LETT = "SCD"          # lettera del gruppo g: _LETT[g]

def _inv3(p):
    q = [0, 0, 0]
    for i, v in enumerate(p):
        q[v] = i
    return tuple(q)

def _sigla_of(p):
    """Permutazione funzionale → sigla."""
    for s, q in MESCOLAMENTO.items():
        if tuple(p) == q:
            return s
    raise ValueError(f"non è una permutazione di S3: {p}")

#: sigla del mescolamento → sigla dell'impilamento (gesto fisico) e viceversa.
#: Scambia CDS↔DSC, fissa le altre (auto-inverse).
IMPILAMENTO_DI = {s: _sigla_of(_inv3(p)) for s, p in MESCOLAMENTO.items()}

def descrizione_impilamento(sigla_mesc: str) -> str:
    """Gesto fisico per eseguire il mescolamento dato: mazzetti dal dorso."""
    imp = IMPILAMENTO_DI[sigla_mesc]
    return f"impila (dal dorso): {imp[0]}, {imp[1]}, {imp[2]}"

# ─── Simulazione fisica ───────────────────────────────────────────────────────

def distribuisci(deck):
    """Distribuisce il mazzo in 3 colonne round-robin.

    Restituisce cols[g] = lista delle carte del gruppo g nell'ordine di
    distribuzione (la prima carta distribuita è la prima della lista).
    """
    cols = [[], [], []]
    for p, c in enumerate(deck):
        cols[p % 3].append(c)
    return cols

def raccogli(cols, sigla_mesc: str, rovescia: bool = False):
    """Raccoglie le colonne eseguendo il mescolamento dato (sigla funzionale).

    L'impilamento fisico è l'inverso: il gruppo che il mescolamento manda
    in 0 (=S) va al dorso, ecc. Se rovescia=True, capovolge il mazzo dopo.
    """
    m = MESCOLAMENTO[sigla_mesc]
    inv = _inv3(m)
    deck = list(cols[inv[0]]) + list(cols[inv[1]]) + list(cols[inv[2]])
    if rovescia:
        deck.reverse()
    return deck

def esegui_partita(mescolamenti, rovesciamenti=(False, False, False)):
    """Esegue le tre fasi del gioco. Restituisce (deck_finale, fasi).

    fasi = lista di dict con lo stato dopo ogni passo (per GUI/protocolli).
    deck[p] = carta (0..26) in posizione p dal dorso.
    """
    if len(mescolamenti) != 3:
        raise ValueError("servono esattamente 3 mescolamenti")
    for s in mescolamenti:
        if s not in MESCOLAMENTO:
            raise ValueError(f"sigla sconosciuta: {s!r} (attese: {SIGLE})")
    deck = list(range(27))
    fasi = [{"tipo": "iniziale", "deck": list(deck)}]
    for i, (s, r) in enumerate(zip(mescolamenti, rovesciamenti), start=1):
        cols = distribuisci(deck)
        fasi.append({"tipo": "colonne", "fase": i, "cols": [list(c) for c in cols]})
        deck = raccogli(cols, s, bool(r))
        fasi.append({"tipo": "raccolta", "fase": i, "sigla": s,
                     "impilamento": IMPILAMENTO_DI[s],
                     "rovesciato": bool(r), "deck": list(deck)})
    return deck, fasi

def T_da_partita(mescolamenti, rovesciamenti=(False, False, False)):
    """Permutazione T: T[carta] = posizione finale (T(n) del libro)."""
    deck, _ = esegui_partita(mescolamenti, rovesciamenti)
    T = [0] * 27
    for pos, c in enumerate(deck):
        T[c] = pos
    return T

# ─── Tabellone / tavola ───────────────────────────────────────────────────────

def digits3(n):
    """n → (n2, n1, n0) in base 3."""
    return (n // 9, (n // 3) % 3, n % 3)

def numero_tavola(mescolamenti) -> int:
    """Numero # nella tavola delle disposizioni semplici (0..215)."""
    i1, i2, i3 = (SIGLE.index(s) for s in mescolamenti)
    return i1 + 6 * i2 + 36 * i3

def mescolamenti_da_numero(n: int):
    """Inversa di numero_tavola."""
    if not 0 <= n <= 215:
        raise ValueError("numero tavola fuori da 0..215")
    return (SIGLE[n % 6], SIGLE[(n // 6) % 6], SIGLE[n // 36])

def T_da_tabellone(mescolamenti):
    """T per via algebrica: agisce cifra per cifra (B0 = primo mescolamento)."""
    B0, B1, B2 = (MESCOLAMENTO[s] for s in mescolamenti)
    T = [0] * 27
    for n in range(27):
        n2, n1, n0 = digits3(n)
        T[n] = 9 * B2[n2] + 3 * B1[n1] + B0[n0]
    return T

def tabellone_da_assi(pos_AS: int, pos_AC: int, pos_AH: int):
    """Ricostruisce i mescolamenti dalle posizioni finali degli Assi.

    Gli Assi occupano in partenza le posizioni diagonali 0, 13, 26:
    le loro immagini T(0), T(13), T(26) sono le colonne del tabellone.
    Restituisce (mescolamenti, numero_tavola). ValueError se le posizioni
    non provengono da alcuna disposizione semplice.
    """
    pos = (pos_AS, pos_AC, pos_AH)
    for p in pos:
        if not 0 <= p <= 26:
            raise ValueError("le posizioni devono essere in 0..26")
    cols = [digits3(p) for p in pos]           # cols[t] = (B2(t), B1(t), B0(t))
    righe = []
    for liv in (2, 1, 0):                      # B2, B1, B0
        riga = tuple(cols[t][2 - liv] for t in range(3))
        if sorted(riga) != [0, 1, 2]:
            raise ValueError(
                "posizioni incompatibili: nessuna disposizione semplice "
                f"produce questi Assi (riga livello {liv} = {riga})")
        righe.append(riga)
    B2, B1, B0 = righe
    mesc = (_sigla_of(B0), _sigla_of(B1), _sigla_of(B2))
    return mesc, numero_tavola(mesc)

# ─── Statistiche ──────────────────────────────────────────────────────────────

def periodo(T):
    """Ordine della permutazione (lcm delle lunghezze dei cicli)."""
    from math import gcd
    seen = [False] * len(T)
    out = 1
    for i in range(len(T)):
        if seen[i]:
            continue
        l, j = 0, i
        while not seen[j]:
            seen[j] = True
            j = T[j]
            l += 1
        out = out * l // gcd(out, l)
    return out

def tipo_ciclo(T):
    """Tipo ciclico come tupla ordinata di lunghezze, es. (1,1,1,3,3,...)."""
    seen = [False] * len(T)
    lens = []
    for i in range(len(T)):
        if seen[i]:
            continue
        l, j = 0, i
        while not seen[j]:
            seen[j] = True
            j = T[j]
            l += 1
        lens.append(l)
    return tuple(sorted(lens))

def punti_fissi(T):
    return sum(1 for i, v in enumerate(T) if i == v)

def parita(T):
    """+1 pari, -1 dispari."""
    seen = [False] * len(T)
    sign = 1
    for i in range(len(T)):
        if seen[i]:
            continue
        l, j = 0, i
        while not seen[j]:
            seen[j] = True
            j = T[j]
            l += 1
        if l % 2 == 0:
            sign = -sign
    return sign

def riga_tavola(n: int) -> dict:
    """Tutti i dati della riga # n della tavola delle disposizioni semplici."""
    mesc = mescolamenti_da_numero(n)
    T = T_da_tabellone(mesc)
    imp = tuple(IMPILAMENTO_DI[s] for s in mesc)
    Tinv = [0] * 27
    for i, v in enumerate(T):
        Tinv[v] = i
    return {
        "numero": n,
        "mescolamenti": mesc,
        "impilamenti": imp,
        "T": T,
        "T_inv": Tinv,
        "assi": (T[0], T[13], T[26]),
        "periodo": periodo(T),
        "punti_fissi": punti_fissi(T),
        "tipo_ciclo": tipo_ciclo(T),
        "parita": parita(T),
        "autoinversa": T == Tinv,
    }

def tavola_216():
    """L'intera tavola delle disposizioni semplici (216 righe)."""
    return [riga_tavola(n) for n in range(216)]

def statistiche_tavola(righe=None) -> dict:
    """Statistiche aggregate sulle 216 disposizioni semplici.

    Riproduce i valori del capitolo 100 del libro:
    periodi {1:1, 2:63, 3:26, 6:126}, 7 tipi ciclici, 64 auto-inverse,
    punti fissi {0? ...} ecc.
    """
    from collections import Counter
    righe = righe if righe is not None else tavola_216()
    return {
        "periodi": dict(Counter(r["periodo"] for r in righe)),
        "punti_fissi": dict(Counter(r["punti_fissi"] for r in righe)),
        "tipi_ciclo": dict(Counter(r["tipo_ciclo"] for r in righe)),
        "parita": dict(Counter(r["parita"] for r in righe)),
        "autoinverse": sum(1 for r in righe if r["autoinversa"]),
    }

# ─── Il trucco: soluzione in forma chiusa ─────────────────────────────────────

def risolvi_trucco(carta: int, bersaglio: int, preferisci_semplici: bool = True):
    """Sceglie i 3 mescolamenti che portano `carta` in posizione `bersaglio`.

    Forma chiusa, nessuna ricerca: al passo i la carta si trova in una
    colonna nota c_i; serve un mescolamento M_i con M_i(c_i) = cifra
    richiesta del bersaglio. Restano 2 gradi di libertà per passo: si
    sceglie la permutazione che ordina i gruppi rimanenti in modo naturale
    (o l'identità quando possibile, se preferisci_semplici).

    Restituisce dict con mescolamenti, impilamenti, colonne attese,
    numero di tavola e T risultante.
    """
    if not (0 <= carta <= 26 and 0 <= bersaglio <= 26):
        raise ValueError("carta e bersaglio devono essere in 0..26")
    b2, b1, b0 = digits3(bersaglio)
    cifre = (b0, b1, b2)             # cifra da realizzare alla fase 1, 2, 3
    deck = list(range(27))
    mesc, colonne = [], []
    for i in range(3):
        col = deck.index(carta) % 3
        colonne.append(col)
        dig = cifre[i]
        # tutte le permutazioni con M(col) = dig
        cands = [s for s in SIGLE if MESCOLAMENTO[s][col] == dig]
        scelto = None
        if preferisci_semplici:
            for s in cands:
                if s == "SCD":
                    scelto = s
                    break
        if scelto is None:
            # canonica: gli altri due gruppi in ordine crescente di cifra
            others = sorted(g for g in range(3) if g != col)
            digs = sorted(d for d in range(3) if d != dig)
            m = [0, 0, 0]
            m[col] = dig
            m[others[0]], m[others[1]] = digs[0], digs[1]
            scelto = _sigla_of(m)
        mesc.append(scelto)
        cols = distribuisci(deck)
        deck = raccogli(cols, scelto)
    finale = deck.index(carta)
    if finale != bersaglio:      # non deve mai accadere
        raise AssertionError("soluzione errata: bug in risolvi_trucco")
    return {
        "mescolamenti": tuple(mesc),
        "impilamenti": tuple(IMPILAMENTO_DI[s] for s in mesc),
        "colonne": tuple(colonne),
        "numero": numero_tavola(mesc),
        "T": T_da_tabellone(mesc),
    }

# ─── Selftest ─────────────────────────────────────────────────────────────────

def selftest(completo: bool = True) -> dict:
    """Verifica l'intero impianto. Restituisce un rapporto; solleva
    AssertionError alla prima incoerenza.

    1. Fisica vs algebra: per tutte le 216 sequenze senza rovesciamenti
       (e, se completo, per tutte le 1728 con rovesciamenti via modello
       matriciale) la simulazione carta-per-carta coincide con T_da_tabellone
       / compute_T_full.
    2. Ancore del libro: #100 → assi (13,8,18); #82 → assi (10,8,21).
    3. Statistiche del capitolo 100.
    4. Ricostruzione dagli assi: bigezione perfetta sulle 216 righe.
    5. risolvi_trucco: tutte le 27×27 coppie (carta, bersaglio).
    """
    rapporto = {}
    # 1a. fisica vs algebra, 216 semplici
    for n in range(216):
        mesc = mescolamenti_da_numero(n)
        assert T_da_partita(mesc) == T_da_tabellone(mesc), f"riga {n}"
    rapporto["fisica_vs_algebra_216"] = "ok"
    # 1b. con rovesciamenti, vs modello matriciale (P3 = raccolta,
    #     rovesciamento inglobato nei P della fase)
    if completo:
        try:
            from .constants import PERM3
            from .permutations import compute_T_full
            name_of = {tuple(v): k for k, v in PERM3.items()}
            J = (2, 1, 0)
            n_check = 0
            for mesc in itertools.product(SIGLE, repeat=3):
                for rov in itertools.product((False, True), repeat=3):
                    params = []
                    for s, r in zip(mesc, rov):
                        p3 = MESCOLAMENTO[s]
                        p2 = p1 = (0, 1, 2)
                        if r:
                            p3 = tuple(J[x] for x in p3)
                            p2 = p1 = J
                        params.append((name_of[p1], name_of[p2],
                                       name_of[p3], "I_3", "I_3", "I_3"))
                    _, _, Tp, _ = compute_T_full(params)
                    Tf = T_da_partita(mesc, rov)
                    assert list(Tp) == Tf, f"{mesc} {rov}"
                    n_check += 1
            rapporto["fisica_vs_matrici_1728"] = f"ok ({n_check})"
        except ImportError:
            rapporto["fisica_vs_matrici_1728"] = "saltato (numpy assente)"
    # 2. ancore
    assert riga_tavola(100)["assi"] == (13, 8, 18), "ancora #100"
    assert riga_tavola(100)["mescolamenti"] == ("CDS", "CDS", "CSD")
    assert riga_tavola(82)["assi"] == (10, 8, 21), "ancora #82"
    assert riga_tavola(82)["mescolamenti"] == ("CDS", "SDC", "CSD")
    rapporto["ancore_libro"] = "ok (#100, #82)"
    # 3. statistiche
    st = statistiche_tavola()
    assert st["periodi"] == {1: 1, 2: 63, 3: 26, 6: 126}, st["periodi"]
    assert st["autoinverse"] == 64
    assert len(st["tipi_ciclo"]) == 7
    rapporto["statistiche_cap100"] = "ok"
    # 4. assi → tabellone
    for n in range(216):
        r = riga_tavola(n)
        mesc, num = tabellone_da_assi(*r["assi"])
        assert num == n and mesc == r["mescolamenti"], f"assi riga {n}"
    rapporto["ricostruzione_assi"] = "ok (216/216)"
    # 5. trucco
    for c in range(27):
        for t in range(27):
            risolvi_trucco(c, t)
    rapporto["trucco_729"] = "ok (729/729)"
    rapporto["esito"] = "TUTTO OK"
    return rapporto


if __name__ == "__main__":
    for k, v in selftest().items():
        print(f"{k:28s} {v}")
