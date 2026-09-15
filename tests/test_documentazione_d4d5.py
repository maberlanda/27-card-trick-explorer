"""D4-D5: guida confrontata con UI/export e limiti descritti senza promesse assolute."""
import ast
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _norm(text):
    return re.sub(r"\s+", " ", text).strip()


def _tree(path):
    return ast.parse((ROOT / path).read_text(encoding="utf-8"))


def _function(tree, name):
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)


def _localized_literal(node):
    """Resolve a literal/f-string tab label using the Italian i18n catalog."""
    from gioco27.gui.i18n import CATALOGS

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif (isinstance(value, ast.FormattedValue)
                  and isinstance(value.value, ast.Call)
                  and isinstance(value.value.func, ast.Name)
                  and value.value.func.id == "tr"
                  and value.value.args
                  and isinstance(value.value.args[0], ast.Constant)):
                parts.append(CATALOGS["it"][value.value.args[0].value])
            else:
                raise AssertionError("etichetta sotto-tab non risolvibile")
        return "".join(parts)
    raise AssertionError("etichetta sotto-tab non letterale/localizzata")


@pytest.fixture
def guide():
    tree = _tree("gioco27/gui/guide.py")
    return _norm("\n".join(n.value for n in ast.walk(tree)
                           if isinstance(n, ast.Constant) and isinstance(n.value, str)))


def test_d4_ordine_sottotab_come_costruiti_dalla_gui(guide):
    tree = _tree("gioco27/gui/explorer_tab.py")
    build = _function(tree, "_build_explorer_tab")
    methods = [n.func.attr for n in ast.walk(build) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute)
               and n.func.attr.startswith("_build_explorer_tab_")]
    names = []
    for method in methods:
        function = _function(tree, method)
        labels = [_localized_literal(kw.value)
                  for n in ast.walk(function) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute) and n.func.attr == "add"
                  for kw in n.keywords if kw.arg == "text"]
        assert len(labels) == 1
        names.append(_norm(labels[0]))
    assert len(names) == 7
    assert names[5] == "📐 Matrice" and names[6] == "🎴 Mescolamento"
    listed = guide.split("I sette sotto-tab", 1)[1].split("Pulsante 🔍", 1)[0]
    positions = [listed.index(name) for name in names]
    assert positions == sorted(positions)
    assert "Matrice (sesto sotto-tab dell'Explorer)" in guide
    assert "sei sotto-tab" not in guide


def test_d4_coniugio_dalla_barra_azioni(guide):
    tree = _tree("gioco27/gui/app.py")
    buttons = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
               and any(kw.arg == "command" and isinstance(kw.value, ast.Attribute)
                       and kw.value.attr == "_open_conjugacy"
                       for kw in n.keywords)]
    assert len(buttons) == 1
    text_node = next(kw.value for kw in buttons[0].keywords if kw.arg == "text")
    assert "Coniugio" in _localized_literal(text_node)
    assert any(kw.arg == "command" and isinstance(kw.value, ast.Attribute)
               and kw.value.attr == "_open_conjugacy" for kw in buttons[0].keywords)
    assert "Accessibile dal pulsante 🔬 Coniugio nella barra azioni" in guide
    assert "Accessibile dal tab Distribuzione" not in guide
    assert "calcolabili dal tab Distribuzione" not in guide


def test_d4_fogli_excel_di_analisi_reali(guide, tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    from gioco27.core.algebra import scrivi_excel
    path = tmp_path / "analisi.xlsx"
    scrivi_excel([], str(path))
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        names = wb.sheetnames
        assert names == ["Perm -> Simboliche", "Simbolica -> Perm"]
    finally:
        wb.close()
    section = guide.split("Analisi molteplicità — Excel", 1)[1].split("Analisi molteplicità — HTML", 1)[0]
    assert re.findall("«(.*?)»", section) == names
    assert "una riga per formula" in section
    assert "due fogli: «Perm -> Simboliche» e «Simbolica -> Perm»" in guide
    assert "Perm→Simboliche" not in guide and "Perm → Simboliche" not in guide


def test_d4_fogli_excel_grezzi_distinti(guide):
    function = _function(_tree("gioco27/gui/analysis_tab.py"), "_export_analisi_raw_excel")
    names = [n.value.value for n in ast.walk(function) if isinstance(n, ast.Assign)
             and isinstance(n.value, ast.Constant)
             and any(isinstance(t, ast.Attribute) and t.attr == "title" for t in n.targets)]
    names += [n.args[0].value for n in ast.walk(function) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute) and n.func.attr == "create_sheet"]
    assert names == ["Dati grezzi", "Analisi molteplicità"]
    assert "Due fogli: «Dati grezzi» (combinazioni) e «Analisi molteplicità» (riepilogo)" in guide


def test_d4_paginazione_dettagliata_non_contraddittoria(guide):
    from gioco27.core.detail_pdf import COMBOS_PER_PAGE
    assert COMBOS_PER_PAGE == 2
    section = guide.split("Export PDF dettagliato (carte, marcatori, periodo)", 1)[1]
    assert section.count("due combinazioni per pagina") == 2
    assert "una pagina ricca per combinazione" not in section


def test_d4_calcoli_normalmente_sequenziali(guide, monkeypatch):
    from gioco27.core import analysis, kronecker
    monkeypatch.delenv("GIOCO27_FORZA_DISTRIB_PARALLELA", raising=False)
    calls = []
    sentinel = object()
    monkeypatch.setattr(kronecker, "find_all_kron_decompositions",
                        lambda target, **kw: calls.append(target) or sentinel)
    assert kronecker.find_all_kron_decompositions_parallel(list(range(27)), n_workers=2) is sentinel
    assert len(calls) == 1
    indices = []
    monkeypatch.setattr(analysis, "_distribution_partial", lambda batch: indices.extend(batch) or {})
    monkeypatch.setattr(analysis, "_finalize_distribution", lambda data: data)
    monkeypatch.setattr(analysis, "ProcessPoolExecutor", lambda **kw: pytest.fail("pool inatteso"))
    assert analysis.compute_distribution_parallel(n_workers=2) == {}
    assert indices == list(range(216))
    assert "decomposizioni Kronecker e distribuzione sono normalmente sequenziali" in guide
    assert "thread di background" in guide
    assert "GIOCO27_FORZA_DISTRIB_PARALLELA" in guide
    assert "- Tab Distribuzione (statistica globale sul gruppo)" not in guide
    assert "- Ricerca delle decomposizioni Kronecker (Explorer)" not in guide


def _check_claims(text):
    text = _norm(text).lower()
    for obsolete in ("nessun export materializza", "la memoria non dipende più dal totale",
                     "memoria indipendente dal totale", "ogni 0,2 s", "ogni 0.2 s",
                     "csv identico byte per byte", "il csv prodotto è identico byte per byte"):
        assert obsolete not in text, obsolete
    assert "cooperativa" in text
    assert "pdf dettagliato" in text
    assert "globali" in text
    assert "librerie pdf" in text


@pytest.mark.parametrize("name", ["README.md", "NOTE_VERSIONE_3.1.1.md"])
def test_d5_limiti_dichiarati_senza_garanzie_assolute(name):
    _check_claims((ROOT / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("obsolete", ["Nessun export materializza le combinazioni in RAM",
                                     "La memoria non dipende più dal totale",
                                     "Controllo ogni 0,2 s", "CSV identico byte per byte"])
def test_d5_controlli_rifiutano_anche_la_coesistenza(obsolete):
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    with pytest.raises(AssertionError):
        _check_claims(text + "\n" + obsolete)


def test_d5_note_distinguono_cronologia_e_header_corrente():
    text = _norm((ROOT / "NOTE_VERSIONE_3.1.1.md").read_text(encoding="utf-8"))
    assert "tappe storiche: conteggi di test" in text
    assert "non allo stato corrente della suite" in text
    assert "**3.1.1** (218 test)" in text
    assert "**Totale: 218 test, tutti verdi.**" in text
    assert "`Stage0..2` e `A0..A2`" in text
    assert "i file non sono identici byte per byte" in text
