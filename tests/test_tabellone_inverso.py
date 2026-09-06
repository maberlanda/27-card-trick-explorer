"""
Il secondo tabellone del PDF dettagliato è quello di T⁻¹.

La griglia A_1/A_2/A_3 del PDF dettagliato, letta per righe, dà le sigle dei
mescolamenti in ordine cronologico inverso: è il «tabellone» di
core/gioco_reale.py. Sostituendo ogni sigla con la propria inversa (che è
esattamente la sigla d'impilamento: CDS↔DSC, le altre quattro auto-inverse) si
ottiene il tabellone della permutazione inversa, perché

    T = B₂ ⊗ B₁ ⊗ B₀   ⟹   T⁻¹ = B₂⁻¹ ⊗ B₁⁻¹ ⊗ B₀⁻¹

Questi test verificano la proprietà su tutte e 216 le sequenze del gioco, non
su un campione.
"""
import pytest

from gioco27.core.combinations import iter_combinations_ex
from gioco27.core.constants import ANY
from gioco27.core.detail import combination_detail, inverse_perm
from gioco27.core.detail_pdf import (_is_game_stage, righe_impilamenti,
                                     righe_tabellone)
from gioco27.core.gioco_reale import IMPILAMENTO_DI, SIGLE, T_da_tabellone, riga_tavola


def _sequenze_di_gioco(con_rovesciamenti):
    """
    Le combinazioni fisicamente eseguibili.

    con_rovesciamenti=False -> le 216 senza alcun rovesciamento
    con_rovesciamenti=True  -> tutte e 1728 (8 pattern di inversione ciascuna)
    """
    j = {'j0': ANY, 'j1': ANY, 'j2': ANY, 'j_uniform': True} \
        if con_rovesciamenti else {'j0': 'I_3', 'j1': 'I_3', 'j2': 'I_3'}
    filtri = [dict({'p0': 'SCD_U', 'p1': 'SCD_U', 'p2': ANY}, **j)
              for _ in range(3)]
    for params in iter_combinations_ex(filtri):
        if all(_is_game_stage(p) for p in params):
            yield params


@pytest.fixture(scope="module")
def sequenze():
    """Le 216 sequenze SENZA rovesciamenti."""
    return list(_sequenze_di_gioco(False))


@pytest.fixture(scope="module")
def tutte_le_sequenze():
    """Tutte e 1728 le sequenze, rovesciamenti compresi."""
    return list(_sequenze_di_gioco(True))


def test_ci_sono_216_sequenze(sequenze):
    assert len(sequenze) == 216


def test_ci_sono_1728_sequenze_coi_rovesciamenti(tutte_le_sequenze):
    assert len(tutte_le_sequenze) == 1728


def test_righe_griglia_sono_i_mescolamenti_invertiti_di_ordine(sequenze):
    """
    Riga 0 (in alto) = terzo mescolamento, riga 2 (in basso) = primo:
    è il tabellone «i tre mescolamenti impilati, il primo in basso».
    """
    for params in sequenze:
        d = combination_detail(params)
        mesc = [p[2].replace("_U", "") for p in params]
        assert righe_tabellone(d["markers"]) == list(reversed(mesc))


def test_ancora_100_del_libro():
    """Controllo esplicito sulla riga #100, una delle ancore del selftest."""
    r = riga_tavola(100)
    assert r["mescolamenti"] == ("CDS", "CDS", "CSD")
    assert r["assi"] == (13, 8, 18)
    params = [("SCD_U", "SCD_U", m + "_U", "I_3", "I_3", "I_3")
              for m in r["mescolamenti"]]
    d = combination_detail(params)
    assert [m[3] for m in d["markers"]] == ["ccc", "sdd", "dss"]
    assert righe_tabellone(d["markers"]) == ["CSD", "CDS", "CDS"]
    assert righe_impilamenti(d["markers"]) == ["CSD", "DSC", "DSC"]


def test_tabellone_diretto_ricostruisce_T(sequenze):
    """Il primo tabellone, riletto, deve riprodurre esattamente T."""
    for params in sequenze:
        d = combination_detail(params)
        righe = righe_tabellone(d["markers"])
        assert T_da_tabellone(tuple(reversed(righe))) == list(d["T_perm"])


def test_tabellone_scambiato_ricostruisce_T_inversa(sequenze):
    """
    Il cuore della funzione: scambiare CDS↔DSC riga per riga produce il
    tabellone di T⁻¹, su tutte e 216 le sequenze.
    """
    for params in sequenze:
        d = combination_detail(params)
        righe = righe_impilamenti(d["markers"])
        assert T_da_tabellone(tuple(reversed(righe))) == inverse_perm(list(d["T_perm"]))


def test_lo_scambio_e_una_involuzione():
    """Applicare due volte la conversione riporta alle sigle di partenza."""
    for s in SIGLE:
        assert IMPILAMENTO_DI[IMPILAMENTO_DI[s]] == s


def test_solo_cds_e_dsc_cambiano():
    """Le altre quattro sigle coincidono con la propria inversa."""
    cambiate = {s for s in SIGLE if IMPILAMENTO_DI[s] != s}
    assert cambiate == {"CDS", "DSC"}
    assert IMPILAMENTO_DI["CDS"] == "DSC"
    assert IMPILAMENTO_DI["DSC"] == "CDS"


def test_righe_maiuscole():
    """Le righe del secondo tabellone vanno stampate in maiuscolo."""
    d = combination_detail([("SCD_U", "SCD_U", "CDS_U", "I_3", "I_3", "I_3")] * 3)
    for riga in righe_impilamenti(d["markers"]):
        assert riga.isupper() and len(riga) == 3


def test_riga_non_valida_lasciata_invariata():
    """
    Con combinazioni non eseguibili fisicamente i settori degli Assi possono
    non formare una permutazione: la riga dev'essere lasciata com'è, non far
    fallire l'export.
    """
    finti_markers = [("A", "", 0, "sss"), ("B", "", 0, "sss"), ("C", "", 0, "sss")]
    assert righe_tabellone(finti_markers) == ["SSS", "SSS", "SSS"]
    assert righe_impilamenti(finti_markers) == ["SSS", "SSS", "SSS"]


# ─────────────── etichette di riga M_2 / M_1 / M_0 del secondo tabellone ────

def test_etichette_riga_dal_basso_M0():
    """
    Il secondo tabellone si legge in orizzontale, quindi al posto delle
    intestazioni di colonna A_1/A_2/A_3 (che hanno senso solo per i settori
    degli Assi) porta le etichette di riga M_2/M_1/M_0 dall'alto in basso:
    M_0 in fondo è il PRIMO mescolamento, secondo la convenzione del tabellone
    («i tre mescolamenti impilati, il primo in basso»).

    Invertire quest'ordine renderebbe la tabella silenziosamente sbagliata,
    quindi lo si verifica sul sorgente.
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "gioco27" / "core" / "detail_pdf.py").read_text(encoding="utf-8")
    assert 'etichette_riga=("M_2", "M_1", "M_0")' in src, \
        "l'ordine delle etichette di riga non è M_2/M_1/M_0 dall'alto"


def test_riga_M0_e_il_primo_impilamento(sequenze):
    """
    La riga in basso (M_0) deve corrispondere all'impilamento del PRIMO
    mescolamento eseguito, su tutte e 216 le sequenze.
    """
    for params in sequenze:
        d = combination_detail(params)
        righe = righe_impilamenti(d["markers"])     # [M_2, M_1, M_0]
        mesc = [p[2].replace("_U", "") for p in params]   # cronologici
        assert righe[2] == IMPILAMENTO_DI[mesc[0]]       # M_0 = primo
        assert righe[1] == IMPILAMENTO_DI[mesc[1]]       # M_1 = secondo
        assert righe[0] == IMPILAMENTO_DI[mesc[2]]       # M_2 = terzo


# ────────────── il caso che le didascalie sbagliavano: i rovesciamenti ─────
#
# I test qui sopra usano solo le 216 combinazioni senza rovesciamenti, ed è
# per questo che non hanno colto il problema: con un rovesciamento le righe
# della griglia NON sono più i mescolamenti stampati sulla pagina, perché
# l'inversione si fonde nelle righe del tabellone. La proprietà su T e T⁻¹
# regge comunque, ed è quella che le didascalie devono dichiarare.

def test_tabelloni_valgono_anche_coi_rovesciamenti(tutte_le_sequenze):
    """
    Su TUTTE e 1728 le combinazioni: la griglia superiore ricostruisce T e
    quella inferiore T⁻¹. È l'affermazione che le didascalie fanno.
    """
    for params in tutte_le_sequenze:
        d = combination_detail(params)
        T = list(d["T_perm"])
        assert T_da_tabellone(tuple(reversed(righe_tabellone(d["markers"])))) == T
        assert T_da_tabellone(tuple(reversed(righe_impilamenti(d["markers"])))) \
            == inverse_perm(T)


def test_le_righe_sono_sempre_sigle_valide(tutte_le_sequenze):
    """Nessuna riga può essere una tripla non-permutazione tipo 'SSD'."""
    for params in tutte_le_sequenze:
        d = combination_detail(params)
        for riga in righe_tabellone(d["markers"]) + righe_impilamenti(d["markers"]):
            assert riga in SIGLE, f"riga non valida: {riga}"


def test_col_rovesciamento_le_righe_non_sono_i_mescolamenti(tutte_le_sequenze):
    """
    Documenta il comportamento che ha reso false le vecchie didascalie:
    con almeno un rovesciamento le righe differiscono, in generale, dai
    mescolamenti nominali. Senza rovesciamenti coincidono sempre.
    """
    coincidono_senza = 0
    differiscono_con = 0
    totale_con = 0
    for params in tutte_le_sequenze:
        d = combination_detail(params)
        mesc = [p[2].replace("_U", "") for p in params]
        righe = righe_tabellone(d["markers"])
        rovesciata = any(p[3] == "R_U" for p in params)
        if rovesciata:
            totale_con += 1
            differiscono_con += (righe != list(reversed(mesc)))
        else:
            coincidono_senza += (righe == list(reversed(mesc)))
    assert coincidono_senza == 216, "senza rovesciamenti devono sempre coincidere"
    assert totale_con == 1512
    assert differiscono_con > 0, (
        "se coincidessero sempre, le didascalie «MESCOLAMENTI» sarebbero "
        "state corrette e questo test andrebbe rimosso")


def test_didascalie_non_promettono_i_mescolamenti():
    """
    Le didascalie devono parlare di T e T⁻¹, non di MESCOLAMENTI/IMPILAMENTI:
    quelle parole sono vere solo in 216 casi su 1728.
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "gioco27" / "core" / "detail_pdf.py").read_text(encoding="utf-8")
    blocco = src.split("def griglia(", 1)[1].split("# Matrice 27x27", 1)[0]
    assert '("TABELLONE", "DI T")' in blocco
    assert '"DI T\\u207b\\u00b9"' in blocco
    for parola in ('"MESCOLAMENTI"', '"(IMPILAMENTI)"'):
        assert parola not in blocco, \
            f"didascalia {parola}: vera solo senza rovesciamenti"


# ═══════════════════════════════════════════════════════════════════════════
# VALIDITÀ UNIVERSALE
#
# I test qui sopra girano sulle 1728 sequenze «di gioco» (P1 = P2 = identità,
# J uniforme). Ma i due tabelloni non hanno bisogno di quelle ipotesi: valgono
# per QUALUNQUE combinazione del modello, compreso il rovesciamento di un solo
# mazzetto (J non uniforme), che non è nemmeno una sequenza eseguibile a mano.
#
# Il motivo è che i tre Assi partono dalle posizioni 0, 13, 26 — cioè (0,0,0),
# (1,1,1), (2,2,2), la diagonale ternaria. Se T = B₂ ⊗ B₁ ⊗ B₀ agisce cifra per
# cifra, allora
#
#     T(j,j,j) = (B₂(j), B₁(j), B₀(j))
#
# quindi la colonna dell'Asso j, letta dall'alto in basso, è (B₂(j), B₁(j),
# B₀(j)); e la riga r, letta per intero, è la sigla completa di B₂₋ᵣ.
#
# Ne segue che la griglia dipende SOLO da T, non dai parametri che l'hanno
# prodotta. E poiché ogni T del modello è un prodotto di Kronecker GEN3³ — ce
# ne sono esattamente 216 — verificare tutti e 216 i T possibili è una verifica
# ESAUSTIVA su tutte e 1728³ = 5.159.780.352 le combinazioni.
# ═══════════════════════════════════════════════════════════════════════════

def _tutti_i_kronecker():
    """I 216 prodotti di Kronecker GEN3 ⊗ GEN3 ⊗ GEN3 come vettori di 27."""
    from gioco27.core.constants import PERM3
    g = list(PERM3.values())
    return [[9 * a[i // 9] + 3 * b[(i % 9) // 3] + c[i % 3] for i in range(27)]
            for a in g for b in g for c in g]


def test_i_tabelloni_valgono_per_tutti_i_216_T_possibili():
    """
    Verifica ESAUSTIVA: la griglia dipende solo da T, e i T possibili sono 216.
    Coprire tutti e 216 significa coprire ogni combinazione del modello.
    """
    from gioco27.core.detail import marker_positions
    for T in _tutti_i_kronecker():
        m = marker_positions(T)
        righe, righe_inv = righe_tabellone(m), righe_impilamenti(m)
        assert all(x in SIGLE for x in righe), righe
        assert T_da_tabellone(tuple(reversed(righe))) == T
        assert T_da_tabellone(tuple(reversed(righe_inv))) == inverse_perm(T)


def test_ogni_combinazione_del_modello_da_un_T_di_kronecker():
    """
    L'altra metà dell'argomento: qualunque combinazione (P e J arbitrari, non
    solo quelle eseguibili a mano) produce un T fra quei 216. Segue dalla
    relazione di trasporto — T = A₃ ∘ rot₂(A₂) ∘ rot₁(A₁), composizione di
    prodotti di Kronecker — e qui si controlla su un campione ampio.
    """
    import itertools
    import random
    from gioco27.core.constants import P_OPTS, J_OPTS
    from gioco27.core.permutations import compute_T_perm

    kron = {tuple(t) for t in _tutti_i_kronecker()}
    stadi = list(itertools.product(P_OPTS, P_OPTS, P_OPTS, J_OPTS, J_OPTS, J_OPTS))
    assert len(stadi) == 1728
    rnd = random.Random(20260726)
    for _ in range(3000):
        params = [rnd.choice(stadi) for _ in range(3)]
        _, _, T = compute_T_perm(params)
        assert tuple(T) in kron, params


def test_valgono_col_rovesciamento_di_un_solo_mazzetto():
    """
    Il caso che le ipotesi «di gioco» escludevano: J NON uniforme, cioè un solo
    mazzetto rovesciato. Non è una sequenza eseguibile con un gesto solo, ma i
    tabelloni restano validi.
    """
    from gioco27.core.constants import P_OPTS
    j_singoli = [("R_U", "I_3", "I_3"), ("I_3", "R_U", "I_3"),
                 ("I_3", "I_3", "R_U")]
    provate = 0
    for j in j_singoli:
        for p3 in P_OPTS:
            params = [("SCD_U", "SCD_U", p3) + j,
                      ("SCD_U", "SCD_U", "CSD_U", "I_3", "I_3", "I_3"),
                      ("SCD_U", "SCD_U", "DSC_U", "I_3", "I_3", "I_3")]
            assert not all(_is_game_stage(p) for p in params), \
                "questo test deve usare combinazioni NON di gioco"
            d = combination_detail(params)
            T = list(d["T_perm"])
            assert T_da_tabellone(
                tuple(reversed(righe_tabellone(d["markers"])))) == T
            assert T_da_tabellone(
                tuple(reversed(righe_impilamenti(d["markers"])))) == inverse_perm(T)
            provate += 1
    assert provate == 18


def test_gli_assi_stanno_sulla_diagonale_ternaria():
    """
    È l'ipotesi da cui dipende tutto: gli Assi partono da (0,0,0), (1,1,1),
    (2,2,2). Spostarli romperebbe silenziosamente entrambi i tabelloni.
    """
    from gioco27.core.detail import MARKERS, num_to_sector
    partenze = [start for _ch, start, _lab in MARKERS]
    assert partenze == [0, 13, 26]
    assert [num_to_sector(p) for p in partenze] == ["sss", "ccc", "ddd"]
