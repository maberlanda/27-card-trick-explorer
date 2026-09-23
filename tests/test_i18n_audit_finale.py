"""
Audit i18n finale: output dinamici visibili solo dopo un'azione.

Il punto di partenza è il pulsante «✔ Verifica / Verify», il cui rapporto
restava in italiano con l'interfaccia inglese. Gli altri test coprono i
residui trovati ispezionando callback e output: export massivi (conferme,
limiti, stato, annullamento, errori), dettaglio della Tavola 216 e
ricostruzione dagli Assi, filtri P/J, nota della Distribuzione, errori di
parsing dell'Explorer, tipo delle classi di coniugio, anteprima del dialogo
LaTeX/SVG, titolo degli errori nei thread, reset delle schede.

Per ogni output si controlla l'italiano (identico al testo originale) e
l'inglese (nessun residuo italiano); dati, formule e codici non cambiano.
"""
import threading
from string import Formatter
from types import SimpleNamespace

import pytest

from gioco27.gui import i18n


@pytest.fixture(autouse=True)
def italian_default():
    i18n.set_language("it")
    yield
    i18n.set_language("it")


def _lang(language):
    i18n.set_language(language)


# ─────────────────────────────── cataloghi ─────────────────────────────────

def test_cataloghi_simmetrici_e_placeholder_coerenti():
    it, en = i18n.CATALOGS["it"], i18n.CATALOGS["en"]
    assert set(it) == set(en)
    assert len(it) == 1316  # +1 in E, +3 in F, +2 in G2, +22 in H1 (presentation degli errori applicativi)
    fields = lambda s: sorted(n for _, n, _, _ in Formatter().parse(s) if n)
    for key in it:
        assert fields(it[key]) == fields(en[key]), key


# ─────────────────────────────── Verify ────────────────────────────────────

ORIGINAL_KEYS = ("fisica_vs_algebra_216", "fisica_vs_matrici_1728", "ancore_libro",
                 "statistiche_cap100", "ricostruzione_assi", "trucco_729", "esito")


def _report(skipped=False):
    return {
        "fisica_vs_algebra_216": "ok",
        "fisica_vs_matrici_1728": "saltato (numpy assente)" if skipped else "ok (1728)",
        "ancore_libro": "ok (#100, #82)",
        "statistiche_cap100": "ok",
        "ricostruzione_assi": "ok (216/216)",
        "trucco_729": "ok (729/729)",
        "esito": "TUTTO OK",
    }


@pytest.mark.parametrize("skipped", [False, True])
def test_verify_rapporto_italiano_identico_all_originale(skipped):
    from gioco27.gui.app import format_selftest_report

    rapporto = _report(skipped)
    originale = "\n".join(f"{k:26s} {v}" for k, v in rapporto.items())
    assert format_selftest_report(rapporto) == originale


@pytest.mark.parametrize("skipped", [False, True])
def test_verify_rapporto_inglese(skipped):
    from gioco27.gui.app import format_selftest_report

    _lang("en")
    text = format_selftest_report(_report(skipped))
    for italian in ORIGINAL_KEYS + ("saltato", "assente", "TUTTO OK"):
        assert italian not in text, italian
    for english in ("Physics vs algebra (216)", "Physics vs matrices (1728)",
                    "Book anchors", "Chapter 100 statistics",
                    "Reconstruction from Aces", "Trick (729 pairs)", "Outcome",
                    "ALL OK", "ok (#100, #82)", "ok (216/216)", "ok (729/729)"):
        assert english in text, english
    assert ("skipped (numpy not installed)" in text) == skipped
    assert ("ok (1728)" in text) == (not skipped)
    assert len(text.splitlines()) == 7


def test_verify_chiave_sconosciuta_resta_leggibile():
    from gioco27.gui.app import format_selftest_report

    _lang("en")
    assert format_selftest_report({"nuovo_controllo": "ok"}).startswith("nuovo_controllo")


def test_selftest_restituisce_dati_invariati_in_ogni_lingua():
    from gioco27.core.gioco_reale import selftest

    _lang("en")
    en = selftest(completo=False)
    _lang("it")
    it = selftest(completo=False)
    assert en == it
    assert en["esito"] == "TUTTO OK" and en["ancore_libro"] == "ok (#100, #82)"


class _SyncThread:
    def __init__(self, target, daemon=None):
        self._target = target

    def start(self):
        self._target()


def _run_verify(monkeypatch, language, break_anchor=False):
    from gioco27.core import gioco_reale
    from gioco27.gui import app as app_module

    shown = []
    monkeypatch.setattr(threading, "Thread", _SyncThread)
    monkeypatch.setattr(app_module.messagebox, "showinfo",
                        lambda title, msg, **kw: shown.append(("info", title, msg)))
    monkeypatch.setattr(app_module.messagebox, "showerror",
                        lambda title, msg, **kw: shown.append(("error", title, msg)))
    monkeypatch.setattr(gioco_reale, "selftest",
                        lambda completo=True, _real=gioco_reale.selftest: _real(False))
    if break_anchor:
        real = gioco_reale.riga_tavola

        def broken(n):
            row = dict(real(n))
            if n == 100:
                row["assi"] = (0, 0, 0)
            return row
        monkeypatch.setattr(gioco_reale, "riga_tavola", broken)
    statuses = []
    fake = SimpleNamespace(status_var=SimpleNamespace(set=statuses.append),
                           _ui=lambda fn: fn())
    _lang(language)
    app_module.App._run_selftest(fake)
    return statuses, shown


def test_verify_callback_inglese_successo(monkeypatch):
    statuses, shown = _run_verify(monkeypatch, "en")
    assert statuses == ["Integrity check in progress…", "Integrity check completed."]
    kind, title, msg = shown[0]
    assert kind == "info" and title == "Integrity check"
    assert msg.startswith("All checks passed:")
    assert "Physics vs algebra (216)" in msg and "ALL OK" in msg
    for italian in ("Verifica", "fisica_vs", "TUTTO OK", "ancore_libro"):
        assert italian not in msg and italian not in title


def test_verify_callback_italiano_successo(monkeypatch):
    statuses, shown = _run_verify(monkeypatch, "it")
    assert statuses == ["Verifica di integrità in corso…", "Verifica completata."]
    kind, title, msg = shown[0]
    assert (kind, title) == ("info", "Verifica di integrità")
    assert msg.startswith("Tutte le verifiche superate:\n\nfisica_vs_algebra_216")
    assert "esito                      TUTTO OK" in msg


@pytest.mark.parametrize("language, prefix, detail, status", [
    ("it", "INCOERENZA RILEVATA:\n", "ancora #100", "Verifica FALLITA!"),
    ("en", "INCONSISTENCY DETECTED:\n", "anchor #100", "Integrity check FAILED!"),
])
def test_verify_callback_ramo_di_errore(monkeypatch, language, prefix, detail, status):
    statuses, shown = _run_verify(monkeypatch, language, break_anchor=True)
    kind, _title, msg = shown[0]
    assert kind == "error"
    assert msg == prefix + detail
    assert statuses[-1] == status


def test_verify_tooltip_localizzato():
    assert i18n.tr("tooltip.verify").startswith("Verifica di integrità")
    _lang("en")
    assert i18n.tr("tooltip.verify").startswith("Integrity check")
    assert "1728" in i18n.tr("tooltip.verify")


# ────────────────────────── export massivi (app) ───────────────────────────

class _Widget:
    def __init__(self):
        self.values = []

    def configure(self, **kw):
        pass

    def set(self, value):
        self.values.append(value)

    def __setitem__(self, key, value):
        pass


def _export_harness(monkeypatch, *, n=10, busy=False, confirm=True, outcome="ok"):
    from gioco27.core.parallel import ExportAnnullato
    from gioco27.gui import app as app_module

    dialogs = []
    for name in ("showinfo", "showwarning", "showerror"):
        monkeypatch.setattr(app_module.messagebox, name,
                            lambda title, msg, _n=name, **kw: dialogs.append((_n, title, msg)))
    monkeypatch.setattr(app_module.messagebox, "askyesno",
                        lambda title, msg, **kw: dialogs.append(("ask", title, msg)) or confirm)
    monkeypatch.setattr(app_module.filedialog, "asksaveasfilename",
                        lambda **kw: dialogs.append(("save", kw.get("title"), "")) or "/tmp/out.csv")
    monkeypatch.setattr(app_module, "count_combinations_ex", lambda f: n)

    def fake_thread(widget, job, error_title=None, on_error=None):
        try:
            job()
        except Exception as exc:
            dialogs.append(("thread_error", error_title, str(exc)))
            on_error(exc)
    monkeypatch.setattr(app_module, "run_in_thread", fake_thread)

    def gen(path, filters, n_workers, progress_cb, annullato):
        if outcome == "cancel":
            raise ExportAnnullato(3, n)
        if outcome == "error":
            raise RuntimeError("boom")
        return n

    status = _Widget()
    fake = SimpleNamespace(
        _closing=False, _export_busy=busy, _export_stop=threading.Event(),
        _btn_annulla=_Widget(), progress=_Widget(), status_var=status,
        _get_filters=lambda: [], update_idletasks=lambda: None,
        _ui=lambda fn: fn(),
    )
    fake._fine_export = lambda: setattr(fake, "_export_busy", False)
    fake._run_generation = lambda **kw: app_module.App._run_generation(
        fake, **{**kw, "gen_func": gen})
    return fake, dialogs, status


def _gen(fake, which):
    from gioco27.gui import app as app_module
    getattr(app_module.App, which)(fake)


@pytest.mark.parametrize("language", ["it", "en"])
def test_export_conferma_salvataggio_e_stato(monkeypatch, language):
    fake, dialogs, status = _export_harness(monkeypatch, n=200_000)
    _lang(language)
    _gen(fake, "_gen_csv")
    ask = next(d for d in dialogs if d[0] == "ask")
    save = next(d for d in dialogs if d[0] == "save")
    if language == "it":
        assert ask[1] == "Conferma"
        assert ask[2] == ("Verranno scritte 200,000 righe CSV (circa 200,000 x 400 byte).\n"
                          "Potrebbe richiedere molto tempo e molto spazio su disco.\n\nProcedere?")
        assert save[1] == "Salva CSV"
        assert status.values[-1] == "✓ CSV salvato: out.csv  (200,000 righe)"
        assert status.values[0].startswith("Generazione CSV in corso... (0/200,000")
    else:
        assert ask[1] == "Confirm"
        assert ask[2].startswith("200,000 CSV rows will be written")
        assert save[1] == "Save CSV"
        assert status.values[-1] == "✓ CSV saved: out.csv  (200,000 rows)"
        assert status.values[0].startswith("Generating CSV... (0/200,000")


@pytest.mark.parametrize("language, title_pdf, title_detail, detail_kind", [
    ("it", "Salva PDF", "Salva PDF dettagliato", "PDF dettagliato"),
    ("en", "Save PDF", "Save detailed PDF", "Detailed PDF"),
])
def test_export_pdf_e_pdf_dettagliato(monkeypatch, language, title_pdf, title_detail,
                                      detail_kind):
    fake, dialogs, status = _export_harness(monkeypatch, n=5)
    _lang(language)
    _gen(fake, "_gen_pdf")
    _gen(fake, "_gen_pdf_detail")
    saves = [d[1] for d in dialogs if d[0] == "save"]
    assert saves == [title_pdf, title_detail]
    assert any(v.startswith(f"✓ {detail_kind} ") for v in status.values)
    unit = "pagine" if language == "it" else "pages"
    assert any(v.endswith(f"(5 {unit})") for v in status.values)


@pytest.mark.parametrize("language, busy, empty, too_large", [
    ("it", ("Export in corso", "C'e' gia' un export in corso."),
     ("Nessuna combinazione", "I filtri attuali non producono combinazioni."),
     ("Export troppo grande", "L'export richiederebbe 5,159,780,352 elementi")),
    ("en", ("Export in progress", "An export is already in progress."),
     ("No combinations", "The current filters produce no combinations."),
     ("Export too large", "The export would require 5,159,780,352 elements")),
])
def test_export_dialoghi_di_blocco(monkeypatch, language, busy, empty, too_large):
    _lang(language)
    fake, dialogs, _ = _export_harness(monkeypatch, busy=True)
    _gen(fake, "_gen_csv")
    fake, d2, _ = _export_harness(monkeypatch, n=0)
    _gen(fake, "_gen_csv")
    fake, d3, _ = _export_harness(monkeypatch, n=5_159_780_352)
    _gen(fake, "_gen_csv")
    assert dialogs[0][1] == busy[0] and dialogs[0][2].startswith(busy[1])
    assert d2[0][1] == empty[0] and d2[0][2] == empty[1]
    assert d3[0][1] == too_large[0] and d3[0][2].startswith(too_large[1])
    assert "20,000,000" in d3[0][2] and "*" in d3[0][2]


@pytest.mark.parametrize("language, cancelled, failed, error_title", [
    ("it", "✕ CSV annullato — nessun file creato (3 righe calcolate)",
     "✗ CSV non completato.", "Errore CSV"),
    ("en", "✕ CSV canceled — no file created (3 rows calculated)",
     "✗ CSV not completed.", "CSV error"),
])
def test_export_annullamento_ed_errore(monkeypatch, language, cancelled, failed, error_title):
    _lang(language)
    fake, _, status = _export_harness(monkeypatch, outcome="cancel")
    _gen(fake, "_gen_csv")
    assert status.values[-1] == cancelled
    fake, dialogs, status = _export_harness(monkeypatch, outcome="error")
    _gen(fake, "_gen_csv")
    assert status.values[-1] == failed
    assert ("thread_error", error_title, "boom") in dialogs


def test_annullamento_in_corso(monkeypatch):
    from gioco27.gui import app as app_module

    for language, expected in (("it", "Annullamento in corso…"), ("en", "Canceling…")):
        _lang(language)
        status = _Widget()
        fake = SimpleNamespace(_export_busy=True, _export_stop=threading.Event(),
                               _btn_annulla=_Widget(), status_var=status)
        app_module.App._annulla_export(fake)
        assert status.values == [expected]


def test_reset_con_errori_mostra_nomi_localizzati():
    from gioco27.gui import app as app_module

    def boom():
        raise RuntimeError("x")

    for language, expected in (("it", "Reset completato (problemi su: Anteprima, Cicli)."),
                               ("en", "Reset completed (problems in: Preview, Cycles).")):
        _lang(language)
        status = _Widget()
        fake = SimpleNamespace(
            filter_frames=[], count_var=_Widget(), progress=_Widget(),
            _update_count=lambda: None, _reset_anteprima=boom,
            _reset_analisi=lambda: None, _explorer_clear=lambda: None,
            _cycles_frame=SimpleNamespace(reset=boom),
            _simulator_frame=SimpleNamespace(reset=lambda: None),
            _shuffle_viewer=SimpleNamespace(clear_all=lambda: None),
            status_var=status)
        app_module.App._reset(fake)
        assert status.values[-1] == expected


def test_titolo_errore_nei_thread_segue_la_lingua(monkeypatch):
    from gioco27.gui import common

    shown = []
    monkeypatch.setattr(common.messagebox, "showerror", lambda t, m: shown.append(t))
    monkeypatch.setattr(common.threading, "Thread", _SyncThread)
    monkeypatch.setattr(common, "ui_call", lambda w, fn: fn())

    def job():
        raise ValueError("x")

    _lang("en")
    common.run_in_thread(SimpleNamespace(), job)
    _lang("it")
    common.run_in_thread(SimpleNamespace(), job)
    assert shown == ["Error", "Errore"]


# ───────────────────────── Explorer: errori e tipi ─────────────────────────

ERROR_CASES = [
    ("FOO", "Errore di parsing:\nSimbolo sconosciuto: 'FOO'",
     "Parsing error:\nUnknown symbol: 'FOO'"),
    ("SCD_U $", "Errore di parsing:\nCarattere non riconosciuto: '$'",
     "Parsing error:\nUnrecognized character: '$'"),
    ("(SCD_U x SCD_U x SCD_U", "Errore di parsing:\nParentesi non chiusa",
     "Parsing error:\nUnclosed parenthesis"),
    ("SCD_U x SCD_U", "Errore di parsing:\nIl prodotto di Kronecker richiede esattamente 3 fattori, trovati 2.",
     "Parsing error:\nThe Kronecker product requires exactly 3 factors; found 2."),
    ("MSC o SCD_U", "Errore di parsing:\nComposizione tra oggetti di tipo diverso: tipo 27 ∘ tipo 3",
     "Parsing error:\nComposition between objects of different types: type 27 ∘ type 3"),
    ("MSC o", "Errore di parsing:\nEspressione incompleta: atteso un termine.",
     "Parsing error:\nIncomplete expression: a term was expected."),
    ("SCD_U", "Errore di valutazione:\nIl risultato è di tipo 3.",
     "Evaluation error:\nThe result is of type 3."),
    ("MSC MSC", "Errore di parsing:\nToken inatteso dopo la fine dell'espressione: 'MSC'",
     "Parsing error:\nUnexpected token after the end of the expression: 'MSC'"),
]


@pytest.mark.parametrize("expr, italian, english", ERROR_CASES)
def test_errori_explorer_nelle_due_lingue(expr, italian, english):
    from gioco27.core.algebra import Controller

    _lang("it")
    r_it = Controller().process(expr)
    _lang("en")
    r_en = Controller().process(expr)
    assert not r_it["ok"] and not r_en["ok"]
    assert r_it["error"].startswith(italian), r_it["error"]
    assert r_en["error"].startswith(english), r_en["error"]
    for word in ("Errore", "Simbolo", "Carattere", "Parentesi", "Espressione",
                 "Composizione", "tipo 3", "trovati", "Token inatteso"):
        assert word not in r_en["error"]


def test_explorer_forma_canonica_non_disponibile_e_tipo_composta():
    from gioco27.core.algebra import Controller, display_normal_form_kind

    expr = "J o MSC"
    _lang("it")
    r_it = Controller().process(expr)
    _lang("en")
    r_en = Controller().process(expr)
    assert r_it["normal_form_kind"] == r_en["normal_form_kind"]      # dato invariato
    assert r_it["perm"] == r_en["perm"]
    assert r_it["canonical_symbolic"].startswith("Non disponibile")
    assert r_en["canonical_symbolic"].startswith("Unavailable")
    assert display_normal_form_kind("composta") == "composite"
    assert display_normal_form_kind("K o MSC") == "K o MSC"
    _lang("it")
    assert display_normal_form_kind("composta") == "composta"


# ─────────────────────── Tavola 216, filtri, gruppi ────────────────────────

@pytest.mark.parametrize("language, expected", [
    ("it", "posizioni incompatibili: nessuna disposizione semplice produce questi Assi"),
    ("en", "incompatible positions: no simple arrangement produces these Aces"),
])
def test_ricostruzione_assi_messaggio(language, expected):
    from gioco27.core import gioco_reale as gr

    _lang(language)
    with pytest.raises(ValueError) as exc:
        gr.tabellone_da_assi(0, 0, 0)
    assert str(exc.value).startswith(expected)
    with pytest.raises(ValueError):
        gr.tabellone_da_assi(0, 0, 30)
    # il risultato valido non dipende dalla lingua
    assert gr.tabellone_da_assi(*gr.riga_tavola(100)["assi"]) == (("CDS", "CDS", "CSD"), 100)


def _tk_root():
    tk = pytest.importorskip("tkinter")
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    root.withdraw()
    return tk, root


def _texts(widget):
    out = []
    try:
        out.append(str(widget.cget("text")))
    except Exception:
        pass
    for child in widget.winfo_children():
        out.extend(_texts(child))
    return out


@pytest.mark.parametrize("language", ["it", "en"])
def test_dettaglio_tavola(language):
    tk, root = _tk_root()
    from gioco27.gui.tavola_tab import TavolaFrame
    try:
        _lang(language)
        frame = TavolaFrame(root)
        frame._tv.selection_set("100")
        frame._dettaglio()
        win = [w for w in frame.winfo_children() if isinstance(w, tk.Toplevel)][-1]
        text = win.winfo_children()[0].get("1.0", "end")
    finally:
        root.destroy()
    if language == "it":
        assert text.startswith("Disposizione semplice #100\n" + "=" * 60)
        assert "Mescolamenti (righe del tabellone, prima in basso): CDS CDS CSD" in text
        assert "Assi: A♠→13  A♣→8  A♥→18" in text
        assert "T (posizione finale della carta n):" in text
        assert "Tabellone (dal basso verso l'alto):\n   riga 1:  CDS   (impila: DSC)" in text
    else:
        for italian in ("Disposizione", "Mescolamenti", "Impilamenti", "Assi:", "Periodo",
                        "punti fissi", "auto-inversa", "Tabellone", "riga", "impila"):
            assert italian not in text, italian
        assert text.startswith("Simple arrangement #100")
        assert "CDS CDS CSD" in text and "A♠→13  A♣→8  A♥→18" in text
        assert "   row 1:  CDS   (stack: DSC)" in text


@pytest.mark.parametrize("language", ["it", "en"])
def test_filtri_p_j(language):
    tk, root = _tk_root()
    from gioco27.gui.filter_frame import FilterFrame
    try:
        _lang(language)
        ff = FilterFrame(root, stage_num=1)
        texts = "\n".join(_texts(ff))
    finally:
        root.destroy()
    if language == "it":
        for italian in ("  Stadio 1  ", "Permutazioni  P", "Permutazioni  J", "Fissa",
                        "oppure seleziona uno o più valori:", "Valori:",
                        "J UNIFORMI  —  J0 = J1 = J2", "2 combinazioni J invece di 8"):
            assert italian in texts, italian
    else:
        for italian in ("Stadio", "Permutazioni", "Fissa", "seleziona", "Valori",
                        "UNIFORMI", "combinazioni"):
            assert italian not in texts, italian
        for english in ("  Stage 1  ", "Permutations  P", "Fix", "or select one or more values:",
                        "Values:", "UNIFORM J  —  J0 = J1 = J2", "2 J combinations instead of 8"):
            assert english in texts, english


@pytest.mark.parametrize("language", ["it", "en"])
def test_nota_distribuzione(language):
    tk, root = _tk_root()
    from gioco27.gui.distribution_tab import DistributionFrame
    try:
        _lang(language)
        frame = SimpleNamespace(_tbl_txt=tk.Text(root))
        DistributionFrame._fill_table(frame, {"histogram": {46656: 216},
                                              "total_T": 216, "total_decomp": 216 * 46656})
        text = frame._tbl_txt.get("1.0", "end")
    finally:
        root.destroy()
    assert "A2∘MSC∘A1∘MSC∘A0∘MSC" in text and "46656" in text
    if language == "it":
        assert "Nota: k-decomp = numero di decomposizioni" in text
    else:
        assert "Note: k-decomp = number of decompositions" in text
        assert "Nota" not in text and "raggiungibili" not in text


def test_tipo_classi_di_coniugio():
    from gioco27.gui.export_group_dialog import _class_type

    triple = ("SCD_U", "SDC_U", "CDS_U")
    assert _class_type(triple) == ("(id, trasp., 3-ciclo)", 6)
    _lang("en")
    assert _class_type(triple) == ("(id, transp., 3-cycle)", 6)


def test_anteprima_troncata_ed_errore_generazione():
    from gioco27.gui.export_group_dialog import _PreviewExportDialog as Dialog

    class Tab:
        def __init__(self):
            self.text = ""

        def configure(self, **kw):
            pass

        def delete(self, *a):
            self.text = ""

        def insert(self, _where, s):
            self.text += s

    for language, marker, error in (
            ("it", "anteprima troncata", "% Errore nella generazione: x"),
            ("en", "preview truncated", "% Generation error: x")):
        _lang(language)
        tab = Tab()

        def bad():
            raise RuntimeError("x")
        fake = SimpleNamespace(_cache={}, _PREVIEW_MAX=5, _tabs={"a": tab, "b": Tab()},
                               _items=[("a", "", None, lambda: "0123456789"),
                                       ("b", "", None, bad)])
        fake._content = lambda key, gen: Dialog._content(fake, key, gen)
        Dialog._refresh_preview(fake)
        assert tab.text.startswith("01234") and marker in tab.text
        # B12: l'errore resta localizzato, ma vive nell'anteprima e non nella
        # cache del contenuto. In cache c'e' un esito tipizzato fallito, con il
        # messaggio grezzo dell'eccezione: nessun file potra' mai contenerlo.
        esito = fake._cache["b"]
        assert esito.ok is False and esito.testo == "" and esito.errore == "x"
        assert fake._tabs["b"].text == error


def test_riepilogo_excel_troppo_lungo(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    from gioco27.core.algebra import scrivi_excel

    risultati = [{"perm_str": "[0]", "simboliche": ["X" * 20000, "Y" * 20000], "n_sim": 2}]
    for language, expected in (("it", "Riepilogo oltre il limite"),
                               ("en", "Summary exceeds the 32767-character")):
        _lang(language)
        path = tmp_path / f"a_{language}.xlsx"
        scrivi_excel(risultati, str(path))
        wb = openpyxl.load_workbook(path, read_only=True)
        try:
            assert wb.sheetnames == ["Perm -> Simboliche", "Simbolica -> Perm"]
            cell = next(wb["Perm -> Simboliche"].iter_rows(min_row=2, values_only=True))[1]
        finally:
            wb.close()
        assert cell.startswith(expected) and "'Simbolica -> Perm'" in cell


# ───────────────────────── guardia contro i residui ────────────────────────

RESIDUI = {
    "gioco27/gui/app.py": ["Verranno generate", "Verranno esportate", "Verranno scritte",
                           "Salva PDF", "Salva CSV", "in corso... (0/", "annullato — nessun file",
                           "non completato.", "Annullamento in corso", "Export troppo grande",
                           "\"Nessuna combinazione\"", "INCOERENZA RILEVATA",
                           "Verifica di integrità: simulazione", "In modalità principiante",
                           "\"Conferma\"", "\"Errore\""],
    "gioco27/gui/common.py": ['error_title="Errore"'],
    "gioco27/gui/tavola_tab.py": ["Disposizione semplice #", "Tabellone (dal basso",
                                  "'auto-inversa' if", "posizione finale della carta"],
    "gioco27/gui/filter_frame.py": ['"Fissa"', "oppure seleziona", '"Valori:"',
                                    'text="  ⚡  J UNIFORMI', "combinazioni J invece", "Stadio {stage_num}"],
    "gioco27/gui/distribution_tab.py": ["Nota: k-decomp"],
    "gioco27/gui/export_group_dialog.py": ["Errore nella generazione", "anteprima troncata"],
    "gioco27/gui/preview_tab.py": ["T (Anteprima)"],
    "gioco27/core/algebra.py": ['f"Errore di parsing', 'f"Errore di valutazione',
                                'f"Simbolo sconosciuto', '"Parentesi non chiusa',
                                '"Il risultato è di tipo 3', '"Non disponibile',
                                '"Riepilogo oltre il limite'],
    "gioco27/core/gioco_reale.py": ["posizioni incompatibili", '"ancora #100"'],
}


def test_residui_corretti_non_ricompaiono():
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1]
    for rel, phrases in RESIDUI.items():
        src = (root / rel).read_text(encoding="utf-8")
        for phrase in phrases:
            assert phrase not in src, f"{rel}: {phrase}"
