"""Regressioni B12-B14: temporanei propri e output senza perdite silenziose."""
import csv
import os

import pytest

from gioco27.core import algebra, parallel


@pytest.mark.parametrize("fail", [False, True])
@pytest.mark.parametrize("preexisting", [False, True])
def test_b12_temporaneo_univoco_preserva_file_omonimo(fail, preexisting, tmp_path):
    dest = tmp_path / "atomic.csv"
    neighbor = tmp_path / "atomic.csv.parziale"
    previous = b"originale\x00\xff\r\n"
    neighbor.write_bytes(previous)
    if preexisting:
        dest.write_bytes(b"destinazione precedente")
    owned = None
    try:
        with parallel.atomic_write(dest) as f:
            f.write(b"completo")
            created = set(tmp_path.iterdir()) - {dest, neighbor}
            assert len(created) == 1
            owned = created.pop()
            assert owned.parent == dest.parent
            assert neighbor.read_bytes() == previous
            if preexisting:
                assert dest.read_bytes() == b"destinazione precedente"
            else:
                assert not dest.exists()
            if fail:
                raise KeyError("interruzione")
    except KeyError:
        assert fail
    assert owned is not None and not owned.exists()
    assert neighbor.read_bytes() == previous
    if not fail:
        assert dest.read_bytes() == b"completo"
    elif preexisting:
        assert dest.read_bytes() == b"destinazione precedente"
    else:
        assert not dest.exists()
    assert set(tmp_path.iterdir()) == {neighbor} | ({dest} if preexisting or not fail else set())


@pytest.mark.parametrize("inner_fails", [False, True])
def test_b12_operazioni_sovrapposte_puliscono_solo_il_proprio_temporaneo(
        inner_fails, tmp_path):
    dest = tmp_path / "atomic.csv"
    dest.write_bytes(b"precedente")
    with pytest.raises(RuntimeError, match="esterna"):
        with parallel.atomic_write(dest) as outer:
            outer.write(b"esterna")
            outer_temp, = set(tmp_path.iterdir()) - {dest}
            try:
                with parallel.atomic_write(dest) as inner:
                    inner.write(b"interna")
                    assert len(set(tmp_path.iterdir()) - {dest}) == 2
                    if inner_fails:
                        raise KeyError("interna")
            except KeyError:
                assert inner_fails
            assert outer_temp.exists()
            assert set(tmp_path.iterdir()) == {dest, outer_temp}
            assert dest.read_bytes() == (b"precedente" if inner_fails else b"interna")
            raise RuntimeError("esterna")
    assert set(tmp_path.iterdir()) == {dest}
    assert dest.read_bytes() == (b"precedente" if inner_fails else b"interna")


def test_b12_errore_apertura_chiude_descrittore_e_rimuove_temporaneo(tmp_path, monkeypatch):
    dest = tmp_path / "atomic.csv"
    neighbor = tmp_path / "atomic.csv.parziale"
    neighbor.write_bytes(b"da conservare")
    descriptors = []

    def fail_open(fd, *args, **kwargs):
        descriptors.append(fd)
        raise OSError("apertura fallita")

    monkeypatch.setattr(parallel, "open", fail_open, raising=False)
    with pytest.raises(OSError, match="apertura fallita"):
        with parallel.atomic_write(dest):
            pytest.fail("corpo non raggiungibile")
    assert len(descriptors) == 1
    with pytest.raises(OSError):
        os.fstat(descriptors[0])
    assert set(tmp_path.iterdir()) == {neighbor}
    assert neighbor.read_bytes() == b"da conservare"


def test_b12_errore_replace_preserva_destinazione(tmp_path, monkeypatch):
    dest = tmp_path / "atomic.csv"
    dest.write_bytes(b"precedente")

    def fail_replace(source, target):
        assert os.path.dirname(source) == str(tmp_path)
        assert dest.read_bytes() == b"precedente"
        raise OSError("replace fallito")

    monkeypatch.setattr(parallel.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace fallito"):
        with parallel.atomic_write(dest, "w", encoding="utf-8", newline="") as f:
            f.write("testo completo")
    assert dest.read_bytes() == b"precedente"
    assert set(tmp_path.iterdir()) == {dest}


def _result(formulas):
    return dict(perm_str=str(list(range(27))), simboliche=formulas, n_sim=len(formulas))


def test_b13_excel_400_formule_disponibili_dopo_riapertura(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    from gioco27.core.kronecker import find_all_kron_decompositions
    decomps = find_all_kron_decompositions(list(range(27)))[:400]
    formulas = [" o MSC o ".join("({} x {} x {})".format(*stage)
                                for stage in reversed(d)) + " o MSC" for d in decomps]
    joined = " , ".join(formulas)
    assert len(joined) == 38_397
    dest = tmp_path / "out.xlsx"
    algebra.scrivi_excel([_result(formulas)], dest)
    wb = openpyxl.load_workbook(dest)
    try:
        summary = wb["Perm -> Simboliche"]["B2"].value
        assert "32767" in summary and "400" in summary
        assert "Simbolica -> Perm" in summary
        assert len(summary) <= 32767 and summary != joined[:32767]
        rows = list(wb["Simbolica -> Perm"].iter_rows(min_row=2, values_only=True))
        assert len(rows) == 400
        assert [r[0] for r in rows] == sorted(formulas)
        assert all(r[1:] == (_result(formulas)["perm_str"], 400) for r in rows)
        assert wb["Perm -> Simboliche"]["C2"].value == 400
    finally:
        wb.close()


@pytest.mark.parametrize("length", [15, 32766, 32767, 32768])
def test_b13_riepilogo_invariato_fino_alla_soglia(length, tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    # Due espressioni con spazi finali: ciascuna rientra nel limite della cella.
    first_size = (length - 3) // 2
    formulas = ["SCD_U".ljust(first_size), "SCD_U".ljust(length - 3 - first_size)]
    joined = " , ".join(formulas)
    assert len(joined) == length
    dest = tmp_path / "out.xlsx"
    algebra.scrivi_excel([_result(formulas)], dest)
    wb = openpyxl.load_workbook(dest)
    try:
        summary = wb["Perm -> Simboliche"]["B2"].value
        if length <= 32767:
            assert summary == joined
        else:
            assert "oltre il limite" in summary and "Simbolica -> Perm" in summary
        assert len(summary) <= 32767
        assert [row[0] for row in wb["Simbolica -> Perm"].iter_rows(
            min_row=2, values_only=True)] == sorted(formulas)
    finally:
        wb.close()


@pytest.mark.parametrize("preexisting", [False, True])
def test_b14_csv_successo_completo(preexisting, tmp_path):
    dest = tmp_path / "out.csv"
    if preexisting:
        dest.write_bytes(b"precedente")
    result = _result(["SCD_U", "CDS_U"])

    def source():
        assert dest.exists() == preexisting
        if preexisting:
            assert dest.read_bytes() == b"precedente"
        yield result
        if preexisting:
            assert dest.read_bytes() == b"precedente"

    algebra.scrivi_output(source(), dest)
    with dest.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    assert len(rows) == 2
    assert rows[1] == [result["perm_str"], "SCD_U , CDS_U", "2"]
    assert set(tmp_path.iterdir()) == {dest}


@pytest.mark.parametrize("preexisting", [False, True])
@pytest.mark.parametrize("fail_after_row", [False, True])
def test_b14_errore_serializzazione_non_pubblica_parziali(preexisting, fail_after_row, tmp_path):
    dest = tmp_path / "out.csv"
    previous = b"dati validi\x00\xff\r\n"
    neighbor = tmp_path / "out.csv.parziale"
    neighbor.write_bytes(b"file estraneo")
    if preexisting:
        dest.write_bytes(previous)

    def source():
        if fail_after_row:
            yield _result(["SCD_U"])
        if preexisting:
            assert dest.read_bytes() == previous
        else:
            assert not dest.exists()
        yield {"perm_str": "manca simboliche"}

    with pytest.raises(KeyError, match="simboliche"):
        algebra.scrivi_output(source(), dest)
    assert neighbor.read_bytes() == b"file estraneo"
    if preexisting:
        assert dest.read_bytes() == previous
    else:
        assert not dest.exists()
    assert set(tmp_path.iterdir()) == {neighbor} | ({dest} if preexisting else set())
