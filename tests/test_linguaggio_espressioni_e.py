"""Compartimento E — B07: Explorer e Mescolamento non parlano la stessa lingua.

Questo file arriva **prima** della correzione e serve a fissarne la misura. Il
corpus qui sotto e' ricavato dal linguaggio realmente supportato — i simboli
accettati dal Lexer autorevole (`core/algebra.py`), la grammatica
expr/term/factor, i test preesistenti e le stringhe prodotte dall'Analisi — e
non inventa nessuna sintassi nuova.

Lo stesso testo viene dato a entrambi i consumatori:

* Explorer  → `core.algebra.Controller.process`;
* Mescolamento → `gui.shuffle.ShuffleViewerFrame._validate_and_parse`.

Oggi le due risposte divergono. Le tre prove che lo dimostrano sono marcate
`xfail(strict=True)`: falliscono adesso, e il giorno in cui il linguaggio sara'
unico dovranno smettere di fallire — con `strict` il test diventa rosso anche
se passa per sbaglio, quindi nessuno puo' dimenticarsi di toglierle.
"""
import pytest

from gioco27.core.algebra import Controller
from gioco27.gui.shuffle import ShuffleViewerFrame


# ═════════════════════════════ corpus condiviso ═════════════════════════════

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

# Sintatticamente valide, ma il risultato non e' una trasformazione di 27.
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

# Code che non devono mai essere ignorate in fondo a un'espressione valida.
CODE_INVALIDE = [" o", " ∘", ")", "(", "]", " XYZ", " x", " o MSC o"]

BASI_PER_CODA = ["MSC", "I", "J o J", "MSC o MSC",
                 "(SCD_U x SCD_U x CDS_U)",
                 "(SCD_U x SCD_U x CDS_U) o MSC",
                 "T = [(R_U x R_U x R_U) o MSC]",
                 "((MSC))"]


# ═══════════════════════════════ armamentario ═══════════════════════════════

_CTRL = Controller()


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
