# Documentazione del progetto

La documentazione **per l'utente** è la Guida integrata nel programma
(scheda «Guida»; si parte dalla scheda «Inizia qui») e il `README.md` nella radice.
Questa cartella raccoglie la documentazione **di progetto e di sviluppo**.

| cartella | stato | contenuto |
|---|---|---|
| `audits/` | **riferimento** | audit di copertura matematico-didattica V4 e la sua matrice (`V4_COVERAGE_MATRIX.csv`, letta dai test di I7); inventario dei file K0; audit progettuale della roadmap (`AUDIT_ROADMAP_4x.md`), da valutare senza applicazione automatica |
| `decisions/` | **corrente come riferimento** | decisioni approvate prima dei compartimenti (`V4_PRE_I1`, `V4_PRE_I2`, `V4_PRE_I5`) e la baseline di riconciliazione Git (`GIT_BASELINE_AND_RECONCILIATION.md`), citate da codice e test |
| `history/` | **storico, chiuso** | documenti di chiusura dei compartimenti A … J e K0, in ordine di esecuzione |
| `release/` | **storico**, tranne la 4.0.2 e la roadmap | note della **4.0.2** (`NOTE_VERSIONE_4.0.2.md`, corrente); note storiche delle versioni 3, 3.1.1, 3.1.3, 4.0.0 e 4.0.1; chiusura del compartimento K (`K_RELEASE_CANDIDATE_CLOSED.md`); sviluppi futuri (`ROADMAP_4.x.md`, corrente) |

## Regole

* I documenti in `history/` descrivono lo stato del repository **al momento
  della chiusura**: non si riscrivono. I percorsi che citano sono relativi
  alla radice di allora; dal compartimento K0 i documenti di progetto stanno
  qui, con lo stesso nome file (i nomi sono univoci).
* Un riferimento corrente (codice, test, README) usa il percorso completo,
  per esempio `docs/decisions/V4_PRE_I2_VIEW_DECISIONS.md`.
* La mappa completa dei file del repository, con categoria e azione K0, è
  in `audits/K0_FILE_INVENTORY.csv`.

## Ordine dei compartimenti

A baseline · B I/O · C stato · D dominio · E linguaggio e simulazione ·
F analisi · G1 servizi · G2 ciclo di vita · H1 presentazione e i18n ·
H2 accessibilità · I1 procedure · I2 tabellone ternario · I3 errori fisici ·
I4 spettatore · I5 riconoscimento · I6 laboratorio · I7 allineamento
didattico · J esperimenti e riproducibilità · K0 bonifica del repository ·
K packaging e preparazione della release candidate 4.0.0 (in `release/`).
