# Documentazione del progetto

La documentazione **per l'utente** è la Guida integrata nel programma
(scheda «Guida»; si parte dalla scheda «Inizia qui») e il [README del programma](../README.md).
Questa cartella raccoglie la documentazione **di progetto e di sviluppo**.

## Riprendere lo sviluppo

1. Le [note della 4.0.3](release/NOTE_VERSIONE_4.0.3.md) descrivono la base di manutenzione da cui parte la 4.1.
2. La [roadmap 4.x](release/ROADMAP_4.x.md) raccoglie gli sviluppi pianificati.
   La 4.1.0 comprende l'infrastruttura grafica comune, la Vista Posizioni e la Vista Fibre.
3. L'[audit della roadmap](audits/AUDIT_ROADMAP_4x.md) censisce le capacità
   disponibili al 5 ottobre 2026 e propone un diverso raggruppamento di alcune attività.
   Per le decisioni recepite vale la roadmap corrente. Prima di aprire una voce, confrontare
   roadmap e audit con il codice corrente.

## Orientarsi nel Laboratorio

| Area | Riferimenti |
|---|---|
| Laboratorio matematico nell'Explorer | [Vista](../gioco27/gui/laboratorio_tab.py), [servizio](../gioco27/services/laboratorio.py), [chiusura I6](history/I6_MATHEMATICAL_LAB_CLOSED.md) |
| Cicli e orbite | [Calcoli](../gioco27/core/analysis.py) e [vista](../gioco27/gui/cycles_tab.py) |
| Fibre e ricostruzione | [Servizio di riconoscimento](../gioco27/services/riconoscimento.py) |
| Riproducibilità degli esperimenti | [Servizio](../gioco27/services/esperimento.py) e [chiusura J](history/J_EXPERIMENTS_REPRODUCIBILITY_CLOSED.md) |

## Struttura della documentazione

| cartella | stato | contenuto |
|---|---|---|
| `audits/` | **riferimento** | audit di copertura matematico-didattica V4 e la sua matrice (`V4_COVERAGE_MATRIX.csv`, letta dai test di I7); inventario dei file K0; audit progettuale della roadmap (`AUDIT_ROADMAP_4x.md`), da valutare senza applicazione automatica |
| `decisions/` | **corrente come riferimento** | decisioni approvate prima dei compartimenti (`V4_PRE_I1`, `V4_PRE_I2`, `V4_PRE_I5`) e la baseline di riconciliazione Git (`GIT_BASELINE_AND_RECONCILIATION.md`), citate da codice e test |
| `history/` | **storico, chiuso** | documenti di chiusura dei compartimenti A … J e K0, in ordine di esecuzione |
| `release/` | **storico**, tranne la 4.0.3 e la roadmap | note della **4.0.3** (`NOTE_VERSIONE_4.0.3.md`, corrente), note storiche fino alla 4.0.2, chiusura del compartimento K (`K_RELEASE_CANDIDATE_CLOSED.md`) e roadmap corrente (`ROADMAP_4.x.md`) |

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
