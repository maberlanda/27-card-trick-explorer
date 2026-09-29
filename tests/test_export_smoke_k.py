"""Compartimento K — smoke test di ogni formato di export e dei percorsi senza
le librerie facoltative.

Formati: CSV, PDF (standard, esteso, dettagliato), XLSX, LaTeX, SVG, HTML,
TXT, JSON (esperimenti J). Senza reportlab/openpyxl/pypdf/pikepdf il
programma deve importarsi per intero e dire quale libreria manca, invece di
un errore ambiguo.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FACOLTATIVE = ("reportlab", "openpyxl", "pypdf", "pikepdf")


def _filtri():
    f = [dict(p0="SCD_U", p1="SCD_U", p2="SCD_U", j0="I_3", j1="I_3", j2="I_3")
         for _ in range(3)]
    f[0]["j0"] = "*"
    return f                                     # 2 combinazioni


def _finto(classe, **attr):
    d = object.__new__(classe)                   # solo i generatori di testo, niente Tk
    for k, v in attr.items():
        setattr(d, k, v)
    return d


T = [(9 * ((i // 9 + 1) % 3) + i % 9) for i in range(27)]   # una permutazione di H


def test_csv(tmp_path):
    from gioco27.core.export_combinazioni import write_csv
    out = tmp_path / "c.csv"
    assert write_csv(str(out), _filtri()) == 2
    righe = out.read_text(encoding="utf-8").splitlines()
    assert len(righe) == 3 and ";" in righe[0]


@pytest.mark.parametrize("funzione", ["generate_pdf", "generate_pdf_ex", "generate_detail_pdf"])
def test_pdf(tmp_path, funzione):
    pytest.importorskip("reportlab")
    from gioco27.core import combinations, detail_pdf
    modulo = detail_pdf if funzione == "generate_detail_pdf" else combinations
    out = tmp_path / f"{funzione}.pdf"
    assert getattr(modulo, funzione)(str(out), _filtri()) == 2
    assert out.read_bytes()[:5] == b"%PDF-"


def test_xlsx(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    from gioco27.core.export_analisi import scrivi_excel
    out = tmp_path / "a.xlsx"
    scrivi_excel([{"perm_str": str(T), "simboliche": ["x"], "n_sim": 1}], str(out))
    assert openpyxl.load_workbook(out).sheetnames


def test_latex_svg_txt_html():
    from gioco27.core.group_theory import get_group_data
    from gioco27.gui import export_dialog as ed
    from gioco27.gui import export_group_dialog as egd
    from gioco27.gui.protocol_dialog import generate_protocol_html

    inv = [0] * 27
    for i, v in enumerate(T):
        inv[v] = i
    libretto = _finto(ed.ExportDialog, _decomps=[])
    tex = libretto._latex_perm(T, inv, "T")
    svg = libretto._svg_arrows(T, "T")
    txt = libretto._txt_summary(T, inv, "T")
    assert "\\" in tex and svg.lstrip().startswith("<") and "</svg>" in svg
    assert "T^-1" in txt and "C00" in txt

    gd = get_group_data()
    con = _finto(egd.ConjugacyExportDialog, _gd=gd)
    assert "\\begin" in con._latex_classes() and "</svg>" in con._svg_grid()

    html = generate_protocol_html({"perm": T, "inverse_perm": inv, "label": "T"})
    assert html.lstrip().lower().startswith("<!doctype html") and "</html>" in html.lower()


def test_json_esperimento(tmp_path):
    from gioco27.services import archivio
    from gioco27.services import esperimento as E
    doc = E.crea_documento({"riconoscimento": {"T": T}}, seed=None, titolo="smoke",
                           nota="", presentazione=None, cronologia=None, fonti=())
    out = tmp_path / "e.json"
    archivio.salva_documento(doc, out)
    assert json.loads(out.read_text(encoding="utf-8"))["schema"] == E.SCHEMA_ID
    assert archivio.carica_documento(out).verificato


# ─────────────────── senza le librerie facoltative ──────────────────────────

_BLOCCO = (
    "import sys\n"
    f"for m in {FACOLTATIVE!r}:\n"
    "    sys.modules[m] = None\n"                       # import -> ImportError(name=m)
)


def test_tutto_il_package_si_importa_senza_facoltative():
    codice = _BLOCCO + (
        "import pkgutil, importlib, gioco27\n"
        "for m in pkgutil.walk_packages(gioco27.__path__, 'gioco27.'):\n"
        "    if m.name.startswith('gioco27.gui'):\n"
        "        try:\n"
        "            import tkinter  # noqa\n"
        "        except ImportError:\n"
        "            continue\n"
        "    try:\n"
        "        importlib.import_module(m.name)\n"
        "    except ImportError as e:\n"
        "        # solo il disegno delle griglie PDF dipende da reportlab gia' all'import;\n"
        "        # e' caricato pigramente dai soli export PDF\n"
        "        assert m.name == 'gioco27.core.pdfgrid' and e.name.startswith('reportlab'), m.name\n"
        "from gioco27.core.gioco_reale import selftest\n"
        "print(selftest()['esito'])\n")
    r = subprocess.run([sys.executable, "-B", "-c", codice], cwd=ROOT,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().endswith("TUTTO OK")


@pytest.mark.parametrize("libreria,chiamata", [
    ("reportlab", "from gioco27.core.combinations import generate_pdf; generate_pdf(OUT + '.pdf', F)"),
    ("openpyxl", "from gioco27.core.export_analisi import scrivi_excel; scrivi_excel([], OUT + '.xlsx')"),
])
def test_export_senza_libreria_dice_quale_manca(tmp_path, libreria, chiamata):
    codice = _BLOCCO + (
        f"OUT = {str(tmp_path / 'x')!r}\n"
        f"F = {_filtri()!r}\n"
        "from gioco27.gui.errori import per_utente, per_file\n"
        "from gioco27.i18n import set_language\n"
        "try:\n"
        f"    {chiamata}\n"
        "except ImportError as e:\n"
        "    for lingua in ('it', 'en'):\n"
        "        set_language(lingua)\n"
        "        print(per_utente(e)[0] + ' | ' + per_utente(e)[1].replace(chr(10), ' '))\n"
        "        print(per_file(e, OUT)[1].replace(chr(10), ' '))\n"
        "else:\n"
        "    print('NESSUN ERRORE')\n")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-B", "-c", codice], cwd=ROOT,
                       capture_output=True, encoding="utf-8", env=env, timeout=300)
    assert r.returncode == 0, r.stderr
    righe = r.stdout.strip().splitlines()
    assert len(righe) == 4, r.stdout
    assert righe[0].startswith("Libreria facoltativa mancante")
    assert righe[2].startswith("Optional library missing")
    assert all(f"pip install {libreria}" in x for x in righe)
    assert not (tmp_path / "x.pdf").exists() and not (tmp_path / "x.xlsx").exists()


def test_dipendenza_mancante_riconosce_solo_le_facoltative():
    from gioco27.gui.errori import dipendenza_mancante
    assert dipendenza_mancante(ImportError("x", name="reportlab.pdfgen")) == "reportlab"
    assert dipendenza_mancante(ImportError("x", name="numpy")) is None
    assert dipendenza_mancante(ValueError("reportlab")) is None
