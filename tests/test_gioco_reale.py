"""Test del modulo gioco_reale: fisica, tavola, ancore del libro, trucco."""
import pytest
from gioco27.core import gioco_reale as gr


def test_impilamenti_prima_crisi():
    # CDS e DSC si scambiano, le altre quattro coincidono
    assert gr.IMPILAMENTO_DI["CDS"] == "DSC"
    assert gr.IMPILAMENTO_DI["DSC"] == "CDS"
    for s in ("SCD", "SDC", "CSD", "DCS"):
        assert gr.IMPILAMENTO_DI[s] == s


def test_numerazione_tavola():
    assert gr.numero_tavola(("CDS", "CDS", "CSD")) == 100
    assert gr.numero_tavola(("CDS", "SDC", "CSD")) == 82
    for n in (0, 1, 82, 100, 215):
        assert gr.numero_tavola(gr.mescolamenti_da_numero(n)) == n


def test_ancore_libro():
    assert gr.riga_tavola(100)["assi"] == (13, 8, 18)
    assert gr.riga_tavola(82)["assi"] == (10, 8, 21)
    # tabella completa dell'esempio del cap. 5 (riga 82)
    T82 = gr.riga_tavola(82)["T"]
    assert T82 == [10, 11, 9, 16, 17, 15, 13, 14, 12, 1, 2, 0, 7, 8, 6,
                   4, 5, 3, 19, 20, 18, 25, 26, 24, 22, 23, 21]


def test_fisica_uguale_algebra():
    for n in range(216):
        mesc = gr.mescolamenti_da_numero(n)
        assert gr.T_da_partita(mesc) == gr.T_da_tabellone(mesc)


def test_statistiche_capitolo_100():
    st = gr.statistiche_tavola()
    assert st["periodi"] == {1: 1, 2: 63, 3: 26, 6: 126}
    assert st["autoinverse"] == 64
    assert len(st["tipi_ciclo"]) == 7
    # Ogni cifra ternaria ha 3 punti fissi per l'identita' (1 scelta),
    # 1 per una trasposizione (3 scelte), 0 per un 3-ciclo (2 scelte).
    # Sulle tre cifre: 27 -> 1; 9 -> 3*3; 3 -> 3*3**2;
    # 1 -> 3**3; zero -> 6**3 - 4**3. Atteso indipendente dalla tavola.
    assert st["punti_fissi"] == {0: 152, 1: 27, 3: 27, 9: 9, 27: 1}
    # totale coerente
    assert sum(st["periodi"].values()) == 216


def test_controllo_statistiche_rifiuta_distribuzione_errata(monkeypatch):
    original = gr.statistiche_tavola

    def wrong(*args, **kwargs):
        result = original(*args, **kwargs)
        result["punti_fissi"] = {999: 216}
        return result

    monkeypatch.setattr(gr, "statistiche_tavola", wrong)
    with pytest.raises(AssertionError):
        test_statistiche_capitolo_100()


def test_ricostruzione_assi():
    for n in (0, 5, 82, 100, 137, 215):
        r = gr.riga_tavola(n)
        mesc, num = gr.tabellone_da_assi(*r["assi"])
        assert (mesc, num) == (r["mescolamenti"], n)
    with pytest.raises(ValueError):
        gr.tabellone_da_assi(0, 0, 0)      # incompatibili
    with pytest.raises(ValueError):
        gr.tabellone_da_assi(-1, 5, 30)    # fuori intervallo


def test_risolvi_trucco_completo():
    for c in range(0, 27, 5):
        for t in range(27):
            sol = gr.risolvi_trucco(c, t)
            assert sol["T"][c] == t
    with pytest.raises(ValueError):
        gr.risolvi_trucco(27, 0)


def test_validazione_input():
    with pytest.raises(ValueError):
        gr.esegui_partita(["CDS", "XXX", "SCD"])
    with pytest.raises(ValueError):
        gr.esegui_partita(["CDS", "SCD"])
    with pytest.raises(ValueError):
        gr.mescolamenti_da_numero(216)
