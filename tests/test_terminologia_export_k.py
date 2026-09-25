"""Compartimento K — nomenclatura dei gruppi negli export 4.0.

Convenzione corrente: H = 216 trasformazioni separabili, Γ = 648 (gruppo
esteso), S27 ambiente. Il vecchio «G = GEN3^3» (216) resta solo negli
identificatori Python interni e nelle note storiche esplicite.
"""
import re

import pytest

from gioco27 import i18n
from gioco27.core.group_theory import get_group_data
from gioco27.gui import export_group_dialog as egd

#: il vecchio nome del gruppo di 216 usato come nomenclatura corrente
VECCHIO_G = re.compile(r"(?<![A-Za-z_\\])(?:\|G\||Z\(G\)|\$G\$|\[G:|G = GEN3|G = S3|"
                       r"(?:di|of|in) G\b)")

#: note che citano G di proposito, come nome storico (libro, codice legacy)
NOTE_STORICHE = {"lab.legacy_note", "glossary.long.group_h", "glossary.long.gaia",
                 "guide.s09.extended_group"}
MARCATORI_STORICI = ("storic", "libro", "legacy", "book", "Gaia", "core")


@pytest.mark.parametrize("lingua", ["it", "en"])
def test_testi_di_export_usano_h(lingua):
    export = {k: v for k, v in i18n.CATALOGS[lingua].items()
              if k.startswith("export.document.")}
    assert export
    vecchi = {k: v for k, v in export.items() if VECCHIO_G.search(v)}
    assert not vecchi, vecchi
    for k in ("export.document.conjugacy.txt_summary", "export.document.cayley.row_axis",
              "export.document.conjugacy.latex.classes"):
        assert "|H|" in export[k], k


@pytest.mark.parametrize("lingua", ["it", "en"])
def test_g_solo_in_note_storiche_esplicite(lingua):
    trovati = {k for k, v in i18n.CATALOGS[lingua].items()
               if re.search(r"(?<![A-Za-z_\\])G(?: ≅| =|\b(?= \(cap| si chiama| is still))", v)
               or VECCHIO_G.search(v)}
    assert trovati <= NOTE_STORICHE, sorted(trovati - NOTE_STORICHE)
    for k in trovati:
        assert any(m in i18n.CATALOGS[lingua][k] for m in MARCATORI_STORICI), k


def _finto(classe, **attr):
    d = object.__new__(classe)          # solo i generatori di testo, niente Tk
    for k, v in attr.items():
        setattr(d, k, v)
    return d


@pytest.mark.parametrize("lingua", ["it", "en"])
def test_export_latex_e_svg_generati(lingua):
    precedente = i18n.get_language()
    i18n.set_language(lingua)
    try:
        gd = get_group_data()
        n = len(gd.kron_arr)
        assert n == 216
        con = _finto(egd.ConjugacyExportDialog, _gd=gd)
        cay = _finto(egd.CayleyExportDialog, _gd=gd, _ia=0, _ib=1,
                     _cols_hex=[egd._hue_hex(v, n) for v in range(n)])
        testi = {"tex_classes": con._latex_classes(), "svg_grid": con._svg_grid(),
                 "svg_heat": cay._svg_heatmap(), "tex_grid": cay._latex_tikz(),
                 "tex_calc": cay._latex_calc()}
    finally:
        i18n.set_language(precedente)
    for nome, testo in testi.items():
        testo = getattr(testo, "testo", testo)
        testo = testo if isinstance(testo, str) else str(testo)
        assert not VECCHIO_G.search(testo), (nome, VECCHIO_G.search(testo).group(0))
    assert "|H| = 216" in str(testi["tex_classes"])
    assert "|H| = 216" in str(testi["svg_heat"])
