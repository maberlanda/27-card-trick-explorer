"""Riga di comando batch (compartimento J): niente Tk, niente GUI.

    python -m gioco27 <comando> [opzioni]          (anche: python gioco27.py …)

Comandi:
    validate FILE             schema, convenzioni, digest e ricalcolo
    replay FILE               ricalcola e mostra i risultati (L90: cammino)
    recognize T…              riconoscimento I5 di una permutazione
    property ID [--domain D]  verifica I6 (oppure --all: tutto il catalogo)
    sequence --proc #,m …     successione L90 (oppure --random N --seed S)
    export FILE --csv OUT     dati tabellari di un esperimento verificato
    compare A B               confronto strutturato di due esperimenti
    selftest                  la verifica di integrita' (= --selftest)

Ogni comando accetta ``--json`` (uscita macchina con codici stabili) e
``--lang it|en`` (solo il testo umano). Codici di uscita:

    0  successo / VERIFIED            4  MISMATCH
    1  selftest fallito               5  INCOMPATIBLE_CONVENTION
    2  uso errato (argparse)          6  UNSUPPORTED_SCHEMA
    3  input non valido / CORRUPT     7  errore di scrittura

I file letti sono solo quelli indicati sulla riga di comando: i percorsi o
i nomi dentro un esperimento sono dati e non vengono mai aperti.
"""

from __future__ import annotations

import argparse
import json
import sys

from .i18n import set_language, tr

__all__ = ["main", "COMANDI", "USCITA"]

COMANDI = ("validate", "replay", "recognize", "property", "sequence", "export",
           "compare", "selftest")

USCITA = {"OK": 0, "SELFTEST": 1, "USAGE": 2, "INVALID": 3, "MISMATCH": 4,
          "INCOMPATIBLE_CONVENTION": 5, "UNSUPPORTED_SCHEMA": 6, "WRITE_ERROR": 7}


def _codice_uscita(stato) -> int:
    from .services.esperimento import Stato
    return {Stato.VERIFIED: 0, Stato.MISMATCH: 4, Stato.INCOMPATIBLE_CONVENTION: 5,
            Stato.UNSUPPORTED_SCHEMA: 6, Stato.CORRUPT: 3}[stato]


class _Uscita:
    def __init__(self, comando, come_json, flusso):
        self.comando, self.json, self.flusso = comando, come_json, flusso

    def fine(self, codice, stato, risultato=None, messaggio=""):
        if self.json:
            print(json.dumps({"command": self.comando, "status": stato, "exit_code": codice,
                              "result": risultato}, ensure_ascii=False, sort_keys=True),
                  file=self.flusso)
        elif messaggio:
            print(messaggio, file=self.flusso)
        return codice


def _parser():
    p = argparse.ArgumentParser(prog="python -m gioco27",
                                description=tr("cli.description"))
    sub = p.add_subparsers(dest="comando", metavar="{" + ",".join(COMANDI) + "}")

    def comune(sp):
        sp.add_argument("--json", action="store_true", help=tr("cli.help.json"))
        sp.add_argument("--lang", choices=("it", "en"), default=None)

    sp = sub.add_parser("validate", help=tr("cli.help.validate"), description=tr("cli.help.validate"))
    sp.add_argument("file")
    comune(sp)
    sp = sub.add_parser("replay", help=tr("cli.help.replay"), description=tr("cli.help.replay"))
    sp.add_argument("file")
    comune(sp)
    sp = sub.add_parser("recognize", help=tr("cli.help.recognize"), description=tr("cli.help.recognize"))
    sp.add_argument("T", nargs="+")
    sp.add_argument("--out")
    comune(sp)
    sp = sub.add_parser("property", help=tr("cli.help.property"), description=tr("cli.help.property"))
    sp.add_argument("id", nargs="?")
    sp.add_argument("--domain")
    sp.add_argument("--all", action="store_true")
    sp.add_argument("--out")
    sp.add_argument("--csv")
    comune(sp)
    sp = sub.add_parser("sequence", help=tr("cli.help.sequence"), description=tr("cli.help.sequence"))
    sp.add_argument("--proc", nargs="+", action="extend", default=[], help="#,m")
    sp.add_argument("--random", type=int)
    sp.add_argument("--seed", type=int)
    sp.add_argument("--out")
    sp.add_argument("--csv")
    comune(sp)
    sp = sub.add_parser("export", help=tr("cli.help.export"), description=tr("cli.help.export"))
    sp.add_argument("file")
    sp.add_argument("--csv", required=True)
    sp.add_argument("--what", required=True,
                    choices=("successione", "replay", "cronologia", "proprieta", "mapping"))
    comune(sp)
    sp = sub.add_parser("compare", help=tr("cli.help.compare"), description=tr("cli.help.compare"))
    sp.add_argument("a")
    sp.add_argument("b")
    comune(sp)
    sp = sub.add_parser("selftest", help=tr("cli.help.selftest"), description=tr("cli.help.selftest"))
    comune(sp)
    return p


def _salva(doc, percorso, out):
    from .services import archivio
    try:
        archivio.salva_documento(doc, percorso)
    except OSError:
        return out.fine(USCITA["WRITE_ERROR"], "WRITE_ERROR",
                        messaggio=tr("cli.error.write", path=percorso))
    return None


def _rapporto_json(r):
    return {"stato": r.stato.value, "codice": r.codice,
            "diagnosi": [{"voce": d.voce, "campo": d.campo, "registrato": d.registrato,
                          "ricalcolato": d.ricalcolato} for d in r.diagnosi]}


def _cmd_validate(a, out, replay=False):
    from .services import archivio, esperimento as E
    r = archivio.carica_documento(a.file)
    codice = _codice_uscita(r.stato)
    ris = _rapporto_json(r)
    righe = [tr("cli.status", status=r.stato.value, code=r.codice)]
    righe += [f"  {d.voce} {d.campo}" + ("" if d.registrato is None and d.ricalcolato is None
                                         else f": {d.registrato!r} ≠ {d.ricalcolato!r}")
              for d in r.diagnosi]
    if replay and r.documento is not None and r.stato in (E.Stato.VERIFIED, E.Stato.MISMATCH):
        ris["voci"] = []
        for v in r.documento["voci"]:
            ricalcolo = E.calcola_risultato(v["tipo"], v["input"], r.documento["seed"])
            ris["voci"].append({"strumento": v["strumento"], "risultato": ricalcolo})
            righe.append(f"  [{v['strumento']}] " + json.dumps(ricalcolo, ensure_ascii=False,
                                                              sort_keys=True)[:300])
            if v["tipo"] == "successione":
                s = E._successione_da_input(v["input"], r.documento["seed"])
                ris["replay_inverso"] = [list(x) for x in s.replay_inverso()]
                righe.append("  " + tr("cli.replay.steps", n=s.lunghezza))
    return out.fine(codice, r.stato.value, ris, "\n".join(righe))


def _perm_da_argomenti(valori):
    testo = " ".join(valori).replace(",", " ").replace("[", " ").replace("]", " ")
    return [int(x) for x in testo.split()]


def _cmd_recognize(a, out):
    from .services import esperimento as E
    try:
        T = _perm_da_argomenti(a.T)
        doc = E.crea_documento({"riconoscimento": {"T": T}})
    except (ValueError, E.EsperimentoNonValido):
        return out.fine(USCITA["INVALID"], "INVALID", messaggio=tr("cli.error.permutation"))
    ris = doc["voci"][0]["risultato"]
    if a.out and (errore := _salva(doc, a.out, out)) is not None:
        return errore
    msg = tr("cli.recognize", separable=ris["separabile"], row=ris["numero_tavola"],
             k=ris["classe_estesa"], sums=ris["criterio_somme"])
    return out.fine(0, "OK", ris, msg)


def _cmd_property(a, out):
    from .services import archivio, esperimento as E, laboratorio as lab
    if a.all:
        voci = [E.crea_documento({"laboratorio": {"proprieta": p.id, "dominio": d.value}})
                ["voci"][0] for p in lab.CATALOGO for d in p.domini]
        if a.csv:
            try:
                archivio.scrivi_csv(a.csv, "verifiche_i6", *archivio.righe_proprieta(voci))
            except OSError:
                return out.fine(USCITA["WRITE_ERROR"], "WRITE_ERROR",
                                messaggio=tr("cli.error.write", path=a.csv))
        righe = [f"{v['input']['proprieta']:32} {v['input']['dominio']:9} "
                 f"{v['risultato']['esito']:6} {v['risultato']['metodo']}" for v in voci]
        return out.fine(0, "OK", [{"input": v["input"], "risultato": v["risultato"],
                                   "digest": v["digest"]} for v in voci], "\n".join(righe))
    if not a.id:
        return out.fine(USCITA["INVALID"], "INVALID", messaggio=tr("cli.error.property"))
    try:
        dominio = a.domain or lab.proprieta(a.id).domini[0].value
        doc = E.crea_documento({"laboratorio": {"proprieta": a.id, "dominio": dominio}})
    except (KeyError, E.EsperimentoNonValido):
        return out.fine(USCITA["INVALID"], "INVALID", messaggio=tr("cli.error.property"))
    voce = doc["voci"][0]
    if a.out and (errore := _salva(doc, a.out, out)) is not None:
        return errore
    if a.csv:
        try:
            archivio.scrivi_csv(a.csv, "verifiche_i6", *archivio.righe_proprieta([voce]))
        except OSError:
            return out.fine(USCITA["WRITE_ERROR"], "WRITE_ERROR",
                            messaggio=tr("cli.error.write", path=a.csv))
    r = voce["risultato"]
    msg = tr("cli.property", id=a.id, domain=dominio, outcome=r["esito"], method=r["metodo"],
             checked=r["controllati"])
    return out.fine(0, "OK", {"input": voce["input"], "risultato": r,
                              "digest": voce["digest"]}, msg)


def _cmd_sequence(a, out):
    from .services import archivio, esperimento as E
    from .services.procedure import ProceduraGioco, ProceduraNonValida
    from .services.successione import SuccessioneNonValida, procedure_casuali
    try:
        if a.random is not None:
            if a.seed is None:
                return out.fine(USCITA["INVALID"], "INVALID", messaggio=tr("cli.error.seed"))
            procedure = procedure_casuali(a.random, a.seed)
            gen, seed = {"n": a.random}, a.seed
        else:
            procedure = []
            for voce in a.proc:
                n, m = (int(x) for x in voce.split(","))
                procedure.append(ProceduraGioco.da_identificatore(n, m))
            gen, seed = None, None
        inp = {"procedure": [E.procedura_in_dati(p) for p in procedure],
               "mazzo_iniziale": None, "generatore": gen}
        doc = E.crea_documento({"successione": inp}, seed=seed)
    except (ValueError, ProceduraNonValida, SuccessioneNonValida, E.EsperimentoNonValido):
        return out.fine(USCITA["INVALID"], "INVALID", messaggio=tr("cli.error.sequence"))
    if a.out and (errore := _salva(doc, a.out, out)) is not None:
        return errore
    if a.csv:
        s = E._successione_da_input(inp, seed)
        try:
            archivio.scrivi_csv(a.csv, "successione", *archivio.righe_successione(s))
        except OSError:
            return out.fine(USCITA["WRITE_ERROR"], "WRITE_ERROR",
                            messaggio=tr("cli.error.write", path=a.csv))
    r = doc["voci"][0]["risultato"]
    rit = r["ritorno"]
    msg = tr("cli.sequence", n=len(procedure), row=r["numero_cumulativo"],
             back=" ".join(rit["mescolamenti"]))
    return out.fine(0, "OK", {"input": inp, "risultato": r, "seed": seed}, msg)


def _cmd_export(a, out):
    from .services import archivio, esperimento as E
    r = archivio.carica_documento(a.file)
    if not r.verificato:
        return out.fine(_codice_uscita(r.stato), r.stato.value, _rapporto_json(r),
                        tr("cli.status", status=r.stato.value, code=r.codice))
    doc = r.documento
    voci = {v["strumento"]: v for v in doc["voci"]}
    try:
        if a.what in ("successione", "replay"):
            s = E._successione_da_input(voci["successione"]["input"], doc["seed"])
            dati = (archivio.righe_successione(s) if a.what == "successione"
                    else archivio.righe_replay(s))
        elif a.what == "cronologia":
            cr = doc["cronologia"] or {"eventi": [], "esterni": []}
            dati = archivio.righe_cronologia(cr["eventi"] + cr["esterni"])
        elif a.what == "proprieta":
            dati = archivio.righe_proprieta([voci["laboratorio"]])
        else:
            T = next(v["risultato"].get("T") or v["risultato"].get("cumulativo")
                     for v in doc["voci"] if v["risultato"].get("T") or
                     v["risultato"].get("cumulativo"))
            dati = archivio.righe_mapping(T)
    except (KeyError, StopIteration):
        return out.fine(USCITA["INVALID"], "INVALID", messaggio=tr("cli.error.export"))
    try:
        m = archivio.scrivi_csv(a.csv, a.what, *dati, fonti=doc["fonti"])
    except OSError:
        return out.fine(USCITA["WRITE_ERROR"], "WRITE_ERROR",
                        messaggio=tr("cli.error.write", path=a.csv))
    return out.fine(0, "OK", m, tr("cli.export", path=a.csv, rows=m["righe"]))


def _cmd_compare(a, out):
    from .services import archivio, esperimento as E
    ra, rb = archivio.carica_documento(a.a), archivio.carica_documento(a.b)
    for r in (ra, rb):
        if r.documento is None:
            return out.fine(_codice_uscita(r.stato), r.stato.value, _rapporto_json(r),
                            tr("cli.status", status=r.stato.value, code=r.codice))
    c = E.confronta(ra.documento, rb.documento)
    ris = {"codici": list(c.codici), "verifica": [ra.stato.value, rb.stato.value],
           "dettagli": [{"campo": k, "a": x, "b": y} for k, x, y in c.dettagli]}
    return out.fine(0, "OK", ris, " ".join(c.codici) or "—")


def _cmd_selftest(a, out):
    from .core.gioco_reale import selftest
    try:
        esito = selftest()
    except AssertionError as e:
        return out.fine(USCITA["SELFTEST"], "SELFTEST_FAILED", {"errore": str(e)},
                        f"✗ {e}")
    return out.fine(0, "OK", {k: str(v) for k, v in esito.items()},
                    "\n".join(f"  {k:28s} {v}" for k, v in esito.items()))


def main(argv=None, flusso=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    flusso = flusso or sys.stdout
    for i, x in enumerate(argv):                    # la lingua prima dell'help
        if x == "--lang" and i + 1 < len(argv) and argv[i + 1] in ("it", "en"):
            set_language(argv[i + 1])
    try:
        a = _parser().parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0)
    if a.comando is None:
        _parser().print_help(flusso)
        return USCITA["USAGE"]
    out = _Uscita(a.comando, a.json, flusso)
    comandi = {"validate": _cmd_validate, "recognize": _cmd_recognize,
               "property": _cmd_property, "sequence": _cmd_sequence,
               "export": _cmd_export, "compare": _cmd_compare, "selftest": _cmd_selftest}
    if a.comando == "replay":
        return _cmd_validate(a, out, replay=True)
    return comandi[a.comando](a, out)
