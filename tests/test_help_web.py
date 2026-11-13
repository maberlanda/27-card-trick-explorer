"""Verifica la corrispondenza con la Guida e i collegamenti delle pagine web."""

from html.parser import HTMLParser
from urllib.parse import urlsplit

from gioco27 import i18n
from gioco27.gui.context_help import TOPICS
from gioco27.gui.guide import SEZIONI
from tools.export_help import esporta


class Documento(HTMLParser):
    def __init__(self, percorso):
        super().__init__()
        self.ids = set()
        self.links = []
        self.lingua = None
        self.feed(percorso.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attributi = dict(attrs)
        if tag == "html":
            self.lingua = attributi["lang"]
        if "id" in attributi:
            assert attributi["id"] not in self.ids
            self.ids.add(attributi["id"])
        if "href" in attributi:
            self.links.append(attributi["href"])


def test_export_bilingue_con_indici_e_collegamenti(tmp_path):
    precedente = i18n.get_language()
    esporta(tmp_path)
    assert i18n.get_language() == precedente
    documenti = {p: Documento(p) for p in tmp_path.rglob("*.html")}
    assert len(documenti) == 5
    for lingua, novita in (("it", "Fibre"), ("en", "Fibres")):
        guida = tmp_path / lingua / "howto.html"
        aiuto = tmp_path / lingua / "help.html"
        assert documenti[guida].lingua == documenti[aiuto].lingua == lingua
        assert "../index.html" in documenti[guida].links
        assert "../index.html" in documenti[aiuto].links
        assert set(SEZIONI) == documenti[guida].ids - {"content"}
        assert set(TOPICS) <= documenti[aiuto].ids
        assert novita in guida.read_text(encoding="utf-8")
    for file, documento in documenti.items():
        for link in documento.links:
            url = urlsplit(link)
            assert not url.scheme
            destinazione = (file.parent / url.path).resolve() if url.path else file
            assert destinazione.is_file(), link
            if url.fragment:
                assert url.fragment in documenti[destinazione].ids, link
