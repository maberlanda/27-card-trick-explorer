"""Compartimento I1 — modello canonico di procedura e servizio delle relazioni.

Contratto (decisioni approvate, docs/decisions/V4_PRE_I1_PRODUCT_DECISIONS.md):

* DP3 = A: una procedura e' (S1,S2,S3 ; e1,e2,e3) con il rovesciamento PRIMA
  della distribuzione dello stadio; identificatori # = k1+6k2+36k3 e
  m = 4e1+2e2+e3. La convenzione fisica B resta un oracolo.
* DP4: nessuna «equivalenza» generica; relazioni nominate (identita',
  stessa trasformazione, stesso effetto su una carta) e fibre strutturate.
* DP5: costi k1, k2, k3 separati.

Gli oracoli sono scritti qui e non passano per il servizio: formula cifra per
cifra del libro e simulazione fisica di `gioco_reale`.
"""
import dataclasses
import subprocess
import sys
from collections import Counter

import pytest

from gioco27.core import gioco_reale as gr
from gioco27.core.dominio import PermutazioneNonValida
from gioco27.services.procedure import (
    FAMIGLIA_SEMPLICE, FAMIGLIA_SEMPLICE_SICURA, FAMIGLIA_SICURA,
    FAMIGLIA_TUTTE, ConfrontoProcedure, Costo, FamigliaGesti,
    ProceduraGioco, ProceduraNonValida, ServizioProcedure,
    TrasformazioneFuoriDominio, adattamento_fisico, chiave_costo,
    chiave_sicura, chiave_storica, servizio_procedure)

R = (2, 1, 0)
I3 = (0, 1, 2)
J27 = tuple(26 - i for i in range(27))


def _c3(a, b):
    return tuple(a[b[i]] for i in range(3))


def _T_libro(mesc, eps):
    """Oracolo: M2 = S3∘R^e3∘R^e2∘R^e1, M1 = R^e3∘S2∘R^e2∘R^e1,
    M0 = R^e3∘R^e2∘S1∘R^e1; T(n) = 9·M2(n2) + 3·M1(n1) + M0(n0)."""
    s1, s2, s3 = (gr.MESCOLAMENTO[s] for s in mesc)
    r1, r2, r3 = (R if e else I3 for e in eps)
    m2 = _c3(s3, _c3(r3, _c3(r2, r1)))
    m1 = _c3(r3, _c3(s2, _c3(r2, r1)))
    m0 = _c3(r3, _c3(r2, _c3(s1, r1)))
    return tuple(9 * m2[n // 9] + 3 * m1[(n // 3) % 3] + m0[n % 3]
                 for n in range(27))


@pytest.fixture(scope="module")
def servizio():
    return servizio_procedure()


def P(mesc, eps=(0, 0, 0)):
    return ProceduraGioco(tuple(mesc.split()) if isinstance(mesc, str) else mesc,
                          eps)


# ═══════════════════════════════ modello ════════════════════════════════════

def test_la_procedura_e_immutabile():
    p = P("CDS SCD DCS", (1, 0, 1))
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.mescolamenti = ("SCD", "SCD", "SCD")
    assert p.mescolamenti == ("CDS", "SCD", "DCS")
    assert p.rovesciamenti == (1, 0, 1)


def test_l_impilamento_e_derivato_non_memorizzato():
    p = P("CDS DSC SDC")
    assert p.impilamenti == ("DSC", "CDS", "SDC")
    assert "impilamenti" not in {f.name for f in dataclasses.fields(p)}


@pytest.mark.parametrize("mesc,eps", [
    (("SCD", "SCD", "XYZ"), (0, 0, 0)),          # sigla sconosciuta
    (("scd", "SCD", "SCD"), (0, 0, 0)),          # le sigle sono maiuscole
    (("SCD", "SCD"), (0, 0, 0)),                 # due stadi
    (("SCD", "SCD", "SCD", "SCD"), (0, 0, 0, 0)),  # quattro stadi
    (("SCD", "SCD", "SCD"), (0, 0)),             # eps corto
    (("SCD", "SCD", "SCD"), (0, 2, 0)),          # eps non binario
    (("SCD", "SCD", "SCD"), (0, "1", 0)),        # eps testuale
    (("SCD", "SCD", "SCD"), (0, 1.0, 0)),        # eps float
    ("SCD SCD SCD", (0, 0, 0)),                  # stringa, non sequenza di sigle
])
def test_procedure_non_valide_sono_rifiutate(mesc, eps):
    with pytest.raises(ProceduraNonValida) as info:
        ProceduraGioco(mesc, eps)
    assert isinstance(info.value, ValueError)
    assert info.value.codice


def test_i_booleani_sono_normalizzati():
    assert P("SCD SCD SCD", (True, False, True)) == P("SCD SCD SCD", (1, 0, 1))
    assert P("SCD SCD SCD", (True, False, True)).rovesciamenti == (1, 0, 1)


def test_identificatori_stabili():
    p = P("SDC CSD DCS", (1, 1, 0))
    assert p.numero_tavola == 1 + 6 * 2 + 36 * 5
    assert p.numero_tavola == gr.numero_tavola(p.mescolamenti)
    assert p.indice_rovesciamenti == 6
    assert p.identificatore == (p.numero_tavola, 6)
    assert ProceduraGioco.da_identificatore(p.numero_tavola, 6) == p


@pytest.mark.parametrize("numero,m", [(-1, 0), (216, 0), (0, 8), (0, -1),
                                      (True, 0), (0, 1.0)])
def test_identificatori_fuori_intervallo(numero, m):
    with pytest.raises(ProceduraNonValida):
        ProceduraGioco.da_identificatore(numero, m)


def test_costi_separati():
    c = P("CDS DCS SCD", (1, 0, 1)).costo
    assert isinstance(c, Costo)
    assert (c.k1, c.k2, c.k3) == (2, 1, 2)
    assert dataclasses.fields(c)[0].name == "k1"


# ═══════════════════════════════ dominio ════════════════════════════════════

def test_1728_procedure_ordinate_e_senza_duplicati(servizio):
    tutte = servizio.procedure
    assert isinstance(tutte, tuple) and len(tutte) == 1728
    ident = [p.identificatore for p in tutte]
    assert len(set(ident)) == 1728
    assert len(set(tutte)) == 1728
    # ordine pubblico dichiarato: (m, #) crescente
    assert [(p.indice_rovesciamenti, p.numero_tavola) for p in tutte] == \
        [(m, n) for m in range(8) for n in range(216)]


def test_l_identificatore_ricostruisce_la_procedura(servizio):
    for p in servizio.procedure:
        assert ProceduraGioco.da_identificatore(*p.identificatore) == p


def test_la_trasformazione_coincide_con_la_formula_del_libro(servizio):
    for p in servizio.procedure:
        T = servizio.trasformazione(p)
        assert isinstance(T, tuple)
        assert T == _T_libro(p.mescolamenti, p.rovesciamenti), p


def test_la_trasformazione_coincide_con_l_oracolo_fisico(servizio):
    """DP3: T_A(S;e1,e2,e3) = T_B(S;e2,e3,0) ∘ J^e1, 1728/1728."""
    for p in servizio.procedure:
        a = adattamento_fisico(p)
        assert a.mescolamenti == p.mescolamenti
        assert a.rovesciamenti_dopo_raccolta[2] is False
        fis = gr.T_da_partita(a.mescolamenti, a.rovesciamenti_dopo_raccolta)
        if a.rovescia_mazzo_iniziale:
            fis = [fis[J27[i]] for i in range(27)]
        assert servizio.trasformazione(p) == tuple(fis), p


def test_le_procedure_semplici_coincidono_con_la_tavola(servizio):
    for n in range(216):
        p = ProceduraGioco.da_identificatore(n, 0)
        assert servizio.trasformazione(p) == tuple(gr.T_da_tabellone(p.mescolamenti))


# ═══════════════════════════ classi per trasformazione ══════════════════════

def test_216_classi_di_8(servizio):
    conta = Counter(servizio.trasformazione(p) for p in servizio.procedure)
    assert len(conta) == 216 and set(conta.values()) == {8}
    assert len(servizio.trasformazioni) == 216


def test_classe_di_ogni_trasformazione(servizio):
    for T in servizio.trasformazioni:
        classe = servizio.classe_trasformazione(T)
        assert len(classe) == 8
        assert all(servizio.trasformazione(p) == T for p in classe)
        assert sorted(p.costo.k3 for p in classe) == [0, 1, 1, 1, 2, 2, 2, 3]
        semplici = [p for p in classe if p.semplice]
        assert len(semplici) == 1
        assert [p.indice_rovesciamenti for p in classe] == list(range(8))


def test_classe_dell_identita(servizio):
    classe = servizio.classe_trasformazione(tuple(range(27)))
    assert {(p.mescolamenti[0], p.rovesciamenti) for p in classe} == {
        ("SCD", (0, 0, 0)), ("SCD", (0, 1, 1)), ("SCD", (1, 0, 1)), ("SCD", (1, 1, 0)),
        ("DCS", (0, 0, 1)), ("DCS", (0, 1, 0)), ("DCS", (1, 0, 0)), ("DCS", (1, 1, 1))}


def test_classe_fuori_dominio_o_non_valida(servizio):
    scambio = list(range(27))
    scambio[0], scambio[1] = 1, 0
    with pytest.raises(TrasformazioneFuoriDominio):
        servizio.classe_trasformazione(scambio)
    with pytest.raises(PermutazioneNonValida):
        servizio.classe_trasformazione([0] * 27)


# ═══════════════════════════════ relazioni ══════════════════════════════════

def test_stessa_trasformazione_e_stesso_effetto_sono_distinte(servizio):
    # 0 → 13 con due trasformazioni diverse (memo § 5)
    a, b = P("CSD CSD CSD"), P("CSD CSD CDS")
    assert servizio.stesso_effetto_carta(a, b, 0)
    assert not servizio.stessa_trasformazione(a, b)
    # stessa trasformazione, procedure diverse
    c, d = P("SCD SCD SCD"), P("SCD SCD SCD", (0, 1, 1))
    assert c != d and servizio.stessa_trasformazione(c, d)


def test_catena_delle_relazioni_su_un_campione(servizio):
    tutte = servizio.procedure
    for i in range(0, 1728, 37):
        for j in range(0, 1728, 41):
            p, q = tutte[i], tutte[j]
            if p == q:
                assert servizio.stessa_trasformazione(p, q)
            if servizio.stessa_trasformazione(p, q):
                assert all(servizio.stesso_effetto_carta(p, q, c) for c in range(27))


def test_carta_non_valida(servizio):
    p = P("SCD SCD SCD")
    with pytest.raises(PermutazioneNonValida):
        servizio.stesso_effetto_carta(p, p, 27)


def test_famiglie_di_gesti():
    assert FAMIGLIA_SEMPLICE == FamigliaGesti(senza_rovesciamenti=True)
    assert FAMIGLIA_SICURA == FamigliaGesti(senza_raccolte_cicliche=True)
    semplice_ciclica = P("CDS SCD SCD")
    rovesciata_sicura = P("DCS SCD SCD", (0, 1, 0))
    assert FAMIGLIA_SEMPLICE.contiene(semplice_ciclica)
    assert not FAMIGLIA_SICURA.contiene(semplice_ciclica)
    assert FAMIGLIA_SICURA.contiene(rovesciata_sicura)
    assert not FAMIGLIA_SEMPLICE.contiene(rovesciata_sicura)
    assert not FAMIGLIA_SEMPLICE_SICURA.contiene(semplice_ciclica)
    assert not FAMIGLIA_SEMPLICE_SICURA.contiene(rovesciata_sicura)
    assert FAMIGLIA_SEMPLICE_SICURA.contiene(P("DCS SCD SCD"))
    assert FAMIGLIA_TUTTE.contiene(rovesciata_sicura)


def test_famiglie_sul_dominio(servizio):
    conta = {f: sum(f.contiene(p) for p in servizio.procedure)
             for f in (FAMIGLIA_TUTTE, FAMIGLIA_SEMPLICE, FAMIGLIA_SICURA,
                       FAMIGLIA_SEMPLICE_SICURA)}
    assert conta == {FAMIGLIA_TUTTE: 1728, FAMIGLIA_SEMPLICE: 216,
                     FAMIGLIA_SICURA: 4 ** 3 * 8, FAMIGLIA_SEMPLICE_SICURA: 64}


def test_confronto_strutturato(servizio):
    p, q = P("CSD CSD CSD"), P("CSD CSD CDS", (1, 0, 0))
    r = servizio.confronta(p, q, carta=0)
    assert isinstance(r, ConfrontoProcedure)
    assert r.stessa_procedura is False
    assert r.stessa_trasformazione is False
    assert r.carta == 0
    assert r.stesso_effetto_carta == servizio.stesso_effetto_carta(p, q, 0)
    assert r.costi == (p.costo, q.costo)
    assert r.semplici == (True, False)
    assert r.sicure == (True, False)
    senza_carta = servizio.confronta(p, p)
    assert senza_carta.stessa_procedura and senza_carta.stessa_trasformazione
    assert senza_carta.carta is None and senza_carta.stesso_effetto_carta is None
    # nessun testo preformattato nel risultato
    for campo in dataclasses.fields(r):
        assert not isinstance(getattr(r, campo.name), str)


# ═══════════════════════════════ chiavi ═════════════════════════════════════

def test_chiavi_dichiarate():
    p = P("CDS DCS SCD", (1, 0, 1))
    n, m = p.numero_tavola, p.indice_rovesciamenti
    assert chiave_storica(p) == (2, n)
    assert chiave_sicura(p) == (2, 1, 2, m, n)
    assert chiave_costo("k2", "k1")(p) == (1, 2, m, n)
    assert chiave_costo()(p) == (m, n)
    with pytest.raises(ValueError):
        chiave_costo("k4")


def test_le_chiavi_sono_ordini_totali(servizio):
    for chiave in (chiave_sicura, chiave_costo("k1"), chiave_costo("k3", "k2")):
        valori = [chiave(p) for p in servizio.procedure]
        assert len(set(valori)) == 1728


def test_ordina_non_dipende_dall_ordine_d_ingresso(servizio):
    tutte = list(servizio.procedure)
    avanti = servizio.ordina(tutte, chiave_sicura)
    indietro = servizio.ordina(list(reversed(tutte)), chiave_sicura)
    assert avanti == indietro and isinstance(avanti, tuple)


# ═══════════════════════════════ architettura ═══════════════════════════════

def test_il_servizio_non_importa_gui_ne_tkinter():
    codice = ("import sys; import gioco27.services.procedure as m; "
              "m.servizio_procedure().procedure; "
              "print(any(k == 'tkinter' or k.startswith('gioco27.gui') "
              "for k in sys.modules))")
    out = subprocess.run([sys.executable, "-c", codice], capture_output=True,
                         text=True, check=True).stdout.strip()
    assert out == "False"


def test_il_servizio_condiviso_e_unico():
    assert servizio_procedure() is servizio_procedure()
    assert isinstance(servizio_procedure(), ServizioProcedure)


def test_nessun_secondo_modello_di_procedura():
    import gioco27.services.procedure as m
    nomi = [n for n in dir(m) if n.lower().startswith("procedura")]
    assert nomi == ["ProceduraGioco", "ProceduraNonValida"]
