"""
Blocco i18n 14 — Guida completa bilingue italiano/inglese.

La Guida (`gui/guide.py`) non contiene più testo leggibile: struttura, tag,
formule e codici restano nel modulo, i testi stanno nei cataloghi `guide.*`
di `gui/i18n.py`. Questi test controllano entrambe le lingue, la simmetria dei
cataloghi, il fallback, l'invarianza di struttura/ancore/formule e
l'allineamento dell'inglese con le etichette reali dell'interfaccia.
"""
import ast
import pathlib
import re
from collections import Counter
from string import Formatter
from types import SimpleNamespace

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GUIDE = ROOT / "gioco27" / "gui" / "guide.py"

N_SECTIONS = 33
N_SEGMENTS = 542
N_GUIDE_KEYS = 354

# Chiavi il cui valore è legittimamente identico nelle due lingue.
SAME_IN_BOTH = {
    "guide.export_heading",        # «Export» è la parola usata in entrambe le UI
    "guide.s26.csv.t_symbolic",    # pura formula
    "guide.s27.approx.1728",       # numero
}


@pytest.fixture(autouse=True)
def italian_default():
    from gioco27.gui import i18n

    i18n.set_language("it")
    yield
    i18n.set_language("it")


def _segments(language):
    from gioco27.gui.guide import render_guide_segments
    return render_guide_segments(language)


def _text(language):
    return "".join(text for _tag, text in _segments(language))


def _norm(text):
    return re.sub(r"\s+", " ", text).strip()


def _guide_keys(catalog):
    return {k for k in catalog if k.startswith("guide.")}


# ───────────────────────────── contenuto completo ──────────────────────────

def test_guida_completa_in_italiano():
    from gioco27.gui.i18n import CATALOGS

    text = _text("it")
    segments = _segments("it")
    assert [t for t, _ in segments].count("h2") == N_SECTIONS
    for phrase in ("Gioco delle 27 carte  —  Guida completa & How-To",
                   "Il gioco delle 27 carte è un classico trucco di magia matematica",
                   "Relazione fondamentale di commutazione con MSC",
                   "Il programma richiede Python 3.9 o superiore",
                   "Domande frequenti (FAQ)",
                   "I sette sotto-tab"):
        assert phrase in text
    # Nessuna chiave guide.* manca in italiano: il testo non è mai una chiave.
    assert not re.search(r"\bguide\.s\d\d\.", text)
    assert len(_guide_keys(CATALOGS["it"])) == N_GUIDE_KEYS


def test_guida_completa_in_inglese():
    from gioco27.gui.i18n import CATALOGS

    text = _text("en")
    assert [t for t, _ in _segments("en")].count("h2") == N_SECTIONS
    for phrase in ("27-card trick  —  Complete Guide & How-To",
                   "The 27-card trick is a classic piece of mathematical magic",
                   "Fundamental commutation relation with MSC",
                   "The program requires Python 3.9 or later",
                   "Frequently asked questions (FAQ)",
                   "The seven sub-tabs", "the seven sub-tabs"):
        assert phrase in text
    assert not re.search(r"\bguide\.s\d\d\.", text)
    it, en = CATALOGS["it"], CATALOGS["en"]
    identical = {k for k in _guide_keys(it) if it[k] == en[k]}
    assert identical == SAME_IN_BOTH, identical ^ SAME_IN_BOTH


@pytest.mark.parametrize("language, titles", [
    ("it", ["Il Gioco Reale — le 1 728 sequenze canoniche",
            "Tab Explorer — analisi algebrica, decomposizioni e protocollo",
            "Finestra Tavola di Cayley", "Glossario dei termini"]),
    ("en", ["The Real Game — the 1 728 canonical sequences",
            "Explorer tab — algebraic analysis, decompositions, and protocol",
            "Cayley Table window", "Glossary of terms"]),
])
def test_sezioni_principali_presenti(language, titles):
    heads = [text for tag, text in _segments(language) if tag == "h2"]
    toc = [text for tag, text in _segments(language) if tag == "toc"]
    for title in titles:
        assert any(title in h for h in heads), title
        assert any(title in t for t in toc), title


# ─────────────────────── cambio lingua e fallback ──────────────────────────

def test_cambio_lingua_segue_la_lingua_attiva_e_la_ripristina():
    from gioco27.gui import i18n
    from gioco27.gui.guide import build_guide_content

    i18n.set_language("en")
    parts = []
    build_guide_content(lambda t, s: parts.append(s), lambda: None)
    assert parts[0].startswith("27-card trick")

    i18n.set_language("it")
    assert _text("en").startswith("27-card trick")
    assert i18n.get_language() == "it"       # ripristinata
    assert _text(None).startswith("Gioco delle 27 carte")


def test_fallback_inglese_italiano_per_chiave_mancante(monkeypatch):
    from gioco27.gui import i18n

    monkeypatch.delitem(i18n.CATALOGS["en"], "guide.s07.intro")
    text = _text("en")
    assert "Per qualsiasi operatore decomponibile A = A₂ ⊗ A₁ ⊗ A₀ vale" in text
    assert "Fundamental commutation relation with MSC" in text


def test_cataloghi_guida_simmetrici_e_placeholder_identici():
    from gioco27.gui.i18n import CATALOGS

    it, en = CATALOGS["it"], CATALOGS["en"]
    assert _guide_keys(it) == _guide_keys(en)
    fields = lambda s: sorted(n for _, n, _, _ in Formatter().parse(s) if n)
    for key in _guide_keys(it):
        assert fields(it[key]) == fields(en[key]), key
        # stessa impaginazione: righe, rientro iniziale, a capo finali
        shape = lambda s: (s.count("\n"), re.match(r"\s*", s).group(0),
                           re.search(r"\s*$", s).group(0))
        assert shape(it[key]) == shape(en[key]), key


def test_placeholder_nominati_usati_dalla_guida():
    from gioco27.gui.i18n import CATALOGS

    used = set()
    for value in (v for k, v in CATALOGS["it"].items() if k.startswith("guide.")):
        used |= {n for _, n, _, _ in Formatter().parse(value) if n}
    assert used == {"digits", "j_values", "msc_power", "order", "version"}


# ───────────────────────────── niente testo cablato ────────────────────────

_TECHNICAL_WORDS = {
    "body", "bullet", "code", "formula", "hilight", "note", "warn", "title",
    "numpy", "openpyxl", "pikepdf", "pypdf", "reportlab", "tkinter", "install",
    "permutazione", "simbolica", "simboliche", "distinte", "stage",
}


def test_guide_py_non_contiene_testo_leggibile_cablato():
    tree = ast.parse(GUIDE.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef)) and node.body \
                and isinstance(node.body[0], ast.Expr) \
                and isinstance(node.body[0].value, ast.Constant):
            docstrings.add(id(node.body[0].value))
    suspicious = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)) \
                or id(node) in docstrings:
            continue
        value = node.value
        if re.fullmatch(r"(guide|button|shuffle|label)\.[\w.]+", value):
            continue                                    # chiave di catalogo
        words = {w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", value)}
        words -= _TECHNICAL_WORDS
        words = {w for w in words if not re.search(r"[A-Z_]", w)}
        if words:
            suspicious.append(value)
    assert not suspicious, suspicious
    source = GUIDE.read_text(encoding="utf-8")
    for old in ("Il gioco delle 27 carte è un classico", "Formula errata (non usare)",
                "Il programma richiede Python", "Domande frequenti"):
        assert old not in source


# ─────────────────── struttura, ancore, formule invariate ───────────────────

def test_struttura_identica_nelle_due_lingue():
    it, en = _segments("it"), _segments("en")
    assert len(it) == len(en) == N_SEGMENTS
    assert [t for t, _ in it] == [t for t, _ in en]
    assert [t for t, _ in it].count("h1") == 1
    assert [t for t, _ in it].count("toc") == N_SECTIONS


def _anchor_numbers(language):
    """Replica la logica di app.py._build_guide_tab che crea le ancore secN."""
    out = []
    for tag, text in _segments(language):
        if tag == "h2":
            num = text.strip().split(".", 1)[0].strip()
            if num.isdigit():
                out.append(num)
    return out


def test_ancore_di_sezione_invariate_in_entrambe_le_lingue():
    expected = [str(n) for n in range(1, N_SECTIONS + 1)]
    assert _anchor_numbers("it") == expected
    assert _anchor_numbers("en") == expected
    app_src = (ROOT / "gioco27" / "gui" / "app.py").read_text(encoding="utf-8")
    used = set(re.findall(r'section="(\d+)"', app_src))
    used |= set(re.findall(r'_wrap_tab\([^)]*?,\s*"(\d+)"\)', app_src))
    assert used and used <= set(expected)


def test_navigazione_reale_con_widget_tk():
    tk = pytest.importorskip("tkinter")
    from gioco27.gui import i18n
    from gioco27.gui.app import App

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    root.withdraw()
    try:
        for language, first in (("it", "Gioco delle 27 carte"), ("en", "27-card trick")):
            i18n.set_language(language)
            fake = SimpleNamespace()
            frame = App._build_guide_tab(fake, root)
            assert sorted(fake._guide_marks, key=int) == \
                [str(n) for n in range(1, N_SECTIONS + 1)]
            txt = fake._guide_text
            assert txt.get("1.0", "1.end").startswith(first)
            line = txt.get(fake._guide_marks["24"], f"{fake._guide_marks['24']} lineend")
            assert line.startswith("24.  ")
            frame.destroy()
    finally:
        i18n.set_language("it")
        root.destroy()


_MATH = re.compile(r"[A-Z]{2,}_[A-Z0-9]+|I_3|R_U|GEN3|MSC|T_\w+|n_sim_distinte"
                   r"|[A-Za-z]?[₀-₉ᵢₖ⁻¹³²]+|\d[\d ]*\d|\d|[∘⊗≠→↔⟨⟩∈σ×·=]")


def test_formule_codici_e_numeri_invariati():
    it, en = _segments("it"), _segments("en")
    for (tag, a), (_, b) in zip(it, en):
        if tag in ("code",) and not re.search(r"[A-Za-z]{4,}", a):
            assert a == b
    # Segmenti formula privi di parole: identici byte per byte.
    for (tag, a), (_, b) in zip(it, en):
        if tag == "formula" and not re.search(r"[a-z]{3,}", a.replace("MSC", "")):
            assert a == b, a
    # Su tutto il testo i token matematici/numerici coincidono, salvo le
    # differenze volute e documentate.
    diff_it = Counter(_MATH.findall(_text("it"))) - Counter(_MATH.findall(_text("en")))
    diff_en = Counter(_MATH.findall(_text("en"))) - Counter(_MATH.findall(_text("it")))
    # «Stadioᵢ» del glossario italiano diventa «Stageᵢ», come in glossary.long.stage;
    # le etichette UI inglesi scrivono «1,728»; «TABELLONE DI T⁻¹» ha la glossa inglese;
    # i decimali italiani «0,03» diventano «0.03» (stesse cifre, stessi token).
    assert diff_it == Counter({"1 728": 2, "1728": 1, "oᵢ": 1}), diff_it
    assert diff_en == Counter({"1": 3, "728": 3, "eᵢ": 1, "T⁻¹": 1}), diff_en
    for formula in ("MSC ∘ (A₂ ⊗ A₁ ⊗ A₀)  =  (A₀ ⊗ A₂ ⊗ A₁) ∘ MSC",
                    "f_k = P_k ∘ J_(k+1 mod 3)", "MSC^{(3−k) mod 3}",
                    "T  =  A₂ ∘ MSC ∘ A₁ ∘ MSC ∘ A₀ ∘ MSC", "{0,1,2}³",
                    "46 656 × 8³ = 23 887 872", "216³ = 10 077 696",
                    "Z(G)", "⟨A,B⟩", "S₃³", "SCD, SDC, CSD, DSC, CDS, DCS"):
        assert formula in _text("it") and formula in _text("en"), formula


def test_riferimenti_interni_uguali_nelle_due_lingue():
    it = re.findall(r"\bsezion[ei]\s+(\d+)(?:\s+e\s+(\d+))?", _text("it"))
    en = re.findall(r"\bsections?\s+(\d+)(?:\s+and\s+(\d+))?", _text("en"))
    assert it and sorted(it) == sorted(en)
    for pair in it:
        assert all(1 <= int(n) <= N_SECTIONS for n in pair if n)


# ─────────────── allineamento dell'inglese con l'interfaccia reale ──────────

def test_etichette_ui_inglesi_citate_nella_guida_inglese():
    from gioco27.gui.i18n import CATALOGS

    en = CATALOGS["en"]
    guide = _norm(_text("en"))
    keys = [
        # schede principali e sotto-tab
        "tab.start", "tab.simulator", "tab.table", "tab.preview", "tab.analysis",
        "tab.explorer", "tab.guide", "tab.cycles", "tab.distribution",
        "explorer.tab.numeric", "explorer.tab.rewrite", "explorer.tab.algebra",
        "explorer.tab.partial_steps", "explorer.tab.canonical", "explorer.tab.matrix",
        "explorer.tab.shuffle", "cycles.tab.disjoint", "cycles.tab.orbits",
        "distribution.tab.histogram", "distribution.tab.data_table",
        "simulator.tab.instructions", "simulator.tab.deck", "simulator.tab.practice",
        # barra azioni e preset
        "button.count", "button.generate", "button.reset_all", "button.beginner_mode",
        "button.cayley", "button.conjugacy", "button.protocol", "button.presentation",
        "button.verify", "button.settings", "button.exit", "button.cancel_export",
        "button.real_game", "button.uniform_j", "button.quick_reset",
        "label.combinations", "menu.pdf_detailed",
        # pulsanti e controlli citati
        "analysis.generate", "analysis.open_explorer", "shuffle.load_explorer",
        "simulator.calculate_sequence", "distribution.calculate",
        "explorer.button.decompositions_inverse", "explorer.button.export",
        "export.export_all", "shuffle.card_by_card", "shuffle.play",
        "banner.what_this_tab_does", "banner.open_guide",
        "onboarding.step1.title", "onboarding.step2.title", "onboarding.step3.title",
        "onboarding.button.try_simulator", "onboarding.button.load_real_game",
        "onboarding.button.go_preview", "onboarding.button.open_guide",
        "export.document.pdf.ace_position", "export.document.pdf.transpose_list",
        "export.document.pdf.undefined_indices",
    ]
    missing = []
    for key in keys:
        label = en[key].replace("{number}", "#1")
        label = _norm(label.split("#")[0] if key.endswith("ace_position") else label)
        label = label.rstrip(":").replace("…", "") if key != "button.generate" else label
        if label not in guide:
            missing.append((key, label))
    assert not missing, missing


def test_barra_azioni_localizzata_nella_guida():
    it, en = _text("it"), _text("en")
    for label in ("🔢  Conta", "⬇  Genera…", "↺  Reset tutto", "🔮  Cayley",
                  "✕  Annulla", "⏮  Reset", "Pross. step ⏭"):
        assert label in it
    for label in ("🔢  Count", "⬇  Generate…", "↺  Reset all", "🔮  Cayley",
                  "✕  Cancel", "⏮  Reset", "Next step ⏭"):
        assert label in en


def test_discrepanze_corrette_restano_corrette():
    """Pulsanti inesistenti citati prima del Blocco 14 non devono tornare."""
    for language in ("it", "en"):
        text = _text(language)
        assert "Genera CSV" not in text and "Genera PDF" not in text
        assert "Accessibile dall'Explorer" not in text
        assert re.search(r"(sezioni|sections) 26 (e|and) 32", text)
