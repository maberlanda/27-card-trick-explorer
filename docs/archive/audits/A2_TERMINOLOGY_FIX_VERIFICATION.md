# A2-FIX — Verifica delle correzioni terminologiche

## Ambito e vincoli

Questa verifica chiude esclusivamente gli issue registrati in
`A2_FINAL_TERMINOLOGY_AUDIT.md` e `A2_FINAL_TERMINOLOGY_AUDIT.csv`. Non
reinterpreta l'audit, non modifica la matematica, non rinomina chiavi o campi
machine-readable e non avvia A3. I tre issue `STYLE-DEFERRED` restano fuori
dall'intervento.

PDF invariati e non tracciati.

## Esito dei 16 issue

| ID | Stato iniziale | Decisione terminologica | Superfici modificate | Esempio prima → dopo | Regressione | Stato finale |
|---|---|---|---|---|---|---|
| A2-TERM-HIGH-01 | `disposizione` indicava sia lo stato `v_k` sia una riga della Tavola | `disposizione/arrangement` è lo stato del mazzo; `trasformazione/transformation` e `riga/Table row` designano le 216 righe | Tavola, Explorer, Simulatore, Presentazione, Guida, export, help IT/EN | `Disposizione #n` → `Riga #n`; `dettaglio disposizioni` → `dettaglio trasformazioni`; `Disposizione v_k` preservato | `test_tavola_usa_trasformazione_e_disposizione_resta_lo_stato_vk` | **VERIFIED FIXED** |
| A2-TERM-HIGH-02 | il bare `R` designava MSC, il reversal locale e `C_N⁻¹` | MSC resta `MSC`; il reversal locale è `R_U`; il ritorno compresso è `C_N⁻¹` senza nuovo simbolo | Glossario, Guida I1/I6, Laboratorio, pannello Laboratorio, L90, CLI e Sessione IT/EN | `H∘R²` → `H∘MSC²`; `R = C_N⁻¹` → `ritorno compresso C_N⁻¹`; formula locale `R` → `R_U` | `test_gamma_usa_msc_e_non_un_bare_r`; `test_rovesciamento_locale_e_ritorno_compresso_non_riusano_bare_r` | **VERIFIED FIXED** |
| A2-TERM-HIGH-03 | `firma` indicava vettore serializzato, forma canonica e somme di blocco | `vettore della permutazione/permutation vector`; `forma canonica/canonical form`; `firma di blocco/block signature` | Explorer, help, Guida, protocollo, rappresentazione testuale del core, glossario IT/EN | `Periodo … Firma …` → `Ordine … Vettore …`; `firma` parziale → `vettore` parziale | `test_vettore_forma_canonica_e_firma_di_blocco_sono_distinti` | **VERIFIED FIXED** |
| A2-TERM-MEDIUM-01 | MSC, distribuzione, raccolta, P, mescolamento e impilamento avevano definizioni sovrapposte | MSC è l'operatore fisso; deal/distribuzione e pickup/raccolta sono gesti; P è la permutazione di raccolta; `M_i` è il codice locale; stacking/impilamento è il gesto di sovrapposizione | Glossario, filtri, Guida, protocollo HTML, Simulatore e Spettatore IT/EN | `basic shuffle` indistinto → definizione esplicita di MSC; `collection` fisica EN → `pickup` | test di glossario, i18n, Simulatore, Spettatore ed export | **VERIFIED FIXED** |
| A2-TERM-MEDIUM-02 | colonna, pila, mazzetto e pacchetto oscillavano fra gesto fisico e modello tensoriale | `colonna/column` è il layout; `mazzetto/pile` il gruppo fisico; `pacchetto/packet` resta alias di fonte o blocco qualificato; nelle spiegazioni tensoriali si usa `blocco/block` | Simulatore, Pratica, Spettatore, Guida, filtri, protocollo/export e glossario IT/EN | `packets from the back` → `piles from the back`; `3 packets of 9` → `3 blocks of 9` | test i18n, Guida, Simulatore/Spettatore ed export | **VERIFIED FIXED** |
| A2-TERM-MEDIUM-03 | fase e stadio descrivevano talvolta la stessa unità | `stadio/stage` è `P_i ∘ MSC ∘ J_i`; `fase/phase` è l'intervallo fisico/interattivo; passo e tappa restano separati | Glossario, Guida, Tavola, Pratica, Spettatore e testi di ritorno IT/EN | `same phase order` algebrico → `same stage order` | test i18n, Guida e flussi I2–I4 | **VERIFIED FIXED** |
| A2-TERM-MEDIUM-04 | il punto fisso di J era descritto come una carta | un punto fisso è una posizione `x` con `T[x]=x`; la carta C13 è citabile solo nel mazzo ordinato | Glossario, Laboratorio e Guida I6 IT/EN | `J fixes only card 13` → `J has position 13 as its unique fixed point` | `test_l90_usa_tappa_checkpoint_e_j_fissa_la_posizione_13` | **VERIFIED FIXED** |
| A2-TERM-MEDIUM-05 | `ritorno` copriva riga inversa, cumulativo, replay e recupero | distinti `riga di ritorno`, `ritorno compresso all'origine`, `replay a ritroso` e `recupero` | Glossario, Tavola, Pratica, Spettatore, L90, Guida e CLI IT/EN | `ritorno` generico → `riga di ritorno`; `return in one Procedure` → `compressed return in one Procedure` | regressioni A2, L90/J, Simulatore/Spettatore e CLI | **VERIFIED FIXED** |
| A2-TERM-MEDIUM-06 | il Gioco Reale era chiamato dominio di 1.728 combinazioni o sequenze | il dominio normativo è `1 728 Procedure` / `1,728 Procedures` | pulsanti, preset, tooltip, Guida, README e note di release IT/EN | `1 728 sequenze canoniche` → `1 728 Procedure` | `test_dominio_gioco_reale_e_1728_procedure` | **VERIFIED FIXED** |
| A2-TERM-MEDIUM-07 | ordine e periodo oscillavano come termini principali | termine primario `ordine della permutazione/permutation order`; `periodo/period` resta solo alias dichiarato nel glossario | Tavola, Explorer, Presentazione, Guida, protocollo, PDF e help IT/EN | `Periodo` → `Ordine`; `period` → `order` | `test_ordine_e_il_termine_principale_periodo_solo_alias_dichiarato` | **VERIFIED FIXED** |
| A2-TERM-MEDIUM-08 | la carta scelta era confusa con il bersaglio | `carta scelta/chosen card` è l'oggetto; `posizione bersaglio/target position` è la destinazione | Simulatore, Pratica, Spettatore, recupero, Guida e glossario IT/EN | `Carta bersaglio: C07` → `Carta scelta: C07`; `Target card` → `Target position` dove il valore è una sede | `test_carta_scelta_e_posizione_bersaglio_sono_separate` | **VERIFIED FIXED** |
| A2-TERM-MEDIUM-09 | `inversione` designava anche `R_U` | `inversa/inverse` è riservato a `T⁻¹`; `rovesciamento/reversal` a `R_U` e J | Guida, legenda, PDF dettagliato, Riconoscimento e glossario IT/EN | `Inversione — S↔D` → `Rovesciamento — S↔D`; `No implicit inversion` → `No implicit passage to the inverse` | `test_inversa_e_rovesciamento_sono_distinti` | **VERIFIED FIXED** |
| A2-TERM-LOW-01 | il grafo tecnico esponeva `Le 216 Cronache` | nel grafo tecnico si usano `trasformazioni/transformations`; Cronaca resta narrativa | Laboratorio, Guida I6 e descrizione del servizio | `Le 216 Cronache` → `Le 216 trasformazioni` | `test_cronaca_non_e_il_nome_tecnico_del_grafo_delle_216` | **VERIFIED FIXED** |
| A2-TERM-LOW-02 | `collection`, `pickup` e `gathering` non avevano ruoli stabili | `pickup` è l'azione fisica; `pickup permutation`/`collection permutation` qualifica P; nessun `gathering` tecnico residuo | Simulatore, Spettatore, Guida, filtri e protocollo/export EN | `collection order` fisico → `pickup order`; `packets` fisici → `piles` | scansione residui e test i18n/export | **VERIFIED FIXED** |
| A2-TERM-LOW-03 | mancavano venti concetti controllati nel glossario | aggiunte voci brevi IT/EN, senza duplicare le definizioni esistenti | glossario e sezione glossario della Guida | assenti → indice, disposizione, carta scelta, posizione bersaglio, fase, tappa, colonna/mazzetto, trasformazioni cumulativa/relativa, mazzi gemelli, tipo/struttura ciclica, orbita, storia, replay, firma di blocco, riconoscimento, taglio, traslazione, rotazione | `test_glossario_a2_copre_le_lacune_in_entrambe_le_lingue` | **VERIFIED FIXED** |
| A2-TERM-ITEN-01 | `Tappa v_k` era tradotto `Stage v_k` | coppia controllata `Tappa/Checkpoint` per gli stati intermedi L90 | L90, Sessione, Guida e CLI EN | `Stage v{k}` → `Checkpoint v{k}` | `test_l90_usa_tappa_checkpoint_e_j_fissa_la_posizione_13` | **VERIFIED FIXED** |

## SOURCE-TERM preservati

Le otto mappature di fonte restano disponibili soltanto nei contesti marcati,
narrativi o esplicitamente storici:

1. `disposizione semplice / simple arrangement`;
2. `G / Gaia`;
3. `Cronaca / Chronicle`;
4. `Giullare / Jester`;
5. `Mondo-di-Mazzo / Deck-World`;
6. `Seldon / Psicostoria / Psychohistory`;
7. `Prima Crisi / First Crisis`;
8. `Seconda Crisi / Second Crisis`.

La preservazione è coperta da
`test_source_terms_restano_disponibili_nei_contesti_marcati` e dalle sette
voci narrative del glossario. Stato: **VERIFIED PRESERVED**.

## STYLE-DEFERRED

Non sono state avviate normalizzazioni generali di:

- `base 3/base-3`, composti e trattini (`A2-STYLE-01`);
- maiuscole/minuscole editoriali (`A2-STYLE-02`);
- varianti tipografiche `S27/S₂₇`, `S3/S₃`, `Γ/Gamma` (`A2-STYLE-03`).

Stato: **VERIFIED DEFERRED** per tutti e tre gli issue di stile, fuori dal gate
A2-FIX.

## Glossario e compatibilità

Il glossario contiene 63 voci: 56 matematiche e 7 narrative. I cataloghi IT ed
EN contengono 2.108 chiavi ciascuno, con identico insieme di chiavi e identici
placeholder. Le chiavi storiche (`explorer.canonical_signature`, campi
`period`, `signature` e altri identificatori di schema) non sono state
rinominate: è cambiato soltanto il testo user-facing. Nessuno schema è stato
modificato.

## Verifiche eseguite

| Ordine | Gruppo | Esito |
|---:|---|---|
| 1 | A2-FIX mirati | 26 passed |
| 2 | i18n | 124 passed, 8 skipped (display non disponibile) |
| 3 | glossario | 41 passed, 6 skipped (display non disponibile) |
| 4 | UI/Guida coinvolte | 123 passed, 26 skipped (display non disponibile) |
| 5 | L90/J | 58 passed, 13 skipped (display non disponibile) |
| 6 | Tavola/Explorer | 364 passed, 19 skipped (display non disponibile) |
| 7 | Simulatore/Spettatore | 410 passed, 30 skipped (display non disponibile) |
| 8 | Recognition/Laboratorio | 98 passed, 31 skipped (display non disponibile) |
| 9 | export | 106 passed |
| 10 | CLI | 32 passed |
| 11 | A1/A1-FIX | 6 passed |
| 12 | K/K0 | 19 passed, 9 skipped (dipendenze/GUI ambientali) |
| 13 | baseline matematica | 25 passed |
| 14 | pyflakes | 2 skipped: modulo `pyflakes` non installato nel runtime locale |
| 15 | `git diff --check` | superato |
| 16 | suite completa | 2.083 passed, 320 skipped |

Gli skip della suite sono ambientali: display GUI non disponibile e dipendenze
facoltative assenti (`pyflakes`, `pikepdf`, `pypdfium2` e tool `build`). Non ci
sono skip terminologici o matematici.

## Gate

I gate AF2-G1–AF2-G16 sono coperti dagli esiti della tabella; AF2-G17–AF2-G24
sono coperti da preservazione SOURCE-TERM, STYLE-DEFERRED, glossario simmetrico,
export/CLI e test A1. AF2-G25 è coperto dalla suite completa verde, AF2-G26 da
`git diff --check`, AF2-G27–AF2-G28 dallo stato del filesystem, AF2-G29–AF2-G30
dall'assenza di push e di attività A3, AF2-G31 dal presente documento. Tutti i
gate A2-FIX risultano chiusi.
