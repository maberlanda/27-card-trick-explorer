"""
La Guida deve restare allineata al programma.

La documentazione integrata (`gui/guide.py`) è lunga oltre mille righe e
descrive schede, sotto-tab, pulsanti, limiti e dipendenze. Nulla impediva che
divergesse dal codice, ed è successo: elencava sei sotto-tab dell'Explorer
quando erano sette, descriveva la scheda Distribuzione con contenuti che non ha
mai avuto, dichiarava Python 3.8 mentre il pacchetto ne richiede 3.9, e il piè
di pagina era fermo alla v2.7.2.

Questi test leggono il SORGENTE della Guida e lo confrontano con il programma
vero, così una divergenza diventa un test rosso invece di una nota sbagliata
letta dall'utente.
"""
import ast
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GUIDE = ROOT / "gioco27" / "gui" / "guide.py"
APP = ROOT / "gioco27" / "gui" / "app.py"


def _norm(t):
    """Normalizza gli spazi: la Guida usa spaziature diverse per estetica."""
    return re.sub(r"\s+", " ", t).strip()


@pytest.fixture(scope="module")
def guida():
    return GUIDE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def guida_norm(guida):
    return _norm(guida)


@pytest.fixture(scope="module")
def app_src():
    return APP.read_text(encoding="utf-8")


# ───────────────────────────── indice e sezioni ────────────────────────────

def _voci_indice(guida):
    """[(numero, titolo)] dall'elenco `toc` della Guida."""
    blocco = guida.split("toc = [", 1)[1].split("]", 1)[0]
    return [(int(n), t) for n, t in re.findall(r'\("(\d+)",\s*"([^"]*)"\)', blocco)]


def _intestazioni(guida):
    """[(numero, titolo)] dalle intestazioni h2."""
    out = []
    for n, resto in re.findall(r'ins\("h2", "(\d+)\.\s+([^"\\]*)', guida):
        out.append((int(n), resto.strip()))
    return out


def test_indice_e_intestazioni_coincidono(guida):
    """Ogni voce dell'indice deve avere la sua sezione, e viceversa."""
    toc = _voci_indice(guida)
    heads = _intestazioni(guida)
    assert [n for n, _ in toc] == [n for n, _ in heads], (
        "numeri di sezione disallineati fra indice e intestazioni")
    for (n1, t1), (n2, t2) in zip(toc, heads):
        assert _norm(t1) == _norm(t2), \
            f"sezione {n1}: indice «{t1}» ≠ intestazione «{t2}»"


def test_sezioni_numerate_senza_buchi(guida):
    numeri = [n for n, _ in _intestazioni(guida)]
    assert numeri == list(range(1, len(numeri) + 1)), \
        f"numerazione non consecutiva: {numeri}"


def test_riferimenti_incrociati_puntano_a_sezioni_esistenti(guida):
    """«vedi sezione N» deve riferirsi a una sezione che esiste davvero."""
    esistenti = {n for n, _ in _intestazioni(guida)}
    for n in re.findall(r'\bsezion[ei]\s+(\d+)\b', guida):
        assert int(n) in esistenti, f"riferimento a una sezione inesistente: {n}"


def test_banner_puntano_a_sezioni_esistenti(guida, app_src):
    """
    I `section=` passati ai banner d'aiuto devono esistere nella Guida:
    altrimenti «Apri Guida» non porta da nessuna parte.
    """
    esistenti = {str(n) for n, _ in _intestazioni(guida)}
    usate = set(re.findall(r'section="(\d+)"', app_src))
    usate |= {m for m in re.findall(r'_wrap_tab\([^)]*?,\s*"(\d+)"\)', app_src)}
    assert usate, "nessun riferimento di sezione trovato in app.py"
    assert usate <= esistenti, f"sezioni citate ma inesistenti: {usate - esistenti}"


def test_ogni_scheda_ha_un_riferimento_alla_guida(app_src):
    """
    Ogni scheda costruita con _wrap_tab deve indicare la sua sezione: passare
    None lasciava il link «Apri Guida» del banner senza destinazione.
    """
    senza = re.findall(r'_wrap_tab\(self\._build_(\w+)_tab,\s*"\w+",\s*None\)',
                       app_src)
    assert not senza, f"schede senza sezione di Guida: {senza}"


def test_open_guide_usa_davvero_il_parametro_section(app_src):
    """
    `_open_guide(section)` accettava il parametro e lo ignorava: ogni link
    apriva la Guida in cima.
    """
    corpo = app_src.split("def _open_guide(", 1)[1].split("\n    def ", 1)[0]
    assert "_guide_marks" in corpo, \
        "_open_guide non usa le ancore di sezione"


# ──────────────────────── coerenza con il programma ────────────────────────

def test_versione_nel_pie_di_pagina_e_quella_reale(guida):
    """Il piè di pagina citava «v2.7.2» con il programma alla 3.x."""
    assert "__version__ as _ver" in guida, \
        "la versione nel piè di pagina dev'essere presa da gioco27.__version__"
    assert not re.search(r"gioco27 v\d+\.\d+\.\d+", guida), \
        "versione scritta a mano nel testo della Guida"


def test_versione_minima_di_python_coerente_con_pyproject(guida):
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'requires-python\s*=\s*">=(\d+\.\d+)"', pyproject)
    assert m, "requires-python non trovato in pyproject.toml"
    attesa = m.group(1)
    assert f"Python {attesa} o superiore" in guida, \
        f"la Guida non dichiara Python {attesa} (valore di pyproject.toml)"
    assert not re.search(r"Python\s+3\.8\s+o superiore", guida), \
        "la Guida conserva anche il vecchio requisito Python 3.8"


def test_requisito_python_rifiuta_formulazioni_contraddittorie(guida):
    with pytest.raises(AssertionError, match="vecchio requisito"):
        test_versione_minima_di_python_coerente_con_pyproject(
            guida + "\nPython 3.8 o superiore")


def test_numero_di_sottotab_explorer(guida):
    """La Guida diceva «sei sotto-tab» quando erano sette."""
    src = (ROOT / "gioco27" / "gui" / "explorer_tab.py").read_text(encoding="utf-8")
    n = len(re.findall(r'nb\.add\(', src))
    parole = {6: "sei", 7: "sette", 8: "otto", 5: "cinque"}
    assert n in parole, f"numero inatteso di sotto-tab: {n}"
    assert f"I {parole[n]} sotto-tab" in guida, \
        f"l'Explorer ha {n} sotto-tab: la Guida deve dire «I {parole[n]} sotto-tab»"
    assert f"i {parole[n]} sotto-tab" in guida, \
        f"anche il flusso di lavoro deve citare {parole[n]} sotto-tab"


def _verifica_assenza_vecchio_numero_sottotab(guida):
    assert not re.search(r"\bsei\s+sotto-tab\b", guida, re.IGNORECASE), \
        "la Guida conserva sei sotto-tab insieme ai sette effettivi"


def test_explorer_non_conserva_il_numero_obsoleto(guida):
    _verifica_assenza_vecchio_numero_sottotab(guida)


def test_controllo_sottotab_rifiuta_formulazioni_contraddittorie():
    corretto = "I sette sotto-tab. Naviga i sette sotto-tab."
    _verifica_assenza_vecchio_numero_sottotab(corretto)
    with pytest.raises(AssertionError, match="sei sotto-tab"):
        _verifica_assenza_vecchio_numero_sottotab(corretto + " Organizzato in sei sotto-tab.")


def _etichette_tab(path):
    """Etichette dei tab (`text="..."` in nb.add) di un modulo GUI."""
    src = pathlib.Path(path).read_text(encoding="utf-8")
    out = []
    for m in re.findall(r'nb\.add\([^,]+,\s*text=("(?:[^"\\]|\\.)*")', src):
        out.append(ast.literal_eval(m).strip())
    return out


def test_nomi_dei_sottotab_explorer_citati_nella_guida(guida_norm):
    """
    Ogni sotto-tab dell'Explorer dev'essere nominato nella Guida con la sua
    etichetta reale: «📝 Traccia» non esiste, l'etichetta è
    «✏️ Traccia riscrittura».
    """
    mancanti = [e for e in _etichette_tab(ROOT / "gioco27" / "gui" / "explorer_tab.py")
                if _norm(e) not in guida_norm]
    assert not mancanti, f"sotto-tab non documentati con l'etichetta reale: {mancanti}"
    assert _norm("📝 Traccia") not in guida_norm, \
        "la Guida conserva anche l'etichetta obsoleta della Traccia"


def test_nomi_sottotab_rifiutano_anche_etichetta_obsoleta(guida_norm):
    with pytest.raises(AssertionError, match="etichetta obsoleta"):
        test_nomi_dei_sottotab_explorer_citati_nella_guida(guida_norm + " 📝 Traccia")


def test_sottotab_di_cicli_e_distribuzione_documentati(guida_norm):
    for modulo in ("cycles_tab.py", "distribution_tab.py"):
        for etichetta in _etichette_tab(ROOT / "gioco27" / "gui" / modulo):
            assert _norm(etichetta) in guida_norm, \
                f"{modulo}: sotto-tab «{etichetta}» non documentato nella Guida"


def test_limiti_export_citati_correttamente(guida):
    """I numeri dei limiti nella Guida devono essere quelli del codice."""
    from gioco27.core.parallel import MAX_EXPORT_ITEMS
    from gioco27.core.detail_pdf import MAX_DETAIL_COMBOS

    def formato(n):
        return f"{n:,}".replace(",", " ")

    assert formato(MAX_EXPORT_ITEMS) in guida, \
        f"la Guida non cita il limite reale {formato(MAX_EXPORT_ITEMS)}"
    assert formato(MAX_DETAIL_COMBOS) in guida, \
        f"la Guida non cita il limite reale {formato(MAX_DETAIL_COMBOS)}"


def test_totale_combinazioni_citato_correttamente(guida):
    from gioco27.core.combinations import count_combinations_ex
    from gioco27.core.constants import ANY
    filtri = [{k: ANY for k in ("p0", "p1", "p2", "j0", "j1", "j2")}
              for _ in range(3)]
    totale = count_combinations_ex(filtri)
    assert f"{totale:,}".replace(",", " ") in guida, \
        "la Guida non cita il numero reale di combinazioni senza filtri"


def test_dipendenze_citate_sono_quelle_di_controlla_requisiti(guida):
    """L'elenco delle librerie nella Guida deve coincidere con quello reale."""
    src = (ROOT / "controlla_requisiti.py").read_text(encoding="utf-8")
    blocco = src.split("DEPS = [", 1)[1].split("]", 1)[0]
    moduli = re.findall(r'\("(\w+)",', blocco)
    assert moduli, "DEPS non interpretabile"
    for m in moduli:
        assert m in guida, f"dipendenza «{m}» non documentata nella Guida"


def _pulsanti_barra_azioni():
    """
    Etichette di tutti i pulsanti della barra azioni e della barra preset,
    estratte da _build_ui() con l'AST (niente regex sulle emoji).
    """
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_build_ui")
    etichette = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        nome = getattr(f, "attr", None) or getattr(f, "id", None)
        if nome not in ("Button", "Checkbutton", "Menubutton"):
            continue
        for kw in node.keywords:
            if kw.arg == "text" and isinstance(kw.value, ast.Constant):
                etichette.append(kw.value.value)
    return etichette


def test_pulsanti_della_barra_azioni_documentati(guida_norm):
    """
    Ogni pulsante delle barre in alto deve comparire nella Guida.

    Ha trovato tre lacune reali: «↺ Reset tutto» (la Guida parlava solo del
    preset «↺ Reset filtri», che è un altro pulsante), «⬇ Genera…» e
    «✔ Verifica».
    """
    etichette = _pulsanti_barra_azioni()
    assert len(etichette) >= 8, f"pulsanti non individuati: {etichette}"
    mancanti = []
    for e in etichette:
        # si confronta il testo senza icona e senza la parte fra parentesi
        testo = _norm(re.sub(r"^[^\w(]+", "", e).split("(")[0])
        if testo and testo not in guida_norm:
            mancanti.append(e)
    assert not mancanti, f"pulsanti non documentati nella Guida: {mancanti}"


def test_schede_nascoste_in_modalita_principiante(guida, app_src):
    """
    §29 elenca le schede visibili in modalità Principiante: deve corrispondere
    a quello che _apply_livello nasconde davvero.
    """
    assert "_advanced_tabs = [self._tab_explorer, self._tab_cycles,\n" \
           "                               self._tab_distrib]" in app_src, \
        "l'elenco delle schede avanzate è cambiato: aggiornare la Guida (§29)"
    for nome in ("Explorer", "Cicli", "Distribuzione"):
        assert nome in guida


def test_glossario_tab_help_copre_tutte_le_schede(app_src):
    """Ogni chiave TAB_HELP usata da app.py deve esistere nel glossario."""
    from gioco27.gui.glossary import TAB_HELP
    usate = set(re.findall(r'_wrap_tab\(self\._build_\w+_tab,\s*"(\w+)"', app_src))
    usate |= set(re.findall(r'TAB_HELP\["(\w+)"\]', app_src))
    mancanti = usate - set(TAB_HELP)
    assert not mancanti, f"chiavi TAB_HELP mancanti nel glossario: {mancanti}"


def test_azioni_rapide_di_inizia_qui_documentate(guida_norm):
    """
    §29 elencava tre azioni rapide quando erano quattro: mancava
    «Prova il Simulatore».
    """
    src = (ROOT / "gioco27" / "gui" / "onboarding_tab.py").read_text(encoding="utf-8")
    etichette = re.findall(r'ttk\.Button\(qa, text="([^"]*)"', src)
    assert len(etichette) >= 3, "azioni rapide non individuate"
    for e in etichette:
        assert _norm(e) in guida_norm, \
            f"azione rapida «{e}» di «Inizia qui» non documentata nella Guida"


def test_passi_di_onboarding_documentati(guida_norm):
    """I titoli dei tre passi della scheda «Inizia qui»."""
    from gioco27.gui.glossary import ONBOARD_STEPS
    for _icona, titolo, _desc in ONBOARD_STEPS:
        assert _norm(titolo) in guida_norm, \
            f"passo «{titolo}» di «Inizia qui» non documentato nella Guida"
