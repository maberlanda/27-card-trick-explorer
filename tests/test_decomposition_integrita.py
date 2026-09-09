"""Regressioni B9-B11, senza finestre o dipendenze dal timing dei thread."""
import html
import json
import re
from types import SimpleNamespace

import pytest

from gioco27.core import cache, kronecker
from gioco27.core.algebra import AlgebraEngine, Controller, Parser, Evaluator
from gioco27.core.constants import PERM3
from gioco27.gui import decomposition, explorer_tab, export_dialog, protocol_dialog


I = ("SCD_U",) * 3
D = (("CDS_U", "SCD_U", "SCD_U"), I, I)
DI = (("DSC_U", "SCD_U", "SCD_U"), I, I)


def expression(d):
    return " o MSC o ".join("({} x {} x {})".format(*s) for s in reversed(d)) + " o MSC"


def evaluate(d):
    engine = AlgebraEngine()
    return Evaluator(engine).evaluate(Parser(engine).parse(expression(d)))


def context(inverse=False):
    d = DI if inverse else D
    return {"target": tuple(evaluate(d)), "inverse": inverse, "results": [d]}


@pytest.mark.parametrize("name", list(PERM3))
@pytest.mark.parametrize("stage", range(3))
def test_b9_istruzioni_stampate_eseguono_la_permutazione(name, stage):
    d = [I, I, I]
    d[stage] = (name, "SCD_U", "SCD_U")
    target = evaluate(d)
    inverse = [target.index(i) for i in range(27)]
    text = protocol_dialog.generate_protocol_html(
        dict(perm=target, inverse_perm=inverse, decompositions=[d]))
    orders = re.findall(r"Raccogli le colonne nell'ordine:\s*<strong>(.*?)</strong>", text)
    assert len(orders) == 3
    labels = ["Sinistra", "Centro", "Destra"]
    deck = list(range(27))
    for order in orders:
        columns = [deck[i::3] for i in range(3)]
        positions = [labels.index(part) for part in html.unescape(order).split(" → ")]
        deck = [card for pos in positions for card in columns[pos]]
    physical = [deck.index(card) for card in range(27)]
    assert physical == target
    assert physical[7] == target[7]
    if name == "CDS_U" and stage == 0:
        assert physical[0] == 1
        assert orders[0] == "Destra → Sinistra → Centro"
    if name == "DSC_U" and stage == 0:
        assert physical[0] == 2
        assert orders[0] == "Centro → Destra → Sinistra"


class Widget:
    def __init__(self, value=None):
        self.value = value
        self.options = {}

    def get(self, *args):
        return self.value

    def set(self, value):
        self.value = value

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def __setitem__(self, key, value):
        self.options[key] = value

    def get_children(self):
        return []


class SearchHarness(decomposition.DecompositionDialog):
    def __init__(self):
        self._perm, self._inv_perm = evaluate(D), evaluate(DI)
        self._results, self._result_context, self._search_id = [], None, 0
        self._target_inv = Widget(False)
        self._cfg = SimpleNamespace(get=lambda *a: False, effective_n_workers=1)
        self.published, self.jobs, self.cancelled = [], [], []
        self._on_results = self.published.append
        for name in ("_progress_bar", "_progress_lbl", "_export_mb", "_open_btn",
                     "_status_var", "_tree"):
            setattr(self, name, Widget())
        self._node_expr, self._node_data, self._flat_job = {}, {}, None
        self.displays = 0

    def after(self, delay, callback):
        self.jobs.append(callback)
        return len(self.jobs)

    def after_cancel(self, job):
        self.cancelled.append(job)

    def winfo_exists(self):
        return True

    def _redisplay(self):
        self.displays += 1


@pytest.mark.parametrize("cached_latest", [False, True])
def test_b10_ricerca_obsoleta_non_pubblica_neanche_dopo_cache(cached_latest, monkeypatch):
    d = SearchHarness()
    assert d._perm != d._inv_perm
    threads = []

    def thread(**kwargs):
        threads.append(lambda: kwargs["target"](*kwargs["args"]))
        return SimpleNamespace(start=lambda: None)

    monkeypatch.setattr(decomposition.threading, "Thread", thread)
    monkeypatch.setattr(decomposition, "save_decompositions", lambda *a: None)
    monkeypatch.setattr(decomposition, "load_decompositions", lambda target:
                        [DI] if cached_latest and list(target) == d._inv_perm else None)
    monkeypatch.setattr(decomposition, "find_all_kron_decompositions", lambda target, **kw:
                        [D] if list(target) == d._perm else [DI])
    d._start_search()
    old_poll = d.jobs[0]
    d._flat_job = 99
    d._target_inv.set(True)
    d._on_target_changed()
    assert 99 in d.cancelled
    if not cached_latest:
        threads[1]()  # termina prima la ricerca nuova
        assert d._results == []  # il worker non pubblica direttamente
        d.jobs[-1]()  # pubblicazione sul chiamante GUI
    assert d._result_context == context(True)
    published = list(d.published)
    threads[0]()  # termina poi la vecchia
    old_poll()
    assert d._result_context == context(True)
    assert d._results == [DI]
    assert d.published == published
    assert d.displays == 1


def test_b10_risultato_worker_incompatibile_non_pubblicato(monkeypatch):
    d = SearchHarness()
    threads = []
    monkeypatch.setattr(decomposition.threading, "Thread", lambda **kw:
                        SimpleNamespace(start=lambda: threads.append(kw)))
    monkeypatch.setattr(decomposition, "load_decompositions", lambda *a: None)
    monkeypatch.setattr(decomposition, "find_all_kron_decompositions", lambda *a, **kw: [(I,I,I)])
    monkeypatch.setattr(decomposition, "save_decompositions", lambda *a: pytest.fail("salvataggio invalido"))
    d._start_search()
    threads[0]["target"](*threads[0]["args"])
    d.jobs[0]()
    assert d._results == [] and d._result_context is None
    assert "Errore:" in d._status_var.value
    assert d.published == [None]


class Text(Widget):
    modified = True

    def edit_modified(self, value=None):
        if value is not None:
            self.modified = value
        return self.modified


class ExplorerHarness(explorer_tab.ExplorerTabMixin):
    def __init__(self):
        self._explorer_ctrl = Controller()
        self._explorer_last_result = self._explorer_ctrl.process(expression(D))
        self._explorer_entry = Text(expression(D))
        self._explorer_status = Widget()
        self._last_decompositions = context()
        self._decomposition_revision = 0
        for name in ("norm steps_sum perm period sig inv nf_kind nf_msc nf_sym "
                     "nf_kron nf_notes can_avail can_sym can_exp can_notes log").split():
            setattr(self, "_exp_" + name, Widget())
        self._exp_can_factors = []
        self._exp_rewrite = self._exp_eval = Widget()
        self._exp_export_btn = self._decomp_btn = Widget()

    def _exp_set(self, *args):
        pass

    def _reset_matrix_tab(self):
        pass

    def _explorer_display(self, *args):
        pass

    def _notify_T_changed(self, *args):
        pass


@pytest.mark.parametrize("event", ["modifica", "calcolo", "vuoto", "errore", "pulizia"])
def test_b10_explorer_invalida_e_ignora_callback_obsoleti(event, monkeypatch):
    app = ExplorerHarness()
    callbacks = []
    monkeypatch.setattr(explorer_tab, "DecompositionDialog", lambda *a, **kw:
                        callbacks.append(kw["on_results"]))
    app._explorer_find_decompositions()
    callbacks[0](context())
    assert app._last_decompositions == context()
    if event == "modifica":
        app._explorer_input_changed()
    elif event == "pulizia":
        app._explorer_clear_results()
    else:
        app._explorer_entry.value = {"calcolo": expression(DI), "vuoto": "", "errore": "???"}[event]
        app._explorer_calc()
    assert app._last_decompositions is None
    callbacks[0](context())
    assert app._last_decompositions is None


def test_b10_due_dialoghi_explorer_solo_ultimo_puo_pubblicare(monkeypatch):
    app = ExplorerHarness()
    callbacks = []
    monkeypatch.setattr(explorer_tab, "DecompositionDialog", lambda *a, **kw:
                        callbacks.append(kw["on_results"]))
    app._explorer_find_decompositions()
    app._explorer_find_decompositions()
    callbacks[1](context(True))
    callbacks[0](context(False))
    assert app._last_decompositions == context(True)
    exported = []
    app._open_export_dialog = lambda **kw: exported.append(kw)
    app._explorer_export()
    assert exported[0]["decompositions"] == context(True)


def make_export(monkeypatch, data):
    monkeypatch.setattr(export_dialog.tk.Toplevel, "__init__", lambda *a: None)
    for name in ("title", "geometry", "resizable", "_build_ui", "_refresh_preview"):
        monkeypatch.setattr(export_dialog.ExportDialog, name, lambda *a: None)
    return export_dialog.ExportDialog(None, evaluate(D), evaluate(DI), data)


@pytest.mark.parametrize("inverse", [False, True])
@pytest.mark.parametrize("legacy", [False, True])
def test_b10_export_bersaglio_e_formule_numericamente_coerenti(inverse, legacy, monkeypatch):
    data = context(inverse)
    dialog = make_export(monkeypatch, data["results"] if legacy else data)
    text = dialog._txt_summary(evaluate(D), evaluate(DI), "T")
    label = "T^-1" if inverse else "T"
    assert f"Decomposizioni Kronecker di {label}: 1" in text
    formulas = re.findall(r"^\s*\d+\.  T(?:\^-1)? = (.*)$", text, re.M)
    assert len(formulas) == 1
    engine = AlgebraEngine()
    assert Evaluator(engine).evaluate(Parser(engine).parse(formulas[0])) == list(data["target"])
    latex = dialog._latex_decomp("T")
    expected = r"\mathrm{T}^{-1}" if inverse else r"\mathrm{T}"
    assert f"% Decomposizioni ${expected}$" in latex
    # Ricostruisce anche la formula dalle tre celle effettivamente esportate.
    row = next(line for line in latex.splitlines() if r"\scriptscriptstyle" in line)
    cells = re.findall(r"\$\\scriptscriptstyle (.*?)\$", row)
    stages = [tuple(name + "_U" for name in re.findall(r"\b[SCD]{3}\b", cell)) for cell in cells]
    assert evaluate(stages) == list(data["target"])


@pytest.mark.parametrize("bad", [None, [(I,I,I)], [D, DI],
                                {"target": tuple(range(27)), "inverse": False, "results": [D]},
                                {"target": tuple(evaluate(D)), "inverse": False, "results": [(I,I,I)]}])
def test_b10_export_e_protocollo_scartano_decomposizioni_incoerenti(bad, monkeypatch):
    dialog = make_export(monkeypatch, bad)
    assert dialog._decomps == []
    assert "Nessuna decomposizione" in dialog._latex_decomp("T")
    text = protocol_dialog.generate_protocol_html(dict(
        perm=evaluate(D), inverse_perm=evaluate(DI), decompositions=bad))
    assert "Raccogli le colonne nell'ordine" not in text
    assert "equivalente registrata" not in text


@pytest.mark.parametrize("inverse", [False, True])
def test_b10_app_protocollo_usa_bersaglio_effettivo(inverse, monkeypatch):
    from gioco27.gui import app as app_module
    app = ExplorerHarness()
    app._last_decompositions = context(inverse)
    opened = []
    monkeypatch.setattr(app_module, "ProtocolDialog", lambda parent, data: opened.append(data))
    app_module.App._open_protocol(app)
    assert opened[0]["decompositions"] == context(inverse)
    text = protocol_dialog.generate_protocol_html(opened[0])
    label = "T⁻¹ (la permutazione inversa)" if inverse else "T (la permutazione diretta)"
    assert label in text


@pytest.mark.parametrize("kind", ["txt", "csv", "html"])
@pytest.mark.parametrize("inverse", [False, True])
def test_b10_export_dialogo_conserva_bersaglio_e_risultati_insieme(
        kind, inverse, tmp_path, monkeypatch):
    d = SearchHarness()
    initial = context(inverse)
    d._accept_results(initial["target"], inverse, initial["results"])
    dest = tmp_path / ("out." + kind)
    titles = []

    def choose_file(**kwargs):
        titles.append(kwargs["title"])
        # Simula uno stato nuovo mentre il selettore file e' aperto.
        newer = context(not inverse)
        d._target_inv.set(not inverse)
        d._accept_results(newer["target"], not inverse, newer["results"])
        return str(dest)

    monkeypatch.setattr(decomposition.filedialog, "asksaveasfilename", choose_file)
    monkeypatch.setattr(decomposition.messagebox, "showinfo", lambda *a, **kw: None)
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda *a: None)
    getattr(d, "_export_" + kind)()
    text = dest.read_text(encoding="utf-8")
    stages = re.findall(r"\((\w+) x (\w+) x (\w+)\)", text)
    assert len(stages) == 3
    assert evaluate(stages) == list(initial["target"])
    suffix = ("⁻¹" if kind == "html" else "-inv") if inverse else ""
    assert "decomposizioni T" + suffix in titles[0]
    if kind == "txt":
        assert text.startswith("T" + suffix + " = [")
        assert ", ".join(map(str, initial["target"])) in text
    elif kind == "html":
        assert "Decomposizioni — T" + suffix in text


@pytest.mark.parametrize("bad", [[[]], [None], [I], [[I,I]], [[I,I,I,I]],
                                [[I,I,[]]], [[I,I,["SCONOSCIUTO"]*3]],
                                [[I,I,["I_3"]*3]], [[I,I,[0,1,2]]],
                                [[I,I,"SCD_U"]], [(I,I,I)], [D,(I,I,I)], None])
def test_b11_cache_semanticamente_invalida_rifiutata(bad, tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "_CACHE_DIR", tmp_path)
    target = evaluate(D)
    cache._cache_path(target).write_text(json.dumps({"version":2,"results":bad}), encoding="utf-8")
    assert cache.load_decompositions(target) is None


@pytest.mark.parametrize("results", [[], [D], [DI]])
def test_b11_cache_json_v2_valida_accettata(results, tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "_CACHE_DIR", tmp_path)
    target = evaluate(results[0]) if results else list(range(27))
    cache.save_decompositions(target, results)
    assert json.loads(cache._cache_path(target).read_text(encoding="utf-8"))["version"] == 2
    assert cache.load_decompositions(target) == results


def test_b11_cache_risultati_motore_reale(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "_CACHE_DIR", tmp_path)
    target = evaluate(D)
    results = kronecker.find_all_kron_decompositions(target)
    assert len(results) == 216 ** 2
    cache.save_decompositions(target, results)
    assert cache.load_decompositions(target) == results
    for d in results[::216]:
        assert evaluate(d) == target
