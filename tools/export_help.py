"""Esporta la Guida e l'aiuto dell'app in HTML statico, senza avviare Tk."""

import argparse
from html import escape
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gioco27 import __version__, i18n
from gioco27.gui.context_help import TOPICS
from gioco27.gui.glossary import SOTTOSCHEDE_HELP, TAB_HELP
from gioco27.gui.guide import PARTI, SEZIONI, render_guide_segments


_PAGINE = {
    "it": ("Guida", "Aiuto", "Vai al contenuto", "Aiuto per scheda", "Argomenti"),
    "en": ("How-to", "Help", "Skip to content", "Help by tab", "Topics"),
}
_LINGUE = {"it": "Italiano", "en": "English"}
_SCHEDE = {
    "stadio": ("tab.stage", "s04"), "anteprima": ("tab.preview", "s14"),
    "analisi": ("tab.analysis", "s15"), "explorer": ("tab.explorer", "s16"),
    "cicli": ("tab.cycles", "s20"), "distribuzione": ("tab.distribution", "s21"),
    "simulatore": ("tab.simulator", "s19"), "tavola": ("tab.table", "i2t"),
}


def _link(url, testo):
    return f'<a href="{escape(url)}">{escape(testo)}</a>'


def _documento(lingua, pagina, titolo, contenuto):
    guida, aiuto, salta, _, _ = _PAGINE[lingua]
    altra = "en" if lingua == "it" else "it"
    navigazione = []
    for nome, titolo_link in (("howto", guida), ("help", aiuto)):
        corrente = ' aria-current="page"' if nome == pagina else ""
        navigazione.append(f'<a href="{nome}.html"{corrente}>{titolo_link}</a>')
    navigazione.append(f'<a href="../{altra}/{pagina}.html" lang="{altra}">{_LINGUE[altra]}</a>')
    return f"""<!doctype html>
<html lang="{lingua}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(titolo)}</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<a class="skip" href="#content">{salta}</a>
<header><nav>{' '.join(navigazione)}</nav><span>v{__version__}</span></header>
<main id="content" tabindex="-1">
<h1>{escape(titolo)}</h1>
{contenuto}
</main>
</body></html>
"""


def _righe(segmenti):
    """Mantiene uniti testo e frammenti di codice che occupano la stessa riga."""
    riga = []
    for tag, testo in segmenti:
        if tag in {"sep", "part", "h2", "h3", "formula", "hilight"}:
            if riga:
                yield "riga", riga
                riga = []
            yield tag, testo.strip()
            continue
        for i, frammento in enumerate(testo.split("\n")):
            if i:
                yield "riga", riga
                riga = []
            if frammento:
                riga.append((tag, frammento))
    if riga:
        yield "riga", riga


def _testo_riga(frammenti):
    return "".join(f"<code>{escape(testo)}</code>" if tag == "code" else escape(testo)
                   for tag, testo in frammenti)


def _guida(lingua):
    tr = i18n.tr
    segmenti = render_guide_segments()
    titolo = segmenti[0][1].strip()
    indice = [f'<nav class="contents" aria-label="{escape(tr("guide.toc"))}">',
              f'<h2>{escape(tr("guide.toc"))}</h2>']
    for parte, sezioni in PARTI:
        indice.append(f"<h3>{escape(tr(parte))}</h3><ul>")
        for sid in sezioni:
            numero = SEZIONI.index(sid) + 1
            testo = f"{numero}. {tr(f'guide.{sid}.title')}"
            indice.append(f"<li>{_link(f'#{sid}', testo)}</li>")
        indice.append("</ul>")
    indice.append("</nav>")

    corpo = []
    sezioni = iter(SEZIONI)
    lista_aperta = False
    primo = next(i for i, (tag, _) in enumerate(segmenti) if tag == "part")
    for tag, valore in _righe(segmenti[primo:]):
        e_voce = tag == "riga" and bool(valore) and valore[0][1].lstrip().startswith(("•", "◦"))
        if lista_aperta and not e_voce:
            corpo.append("</ul>")
            lista_aperta = False
        if e_voce:
            if not lista_aperta:
                corpo.append("<ul>")
                lista_aperta = True
            stile, testo = valore[0]
            testo = testo.lstrip()[1:].lstrip()
            corpo.append(f"<li>{_testo_riga([(stile, testo), *valore[1:]])}</li>")
        elif tag == "part":
            corpo.append(f'<h2 class="part">{escape(valore)}</h2>')
        elif tag == "h2":
            corpo.append(f'<h3 id="{next(sezioni)}">{escape(valore)}</h3>')
        elif tag == "h3":
            corpo.append(f"<h4>{escape(valore)}</h4>")
        elif tag in {"formula", "hilight"}:
            corpo.append(f'<pre class="{tag}">{escape(valore)}</pre>')
        elif tag == "riga" and valore:
            stile = valore[0][0]
            corpo.append(f'<p class="{stile}">{_testo_riga(valore)}</p>')
    if lista_aperta:
        corpo.append("</ul>")
    return _documento(lingua, "howto", titolo, "\n".join(indice + corpo))


def _aiuto(lingua):
    tr = i18n.tr
    guida, aiuto, _, per_scheda, argomenti = _PAGINE[lingua]
    schede = []
    for chiave, (breve, esteso) in TAB_HELP.items():
        etichetta, sezione = _SCHEDE[chiave]
        titolo = tr(etichetta, number="0–2")
        schede.append((chiave, titolo, sezione, breve, esteso))
    indice = [f'<nav class="contents" aria-label="{per_scheda}"><h2>{per_scheda}</h2><ul>']
    corpo = [f"<h2>{per_scheda}</h2>"]
    for chiave, titolo, sezione, breve, esteso in schede:
        indice.append(f"<li>{_link(f'#{chiave}', titolo)}</li>")
        corpo.extend((f'<h3 id="{chiave}">{escape(titolo)}</h3>',
                      f"<p><strong>{escape(tr(breve))}</strong></p>",
                      f"<p>{escape(tr(esteso))}</p>"))
        sotto = SOTTOSCHEDE_HELP.get(chiave, ())
        if sotto:
            corpo.append("<ul>")
            for nome, testo in sotto:
                corpo.append(f"<li><strong>{escape(tr(nome))}</strong> — {escape(tr(testo))}</li>")
            if chiave == "cicli":
                for key in ("positions.tab", "fibres.tab"):
                    corpo.append(f"<li>{_link(f'howto.html#{sezione}', tr(key))}</li>")
            corpo.append("</ul>")
        corpo.append(f"<p>{_link(f'howto.html#{sezione}', guida)}</p>")
    indice.append(f"</ul><h2>{argomenti}</h2><ul>")
    corpo.append(f"<h2>{argomenti}</h2>")
    for topic, sezione in TOPICS.items():
        titolo = tr(f"ux4.help.{topic}.title")
        indice.append(f"<li>{_link(f'#{topic}', titolo)}</li>")
        corpo.extend((f'<h3 id="{topic}">{escape(titolo)}</h3>',
                      f'<p>{escape(tr(f"ux4.help.{topic}.body"))}</p>',
                      f"<p>{_link(f'howto.html#{sezione}', guida)}</p>"))
    indice.append("</ul></nav>")
    return _documento(lingua, "help", aiuto, "\n".join(indice + corpo))


def esporta(destinazione):
    """Scrive due documenti per lingua e un indice bilingue."""
    destinazione.mkdir(parents=True, exist_ok=True)
    css = Path(__file__).with_name("help_web.css").read_text(encoding="utf-8")
    (destinazione / "style.css").write_text(css, encoding="utf-8")
    precedente = i18n.get_language()
    try:
        for lingua in _LINGUE:
            i18n.set_language(lingua)
            cartella = destinazione / lingua
            cartella.mkdir(exist_ok=True)
            (cartella / "howto.html").write_text(_guida(lingua), encoding="utf-8")
            (cartella / "help.html").write_text(_aiuto(lingua), encoding="utf-8")
    finally:
        i18n.set_language(precedente)
    indice = """<!doctype html>
<html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gioco delle 27 carte · 27-card trick</title>
<link rel="stylesheet" href="style.css"></head><body><main>
<h1>Gioco delle 27 carte</h1>
<p>Italiano · <a href="it/howto.html">Guida</a> · <a href="it/help.html">Aiuto</a></p>
<p lang="en">English · <a href="en/howto.html">How-to</a> · <a href="en/help.html">Help</a></p>
</main></body></html>
"""
    (destinazione / "index.html").write_text(indice, encoding="utf-8")
    (destinazione / ".nojekyll").touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destinazione", type=Path, nargs="?", default=Path("build/help-web"))
    esporta(parser.parse_args().destinazione)
