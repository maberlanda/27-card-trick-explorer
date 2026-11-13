# H1 — Correttezza della presentation e localizzazione

Primo blocco del compartimento H.

## 1. Identità

| | |
|---|---|
| Branch | `main` |
| HEAD iniziale | `629e048` — *docs(G2): close the application services compartment* |
| HEAD finale | il commit di questo documento — *docs(H1): record presentation correctness milestone*, ottavo e ultimo di H1 |
| `origin/main` | `54445af`, invariato — **nessun push** |
| Commit locali di H1 | 8 |
| Versione | 3.1.3 (invariata) |

## 2. Nota di perimetro

Tutto il lavoro è avvenuto **dentro il repository corrente**: nessun worktree, checkout, clone,
copia o script di lavoro esterno; nessuna directory padre o sorella consultata; nessun file di
appoggio fuori dal repository; nessuna vecchia copia del progetto aperta. I controlli
occasionali sono stati comandi Python inline, e ciò che meritava di restare è diventato un test
dentro `tests/`. Gli unici accessi al filesystem esterni al repository sono le directory
temporanee di pytest, usate per provare l'I/O reale del programma.

## 3. Baseline all'ingresso

```text
pytest tests/test_baseline_matematica.py     25 passati
suite completa                               1298 raccolti
                                             1297 passati
                                                1 saltato   (N03, pypdfium2 assente)
                                                0 falliti
```

Corrisponde alla baseline attesa dopo G2. `git status`: *working tree clean*, `main` avanti di
49 commit su `origin/main`.

## 4. Audit dei messaggi che arrivano all'utente

Fatto **prima** di qualunque modifica.

| Eccezione | Nasce in | Dati strutturati | Diventa testo in | Già localizzato |
|---|---|---|---|---|
| `ParseError` | `core/algebra` | — | il core stesso, con `tr()` | **sì** (E) |
| `EspressioneNonSimulabile` | `core/espressione` | — | il core stesso, con `tr()` | **sì** (E) |
| `ExportTooLarge` | `core/parallel` | `requested`, `limit` | `gui/app`, con `tr()` | **sì** (B) |
| `AnalisiTroppoGrande` | `core/analisi` | `richieste`, `limite` | `gui/analysis_tab`, con `tr()` | **sì** (F) |
| `ConfigNonSalvata` | `core/config` | `percorso`, `causa`, `operazione` | `gui/app`, con `tr()` | **sì** (G2) |
| `SchemaNonRiconosciuto` | `core/analisi` | nessuno | `str(exc)` nel worker | **no** |
| `PermutazioneNonValida` | `core/dominio`, `core/analisi` | nessuno | `str(exc)`, e dentro `RigaScartata.motivo` | **no** |
| `FiltroNonValido` | `core/combinations` | nessuno | `str(errore)` nel preflight | **no** |
| diagnostica import | `core/analisi` + `services/analisi` | `lette`, `scartate` | frase composta **nel core** | **no** |

Due constatazioni hanno guidato il resto.

La prima: i messaggi del core sono **neutri di proposito**, e devono restare tali. Un'eccezione
descrive un fatto, non una frase; il suo testo finisce nel log, nei test e nei rapporti, dove
una traduzione sarebbe un danno. Un test lo verifica: lo stesso errore, letto in italiano e in
inglese, produce lo stesso `str(exc)`.

La seconda: sei moduli del core (`combinations`, `detail_pdf`, `algebra`, `gioco_reale`,
`espressione`, `export_analisi`) usano già `gioco27.i18n` — il catalogo condiviso alla radice
del package, **non** `gioco27.gui.i18n`. È il testo che finisce dentro i documenti prodotti
(PDF, CSV, intestazioni), non nelle finestre, ed è una scelta dei compartimenti precedenti che
H1 non ha toccato. Nessun modulo di `core/` o `services/` importa la i18n della presentation, e
un test lo sorveglia.

## 5. M01 — la selezione vuota dei filtri

### Prima

`FilterFrame.get_filter`, da sempre:

```python
elif len(selected) == 0:
    result[name.lower()] = opts[0]   # fallback
```

Togliendo l'ultima casella di un livello P o J, il filtro non diventava vuoto: prendeva la
prima opzione, che è l'identità (`SCD_U` per P, `I_3` per J). Il risultato era corretto e il
pannello mostrava sei caselle spente. L'utente vedeva un livello senza valori e otteneva quello
dell'identità, senza nulla che glielo dicesse.

Il fallback è applicato solo quando il menu «Fissa» è su `*`: una scelta fissa ha sempre avuto
la precedenza, e continua ad averla.

### Dopo

La semantica **non cambia**: passare da «nessuna selezione → identità» a «nessuna selezione →
insieme vuoto» altererebbe i risultati ed è una decisione di prodotto, non una correzione. La
sostituzione smette invece di essere invisibile: togliendo l'ultimo valore, la prima opzione si
riaccende sotto gli occhi di chi guarda, e il tooltip del livello dice perché.

La traccia sulla `BooleanVar` è ora sempre registrata, anche quando il pannello non ha
`on_change`: non serve solo a notificare, è dove il riallineamento avviene. Una guardia evita
la ricorsione e fa in modo che un click produca **una** notifica, non due.

Il ramo `len(selected) == 0` resta in `get_filter`: dal pannello non ci si arriva più, ma il
filtro deve restare definito anche per chi costruisce un `FilterFrame` a mano, e la semantica
è quella di sempre.

### Prova

Il filtro prodotto è identico, casella per casella. Undici test coprono una scelta, più scelte,
la deselezione dell'ultima (sia scrivendo la variabile sia invocando i `Checkbutton` veri, come
farebbe l'utente), il preset Gioco Reale, il reset, la precedenza del menu «Fissa», il numero
di notifiche e il testo IT/EN — verificando ogni volta **sia** lo stato visibile **sia** il
filtro prodotto. Verificato anche sull'applicazione vera sotto Xvfb.

## 6. M05 — il temporaneo del protocollo

### Caratterizzazione

```text
dove      tempfile.mkstemp(), cartella temporanea di sistema
nome      gioco27_proto_XXXXXXXX.html  (univoco)
URI       pathlib.Path(path).as_uri()  — senza resolve()
durata    per sempre: nessuno lo rimuove
quanti    uno per ogni «Apri nel browser», senza limite
seconda apertura   un secondo file, nessuna sovrascrittura
spazi/accenti/#    già corretti: `as_uri()` fa il quoting
```

Il problema non era «cancellarlo»: il browser legge il file **dopo** `webbrowser.open()`,
spesso molto dopo, e cancellarlo subito aprirebbe una pagina vuota. Mancava una policy.

### Policy

```text
cartella propria    <temp>/gioco27-protocolli
                    «i miei file» diventa una domanda con una risposta, e il
                    cleanup non si affaccia mai sulla temporanea di sistema
nome univoco        mkstemp, prefisso «protocollo-», suffisso «.html»
conservazione       24 ore — generose di proposito: il documento si può tenere
                    aperto, ricaricare o stampare più tardi
cleanup             differito, all'apertura successiva e PRIMA di scrivere il
                    file nuovo, che quindi non è mai un candidato.
                    Nessun demone, nessun servizio di pulizia
riconoscimento      esplicito (`e_un_protocollo`): prefisso, suffisso e file
                    regolare. Mai un file che non sappiamo di aver scritto
robustezza          la pulizia non solleva: non riuscire a fare ordine non è un
                    motivo per non aprire il documento che l'utente ha chiesto
```

L'URI passa ora da `resolve().as_uri()`, come tutte le altre rotte che aprono il browser
(Cayley, coniugio, decomposizioni): su una cartella temporanea raggiunta da un link simbolico
l'URI non risolto punta altrove.

I temporanei degli export non sono toccati: `atomic_write` e `pdfmerge` hanno la loro policy,
che G2 ha già classificato, e il cleanup del protocollo non li vede nemmeno.

### Prova

Undici test, nessuno dei quali apre un browser vero (`webbrowser.open` è iniettato) né assume
`/tmp` (la cartella temporanea è quella di pytest): apertura, file che sopravvive, due aperture
distinte, URI corretto con spazi, accenti e `#` — verificato **aprendo davvero il file
dall'URI prodotto** — pulizia dei soli file vecchi, file recenti preservati, file estraneo
preservato (anche se il nome comincia per «protocollo-» ma non è un `.html`), cartella propria,
pulizia che fallisce, browser che fallisce.

## 7. M06 — il testo dinamico del PDF dettagliato

### Prima

```python
Tt(f"... (+{len(trans) - max_shown} altre)", ...)
```

Era l'ultimo testo naturale in chiaro di un export, e restava italiano anche in inglese.

### Dopo

Due chiavi, non una: «+1 altra» e «+3 altre» non sono la stessa frase, e concatenare un numero
a un plurale fisso produce italiano sbagliato. È il minimo che serve a scrivere frasi corrette
nelle due lingue; un motore di pluralizzazione sarebbe stato una risposta più grande della
domanda.

Non cambia nient'altro: ordine delle trasposte, limite di 60 esempi, posizione, corpo, colore e
layout restano quelli. Restano fisse anche le etichette matematiche e quelle ereditate dal
programma C — `D#12`, `R[ 3]`, `M2 = TRUE`, `M[0]xM[1]xM[2]`, i numeri di posizione, il filetto
di separazione: non sono lingua, e in inglese si leggono uguali.

### Prova

Test end-to-end: il PDF viene generato davvero con ReportLab e riletto con pypdf. Sotto il
limite non compare nessuna coda; sopra il limite compare in italiano e in inglese, con la frase
giusta anche per una sola trasposta in più; l'ordine e il limite sono verificati sul testo
estratto. Un guardiano statico controlla che in `render_detail_pages` non torni un letterale di
lingua naturale, distinguendolo dalle etichette — ed è stato provato per mutazione,
reintroducendo la vecchia f-string.

## 8. Errori applicativi localizzati

`gioco27/gui/errori.py` è il confine dove un fatto constatato dal core diventa una frase.
Riceve l'eccezione (o una riga scartata) e restituisce titolo e messaggio nella lingua attiva,
componendoli dai **dati strutturati** e non leggendo il messaggio: niente
`if "fuori dall'intervallo" in str(exc)`. Due funzioni pubbliche, tre tabelle; il core non lo
importa e non sa che esiste.

### Struttura aggiunta al core, e perché

I dati non c'erano tutti. Tre tipi ricevono un `codice` stabile e i `dati` che lo descrivono,
**senza cambiare di una virgola il messaggio** — `str(exc)` resta quello di prima, e nessun
test del core è cambiato:

| Tipo | Codici | Dati |
|---|---|---|
| `PermutazioneNonValida` | 10 (`lunghezza`, `fuori_intervallo`, `valore_ripetuto`, `non_intero`, `campo_vuoto`, …) | nome dell'API, valore, posizione, intervallo, lunghezza attesa |
| `SchemaNonRiconosciuto` | 4 (file vuoto, senza intestazione, schema non importabile, intestazione ignota) | nome dello schema, colonne trovate |
| `RigaScartata` | il codice e i dati dell'eccezione che l'ha prodotta, più 3 motivi di incoerenza fra formula e T | numero di riga, campo, dati del motivo |

`FiltroNonValido` **non** riceve codici: dopo M01 il pannello non può più produrre un filtro
invalido, e quando l'eccezione compare viene da un'API o da un filtro costruito a mano. Il
confine mostra una frase completa e manda il dettaglio tecnico nel log, che è dove serve.

### Punti di innesto

```text
common.run_in_thread     dove finiscono gli errori di ogni lavoro di fondo,
                         import CSV compreso. Il titolo resta di chi ha avviato
                         il lavoro, il messaggio passa dal confine
analysis_tab             preflight dei filtri e budget dell'analisi
analysis_tab             la diagnostica dell'import, accanto al riepilogo
```

### Una modifica sotto `services/`

`services/analisi.py` smette di comporre la diagnostica: la nota porta il nome del file e
basta — un dato, non una frase — e `lette` e `scartate` viaggiano interi nel modello. Un
servizio non sa in che lingua verrà letto. È l'unica modifica sotto `services/` e il suo motivo
è esattamente il principio di H1.

### Ripiego

A due gradini, e nessuno dei due solleva: frase specifica → frase generica dell'errore → testo
neutro del core. Una chiave mancante o un segnaposto assente lasciano una riga nel log e
restituiscono il gradino successivo, perché un errore secondario non deve diventare un guasto
mentre si sta già riferendo un guasto. La politica del catalogo non cambia: `tr` continua a
sollevare, ed è giusto che si scopra nei test.

### Diagnostica delle righe scartate

L'informazione non si perde nella traduzione. La presentation mostra quante righe sono state
**lette**, quante **accettate**, quante **scartate**, e per le prime tre il numero di riga, il
campo e il motivo — quest'ultimo composto dal codice e dai dati, non tradotto a mano. La coda è
al singolare o al plurale a seconda di quanti scarti restano. Lo schema CSV non è toccato.

## 9. `ConfigNonSalvata` nella UI

G2 ha reso osservabile il fallimento; H1 lo fa dire da un posto solo. Il principio di G2 resta
intatto e sotto test:

```text
preferenza lingua     salvataggio fallito  →  errore mostrato, ritorna False,
                                              nessun «sarà applicato al riavvio»
dialogo impostazioni  salvataggio fallito  →  errore mostrato, il dialogo NON
                                              si chiude
migrazione all'avvio  silenzio deliberato: non c'è ancora una UI, e nulla viene
                      annunciato come riuscito
geometria in chiusura silenzio deliberato: si perde la geometria, non si
                      impedisce di chiudere
```

I due silenzi restano tali: H1 non introduce finestre durante l'avvio o la chiusura solo per
uniformità. Il messaggio passa ora dallo stesso confine degli altri errori, così la sua
formulazione vive accanto alle altre invece che in un ramo a sé.

La politica della lingua non cambia: si applica al riavvio, come prima. H1 sistema il feedback,
non introduce il cambio a caldo.

## 10. Navigazione per identificatori

Due rotte cercavano una scheda leggendo la sua etichetta:

```python
if "Explorer" in w.tab(tab, "text"):          # explorer_tab
if needle.lower() in nb.tab(tab, "text"):     # app, con una tabella di alias
```

La prima funzionava per una coincidenza — «Explorer» si scrive uguale nelle due lingue. La
seconda no, e infatti aveva già una tabella di alias (`"Simulatore"` → `tr("tab.simulator")`)
per rimediare a mano a un problema che non doveva esistere.

Ogni scheda si registra ora con una chiave stabile al momento in cui viene aggiunta al notebook
(`_aggiungi_scheda`), e la si sceglie con `_seleziona_scheda(chiave)`, che restituisce `True` o
`False` invece di fallire in silenzio. Dodici chiavi, nessuna tradotta: `inizio`, `stadio0-2`,
`simulatore`, `tavola`, `anteprima`, `analisi`, `explorer`, `guida`, `cicli`, `distribuzione`.

La navigazione **non** è stata ridisegnata: stessi punti di partenza, stessi punti di arrivo,
stesso comportamento sulle schede nascoste in modalità principiante.

## 11. Catalogo IT/EN

| | Prima | Dopo |
|---|---:|---:|
| Chiavi IT | 1294 | **1316** |
| Chiavi EN | 1294 | **1316** |
| Chiavi presenti in una lingua sola | 0 | **0** |
| Segnaposti discordanti fra IT ed EN | 0 | **0** |
| Chiavi nuove non citate nel codice | — | **0** |

Le 22 chiavi nuove: `filter.never_empty` (M01), due per la coda delle trasposte (M06) e
diciannove `errore.*` per il confine di presentation. Nessuna chiave è stata rimossa: una
ricerca statica che non trova il consumatore non prova che non ci sia, e le chiavi possono
essere usate dinamicamente.

**Dati stabili non tradotti**, verificato cambiando lingua e rileggendo: intestazioni del CSV,
nomi dei fogli Excel, campi di schema, sigle `SCD/CDS/DSC/…`, `MSC`, `I_3`, `R_U`, `P0/P1/P2`,
`J0/J1/J2`, formule, nomi dei generatori, etichette matematiche del PDF. La lingua
dell'interfaccia non cambia il formato dei dati.

## 12. Testi in chiaro: che cosa è stato corretto e che cosa no

M06 era obbligatorio ed è fatto. Durante l'audit è stato corretto **un solo** altro testo
naturale, la diagnostica dell'import, perché ricade nello stesso percorso e produceva una
discordanza IT/EN dimostrabile.

Il testo grezzo di un'eccezione arriva ancora all'utente in otto moduli, e un censimento li
elenca con il loro perché: sono tutti errori del sistema operativo (disco pieno, permesso
negato) o messaggi che il core produce già localizzati — il parser di E in `shuffle.py`. Il
test fallisce se ne compare un nono, così la decisione resta esplicita invece che dimenticata.

H1 non è stato trasformato in una riscrittura dei 1316 testi.

## 13. Test

| Suite | Esito |
|---|---|
| Baseline matematica (D) | 25 passati |
| Dominio (permutazioni, indici, selftest) | 98 passati |
| I/O e integrità (B) | 28 passati |
| Stato e concorrenza (C) | 36 passati |
| Linguaggio e simulazione (E) | 228 passati |
| Analisi, filtri e budget (F) | 112 passati |
| Servizi e modelli (G1) | 44 passati |
| Lifecycle e persistenza (G2) | 45 passati |
| **Presentation e i18n (H1)** | **65 passati** |
| Cataloghi e audit i18n | 149 passati |
| Statici (pyflakes, nomi non definiti) | 2 passati |
| **Suite completa** | **1363 raccolti, 1362 passati, 1 saltato (N03), 0 falliti, 0 xfail** |

`pyflakes` pulito su `gioco27/` e `tests/`. Nessun `xfail` residuo: gli otto di caratterizzazione
sono stati chiusi uno per uno dai commit che li riguardavano.

Ogni commit è stato verificato con la suite completa sull'albero effettivamente committato
(confrontato per hash):

| Commit | Suite |
|---|---|
| `test(H1)` caratterizzazione | 1322 passati, 1 saltato, 8 xfail attesi |
| `fix(H1)` M01 | 1329 passati, 1 saltato, 6 xfail attesi |
| `fix(H1)` M05 | 1336 passati, 1 saltato, 4 xfail attesi |
| `fix(H1)` M06 | 1341 passati, 1 saltato, 3 xfail attesi |
| `refactor(H1)` errori localizzati | 1352 passati, 1 saltato, 1 xfail atteso |
| `fix(H1)` navigazione per chiave | 1355 passati, 1 saltato |
| `test(H1)` contratti di presentation | 1362 passati, 1 saltato |

### Portabilità

Niente `chmod`, niente semantica POSIX di `rename`, niente `/tmp`, niente browser reale, niente
`sleep`. I guasti sono iniettati, le cartelle sono quelle di pytest, gli URI si costruiscono
con `pathlib` e si rileggono con `urllib`. I test che aprono widget veri si saltano da soli
quando non c'è un display.

## 14. Sweep dei difetti

```text
B01  CORRETTO     5 test      B02  CORRETTO     6 test
B03  CORRETTO     7 test      B04  CORRETTO    13 test
B05  CORRETTO    32 test      B06  CORRETTO    57 test
B07  CORRETTO   127 test      B08  CORRETTO     7 test
B09  CORRETTO     7 test      B10  CORRETTO    32 test
B11  CORRETTO    17 test      B12  CORRETTO    12 test

R01  CORRETTO    13 test      R04  CORRETTO    74 test
R05  CORRETTO     6 test      R07  CORRETTO    10 test
```

## 15. Non-regressione del compartimento G

I confini di G1 e G2 restano verificati dai loro test, che scandiscono automaticamente tutti i
moduli del package — quindi anche `gui/errori.py`, nato in H1:

```text
services → gui                      = 0
core → services                     = 0
core → gui                          = 0
cicli statici applicativi           = 0
worker che toccano widget Tk        = 0
rotte di destinazione non atomiche  = 0
R07 corretto                        ✓
parser autorevoli                   = 1
```

## 16. Metriche prima / dopo

| Metrica | Prima (`629e048`) | Dopo | Come è misurata |
|---|---:|---:|---|
| Livelli del filtro con fallback invisibile | 6 per stadio | **0** | test su UI e filtro |
| File del protocollo senza policy di cleanup | illimitati | **0** (24 h, cartella propria) | test |
| Testi naturali scritti a mano negli export | 1 | **0** | guardiano statico su `render_detail_pages` |
| Percorsi che mostrano un errore applicativo neutro | 3 | **0** | test IT/EN sui percorsi reali |
| Moduli che mostrano `str(exc)` all'utente | 9 | **8**, tutti dichiarati | censimento nel test |
| Rotte di navigazione che leggono un titolo tradotto | 2 | **0** | test statico + test funzionale |
| Chiavi i18n | 1294 | **1316** | test |
| Chiavi asimmetriche IT/EN | 0 | **0** | test |
| `core`/`services` che importano la i18n della GUI | 0 | **0** | test |

## 17. File modificati

| File | Tema | Righe |
|---|---|---|
| `gioco27/gui/errori.py` | **nuovo** — il confine di presentation degli errori | 177 |
| `gioco27/gui/filter_frame.py` | M01: il livello non resta mai vuoto, e si vede | 288 → 333 |
| `gioco27/gui/protocol_dialog.py` | M05: policy del temporaneo, cleanup, URI risolto | 472 → 573 |
| `gioco27/core/detail_pdf.py` | M06: la coda dell'elenco delle trasposte | 952 → 961 |
| `gioco27/core/dominio.py` | codice e dati su `PermutazioneNonValida` | 139 → 168 |
| `gioco27/core/analisi.py` | codice e dati su schema, righe scartate, formula | 462 → 502 |
| `gioco27/services/analisi.py` | la nota dell'import torna a essere un dato | 165 → 167 |
| `gioco27/gui/common.py` | il worker mostra il messaggio dal confine | 290 → 296 |
| `gioco27/gui/analysis_tab.py` | filtri, budget e diagnostica dal confine | 815 → 820 |
| `gioco27/gui/app.py` | schede registrate per chiave stabile | 1253 → 1268 |
| `gioco27/gui/explorer_tab.py` | `_switch_to_explorer` per chiave | — |
| `gioco27/gui/onboarding_tab.py` | due rotte di navigazione per chiave | — |
| `gioco27/i18n.py` | +22 chiavi simmetriche IT/EN | 2673 → 2745 |
| `tests/test_presentation_i18n_h1.py` | **nuovo** — 65 test | 992 |
| `tests/test_servizi_g1.py` | la nota del risultato è il nome del file | — |
| `tests/test_i18n.py` | selezione per chiave; conteggi | — |
| `tests/test_i18n_anomalie_ui.py`, `tests/test_i18n_audit_finale.py` | conteggio chiavi 1316 | — |

## 18. Commit locali

```text
04ba5de  test(H1): characterize presentation and i18n debts
35c304d  fix(H1): make the empty filter selection visible (M01)
1522509  fix(H1): define the protocol temporary-file policy (M05)
3def953  fix(H1): localize the dynamic detail PDF text (M06)
83c9d02  refactor(H1): localize application errors at the presentation boundary
1b9daa5  fix(H1): select tabs by a stable identifier, not by their title
1935ac9  test(H1): enforce IT/EN presentation contracts
  ⟵      docs(H1): record presentation correctness milestone  (questo documento)
```

Nessun `push`, nessun `reset` o `rebase` distruttivo, nessun commit precedente riscritto.

## 19. Git status finale

```text
On branch main
Your branch is ahead of 'origin/main' by 57 commits.
  (use "git push" to publish your local commits)

nothing to commit, working tree clean
```

Nessun `__pycache__`, nessun `.pytest_cache`, nessun file di lavoro residuo.

## 20. Gate di uscita

| Gate | Esito |
|---|---|
| H1-G1 M01 non è più un fallback invisibile | **OK** — § 5 |
| H1-G2 la semantica matematica di M01 non è cambiata | **OK** — § 5, filtro identico |
| H1-G3 M05 ha una policy esplicita di retention/cleanup | **OK** — § 6 |
| H1-G4 il file del protocollo non viene cancellato mentre il browser può usarlo | **OK** — § 6, 24 h |
| H1-G5 URI corretti con spazi, accenti e `#` | **OK** — § 6, verificato riaprendo il file |
| H1-G6 M06 completamente localizzato IT/EN | **OK** — § 7 |
| H1-G7 nessun «altre» italiano nell'output inglese | **OK** — § 7, test end-to-end sul PDF |
| H1-G8 errori applicativi principali localizzati dalla presentation | **OK** — § 8, § 12 |
| H1-G9 core/services non dipendono dalla GUI | **OK** — § 4, test |
| H1-G10 il fallimento di `Config.save` non è presentato come successo | **OK** — § 9 |
| H1-G11 i formati dati stabili non vengono tradotti | **OK** — § 11 |
| H1-G12 cataloghi IT/EN con chiavi e segnaposti coerenti | **OK** — § 11 |
| H1-G13 la navigazione non dipende dal testo tradotto | **OK** — § 10 |
| H1-G14 M04 non è stato iniziato | **OK** — § 21, test |
| H1-G15 architettura di G invariata | **OK** — § 15 |
| H1-G16 B01–B12 ancora corretti | **OK** — § 14 |
| H1-G17 matematica invariata | **OK** — baseline 25/25 |
| H1-G18 suite completa verde | **OK** — § 13 |
| H1-G19 nessun I/J/K iniziato | **OK** — § 21 |
| H1-G20 nessuna risorsa di lavoro esterna | **OK** — § 2 |
| H1-G21 nessun push | **OK** — `origin/main` fermo a `54445af` |

## 21. Debiti espliciti per H2 e oltre

**Per H2 — layout, accessibilità, tastiera (M04)**

* dimensioni minime, layout adattivo, DPI, wrapping della toolbar: `App.minsize(1200, 750)` è
  quella di sempre, e un test lo sorveglia perché non cambi per sbaglio;
* focus traversal, `Tab`/`Shift-Tab`, tooltip raggiungibili da tastiera, testo alternativo dei
  Canvas, contrasto;
* il **dialogo delle impostazioni che resta aperto** dopo un salvataggio fallito è la scelta più
  onesta disponibile senza toccare la UX: il dialogo non può dire «fatto» se non lo è. Una
  revisione del flusso — un messaggio in linea invece di una finestra, o un pulsante «riprova» —
  appartiene a H2;
* il tooltip di M01 spiega la regola del livello mai vuoto; se H2 introdurrà un'area di stato
  nel pannello dei filtri, quel testo starà meglio lì;
* le frasi introdotte da H1 sono corrette e simmetriche, ma non sono passate da una revisione
  redazionale complessiva: H2 può rivederne il tono insieme al resto.

**Per H2 — testi rimasti in chiaro**

* gli otto moduli che mostrano ancora `str(exc)` (§ 12) riguardano errori del sistema
  operativo. Se H2 vorrà dare loro una cornice localizzata («Non è stato possibile scrivere il
  file {nome}: {dettaglio}»), il confine di `gui/errori.py` è il posto dove aggiungerla, e il
  censimento è già scritto;
* `distribution_tab` e `decomposition` mostrano l'errore di un worker come stringa in
  un'etichetta di stato: passano da una coda, non da `run_in_thread`, quindi non dal confine.
  Non producono testo applicativo italiano oggi, ma sono le due rotte che lo farebbero per
  prime.

**Per I, J, K**

* nulla proveniente da H1. Restano quelli già dichiarati: `N03` (`pypdfium2`) e `N04`
  (PyInstaller) per K, la cronologia utente per J, gli strumenti matematici avanzati per I.

**Legacy, senza compartimento assegnato**

* le facciate differite di `core.algebra` (G1) e `core.permutations` (G2), entrambe conservate e
  sotto test.
