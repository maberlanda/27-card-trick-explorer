"""Compartimento E — il linguaggio ha un solo parser e una sola AST.

Il corpus condiviso e le tre prove della divergenza B07 restano quelle del
passo precedente (ancora `xfail`: il Mescolamento ha tuttora una grammatica
propria). Qui si verifica il contratto nuovo — `core.espressione`: AST,
valutazione e traccia cronologica — e che non dipenda da GUI, Tk o
filesystem.

Convenzioni verificate (invarianti di D, qui solo usate):

* ``T[carta] = posizione di destinazione``;
* ``mazzo[posizione] = carta``;
* ``(a ∘ b)[i] = a[b[i]]`` — in ``A ∘ B`` si applica prima B.

I test non dipendono da tempi o risorse esterne: tutto e' deterministico.
"""
import ast
import pathlib

import numpy as np
import pytest

from gioco27.core.algebra import Controller, ParseError
from gioco27.core.espressione import analizza, permutazione_di, traccia_simulazione
from gioco27.gui.shuffle import ShuffleViewerFrame

RADICE = pathlib.Path(__file__).resolve().parents[1]


# ═════════════════════════════ corpus condiviso ═════════════════════════════
#
# Ricavato dal linguaggio realmente supportato dal parser autorevole
# (core/algebra.py: Lexer.VALID_ATOMS + grammatica expr/term/factor), dai test
# preesistenti e dalle stringhe prodotte dall'Analisi. Nessuna sintassi nuova
# e' stata inventata qui.

VALIDI = [
    # identita'
    ("I",                                   "identita' di 27"),
    ("(SCD_U x SCD_U x SCD_U)",             "identita' come Kronecker"),
    ("MSC o MSC o MSC",                     "MSC³ = I"),
    ("J o J",                               "J² = I"),
    # atomi
    ("MSC",                                 "mescolamento singolo"),
    ("J",                                   "blocco J"),
    # generatori validi, uno per nome
    ("(SCD_U x SDC_U x CSD_U)",             "tre generatori distinti"),
    ("(CDS_U x DSC_U x DCS_U)",             "gli altri tre generatori"),
    # alias storici di gioco
    ("(R_U x R_U x R_U)",                   "alias R_U = DCS_U"),
    ("(I_3 x I_3 x I_3)",                   "alias I_3 = SCD_U"),
    ("(R_U x I_3 x DSC_U)",                 "alias e nomi canonici insieme"),
    # composizioni
    ("MSC o (SCD_U x SCD_U x CDS_U)",       "composizione di due fattori"),
    ("(SCD_U x SCD_U x CDS_U) o MSC o (I_3 x I_3 x I_3)",
                                            "turno di gioco completo"),
    ("MSC o J",                             "atomi di 27 composti"),
    # parentesi e annidamento
    ("(MSC o MSC)",                         "composizione fra parentesi"),
    ("((MSC))",                             "parentesi ridondanti"),
    ("(MSC) o (MSC)",                       "parentesi su ogni termine"),
    ("((SCD_U x SCD_U x CDS_U) o MSC) o (R_U x R_U x R_U)",
                                            "raggruppamento a sinistra"),
    ("(SCD_U x SCD_U x CDS_U) o (MSC o (R_U x R_U x R_U))",
                                            "raggruppamento a destra"),
    ("((SCD_U o CDS_U) x SCD_U x SCD_U)",   "fattore Kronecker composto"),
    # forme simboliche effettivamente prodotte dall'Analisi
    ("T = MSC o MSC",                       "prefisso «T =»"),
    ("T = [(R_U x R_U x R_U) o MSC]",       "prefisso e quadre"),
    ("[(SCD_U x SCD_U x DCS_U) o MSC] o [(SCD_U x SCD_U x CDS_U) o MSC]",
                                            "due turni fra quadre"),
    # operatori alternativi e spaziature
    ("MSC∘MSC",                             "composizione Unicode senza spazi"),
    ("MSC@MSC",                             "alias ASCII @"),
    ("MSC  o   MSC",                        "spazi multipli"),
    ("MSC\no\nMSC",                         "a capo fra i termini"),
    ("  MSC  ",                             "spazi ai bordi"),
    ("(SCD_U ⊗ SCD_U ⊗ DCS_U)",             "Kronecker Unicode"),
]

# Sintatticamente valide, ma il risultato non e' una trasformazione di 27:
# entrambi i consumatori devono rifiutarle, e per il motivo giusto.
NON_A_27 = [
    ("SCD_U",                               "generatore di tipo 3 isolato"),
    ("(SCD_U o CDS_U)",                     "composizione di tipo 3"),
    ("DCS_U o DCS_U",                       "tipo 3 senza parentesi"),
]

INVALIDI = [
    # input vuoto
    ("",                                    "stringa vuota"),
    ("   ",                                 "solo spazi"),
    ("T =",                                 "solo il prefisso"),
    # operatore finale / iniziale / doppio
    ("MSC o",                                "operatore finale ASCII"),
    ("MSC ∘",                                "operatore finale Unicode"),
    ("MSC @",                                "operatore finale @"),
    ("o MSC",                                "operatore iniziale"),
    ("MSC o o MSC",                          "operatori consecutivi"),
    ("T = o",                                "prefisso e solo operatore"),
    # parentesi
    ("MSC)",                                 "parentesi eccedente a destra"),
    ("(MSC",                                 "parentesi non chiusa"),
    ("MSC))",                                "due parentesi eccedenti"),
    ("((MSC)",                               "una chiusura mancante"),
    ("()",                                   "parentesi vuote"),
    ("MSC o ()",                             "termine vuoto fra parentesi"),
    ("[MSC",                                 "quadra non chiusa"),
    # token sconosciuti
    ("XYZ",                                  "identificatore sconosciuto"),
    ("MSC o FOO",                            "secondo termine sconosciuto"),
    ("MSC o 27",                             "numero al posto di un atomo"),
    ("MSC &",                                "carattere non previsto"),
    # uso scorretto del Kronecker
    ("MSC x MSC",                            "Kronecker fra tipi 27"),
    ("x MSC",                                "Kronecker iniziale"),
    ("MSC x",                                "Kronecker finale"),
    ("(SCD_U x SCD_U)",                      "due soli fattori"),
    ("(SCD_U x SCD_U x SCD_U x SCD_U)",      "quattro fattori"),
    ("(SCD_U x MSC x SCD_U)",                "fattore di tipo 27"),
    # tipi incompatibili nella composizione
    ("MSC o SCD_U",                          "composizione fra tipi diversi"),
    # giustapposizione senza operatore
    ("MSC MSC",                              "due atomi accostati"),
    ("(SCD_U x SCD_U x CDS_U) MSC",          "blocco e atomo accostati"),
]

# Code che non devono mai essere ignorate in coda a un'espressione valida.
CODE_INVALIDE = [" o", " ∘", ")", "(", "]", " XYZ", " x", " o MSC o"]

BASI_PER_CODA = ["MSC", "I", "J o J", "MSC o MSC",
                 "(SCD_U x SCD_U x CDS_U)",
                 "(SCD_U x SCD_U x CDS_U) o MSC",
                 "T = [(R_U x R_U x R_U) o MSC]",
                 "((MSC))"]


# ═══════════════════════════════ armamentario ═══════════════════════════════

_CTRL = Controller()


def _explorer(testo):
    """Il percorso dell'Explorer: Controller.process."""
    return _CTRL.process(testo)


def _shuffle(testo):
    """Il percorso del Mescolamento: il suo punto d'ingresso storico."""
    vista = object.__new__(ShuffleViewerFrame)
    return vista._validate_and_parse(testo)


def _shuffle_accetta(testo):
    try:
        _shuffle(testo)
        return True
    except (ParseError, ValueError):
        return False


def _componi(a, b):
    """(a ∘ b)[i] = a[b[i]] — riscritta qui, senza importare il motore."""
    return [a[b[i]] for i in range(len(b))]


def _applica_al_mazzo(passi):
    """Oracolo indipendente: applica i passi in ordine cronologico.

    Implementazione minima e locale: la carta in posizione `i` va in posizione
    `perm[i]`. Non usa numpy ne' le funzioni del package.
    """
    mazzo = list(range(27))
    for passo in passi:
        nuovo = [None] * 27
        for posizione, carta in enumerate(mazzo):
            nuovo[passo.permutazione[posizione]] = carta
        assert None not in nuovo
        mazzo = nuovo
    return mazzo


def _inversa(perm):
    inv = [0] * len(perm)
    for i, v in enumerate(perm):
        inv[v] = i
    return inv


def _corpus_generativo():
    """Corpus deterministico di profondita' 1-3, senza dipendenze nuove."""
    atomi = ["MSC", "J", "I", "(SCD_U x SCD_U x CDS_U)", "(R_U x I_3 x DSC_U)"]
    espressioni = list(atomi)
    for a in atomi:
        for b in atomi:
            espressioni.append(f"{a} o {b}")
    for i, a in enumerate(atomi):
        for j, b in enumerate(atomi):
            c = atomi[(i + j) % len(atomi)]
            espressioni.append(f"({a} o {b}) o {c}")
            espressioni.append(f"{a} o ({b} o {c})")
    # varianti di scrittura lecite, applicate in modo deterministico
    varianti = []
    for k, e in enumerate(espressioni):
        if k % 4 == 1:
            varianti.append(e.replace(" o ", " ∘ "))
        elif k % 4 == 2:
            varianti.append(e.replace(" o ", "@"))
        elif k % 4 == 3:
            varianti.append(f"T = [{e}]")
    return espressioni + varianti


GENERATIVO = _corpus_generativo()


def _explorer_accetta(testo):
    return bool(_CTRL.process(testo)["ok"])


def _mescolamento_accetta(testo):
    vista = object.__new__(ShuffleViewerFrame)
    try:
        vista._validate_and_parse(testo)
        return True
    except Exception:
        return False


def _discordi(espressioni):
    """Espressioni su cui i due consumatori non sono d'accordo."""
    return [(t, _explorer_accetta(t), _mescolamento_accetta(t))
            for t in espressioni
            if _explorer_accetta(t) != _mescolamento_accetta(t)]


# ═══════════════════════════════ il corpus ══════════════════════════════════

def test_corpus_ben_formato():
    testi = [t for t, _ in VALIDI] + [t for t, _ in NON_A_27] + \
            [t for t, _ in INVALIDI]
    assert len(testi) == len(set(testi)), "espressioni duplicate nel corpus"
    assert len(VALIDI) >= 25 and len(INVALIDI) >= 25
    assert len(GENERATIVO) > 100


# ═════════════════════════ B07 — la divergenza ══════════════════════════════

@pytest.mark.xfail(strict=True, reason="B07: il Mescolamento non conosce I, J "
                                       "ne' i fattori Kronecker composti")
def test_b07_ogni_espressione_valida_e_accettata_da_entrambi():
    assert _discordi([t for t, _ in VALIDI]) == []


@pytest.mark.xfail(strict=True, reason="B07: il Mescolamento cancella "
                                       "l'operatore finale e le parentesi spaiate")
def test_b07_ogni_espressione_invalida_e_rifiutata_da_entrambi():
    assert _discordi([t for t, _ in INVALIDI]) == []


@pytest.mark.xfail(strict=True, reason="B07: il Mescolamento accetta un "
                                       "prefisso valido ignorando la coda")
def test_b07_nessuna_coda_invalida_viene_ignorata():
    guaste = [base + coda for base in BASI_PER_CODA for coda in CODE_INVALIDE]
    accettate = [t for t in guaste
                 if _explorer_accetta(t) or _mescolamento_accetta(t)]
    assert accettate == []

def test_b07_le_forme_di_tipo_3_sono_rifiutate_da_entrambi():
    """Su queste i due sono gia' d'accordo, per ragioni diverse.

    L'Explorer le parsa e poi rifiuta il risultato di tipo 3; il Mescolamento
    non le riconosce proprio. L'accordo va conservato anche dopo l'unificazione.
    """
    assert _discordi([t for t, _ in NON_A_27]) == []
    for testo, _ in NON_A_27:
        assert not _explorer_accetta(testo)


# ═════════════════════ semantica: valutazione e traccia ═════════════════════

@pytest.mark.parametrize("testo,nota", VALIDI, ids=[n for _, n in VALIDI])
def test_valutazione_e_traccia_sono_deterministiche(testo, nota):
    primo, secondo = traccia_simulazione(testo), traccia_simulazione(testo)
    assert primo == secondo
    assert permutazione_di(testo) == permutazione_di(testo)
    assert list(primo.permutazione) == permutazione_di(testo)


@pytest.mark.parametrize("testo,nota", VALIDI, ids=[n for _, n in VALIDI])
def test_la_traccia_fattorizza_la_permutazione(testo, nota):
    """Componendo i passi in ordine testuale si riottiene T."""
    traccia = traccia_simulazione(testo)
    perms = [list(p.permutazione) for p in reversed(traccia.passi)]
    composta = perms[0]
    for p in perms[1:]:
        composta = _componi(composta, p)
    assert composta == list(traccia.permutazione)
    assert composta == _explorer(testo)["perm"]


def test_ordine_cronologico_da_destra_a_sinistra():
    traccia = traccia_simulazione("(SCD_U x SCD_U x CDS_U) o MSC o (R_U x R_U x R_U)")
    assert [p.etichetta for p in traccia] == [
        "(R_U x R_U x R_U)", "MSC", "(SCD_U x SCD_U x CDS_U)"]
    assert [p.indice for p in traccia] == [0, 1, 2]
    assert all(p.totale == 3 for p in traccia)


def test_il_raggruppamento_non_cambia_la_simulazione():
    """L'associativita' vale anche per la traccia, non solo per il prodotto."""
    a = traccia_simulazione("((SCD_U x SCD_U x CDS_U) o MSC) o (R_U x R_U x R_U)")
    b = traccia_simulazione("(SCD_U x SCD_U x CDS_U) o (MSC o (R_U x R_U x R_U))")
    c = traccia_simulazione("(SCD_U x SCD_U x CDS_U) o MSC o (R_U x R_U x R_U)")
    assert a == b == c


def test_gli_alias_storici_restano_visibili():
    """R_U e I_3 vengono normalizzati per la matematica, non per l'occhio."""
    traccia = traccia_simulazione("(R_U x I_3 x DSC_U) o MSC")
    assert traccia.passi[1].etichetta == "(R_U x I_3 x DSC_U)"
    assert list(traccia.passi[1].permutazione) == \
        permutazione_di("(DCS_U x SCD_U x DSC_U)")


def test_composizione_invariata():
    """(a ∘ b)[i] = a[b[i]], con a e b presi dagli atomi del linguaggio."""
    msc = permutazione_di("MSC")
    j = permutazione_di("J")
    assert permutazione_di("MSC o J") == _componi(msc, j)
    assert permutazione_di("J o MSC") == _componi(j, msc)
    assert permutazione_di("MSC o MSC o MSC") == list(range(27))


def test_la_traccia_deriva_dalla_ast():
    """Stessa traccia partendo dal testo o dall'AST gia' prodotta."""
    for testo, _ in VALIDI:
        assert traccia_simulazione(analizza(testo)) == traccia_simulazione(testo)


def test_il_prefisso_t_appartiene_al_parser():
    """«T =» e' tollerato dalla grammatica, non da ogni chiamante per conto suo."""
    assert analizza("T = MSC") is not None
    assert permutazione_di("T = MSC o MSC") == permutazione_di("MSC o MSC")
    assert traccia_simulazione("T = MSC") == traccia_simulazione("MSC")


# ═══════════════════════════ architettura di E ══════════════════════════════

def _albero(percorso):
    return ast.parse(pathlib.Path(percorso).read_text(encoding="utf-8"))


def test_un_solo_parser_autorevole():
    """Nel package esiste una sola grammatica: quella di core/algebra.py."""
    proprietari = []
    for sorgente in sorted((RADICE / "gioco27").rglob("*.py")):
        albero = _albero(sorgente)
        classi = {n.name for n in ast.walk(albero) if isinstance(n, ast.ClassDef)}
        if {"Lexer", "Parser"} & classi:
            proprietari.append(sorgente.relative_to(RADICE).as_posix())
    assert proprietari == ["gioco27/core/algebra.py"], proprietari


def test_il_linguaggio_non_dipende_da_gui_tk_filesystem():
    """Le classi del linguaggio non toccano widget ne' file."""
    albero = _albero(RADICE / "gioco27" / "core" / "algebra.py")
    vietati = {"tk", "tkinter", "ttk", "filedialog", "messagebox", "open",
               "os", "pathlib", "csv", "openpyxl"}
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.ClassDef) and nodo.name in (
                "Token", "Lexer", "Parser", "SymbolicExpr", "Evaluator"):
            nomi = {n.id for n in ast.walk(nodo) if isinstance(n, ast.Name)}
            nomi |= {n.attr for n in ast.walk(nodo) if isinstance(n, ast.Attribute)}
            assert not (nomi & vietati), (nodo.name, sorted(nomi & vietati))

    modulo = _albero(RADICE / "gioco27" / "core" / "espressione.py")
    moduli = [n.module for n in ast.walk(modulo) if isinstance(n, ast.ImportFrom)]
    moduli += [a.name for n in ast.walk(modulo) if isinstance(n, ast.Import)
               for a in n.names]
    # `ImportFrom.module` non contiene i punti del livello relativo:
    # `from ..i18n import tr` compare come "i18n".
    assert set(moduli) == {"dataclasses", "typing", "i18n", "algebra"}, moduli


def test_importare_il_linguaggio_non_importa_tkinter():
    """Prova a runtime, non solo sul sorgente."""
    import subprocess
    import sys
    codice = ("import sys; import gioco27.core.espressione as E; "
              "print(any(m.startswith('tkinter') for m in sys.modules), "
              "any(m.startswith('gioco27.gui') for m in sys.modules))")
    esito = subprocess.run([sys.executable, "-c", codice], cwd=str(RADICE),
                           capture_output=True, text=True, timeout=120)
    assert esito.returncode == 0, esito.stderr
    assert esito.stdout.split() == ["False", "False"], esito.stdout


def test_numpy_resta_fuori_dal_contratto():
    """La traccia e' fatta di tuple di int: chi la consuma non deve numpy."""
    traccia = traccia_simulazione("MSC o (R_U x R_U x R_U)")
    for passo in traccia:
        assert isinstance(passo.permutazione, tuple)
        assert isinstance(passo.mazzo, tuple)
        assert all(isinstance(v, int) and not isinstance(v, np.integer)
                   for v in passo.permutazione)
