# Gioco delle 27 carte

Analisi combinatoria e algebrica del trucco delle 27 carte (gruppo GEN3³,
mescolamento MSC, decomposizioni di Kronecker).

## Avvio

    python gioco27.py        # oppure: python -m gioco27
    avvia.bat                # Windows, doppio click

## Verifica di integrità (v3)

    python -m gioco27 --selftest      # oppure: python gioco27.py --selftest

Confronta la simulazione fisica carta-per-carta con il modello matriciale
(1728 combinazioni), le ancore della tavola del libro (#100, #82), le
statistiche del capitolo 100 e la ricostruzione dagli Assi. Disponibile
anche dalla GUI con il pulsante «✔ Verifica».

Requisiti: Python ≥ 3.9, `numpy`. Facoltativi: `reportlab` (PDF),
`openpyxl` (Excel), `pypdf` (unione PDF). Verifica con:

    python controlla_requisiti.py

## Installazione come pacchetto (facoltativa)

    pip install .[export]    # con le dipendenze di export
    gioco27                  # avvia la GUI

## Eseguibile Windows (facoltativo)

    pip install pyinstaller
    pyinstaller gioco27.spec

Produce `dist/Gioco27/Gioco27.exe`, avviabile senza Python installato.

## Test

    pip install .[dev]
    python -m pytest

## Limiti degli export

Con i filtri su «*» le combinazioni sono 1728³ = 5.159.780.352: gli export
rifiutano subito i lavori oltre 20 milioni di elementi (200.000 per il PDF
dettagliato, che deve tenere tutto in memoria per l'elenco delle trasposte),
spiegando come restringere i filtri. Nessun export materializza le
combinazioni in RAM: sono generate e consumate a flusso.

## Log e dati

Configurazione, cache e log sono in `~/.gioco27/`
(`config.json`, `cache/`, `gioco27.log`).
