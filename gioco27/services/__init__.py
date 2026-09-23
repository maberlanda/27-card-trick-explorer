"""Servizi applicativi: orchestrano il dominio, non lo reimplementano.

Compartimento G1. Un servizio di questo package:

* riceve dati semplici (filtri, percorsi) e restituisce modelli applicativi;
* non importa nulla da `gioco27.gui` e non tocca widget;
* e' sincrono e non sa se qualcuno lo sta chiamando da un thread;
* riusa gli algoritmi di `gioco27.core` senza riscriverli.

La direzione delle dipendenze e' `gui → services → core`, e un test
architetturale la verifica. Per ora qui vivono i modelli applicativi: i servizi
veri e propri arrivano con l'estrazione dell'analisi.
"""

from .modelli import Provenienza, RisultatoAnalisi

__all__ = ["Provenienza", "RisultatoAnalisi"]
