"""Fase P (iterazione 2) — riferimenti al libro in un solo punto.

Protegge: nessun segnaposto ⟦rif:…⟧ non risolto nei cataloghi, nessun numero
editoriale obsoleto (prima della Fase G del libro) nei testi correnti, numeri
dei risultati citati presenti soltanto in `gioco27/riferimenti.py`, fonti del
Laboratorio con chiavi semantiche.
"""
import re
from pathlib import Path

import pytest

from gioco27 import i18n, riferimenti
from gioco27.services import laboratorio as lab

ROOT = Path(__file__).resolve().parents[1]

#: numerazione precedente alla Fase G del libro: non deve ricomparire
OBSOLETI = re.compile(r"\b(?:11\.68|9\.58|5\.53)\b")


def test_tabella_dei_riferimenti_ben_formata():
    assert set(riferimenti.RIFERIMENTI_LIBRO) == {
        "forma_normale_intermedie", "ricostruzione_fibre",
        "uniformita_gioco_ordinario", "autoinversa_tabellone",
        "griglia_classi_coniugio"}
    for chiave, r in riferimenti.RIFERIMENTI_LIBRO.items():
        assert r.tipo in ("teorema", "proposizione", "figura"), chiave
        assert re.fullmatch(r"\d+\.\d+", r.numero), chiave
        assert r.titolo and r.sezione.startswith("§ "), chiave


@pytest.mark.parametrize("lingua, teorema", [("it", "Teor."), ("en", "Thm.")])
def test_forma_breve_localizzata(lingua, teorema):
    numero = riferimenti.RIFERIMENTI_LIBRO["forma_normale_intermedie"].numero
    assert riferimenti.riferimento("forma_normale_intermedie", lingua) == f"{teorema} {numero}"
    assert riferimenti.risolvi_riferimenti(
        "(⟦rif:forma_normale_intermedie⟧)", lingua) == f"({teorema} {numero})"
    with pytest.raises(KeyError):
        riferimenti.risolvi_riferimenti("⟦rif:inesistente⟧", lingua)


@pytest.mark.parametrize("lingua", ["it", "en"])
def test_cataloghi_senza_segnaposto_ne_numeri_obsoleti(lingua):
    for k, v in i18n.CATALOGS[lingua].items():
        assert "⟦" not in v and "⟧" not in v, k
        assert not OBSOLETI.search(v), k


@pytest.mark.parametrize("lingua", ["it", "en"])
def test_testi_che_citano_i_risultati_usano_il_numero_corrente(lingua):
    cat = i18n.CATALOGS[lingua]
    forma = riferimenti.riferimento("forma_normale_intermedie", lingua)
    otto = riferimenti.riferimento("uniformita_gioco_ordinario", lingua)
    for k in ("lab.cosets.intro", "glossary.long.group_gamma",
              "lab.source.libro_forma_normale_intermedie"):
        assert forma in cat[k], k
    for k in ("guide.i1.count", "lab.source.libro_uniformita_gioco_ordinario"):
        assert otto in cat[k], k
    assert riferimenti.riferimento("autoinversa_tabellone", lingua) in cat[
        "lab.source.libro_autoinversa_tabellone"]
    assert riferimenti.riferimento("ricostruzione_fibre", lingua) in cat[
        "glossary.long.fiber_sum"]


def test_numeri_dei_risultati_solo_nella_tabella():
    """Il numero corrente non e' duplicato in sorgenti, servizi, GUI o i18n."""
    numeri = {f"{r.numero}" for r in riferimenti.RIFERIMENTI_LIBRO.values()}
    citazione = re.compile(r"(?:Teor|Thm|Prop|Fig)\.\s*(\d+\.\d+)\b")
    for p in (ROOT / "gioco27").rglob("*.py"):
        if p.name == "riferimenti.py":
            continue
        trovati = set(citazione.findall(p.read_text(encoding="utf-8"))) & numeri
        assert not trovati, (p.relative_to(ROOT).as_posix(), trovati)


# ═══════════════ Fase P3: articolo originale, distinto dal libro ═══════════════

#: numeri della versione originale dell'articolo: solo in riferimenti.py
ARTICOLO_VECCHIO = re.compile(r"(?:Teor|Thm)\.\s*5\.1\b|(?:Oss|Obs)\.\s*5\.3\b|(?:Es|Ex)\.\s*6\.1\b")


def test_versione_dell_articolo_originale_identificata():
    v = riferimenti.ARTICOLO_ORIGINALE
    assert "8a2e41a" in v.sorgente and "2026-09-10" in v.pdf
    assert "unpublished" in v.pubblicazione
    arts = riferimenti.RIFERIMENTI_ARTICOLO_ORIGINALE
    assert {k: (r.tipo, r.numero) for k, r in arts.items()} == {
        "statistiche_fibra": ("teorema", "5.1"),
        "somme_non_criterio": ("osservazione", "5.3"),
        "ricostruzione_codice": ("esempio", "6.1")}
    # nessuna corrispondenza inventata: l'osservazione non ha un gemello in App. D
    assert arts["somme_non_criterio"].equivalente_app_d is None
    assert arts["statistiche_fibra"].equivalente_app_d == "App. D, Teor. 6.1"
    assert arts["ricostruzione_codice"].equivalente_app_d == "App. D, Es. 7.1"


@pytest.mark.parametrize("lingua, oss, es", [("it", "Oss. 5.3", "Es. 6.1"),
                                             ("en", "Obs. 5.3", "Ex. 6.1")])
def test_citazioni_dell_articolo_originale_dichiarano_la_versione(lingua, oss, es):
    cat = i18n.CATALOGS[lingua]
    assert oss in cat["guide.i5.directions"]
    assert ("settembre 2026" if lingua == "it" else "September 2026") in cat["guide.i5.directions"]
    assert ("settembre 2026" if lingua == "it" else "September 2026") in cat["guide.i1.reversals"]
    assert ("Es. 7.1" if lingua == "it" else "Ex. 7.1") in cat["recognition.example.es71"] and "App. D" in cat["recognition.example.es71"]
    assert riferimenti.risolvi_riferimenti("⟦art:statistiche_fibra⟧", lingua).endswith("5.1")


def test_numeri_dell_articolo_originale_solo_nella_tabella():
    for p in (ROOT / "gioco27").rglob("*.py"):
        if p.name == "riferimenti.py":
            continue
        trovati = ARTICOLO_VECCHIO.findall(p.read_text(encoding="utf-8"))
        assert not trovati, (p.relative_to(ROOT).as_posix(), trovati)


def test_fonti_del_laboratorio_semantiche_e_tradotte():
    fonti = {p.fonte for p in lab.CATALOGO}
    # le fonti del libro hanno chiavi semantiche; quelle dell'App. D (articolo,
    # numerazione propria e stabile) restano com'erano
    assert not {f for f in fonti if re.match(r"libro_(?:teor|prop)_\d", f)}, fonti
    for lingua in ("it", "en"):
        for f in fonti:
            assert f"lab.source.{f}" in i18n.CATALOGS[lingua], (lingua, f)
