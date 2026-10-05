"""Blocco 2: contratti osservabili di risultati, export e cancellazione."""
import csv
import queue
from types import SimpleNamespace

import pytest

from gioco27 import i18n
from gioco27.core import config, kronecker
from gioco27.core.combinations import iter_combinations_ex
from gioco27.gui import (app as app_module, cayley_dialog, decomposition,
                         distribution_tab, export_contract, export_dialog,
                         export_group_dialog)
from gioco27.gui.calcolo_locale import CalcoloAnnullato, verifica_annullamento
from gioco27.services import servizio_analisi


@pytest.fixture(scope="module")
def isolated_app(tmp_path_factory):
    # Un solo interprete Tk: creare/distruggere molte radici non e' affidabile
    # su Windows. Le viste vengono azzerate tra i casi.
    tmp_path = tmp_path_factory.mktemp("ux2-profile")
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(config, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "_CONFIG_FILE", tmp_path / "config.json")
    cfg = config.Config()
    cfg._data.update(n_workers=1, use_parallel=False, ui_intro_done=True,
                     livello="laboratorio", language="it")
    cfg.save()
    monkeypatch.setattr(config, "_instance", cfg)
    from gioco27.core import cache
    monkeypatch.setattr(cache, "_CACHE_DIR", tmp_path / "cache")
    a = app_module.App()
    a.withdraw()
    a.update()
    yield a
    if a.winfo_exists():
        a.destroy()
    monkeypatch.undo()
    i18n.set_language("it")


@pytest.fixture
def app(isolated_app):
    a = isolated_app
    a._explorer_clear()
    a._reset_anteprima()
    a._reset_analisi()
    a._reset_filtri()
    a._tavola_frame.reset()
    a._distrib_frame.reset()
    a.update()
    return a


@pytest.mark.parametrize("consent", [False, True])
def test_t01_conflict_requires_explicit_consent(tmp_path, monkeypatch, consent):
    old = tmp_path / "T.svg"
    old.write_text("old", encoding="utf-8")
    reviews, reports = [], []

    def choose(parent, title, text, choices):
        assert old.read_text(encoding="utf-8") == "old"
        reviews.append((text, choices))
        return consent

    monkeypatch.setattr(export_contract, "_scegli", choose)
    monkeypatch.setattr(export_contract, "riepilogo", lambda *args: reports.append(args))
    export_contract.esporta_cartella(None, tmp_path, [("T.svg", "new"), ("cycles.tex", "cycles")])
    assert str(old) in reviews[0][0]
    assert reviews[0][1] == ((True, "ux2.export.overwrite"), (False, "button.cancel"))
    assert old.read_text(encoding="utf-8") == ("new" if consent else "old")
    assert (tmp_path / "cycles.tex").exists() is consent
    assert bool(reports) is consent


def test_t02_table_scope_exports_visible_or_all(app, tmp_path, monkeypatch):
    table = app._tavola_frame
    table._filtro_var.set("100")
    assert 0 < len(table._tv.get_children()) < 216
    files = []
    monkeypatch.setattr(export_contract.messagebox, "showinfo", lambda *a, **k: None)
    from gioco27.gui import tavola_tab
    monkeypatch.setattr(tavola_tab.filedialog, "asksaveasfilename",
                        lambda **kw: str(tmp_path / f"scope{len(files)}.csv"))
    for scope in (0, 1):
        table._export_scope.current(scope)
        table._esporta_csv()
        path = tmp_path / f"scope{len(files)}.csv"
        with path.open(encoding="utf-8", newline="") as f:
            files.append(list(csv.reader(f, delimiter=";")))
    assert len(files[0]) == 217
    assert [r[0] for r in files[1][1:]] == list(table._tv.get_children())


def test_t03_t13_decomposition_a1_and_scope(app, tmp_path, monkeypatch):
    all_rows = kronecker.find_all_kron_decompositions(list(range(27)))
    first = all_rows[0]
    other = next(r for r in all_rows if r[0] == first[0] and r[1] != first[1])
    # L'A0 della prima riga compare come A1 dell'altra: distingue i due componenti.
    rows = [first, other]
    monkeypatch.setattr(decomposition, "load_decompositions", lambda *a: rows)
    d = decomposition.DecompositionDialog(app, list(range(27)), list(range(27)))
    d._filter_var.set(str(other[1]))
    d._redisplay()
    assert d._visible_results == [other]
    d._export_scope.current(0)
    assert d._export_context()["results"] == rows
    d._export_scope.current(1)
    assert d._export_context()["results"] == [other]
    path = tmp_path / "visible.csv"
    monkeypatch.setattr(decomposition.filedialog, "asksaveasfilename", lambda **k: str(path))
    monkeypatch.setattr(decomposition.messagebox, "showinfo", lambda *a, **k: None)
    d._export_csv()
    with path.open(encoding="utf-8", newline="") as f:
        exported = list(csv.reader(f, delimiter=";"))
    assert exported[0] == ["#", "A0", "A1", "A2"]
    assert len(exported) == 2 and exported[1][2] == decomposition._disp(other[1])
    d.destroy()


def test_t03_latex_limit_visible_before_write(app, tmp_path, monkeypatch):
    rows = kronecker.find_all_kron_decompositions(list(range(27)))[:201]
    d = export_dialog.ExportDialog(app, list(range(27)), list(range(27)), rows)
    assert "200 di 201" in d._notice.cget("text")
    assert "10 di 201" in d._notice.cget("text")
    plans = []
    monkeypatch.setattr(export_dialog.filedialog, "askdirectory", lambda **k: str(tmp_path))
    monkeypatch.setattr(export_contract, "_scegli", lambda p, t, text, choices: plans.append(text) or False)
    d._export_all()
    assert "200 di 201" in plans[0] and "10 di 201" in plans[0]
    assert not list(tmp_path.glob("*.tex"))
    d.destroy()


@pytest.mark.parametrize("kind", ["zero", "omission", "write_failure"])
def test_t04_actual_summary(tmp_path, monkeypatch, kind):
    messages = []
    monkeypatch.setattr(export_contract, "_scegli", lambda *a: True)
    monkeypatch.setattr(export_contract.messagebox, "showinfo", lambda *a, **k: messages.append(("info", a[1])))
    monkeypatch.setattr(export_contract.messagebox, "showwarning", lambda *a, **k: messages.append(("warning", a[1])))
    contents = [] if kind == "zero" else [("a.txt", "a")]
    omissions = ["decomposizioni non disponibili"] if kind == "omission" else []
    if kind == "write_failure":
        contents += [("missing/b.txt", "b"), ("c.txt", "c")]
    export_contract.esporta_cartella(None, tmp_path, contents, omissions)
    assert len(messages) == 1 and messages[0][0] == "warning"
    assert ("Creati: 0" if kind == "zero" else "Creati: 1") in messages[0][1]
    if kind == "write_failure":
        assert "c.txt: non scritto" in messages[0][1]


def test_t04_group_generator_failure_is_omitted_before_write(app, tmp_path, monkeypatch):
    items = [("ok", "OK", "ok.svg", lambda: "<svg/>"),
             ("bad", "BAD", "bad.svg", lambda: (_ for _ in ()).throw(ValueError("unavailable")))]
    d = export_group_dialog._PreviewExportDialog(app, "test", items)
    plans, reports = [], []
    monkeypatch.setattr(export_group_dialog.filedialog, "askdirectory", lambda **k: str(tmp_path))
    monkeypatch.setattr(export_contract, "_scegli", lambda p, t, text, choices: plans.append(text) or True)
    monkeypatch.setattr(export_contract, "riepilogo", lambda *a: reports.append(a))
    d._export_all()
    assert "BAD: unavailable" in plans[0]
    assert (tmp_path / "ok.svg").exists() and not (tmp_path / "bad.svg").exists()
    assert len(reports[0][1]) == 1 and "BAD: unavailable" in reports[0][2]
    d.destroy()


def test_t05_t06_preview_reset_stale_and_snapshot(app, monkeypatch):
    app._calcola_anteprima()
    previous = list(app._prev_T_perm)
    app._prev_vars[0]["p0"].set("CDS_U")
    assert "DA RICALCOLARE" in app._prev_state.get()
    assert app._prev_T_perm == previous
    exports = []
    monkeypatch.setattr(app, "_open_export_dialog", lambda **kw: exports.append(kw))
    app._anteprima_export()
    assert exports[0]["perm"] == previous
    assert exports[0]["origin"] == i18n.tr("tab.preview")
    app._reset_anteprima()
    app._anteprima_export()
    assert len(exports) == 1 and app._prev_T_perm is None
    assert app._prev_export_btn.instate(["disabled"])
    assert "ASSENTE" in app._prev_state.get()


def test_t06_explorer_keeps_last_calculation(app, monkeypatch):
    app._explorer_entry.insert("1.0", "MSC")
    app._explorer_calc()
    app.update()
    previous = app._explorer_last_result
    app._explorer_entry.insert("end", " o MSC")
    app.update()
    assert "DA RICALCOLARE" in app._explorer_status.get()
    assert app._explorer_last_result is previous
    exports = []
    monkeypatch.setattr(app, "_open_export_dialog", lambda **kw: exports.append(kw))
    app._explorer_export()
    assert exports[0]["perm"] == previous["perm"] and exports[0]["origin"] == "Explorer"
    app._explorer_calc()
    assert "AGGIORNATO" in app._explorer_status.get()


def test_t06_analysis_changed_filters_not_csv_source(app, monkeypatch, tmp_path):
    app._preset_gioco_reale()
    for f in app.filter_frames:
        for var, _ in f._vars.values():
            if var.get() == "*":
                var.set("I_3" if any(var is f._vars[n][0] for n in ("J0", "J1", "J2")) else "SCD_U")
    filters = app._get_filters()
    revision = app._analisi_nuova_revisione()
    app._analisi_begin_work(revision, filters)
    result = servizio_analisi().da_filtri(filters)
    app._analisi_pubblica(result, revision)
    app.filter_frames[0]._vars["P0"][0].set("CDS_U")
    app._update_count()
    assert "DA RICALCOLARE" in app._analisi_status.get()
    assert app._analisi_corrente is result
    monkeypatch.setattr(app_module.filedialog, "asksaveasfilename", lambda **kw: str(tmp_path / "analysis.csv"))
    app._export_analisi_csv()
    assert "DA RICALCOLARE" in app._analisi_status.get()
    assert (tmp_path / "analysis.csv").exists()
    app._analisi_failed(revision)
    assert "DA RICALCOLARE" in app._analisi_status.get()
    assert app._analisi_cancel.instate(["disabled"])
    state = app._analisi_status.get()
    app._analisi_nuova_revisione()
    app._analisi_failed(revision)
    assert app._analisi_status.get() == state
    app._analisi_calculated_filters = None
    app._analisi_input_changed()
    assert "AGGIORNATO" in app._analisi_status.get()


def test_t06_cayley_exports_calculated_pair(app, monkeypatch, tmp_path):
    monkeypatch.setattr(cayley_dialog, "run_in_thread", lambda widget, job, **k: job())
    monkeypatch.setattr(cayley_dialog, "ui_call", lambda widget, job: job())
    d = cayley_dialog.CayleyDialog(app)
    assert "ASSENTE" in d._status.get()
    d._calc()
    pair = d._calculated_pair
    previous = d._res_ab.get()
    d._combo_a.current(2)
    d._input_changed()
    assert "DA RICALCOLARE" in d._status.get() and d._res_ab.get() == previous
    opened = []
    monkeypatch.setattr(export_group_dialog, "CayleyExportDialog", lambda parent, gd, ia, ib:
                        opened.append((ia, ib)) or SimpleNamespace(title=lambda t: None))
    d._export_latex_svg()
    assert opened == [pair]
    monkeypatch.setattr(cayley_dialog.filedialog, "asksaveasfilename", lambda **kw: str(tmp_path / "cayley.csv"))
    monkeypatch.setattr(cayley_dialog.messagebox, "showinfo", lambda *a, **kw: None)
    d._export_csv()
    assert "DA RICALCOLARE" in d._status.get()
    assert (tmp_path / "cayley.csv").exists()
    d.destroy()


def test_t07_t08_table_selection_and_publication(app):
    app._calcola_anteprima()
    previous, origin = list(app._last_T_perm), app._T_origin
    table = app._tavola_frame
    table.vai_alla_riga(100)
    app.update()
    assert app._last_T_perm == previous and app._T_origin == origin
    table._usa_come_T()
    assert app._last_T_perm == table._T_selezionata()
    assert app._T_origin == "Tavola, riga 100"
    assert "Tavola, riga 100" in app._cycles_frame._hint.cget("text")
    assert "Protocollo" not in i18n.tr("nav.published", number=100)


def test_t09_protocol_uses_explorer_not_shared_t(app, monkeypatch):
    app._explorer_entry.insert("1.0", "MSC")
    app._explorer_calc()
    explorer_perm = list(app._explorer_last_result["perm"])
    app._calcola_anteprima()
    assert app._last_T_perm != explorer_perm
    opened = []
    monkeypatch.setattr(app_module, "ProtocolDialog", lambda parent, data: opened.append(data))
    app._open_protocol()
    assert opened[0]["perm"] == explorer_perm
    assert "Explorer" in i18n.tr("protocol.help.long")
    assert "Explorer" in i18n.tr("tooltip.protocol")
    assert "Explorer" in i18n.tr("guide.s16.protocol.body")


def test_t10_distribution_running_completed_and_error(app, monkeypatch):
    d = app._distrib_frame
    monkeypatch.setattr(distribution_tab.threading, "Thread", lambda **k: SimpleNamespace(start=lambda: None))
    assert "non ancora avviato" in d._riassunto.cget("text")
    d._start_compute()
    assert "In corso" in d._tbl_txt.get("1.0", "end")
    assert "filtri non si applicano" in d._riassunto.cget("text")
    d._q.put(("P", 7, 216))
    d._q.put(("P", 15, 216))
    d._poll_queue()
    assert d._prog_bar["value"] == 16
    assert "iterazione" not in d._prog_lbl.cget("text")
    result = dict(histogram={46656: 216}, total_T=216, total_decomp=216**3)
    d._q.put(("DONE", result))
    d._poll_queue()
    assert d._result is result and not d._computing
    assert "216" in d._riassunto.cget("text")
    d._start_compute()
    d._q.put(("ERR", "test failure"))
    d._poll_queue()
    assert "Errore" in d._riassunto.cget("text")
    assert "In corso" not in d._tbl_txt.get("1.0", "end")


def test_t11_distribution_cancel_really_stops_and_reset_discards(app, monkeypatch):
    d = app._distrib_frame
    monkeypatch.setattr(distribution_tab.threading, "Thread", lambda **k: SimpleNamespace(start=lambda: None))
    d._start_compute()
    calls = []

    def compute(**kw):
        calls.append(1)
        d._stop_compute.set()
        kw["progress_cb"](8, 216)
        pytest.fail("calculation continued after cancellation")

    monkeypatch.setattr(distribution_tab, "_compute_distribution_fast", compute)
    d._compute_worker()
    d._poll_queue()
    assert calls == [1] and not d._computing and d._result is None
    assert "annullato" in d._riassunto.cget("text")
    from gioco27.core.analysis import compute_distribution_parallel
    d._stop_compute.clear()
    progress = []

    def callback(done, total):
        progress.append(done)
        d._stop_compute.set()
        verifica_annullamento(d._stop_compute)

    with pytest.raises(CalcoloAnnullato):
        compute_distribution_parallel(n_workers=1, progress_cb=callback)
    assert len(progress) == 1
    d._start_compute()
    d.reset()
    d._q.put(("DONE", dict(histogram={1: 216})))
    d._poll_queue()
    assert d._result is None and "non ancora avviato" in d._riassunto.cget("text")


def test_t11_decomposition_cancel_and_close_signal(app, monkeypatch):
    monkeypatch.setattr(decomposition, "load_decompositions", lambda *a: None)
    monkeypatch.setattr(decomposition.threading, "Thread", lambda **k: SimpleNamespace(start=lambda: None))
    saved = []
    monkeypatch.setattr(decomposition, "save_decompositions", lambda *a: saved.append(a))
    d = decomposition.DecompositionDialog(app, list(range(27)), list(range(27)))
    stop = d._stop_search
    d._cancel_search()
    q = queue.Queue()
    d._search_thread(tuple(range(27)), q, stop)
    assert q.get_nowait()[0] == "CANCEL" and not saved
    # Callback reale: arresto a un confine di lavoro, senza cambiare il motore.
    stop.clear()
    progress = []

    def callback(done, found):
        progress.append(done)
        stop.set()
        verifica_annullamento(stop)

    with pytest.raises(CalcoloAnnullato):
        kronecker.find_all_kron_decompositions(list(range(27)), progress_cb=callback)
    assert progress == [0]
    stop.clear()
    d.destroy()
    assert stop.is_set()


def test_t12_j_uniform_within_stage_math_unchanged(app):
    app._preset_j_uniform()
    for idx, f in enumerate(app.filter_frames):
        for n in ("P0", "P1", "P2"):
            f._vars[n][0].set("SCD_U")
        f._vars["J0"][0].set("R_U" if idx == 1 else "I_3")
        assert all(str(w.cget("state")) == "disabled" for w in f._j_row_widgets)
    choices = list(iter_combinations_ex(app._get_filters()))
    assert len(choices) == 1
    for idx, stage in enumerate(choices[0]):
        assert stage[3:] == ("R_U",)*3 if idx == 1 else stage[3:] == ("I_3",)*3
    assert "ogni stadio" in i18n.tr("button.uniform_j")
    assert "Stadi diversi" in i18n.tr("tooltip.uniform_j")
    assert "seguono J0" in i18n.tr("filter.uniform_j_note")
