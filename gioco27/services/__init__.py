"""Servizi applicativi: orchestrano il dominio, non lo reimplementano.

Compartimento G1. Un servizio di questo package:

* riceve dati semplici (filtri, percorsi) e restituisce modelli applicativi;
* non importa nulla da `gioco27.gui` e non tocca widget;
* e' sincrono e non sa se qualcuno lo sta chiamando da un thread;
* riusa gli algoritmi di `gioco27.core` senza riscriverli.

La direzione delle dipendenze e' `gui → services → core`, e un test
architetturale la verifica.
"""

from .analisi import ServizioAnalisi, servizio_analisi
from .lavoro import Revisioni
from .modelli import Provenienza, RisultatoAnalisi
from .procedure import (ConfrontoProcedure, Costo, FamigliaGesti,
                        FibraBersaglio, ProceduraGioco, ServizioProcedure,
                        servizio_procedure)

__all__ = ["ServizioAnalisi", "servizio_analisi", "Provenienza",
           "RisultatoAnalisi", "Revisioni",
           # I1: procedure canoniche, relazioni e strategie
           "ProceduraGioco", "Costo", "FamigliaGesti", "FibraBersaglio",
           "ConfrontoProcedure", "ServizioProcedure", "servizio_procedure"]
