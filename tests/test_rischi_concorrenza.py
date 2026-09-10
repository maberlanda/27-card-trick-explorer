"""R1-R2: chiusura controllata e due processi sui file persistenti condivisi."""
import json
import multiprocessing
import os
import sys
from pathlib import Path
import threading
import traceback
from types import SimpleNamespace
import tkinter as tk

import pytest

from gioco27.core import cache, config, parallel
from gioco27.gui import app as app_module, common, analysis_tab


class Event(threading.Event):
    def __init__(self):
        super().__init__()
        self.set_count = 0

    def set(self):
        self.set_count += 1
        super().set()


class Widget:
    def __init__(self, app):
        self.app = app

    def configure(self, **kwargs):
        if self.app.destroyed:
            raise tk.TclError("widget distrutto")

    def set(self, value):
        self.configure()

    def __setitem__(self, key, value):
        self.configure()


class AppHarness:
    _on_close = app_module.App._on_close
    _quit_app = app_module.App._quit_app
    _ui = app_module.App._ui
    _fine_export = app_module.App._fine_export
    _run_generation = app_module.App._run_generation

    def __init__(self):
        self.destroyed = 0
        self.scheduled = []
        self._closing = False
        self._export_stop = Event()
        self._export_busy = False
        self._btn_annulla = self.progress = self.status_var = self._analisi_status = Widget(self)

    def geometry(self):
        return "1280x800"

    def destroy(self):
        self.stop_at_destroy = self._export_stop.is_set()
        self.destroyed += 1

    def winfo_exists(self):
        return not self.destroyed

    def after(self, delay, fn):
        if self.destroyed:
            raise RuntimeError("main thread is not in main loop")
        self.scheduled.append(fn)

    def update_idletasks(self):
        pass

    def _get_filters(self):
        return [dict(p0="SCD_U", p1="SCD_U", p2="SCD_U",
                     j0="I_3", j1="I_3", j2="I_3") for _ in range(3)]


@pytest.mark.parametrize("close", [False, True])
@pytest.mark.parametrize("writing", [False, True])
def test_r1_export_attivo_chiusura_e_callback(close, writing, tmp_path, monkeypatch):
    app = AppHarness()
    dest = tmp_path / "out.csv"
    dest.write_bytes(b"precedente")
    started, release = threading.Event(), threading.Event()
    threads, errors = [], []
    monkeypatch.setattr(threading, "excepthook", lambda args: errors.append(args.exc_value))
    monkeypatch.setattr(app_module.filedialog, "asksaveasfilename", lambda **kw: str(dest))
    monkeypatch.setattr(app_module, "get_config", lambda: SimpleNamespace(
        effective_n_workers=1, get=lambda *a: False))

    def start(*args, **kwargs):
        threads.append(common.run_in_thread(*args, **kwargs))

    def generate(path, filters, *, progress_cb, annullato, **kwargs):
        progress_cb(1)  # callback accodato prima della chiusura
        if not writing:
            started.set()
            assert release.wait(10)
        with parallel.atomic_write(path, annullato=annullato) as f:
            f.write(b"nuovo")
            if writing:
                started.set()
                assert release.wait(10)
        return 1

    monkeypatch.setattr(app_module, "run_in_thread", start)
    app._run_generation(gen_func=generate, kind="CSV", unit="riga", unit_plural="righe",
                        step=1, dialog_kw={})
    try:
        assert started.wait(5)
        if close:
            with pytest.raises(SystemExit):
                app._on_close()
        release.set()
        threads[0].join(5)
        assert not threads[0].is_alive()
        for callback in list(app.scheduled):
            try:
                callback()
            except Exception as exc:
                errors.append(exc)
        assert errors == []
        if close:
            assert app.stop_at_destroy and app._export_stop.is_set()
            assert dest.read_bytes() == b"precedente"
        else:
            assert dest.read_bytes() == b"nuovo"
            assert not app._export_busy and not app._export_stop.is_set()
        assert set(tmp_path.iterdir()) == {dest}
    finally:
        release.set()
        for thread in threads:
            thread.join(10)


def test_r1_chiusura_idempotente_non_azzera_stop():
    app = AppHarness()
    with pytest.raises(SystemExit):
        app._quit_app()
    app._quit_app()
    app._fine_export()  # completamento tardivo
    assert app.destroyed == app._export_stop.set_count == 1
    assert app._export_stop.is_set()


@pytest.mark.parametrize("close", [False, True])
def test_r1_analisi_si_ferma_fra_due_elementi(close, monkeypatch):
    app = AppHarness()
    calls = []
    displayed = []
    expected = [{"n_sim": 2}]
    app._analisi_populate = lambda results, n: displayed.append((results, n))

    def params(filters):
        yield 0
        if close:
            with pytest.raises(SystemExit):
                app._on_close()
        yield 1

    def row(i, params):
        calls.append(i)
        return [str(i)] * 9

    monkeypatch.setattr(analysis_tab, "count_combinations_ex", lambda f: 2)
    monkeypatch.setattr(analysis_tab, "iter_combinations_ex", params)
    monkeypatch.setattr(analysis_tab, "make_csv_row", row)
    def analyze(rows):
        assert not app._closing
        assert len(rows) == 2
        assert rows[0]["Stage0"] == "1" and rows[1]["Stage2"] == "2"
        return expected

    monkeypatch.setattr(analysis_tab, "analizza_righe", analyze)
    monkeypatch.setattr(analysis_tab, "run_in_thread", lambda widget, job, **kw: job())
    analysis_tab.AnalysisTabMixin._run_analisi(app)
    for callback in app.scheduled:
        callback()
    assert calls == ([1] if close else [1, 2])
    assert displayed == ([] if close else [(expected, 2)])


@pytest.mark.parametrize("close", [False, True])
def test_r1_errore_worker_accodato_prima_della_chiusura(close, monkeypatch):
    app = AppHarness()
    reported = []
    monkeypatch.setattr(common.messagebox, "showerror", lambda *a: reported.append(a))
    error = ValueError("errore controllato")

    def job():
        raise error

    worker = common.run_in_thread(app, job, on_error=lambda exc: reported.append(exc))
    worker.join(5)
    assert not worker.is_alive() and len(app.scheduled) == 1
    if close:
        with pytest.raises(SystemExit):
            app._on_close()
    app.scheduled[0]()
    assert reported == ([] if close else [("Errore", str(error)), error])


@pytest.mark.parametrize("error", [tk.TclError("distrutto"), RuntimeError("main thread is not in main loop")])
def test_r1_chiusura_durante_accodamento(error):
    app = AppHarness()

    def after(*args):
        raise error

    app.after = after
    app._ui(lambda: pytest.fail("callback dopo la chiusura"))


@pytest.mark.parametrize("pipeline", [False, True])
@pytest.mark.parametrize("close", [False, True])
def test_r1_analisi_csv_completa_o_interrotta(pipeline, close, monkeypatch, tmp_path):
    app = AppHarness()
    displayed, saved = [], []
    result = [{"n_sim": 4}]
    app._analisi_populate = lambda rows, n: displayed.append((rows, n))
    monkeypatch.setattr(analysis_tab.filedialog, "askopenfilename", lambda **kw: "input.csv")
    monkeypatch.setattr(analysis_tab.filedialog, "asksaveasfilename", lambda **kw: str(tmp_path / "out.csv"))
    monkeypatch.setattr(analysis_tab, "run_in_thread", lambda widget, job, **kw: job())
    monkeypatch.setattr(analysis_tab, "scrivi_output", lambda *args: saved.append("csv"))
    monkeypatch.setattr(analysis_tab, "scrivi_excel", lambda *args: saved.append("excel"))
    monkeypatch.setattr(analysis_tab.messagebox, "showinfo", lambda *args: displayed.append("message"))

    def analyze(path):
        if close:
            with pytest.raises(SystemExit):
                app._on_close()
        return result

    monkeypatch.setattr(analysis_tab, "analizza_csv", analyze)
    method = (analysis_tab.AnalysisTabMixin._analisi_csv_pipeline if pipeline
              else analysis_tab.AnalysisTabMixin._analisi_load_csv)
    method(app)
    for callback in app.scheduled:
        callback()
    assert saved == (["csv", "excel"] if pipeline and not close else [])
    assert displayed == ([] if close else [(result, 4)] + (["message"] if pipeline else []))


def _persistent_writer(root, kind, index, opened, written_a, written_b, closed, committed, report):
    """Processo indipendente: stessi percorsi reali, interleaving forzato all'I/O."""
    from gioco27.core import config as cfg, cache as dec
    shared = Path(root) / ".gioco27"
    cfg._CONFIG_DIR, cfg._CONFIG_FILE = shared, shared / "config.json"
    dec._CACHE_DIR = shared / "cache"
    errors = []
    logger = SimpleNamespace(exception=lambda *a, **kw: errors.append(
        f"{a[0]}: {sys.exc_info()[1]!r}\n{traceback.format_exc()}"))
    cfg._log = dec._log = logger
    real_dump, real_replace = json.dump, os.replace
    first_dump = first_replace = True

    def dump(data, file, *args, **kwargs):
        nonlocal first_dump
        if not first_dump:
            return real_dump(data, file, *args, **kwargs)
        first_dump = False
        opened.wait(10)  # entrambi i save hanno aperto il proprio temporaneo
        if index == 1:
            assert written_a.wait(10)
        real_dump(data, file, *args, **kwargs)
        file.flush()
        if index == 0:
            written_a.set()
            assert written_b.wait(10)
        else:
            written_b.set()

    def replace(source, dest):
        nonlocal first_replace
        if not first_replace:
            return real_replace(source, dest)
        first_replace = False
        closed.wait(10)  # entrambi i descrittori sono chiusi, anche su Windows
        if index == 1:
            assert committed.wait(10)
        try:
            real_replace(source, dest)
        finally:
            if index == 0:
                committed.set()

    json.dump, os.replace = dump, replace
    try:
        if kind == "config":
            instance = cfg.Config()
            instance["last_expression"] = "A" * 4000 if index == 0 else "B"
            instance.save()
        else:
            identity = (("SCD_U",) * 3,) * 3
            # Contenuto identico: le due istanze cercano lo stesso bersaglio.
            dec.save_decompositions(list(range(27)), [identity])
        report.put((index, errors))
    except BaseException as exc:
        report.put((index, [repr(exc)]))
    finally:
        json.dump, os.replace = real_dump, real_replace


@pytest.mark.parametrize("kind", ["config", "cache"])
def test_r2_due_istanze_scrivono_senza_collisioni(kind, tmp_path, monkeypatch):
    shared = tmp_path / ".gioco27"
    (shared / "cache").mkdir(parents=True)
    ctx = multiprocessing.get_context("spawn")
    opened, closed = ctx.Barrier(2), ctx.Barrier(2)
    written_a, written_b, committed, report = ctx.Event(), ctx.Event(), ctx.Event(), ctx.Queue()
    processes = [ctx.Process(target=_persistent_writer,
                            args=(str(tmp_path), kind, i, opened, written_a, written_b, closed, committed, report))
                 for i in range(2)]
    try:
        for process in processes:
            process.start()
        outcomes = [report.get(timeout=20) for _ in processes]
        for process in processes:
            process.join(10)
            assert process.exitcode == 0
        errors = [error for _, group in outcomes for error in group]
        path = shared / "config.json" if kind == "config" else next((shared / "cache").glob("dec_*.json"))
        content = path.read_text(encoding="utf-8")
        try:
            payload = json.loads(content)
        except ValueError as exc:
            pytest.fail(f"JSON corrotto fra istanze: {exc}; errori: {errors}")
        assert errors == [], errors
        if kind == "config":
            expected = dict(config._DEFAULTS)
            assert payload == dict(expected, last_expression="B")
        else:
            monkeypatch.setattr(cache, "_CACHE_DIR", shared / "cache")
            assert cache.load_decompositions(list(range(27))) == [(("SCD_U",) * 3,) * 3]
        assert [p for p in shared.rglob("*") if p.is_file()] == [path]
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
            if process.pid is not None:
                process.join(10)
        report.close()
        report.join_thread()


@pytest.mark.parametrize("kind", ["config", "cache"])
@pytest.mark.parametrize("fail", [False, True])
def test_r2_salvataggio_preserva_file_e_rimuove_solo_il_proprio_temporaneo(kind, fail, tmp_path, monkeypatch):
    errors = []
    monkeypatch.setattr(config, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "_CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(cache, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "_log", SimpleNamespace(exception=lambda *a: errors.append(a)))
    monkeypatch.setattr(cache, "_log", SimpleNamespace(exception=lambda *a: errors.append(a)))
    perm = list(range(27))
    path = config._CONFIG_FILE if kind == "config" else cache._cache_path(perm)
    previous = b'{"precedente": "intatto"}\r\n'
    path.write_bytes(previous)
    neighbor = path.with_suffix(".json.tmp")
    neighbor.write_bytes(b"file preesistente\x00\xff")
    instance = config.Config()
    instance["last_expression"] = "nuova"
    identity = (("SCD_U",) * 3,) * 3

    def dump_error(data, file, **kw):
        file.write('{"parziale":')
        raise ValueError("serializzazione interrotta")

    if fail:
        monkeypatch.setattr(json, "dump", dump_error)
    if kind == "config":
        instance.save()
    else:
        cache.save_decompositions(perm, [identity])
    assert bool(errors) == fail
    if fail:
        assert path.read_bytes() == previous
    elif kind == "config":
        assert json.loads(path.read_text(encoding="utf-8"))["last_expression"] == "nuova"
    else:
        assert cache.load_decompositions(perm) == [identity]
    assert neighbor.read_bytes() == b"file preesistente\x00\xff"
    assert set(tmp_path.iterdir()) == {path, neighbor}


@pytest.mark.parametrize("persistent", [False, True])
def test_r2_cache_accesso_temporaneamente_negato(persistent, tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(cache.time, "sleep", lambda seconds: None)
    errors, attempts = [], []
    monkeypatch.setattr(cache, "_log", SimpleNamespace(exception=lambda *a: errors.append(a)))
    perm = list(range(27))
    path = cache._cache_path(perm)
    path.write_bytes(b"precedente")
    replace = os.replace

    def busy(source, dest):
        attempts.append(source)
        if persistent or len(attempts) == 1:
            raise PermissionError("file occupato da un'altra istanza")
        replace(source, dest)

    monkeypatch.setattr(os, "replace", busy)
    identity = (("SCD_U",) * 3,) * 3
    cache.save_decompositions(perm, [identity])
    assert len(attempts) == (3 if persistent else 2)
    assert bool(errors) == persistent
    if persistent:
        assert path.read_bytes() == b"precedente"
    else:
        assert cache.load_decompositions(perm) == [identity]
    assert set(tmp_path.iterdir()) == {path}
