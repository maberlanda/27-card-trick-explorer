# I3 — Traccia fisica, errori e recupero: chiusura

Compartimento I3 della 4.0, implementato con le decisioni D-I3-1…D-I3-7 approvate, dopo la chiusura di I1 e I2
(`4b2f9c7`). Non c'è un PRE-I3 separato.

**Etichette di provenienza**:

| Etichetta | Significato |
|---|---|
| **FONTE** | libro o documenti autorevoli |
| **CODICE** | lettura del codice |
| **TEST** | test del repository |
| **ESEC** | esecuzioni fatte in questa sessione |
| **INFERENZA** | deduzione argomentata dalle voci precedenti |

## 1. Stato d'ingresso

ESEC:

| Voce | Valore |
|---|---|
| branch | `main` |
| HEAD | `4b2f9c7 docs(I2): close board and ternary views compartment` |
| commit avanti rispetto a `origin/main` | 81 |
| working tree tracciato | pulito |
| non tracciati | solo `Articolo.pdf` e `LIBRO_MAIN.pdf` |
| suite di I2 | 1602 passed, 1 skipped, 1 failed (Tk 9 noto) |
| ambiente | CPython 3.12.14, Tk 9.0.4 sotto xvfb |

## 2. Decisioni applicate (DP6 e D-I3)

DP6 riguardava I3 (PRE-I2 § 21.1). È applicata attraverso le decisioni approvate D-I3-1…7. DP10 **non** è decisa
(vedi E6).

| Decisione | Applicazione |
|---|---|
| D-I3-1 | E1–E5 sono simulati fisicamente, carta per carta, nel service `services.errori` |
| D-I3-2 | E6 compare solo nel catalogo e nella diagnostica (`simulato=False`, nessuna fase). Non c'è un atomo «taglio» in produzione, il linguaggio algebrico non è esteso e DP10 non è decisa. Le traslazioni C_k esistono solo come oracolo nei test |
| D-I3-3 | E4 = «colonna indicata sbagliata» con la carta tracciata. Lo spettatore adattivo non c'è (è I4) |
| D-I3-4 | la Pratica storica («valutazione») resta il default ed è invariata. La modalità «conseguenze reali» è opt-in |
| D-I3-5 | recupero A: ripianificazione delle fasi residue (al più 36 suffissi dopo la fase 1, 6 dopo la fase 2). Si elencano tutte le opzioni che raggiungono il bersaglio, ordinate per (meno modifiche, meno raccolte non SCD, ordine `SIGLE`), e ognuna è applicabile. Recupero B: ritorno con T_eseguita⁻¹ tramite il presenter di I2 |
| D-I3-6 | previsto ed eseguito sono sempre distinti (T, riga, posizione e cifre). Né il catalogo né la UI dicono mai «equivalente» in modo generico |
| D-I3-7 | Tavola → Pratica con disposizione fissata: il piano è fisso, la carta è variabile e il bersaglio è T[carta]; `risolvi_trucco` non viene chiamato |

## 3. Ordine fisico per fase

CODICE (`services.errori.esegui_fase`), TEST (`test_eventi_multipli_nello_stesso_ordine_fisico`):

distribuzione → **E3** (ordine interno di ogni mazzetto invertito) → colonna reale → **E4** (colonna indicata) →
mescolamento inteso → impilamento → **E1/E5** → raccolta → **E2** (mazzo rovesciato dopo la raccolta; alla fase 3
è J∘T).

Nella stessa fase gli eventi si registrano in quest'ordine: E3, E4, E1/E5, E2.

## 4. File modificati

ESEC (`git diff 4b2f9c7 --stat`): 14 file, +2086 / −34.

| File | Natura |
|---|---|
| `gioco27/core/gioco_reale.py` | + `mescolamento_per_colonna`, estratta da `risolvi_trucco` a comportamento invariato |
| `gioco27/services/errori.py` | **nuovo**, service puro (471 righe) |
| `gioco27/gui/pratica_reale.py` | **nuovo**, `PraticaRealeMixin` (conseguenze reali, confronto, recupero) |
| `gioco27/gui/simulator_tab.py` | mixin, `SessionePratica.da_disposizione`, piano fissato, dispatch delle modalità, riga di stato spostata sotto le impostazioni (H2) |
| `gioco27/gui/tavola_tab.py` | pulsante «Pratica questa disposizione» e callback `on_pratica` |
| `gioco27/gui/app.py` | `_pratica_disposizione(numero)` |
| `gioco27/i18n.py` | 53 chiavi nuove, IT ed EN |
| `tests/test_errori_fisici_i3.py` | **nuovo**, 35 test |
| `tests/test_pratica_reale_i3.py` | **nuovo**, 18 test |
| `tests/test_layout_accessibilita_h2.py` | + 7 test I3 |
| `tests/test_i18n*.py` (3 file) | conteggi delle chiavi aggiornati (1441) |
| `tests/test_navigazione_i2.py` | guardia Tavola → Simulatore evoluta (§ 26) |

## 5. API del core

| API | Contratto |
|---|---|
| `gioco_reale.mescolamento_per_colonna(colonna, cifra, preferisci_semplici=True)` | la scelta di **una** fase del trucco: SCD se basta, altrimenti la permutazione che conserva l'ordine. `risolvi_trucco` la chiama; la sua uscita è invariata (TEST `test_la_regola_per_fase_e_quella_di_risolvi_trucco`, su tutte le coppie) |

Nessun'altra API del core è cambiata.

## 6. Service `services.errori`

CODICE. Il service è puro: dipende solo da `core` e da `services.tabellone` e non contiene testo (TEST
`test_il_service_e_puro`, `test_il_confronto_e_strutturato_e_senza_testo`).

| Tipo / funzione | Ruolo |
|---|---|
| `TipoErrore` E1…E6, `VoceCatalogo`, `CATALOGO` | catalogo. E6 ha `fasi=()`, `simulato=False` e `resta_nella_tavola=False` |
| `SessioneErrori(carta, bersaglio, mescolamenti, guidata_dal_bersaglio)` | `da_trucco(c, t)`, `da_disposizione(numero, carta)`, `procedura`, `cifra_bersaglio(fase)` |
| `GestiFase` | colonna indicata, impilamento eseguito, E3, E2 |
| `EventoErrore` | fase, tipo, colonna reale e indicata, impilamento corretto ed eseguito |
| `avvia`, `esegui_fase`, `esegui`, `traccia`, `traccia_prevista` | l'esecuzione, un'unica sequenza fisica globale: `T_eseguita[c] = mazzo_finale.index(c)` |
| `PassoEseguito`, `StatoEsecuzione`, `TracciaEseguita` | stato e traccia, previsto ed eseguito per fase |
| `confronta` → `ConfrontoPianoEseguito` | T, riga, posizione e cifre previste ed eseguite, cifre cambiate, fasi divergenti, `piano_modificato`, `realizzabile_da_riga` |
| `recuperi`, `applica_recupero` → `OpzioneRecupero` | recupero A. Un'opzione di un'altra fase dà `ValueError` |
| `ritorno_eseguito` → `EsitoRitorno` | recupero B, tramite `tabellone.numero_di` / `tabellone.ritorno` |

**Modello dell'esecutore**: si segue il piano congelato (`piano_corrente`). Con E4 in una sessione guidata dal
bersaglio, il mescolamento inteso è la regola applicata alla colonna **indicata** e alla cifra della fase. In una
sessione a piano fissato, E4 viene registrato ma non cambia la scelta (TEST
`test_e4_in_un_piano_fissato_non_cambia_la_scelta`).

## 7. E1 — impilamento non corrispondente al mescolamento (CDS ↔ DSC)

E1 si ha quando l'impilamento eseguito coincide con il mescolamento inteso ma questo è diverso da quello corretto.
Può accadere solo con CDS/DSC, le uniche sigle non auto-inverse (TEST `test_e1_solo_per_cds_dsc`).

Caso dell'audit, ESEC/TEST: riga #111. Con E1 alla fase 1 si arriva a 19, cioè alla riga #112; con E1 alla fase 3
si arriva a 11, cioè alla riga #147.

Esaustivo, TEST: sui 216 casi l'errore sposta **solo** la cifra della propria fase.

## 8. E2 — mazzo rovesciato dopo la raccolta

Caso dell'audit, TEST: con CSD³, E2 alla fase 1, 2 o 3 porta la carta a 25, 22 e 13 rispettivamente.
* **Alla fase 3** la carta arriva al bersaglio, ma la trasformazione è J∘T (riga #172), non T. Il confronto lo dice
  con `bersaglio_raggiunto=True` e `stessa_trasformazione=False` (TEST
  `test_e2_fase_3_carta_al_bersaglio_ma_T_diversa`).
* **Periodo**: con E2 il periodo è 3.

Esaustivo, TEST: 216 righe × 3 fasi × 27 carte = 17 496 casi. E2 può cambiare fino a 3 cifre.

## 9. E3 — ordine interno dei mazzetti invertito

Caso dell'audit, TEST: 25/22/13. Con E3 il periodo è 6. Esaustivo, TEST: E3 resta nella Tavola e può cambiare fino
a 2 cifre.

## 10. E4 — colonna indicata sbagliata

Caso dell'audit, TEST: trucco 0 → 13. Indicando la colonna 1, il mescolamento inteso è SCD e la carta finisce in 12.

Esaustivo, TEST: 729 coppie × 6 = 4374 casi. La cifra cambiata è solo quella della fase.

Combinazione E4 + E1 nella stessa fase, TEST: sessione (2, 2), colonna indicata 0 → DSC.

## 11. E5 — impilamento alternativo diverso da E1

TEST: 216 × 15 − 216 = 3024 casi. Anche qui cambia solo la cifra della fase.

## 12. E6 — traslazioni (solo catalogo)

TEST, con un oracolo costruito nei test: fra le 26 traslazioni C_k non banali, **C_9 e C_18 sono nella Tavola**, le
altre 24 no.

Nel prodotto E6 è solo una voce di catalogo: nessuna simulazione, nessun atomo, nessuna estensione del
linguaggio.

## 13. Casi fissi: riepilogo

| Caso | Atteso | Esito |
|---|---|---|
| E1 #111, fase 1 | 19 / #112 | ✔ |
| E1 #111, fase 3 | 11 / #147 | ✔ |
| E2 CSD³, fasi 1/2/3 | 25 / 22 / 13, fase 3 T = #172 (J∘T) | ✔ |
| E3 CSD³, fasi 1/2/3 | 25 / 22 / 13, periodo 6 | ✔ |
| E4 0 → 13, colonna indicata 1 | SCD → 12 | ✔ |
| E6 | C_9, C_18 nella Tavola; 24 fuori | ✔ |
| recupero dopo E3 alla fase 1 | 0 → 13, opzione applicabile | ✔ |
| ritorno dopo E2 finale | inverso esatto di `tabellone.ritorno(172)` | ✔ |

## 14. Conteggi esaustivi

TEST; il service è confrontato con l'oracolo di caratterizzazione:

| Verifica | Casi |
|---|---|
| E1, localizzazione a una cifra | 216 |
| E2 (tutte le carte) | 17 496 |
| E2/E3 via service contro l'oracolo | 1296 |
| E4 via service contro l'oracolo | 4374 |
| E5 via service contro l'oracolo | 3240 (3024 alternative) |
| ritorno della trasformazione eseguita | 1944 (216 × 3 × 3) |
| recuperi dopo errori alle fasi 1 e 2 | tabella del § 15 |

## 15. Recupero A — ripianificazione residua

TEST `test_recuperi_esaustivi_dopo_errori_alle_fasi_1_e_2`. Ogni coppia è (tipo, fase) e riporta quanti casi
hanno un recupero (✔) e quanti no (✘):

| Tipo | Fase | ✘ | ✔ |
|---|---|---|---|
| E1 | 1 | 162 | 0 |
| E1 | 2 | 162 | 0 |
| E2 | 1 | 486 | 243 |
| E2 | 2 | 648 | 81 |
| E3 | 1 | 0 | 729 |
| E3 | 2 | 486 | 243 |
| E4 | 1 | 729 | 0 |
| E4 | 2 | 729 | 0 |
| E5 | 1 | 486 | 243 |
| E5 | 2 | 486 | 243 |

**Legge** (INFERENZA confermata dal TEST): quando l'errore ha già scritto una cifra sbagliata, le fasi successive
non possono riscriverla, per la «macchina che dimentica» di I2. Per questo E1 e E4, che cambiano la cifra della
propria fase, non sono mai recuperabili. Dopo la fase 3 non ci sono recuperi residui (TEST).

## 16. Recupero B — ritorno

TEST: `ritorno_eseguito` usa `tabellone.numero_di` e `tabellone.ritorno`, cioè T_eseguita⁻¹.
* Se T_eseguita è una riga della Tavola, il ritorno è disponibile ed è esattamente l'inverso.
* Altrimenti `disponibile` è falso e la UI lo dice.

## 17. Modalità della Pratica

| Modalità | Comportamento |
|---|---|
| **Valutazione** (predefinita, storica) | invariata: valuta la scelta e applica **sempre** il mescolamento corretto (TEST `test_la_logica_storica_e_ancora_nel_percorso_storico`) |
| **Conseguenze reali** (opt-in) | applica il gesto eseguito. La colonna indicata può essere sbagliata (E4), l'impilamento può essere E1/E5 e la domanda d'ordine offre «nessun errore fisico / E2 / E3» |

In conseguenze reali la Pratica mostra:
* un **confronto** per fase, in testo leggibile con righe marcate «=» o «≠», cifre n2/n1/n0 e colonna e mescolamento
  previsto/eseguito;
* il **recupero**, mostrato solo dopo un evento: elenco delle opzioni e pulsante «Applica», oppure una frase che
  dice che non c'è recupero;
* un **riepilogo** con T prevista ed eseguita, riga, posizione, cifre cambiate e ritorno.

Cambiare modalità ricomincia la stessa sessione con gli stessi input.

## 18. Piano fissato (Tavola → Pratica)

CODICE/TEST:
* **Nella Tavola**: il pulsante «Pratica questa disposizione» si attiva selezionando una riga, anche in Principiante.
* **Nel Simulatore**: `imposta_disposizione_fissa(numero)` blocca il bersaglio (T[carta]) e mostra un'etichetta
  con il pulsante «Togli».
* **Sessione**: `SessionePratica.da_disposizione` usa le stesse chiavi del piano, più `disposizione_fissata`.
* **`risolvi_trucco` non è chiamato** (TEST con monkeypatch).
* **Selezione**: selezionare una riga non tocca la Pratica.
* **Uscita**: togliendo il piano fissato si torna al trucco.

## 19. Distinzione previsto / eseguito (D-I3-6)

* Il service restituisce campi separati per ogni grandezza.
* La UI scrive «previsto … / eseguito …» e marca le differenze con «≠», non solo col colore (TEST
  `test_cifre_diverse_segnate_non_solo_col_colore`).
* Le chiavi nuove non contengono «equivalente» (ESEC: grep sul diff).

## 20. Blocker del § 20 della consegna

Nessuno dei blocker A–H si è verificato. I casi fissi sono stati riprodotti tutti (§ 13) e il caso E4 dell'audit non
è un blocker.

## 21. i18n

* **Chiavi**: 53 nuove (`practice.real.*`, `simulator.fixed.*`, `nav.practice_disposition`), simmetriche IT/EN.
  Il totale sale a 1441.
* **Termini**: nessun termine narrativo nuovo (Seldon, Giullare, Gaia, Cronaca) e nessun nome di gruppo (G/H/Γ)
  nelle etichette nuove (ESEC: grep).
* **Guida, glossario, `TAB_HELP` e onboarding non modificati.** Le chiavi `guide.*`, `help.*` e `onboarding.*`
  sono intatte: il diff di `i18n.py` aggiunge solo le 106 righe delle 53 chiavi, più due commenti.
* **Inglese** verificato forzando davvero la lingua prima di costruire il frame (TEST `test_in_inglese_davvero`,
  `test_i3_la_pratica_reale_sta_in_1280_anche_in_inglese`).

## 22. H2 e layout

ESEC, prima della correzione: il contenuto del Simulatore chiedeva 1399 px. Con le barre accese a 1280 e 1366, la
riga «Impostazioni» (carta, bersaglio, Calcola e stato «Sequenza: … (disposizione #N della tavola)») stava su
un'unica riga.

**Correzione**: la riga di stato va sotto le impostazioni. La larghezza scende a 1003 px.

TEST (7 nuovi in `test_layout_accessibilita_h2.py`):

| Test | Contratto |
|---|---|
| `test_i3_la_pratica_reale_si_raggiunge` × 3 geometrie | nessun controllo perso e nessuno scorrimento orizzontale; confronto, recupero, radio fisiche e conferma sullo schermo |
| `test_i3_il_confronto_e_testo_leggibile_e_marcato` | Text di sola lettura che prende il fuoco, con «≠» |
| `test_i3_ordine_di_tab_nella_domanda_d_ordine` | impilamento → errore fisico → conferma (**era rosso**: la conferma veniva prima delle radio; corretto con l'ordine di impilamento) |
| `test_i3_il_ridimensionamento_non_innesca_cicli` | barre stabili fra 1280, 1920 e 1366 |
| `test_i3_la_pratica_reale_sta_in_1280_anche_in_inglese` | ≤ 1240 px in inglese |

Nessun Canvas nuovo: `test_i_canvas_del_programma_sono_censiti` è invariato e verde.

## 23. Compatibilità (semanticamente invariati)

`risolvi_trucco`, `procedura_storica`, `procedura_sicura`, `ProceduraGioco` (DP3 = A), la Tavola 216, il pannello
di I2, Explorer, Cicli, Presentazione, Protocollo, gli export e R[m].

**Evidenza**: le rispettive suite sono verdi e non ci sono diff su quei moduli. L'unica eccezione è
`gioco_reale.py`, dove `risolvi_trucco` delega a `mescolamento_per_colonna` con uscita verificata identica.

## 24. Invarianti architetturali

ESEC (AST inline) e TEST (`test_lifecycle_persistenza_g2.py`, `test_static.py`, `test_servizi_g1.py`):

| Invariante | Valore |
|---|---|
| core → services | 0 |
| core → gui | 0 |
| services → gui | 0 |
| services → tkinter | 0 |
| cicli d'importazione | 0 |
| parser autorevoli | 1 |

**Nota**: la guardia G2 ha trovato un ciclo `gui.pratica_reale → gui.simulator_tab`, nato dall'import pigro dei
nomi di colonna. È stato corretto nel commit `0515e02`: il mixin legge le stesse chiavi i18n.

## 25. Suite

Un file per volta sotto xvfb:

| Insieme | Esito |
|---|---|
| test I3 | 35 + 18 + 7 H2 = **60** passed |
| baseline matematica | 25/25 |
| suite completa: 46 file, 1664 test | **1662 passed, 1 skipped, 1 failed** |

* **Skipped**: `test_layout_dettaglio.py` (manca `pypdfium2`).
* **Failed**: `test_layout_accessibilita_h2.py::test_lo_scorrimento_si_accende_quando_il_testo_cresce`, il noto
  fallimento ambientale Tk 9, non modificato.
* **Rispetto a I2**: 1604 + 60 = 1664. Nessuna nuova regressione.

## 26. Tensioni e limiti registrati

1. **Periodo di E3.** L'audit dice che E3 ha periodo 6 «invece di 3», ma il piano CSD³ ha periodo proprio 2. Il
   «3» è quindi il periodo di E2, non del piano. Si registra; il documento dell'audit non si corregge.
2. **E6.** C_9 e C_18 sono nella Tavola. L'affermazione «le traslazioni escono dalla Tavola» vale per 24 casi
   su 26.
3. **«Una sola cifra»** vale per E1, E4 ed E5, non per E2 (fino a 3 cifre) né per E3 (fino a 2).
4. **Recupero.** Il recupero è impossibile quando una cifra già scritta è sbagliata. Il recupero A non è quindi
   universale: la UI lo dice invece di tacere.
5. **Guardia di I2 evoluta.** La guardia I2 «nessun collegamento Tavola → Simulatore» è diventata:
   * `tavola_tab` non contiene `risolvi_trucco`;
   * c'è un solo `self._on_pratica(`;
   * il pannello ternario non nomina il simulatore.

   Il collegamento D-I3-7 è l'unico ammesso.
6. **Debito H2 in inglese.** `test_il_layout_regge_anche_in_inglese` dipende ancora dalla lingua della
   configurazione. I test I3 forzano invece la lingua direttamente.

## 27. Debiti

**I4**: lo spettatore adattivo; E4 senza colonna tracciata.

**I7**:
* guida, glossario, `TAB_HELP` e onboarding per la modalità «conseguenze reali», il recupero e il piano fissato;
* gli allineamenti già elencati in I2.

**DP10**: il taglio come atomo del linguaggio resta non deciso (E6 resta solo nel catalogo).

**H2/J**: la dipendenza dalla configurazione del test inglese; il fallimento Tk 9 da riesaminare nell'ambiente di
riferimento.

**Aperte**: DP1, DP2, DP7–DP12 invariate.

## 28. Gate

| # | Gate | Esito |
|---|---|---|
| G1 | D-I3-1…7 applicate | ✔ § 2 |
| G2 | nessun PRE-I3 separato | ✔ |
| G3 | DP3 = A preservata | ✔ |
| G4 | `adattamento_fisico` solo come oracolo | ✔ |
| G5 | una sola regola per fase (`mescolamento_per_colonna`) | ✔ |
| G6 | `risolvi_trucco` invariato | ✔ |
| G7 | ordine fisico per fase come da consegna | ✔ § 3 |
| G8 | un'unica sequenza fisica globale | ✔ |
| G9 | E1 casi dell'audit | ✔ |
| G10 | E1 esaustivo, una cifra | ✔ |
| G11 | E1 solo CDS/DSC | ✔ |
| G12 | E2 casi dell'audit | ✔ |
| G13 | E2 fase 3 = J∘T | ✔ |
| G14 | E2 esaustivo (17 496) | ✔ |
| G15 | E3 casi dell'audit e periodo 6 | ✔ |
| G16 | E3 esaustivo, resta nella Tavola | ✔ |
| G17 | E2/E3 cifre multiple dichiarate | ✔ |
| G18 | E4 caso dell'audit | ✔ |
| G19 | E4 esaustivo (4374) | ✔ |
| G20 | E4 con piano fissato non cambia la scelta | ✔ |
| G21 | E5 esaustivo (3024/3240) | ✔ |
| G22 | E6 solo catalogo, niente atomo, DP10 aperta | ✔ |
| G23 | E6 C_9/C_18 registrati | ✔ |
| G24 | eventi multipli nell'ordine fisico | ✔ |
| G25 | E4 + E1 nella stessa fase | ✔ |
| G26 | service puro, senza testo | ✔ |
| G27 | gesti non validi rifiutati | ✔ |
| G28 | confronto strutturato previsto/eseguito | ✔ |
| G29 | recupero A ≤ 36/6 suffissi, tutti quelli che raggiungono, ordinati | ✔ |
| G30 | recupero A applicabile; altra fase rifiutata | ✔ |
| G31 | recuperi esaustivi alle fasi 1 e 2 | ✔ § 15 |
| G32 | nessun recupero dopo la fase 3 | ✔ |
| G33 | recupero B = T_eseguita⁻¹ via I2 | ✔ |
| G34 | ritorno esaustivo (1944) | ✔ |
| G35 | Pratica storica default e invariata | ✔ |
| G36 | conseguenze reali opt-in | ✔ |
| G37 | E1–E5 raggiungibili dalla Pratica | ✔ |
| G38 | cambio di modalità = stessa sessione | ✔ |
| G39 | confronto per fase in testo | ✔ |
| G40 | recupero mostrato solo dopo un evento | ✔ |
| G41 | «nessun recupero» detto esplicitamente | ✔ |
| G42 | riepilogo con T prevista/eseguita e ritorno | ✔ |
| G43 | mai «equivalente» generico | ✔ |
| G44 | Tavola → Pratica con piano fissato | ✔ |
| G45 | niente `risolvi_trucco` nel piano fissato | ✔ |
| G46 | la selezione non tocca la Pratica | ✔ |
| G47 | piano fissato removibile | ✔ |
| G48 | i18n IT/EN simmetrico | ✔ |
| G49 | inglese verificato forzando la lingua | ✔ |
| G50 | guida, glossario, `TAB_HELP`, onboarding intatti | ✔ |
| G51 | nessun termine narrativo o di gruppo nuovo | ✔ |
| G52 | H2 alle tre geometrie, senza barra orizzontale | ✔ |
| G53 | ordine di Tab = ordine visivo | ✔ |
| G54 | niente solo colore («=/≠») | ✔ |
| G55 | nessun Canvas nuovo | ✔ |
| G56 | ridimensionamento senza cicli | ✔ |
| G57 | architettura a zero, parser autorevole 1 | ✔ |
| G58 | baseline 25/25, test I1 e I2 verdi | ✔ |
| G59 | unico fallimento = Tk 9 noto; nessuna regressione | ✔ |
| G60 | PDF non tracciati, `.gitignore` intatto | ✔ |
| G61 | nessun push, I4 non iniziato, nessun accesso fuori dal repository | ✔ |
| G62 | documenti precedenti non corretti retroattivamente | ✔ |
| G63 | ciclo d'importazione trovato e rimosso | ✔ § 24 |

## 29. Commit

| Commit | Messaggio |
|---|---|
| `b55d6a9` | `test(I3): characterize physical error consequences` |
| `75bf7cd` | `feat(I3): add physical error trace service` |
| `575ea8b` | `feat(I3): add residual recovery and executed return` |
| `c8880c5` | `feat(I3): add real-consequences practice mode` |
| `ffaaeb0` | `feat(I3): practice a fixed table disposition` |
| `7277ce7` | `test(I3): enforce error recovery accessibility contracts` |
| `0515e02` | `fix(I3): break the practice mixin import cycle` |
| (questo) | `docs(I3): close physical errors and recovery compartment` |

## 30. Stato Git

Prima del commit di chiusura:

```
## main...origin/main [ahead 88]
?? Articolo.pdf
?? LIBRO_MAIN.pdf
```

Dopo il commit di chiusura i commit avanti sono 89, con gli stessi due PDF non tracciati. Nessun push; I4 non è
iniziato.
