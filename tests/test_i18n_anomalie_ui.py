"""
Anomalie i18n rilevate a mano con l'interfaccia in inglese.

Coprono SOLO le schermate segnalate: scheda Anteprima (Preview) e, nell'Explorer,
riepilogo dei passi (Numeric), traccia di riscrittura (Rewrite trace) e passi
parziali (Partial steps). L'italiano deve restare identico a prima; l'inglese
non deve più mostrare le stringhe italiane; formule, codici e risultati non
cambiano con la lingua.
"""
import re
from string import Formatter

import pytest

EXPRS = [
    "(CDS_U x SCD_U x SCD_U) o MSC o (DCS_U x SCD_U x SCD_U) o MSC o "
    "(SDC_U x CSD_U x DSC_U) o MSC",
    "(MSC o (CDS_U x SCD_U x SCD_U)) o (MSC o MSC)",
    "I o MSC o I o (SCD_U x SCD_U x SCD_U)",
    "MSC o (CDS_U x CDS_U x CDS_U) o MSC o (SDC_U x SCD_U x CSD_U)",
]

NEW_KEYS_PREFIXES = ("preview.", "explorer.trace.", "explorer.eval.",
                     "explorer.rewrite.legend")


@pytest.fixture(autouse=True)
def italian_default():
    from gioco27.gui import i18n

    i18n.set_language("it")
    yield
    i18n.set_language("it")


def _process(expr, language):
    from gioco27.gui import i18n
    from gioco27.core.algebra import Controller

    i18n.set_language(language)
    return Controller().process(expr)


# ───────────────────────────── cataloghi ────────────────────────────────────

def test_nuove_chiavi_simmetriche_con_placeholder_coerenti():
    from gioco27.gui.i18n import CATALOGS

    it, en = CATALOGS["it"], CATALOGS["en"]
    assert set(it) == set(en)
    assert len(it) == 2118  # A4-FIX: +10 etichette localizzate per export/CLI
    new = {k for k in it if k.startswith(NEW_KEYS_PREFIXES)}
    assert len(new) == 32
    fields = lambda s: sorted(n for _, n, _, _ in Formatter().parse(s) if n)
    for key in new:
        assert fields(it[key]) == fields(en[key]), key
        assert it[key] != en[key], key


# ───────────────────────────── Explorer (core) ──────────────────────────────

ITALIAN_TRACE = ("Espressione iniziale", "Appiattimento composizioni",
                 "Trasporto MSC", "Riduzione potenze MSC",
                 "Composizione Kronecker consecutivi", "Forma normale finale",
                 "Rimozione identità", "Regola R1", "Regola R2", "Regola R3",
                 "Input originale dopo il parsing", "si legge da DESTRA a SINISTRA",
                 "La composizione è associativa", "fattore per fattore",
                 "esponente MSC residuo", "gli atomi I vengono eliminati")


def _trace_text(result):
    return "\n".join(f"{s.rule}\n{s.detail}" for s in result["rewrite_trace"])


def test_riepilogo_numeric_in_inglese():
    r = _process(EXPRS[0], "en")
    assert r["norm_steps"] == (
        "Initial expression  →  MSC transport (step 1)  →  MSC transport (step 2)"
        "  →  MSC transport (step 3)  →  Reducing MSC powers  →  "
        "Combining consecutive Kronecker products  →  Final normal form")
    flat = _process(EXPRS[1], "en")["norm_steps"]
    assert flat.startswith("Initial expression  →  Flattening compositions")


def test_riepilogo_numeric_in_italiano_invariato():
    r = _process(EXPRS[0], "it")
    assert r["norm_steps"] == (
        "Espressione iniziale  →  Trasporto MSC (passo 1)  →  Trasporto MSC (passo 2)"
        "  →  Trasporto MSC (passo 3)  →  Riduzione potenze MSC  →  "
        "Composizione Kronecker consecutivi  →  Forma normale finale")


def test_traccia_riscrittura_in_inglese():
    text = "\n".join(_trace_text(_process(e, "en")) for e in EXPRS)
    for italian in ITALIAN_TRACE:
        assert italian not in text, italian
    for english in ("Initial expression", "Original input after parsing.",
                    "The composition ∘ is read from RIGHT to LEFT",
                    "Flattening compositions",
                    "Composition is associative: the parentheses around ∘ do not "
                    "change the result and are removed.",
                    "Removing identities", "MSC transport (step 1)", "Rule R1",
                    "Reducing MSC powers", "Rule R2",
                    "Combining consecutive Kronecker products", "Rule R3",
                    "factor by factor:", "Final normal form",
                    "residual MSC exponent", "k ∈ {0,1,2}"):
        assert english in text, english


def test_traccia_riscrittura_in_italiano():
    text = "\n".join(_trace_text(_process(e, "it")) for e in EXPRS)
    for italian in ("Espressione iniziale", "Appiattimento composizioni",
                    "Trasporto MSC (passo 1)", "Riduzione potenze MSC",
                    "Composizione Kronecker consecutivi", "Forma normale finale",
                    "Rimozione identità", "Input originale dopo il parsing.",
                    "La composizione è associativa: le parentesi attorno a ∘ "
                    "non cambiano il risultato e vengono eliminate.",
                    "fattore per fattore:", "k ∈ {0,1,2} mescolamenti"):
        assert italian in text, italian


def test_passi_parziali_atom_atomo():
    en = _process(EXPRS[0], "en")["partial_descriptions"]
    it = _process(EXPRS[0], "it")["partial_descriptions"]
    assert any(d.startswith("Atom: ") for d in en)
    assert not any(d.startswith(("Atomo", "Atomic")) for d in en)
    assert any(d.startswith("Atomo: ") for d in it)
    assert any(d.startswith("Kronecker ⊗: ") for d in en)
    joined = "\n".join(en)
    assert "Composizione" not in joined and "risultato precedente" not in joined


def test_formule_codici_e_risultati_non_dipendono_dalla_lingua():
    keys = ("ok", "error", "normalized_str", "perm", "signature", "period",
            "inverse_perm", "partial_perms", "partial_signatures",
            "normal_form_kind", "msc_exponent", "kron_factors_repr")
    for expr in EXPRS:
        it, en = _process(expr, "it"), _process(expr, "en")
        for key in keys:
            assert it.get(key) == en.get(key), (expr, key)
        for s_it, s_en in zip(it["rewrite_trace"], en["rewrite_trace"]):
            assert (s_it.expr_before, s_it.expr_after, s_it.state_after) == \
                   (s_en.expr_before, s_en.expr_after, s_en.state_after)
            math = lambda t: re.findall(r"[A-Z]{2,}_[A-Z]|MSC\^?\d?|[∘⊗→]|R\d", t)
            assert math(s_it.detail) == math(s_en.detail)
        assert len(it["rewrite_trace"]) == len(en["rewrite_trace"])


# ───────────────────────── Explorer: pannelli GUI ───────────────────────────

def _fake_explorer():
    from gioco27.gui.explorer_tab import ExplorerTabMixin

    class _FakeExplorer(ExplorerTabMixin):
        """Cattura cosa _explorer_display scrive nei widget, senza Tk."""

        def __init__(self):
            self.out = {}
            self._exp_can_factors = ["f0", "f1", "f2"]

        def __getattr__(self, name):
            if name.startswith("_exp_"):
                return name
            raise AttributeError(name)

        def _exp_set(self, widget, text, **_kw):
            self.out[widget] = str(text)

        _exp_set_colored = _exp_set

    return _FakeExplorer()


def _display(expr, language):
    from gioco27.gui.explorer_tab import ExplorerTabMixin

    fake = _fake_explorer()
    r = _process(expr, language)
    try:
        ExplorerTabMixin._explorer_display(fake, r)
    except AttributeError:
        pass          # parti successive (matrici, pulsanti) non interessano qui
    return fake.out


@pytest.mark.parametrize("language", ["it", "en"])
def test_pannelli_explorer(language):
    out = _display(EXPRS[0], language)
    rewrite, partial, summary = out["_exp_rewrite"], out["_exp_eval"], out["_exp_steps_sum"]
    for formula in ("R1", "R2", "R3", "R4", "MSC ∘ (a ⊗ b ⊗ c)  =  (c ⊗ a ⊗ b) ∘ MSC",
                    "MSC ∘ MSC ∘ MSC  =  I", "(a⊗b⊗c) ∘ (d⊗e⊗f)  =  (a∘d ⊗ b∘e ⊗ c∘f)",
                    "I ∘ X  =  X ∘ I  =  X", "R1–R4"):
        assert formula in rewrite, formula
    if language == "en":
        for italian in ("REGOLE DI RISCRITTURA", "Trasporto", "Potenze", "Fusione",
                        "Identità", "Prima/Dopo", "«Espressione»", "NOTA SULL'ORDINE",
                        "APPLICAZIONE", "RISCRITTURA", "Espressione iniziale",
                        "Input originale", "Appiattimento"):
            assert italian not in rewrite, italian
        for english in ("REWRITE RULES", "Transport", "Powers", "Merging", "Identity",
                        "Before/After", "NOTE ON ORDER",
                        "APPLICATION of the permutation: from RIGHT to LEFT",
                        "algebraic REWRITING (this tab)",
                        "Step 0 · Initial expression",
                        "Note: Original input after parsing.",
                        "“Partial steps”"):
            assert english in rewrite, english
        assert "Atom: " in partial and "Atomo" not in partial
        assert "perm" in partial and "permutation vector" in partial
        assert summary.startswith("Initial expression")
    else:
        for italian in ("REGOLE DI RISCRITTURA", "R1  Trasporto", "R2  Potenze",
                        "R3  Fusione", "R4  Identità", "«Prima/Dopo»",
                        "NOTA SULL'ORDINE", "Passo 0 · Espressione iniziale",
                        "Nota: Input originale dopo il parsing."):
            assert italian in rewrite, italian
        assert "Atomo: " in partial
        assert summary.startswith("Espressione iniziale")


# ─────────────────────────────── Anteprima ──────────────────────────────────

def _widget_texts(widget):
    texts = []
    try:
        texts.append(str(widget.cget("text")))
    except Exception:
        pass
    for child in widget.winfo_children():
        texts.extend(_widget_texts(child))
    return texts


@pytest.mark.parametrize("language", ["it", "en"])
def test_scheda_anteprima(language):
    tk = pytest.importorskip("tkinter")
    from gioco27.gui import i18n
    from gioco27.gui.preview_tab import PreviewTabMixin

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    root.withdraw()

    class Fake(PreviewTabMixin):
        notified = None

        def _notify_T_changed(self, perm):
            self.notified = perm

        def _open_export_dialog(self, **kw):
            pass

    try:
        i18n.set_language(language)
        fake = Fake()
        frame = fake._build_anteprima_tab(root)
        texts = "\n".join(_widget_texts(frame))
        placeholder = fake._prev_result.get("1.0", "end")
        fake._calcola_anteprima()
        result = fake._prev_result.get("1.0", "end")
        perm = list(fake.notified)
        frame.destroy()
    finally:
        i18n.set_language("it")
        root.destroy()

    if language == "en":
        for italian in ("Anteprima singola combinazione", "Parametri", "Stadio 0",
                        "Stadio 1", "Stadio 2", "Calcola", "Esporta LaTeX / SVG",
                        "Risultato", "carte", "terzine", "pacchetti"):
            assert italian not in texts, italian
        for english in ("Single-combination preview", "Parameters", "Stage 0",
                        "Stage 1", "Stage 2", "▶  Calculate", "Export LaTeX / SVG",
                        "Result", "P0  (cards)"):
            assert english in texts, english
        assert "Imposta P e J" not in placeholder and "press  ▶ Calculate" in placeholder
        assert "Symbolic T:" in result and "Permutation T:" in result
        assert "Stage 0:  " in result
        assert "T simbolica" not in result and "T permutazione" not in result
    else:
        for italian in ("🔍  Anteprima singola combinazione", "  Parametri  ",
                        "Stadio 0", "  ▶  Calcola  ", "📄  Esporta LaTeX / SVG",
                        "  Risultato  ", "P0  (carte)"):
            assert italian in texts, italian
        assert placeholder.startswith(
            "Imposta P e J per i tre stadi qui sopra e premi  ▶ Calcola.")
        assert "T simbolica:  " in result and "T permutazione:\n" in result
        assert "Stadio 0:  " in result
    # formule e risultati identici nelle due lingue
    assert re.search(r"Stage0 = \S.* ∘ MSC ∘ \S", result)
    assert "SCD_U" in result and "I_3" in result
    assert "T = A2 ∘ MSC ∘ A1 ∘ MSC ∘ A0 ∘ MSC" in result
    assert "[ 0]→" in result
    assert len(perm) == 27 and sorted(perm) == list(range(27))
