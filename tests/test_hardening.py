"""
Test delle correzioni di robustezza e delle ottimizzazioni introdotte
nella revisione 3.1.x.

Ogni test documenta il problema che previene.
"""
import ast
import itertools
import json
import os
import tempfile

import pytest

from gioco27.core.constants import ANY, P_OPTS, J_OPTS


# ─────────────────────────── infrastruttura parallela ──────────────────────

def test_chunked_e_pigro_e_completo():
    """chunked non deve materializzare l'iterabile: dev'essere un generatore."""
    from gioco27.core.parallel import chunked
    assert list(chunked(range(7), 3)) == [[0, 1, 2], [3, 4, 5], [6]]
    assert list(chunked([], 3)) == []
    with pytest.raises(ValueError):
        list(chunked(range(3), 0))

    # Su un generatore infinito deve restituire il primo blocco e fermarsi.
    def infinito():
        i = 0
        while True:
            yield i
            i += 1
    it = chunked(infinito(), 4)
    assert next(it) == [0, 1, 2, 3]
    assert next(it) == [4, 5, 6, 7]


def _square(task):
    """Worker top-level per il test di imap_ordered (deve essere picklable)."""
    start, block = task
    return start, [x * x for x in block]


def test_imap_ordered_preserva_ordine():
    """
    L'ordine dei risultati determina la numerazione delle righe CSV e delle
    pagine PDF: se imap_ordered restituisse i blocchi nell'ordine di
    completamento, l'export parallelo non coinciderebbe col sequenziale.
    """
    from gioco27.core.parallel import imap_ordered
    tasks = [(i, list(range(i, i + 4))) for i in range(0, 60, 4)]
    got = list(imap_ordered(_square, iter(tasks), n_workers=2, max_pending=3))
    assert got == [_square(t) for t in tasks]


def test_plan_workers_sceglie_il_sequenziale_sui_carichi_piccoli():
    """
    La decisione si basa sul LAVORO stimato, non su una soglia fissa di
    elementi: la soglia fissa (80 per il PDF, 400 per il CSV) era tarata su
    macchine da 4-8 core e su 128 core limitava l'export standard a 21 worker.
    """
    from gioco27.core.parallel import (COSTO_PAGINA_PDF, COSTO_RIGA_CSV,
                                       LAVORO_MINIMO_S, plan_workers)

    assert plan_workers(100_000, n_workers=1) is None, "un solo core"
    assert plan_workers(4, n_workers=8) is None, "troppi pochi elementi"

    # lavoro sotto la soglia -> in-process, anche con 127 core liberi
    pochi = int(LAVORO_MINIMO_S / COSTO_PAGINA_PDF / 4)
    assert plan_workers(pochi, 127, cost_per_item=COSTO_PAGINA_PDF) is None

    # il CSV e' cosi' veloce che il parallelo conviene solo da decine di
    # migliaia di righe in su
    assert plan_workers(1728, 127, cost_per_item=COSTO_RIGA_CSV) is None
    assert plan_workers(1_000_000, 127, cost_per_item=COSTO_RIGA_CSV) is not None


def test_plan_workers_usa_i_core_disponibili():
    """Su molti core l'export standard non deve piu' fermarsi a 21 worker."""
    from gioco27.core.parallel import COSTO_PAGINA_PDF, plan_workers
    nw, _chunk = plan_workers(1728, 127, cost_per_item=COSTO_PAGINA_PDF)
    assert nw > 21, f"solo {nw} worker: il vecchio tetto morde ancora"
    nw_grande, _ = plan_workers(46656, 127, cost_per_item=COSTO_PAGINA_PDF)
    assert nw_grande == 127, "su un export grande vanno usati tutti i core"


def test_plan_workers_da_lavoro_sensato_a_ogni_worker():
    """
    Ogni worker deve avere abbastanza lavoro da giustificare il proprio avvio
    e il proprio blocco da unire: spezzettare all'infinito peggiora.
    """
    from gioco27.core.parallel import (COSTO_PAGINA_PDF, LAVORO_PER_WORKER_S,
                                       plan_workers)
    for totale in (500, 1728, 10_000, 46_656, 200_000):
        piano = plan_workers(totale, 127, cost_per_item=COSTO_PAGINA_PDF)
        if piano is None:
            continue
        nw, chunk = piano
        assert chunk * COSTO_PAGINA_PDF >= LAVORO_PER_WORKER_S * 0.9, \
            f"{totale}: blocchi da {chunk} = troppo poco lavoro per worker"
        assert nw * chunk >= totale, "i blocchi devono coprire tutto"


def test_un_blocco_per_worker():
    """
    Un blocco per worker, non quattro: le pagine hanno costo uniforme, e ogni
    blocco in piu' e' un PDF parziale in piu' da unire, con la sua copia dei
    font incorporati.
    """
    from gioco27.core.parallel import COSTO_PAGINA_PDF, plan_workers
    nw, chunk = plan_workers(46_656, 127, cost_per_item=COSTO_PAGINA_PDF)
    import math
    assert math.ceil(46_656 / chunk) <= nw + 1


# ────────────────────── limite di sicurezza degli export ───────────────────

def _filtri_senza_vincoli():
    return [{k: ANY for k in ("p0", "p1", "p2", "j0", "j1", "j2")}
            for _ in range(3)]


def test_combinazioni_senza_filtri_sono_miliardi():
    """
    Documenta il numero che rendeva letale `list(iter_combinations_ex(...))`:
    (6³·2³)³ = 1728³. Se questo numero cambia, il limite va rivisto.
    """
    from gioco27.core.combinations import count_combinations_ex
    assert count_combinations_ex(_filtri_senza_vincoli()) == 1728 ** 3
    assert 1728 ** 3 == 5_159_780_352


def test_export_csv_rifiuta_subito_i_filtri_vuoti():
    """
    Prima: write_csv_parallel chiamava list() su 5,16 miliardi di combinazioni
    e il processo moriva per esaurimento memoria, senza messaggi.
    Ora: ExportTooLarge immediata e nessun file scritto.
    """
    from gioco27.core.permutations import write_csv_parallel
    from gioco27.core.parallel import ExportTooLarge
    d = tempfile.mkdtemp()
    out = os.path.join(d, "grande.csv")
    with pytest.raises(ExportTooLarge):
        write_csv_parallel(out, _filtri_senza_vincoli(), n_workers=2)
    assert not os.path.exists(out), "nessun file parziale deve restare"


def test_export_pdf_dettagliato_ha_un_limite_piu_basso():
    """
    Il PDF dettagliato deve tenere tutte le combinazioni in RAM (serve per
    l'«Elenco matrici trasposte»), quindi il suo tetto e' piu' stringente.
    """
    from gioco27.core.detail_pdf import MAX_DETAIL_COMBOS, generate_detail_pdf
    from gioco27.core.parallel import MAX_EXPORT_ITEMS, ExportTooLarge
    assert MAX_DETAIL_COMBOS < MAX_EXPORT_ITEMS
    d = tempfile.mkdtemp()
    with pytest.raises(ExportTooLarge):
        generate_detail_pdf(os.path.join(d, "x.pdf"), _filtri_senza_vincoli())


# ──────────────────────── iter_combinations: stesso ordine ─────────────────

def test_iter_combinations_ordine_come_i_cicli_annidati():
    """
    I 18 `for` annidati sono stati sostituiti da itertools.product: l'ordine di
    emissione deve restare identico, altrimenti cambia la numerazione
    «Combinazione #N» di tutti gli export.
    """
    from gioco27.core.combinations import iter_combinations
    f = [{'p0': ANY, 'p1': 'SCD_U', 'p2': 'SDC_U',
          'j0': ANY, 'j1': ANY, 'j2': 'I_3'} for _ in range(3)]

    def choices(val, opts):
        return opts if val == ANY else [val]

    axes = [choices(f[s][k], P_OPTS if k[0] == 'p' else J_OPTS)
            for s in range(3) for k in ('p0', 'p1', 'p2', 'j0', 'j1', 'j2')]
    attesi = [[c[0:6], c[6:12], c[12:18]] for c in itertools.product(*axes)]
    assert [[tuple(x) for x in c] for c in iter_combinations(f)] == \
           [[tuple(x) for x in c] for c in attesi]


# ─────────────────── T su vettori == T su matrici (7x piu' veloce) ─────────

def test_compute_T_perm_coincide_con_la_matrice():
    """
    compute_T_perm evita di costruire tre prodotti di Kronecker e cinque
    prodotti di matrici 27x27 per combinazione. Il risultato deve essere
    identico a quello ottenuto dalla matrice.
    """
    from gioco27.core.permutations import (compute_T_full, compute_T_perm,
                                           mat_to_perm27, perm27_to_mat)
    combos = list(itertools.islice(
        itertools.product(P_OPTS, P_OPTS, P_OPTS, J_OPTS, J_OPTS, J_OPTS),
        0, 1728, 53))
    assert len(combos) > 20
    for a in combos:
        for b in combos[:4]:
            params = [a, b, a]
            lab, T_label, T_perm = compute_T_perm(params)
            lab2, T_label2, T_perm2, M = compute_T_full(params)
            assert (lab, T_label, T_perm) == (lab2, T_label2, T_perm2)
            assert mat_to_perm27(M) == T_perm
            assert (perm27_to_mat(T_perm) == M).all()


def test_perm27_to_mat_e_una_matrice_di_permutazione():
    from gioco27.core.permutations import perm27_to_mat
    perm = [(7 * i + 3) % 27 for i in range(27)]
    M = perm27_to_mat(perm)
    assert M.sum() == 27
    assert (M.sum(axis=0) == 1).all() and (M.sum(axis=1) == 1).all()


# ──────────── distribuzione: conteggio veloce == forza bruta vera ──────────

def test_distribution_partial_coincide_con_la_forza_bruta():
    """
    Il conteggio delle decomposizioni non itera piu' su 216³ terne ma verifica
    che C = MSC∘A2∘MSC∘A1∘MSC sia un Kronecker e usa la tabella di Cayley.
    Qui si confronta con la forza bruta autentica su due indici esterni.
    """
    from gioco27.core.analysis import (_build_kron_table_27,
                                       _distribution_partial)

    K, msc = _build_kron_table_27()
    atteso = {}
    for outer_i in (0, 137):
        step1 = K[outer_i][msc]
        for j in range(216):
            C = msc[K[j][msc[step1]]]
            for a3 in range(216):
                key = K[a3][C].tobytes()
                atteso[key] = atteso.get(key, 0) + 1

    assert _distribution_partial([0, 137]) == atteso
    # struttura attesa: 216 T, ciascuno con 2*216 contributi
    assert len(atteso) == 216
    assert set(atteso.values()) == {2 * 216}


def test_distribuzione_completa_ha_la_forma_chiusa_attesa():
    from gioco27.core.analysis import compute_distribution_parallel
    d = compute_distribution_parallel(n_workers=1)
    assert d["total_T"] == 216
    assert d["total_decomp"] == 216 ** 3
    assert d["histogram"] == {216 ** 2: 216}


# ────────────────────────────── cache su JSON ─────────────────────────────

def test_cache_round_trip_json(tmp_path, monkeypatch):
    """
    La cache non usa piu' pickle (che puo' eseguire codice arbitrario in fase
    di load su file presi dal disco): il formato e' JSON.
    """
    from gioco27.core import cache
    monkeypatch.setattr(cache, "_CACHE_DIR", tmp_path)
    perm = list(range(27))
    dati = [(("SCD_U", "SDC_U", "CSD_U"),
             ("CDS_U", "DSC_U", "DCS_U"),
             ("SCD_U", "SCD_U", "SCD_U"))]
    cache.save_decompositions(perm, dati)
    assert cache.cache_entries() == 1
    assert cache.load_decompositions(perm) == dati
    files = list(tmp_path.glob("dec_*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["version"] == cache.CACHE_FORMAT_VERSION
    assert cache.clear_cache() == 1


def test_cache_scarta_le_versioni_vecchie(tmp_path, monkeypatch):
    from gioco27.core import cache
    monkeypatch.setattr(cache, "_CACHE_DIR", tmp_path)
    perm = list(range(27))
    cache.save_decompositions(perm, [(("SCD_U",) * 3,) * 3])
    path = next(tmp_path.glob("dec_*.json"))
    path.write_text(json.dumps({"version": 0, "results": []}), encoding="utf-8")
    assert cache.load_decompositions(perm) is None
    assert not path.exists(), "l'entry obsoleta deve essere rimossa"


def test_cache_ignora_file_corrotti(tmp_path, monkeypatch):
    from gioco27.core import cache
    monkeypatch.setattr(cache, "_CACHE_DIR", tmp_path)
    perm = list(range(27))
    cache.save_decompositions(perm, [(("SCD_U",) * 3,) * 3])
    next(tmp_path.glob("dec_*.json")).write_text("{non json", encoding="utf-8")
    assert cache.load_decompositions(perm) is None   # nessuna eccezione


# ───────────────────────── validazione della config ───────────────────────

@pytest.mark.parametrize("chiave,valore_invalido", [
    ("n_workers", -5),
    ("n_workers", "quattro"),
    ("use_parallel", "si"),
    ("livello", "GURU"),
    ("help_font_scale", 0),
    ("help_font_scale", 99),
    ("window_geometry", "rm -rf /"),
    ("decomp_mode", "X"),
])
def test_config_scarta_i_valori_invalidi(tmp_path, monkeypatch, chiave,
                                         valore_invalido):
    """
    config.json e' un file di testo nella home: puo' essere modificato a mano o
    arrivare da una versione precedente. Un valore fuori range non deve
    raggiungere la GUI (prima produceva font invisibili o schede mancanti).
    """
    from gioco27.core import config as C
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({chiave: valore_invalido}), encoding="utf-8")
    monkeypatch.setattr(C, "_CONFIG_FILE", cfg_file)
    monkeypatch.setattr(C, "_CONFIG_DIR", tmp_path)
    c = C.Config()
    assert c.get(chiave) == C._DEFAULTS[chiave]


@pytest.mark.parametrize("chiave,valore_valido", [
    ("n_workers", 4),
    ("use_parallel", False),
    ("livello", "esperto"),
    ("help_font_scale", 1.25),
    ("window_geometry", "1600x900+10+10"),
    ("window_geometry", "1280x800"),
    ("decomp_mode", "T"),
])
def test_config_accetta_i_valori_validi(tmp_path, monkeypatch, chiave,
                                        valore_valido):
    from gioco27.core import config as C
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({chiave: valore_valido}), encoding="utf-8")
    monkeypatch.setattr(C, "_CONFIG_FILE", cfg_file)
    monkeypatch.setattr(C, "_CONFIG_DIR", tmp_path)
    assert C.Config().get(chiave) == valore_valido


def test_config_sopravvive_a_un_file_non_json(tmp_path, monkeypatch):
    from gioco27.core import config as C
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text("[1, 2, 3]", encoding="utf-8")
    monkeypatch.setattr(C, "_CONFIG_FILE", cfg_file)
    monkeypatch.setattr(C, "_CONFIG_DIR", tmp_path)
    c = C.Config()
    assert c.get("livello") == C._DEFAULTS["livello"]


# ─────────────────────── PDF: griglie come Form XObject ───────────────────

def test_gridpainter_produce_un_pdf_valido():
    pytest.importorskip("reportlab")
    import io
    import numpy as np
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A3, landscape
    from gioco27.core.pdfgrid import GridPainter, GridSpec

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=landscape(A3))
    painter = GridPainter(c, [GridSpec("m3", 9.5, 3),
                             GridSpec("m27", 5.2, 27, thick_at=(9, 18))])
    painter.draw("m27", np.eye(27), 20, 800)
    painter.draw("m3", np.eye(3), 20, 400)
    c.showPage()
    c.save()
    data = buf.getvalue()
    assert data.startswith(b"%PDF")
    assert b"/Form" in data, "la griglia deve essere un Form XObject riusabile"


# ───────────────────────── scrittura atomica degli export ──────────────────

def test_atomic_write_non_lascia_file_parziali(tmp_path):
    """
    Un export interrotto non deve lasciare al posto del file buono un PDF o un
    CSV troncato: la destinazione o non esiste, o è completa.
    """
    from gioco27.core.parallel import atomic_write
    dest = tmp_path / "uscita.pdf"

    class Interrotto(Exception):
        pass

    with pytest.raises(Interrotto):
        with atomic_write(dest) as f:
            f.write(b"%PDF-1.4 meta scrittura...")
            raise Interrotto
    assert not dest.exists(), "destinazione creata da una scrittura fallita"
    assert list(tmp_path.iterdir()) == [], "file temporaneo non rimosso"


def test_atomic_write_sostituisce_solo_alla_fine(tmp_path):
    from gioco27.core.parallel import atomic_write
    dest = tmp_path / "uscita.txt"
    dest.write_text("vecchio", encoding="utf-8")
    with atomic_write(dest, "w", encoding="utf-8") as f:
        f.write("nuovo")
        # finché il blocco non si chiude, la destinazione ha ancora il vecchio
        assert dest.read_text(encoding="utf-8") == "vecchio"
    assert dest.read_text(encoding="utf-8") == "nuovo"
    assert [p.name for p in tmp_path.iterdir()] == ["uscita.txt"]


def test_export_csv_interrotto_non_sovrascrive(tmp_path, monkeypatch):
    """Se la generazione fallisce a metà, il CSV precedente resta intatto."""
    from gioco27.core import permutations as P
    dest = tmp_path / "dati.csv"
    dest.write_text("precedente", encoding="utf-8")

    def esplode(*a, **k):
        raise RuntimeError("errore simulato")

    monkeypatch.setattr(P, "make_csv_row", esplode)
    base = {"p0": "SCD_U", "p1": "SCD_U", "p2": "SCD_U",
            "j0": "I_3", "j1": "I_3", "j2": "I_3"}
    with pytest.raises(RuntimeError):
        P.write_csv(str(dest), [dict(base), dict(base), dict(base)])
    assert dest.read_text(encoding="utf-8") == "precedente"


# ──────────────────── deduplicazione delle risorse nei PDF ─────────────────

def test_deduplica_non_solleva_mai(tmp_path):
    """
    `deduplica` è un'ottimizzazione: su un file illeggibile deve arrendersi in
    silenzio, non far fallire un export già riuscito.
    """
    from gioco27.core.pdfmerge import deduplica
    finto = tmp_path / "non_un_pdf.pdf"
    finto.write_bytes(b"questo non e' un PDF")
    assert deduplica(str(finto)) is None
    assert finto.read_bytes() == b"questo non e' un PDF", \
        "un file non deduplicabile non va toccato"


def test_pdf_parallelo_non_duplica_i_font(tmp_path):
    """
    Ogni processo figlio incorpora la propria copia dei font: unendo N blocchi
    si ottenevano N copie identiche dello stesso programma font, e il file
    pesava il 50% in più del sequenziale.
    """
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    pikepdf = pytest.importorskip("pikepdf")
    from gioco27.core.combinations import generate_pdf_ex_parallel

    filtri = [{'p0': 'SCD_U', 'p1': 'SCD_U', 'p2': ANY,
               'j0': 'I_3', 'j1': 'I_3', 'j2': 'I_3'} for _ in range(3)]
    out = tmp_path / "par.pdf"
    generate_pdf_ex_parallel(str(out), filtri, n_workers=2)
    assert out.exists()

    pdf = pikepdf.open(str(out))
    programmi = set()
    for pagina in pdf.pages:
        for font in pagina.get("/Resources", {}).get("/Font", {}).values():
            df = font.get("/DescendantFonts")
            desc = df[0].get("/FontDescriptor") if df else font.get("/FontDescriptor")
            if desc is None:
                continue
            for chiave in ("/FontFile", "/FontFile2", "/FontFile3"):
                if chiave in desc:
                    programmi.add(desc[chiave].objgen)
    assert len(programmi) <= 2, \
        f"{len(programmi)} copie di font incorporati: deduplicazione non applicata"


# ══════════════════ il limite di 61 worker di Windows ═════════════════════
#
# `ProcessPoolExecutor` su Windows solleva
#     ValueError: max_workers must be <= 61
# (il limite viene da WaitForMultipleObjects, che gestisce 64 handle).
#
# Su una macchina a 128 core il programma chiedeva 127 worker, il pool veniva
# rifiutato, e il blocco `except Exception` faceva ripiegare sul sequenziale
# registrandolo solo nel log: il parallelismo non funzionava per NESSUN
# export, e l'utente vedeva l'1-2% di CPU senza spiegazione.

def test_esiste_un_tetto_su_windows(monkeypatch):
    from gioco27.core import parallel
    monkeypatch.setattr(parallel.sys, "platform", "win32")
    assert parallel.max_workers_piattaforma() == 61


def test_nessun_tetto_altrove(monkeypatch):
    from gioco27.core import parallel
    monkeypatch.setattr(parallel.sys, "platform", "linux")
    assert parallel.max_workers_piattaforma() is None


def test_worker_limitati_al_tetto_di_windows(monkeypatch):
    """Con 128 core su Windows non si devono chiedere 127 worker."""
    from gioco27.core import parallel
    monkeypatch.setattr(parallel.sys, "platform", "win32")
    monkeypatch.setattr(parallel.os, "cpu_count", lambda: 128)
    assert parallel.default_workers(None) == 61
    assert parallel.default_workers(127) == 61
    assert parallel.default_workers(32) == 32, "sotto il tetto non si tocca"


def test_il_piano_rispetta_il_tetto(monkeypatch):
    from gioco27.core import parallel
    monkeypatch.setattr(parallel.sys, "platform", "win32")
    monkeypatch.setattr(parallel.os, "cpu_count", lambda: 128)
    nw, _chunk = parallel.plan_workers(
        46_656, None, cost_per_item=parallel.COSTO_PAGINA_PDF)
    assert nw <= 61, f"{nw} worker: il pool verrebbe rifiutato da Windows"
    assert nw == 61, "sotto il tetto vanno usati tutti i worker possibili"


def test_effective_n_workers_rispetta_il_tetto(monkeypatch, tmp_path):
    """
    Anche il valore mostrato e usato dalla GUI deve essere realistico: e' quello
    che viene passato a ProcessPoolExecutor.
    """
    from gioco27.core import config as C
    from gioco27.core import parallel
    monkeypatch.setattr(parallel.sys, "platform", "win32")
    monkeypatch.setattr(parallel.os, "cpu_count", lambda: 128)
    monkeypatch.setattr(C, "_CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(C, "_CONFIG_DIR", tmp_path)
    cfg = C.Config()
    assert cfg.effective_n_workers == 61
    cfg["n_workers"] = 100
    assert cfg.effective_n_workers == 61


def _identita(task):
    """Worker top-level per il test del pool."""
    start, blocco = task
    return start, list(blocco)


class _FintoPool:
    """
    Esecutore finto e SINCRONO: esegue subito e restituisce future gia' pronte.
    Serve a verificare la logica di ripiego senza avviare processi veri.
    """

    def __init__(self, max_workers=None, **kw):
        self.max_workers = max_workers

    def submit(self, fn, *a, **kw):
        from concurrent.futures import Future
        fut = Future()
        try:
            fut.set_result(fn(*a, **kw))
        except BaseException as e:      # pragma: no cover
            fut.set_exception(e)
        return fut

    def shutdown(self, wait=True, cancel_futures=False):
        """`imap_ordered` chiude il pool esplicitamente per poter annullare
        senza attendere i worker: il finto pool deve offrire la stessa API."""
        self.chiuso = (wait, cancel_futures)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_un_pool_troppo_grande_non_fa_fallire_l_export(monkeypatch):
    """
    Rete di sicurezza: se la piattaforma rifiuta il numero di worker,
    `imap_ordered` riprova col tetto invece di far fallire tutto l'export.

    E' la situazione che rendeva inutile il parallelismo su una macchina a 128
    core: 127 worker richiesti, ValueError, ripiego silenzioso sul sequenziale.
    L'esecutore viene iniettato, cosi' il test non avvia processi veri.
    """
    from gioco27.core import parallel

    TETTO_FINTO = 4
    richiesti = []

    def fabbrica(max_workers=None, **kw):
        richiesti.append(max_workers)
        if max_workers is not None and max_workers > TETTO_FINTO:
            raise ValueError(f"max_workers must be <= {TETTO_FINTO}")
        return _FintoPool(max_workers=max_workers, **kw)

    monkeypatch.setattr(parallel, "max_workers_piattaforma",
                        lambda: TETTO_FINTO)

    compiti = [(i, [i, i + 1]) for i in range(6)]
    risultati = list(parallel.imap_ordered(_identita, iter(compiti),
                                           n_workers=127, max_pending=4,
                                           executor_factory=fabbrica))
    assert risultati == [_identita(t) for t in compiti], "ordine non preservato"
    assert richiesti == [127, TETTO_FINTO], f"tentativi inattesi: {richiesti}"


# ═════════ deduplicazione: sostituire un file ancora aperto (Windows) ══════
#
# `PdfReader(path)` e `pikepdf.open(path)` tengono il file aperto per la
# lettura pigra. Su Windows `os.replace` su una destinazione aperta fallisce
# con «PermissionError: [WinError 5] Accesso negato», e la deduplicazione
# moriva subito dopo aver lavorato per decine di secondi.
#
# Su Linux la stessa sequenza funziona (POSIX consente di rinominare sopra un
# file aperto), quindi il difetto e' invisibile qui: lo si riproduce
# simulando la semantica di Windows su os.replace.

class _ReplaceStileWindows:
    """
    Sostituto di os.replace che rifiuta la sostituzione se la destinazione
    risulta ancora aperta da questo processo — come fa Windows.
    """

    def __init__(self, aperti):
        self.aperti = aperti          # set di path considerati "aperti"
        self.chiamate = []

    def __call__(self, src, dst):
        self.chiamate.append((src, dst))
        if os.path.abspath(dst) in self.aperti:
            raise PermissionError(
                5, "Accesso negato (simulazione Windows)", dst)
        return os.rename(src, dst)


def test_dedup_chiude_il_file_prima_di_sostituirlo(tmp_path, monkeypatch):
    """
    Il file di origine dev'essere chiuso PRIMA della sostituzione: se restasse
    aperto, su Windows l'intera deduplicazione fallirebbe.
    """
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    from gioco27.core import pdfmerge
    from gioco27.core.combinations import generate_pdf_ex

    sorgente = tmp_path / "doc.pdf"
    filtri = [{'p0': 'SCD_U', 'p1': 'SCD_U', 'p2': 'SCD_U',
               'j0': 'I_3', 'j1': 'I_3', 'j2': 'I_3'} for _ in range(3)]
    generate_pdf_ex(str(sorgente), filtri)
    assert sorgente.exists()

    # Simula Windows: il path di destinazione è considerato "aperto" solo se
    # qualcuno lo tiene aperto davvero. Qui lo dichiariamo sempre aperto per i
    # file .parziale, che è la firma del difetto: la vecchia implementazione
    # usava atomic_write sul file appena letto da PdfReader.
    finto = _ReplaceStileWindows(aperti=set())
    monkeypatch.setattr(pdfmerge.os, "replace", finto)

    esito = pdfmerge.deduplica(str(sorgente))
    assert esito in ("pikepdf", "pypdf", None)
    assert sorgente.exists(), "il PDF non deve sparire"
    residui = [p.name for p in tmp_path.iterdir() if p.name != "doc.pdf"]
    assert not residui, f"file temporanei rimasti: {residui}"


def test_dedup_ripulisce_dopo_un_fallimento(tmp_path, monkeypatch):
    """
    Se la sostituzione fallisce (come su Windows col file aperto), il PDF
    originale deve restare intatto e non devono restare file temporanei.
    """
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    from gioco27.core import pdfmerge
    from gioco27.core.combinations import generate_pdf_ex

    sorgente = tmp_path / "doc.pdf"
    filtri = [{'p0': 'SCD_U', 'p1': 'SCD_U', 'p2': 'SCD_U',
               'j0': 'I_3', 'j1': 'I_3', 'j2': 'I_3'} for _ in range(3)]
    generate_pdf_ex(str(sorgente), filtri)
    originale = sorgente.read_bytes()

    def replace_che_fallisce(src, dst):
        raise PermissionError(5, "Accesso negato (simulazione Windows)", dst)

    monkeypatch.setattr(pdfmerge.os, "replace", replace_che_fallisce)
    assert pdfmerge.deduplica(str(sorgente)) is None
    assert sorgente.read_bytes() == originale, "il PDF originale è stato toccato"
    residui = [p.name for p in tmp_path.iterdir() if p.name != "doc.pdf"]
    assert not residui, f"file temporanei rimasti: {residui}"


def test_ripiego_pypdf_salta_i_file_grandi(tmp_path, monkeypatch):
    """
    La compattazione di ripiego costa decine di secondi e non deduplica i font:
    sopra la soglia non va nemmeno tentata (26 s misurati su 13 824 pagine).
    """
    from gioco27.core import pdfmerge
    grande = tmp_path / "grande.pdf"
    grande.write_bytes(b"x" * int(pdfmerge.MAX_MB_RIPIEGO_PYPDF * 1e6 + 1))
    assert pdfmerge._dedup_pypdf(str(grande)) is False
    assert grande.stat().st_size == int(pdfmerge.MAX_MB_RIPIEGO_PYPDF * 1e6 + 1)


def test_dedup_non_tiene_aperto_il_file_di_origine():
    """
    L'invariante che il difetto Windows ha violato, verificata sul sorgente
    con l'AST (una ricerca testuale troverebbe anche i commenti che spiegano
    il difetto).

    Su Linux il test funzionale non può distinguere le due implementazioni,
    perché POSIX consente di rinominare sopra un file aperto: qui si controlla
    direttamente che nessuno apra il percorso di destinazione per poi
    sostituirlo.
    """
    import pathlib
    percorso = (pathlib.Path(__file__).resolve().parent.parent
                / "gioco27" / "core" / "pdfmerge.py")
    albero = ast.parse(percorso.read_text(encoding="utf-8"))

    aperture_sospette = []
    pikepdf_sicuro = False
    for nodo in ast.walk(albero):
        if not isinstance(nodo, ast.Call):
            continue
        nome = getattr(nodo.func, "id", None) or getattr(nodo.func, "attr", None)
        primo = nodo.args[0] if nodo.args else None
        passa_path = isinstance(primo, ast.Name) and primo.id == "path"
        if nome == "PdfReader" and passa_path:
            aperture_sospette.append("PdfReader(path)")
        if nome == "open" and passa_path and getattr(nodo.func, "value", None) is None:
            # open(path, ...) diretto: accettabile solo se usato come context
            # manager per leggere i byte, cosa che il test sotto verifica
            pass
        if nome == "open" and getattr(nodo.func, "attr", None) == "open":
            modulo = getattr(nodo.func.value, "id", "")
            if modulo == "pikepdf" and passa_path:
                pikepdf_sicuro = any(
                    kw.arg == "allow_overwriting_input"
                    and getattr(kw.value, "value", False) is True
                    for kw in nodo.keywords)

    assert not aperture_sospette, (
        f"{aperture_sospette}: tiene aperto il file, os.replace fallirebbe "
        "su Windows con PermissionError [WinError 5]")
    assert pikepdf_sicuro, (
        "pikepdf.open(path) deve usare allow_overwriting_input=True, "
        "altrimenti su Windows la destinazione resta bloccata")
