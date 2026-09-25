# K0 — Bonifica completa e riordino strutturale del repository

**Stato: chiuso.** Tutti i gate K0-G1…K0-G28 sono soddisfatti (§ 20 bis).
Nessun cambiamento funzionale; packaging, CI, release, versione 4.0.0 e K non
sono stati iniziati.

---

## 1. Stato iniziale

| voce | valore |
|---|---|
| branch | `main` |
| HEAD iniziale | `a98760b` (chiusura J) |
| origin/main | `54445af`, 134 commit avanti (verificato, non assunto) |
| tracciato | pulito |
| non tracciati | `Articolo.pdf`, `LIBRO_MAIN.pdf` (input dell'utente) |
| ignorati presenti | `gioco27.spec`; 4 directory `__pycache__` (bytecode CPython 3.10 e 3.12, in parte obsoleto: mancavano i moduli J) |
| file tracciati | 177 (26 documenti e 1 CSV in radice) |
| baseline | 2326 raccolti · 2324 passati · 1 saltato · 1 fallito noto (Tk 9) |

Verifiche prima di ogni modifica: `git status`, inventario, baseline
matematica 25/25, architettura J 6/6, documentazione D1–D5, pyflakes, J 51/51.

## 2. Metodo

Classificare prima, modificare dopo, cancellare per ultimo (fasi A–H).

* **Inventario**: `git ls-files`, `git ls-files --others` (con e senza
  `--exclude-standard`), `git check-ignore -v`, `find` per cache e residui,
  SHA-256 di ogni file tracciato per i duplicati esatti.
* **Riferimenti**: grafo degli import ricavato dall'AST (relativi compresi)
  per ogni modulo di `gioco27/`, di `tests/` e dei launcher; ricerca testuale
  su tutto il repository (`git grep`) dei nomi di file, dei percorsi aperti
  dai test (`ROOT / …`), di `pyproject.toml`, `gioco27.spec`, README, Guida
  (cataloghi i18n) e documenti.
* **Codice morto**: per ogni nome di primo livello e metodo di classe si
  contano le occorrenze in tutto il sorgente, test compresi (stringhe
  incluse, quindi anche `getattr`/`globals()` con nome letterale). Zero
  riferimenti esterni è **uso non trovato**; diventa **non usato dimostrato**
  solo per nomi privati (`_…`) o classi mai importate, con conferma di
  pyflakes e dei test. Le sezioni della Guida `_sNN`, risolte con
  `globals()[f"_s{n:02d}"]`, sono state riconosciute come vive.
* **Suite** dopo ogni gruppo di modifiche, completa alla fine.

## 3. Classificazione

Inventario completo in `docs/audits/K0_FILE_INVENTORY.csv` (path, category,
tracked, referenced, purpose, action, reason, risk).

| classe | n. | note |
|---|---|---|
| A SOURCE | 76 | tutti i file Python di `gioco27/` hanno almeno un importatore di produzione |
| B TEST | 61 | 60 esistenti + `test_struttura_repository_k0.py` |
| C RUNTIME RESOURCE | 2 | font DejaVu, caricati per percorso |
| D BUILD / CONFIGURATION | 7 | `pyproject.toml`, `requirements*.txt`, `.gitignore`, `.gitattributes`, `conftest.py`, `gioco27.spec` (ignorato) |
| E USER DOCUMENTATION CURRENT | 2 | `README.md`, `LICENSE` |
| F DEVELOPER DOCUMENTATION CURRENT | 1 | `docs/README.md` |
| G PROJECT AUDIT / DESIGN | 7 | `docs/decisions/` (4), `docs/audits/` (3 con l'inventario) |
| H HISTORICAL / CLOSED | 22 | 18 chiusure A…J + K0, 3 note di versione |
| I SCRIPT / TOOL | 3 | `gioco27.py`, `avvia.bat`, `controlla_requisiti.py` |
| L CACHE / TEMPORARY | 4 dir | `__pycache__`, eliminate |
| M LEGACY BUT REQUIRED | 1 | `gioco27/gui/i18n.py` |
| P USER INPUT | 2 | i PDF |
| J, K, N, O, Q | 0 | nessuna fixture binaria, nessun artefatto generato versionato, nessun duplicato, nessun file morto intero, nessun file ignoto |

## 4. Struttura iniziale

    /
    ├── A_BASELINE_CLOSED.md … J_EXPERIMENTS_REPRODUCIBILITY_CLOSED.md   (18)
    ├── GIT_BASELINE_AND_RECONCILIATION.md
    ├── V4_MATHEMATICAL_DIDACTIC_COVERAGE_AUDIT.md, V4_COVERAGE_MATRIX.csv
    ├── V4_PRE_I1_PRODUCT_DECISIONS.md, V4_PRE_I2_VIEW_DECISIONS.md, V4_PRE_I5_DECISIONS.md
    ├── NOTE_VERSIONE_3.md, NOTE_VERSIONE_3.1.1.md, NOTE_VERSIONE_3.1.3.md
    ├── README.md, LICENSE
    ├── pyproject.toml, requirements.txt, requirements-dev.txt
    ├── .gitignore, .gitattributes, conftest.py
    ├── gioco27.py, avvia.bat, controlla_requisiti.py
    ├── gioco27.spec            (ignorato)
    ├── Articolo.pdf, LIBRO_MAIN.pdf   (non tracciati)
    ├── gioco27/  (core, services, gui, assets; + __pycache__ ignorati)
    └── tests/

Quarantatré voci al primo livello (41 file e 2 directory), di cui 27 documenti di progetto.

## 5. Problemi trovati

| # | problema | esito |
|---|---|---|
| P1 | radice con 26 documenti e 1 CSV: storia, decisioni, audit e note di versione indistinguibili dalla documentazione corrente | **risolto**: `docs/` in quattro classi (§ 11) |
| P2 | cache `__pycache__` presenti (ignorate), con bytecode di due interpreti e senza i moduli J | **risolto**: eliminate |
| P3 | seconda classe `Tooltip` in `gui/common.py` mai importata (audit Git baseline: «Due classi Tooltip — CONFERMATA») | **risolto**: rimossa |
| P4 | helper privati `_compose`, `_kron27` in `gui/protocol_dialog.py` senza chiamanti | **risolto**: rimossi |
| P5 | flag privato `_HAS_REPORTLAB` in `core/combinations.py` mai letto | **risolto**: rimosso con l'import di `find_spec` |
| P6 | `gioco27.spec` escluso da `.gitignore` (`*.spec`) ma necessario alla build documentata nel README (N04) | **DEFER** a K (§ 16) |
| P7 | `LICENSE` = GPL v3 e README coerenti, `pyproject.toml` dichiara `license = "Proprietary"` | **DEFER** a K (packaging) |
| P8 | font DejaVu distribuiti senza il file di licenza dei font | **DEFER** a K (packaging/licenze) |
| P9 | `core/analisi.py` (pipeline di analisi F) e `core/analysis.py` (cicli/orbite) con nomi quasi uguali | **DEFER**: rinomina con ~15 importatori, rischio non trascurabile |
| P10 | nomi pubblici senza chiamanti (uso non trovato) | **DEFER** (§ 17) |
| P11 | helper dei test duplicati (`lingua` in 6 file, `_c3` in 3, …) | **DEFER** (§ 14) |
| P12 | identificatori legacy G/H nel core | inventariati (§ 13.2), non migrati |

## 6. File spostati

Tutti con `git mv`, contenuto invariato (rinomine al 100 %):

| da (radice) | a |
|---|---|
| `A_BASELINE_CLOSED.md` … `J_EXPERIMENTS_REPRODUCIBILITY_CLOSED.md` (18) | `docs/history/` |
| `GIT_BASELINE_AND_RECONCILIATION.md` | `docs/decisions/` |
| `V4_PRE_I1_PRODUCT_DECISIONS.md`, `V4_PRE_I2_VIEW_DECISIONS.md`, `V4_PRE_I5_DECISIONS.md` | `docs/decisions/` |
| `V4_MATHEMATICAL_DIDACTIC_COVERAGE_AUDIT.md`, `V4_COVERAGE_MATRIX.csv` | `docs/audits/` |
| `NOTE_VERSIONE_3.md`, `NOTE_VERSIONE_3.1.1.md`, `NOTE_VERSIONE_3.1.3.md` | `docs/release/` |

Totale: 27 file.

## 7. File rinominati

Nessuno. I nomi dei documenti sono univoci e già citati per nome da codice,
test e da altri documenti: rinominarli avrebbe rotto la tracciabilità senza
migliorare la comprensione. I nomi dei moduli vicini (P9) sono rinviati.

## 8. File eliminati

Nessun file tracciato è stato eliminato. Eliminati:

| elemento | perché inutile | verifica | sostituto |
|---|---|---|---|
| 4 directory `__pycache__` (ignorate) | bytecode generato, rigenerabile, di interpreti diversi | ignorate da `.gitignore`, mai tracciate | rigenerato da Python a richiesta |
| `gui/common.py`: `class Tooltip` + `_GEN3_DESCRIPTIONS` (127 righe) | nessun importatore: tutte le viste usano `gui/tooltip.py` | grafo AST degli import (produzione, test, launcher): 0; `git grep "common.Tooltip"`, `attach_gen3`, `attach_text_tag`: solo definizione; pyflakes pulito; suite verde | `gui/tooltip.py` (H2: una sola classe, anche da tastiera) |
| `gui/protocol_dialog.py`: `_compose`, `_kron27` | helper privati senza chiamanti | nomi presenti solo nella definizione in tutto il repository; suite verde | il documento usa `_protocol_perm` e il core |
| `core/combinations.py`: `_HAS_REPORTLAB` e `from importlib.util import find_spec` | flag privato mai letto | nome presente solo nella definizione; `find_spec` usato solo lì | la disponibilità di reportlab è verificata dove serve, all'export |

Un nuovo test impedisce il ritorno della seconda classe `Tooltip`.

## 9. Duplicati

* **Duplicati esatti** (SHA-256 identico) fra i 177 file tracciati: **nessuno**.
* **Nomi sospetti** (`_1`, `(1)`, `copy`, `old`, `bak`, `tmp`, `draft`): **nessuno**.
* **Documenti**: nessuna coppia con lo stesso contenuto; le tre note di
  versione sono tappe diverse, non copie.
* **Codice**: la sola duplicazione eliminata è la classe `Tooltip`. Le
  tabelle GEN3/MSC e le inverse ripetute in più moduli del core restano:
  la baseline Git le documenta come **oracoli indipendenti** usati dai test.

## 10. Cache e residui

Cercati in tutto l'albero (esclusa `.git`): `__pycache__`, `*.pyc`,
`.pytest_cache`, `.coverage*`, `htmlcov`, `build/`, `dist/`, `*.egg-info`,
output PyInstaller, `*.log`, `*.tmp`, `*.bak`, `*~`, temporanei
`.gioco27-*`/`*.parziale`, file vuoti, directory vuote.

| categoria | presenti | tracciati | esito |
|---|---|---|---|
| `__pycache__` / `*.pyc` | 4 dir | no | eliminati |
| tutti gli altri | 0 | 0 | — |
| lock residui in `.git` (`*.lock`, `tmp_obj_*`) | ripuliti dopo ogni commit | — | — |

I test girano con `-B`/`PYTHONDONTWRITEBYTECODE=1` e `-p no:cacheprovider`:
la suite finale non ha ricreato cache (verificato).

## 11. Documentazione

    docs/
    ├── README.md        indice: cosa è corrente, cosa è storia, regole
    ├── audits/          CORRENTE — audit V4 e matrice (letta dai test I7), inventario K0
    ├── decisions/       CORRENTE COME RIFERIMENTO — V4_PRE_I1/I2/I5, baseline Git
    ├── history/         STORICO — chiusure A…J, K0
    └── release/         STORICO — note 3, 3.1.1, 3.1.3

* Documentazione **utente**: Guida integrata (scheda «Guida») e `README.md`.
  Il README ha una nuova sezione «Documentazione» che rimanda a `docs/`.
* Riferimenti **correnti** aggiornati al percorso completo: 4 docstring di
  produzione (`services/procedure.py`, `services/tabellone.py`,
  `services/errori.py`, `gui/pannello_ternario.py`), 10 file di test (2 con
  percorsi aperti davvero: `test_didattica_i7.py` → matrice V4,
  `test_documentazione_d4d5.py` → note 3.1.1; 8 in docstring/commenti).
* Documenti **storici** non riscritti: citano altri documenti per nome file,
  e i nomi restano univoci dentro `docs/`. La regola è scritta in
  `docs/README.md`.
* Nessun link Markdown relativo esisteva nei documenti (verificato), quindi
  nessun link si è rotto.

## 12. Script

| file | classe | destinazione | motivo |
|---|---|---|---|
| `gioco27.py` | A launcher utente | radice | citato da README, Guida (s28), `avvia.bat`, `gioco27.spec` |
| `avvia.bat` | A launcher utente | radice | doppio clic su Windows accanto a `gioco27.py` |
| `controlla_requisiti.py` | B diagnostica per l'utente | radice | citato da README e Guida; testato da `test_guida_allineata`, `test_static` |
| `conftest.py` | configurazione dei test | radice | deve stare accanto al package |

Non esistono script di manutenzione, build/release, helper temporanei o
script morti: **nessuna cartella `scripts/` o `tools/`** è stata creata
(sarebbe stata vuota).

## 13. Package

### 13.1 Moduli

Tutti i 77 file Python del package (76 A + `gui/i18n.py`) hanno almeno un importatore di produzione (nessun modulo
orfano, nessun file vuoto). Colonna «importato da» = file di produzione /
file di test che lo importano.

| modulo | layer | righe | responsabilità | importato da | API | legacy | cleanup |
|---|---|---|---|---|---|---|---|
| `__init__.py` | package | 2 | Package gioco27 — Gioco delle 27 carte | 5 / 11 | interna | — | — |
| `__main__.py` | package | 44 | Punto di ingresso: python -m gioco27  [--selftest / <comando batch> …] ( | 1 / 0 | entry point | — | — |
| `cli.py` | package | 322 | Riga di comando batch (compartimento J): niente Tk, niente GUI | 1 / 0 | entry point | — | — |
| `core/__init__.py` | core | 1 | Nucleo matematico del gioco delle 27 carte | 16 / 40 | interna | — | — |
| `core/algebra.py` | core | 1633 | Motore algebrico e simbolico: Parser, Rewriter, Evaluator, Controller | 7 / 20 | interna | — | DEFER (§ 17) |
| `core/analisi.py` | core | 502 | Pipeline dell'analisi: schema, validazione, piano, aggregazione | 3 / 7 | interna | nome (P9) | DEFER (P9) |
| `core/analysis.py` | core | 327 | Analisi matematica del gruppo: cicli, ordine, orbite, distribuzione | 5 / 5 | interna | nome (P9) | DEFER (P9) |
| `core/cache.py` | core | 206 | Cache su disco per le decomposizioni Kronecker | 2 / 3 | interna | — | — |
| `core/combinations.py` | core | 752 | Generazione e conteggio combinazioni filtrate; export PDF/CSV | 6 / 14 | interna | — | fatto: flag morto |
| `core/config.py` | core | 209 | Configurazione persistente salvata in ~/.gioco27/config.json | 6 / 7 | interna | — | — |
| `core/constants.py` | core | 50 | Costanti simboliche del gioco delle 27 carte | 12 / 14 | interna | — | — |
| `core/detail.py` | core | 128 | Dati di dettaglio per l'export PDF "stile-C" (elenco_disposizioni) | 1 / 3 | interna | — | — |
| `core/detail_pdf.py` | core | 961 | Export PDF dettagliato — riproduzione fedele del layout HTML del program | 1 / 13 | interna | — | — |
| `core/dominio.py` | core | 168 | Contratti del dominio matematico: validazione degli ingressi e glossario | 11 / 6 | interna | — | — |
| `core/espressione.py` | core | 210 | Linguaggio delle espressioni: un solo ingresso da testo ad AST e a tracc | 2 / 2 | interna | — | — |
| `core/export_analisi.py` | core | 97 | Export dei risultati dell'analisi: CSV e Excel | 2 / 0 | interna | — | — |
| `core/export_combinazioni.py` | core | 166 | Export CSV del dominio delle combinazioni: orchestrazione, non matematic | 1 / 2 | interna | — | — |
| `core/gioco_reale.py` | core | 467 | gioco_reale.py — Il gioco fisico delle 27 carte | 20 / 28 | interna | — | DEFER (§ 17) |
| `core/group_theory.py` | core | 199 | Analisi algebrica del gruppo G = GEN3 x GEN3 x GEN3  (/G/ = 216) | 3 / 6 | interna | G legacy (§ 13.2) | — |
| `core/kronecker.py` | core | 357 | Ricerca vettorizzata di tutte le decomposizioni Kronecker di T^-1 | 7 / 8 | interna | G/H legacy (§ 13.2) | — |
| `core/log.py` | core | 47 | Logging centralizzato su ~/.gioco27/gioco27.log | 15 / 0 | interna | — | — |
| `core/parallel.py` | core | 508 | Infrastruttura comune per gli export massivi (CSV, PDF, PDF dettagliato) | 18 / 12 | interna | — | — |
| `core/pdfgrid.py` | core | 152 | Disegno efficiente delle matrici di permutazione sui PDF | 2 / 1 | interna | — | — |
| `core/pdfmerge.py` | core | 237 | Fusione dei PDF parziali prodotti dai processi figli | 2 / 2 | interna | — | — |
| `core/permutations.py` | core | 450 | Utilità sulle permutazioni: perm_to_mat3, build_P27, build_J27, | 10 / 17 | interna | — | — |
| `gui/__init__.py` | gui | 1 | Componenti GUI del gioco delle 27 carte | 5 / 21 | interna | — | — |
| `gui/analysis_tab.py` | gui | 823 | Tab "📊 Analisi" — molteplicità delle permutazioni e relativi export | 1 / 8 | interna | — | — |
| `gui/app.py` | gui | 1448 | App: finestra principale e orchestrazione di tutti i tab | 1 / 17 | interna | — | — |
| `gui/barra.py` | gui | 208 | Barre di azioni che vanno a capo invece di uscire dalla finestra | 1 / 0 | interna | — | — |
| `gui/cayley_dialog.py` | gui | 355 | CayleyDialog: calcolatore interattivo di prodotti in G = GEN3^3 | 1 / 0 | interna | — | — |
| `gui/common.py` | gui | 246 | Widget e tag tkinter condivisi tra tutti i moduli GUI | 9 / 5 | interna | — | fatto: Tooltip duplicato rimosso |
| `gui/conjugacy_dialog.py` | gui | 380 | ConjugacyDialog: mostra le classi di coniugio e il centro di GEN3^3 | 1 / 2 | interna | — | — |
| `gui/cycles_tab.py` | gui | 339 | Tab "🔄 Cicli e Ordine" | 1 / 1 | interna | — | — |
| `gui/decomposition.py` | gui | 597 | DecompositionDialog: cerca e mostra tutte le decomposizioni di T o T^-1, | 1 / 3 | interna | — | — |
| `gui/distribution_tab.py` | gui | 338 | Tab "📊 Distribuzione" | 1 / 3 | interna | — | — |
| `gui/errori.py` | gui | 204 | Come dire all'utente cio' che il core ha constatato | 8 / 3 | interna | — | — |
| `gui/explorer_tab.py` | gui | 928 | Tab "🔬 Explorer" — analisi simbolica, traccia di riscrittura, forma cano | 1 / 5 | interna | — | — |
| `gui/export_dialog.py` | gui | 346 | ExportDialog — Esportazione per il libretto | 1 / 3 | interna | — | — |
| `gui/export_group_dialog.py` | gui | 628 | Export LaTeX / SVG per il gruppo G = GEN3^3 | 2 / 2 | interna | — | — |
| `gui/filter_frame.py` | gui | 371 | FilterFrame: selettore combinazioni P/J per ogni stadio | 1 / 3 | interna | — | — |
| `gui/glossary.py` | gui | 111 | Testi della scheda «Inizia qui», glossario e aiuti delle schede | 3 / 3 | interna | — | DEFER (§ 17) |
| `gui/guide.py` | gui | 851 | Contenuto della Guida / How-To del Gioco delle 27 carte | 1 / 7 | interna | — | DEFER (§ 17) |
| `gui/help_banner.py` | gui | 73 | HelpBanner: banner d'aiuto riusabile da mettere in cima a schede e dialo | 4 / 1 | interna | — | — |
| `gui/i18n.py` | gui | 27 | Adattatore di compatibilita': il catalogo i18n vive in gioco27.i18n | 29 / 6 | interna | re-export (A2) | — |
| `gui/laboratorio_tab.py` | gui | 409 | Explorer → «Laboratorio» (compartimento I6) | 1 / 2 | interna | — | — |
| `gui/livelli.py` | gui | 97 | Livelli didattici (DP7, compartimento I7): chi vede che cosa | 5 / 2 | interna | — | — |
| `gui/onboarding_tab.py` | gui | 150 | Scheda "🚀 Inizia qui": orientamento rapido, azioni rapide e glossario | 1 / 1 | interna | — | — |
| `gui/pannello_ternario.py` | gui | 616 | Pannello ternario della Tavola (compartimento I2) | 1 / 0 | interna | — | — |
| `gui/pratica_reale.py` | gui | 331 | Pratica con conseguenze reali (compartimento I3, D-I3-4/5/6) | 1 / 0 | interna | — | — |
| `gui/presentation.py` | gui | 193 | PresentationWindow — "Vista esecutore" a schermo intero | 1 / 1 | interna | — | — |
| `gui/preview_tab.py` | gui | 212 | Tab "🔍 Anteprima" — calcolo di una singola combinazione al volo | 1 / 3 | interna | — | — |
| `gui/protocol_dialog.py` | gui | 568 | ProtocolDialog: genera e apre nel browser un documento HTML stampabile, | 1 / 5 | interna | — | fatto: 2 helper morti |
| `gui/riconoscimento_tab.py` | gui | 466 | Explorer → «Riconoscimento» (compartimento I5) | 1 / 2 | interna | — | — |
| `gui/scorrimento.py` | gui | 196 | Un'area che scorre quando il contenuto non ci sta, e non scorre quando c | 2 / 0 | interna | — | — |
| `gui/sessione_tab.py` | gui | 552 | Sessione, cronologia, undo/redo e successione L90 (compartimento J) | 1 / 1 | interna | — | — |
| `gui/shuffle.py` | gui | 665 | ShuffleViewerFrame: visualizzatore animato del mescolamento | 1 / 5 | interna | — | — |
| `gui/simulator_tab.py` | gui | 831 | Tab "🎩 Simulatore" | 1 / 6 | interna | — | — |
| `gui/spettatore_tab.py` | gui | 355 | Vista «Spettatore (carta ignota)» del Simulatore — compartimento I4 | 1 / 1 | interna | — | — |
| `gui/tavola_tab.py` | gui | 350 | Tab "📚 Tavola 216" — la tavola delle disposizioni semplici del libro | 1 / 4 | interna | — | — |
| `gui/tooltip.py` | gui | 107 | Tooltip leggero per Tkinter (non esiste un widget nativo) | 5 / 1 | interna | — | DEFER (§ 17) |
| `gui/uifont.py` | gui | 49 | Font con nome per i testi di aiuto / note, scalabili dall'utente | 1 / 1 | interna | — | — |
| `i18n.py` | package | 4237 | Minimal runtime localization support for the GUI | 8 / 12 | interna | — | — |
| `services/__init__.py` | services | 25 | Servizi applicativi: orchestrano il dominio, non lo reimplementano | 19 / 24 | pubblica (services) | — | — |
| `services/analisi.py` | services | 167 | Servizio applicativo dell'analisi: orchestrazione, non algoritmi | 1 / 2 | pubblica (services) | — | — |
| `services/archivio.py` | services | 134 | Persistenza degli esperimenti e export interoperabili (compartimento J) | 3 / 1 | pubblica (services) | — | — |
| `services/cronologia.py` | services | 176 | Cronologia dell'applicazione e undo/redo (compartimento J) | 1 / 1 | pubblica (services) | — | — |
| `services/errori.py` | services | 471 | Errori fisici, confronto piano/eseguito e recupero (compartimento I3) | 1 / 1 | pubblica (services) | — | — |
| `services/esperimento.py` | services | 754 | Esperimenti versionati, verificabili e riproducibili (compartimento J) | 5 / 3 | pubblica (services) | — | — |
| `services/laboratorio.py` | services | 1042 | Laboratorio matematico (compartimento I6) | 4 / 2 | pubblica (services) | — | — |
| `services/lavoro.py` | services | 91 | Identita' delle richieste: cio' che distingue «obsoleto» da tutto il res | 1 / 0 | pubblica (services) | — | — |
| `services/modelli.py` | services | 141 | Modelli applicativi condivisi: il risultato di un'analisi | 2 / 3 | pubblica (services) | — | — |
| `services/procedure.py` | services | 460 | Procedure del gioco, relazioni fra procedure e strategie (compartimento  | 11 / 10 | pubblica (services) | — | — |
| `services/riconoscimento.py` | services | 544 | Decodifica e riconoscimento (compartimento I5) | 3 / 4 | pubblica (services) | — | — |
| `services/sessione.py` | services | 123 | Sessione di lavoro J: stato scientifico, annotazioni, presentazione, cro | 1 / 1 | pubblica (services) | — | — |
| `services/spettatore.py` | services | 384 | Lo spettatore con la carta ignota: dinamica informativa (compartimento I | 1 / 2 | pubblica (services) | — | — |
| `services/successione.py` | services | 201 | Successione di Procedure, tabellone cumulativo e ritorno (J, riga L90) | 3 / 1 | pubblica (services) | — | — |
| `services/tabellone.py` | services | 367 | Presenter del tabellone e del livello ternario (compartimento I2) | 9 / 12 | pubblica (services) | — | — |

`gui/i18n.py` è **M — legacy but required**: re-export del catalogo di
`gioco27/i18n.py` (A2), importato da 29 moduli GUI. Rimuoverlo richiederebbe
di cambiare 29 import: è un refactoring, non una bonifica. **KEEP.**

Non esistono package `persistence/`, `cli/` o `assets/` di codice: la
persistenza J è in `services/archivio.py`, la CLI è `cli.py`, `assets/`
contiene solo i due font.

### 13.2 Identificatori legacy (G, H, G_ext)

Convenzione corrente (I7, test D1/D3): **H** = 216 trasformazioni
separabili, **Γ** = 648 (esteso). Inventario, senza migrazione:

| identificatore | dove | classe | nota |
|---|---|---|---|
| «G = GEN3^3», `$G$`, `Z(G)`, `[G:…]` | `i18n.py`: chiavi `export.document.cayley.*` e `export.document.conjugacy.*` (IT/EN, ~10 per lingua) | **A user-facing** (documenti LaTeX/SVG esportati) | è il debito «export.document usa ancora G» già registrato in J; va con la riconciliazione export/packaging H/Γ di K |
| «il libro chiama Gaia il gruppo G» | `glossary.long.gaia` | A user-facing, **intenzionale** | nome del libro, spiegato come H |
| `appartiene_a_G` (216), `DECOMPOSIZIONI_PER_TARGET_IN_G` | `core/kronecker.py`; usati da 3 file di test | **C internal-only** (API del core usata dai test) | registrato per K |
| `appartiene_a_H` con docstring «\|H\| = 648» | `core/kronecker.py` | **C internal-only**, **nome in conflitto** con la convenzione corrente (qui H significa Γ) | registrato per K; i test di documentazione vietano «\|H\| = 648» solo nei testi utente |
| docstring «G = GEN3 x GEN3 x GEN3», «in G» | `core/group_theory.py`, `core/cache.py`, `core/kronecker.py`, `gui/cayley_dialog.py`, `gui/export_group_dialog.py` | C internal-only | commenti |
| `G_ext` | — | — | **nessuna occorrenza** |
| **D dead** | — | — | **nessuno trovato**: nulla da eliminare |

## 14. Test

61 file, tutti attivi: ciascuno protegge un comportamento esistente (lo
scopo di ogni file è nella colonna `purpose` dell'inventario). Nessun test
è stato eliminato o accorpato.

| gruppo | file |
|---|---|
| matematica e dominio | `test_baseline_matematica`, `test_core`, `test_dominio_*` (3), `test_perm_matrix_convention`, `test_numerazione_base0`, `test_tabellone_inverso`, `test_alias_nomi`, `test_gioco_reale`, `test_fuori_dal_gioco`, `test_decomposition_integrita` |
| I/O, export, concorrenza (B, C, F, G) | `test_io_integrita_b`, `test_output_integrita`, `test_export_integrita`, `test_pdf_memoria`, `test_parallel_limiti`, `test_stato_concorrenza_c`, `test_rischi_concorrenza`, `test_annullamento`, `test_analisi_filtri_f`, `test_servizi_g1`, `test_lifecycle_persistenza_g2`, `test_hardening`, `test_chiusura_regressioni` |
| linguaggio (E) | `test_linguaggio_espressioni_e` |
| presentazione, i18n, accessibilità (H) | `test_i18n*` (4), `test_presentation_i18n_h1`, `test_layout_accessibilita_h2`, `test_layout_dettaglio`, `test_gui_stato` |
| I1–I7 | `test_procedure_i1_*` (3), `test_tabellone_ternario_i2`, `test_tavola_ternaria_i2`, `test_navigazione_i2`, `test_errori_fisici_i3`, `test_pratica_reale_i3`, `test_spettatore_i4_*` (3), `test_riconoscimento_i5_*` (3), `test_laboratorio_i6_*` (3), `test_didattica_i7`, `test_guida_allineata` |
| J | `test_esperimenti_j`, `test_cli_j`, `test_sessione_j_gui`, `test_architettura_j` |
| documentazione e statica | `test_documentazione_d1d3`, `test_documentazione_d4d5`, `test_static` |
| K0 | `test_struttura_repository_k0` (nuovo) |

* **Fixture e golden**: `tests/` contiene solo `.py`; nessun file di dati,
  nessun golden orfano. Le fixture sono locali ai file.
* **Corpi di test identici**: nessuno (confronto AST).
* **Helper duplicati** (P11): `lingua` identica in 6 file, `_c3` in 3,
  `inv`, `italian_default`, `servizio`, `vista` in 2; altri nomi comuni
  (`app`, `_norm`, `_testo`, …) hanno corpi diversi. **DEFER**: spostarli in
  un `tests/conftest.py` cambierebbe scope e isolamento delle fixture Tk, e
  alcune copie sono oracoli indipendenti per scelta.
* **Test modificati da K0**: solo percorsi (§ 11); più il nuovo
  `test_struttura_repository_k0.py` (7 test): radice ammessa, `docs/`
  classificata, nessun artefatto generato tracciato, PDF mai tracciati, una
  sola `Tooltip`, riferimenti `docs/…` risolvibili, inventario completo.

## 15. Risorse

| risorsa | uso | package data | spec | esito |
|---|---|---|---|---|
| `gioco27/assets/DejaVuSans.ttf` | `core/detail_pdf.py` (percorso `_ASSETS`) | `pyproject`: `assets/*.ttf` | `datas` | KEEP |
| `gioco27/assets/DejaVuSans-Bold.ttf` | idem | idem | idem | KEEP |

Nessun duplicato, nessun template, immagine o dato incorporato. La licenza
dei font non è nel repository (P8, K).

## 16. `.gitignore`

**Invariato.** È il modello GitHub per Python, più ampio del necessario ma
senza pattern che nascondano sorgenti utili, **con una sola eccezione
nota**:

| pattern | cosa nasconde | intenzionale? | necessario alla riproducibilità? | esito |
|---|---|---|---|---|
| `__pycache__/`, `*.py[cod]` | bytecode | sì | no | corretto |
| `build/`, `dist/`, `*.egg-info/` | output di build | sì | no | corretto |
| `.pytest_cache/`, `.coverage*`, `htmlcov/` | cache/copertura | sì | no | corretto |
| `*.manifest` | manifest PyInstaller | sì | no | non colpisce i manifest J (`*.manifest.json`) |
| **`*.spec`** | **`gioco27.spec`** | **accidentale** | **sì**: README e Guida documentano `pyinstaller gioco27.spec` | **DEFER a K (N04)**: la correzione minima è `!gioco27.spec` dopo `*.spec` e il versionamento del file; non applicata perché N04 è «aperto per decisione» con proprietario K e riguarda il packaging |
| `lib/`, `var/`, `env/` … | directory generiche | sì | no | nessuna directory del progetto colpita |

Nessun file tracciato è anche ignorato (`git ls-files -ci --exclude-standard`
vuoto). I PDF non sono ignorati: restano visibili come non tracciati, per
scelta (DP12 aperta).

## 17. File e nomi rinviati (DEFER)

| elemento | classe | motivo del rinvio |
|---|---|---|
| `gioco27.spec` (ignorato) | D | N04 → K |
| `pyproject.toml` `license = "Proprietary"` vs GPL v3 | D | packaging → K |
| licenza dei font DejaVu | C | packaging/licenze → K |
| `requirements-dev.txt` senza `pypdfium2` (N03, unico skip) | D | K |
| `core/analisi.py` / `core/analysis.py` | A | nomi vicini; ~15 importatori |
| `CanonicalForm.from_kron_and_exp` (`core/algebra.py`) | A | pubblico, uso non trovato |
| `descrizione_impilamento` (`core/gioco_reale.py`) | A | pubblico, uso non trovato; citato dall'audit V4 come fonte delle istruzioni d'impilamento |
| `ONBOARD_INTRO` (`gui/glossary.py`) | A | costante pubblica, uso non trovato (A2 ne tolse solo l'import) |
| `SECTION_TITLE_KEYS` (`gui/guide.py`) | A | pubblica, commentata «compatibilità con app/test», uso non trovato |
| `Tooltip.set_text` (`gui/tooltip.py`) | A | metodo pubblico, uso non trovato |
| helper duplicati dei test | B | § 14 |
| identificatori legacy G/H | A/C | § 13.2, riconciliazione H/Γ in K |

Per i nomi pubblici l'evidenza è «uso non trovato», non «non usato
dimostrato»: non sono stati eliminati.

## 18. Struttura finale

    /
    ├── README.md                 documentazione utente (+ «Documentazione»)
    ├── LICENSE
    ├── pyproject.toml
    ├── requirements.txt
    ├── requirements-dev.txt
    ├── .gitignore  .gitattributes
    ├── conftest.py
    ├── gioco27.py                launcher
    ├── avvia.bat                 launcher Windows
    ├── controlla_requisiti.py    diagnostica utente
    ├── gioco27.spec              (ignorato — N04, K)
    ├── Articolo.pdf  LIBRO_MAIN.pdf   (non tracciati — input utente)
    ├── docs/
    │   ├── README.md
    │   ├── audits/
    │   │   ├── K0_FILE_INVENTORY.csv
    │   │   ├── V4_COVERAGE_MATRIX.csv
    │   │   └── V4_MATHEMATICAL_DIDACTIC_COVERAGE_AUDIT.md
    │   ├── decisions/
    │   │   ├── GIT_BASELINE_AND_RECONCILIATION.md
    │   │   ├── V4_PRE_I1_PRODUCT_DECISIONS.md
    │   │   ├── V4_PRE_I2_VIEW_DECISIONS.md
    │   │   └── V4_PRE_I5_DECISIONS.md
    │   ├── history/
    │   │   ├── A_BASELINE_CLOSED.md … J_EXPERIMENTS_REPRODUCIBILITY_CLOSED.md
    │   │   └── K0_REPOSITORY_CLEANUP_CLOSED.md
    │   └── release/
    │       ├── NOTE_VERSIONE_3.md
    │       ├── NOTE_VERSIONE_3.1.1.md
    │       └── NOTE_VERSIONE_3.1.3.md
    ├── gioco27/
    │   ├── __init__.py  __main__.py  cli.py  i18n.py
    │   ├── assets/               2 font DejaVu
    │   ├── core/                 21 moduli + __init__ (matematica, export, infrastruttura)
    │   ├── services/             14 moduli + __init__ (G1 … J)
    │   └── gui/                  35 moduli + __init__
    └── tests/                    61 file

Radice: da 43 voci (41 file, 2 directory) a 17 (14 file, 3 directory);
tracciate al primo livello: 11 file e 3 directory (`docs/`, `gioco27/`,
`tests/`). Le altre tre voci sono i due PDF dell'utente e lo spec ignorato.

## 19. Suite

Eseguita file per file sotto xvfb (1920×1080), come nei compartimenti
precedenti, con `-B -p no:cacheprovider`.

| | prima di K0 | dopo K0 |
|---|---|---|
| raccolti | 2326 | **2333** |
| passati | 2324 | **2331** |
| saltati | 1 | 1 (`test_layout_dettaglio`, N03) |
| falliti | 1 | 1 — solo il noto Tk 9 `test_lo_scorrimento_si_accende_quando_il_testo_cresce` |

+7 = `test_struttura_repository_k0.py`. Baseline matematica 25/25, I1–I7
verdi, J 84/84, documentazione D1–D5 verdi, architettura J 6/6, pyflakes
pulito su `gioco27/`, `tests/` e launcher; import di GUI, CLI e servizi
riusciti.

## 20. Filesystem

* Lavoro solo nel repository; nessun file scritto fuori (gli strumenti di
  analisi sono stati eseguiti da stdin, senza file temporanei).
* `Articolo.pdf`, `LIBRO_MAIN.pdf`: non tracciati, non spostati, non
  rinominati, MD5 invariati (`89ad587f…`, `c6fac165…`).
* Nessun `git clean`, reset, rebase o riscrittura della storia; nessun push.
* Eliminazioni solo di cache ignorate e di codice morto dimostrato (§ 8).

## 20 bis. Gate

| gate | esito | evidenza |
|---|---|---|
| K0-G1 inventario completo | ✔ | § 2, inventario CSV |
| K0-G2 ogni file classificato | ✔ | § 3 (Q = 0) |
| K0-G3 untracked classificati | ✔ | i due PDF = P |
| K0-G4 ignored rilevanti classificati | ✔ | § 16 |
| K0-G5 cache/residui rimossi | ✔ | § 10 |
| K0-G6 nessun generato tracciato | ✔ | § 10, test K0 |
| K0-G7 duplicati risolti o motivati | ✔ | § 9 |
| K0-G8 file morti dimostrati eliminati | ✔ | § 8 |
| K0-G9 nessun ambiguo eliminato | ✔ | § 17 |
| K0-G10 root ordinata | ✔ | § 18, test K0 |
| K0-G11 corrente/storica distinguibile | ✔ | § 11 |
| K0-G12 script classificati | ✔ | § 12 |
| K0-G13 package classificato | ✔ | § 13 |
| K0-G14 test classificati | ✔ | § 14 |
| K0-G15 risorse classificate | ✔ | § 15 |
| K0-G16 nessun riferimento rotto | ✔ | § 11, test K0 |
| K0-G17 `.gitignore` coerente | ✔ | § 16 (eccezione N04 documentata) |
| K0-G18 PDF intatti/non tracciati | ✔ | § 20 |
| K0-G19 architettura invariata | ✔ | `test_architettura_j` |
| K0-G20 matematica invariata | ✔ | baseline 25/25 |
| K0-G21 I1–I7 verdi | ✔ | § 19 |
| K0-G22 J verde | ✔ | § 19 |
| K0-G23 nessuna nuova regressione | ✔ | § 19 |
| K0-G24 filesystem conforme | ✔ | § 20 |
| K0-G25 nessun push | ✔ | § 22 |
| K0-G26 packaging/CI/release non iniziati | ✔ | § 17 |
| K0-G27 albero finale documentato | ✔ | § 18 |
| K0-G28 inventario macchina-leggibile | ✔ | `docs/audits/K0_FILE_INVENTORY.csv` |

## 21. Commit

| commit | messaggio |
|---|---|
| `4860860` | docs(K0): organize project and historical documentation under docs/ |
| `90dc0a9` | refactor(K0): remove proven dead code |
| `8314512` | test(K0): protect cleaned repository structure |
| `ed5e2f4` | docs(K0): inventory and close repository cleanup compartment |
| (questo) | fix(K0): complete inventory reasons for the font resources |

`ed5e2f4` è stato registrato con due righe dell'inventario (i font) senza
`reason`: il test K0 l'ha segnalato subito dopo il commit; il commit
successivo completa le due righe. Nessun codice coinvolto.

## 22. Git status

Branch `main`; working tree pulito salvo `Articolo.pdf` e `LIBRO_MAIN.pdf`
non tracciati; 139 commit avanti rispetto a `origin/main` (`54445af`) dopo
questo commit; nessun push.
