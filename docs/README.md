# Documentazione del progetto

La documentazione **per l'utente** è la Guida integrata nel programma
(scheda «Guida»; si parte dalla scheda «Inizia qui») e il [README del programma](../README.md).
Questa cartella raccoglie la documentazione **di progetto e di sviluppo**.

## Riprendere lo sviluppo

1. Le [note della 4.1.0](release/NOTE_VERSIONE_4.1.0.md) descrivono le nuove viste strutturali.
2. La [roadmap 4.x](release/ROADMAP_4.x.md) raccoglie gli sviluppi pianificati.
   La Vista Gruppo è una tappa successiva della serie 4.1.x.
3. L'[audit della roadmap](audits/AUDIT_ROADMAP_4x.md) censisce le capacità
   disponibili al 5 ottobre 2026 e propone un diverso raggruppamento di alcune attività.
   Per le decisioni recepite vale la roadmap corrente. Prima di aprire una voce, confrontare
   roadmap e audit con il codice corrente.

## Orientarsi nel Laboratorio

| Area | Riferimenti |
|---|---|
| Laboratorio matematico nell'Explorer | [Vista](../gioco27/gui/laboratorio_tab.py), [servizio](../gioco27/services/laboratorio.py), [chiusura I6](archive/compartments/I6_MATHEMATICAL_LAB_CLOSED.md) |
| Cicli e orbite | [Calcoli](../gioco27/core/analysis.py) e [vista](../gioco27/gui/cycles_tab.py) |
| Fibre e ricostruzione | [Servizio di riconoscimento](../gioco27/services/riconoscimento.py) |
| Riproducibilità degli esperimenti | [Servizio](../gioco27/services/esperimento.py) e [chiusura J](archive/compartments/J_EXPERIMENTS_REPRODUCIBILITY_CLOSED.md) |

## Struttura della documentazione

| Cartella | Contenuto |
|---|---|
| [release/](release/) | Note della versione corrente e roadmap 4.x |
| [decisions/](decisions/) | Decisioni di progetto che descrivono convenzioni e contratti del programma |
| [audits/](audits/) | Audit di riferimento e matrice di copertura usata dai test |
| [archive/](archive/README.md) | Note precedenti, audit conclusi e documenti di chiusura |

Il codice applicativo è in `gioco27/`, i test e le fixture sono in `tests/`
e il benchmark manuale è in [tools/](../tools/benchmark_k.py).

## Guida e aiuto sul web

`python tools/export_help.py` genera le quattro pagine HTML in
`build/help-web/`. Apri `build/help-web/index.html` per consultarle anche
offline. L’esportazione usa i testi dell’app e conserva l’indice, i
collegamenti agli argomenti e il passaggio fra italiano e inglese.
Gli aggiornamenti ai testi su `main` avviano la pubblicazione su GitHub Pages.
