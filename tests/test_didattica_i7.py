"""Compartimento I7 — percorso didattico, guida, glossario e livelli.

I7 non aggiunge matematica: questi test legano i TESTI (guida, glossario,
onboarding, aiuti) al programma vero. Un livello che punta a una scheda
inesistente, una sotto-scheda non descritta, un esempio citato che non torna
col core o un nome di gruppo legacy in un testo utente diventano test rossi.
"""
import re
import tkinter as tk
from collections import Counter
from pathlib import Path

import pytest

from gioco27 import i18n as catalogo
from gioco27.core import gioco_reale as gr
from gioco27.gui import livelli
from gioco27.gui.glossary import (GLOSSARIO, GLOSSARIO_MATEMATICO, GLOSSARIO_NARRATIVO,
                                  SOTTOSCHEDE_HELP, TAB_HELP)
from gioco27.gui.glossary import testo_aiuto_scheda as _aiuto
from gioco27.gui.guide import PARTI, SEZIONI, numero_sezione, render_guide_segments
from gioco27.services import riconoscimento as rc
from gioco27.services import tabellone as tb
from gioco27.services.procedure import servizio_procedure

ROOT = Path(__file__).resolve().parents[1]
APP_SRC = (ROOT / "gioco27" / "gui" / "app.py").read_text(encoding="utf-8")
IT, EN = catalogo.CATALOGS["it"], catalogo.CATALOGS["en"]


@pytest.fixture(autouse=True)
def italiano():
    catalogo.set_language("it")
    yield
    catalogo.set_language("it")


def _guida(lingua):
    return "".join(t for _, t in render_guide_segments(lingua))


def _norm(t):
    return re.sub(r"\s+", " ", t).strip()


# ════════════════════════════ livelli (DP7) ═══════════════════════════════════

def test_quattro_livelli_in_ordine():
    assert livelli.LIVELLI == ("base", "intermedio", "avanzato", "laboratorio")
    assert livelli.visibile("base", "base") and not livelli.visibile("avanzato", "intermedio")
    assert livelli.normalizza("principiante") == "base"
    assert livelli.normalizza("esperto") == "laboratorio"
    assert livelli.normalizza("GURU") == "base" and livelli.normalizza(None) == "base"


def test_ogni_voce_di_livello_punta_a_una_scheda_esistente():
    schede = set(re.findall(r'_aggiungi_scheda\(\s*nb,\s*"(\w+)"', APP_SRC))
    schede |= {f"stadio{i}" for i in range(3)} if 'f"stadio{i}"' in APP_SRC else set()
    assert schede == set(livelli.SCHEDE)
    azioni = set(re.findall(r'_azioni_livello\["(\w+)"\]', APP_SRC)) | {"preset"}
    assert azioni == set(livelli.AZIONI)
    assert len(livelli.ORDINE_SOTTOSCHEDE_EXPLORER) == 9
    assert set(livelli.SOTTOSCHEDE_EXPLORER) == set(livelli.ORDINE_SOTTOSCHEDE_EXPLORER)


def test_nessuna_vista_sotto_un_suo_prerequisito():
    for vista, prerequisiti in livelli.PREREQUISITI.items():
        for p in prerequisiti:
            assert livelli.indice(livelli.livello_di(p)) <= \
                livelli.indice(livelli.livello_di(vista)), (vista, p)


def test_anomalia_storica_corretta():
    """Prima: in Principiante c'erano Anteprima e Analisi ma non Cicli."""
    s = livelli.SCHEDE
    assert livelli.indice(s["cicli"]) < livelli.indice(s["explorer"])
    assert s["cicli"] == s["anteprima"] == "intermedio"
    assert s["analisi"] == s["distribuzione"] == "laboratorio"
    assert s["explorer"] == "avanzato"
    assert livelli.SOTTOSCHEDE_EXPLORER["riconoscimento"] == "avanzato"
    assert livelli.SOTTOSCHEDE_EXPLORER["laboratorio"] == "laboratorio"


@pytest.mark.parametrize("salvato,atteso", [
    ("principiante", "base"), ("esperto", "laboratorio"), ("intermedio", "intermedio"),
    ("avanzato", "avanzato"), ("GURU", "base"), (["x"], "base"),
])
def test_migrazione_esplicita_della_configurazione(tmp_path, monkeypatch, salvato, atteso):
    import json
    from gioco27.core import config as C
    f = tmp_path / "config.json"
    f.write_text(json.dumps({"livello": salvato}), encoding="utf-8")
    monkeypatch.setattr(C, "_CONFIG_FILE", f)
    monkeypatch.setattr(C, "_CONFIG_DIR", tmp_path)
    c = C.Config()
    assert c.get("livello") == atteso
    c.save()                                   # il valore migrato viene riscritto
    assert json.loads(f.read_text(encoding="utf-8"))["livello"] == atteso


# ═════════════════════════ app reale: visibilita' ═════════════════════════════

@pytest.fixture(scope="module")
def app():
    try:
        radice = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    radice.destroy()
    from gioco27.gui import app as app_module
    a = app_module.App()
    a.update_idletasks()
    try:
        yield a
    finally:
        a._imposta_livello("laboratorio")
        a._cfg["livello"] = "laboratorio"
        a.destroy()


def _visibili(a):
    return {k for k, w in a._schede.items() if a._nb.tab(w, "state") != "hidden"}


@pytest.mark.parametrize("livello", livelli.LIVELLI)
def test_il_livello_controlla_solo_la_visibilita(app, livello):
    app._imposta_livello(livello)
    app.update()
    attese = {k for k, m in livelli.SCHEDE.items() if livelli.visibile(m, livello)}
    assert _visibili(app) == attese
    if livelli.visibile(livelli.SCHEDE["explorer"], livello):
        sotto = {k for k, w in app._sottoschede_explorer.items()
                 if app._explorer_nb.tab(w, "state") != "hidden"}
        assert sotto == {k for k, m in livelli.SOTTOSCHEDE_EXPLORER.items()
                         if livelli.visibile(m, livello)}
    for chiave, widget in app._azioni_livello.items():
        assert widget.winfo_ismapped() == livelli.visibile(livelli.AZIONI[chiave], livello), chiave
    assert bool(app._barra_preset_frame.winfo_manager()) == (livello == "laboratorio")
    assert app._livello_cb.current() == livelli.indice(livello)
    assert app._livello_onboarding_var.get() == livello
    assert app._cfg["livello"] == livello


def test_scendere_di_livello_non_distrugge_nulla(app):
    app._imposta_livello("laboratorio")
    app._seleziona_scheda("explorer")
    app._explorer_nb.select(app._sottoschede_explorer["laboratorio"])
    app._explorer_entry.delete("1.0", "end")
    app._explorer_entry.insert("1.0", "(SCD_U x SDC_U x SDC_U) o MSC")
    widget = app._schede["explorer"]
    app._imposta_livello("base")
    app.update()
    assert app._nb.select() == str(app._schede["inizio"])      # la scheda aperta e' sparita
    assert widget.winfo_exists()
    app._imposta_livello("avanzato")
    app.update()
    assert app._explorer_nb.select() != str(app._sottoschede_explorer["laboratorio"])
    assert app._explorer_entry.get("1.0", "end").strip() == "(SCD_U x SDC_U x SDC_U) o MSC"
    app._explorer_entry.delete("1.0", "end")
    app._imposta_livello("laboratorio")


def test_selettori_di_livello_da_barra_e_onboarding(app):
    app._livello_cb.current(1)
    app._livello_cb.event_generate("<<ComboboxSelected>>")
    app.update()
    assert app._livello == "intermedio" and "cicli" in _visibili(app)
    rb = app._livelli_rb[2]
    rb.invoke()
    app.update()
    assert app._livello == "avanzato" and "explorer" in _visibili(app)
    assert str(app._livello_cb.cget("state")) == "readonly"
    app._imposta_livello("laboratorio")


def test_prima_apertura_suggerisce_base(monkeypatch, tmp_path):
    from gioco27.core import config as C
    monkeypatch.setattr(C, "_CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(C, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(C, "_instance", None, raising=False)
    cfg = C.Config()
    assert cfg.get("livello") == "base" and cfg.get("ui_intro_done") is False


# ═════════════════════════════ guida ═════════════════════════════════════════

def test_percorso_a_parti():
    assert [p for p, _ in PARTI] == [f"guide.part.{c}" for c in "abcdefghijklm"]
    assert len(SEZIONI) == len(set(SEZIONI)) == 41
    assert {f"s{n:02d}" for n in range(1, 34)} <= set(SEZIONI)
    assert [numero_sezione(s) for s in SEZIONI] == list(range(1, 42))
    assert numero_sezione("storia") == 34          # facoltativa, dopo il percorso operativo
    for lingua in ("it", "en"):
        seg = render_guide_segments(lingua)
        assert [t for t, _ in seg].count("part") == len(PARTI)
        assert [t for t, _ in seg].count("tocpart") == len(PARTI)


#: Funzionalita' I1–I6 → frasi che la Guida deve contenere (IT, EN).
COPERTURA = {
    "I1 procedura ed equivalenze": (["216 × 8 = 1 728", "stessa trasformazione", "64", "Variante sicura", "k2"],
                                    ["216 × 8 = 1,728", "same transformation", "64", "Safe variant", "k2"]),
    "I2 tabellone e ritorno": (["Tabellone diretto", "Tabellone inverso", "#56 ↔ #62", "#100 → riga di ritorno #93"],
                               ["Direct board", "Inverse board", "#56 ↔ #62", "#100 → return row #93"]),
    "I2 macchina che dimentica": (["P′  =  ⌊P / 3⌋  +  9·s", "19 = (2,0,1), indirizzo DSC", "= 23"],
                                  ["P′  =  ⌊P / 3⌋  +  9·s", "19 = (2,0,1), address DSC", "= 23"]),
    "I3 errori e recupero": (["Conseguenze reali", "E1", "E2", "E3", "E4", "E5", "E6", "Applica il recupero", "#172"],
                             ["Real consequences", "E1", "E2", "E3", "E4", "E5", "E6", "Apply recovery", "#172"]),
    "I4 spettatore": (["27  →  9  →  3  →  1", "B12", "posizione 13", "#100"],
                      ["27  →  9  →  3  →  1", "B12", "position 13", "#100"]),
    "I5 riconoscimento": (["Teor. 6.4", "Avanti", "A1", "A8", "v → w", "C1", "C9", "C18", "36, 117, 198", "#100 / #91"],
                          ["Thm. 6.4", "Forward", "A1", "A8", "v → w", "C1", "C9", "C18", "36, 117, 198", "#100 / #91"]),
    "I6 laboratorio": (["H — le 216", "Γ — i 648", "S₂₇", "7 tipi ciclici", "#215", "H∘MSC²", "36/36", "controesempio"],
                       ["H — the 216", "Γ — the 648", "S₂₇", "seven cycle types", "#215", "H∘MSC²", "36/36", "counterexample"]),
    "DP9 storia": (["Pacioli", "Verini", "Galasso", "Gergonne", "Gardner", "Elmsley", "21 carte", "problema inverso"],
                   ["Pacioli", "Verini", "Galasso", "Gergonne", "Gardner", "Elmsley", "21-card", "inverse problem"]),
}


@pytest.mark.parametrize("funzione", sorted(COPERTURA))
def test_ogni_funzionalita_i1_i6_ha_una_spiegazione(funzione):
    frasi_it, frasi_en = COPERTURA[funzione]
    for lingua, frasi in (("it", frasi_it), ("en", frasi_en)):
        testo = _guida(lingua)
        mancanti = [f for f in frasi if f not in testo]
        assert not mancanti, (funzione, lingua, mancanti)


def test_nessun_riferimento_obsoleto():
    for lingua in ("it", "en"):
        testo = _guida(lingua)
        assert not re.search(r"capitolo 100|chapter 100", testo)
        assert not re.search(r"\b(sei|sette|otto) sotto-tab|\b(six|seven|eight) sub-tabs", testo)
        assert "Modalità principiante" not in testo and "Beginner mode" not in testo
        assert "posizione 14" not in testo and "position 14" not in testo
        assert "G_ext" not in testo and not re.search(r"\|G\|", testo)
    for cat in (IT, EN):
        for k, v in cat.items():
            assert not re.search(r"capitolo 100|chapter 100", v), k


def test_nove_sotto_tab_esistenti_e_descritte():
    etichette = [e for e, _ in SOTTOSCHEDE_HELP["explorer"]]
    assert len(etichette) == 9
    aiuto_it = _aiuto("explorer")
    for e in etichette:
        assert IT[e] in aiuto_it
        assert _norm(IT[e]) in _norm(_guida("it"))
    catalogo.set_language("en")
    aiuto_en = _aiuto("explorer")
    for e in etichette:
        assert EN[e] in aiuto_en


def test_ogni_scheda_principale_ha_aiuto():
    usate = set(re.findall(r'_wrap_tab\(self\._build_\w+_tab,\s*"(\w+)"', APP_SRC))
    assert usate and usate <= set(TAB_HELP)
    for chiave in TAB_HELP:
        assert _aiuto(chiave)
    for chiave, righe in SOTTOSCHEDE_HELP.items():
        for etichetta, aiuto in righe:
            assert etichetta in IT and aiuto in IT and aiuto in EN
    assert "Spettatore" in _aiuto("simulatore")
    assert "27 → 9 → 3 → 1" in _aiuto("simulatore")


# ═════════════════════ esempi citati: tornano col core ════════════════════════

def test_esempi_citati_esistono():
    assert tb.ritorno(100).numero_tavola == 93
    assert tb.ritorno(56).numero_tavola == 62 and tb.ritorno(62).numero_tavola == 56
    assert tb.ritorno(177).numero_tavola == 142
    for n in (78, 193, 0):
        assert tb.ritorno(n).numero_tavola == n
    assert gr.digits3(19) == (2, 0, 1) and gr.parola(19) == "DSC"
    assert gr.digits3(13) == (1, 1, 1)
    assert [sum(range(9 * d, 9 * d + 9)) for d in range(3)] == [36, 117, 198]
    assert rc.separabile(rc.traslazione(9)).numero_tavola == 144
    assert rc.separabile(rc.traslazione(18)).numero_tavola == 108
    assert not rc.separabile(rc.traslazione(1)).separabile
    assert not rc.classe_estesa(rc.traslazione(1)).appartiene
    J = tuple(26 - i for i in range(27))
    assert rc.separabile(J).numero_tavola == 215
    s = servizio_procedure()
    assert sorted(p.identificatore for p in s.classe_trasformazione(J)) == [
        (0, 1), (0, 2), (0, 4), (0, 7), (215, 0), (215, 3), (215, 5), (215, 6)]
    fibra = s.fibra_bersaglio(0, 13)
    assert len(fibra.procedure) == 64 and len(fibra.gruppi) == 8
    diverse = sum(s.procedura_storica(c, t) != s.procedura_sicura(c, t)
                  for c in range(27) for t in range(27))
    assert diverse == 386
    T100 = tuple(gr.riga_tavola(100)["T"])
    assert T100[10] == 5 and T100.index(10) == 6
    assert sum(1 for n in range(216) if gr.riga_tavola(n)["autoinversa"]) == 64
    assert Counter(len(gr.riga_tavola(n)["T"]) for n in range(216)) == {27: 216}
    fissi = Counter(sum(1 for i, v in enumerate(gr.riga_tavola(n)["T"]) if i == v)
                    for n in range(216))
    assert fissi == {0: 152, 1: 27, 3: 27, 9: 9, 27: 1}


def test_numeri_di_riga_citati_sono_righe_valide():
    for lingua in ("it", "en"):
        for n in re.findall(r"#(\d+)", _guida(lingua)):
            assert 0 <= int(n) <= 215, n


# ═══════════════════════════ glossario (DP8) ═════════════════════════════════

#: termini richiesti dal compartimento → chiave del glossario
TERMINI = {
    "carta": "card", "posizione": "position", "mescolamento": "shuffle",
    "impilamento": "stacking", "tabellone": "board", "tabellone inverso": "inverse_board",
    "procedura": "procedure", "trasformazione": "transformation",
    "permutazione": "permutation", "inversa": "inverse", "ciclo": "cycle",
    "ordine": "order", "punto fisso": "fixed_point", "fibra": "fiber",
    "separabilità digitale": "separability", "fattore locale": "local_factor",
    "somma di fibra": "fiber_sum", "forma canonica": "canonical_form",
    "classe di coniugio": "conjugacy", "gruppo H": "group_h", "gruppo Γ": "group_gamma",
    "S27": "s27", "centro": "center", "classe laterale": "coset", "ritorno": "return",
    "guida": "guide_cards", "recupero": "recovery",
    "indice": "index", "disposizione": "arrangement", "carta scelta": "chosen_card",
    "posizione bersaglio": "target_position", "fase": "phase", "tappa": "checkpoint",
    "colonna e mazzetto": "column_pile", "trasformazione cumulativa": "cumulative_transform",
    "trasformazione relativa": "relative_transform", "mazzi gemelli": "twin_decks",
    "tipo ciclico": "cycle_type", "struttura ciclica": "cycle_structure",
    "orbita": "orbit", "storia": "history", "replay a ritroso": "path_replay",
    "firma di blocco": "block_signature", "riconoscimento": "recognition",
    "taglio": "cut", "traslazione": "translation", "rotazione": "rotation",
}


def test_glossario_copre_i_termini_richiesti():
    assert set(TERMINI.values()) <= set(GLOSSARIO_MATEMATICO)
    assert len(GLOSSARIO) == len(set(GLOSSARIO)) == 63


def test_glossario_simmetrico():
    for k in GLOSSARIO:
        for campo in ("term", "short", "long"):
            chiave = f"glossary.{campo}.{k}"
            assert IT[chiave] and EN[chiave], chiave
            fi = sorted(re.findall(r"\{(\w+)\}", IT[chiave]))
            fe = sorted(re.findall(r"\{(\w+)\}", EN[chiave]))
            assert fi == fe == [], chiave


def test_alias_narrativi_rimandano_al_termine_tecnico():
    rimandi = {"gaia": "H", "cronaca": "rasformazion", "giullare": "J",
               "prima_crisi": "impil", "seconda_crisi": "J"}
    for k, frammento in rimandi.items():
        assert frammento in IT[f"glossary.long.{k}"] + IT[f"glossary.short.{k}"], k
    assert set(rimandi) <= set(GLOSSARIO_NARRATIVO)
    # nei controlli e nei risultati matematici nessun nome narrativo
    for k, v in IT.items():
        if k.startswith(("lab.", "recognition.", "button.", "tab.", "level.")) \
                and not k.startswith("lab.source."):     # le fonti citano titoli del libro
            assert not re.search(r"\b(Gaia|Cronaca|Giullare|Seldon)\b", v), k


# ═══════════════════════════ DP2: H = 216, Γ = 648 ═══════════════════════════

def test_dp2_nei_testi_utente():
    for cat in (IT, EN):
        for k, v in cat.items():
            if k.startswith("export.document."):
                continue                       # formato di export: invariato (debito K0)
            assert "G_ext" not in v, k
            assert not re.search(r"\|G\||\bG = GEN3|Z\(G\)", v), k
            assert not re.search(r"\bH\s*[—=(-]\s*648|\|H\|\s*=\s*648", v), k
            if re.search(r"\b648\b", v):
                assert "Γ" in v, k
    for lingua in ("it", "en"):
        testo = _guida(lingua)
        assert "|H| = 216" in testo and "648" in testo and "Γ" in testo
    assert "H = GEN3³" in IT["cayley.window_title"] and "|H| = 216" in IT["conjugacy.window_title"]


# ═══════════════════════════ i18n: chiavi usate ══════════════════════════════

def test_chiavi_della_guida_tutte_usate(monkeypatch):
    from gioco27.gui import guide as guida
    usate = set()
    originale = guida.tr

    def spia(chiave, **valori):
        usate.add(chiave)
        return originale(chiave, **valori)
    monkeypatch.setattr(guida, "tr", spia)
    guida.render_guide_segments("it")
    inutilizzate = {k for k in IT if k.startswith("guide.")} - usate
    assert not inutilizzate, sorted(inutilizzate)


def test_chiavi_nuove_i7_referenziate():
    sorgenti = "".join(p.read_text(encoding="utf-8")
                       for p in (ROOT / "gioco27").rglob("*.py") if p.name != "i18n.py")
    famiglie = {f"level.name.{l}" for l in livelli.LIVELLI} | \
        {f"level.desc.{l}" for l in livelli.LIVELLI} | \
        {f"glossary.{c}.{k}" for c in ("term", "short", "long") for k in GLOSSARIO} | \
        {a for righe in SOTTOSCHEDE_HELP.values() for _, a in righe}
    nuove = [k for k in IT if k.startswith(("level.", "help.sub.", "onboarding.", "tooltip.level",
                                              "tooltip.open_table", "glossary."))]
    assert nuove
    for k in nuove:
        assert k in famiglie or f"'{k}'" in sorgenti or f'"{k}"' in sorgenti, k
    for k in ("button.beginner_mode", "tooltip.beginner_mode", "onboarding.button.go_preview",
              "guide.s30.terms", "guide.s29.mode.items"):
        assert k not in IT and k not in EN


def test_onboarding_senza_testo_italiano_cablato():
    src = (ROOT / "gioco27" / "gui" / "onboarding_tab.py").read_text(encoding="utf-8")
    assert not re.findall(r'text="[^"]*[a-zà-ù]{4,}[^"]*"', src)
    assert "_livello_onboarding_var" in src and "level.desc." in src


# ═════════════ matrice di completezza V4 (righe P0/P1, livello D) ═════════════

def _sezioni(lingua="it"):
    """{identificatore: testo della sezione} dalla Guida renderizzata."""
    per_numero, corrente = {}, None
    for tag, testo in render_guide_segments(lingua):
        if tag == "h2":
            corrente = int(testo.split(".", 1)[0])
            per_numero[corrente] = ""
        if corrente is not None and tag not in ("part", "tocpart"):
            per_numero[corrente] += testo
    return {sid: per_numero[numero_sezione(sid)] for sid in SEZIONI}


#: riga dell'audit (docs/audits/V4_MATHEMATICAL_DIDACTIC_COVERAGE_AUDIT.md § 7, priorita'
#: V4-P0/P1) → (sezione della Guida, frase che la spiega). Dopo I7: D = sì.
COPERTURA_AUDIT = {
    "L04": ("i2m", "P = 3·altezza + colonna"),
    "L05": ("s02", "codificate in base 3"),
    "L06": ("i2m", "tre gruppi (n₂ = 0, 1, 2)"),
    "L07": ("i2m", "indirizzo DSC"),
    "L08": ("i2m", "P′  =  ⌊P / 3⌋  +  9·s"),
    "L09": ("i2m", "cifra che esce e cifra che entra"),
    "L10": ("i2m", "rev ω(n)"),
    "L11": ("i2m", "x  =  36 + 81j − S₈"),
    "L12": ("i5", "mazzo finale della riga #195"),
    "L14": ("i5", "T[carta] = posizione finale"),
    "L15": ("s01", "contando da 0"),
    "L18": ("i2t", "Tabellone diretto"),
    "L20": ("i5", "Criterio delle somme"),
    "L21": ("i2t", "la colonna è la cifra iniziale"),
    "L22": ("i5", "#195"),
    "L23": ("i2m", "26 − P"),
    "L26": ("s17", "trasposta di T"),
    "L35": ("i2m", "27 posizioni"),
    "L36": ("i2t", "sigle inverse (CDS ↔ DSC)"),
    "L39": ("i2m", "capovolgimento"),
    "L44": ("i1", "esattamente 8 procedure"),
    "L46": ("s30", "Cronaca"),
    "L54": ("i3", "J∘T (riga #172)"),
    "L55": ("s29", "I quattro livelli"),
    "L57": ("i5", "A1 — «note due, la terza si calcola»"),
    "L58": ("i2t", "La riga della Tavola è l'unica procedura semplice"),
    "L59": ("i5", "39 − q₀ − q₂"),
    "L63": ("i1", "216 × 8 = 1 728"),
    "L67": ("i4", "ogni risposta fissa una cifra"),
    "L70": ("i4", "ordine iniziale noto"),
    "L81": ("i4", "B12"),
    "L91": ("i5", "Due carte guida"),
    "L93": ("i5", "v → w"),
    "L95": ("s09", "Γ = ⟨S₃³, MSC⟩"),
    "L97": ("i5", "fibra (i, t)"),
    "L106": ("s09", "Nel codice storico"),
    "A02": ("i2m", "Legge del singolo stadio"),
    "A04": ("i5", "Def. 4.1"),
    "A06": ("i5", "ρ̂ᵢ(t)"),
    "A07a": ("i5", "C₀ = 108,  C₁ = 90,  C₂ = 36"),
    "A09": ("i6", "7 tipi ciclici"),
    "A12": ("i4", "27  →  9  →  3  →  1"),
    "A13": ("i1", "Qᵢ = R_U^vᵢ ∘ Sᵢ ∘ R_U^uᵢ"),
}

#: righe P0/P1 fuori da I7: unica eccezione, rinvio approvato.
FUORI_I7 = {
    "L90": "rinvio approvato: richiede successione di Procedure / tabellone cumulativo / "
           "replay; proprietario futuro = J.",
}


def test_matrice_audit_p0_p1_didattica():
    csv = (ROOT / "docs" / "audits" / "V4_COVERAGE_MATRIX.csv").read_text(encoding="utf-8")
    righe = {}
    for linea in csv.splitlines()[1:]:
        campi = linea.split(";") if linea.count(";") > linea.count(",") else linea.split(",")
        righe[campi[0].strip('"')] = linea
    p0p1 = {k for k, v in righe.items() if "V4-P0" in v or "V4-P1" in v}
    assert p0p1, "matrice V4 non letta"
    assert set(COPERTURA_AUDIT) | set(FUORI_I7) >= p0p1 - {"L37"}, \
        sorted(p0p1 - set(COPERTURA_AUDIT) - set(FUORI_I7))
    assert len(p0p1 - {"L37"}) == 44 and set(FUORI_I7) == {"L90"}
    assert len(set(COPERTURA_AUDIT) & p0p1) == 43
    sezioni = _sezioni("it")
    for riga, (sid, frase) in COPERTURA_AUDIT.items():
        assert frase in sezioni[sid], (riga, sid, frase)


def test_l11_firma_dei_blocchi_e_elemento_mancante():
    """Libro § 1.10, Prop. 1.7–1.8, e l'esempio della Guida (S₈ = 104 → 13)."""
    blocchi = [range(9 * j, 9 * j + 9) for j in range(3)]
    assert [sum(b) for b in blocchi] == [36 + 81 * j for j in range(3)] == [36, 117, 198]
    intervalli = []
    for j, b in enumerate(blocchi):
        s8 = {sum(b) - x: x for x in b}
        intervalli.append((min(s8), max(s8)))
        for somma, x in s8.items():
            assert 36 + 81 * j - somma == x
    assert intervalli == [(28, 36), (100, 108), (172, 180)]
    assert 36 + 81 * 1 - 104 == 13


def test_a13_corollario_5_2_su_tutte_le_procedure():
    """App. D Cor. 5.2 con la convenzione DP3 = A del programma, e l'Es. 7.2."""
    from itertools import product
    from gioco27.services.procedure import ProceduraGioco
    s = servizio_procedure()
    R, ident = (2, 1, 0), (0, 1, 2)

    def comp(a, b):
        return tuple(a[b[x]] for x in range(3))

    def rp(k):
        return R if k % 2 else ident
    for sig, eps in product(product(gr.SIGLE, repeat=3), product((0, 1), repeat=3)):
        fattori = rc.separabile(s.trasformazione(ProceduraGioco(sig, eps))).fattori
        for i in range(3):
            u, v = sum(eps[:i + 1]) % 2, sum(eps[i + 1:]) % 2
            S = tuple(gr.MESCOLAMENTO[sig[i]])
            assert comp(rp(v), comp(S, rp(u))) == tuple(fattori[i])
            assert comp(rp(v), comp(tuple(fattori[i]), rp(u))) == S
    # Es. 7.2: S0 = (0 1 2), S1 = (0 1), S2 = (0 2) in cicli; ε = (1, 0, 1)
    S = ((1, 2, 0), (1, 0, 2), (2, 1, 0))
    eps = (1, 0, 1)
    Q = [comp(rp(sum(eps[i + 1:])), comp(S[i], rp(sum(eps[:i + 1])))) for i in range(3)]
    assert Q == [(2, 0, 1), (0, 2, 1), (2, 1, 0)]          # (0 2 1), (1 2), (0 2)
    d2, d1, d0 = gr.digits3(5)
    assert 9 * Q[2][d2] + 3 * Q[1][d1] + Q[0][d0] == 25
    # le 8 procedure di una trasformazione hanno lo stesso tabellone: ε non si ricostruisce
    J = tuple(26 - i for i in range(27))
    storie = {p.rovesciamenti for p in s.classe_trasformazione(J)}
    assert len(storie) == 8
