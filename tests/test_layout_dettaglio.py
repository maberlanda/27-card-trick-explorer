"""
Layout della colonna centrale del PDF dettagliato.

I due tabelloni stavano a metà altezza, sotto la tabella degli Assi: il blocco
più recente finiva nel punto meno visibile della pagina mentre in alto restava
spazio inutilizzato. Ora il riquadro è allineato in cima come i mazzi, e i
blocchi ROVESCIAMENTO e MOLTIPLICAZIONE scendono sotto.

La metà inferiore del foglio ha poco margine: uno spostamento eccessivo
uscirebbe dalla pagina. Questi test verificano l'ordine dei blocchi e
l'ingombro, e — se pypdfium2 è disponibile — che non ci sia inchiostro fuori
dai margini.
"""

import pytest

from gioco27.core.detail_pdf import (ALTEZZA_TABELLONI, OFF_MOLTIPLICAZIONE,
                                     OFF_ROVESCIAMENTO, OFF_TABELLONI)

#: geometria della pagina, come in render_detail_pages
PAGE_H = 842.0                     # A3 orizzontale
Y_TOPS = (PAGE_H - 14, PAGE_H / 2 - 10)
YB = [y - 76 for y in Y_TOPS]      # bordo superiore dei mazzi, per metà


def test_ordine_dei_blocchi():
    """Dall'alto: tabelloni, poi ROVESCIAMENTO, poi MOLTIPLICAZIONE."""
    assert OFF_TABELLONI > OFF_ROVESCIAMENTO > OFF_MOLTIPLICAZIONE


def test_i_tabelloni_stanno_in_cima():
    """
    Il riquadro deve partire sopra il bordo dei mazzi, non a metà pagina:
    è la modifica richiesta.
    """
    assert OFF_TABELLONI > 0, "il riquadro non è allineato in cima"


def test_i_blocchi_non_si_sovrappongono():
    """
    Il riquadro dei tabelloni occupa ALTEZZA_TABELLONI punti verso il basso e
    non deve invadere il blocco MOLTIPLICAZIONE, che sta alla sua sinistra ma
    su un intervallo verticale sovrapponibile.
    """
    fondo_tabelloni = OFF_TABELLONI - ALTEZZA_TABELLONI
    assert fondo_tabelloni > OFF_MOLTIPLICAZIONE - 60, (
        "il riquadro scende sotto il blocco MOLTIPLICAZIONE")


def test_tutto_dentro_la_pagina():
    """
    Il controllo che conta: nella metà INFERIORE il fondo della pagina è a 0.
    Il blocco più basso è POSIZIONE ASSO, 44+26+4 punti sotto Y_MOLT.
    """
    FONDO_ASSI = 44 + 2 * 13 + 4      # come nel renderer
    for meta, yb in enumerate(YB):
        cima = yb + OFF_TABELLONI
        fondo = yb + OFF_MOLTIPLICAZIONE - FONDO_ASSI
        assert fondo > 0, f"metà {meta}: il blocco esce dalla pagina (y={fondo:.0f})"
        assert cima < PAGE_H, f"metà {meta}: il riquadro esce in alto"
    # la metà superiore non deve invadere quella inferiore
    Y_SEP = PAGE_H / 2 + 4
    assert YB[0] + OFF_MOLTIPLICAZIONE - FONDO_ASSI > Y_SEP, \
        "la metà superiore sconfina oltre la linea di separazione"


def test_nessun_inchiostro_fuori_dai_margini(tmp_path):
    """
    Verifica funzionale: si rasterizza la pagina e si controlla che i margini
    siano bianchi. Coglie gli sconfinamenti che il calcolo sulle costanti non
    prevede (testi lunghi, etichette adattate).
    """
    pdfium = pytest.importorskip("pypdfium2")
    pytest.importorskip("reportlab")
    import numpy as np
    from gioco27.core.detail_pdf import _generate_sequential, annotate_like_c

    params = [[("SCD_U", "SCD_U", "SCD_U", "I_3", "I_3", "I_3")] * 3,
              [("SDC_U", "CSD_U", "CDS_U", "I_3", "I_3", "R_U")] * 3]
    labels, transposes = annotate_like_c(params)
    out = tmp_path / "layout.pdf"
    _generate_sequential(str(out), params, labels, transposes)

    pagina = pdfium.PdfDocument(str(out))[0].render(scale=1.5).to_pil().convert("L")
    g = np.asarray(pagina)
    h, w = g.shape
    m = int(8 * 1.5)                      # 8 punti di margine
    bordi = {
        "alto":    g[:m, :],
        "basso":   g[h - m:, :],
        "sinistro": g[:, :m],
        "destro":  g[:, w - m:],
    }
    for nome, banda in bordi.items():
        sporchi = int((banda < 240).sum())
        assert sporchi == 0, f"inchiostro nel margine {nome}: {sporchi} pixel"


# ────────────────── etichette verticali centrate sul blocco ────────────────

def test_etichette_verticali_centrate_sui_blocchi():
    """
    `vtext` centra il testo ruotato sulla y ricevuta. Con due scostamenti
    fissi le etichette finivano SOTTO il testo che dovevano etichettare;
    ora si calcolano dal punto medio del blocco.
    """
    from gioco27.core.detail_pdf import (ALTEZZA_MOLTIPLICAZIONE,
                                         ALTEZZA_ROVESCIAMENTO)

    for cima, altezza, nome in (
            (OFF_ROVESCIAMENTO, ALTEZZA_ROVESCIAMENTO, "ROVESCIAMENTO"),
            (OFF_MOLTIPLICAZIONE, ALTEZZA_MOLTIPLICAZIONE, "MOLTIPLICAZIONE")):
        centro = cima - altezza / 2
        assert cima > centro > cima - altezza, \
            f"{nome}: l'etichetta non cade dentro il proprio blocco"


def test_le_due_etichette_non_si_accavallano():
    """
    Il testo ruotato è lungo: ROVESCIAMENTO ~78 pt, MOLTIPLICAZIONE ~90 pt.
    Centrati sui rispettivi blocchi non devono sovrapporsi.
    """
    from gioco27.core.detail_pdf import (ALTEZZA_MOLTIPLICAZIONE,
                                         ALTEZZA_ROVESCIAMENTO)
    LUNG_ROVESC, LUNG_MOLT = 78, 90
    fondo_rovesc = (OFF_ROVESCIAMENTO - ALTEZZA_ROVESCIAMENTO / 2) - LUNG_ROVESC / 2
    cima_molt = (OFF_MOLTIPLICAZIONE - ALTEZZA_MOLTIPLICAZIONE / 2) + LUNG_MOLT / 2
    assert fondo_rovesc > cima_molt, (
        f"le etichette si accavallano: ROVESCIAMENTO finisce a {fondo_rovesc:.0f}, "
        f"MOLTIPLICAZIONE comincia a {cima_molt:.0f}")


def test_le_etichette_non_usano_scostamenti_fissi():
    """
    I test sulle costanti non colgono chi rimette un numero magico nella
    chiamata a `vtext`. Qui si guarda l'AST: la y dev'essere calcolata dalle
    costanti di ingombro, non scritta a mano.
    """
    import ast
    import pathlib

    sorgente = (pathlib.Path(__file__).resolve().parent.parent
                / "gioco27" / "core" / "detail_pdf.py").read_text(encoding="utf-8")
    atteso = {"ROVESCIAMENTO": "ALTEZZA_ROVESCIAMENTO",
              "MOLTIPLICAZIONE": "ALTEZZA_MOLTIPLICAZIONE"}
    trovate = {}
    for nodo in ast.walk(ast.parse(sorgente)):
        if not (isinstance(nodo, ast.Call)
                and getattr(nodo.func, "id", None) == "vtext"):
            continue
        if not (nodo.args and isinstance(nodo.args[0], ast.Constant)):
            continue
        etichetta = nodo.args[0].value
        if etichetta not in atteso:
            continue
        nomi = {n.id for n in ast.walk(nodo.args[2]) if isinstance(n, ast.Name)}
        trovate[etichetta] = nomi

    assert set(trovate) == set(atteso), f"chiamate vtext trovate: {sorted(trovate)}"
    for etichetta, costante in atteso.items():
        assert costante in trovate[etichetta], (
            f"{etichetta}: la posizione non deriva da {costante} "
            f"(nomi usati: {sorted(trovate[etichetta])}) — scostamento fisso?")
