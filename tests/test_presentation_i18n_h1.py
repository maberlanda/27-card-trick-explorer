"""Compartimento H1 — correttezza della presentation e localizzazione.

Come in C, E, F e G, questo file nasce **prima** delle correzioni: descrive il
comportamento attuale e marca con `xfail(strict=True)` i contratti che H1 deve
introdurre, cosi' che ogni commit successivo dimostri di aver cambiato quello
e nient'altro.

Quattro debiti e un principio:

* **M01** — deselezionando tutte le caselle di un livello P o J il filtro non
  diventa vuoto: `FilterFrame.get_filter` sostituisce silenziosamente la prima
  opzione, che e' l'identita'. Il risultato e' corretto e il pannello mostra
  sei caselle spente: il fallback e' invisibile;
* **M05** — `protocol_dialog` scrive un HTML nella cartella temporanea di
  sistema e lo apre nel browser. Il file non viene mai rimosso e non esiste
  nessuna policy: ogni apertura ne lascia uno in piu';
* **M06** — l'elenco delle trasposte del PDF dettagliato, quando supera il
  massimo visualizzato, chiude con un «altre» italiano anche in inglese;
* **errori applicativi** — D, E, F e G hanno lasciato di proposito messaggi
  neutri nel core. Nessuno li traduce, quindi in modalita' inglese l'utente
  legge testo tecnico italiano.

Il principio che H1 non deve violare: il core dice **che cosa e' successo**, la
presentation decide **come dirlo**. Nessuna traduzione scende in
`core/dominio`, `core/analisi`, `core/combinations` o nei servizi.

Nessun test apre un browser vero, nessuno dipende dai permessi del filesystem
o da `/tmp`: `webbrowser.open` e' iniettato e le cartelle temporanee sono
quelle di pytest.
"""
import ast
import pathlib
import re

import pytest

from gioco27 import i18n as catalogo
from gioco27.core.constants import ANY, J_OPTS, P_OPTS

RADICE = pathlib.Path(__file__).resolve().parents[1]
PACCHETTO = RADICE / "gioco27"


# ════════════════════════════ armamentario ══════════════════════════════════

@pytest.fixture
def lingua():
    """Permette di cambiare lingua senza lasciarla cambiata agli altri test."""
    precedente = catalogo.get_language()
    yield catalogo.set_language
    catalogo.set_language(precedente)


def _radice_tk():
    tk = pytest.importorskip("tkinter")
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    root.withdraw()
    return root


@pytest.fixture
def pannello():
    """Un `FilterFrame` vero, con i suoi widget, senza mostrare la finestra."""
    from gioco27.gui.filter_frame import FilterFrame

    root = _radice_tk()
    try:
        yield FilterFrame(root, stage_num=0)
    finally:
        root.destroy()


def _selezionate(pannello, nome):
    return {opt for opt, bv in pannello._vars[nome][1] if bv.get()}


def _attese_dal_filtro(valore, opzioni):
    """L'insieme di valori che il filtro prodotto descrive davvero."""
    if valore == ANY:
        return set(opzioni)
    if isinstance(valore, str):
        return {valore}
    return set(valore)


# ═══════════════════ M01 — la selezione vuota dei filtri ════════════════════

def test_m01_tutte_le_caselle_danno_il_dominio_intero(pannello):
    assert pannello.get_filter()["p0"] == ANY
    assert _selezionate(pannello, "P0") == set(P_OPTS)


def test_m01_una_sola_casella(pannello):
    _, caselle = pannello._vars["P0"]
    for opt, bv in caselle:
        bv.set(opt == "CDS_U")
    assert pannello.get_filter()["p0"] == "CDS_U"


def test_m01_piu_caselle(pannello):
    _, caselle = pannello._vars["P0"]
    scelte = {"SCD_U", "CDS_U", "DSC_U"}
    for opt, bv in caselle:
        bv.set(opt in scelte)
    assert set(pannello.get_filter()["p0"]) == scelte


@pytest.mark.parametrize("livello,opzioni", [("P0", P_OPTS), ("J0", J_OPTS)])
def test_m01_il_fallback_e_la_prima_opzione(pannello, livello, opzioni):
    """La semantica storica, fissata prima di renderla visibile.

    Non e' un difetto matematico: il filtro prodotto e' quello dell'identita',
    ed e' esattamente il comportamento che H1 deve **conservare**.
    """
    _, caselle = pannello._vars[livello][0], pannello._vars[livello][1]
    for _, bv in caselle:
        bv.set(False)
    prodotto = pannello.get_filter()[livello.lower()]
    assert prodotto == opzioni[0]
    assert opzioni[0] in ("SCD_U", "I_3"), "la prima opzione e' l'identita'"


@pytest.mark.parametrize("livello,opzioni", [("P0", P_OPTS), ("J0", J_OPTS)])
def test_m01_la_ui_mostra_cio_che_il_filtro_usa(pannello, livello, opzioni):
    """Quello che si vede e quello che si ottiene devono coincidere."""
    for _, bv in pannello._vars[livello][1]:
        bv.set(False)
    prodotto = pannello.get_filter()[livello.lower()]
    assert _selezionate(pannello, livello) == _attese_dal_filtro(prodotto,
                                                                opzioni)


@pytest.mark.parametrize("livello,opzioni", [("P0", P_OPTS), ("J0", J_OPTS)])
def test_m01_togliendo_l_ultima_casella_la_prima_si_riaccende(pannello, livello,
                                                              opzioni):
    """La sostituzione avviene sotto gli occhi di chi guarda, non nel codice."""
    for _, bv in pannello._vars[livello][1]:
        bv.set(False)
    assert _selezionate(pannello, livello) == {opzioni[0]}


def test_m01_il_click_reale_non_svuota_il_livello(pannello):
    """Non e' un effetto della scrittura diretta della variabile: si prova
    invocando i Checkbutton veri, uno per uno, come farebbe l'utente."""
    for casella in pannello._caselle["J0"]:
        casella.invoke()
    assert _selezionate(pannello, "J0") == {J_OPTS[0]}
    assert pannello.get_filter()["j0"] == J_OPTS[0]


def test_m01_il_riallineamento_notifica_una_volta_sola():
    """`on_change` non deve partire due volte per un solo click."""
    from gioco27.gui.filter_frame import FilterFrame

    root = _radice_tk()
    try:
        conteggio = []
        ff = FilterFrame(root, stage_num=0,
                         on_change=lambda: conteggio.append(1))
        for _, bv in ff._vars["J0"][1]:
            bv.set(False)
        # due scritture (J0 spenta due volte) piu' il riallineamento, che non
        # deve produrre una notifica propria.
        assert len(conteggio) == 2
        assert _selezionate(ff, "J0") == {J_OPTS[0]}
    finally:
        root.destroy()


def test_m01_la_regola_e_scritta_nell_interfaccia(lingua):
    """Il perche' si legge nel pannello, localizzato, non solo nel codice."""
    for codice, atteso in (("it", "identità"), ("en", "identity")):
        lingua(codice)
        testo = catalogo.tr("filter.never_empty", option="SCD_U")
        assert "SCD_U" in testo and atteso in testo


def test_m01_il_reset_riaccende_tutto(pannello):
    for _, bv in pannello._vars["P0"][1]:
        bv.set(False)
    pannello.reset()
    assert _selezionate(pannello, "P0") == set(P_OPTS)
    assert pannello.get_filter()["p0"] == ANY
    assert pannello.get_filter()["j_uniform"] is False


def test_m01_il_preset_gioco_reale_resta_quello(pannello):
    pannello.set_preset_gioco_reale()
    filtro = pannello.get_filter()
    assert filtro["p0"] == "SCD_U" and filtro["p1"] == "SCD_U"
    assert filtro["p2"] == ANY and filtro["j_uniform"] is True
    assert _selezionate(pannello, "P2") == set(P_OPTS)


def test_m01_la_scelta_fissa_ha_la_precedenza(pannello):
    """Il menu «Fissa» vince sulle caselle: e' il contratto storico."""
    dvar, caselle = pannello._vars["P0"]
    dvar.set("DCS_U")
    for _, bv in caselle:
        bv.set(False)
    assert pannello.get_filter()["p0"] == "DCS_U"


# ═════════════════ M05 — il temporaneo del protocollo ═══════════════════════

@pytest.fixture
def protocollo(monkeypatch, tmp_path):
    """Il dialogo reale, con cartella temporanea isolata e browser finto."""
    import tempfile

    from gioco27.gui import protocol_dialog

    aperti = []
    monkeypatch.setattr(protocol_dialog.webbrowser, "open",
                        lambda uri: aperti.append(uri) or True)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(protocol_dialog, "generate_protocol_html",
                        lambda dati, opzioni: "<html><body>ciao</body></html>")
    return protocol_dialog, aperti


class _DialogoProtocollo:
    """`_open_browser` reale, senza widget."""

    def __init__(self, modulo):
        from gioco27.gui import protocol_dialog

        self._open_browser = protocol_dialog.ProtocolDialog._open_browser.__get__(
            self, type(self))
        self._vars = {}
        self._T_data = {"perm": list(range(27))}
        self.distrutto = 0

    def destroy(self):
        self.distrutto += 1


def _apri(protocollo):
    modulo, aperti = protocollo
    _DialogoProtocollo(modulo)._open_browser()
    return aperti


def test_m05_l_apertura_produce_un_file_e_un_uri(protocollo, tmp_path):
    aperti = _apri(protocollo)
    assert len(aperti) == 1 and aperti[0].startswith("file://")
    prodotti = list(tmp_path.rglob("*.html"))
    assert len(prodotti) == 1
    assert prodotti[0].read_text(encoding="utf-8").startswith("<html>")


def test_m05_il_file_sopravvive_all_apertura(protocollo, tmp_path):
    """Il browser puo' ancora averne bisogno: non va cancellato subito."""
    _apri(protocollo)
    assert list(tmp_path.rglob("*.html")), "il file e' sparito sotto il browser"


def test_m05_due_aperture_non_si_sovrascrivono(protocollo, tmp_path):
    aperti = _apri(protocollo)
    _apri(protocollo)
    assert len(aperti) == 2 and aperti[0] != aperti[1]
    assert len(list(tmp_path.rglob("*.html"))) == 2


def _invecchia(percorso, ore):
    import os
    import time

    quando = time.time() - ore * 3600
    os.utime(percorso, (quando, quando))


def test_m05_i_file_vecchi_vengono_ripuliti(protocollo, tmp_path):
    """Una apertura smaltisce i propri file di ieri."""
    _apri(protocollo)
    vecchio = list(tmp_path.rglob("*.html"))[0]
    _invecchia(vecchio, 48)

    _apri(protocollo)
    rimasti = list(tmp_path.rglob("*.html"))
    assert vecchio not in rimasti, "il file di due giorni fa e' ancora li'"
    assert len(rimasti) == 1


def test_m05_i_file_recenti_restano(protocollo, tmp_path):
    """Il browser puo' ancora tenere aperto il documento di poco fa."""
    _apri(protocollo)
    recente = list(tmp_path.rglob("*.html"))[0]
    _invecchia(recente, 2)
    _apri(protocollo)
    assert recente.exists()
    assert len(list(tmp_path.rglob("*.html"))) == 2


def test_m05_il_file_appena_creato_non_e_mai_un_candidato(protocollo,
                                                          tmp_path):
    """La pulizia avviene prima della scrittura, non dopo."""
    modulo, _ = protocollo
    for _ in range(3):
        _apri(protocollo)
    assert len(list(tmp_path.rglob("*.html"))) == 3
    assert modulo.pulisci_protocolli_vecchi(ore=0) == 3
    assert list(tmp_path.rglob("*.html")) == []


def test_m05_un_file_estraneo_non_viene_toccato(protocollo, tmp_path):
    """Mai cancellare file arbitrari: solo quelli che sappiamo di aver scritto."""
    modulo, _ = protocollo
    _apri(protocollo)
    cartella = modulo.cartella_protocolli()
    estraneo = cartella / "appunti-di-qualcun-altro.html"
    estraneo.write_text("non e' mio", encoding="utf-8")
    anche_questo = cartella / "protocollo-ma-non-html.txt"
    anche_questo.write_text("nemmeno questo", encoding="utf-8")
    for p in (estraneo, anche_questo):
        _invecchia(p, 72)

    assert modulo.pulisci_protocolli_vecchi(ore=0) == 1
    assert estraneo.exists() and anche_questo.exists()
    assert not modulo.e_un_protocollo(estraneo)
    assert not modulo.e_un_protocollo(anche_questo)


def test_m05_i_protocolli_stanno_in_una_cartella_propria(protocollo, tmp_path):
    """Il cleanup non deve nemmeno affacciarsi sulla temp di sistema."""
    modulo, _ = protocollo
    _apri(protocollo)
    cartella = modulo.cartella_protocolli()
    assert cartella.parent == tmp_path
    assert cartella.name == modulo.CARTELLA_PROTOCOLLI
    assert [p.parent for p in tmp_path.rglob("*.html")] == [cartella]


def test_m05_la_pulizia_non_impedisce_l_apertura(protocollo, monkeypatch,
                                                 tmp_path):
    """Non riuscire a fare pulizia non e' un motivo per non aprire il documento."""
    modulo, aperti = protocollo
    monkeypatch.setattr(modulo, "pulisci_protocolli_vecchi",
                        lambda *a, **k: (_ for _ in ()).throw(
                            OSError("cartella occupata")))
    _DialogoProtocollo(modulo)._open_browser()
    assert len(aperti) == 1
    assert len(list(tmp_path.rglob("*.html"))) == 1


def test_m05_l_uri_indica_davvero_il_file(protocollo, tmp_path):
    aperti = _apri(protocollo)
    prodotto = list(tmp_path.rglob("*.html"))[0]
    assert aperti[0] == prodotto.resolve().as_uri()


@pytest.mark.parametrize("cartella", [
    "con spazio", "accentata città", "con#cancelletto", "mista à b#c"])
def test_m05_uri_con_spazi_accenti_e_cancelletto(monkeypatch, tmp_path,
                                                 protocollo, cartella):
    """H1-G5: l'URI deve riportare al file, non a un pezzo di esso.

    Un `#` non quotato taglia l'URI in due e il browser apre una pagina
    inesistente; uno spazio o un accento non quotati fanno lo stesso.
    """
    import tempfile
    import urllib.parse
    import urllib.request

    base = tmp_path / cartella
    base.mkdir()
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(base))

    aperti = _apri(protocollo)
    assert len(aperti) == 1
    for carattere in (" ", "#"):
        assert carattere not in urllib.parse.urlparse(aperti[0]).path

    percorso = urllib.request.url2pathname(
        urllib.parse.urlparse(aperti[0]).path)
    assert pathlib.Path(percorso).read_text(encoding="utf-8").startswith("<html>")


def test_m05_apre_il_browser_come_le_altre_rotte():
    """Le altre rotte HTML costruiscono l'URI con `resolve().as_uri()`.

    Su una cartella temporanea raggiunta da un link simbolico — `/tmp` su
    macOS — la differenza si vede; il test guarda la forma perche' creare
    link simbolici non e' portabile.
    """
    sorgente = (PACCHETTO / "gui" / "protocol_dialog.py").read_text(
        encoding="utf-8")
    assert "resolve().as_uri()" in sorgente


def test_m05_il_fallimento_del_browser_viene_riportato(protocollo,
                                                       monkeypatch):
    modulo, _ = protocollo
    mostrati = []
    monkeypatch.setattr(modulo.webbrowser, "open",
                        lambda uri: (_ for _ in ()).throw(
                            RuntimeError("nessun browser")))
    monkeypatch.setattr(modulo, "messagebox", pytest.importorskip(
        "types").SimpleNamespace(
            showerror=lambda *a, **k: mostrati.append(a)))
    _DialogoProtocollo(modulo)._open_browser()
    assert len(mostrati) == 1


# ══════════════════ M06 — il testo dinamico del PDF dettagliato ═════════════

MASSIMO_TRASPOSTE = 20 * 3      # ROWS * N_COLS in render_detail_pages


def _testo_pdf_dettagliato(percorso, n_trasposte):
    """Genera una pagina del PDF dettagliato e ne estrae il testo."""
    pytest.importorskip("reportlab")
    pypdf = pytest.importorskip("pypdf")

    from gioco27.core.detail_pdf import _new_detail_canvas, render_detail_pages

    params = [("SCD_U", "SCD_U", "SCD_U", "I_3", "I_3", "I_3")] * 3
    c, painter = _new_detail_canvas(str(percorso))
    render_detail_pages(
        c, [params], start_index=1, painter=painter,
        labels=["D#0"],
        transposes=[[f"E#{i}" for i in range(n_trasposte)]])
    c.save()
    lettore = pypdf.PdfReader(str(percorso))
    return "\n".join(p.extract_text() or "" for p in lettore.pages)


def test_m06_sotto_il_limite_non_compare_nessuna_coda(tmp_path, lingua):
    lingua("it")
    testo = _testo_pdf_dettagliato(tmp_path / "sotto.pdf",
                                   MASSIMO_TRASPOSTE - 5)
    assert "E#0" in testo
    assert "altre" not in testo and "more" not in testo


def test_m06_sopra_il_limite_la_coda_compare_in_italiano(tmp_path, lingua):
    lingua("it")
    testo = _testo_pdf_dettagliato(tmp_path / "sopra.pdf",
                                   MASSIMO_TRASPOSTE + 7)
    assert "+7" in testo and "altre" in testo


@pytest.mark.xfail(strict=True,
                   reason="M06: «altre» e' scritto a mano nel PDF e resta "
                          "italiano anche in inglese")
def test_m06_in_inglese_non_compare_altre(tmp_path, lingua):
    lingua("en")
    testo = _testo_pdf_dettagliato(tmp_path / "sopra_en.pdf",
                                   MASSIMO_TRASPOSTE + 7)
    assert "+7" in testo
    assert "altre" not in testo, "testo italiano nell'output inglese"


def test_m06_le_etichette_matematiche_non_si_traducono(tmp_path, lingua):
    """Le sigle e le etichette delle trasposte restano quelle, in ogni lingua."""
    lingua("en")
    testo = _testo_pdf_dettagliato(tmp_path / "sigle.pdf", 5)
    assert "E#0" in testo and "E#4" in testo


# ═══════════════ errori applicativi: neutri nel core, tradotti sopra ════════

def _messaggi_errore_del_core():
    """Le eccezioni applicative che la GUI mostra all'utente."""
    from gioco27.core.analisi import SchemaNonRiconosciuto, riconosci_schema
    from gioco27.core.combinations import FiltroNonValido, normalizza_filtri
    from gioco27.core.dominio import PermutazioneNonValida, valida_permutazione

    casi = []
    try:
        riconosci_schema(["foo", "bar"])
    except SchemaNonRiconosciuto as exc:
        casi.append(("schema", exc))
    try:
        normalizza_filtri([{"p0": "SCD_U"}] * 3)
    except FiltroNonValido as exc:
        casi.append(("filtro", exc))
    try:
        valida_permutazione([0, 0, 2], 3, nome="T")
    except PermutazioneNonValida as exc:
        casi.append(("permutazione", exc))
    return casi


def test_il_core_resta_neutro_e_in_una_lingua_sola(lingua):
    """Il messaggio del core non cambia con la lingua: e' un fatto, non un testo.

    E' il contratto lasciato da D/E/F e G, e H1 non deve toccarlo: cambia
    soltanto chi lo mostra.
    """
    lingua("it")
    italiano = {n: str(e) for n, e in _messaggi_errore_del_core()}
    lingua("en")
    inglese = {n: str(e) for n, e in _messaggi_errore_del_core()}
    assert italiano == inglese and italiano


@pytest.mark.xfail(strict=True,
                   reason="gli errori applicativi arrivano all'utente come "
                          "str(exc), cioe' in italiano anche in inglese")
def test_gli_errori_applicativi_sono_localizzati(lingua):
    """In inglese l'utente non deve leggere il messaggio tecnico italiano."""
    from gioco27.gui import errori

    lingua("en")
    for nome, exc in _messaggi_errore_del_core():
        titolo, messaggio = errori.per_utente(exc)
        assert titolo and messaggio, nome
        assert messaggio != str(exc), nome
        assert not re.search(r"\b(stadio|attesi|valore|sconosciut|manca)",
                             messaggio), (nome, messaggio)


@pytest.mark.xfail(strict=True,
                   reason="la diagnostica dell'import e' composta nel core, "
                          "in italiano")
def test_la_diagnostica_dell_import_e_localizzata(lingua):
    from gioco27.core.analisi import RigaScartata, RisultatiImport
    from gioco27.gui import errori

    esito = RisultatiImport([], lette=4, scartate=(
        RigaScartata(2, "T_permutazione", "valore 99 fuori dall'intervallo"),
        RigaScartata(4, "T_permutazione", "campo vuoto")))

    lingua("en")
    testo = errori.diagnostica_import(esito)
    assert "4" in testo and "2" in testo
    assert "righe" not in testo and "scartate" not in testo


def test_la_presentation_non_entra_nel_core():
    """H1-G9: nessun modulo di core o services importa la i18n della GUI."""
    for percorso in sorted(PACCHETTO.rglob("*.py")):
        rel = percorso.relative_to(RADICE).as_posix()
        if not (rel.startswith("gioco27/core/")
                or rel.startswith("gioco27/services/")):
            continue
        sorgente = percorso.read_text(encoding="utf-8")
        for n in ast.walk(ast.parse(sorgente)):
            if isinstance(n, ast.ImportFrom) and n.module:
                assert "gui" not in n.module.split("."), (rel, n.module)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    assert not a.name.startswith("gioco27.gui"), (rel, a.name)


# ═══════════════ navigazione: identificatori, non testo tradotto ════════════

def test_le_schede_hanno_chiavi_stabili():
    """Le etichette sono tradotte: cercarle per testo e' fragile."""
    it = catalogo.CATALOGS["it"]
    en = catalogo.CATALOGS["en"]
    for chiave in ("tab.guide", "tab.simulator", "tab.preview", "tab.explorer"):
        assert chiave in it and chiave in en


@pytest.mark.xfail(strict=True,
                   reason="la selezione delle schede passa ancora dal titolo "
                          "tradotto")
def test_la_selezione_delle_schede_non_passa_dal_titolo():
    sorgenti = {
        "app": (PACCHETTO / "gui" / "app.py").read_text(encoding="utf-8"),
        "explorer": (PACCHETTO / "gui" / "explorer_tab.py").read_text(
            encoding="utf-8"),
    }
    assert 'w.tab(tab, "text")' not in sorgenti["explorer"]
    assert 'nb.tab(tab, "text")' not in sorgenti["app"]


# ════════════════════════════ catalogo IT/EN ════════════════════════════════

def test_i_cataloghi_restano_simmetrici():
    it, en = catalogo.CATALOGS["it"], catalogo.CATALOGS["en"]
    assert set(it) == set(en)
    segnaposti = lambda s: set(re.findall(r"\{(\w+)", s))
    discordanti = [k for k in it if segnaposti(it[k]) != segnaposti(en[k])]
    assert discordanti == [], discordanti


def test_i_dati_stabili_non_sono_tradotti(lingua):
    """H1-G11: la lingua dell'interfaccia non cambia il formato dei dati."""
    from gioco27.core.analisi import SCHEMA_COMBINAZIONI
    from gioco27.core.constants import J_OPTS as J, P_OPTS as P
    from gioco27.core.permutations import CSV_HEADER

    lingua("it")
    intestazione_it = list(CSV_HEADER)
    sigle_it = (list(P), list(J), list(SCHEMA_COMBINAZIONI.obbligatorie))
    lingua("en")
    assert list(CSV_HEADER) == intestazione_it
    assert (list(P), list(J), list(SCHEMA_COMBINAZIONI.obbligatorie)) == sigle_it
    assert CSV_HEADER[0] == "#" and "T_permutazione" in CSV_HEADER[8]
