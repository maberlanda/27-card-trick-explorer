"""
Nomi doppi: I_3/SCD_U e R_U/DCS_U sono la stessa permutazione.

    [0,1,2]  =  SCD_U (raccolta identica)  =  I_3 (nessuna inversione)
    [2,1,0]  =  DCS_U (raccolta S↔D)       =  R_U (inversione completa)

`compose3` restituisce l'identità come **I_3** (nome J) e l'inversione come
**DCS_U** (nome P). Non è uniforme, ed è una scelta: la funzione vede solo il
risultato, non da dove viene, e una raccolta P genuinamente DCS_U è
indistinguibile da un'inversione J.

Questi test pinnano la convenzione: se un giorno si decide di uniformarla,
falliscono e obbligano a farlo consapevolmente, aggiornando anche la Guida.
"""

from gioco27.core.permutations import _ALL3, compose3, simplify3


def test_sono_davvero_la_stessa_permutazione():
    assert _ALL3["SCD_U"] == _ALL3["I_3"] == [0, 1, 2]
    assert _ALL3["DCS_U"] == _ALL3["R_U"] == [2, 1, 0]


def test_identita_esce_come_I_3():
    """Per l'identità si preferisce il nome J."""
    for a, b in (("SCD_U", "SCD_U"), ("I_3", "I_3"), ("SCD_U", "I_3"),
                 ("R_U", "R_U"), ("DCS_U", "DCS_U")):
        assert compose3(a, b) == "I_3", f"{a} ∘ {b}"


def test_inversione_esce_come_DCS_U():
    """
    Per l'inversione si preferisce il nome P: è il primo che compare nella
    tavola. Sorprende chi imposta J = R_U e ritrova DCS_U nell'etichetta, ma
    non è un errore — è la stessa permutazione.
    """
    for a, b in (("I_3", "R_U"), ("R_U", "I_3"), ("DCS_U", "SCD_U"),
                 ("SCD_U", "DCS_U")):
        assert compose3(a, b) == "DCS_U", f"{a} ∘ {b}"


def test_simplify3_non_e_simmetrica():
    """SCD_U → I_3, ma DCS_U resta DCS_U: l'asimmetria è deliberata."""
    assert simplify3("SCD_U") == "I_3"
    assert simplify3("DCS_U") == "DCS_U"
    assert simplify3("R_U") == "R_U"


def test_uscita_sempre_in_un_nome_conosciuto():
    """Qualunque composizione produce un nome della tavola."""
    nomi = list(_ALL3)
    for a in nomi:
        for b in nomi:
            assert compose3(a, b) in _ALL3


def test_composizione_corretta_a_prescindere_dal_nome():
    """
    Il controllo che conta: la PERMUTAZIONE è giusta, qualunque nome le venga
    dato. L'ambiguità è solo di etichetta.
    """
    nomi = list(_ALL3)
    for a in nomi:
        for b in nomi:
            pa, pb = _ALL3[a], _ALL3[b]
            atteso = [pa[pb[i]] for i in range(3)]
            assert _ALL3[compose3(a, b)] == atteso, f"{a} ∘ {b}"


def test_la_convenzione_e_documentata():
    """La nota nel codice deve esistere: senza, l'alias è una trappola."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "gioco27" / "core" / "permutations.py").read_text(encoding="utf-8")
    assert "NOMI DOPPI" in src
    for nome in ("SCD_U", "I_3", "DCS_U", "R_U"):
        assert nome in src.split("NOMI DOPPI", 1)[1][:2000], \
            f"la nota non menziona {nome}"
