# Gioco delle 27 carte — 4.0.0 (release candidate)

Programma didattico e di ricerca sul trucco delle 27 carte: simula il gioco
fisico carta per carta, ne descrive la matematica (base 3, prodotti di
Kronecker, il mescolamento MSC) e permette di verificarla, esplorarla e
riprodurla. Interfaccia grafica in italiano e inglese, con una **Guida
integrata** organizzata come percorso (scheda «Inizia qui»).

> **Stato:** release candidate 4.0.0, tecnicamente pronta per l'audit finale
> matematico, terminologico e linguistico, che non è ancora stato eseguito.
> Vedi `docs/release/NOTE_VERSIONE_4.0.0.md`.

## Nomenclatura

* **H** — le 216 trasformazioni separabili (la Tavola 216; il libro la chiama
  Gaia, H ≅ S₃³).
* **Γ** — il gruppo esteso di 648 elementi, Γ = H ⊔ H∘MSC ⊔ H∘MSC².
* **S₂₇** — il gruppo ambiente di tutte le permutazioni delle 27 posizioni.
* **1 728** sono le *Procedure* di gioco (6³ mescolamenti × 2³ rovesciamenti),
  non 1 728 trasformazioni distinte: più procedure realizzano la stessa riga
  della Tavola (DP11, § sotto).

## Funzionalità principali

* **Quattro livelli** — Base, Intermedio, Avanzato, Laboratorio: ogni livello
  mostra anche tutto ciò che mostrano i precedenti; cambiare livello non
  cambia i calcoli.
* **Simulatore e Pratica** — il trucco passo per passo, la vista esecutore a
  schermo intero, la pratica con conseguenze reali, errori fisici e recupero,
  lo spettatore con la carta ignota.
* **Tavola 216 e tabellone ternario** — righe, cifre, flussi delle carte,
  procedure equivalenti.
* **Explorer** — espressioni simboliche, forma canonica, decomposizioni,
  riconoscimento di una permutazione, laboratorio di proprietà con dominio
  dichiarato (H, Γ, S₂₇).
* **Esperimenti (🗂 Sessione)** — lo stato scientifico di tutte le viste in un
  file JSON versionato; all'apertura ogni risultato viene **ricalcolato** e il
  file è accettato solo se coincide (VERIFIED); cronologia con
  annulla/ripristina; successioni di procedure con cumulativo e ritorno.
* **Riga di comando** — `validate`, `replay`, `recognize`, `property`,
  `sequence`, `export`, `compare`, `selftest`, senza interfaccia grafica.
* **Export** — CSV, PDF (standard, esteso, dettagliato), Excel, LaTeX, SVG,
  HTML (protocollo), TXT, JSON.

## Requisiti

* **Python 3.10 o superiore** (certificato 3.10–3.14).
* **numpy** — l'unica dipendenza obbligatoria.
* **tkinter / Tk** per l'interfaccia grafica: fa parte di Python
  (Windows/macOS da python.org, opzione «tcl/tk») o del sistema (Linux:
  `sudo apt install python3-tk`); non si installa con pip. Senza Tk funziona
  la riga di comando.
* Facoltative, solo per gli export: `reportlab` (PDF), `openpyxl` (Excel),
  `pypdf` e `pikepdf` (unione e deduplica dei PDF). Senza, il programma parte
  e l'export interessato dice quale libreria manca.

Verifica dell'ambiente:

    python controlla_requisiti.py          # uso
    python controlla_requisiti.py --dev    # anche test e build

## Installazione

Dalla cartella del programma (installazione desktop completa):

    pip install -r requirements.txt

oppure come pacchetto:

    pip install .              # solo numpy
    pip install ".[export]"    # con gli export

Politica: `pyproject.toml` è la fonte delle dipendenze; `requirements.txt`
installa runtime + export, `requirements-dev.txt` aggiunge test e build.

## Avvio

    python gioco27.py          # GUI (oppure: python -m gioco27)
    avvia.bat                  # Windows, doppio clic (usa «py -3», poi «python»)
    gioco27                    # GUI, dopo pip install
    gioco27-cli --help         # riga di comando, dopo pip install
    python -m gioco27 --help   # riga di comando dal sorgente
    python -m gioco27 --version

## Verifica di integrità

    python -m gioco27 --selftest       # anche: gioco27-cli selftest --json

Confronta la simulazione fisica carta per carta con il modello matriciale
(1 728 Procedure), le ancore della tavola del libro (#100, #82), le
statistiche della Tavola date dal libro (App. B.9, § 7.1.5–7.1.6), la
ricostruzione dagli Assi e la soluzione del trucco per tutte le 729 coppie
carta/posizione. Disponibile anche dalla GUI con il pulsante «✔ Verifica».
I controlli non dipendono da `assert` (funzionano anche con `python -O`).

## Fonti matematiche esterne

La struttura matematica è sviluppata nell'articolo **27-Card Tensor
Structure** (https://github.com/maberlanda/27-card-tensor-structure) e nel
libro di riferimento. I due PDF (`LIBRO_MAIN.pdf`, `Articolo.pdf`) sono
**fonti esterne** (DP12): non sono versionati nel repository, non entrano in
sdist, wheel o eseguibile, e il programma non ne ha bisogno per funzionare. Se
sono presenti nella cartella del programma, un esperimento può registrarne
l'impronta SHA-256 come provenienza.

## Decisioni di prodotto della 4.0

* **DP11** — La Tavola è di **216 trasformazioni**. Le 1 728 Procedure
  (mescolamenti × rovesciamenti) sono Procedure, non trasformazioni distinte:
  nella 4.0 non esiste una «Tavola 1 728».
* **DP12** — I PDF delle fonti restano esterni e non tracciati (vedi sopra).

## Costruire dal sorgente

    pip install -r requirements-dev.txt    # test + build
    python -m pytest                       # suite (le prove GUI richiedono un display)
    python -m build                        # sdist e wheel in dist/
    pyinstaller gioco27.spec               # eseguibile: dist/Gioco27/

La ricetta PyInstaller `gioco27.spec` è versionata; include i font DejaVu con
la loro licenza e la licenza del programma, mai i PDF delle fonti. Una build
per Windows va prodotta su Windows.

## Limiti degli export

Con i filtri su «*» le combinazioni sono 1 728³ = 5 159 780 352: gli export
rifiutano subito i lavori oltre 20 milioni di elementi (200.000 per il PDF
dettagliato), spiegando come restringere i filtri. CSV e PDF standard/esteso
generano le combinazioni a flusso; il parallelismo limita i blocchi in volo.
Il PDF dettagliato mantiene invece combinazioni e annotazioni globali per
l'ordinamento e l'elenco delle trasposte. Le strutture interne delle librerie
PDF possono crescere con il numero di pagine: la memoria complessiva non è
costante rispetto alla dimensione dell'export.

La cancellazione è **cooperativa**, nei punti di controllo della generazione,
dell'attesa dei risultati e prima della pubblicazione del file. Non garantisce
un tempo massimo di risposta: un blocco già in esecuzione può terminare prima
dell'arresto. Se la cancellazione è rilevata prima della pubblicazione, la
destinazione precedente resta intatta e il temporaneo viene rimosso.

## Log e dati

Configurazione, cache e log sono in `~/.gioco27/`
(`config.json`, `cache/`, `gioco27.log`).

## Limiti noti

* La 4.0.0 è una **release candidate**: l'audit finale matematico,
  terminologico e linguistico non è ancora stato eseguito.
* Alcuni identificatori interni del codice conservano il nome storico G per il
  gruppo di 216 (per esempio `appartiene_a_G`); i testi per l'utente e gli
  export usano H e Γ.
* L'eseguibile Windows è costruito dalla CI; la build locale verificata è
  quella Linux.

## Documentazione

La Guida completa è integrata nel programma. La documentazione di progetto
(audit, decisioni, chiusure dei compartimenti, note di versione) è in
`docs/` — vedi `docs/README.md`; le note della 4.0.0 sono in
`docs/release/NOTE_VERSIONE_4.0.0.md`.

## Licenza

Copyright © 2026 Maurizio Berlanda.

Il software è distribuito sotto GNU General Public License v3.0 (SPDX
`GPL-3.0-only`, file `LICENSE`). I font DejaVu inclusi in `gioco27/assets/`
hanno una licenza propria, riportata in `gioco27/assets/LICENSE-DejaVu.txt`.
