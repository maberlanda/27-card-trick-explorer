"""Compartimento F — B05: l'analisi accetta qualunque cosa le si dia.

Questo file arriva **prima** della correzione e ne fissa la misura. Gli
ingressi qui sotto non sono inventati: sono le forme che il programma produce
(il CSV COMBINAZIONI di `write_csv`) e quelle che un file corrotto o di un'altra
origine puo' avere.

Oggi `analizza_righe` legge `T_permutazione` con un `int()` dentro un
`try/except ValueError: continue` — quindi una permutazione impossibile passa e
una riga illeggibile sparisce — e `analizza_csv` cerca le colonne per
sottostringa, cosi' un'intestazione sconosciuta produce zero risultati invece di
un errore di schema.

Le tre prove sono marcate `xfail(strict=True)`: falliscono adesso e dovranno
smettere di fallire quando la validazione esistera'. Con `strict` il test
diventa rosso anche se passa per sbaglio, quindi il marcatore non puo' essere
dimenticato.
"""
import pytest

from gioco27.core.algebra import analizza_csv, analizza_righe

IDENTITA = "[" + ",".join(str(i) for i in range(27)) + "]"

#: `T` che non sono permutazioni di 27 elementi distinti in 0..26.
T_INVALIDE = [
    ("[0,0,99]",                                    "duplicati e fuori range"),
    ("[" + ",".join(str(i) for i in range(26)) + "]",            "26 elementi"),
    ("[" + ",".join(str(i) for i in range(28)) + "]",            "28 elementi"),
    ("[-1," + ",".join(str(i) for i in range(1, 27)) + "]",         "negativo"),
    ("[99," + ",".join(str(i) for i in range(1, 27)) + "]",        "valore 99"),
    ("[0,0," + ",".join(str(i) for i in range(2, 27)) + "]",       "duplicato"),
    ("[0,1,2]",                                                "solo 3 valori"),
]

#: `T` illeggibili: oggi spariscono in silenzio.
T_ILLEGGIBILI = [("[]", "lista vuota"), ("", "campo vuoto"),
                 ("[a,b,c]", "stringhe"),
                 ("[0.0," + ",".join(str(i) for i in range(1, 27)) + "]", "float")]


def _riga(perm):
    return {"Stage0": "", "Stage1": "", "Stage2": "", "T_simbolica": "",
            "T_permutazione": perm}


def test_una_t_valida_entra_nei_risultati():
    risultati = analizza_righe([_riga(IDENTITA)])
    assert len(risultati) == 1 and risultati[0]["perm_str"] == IDENTITA


@pytest.mark.xfail(strict=True, reason="B05: nessuna validazione della T")
def test_b05_le_t_invalide_non_entrano_nei_risultati():
    accettate = [nota for perm, nota in T_INVALIDE
                 if analizza_righe([_riga(perm)])]
    assert accettate == []


@pytest.mark.xfail(strict=True,
                   reason="B05: le righe illeggibili spariscono senza diagnostica")
def test_b05_le_righe_scartate_lasciano_traccia():
    esito = analizza_righe([_riga(IDENTITA)] +
                           [_riga(perm) for perm, _ in T_ILLEGGIBILI])
    assert len(esito) == 1
    assert len(getattr(esito, "scartate", ())) == len(T_ILLEGGIBILI)


@pytest.mark.xfail(strict=True,
                   reason="B05: uno schema sconosciuto vale un'analisi vuota")
def test_b05_uno_schema_sconosciuto_non_e_un_analisi_vuota(tmp_path):
    percorso = tmp_path / "ignoto.csv"
    percorso.write_text('"foo";"bar"\n"1";"2"\n', encoding="utf-8")
    with pytest.raises(Exception):
        analizza_csv(percorso)
