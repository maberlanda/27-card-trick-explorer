# Gioco delle 27 carte — v3.0.1 (note di versione)

## PDF dettagliato allineato al layout HTML del programma C

* Titoli dei mazzi come nel C: «Mescolamento 1/2/3 = sigla» con
  l'impilamento (gesto dal dorso) fra parentesi; l'etichetta di gioco è
  ora il fattore **P3** (v3), non più P1 — prima le combinazioni del
  preset comparivano come prodotto «CDS×SCD×SCD» invece di «CDS».
* DISP INIZIALE / DISP FINALE in tabella bordata; celle di POSIZIONE
  ASSO e griglia A_1/A_2/A_3 bordate come le `<td>` dell'HTML.
* Sezione MOLTIPLICAZIONE fedele al C: `M[k]xM[j]xM[i]` con gli indici
  numerici, riga dei **mescolamenti** in grassetto e riga degli
  impilamenti in piccolo.
* Matrice 27×27 con griglia nera (come le celle HTML), intestazione
  **«Matrice: P[i][j][k][m]»** e, sotto, «Mescolamenti … x … x …»,
  «Periodo: N» ed **«Elenco matrici trasposte»** (le combinazioni
  dell'export la cui matrice è la trasposta di quella corrente — per una
  matrice di permutazione, l'inversa), come findAllTransposesInResults.
* Numerazione **D# da 0** come il contatore Cntr del C.
* **Due combinazioni per pagina** (meta' superiore/inferiore, con linea di
  separazione), come l'elenco continuo del C; l'elenco delle trasposte e'
  a destra della matrice, su piu' colonne.
* Ordinamento di stampa corretto: gli indici i, j, k seguono la tabella
  **M dei mescolamenti** del C (SCD SDC CSD DSC CDS DCS), non la tabella
  W degli impilamenti (differiscono per lo scambio CDS↔DSC). La
  numerazione D# = ((i·6+j)·6+k)·8+m è ora verificata da test su tutte
  le 1728 sequenze.

## CPU ed export paralleli

* Default dei worker portato da `cpu/2` a **`cpu−1`** (un core resta
  alla GUI): prima, su macchine con molti core, gli export usavano una
  frazione minima della CPU.
* Blocchi di lavoro ~4× i worker: carico bilanciato (niente processi
  fermi in coda) e barra di avanzamento più fluida.
* I fallback silenziosi al sequenziale ora scrivono il motivo nel log
  (`~/.gioco27/gioco27.log`): se pypdf manca o il multiprocessing
  fallisce, non si scopre più «a occhio» dalla CPU bassa.
* La barra di stato indica quanti processi lavorano all'export.

## Robustezza

* `config.json` salvato con scrittura atomica (tmp + replace): un crash
  a metà salvataggio non lascia più un file troncato.
* Etichetta corretta nelle Impostazioni: CPU **logiche** e default.

## Test

* Aggiornato `test_detail_order_matches_c_numbering` (preset v3 con P3
  libero, indici in ordine M) e aggiunto `test_detail_annotations`
  (coerenza permutazioni ed elenco trasposte). Suite: 80 test.

---

# Gioco delle 27 carte — v3.0.0 (note di versione)

## Correzione sostanziale: il preset «Gioco Reale»

Il preset liberava **P1** (livello unità) come "raccolta", con P2=P3
identità. Verificato contro la tavola del libro: la raccolta fisica agisce
al **livello dei blocchi, cioè P3** (con mescolamenti CDS, CDS, CSD lo slot
P3 produce gli Assi 13, 8, 18 della riga #100; P1 produce 13, 24, 2).

L'errore era invisibile per due ragioni: (a) le tre famiglie P1/P2/P3
libere generano lo **stesso insieme** di 216 tabelloni (la distribuzione
MSC fa ruotare i livelli), quindi conteggi e statistiche erano corretti;
(b) le carte diagonali (gli Assi in partenza: 0, 13, 26) non distinguono
il livello quando i tre mescolamenti coincidono. Cambiava però la
corrispondenza fra singola scelta di raccolta e tabellone. Preset, guida e
glossario ora usano P3.

Nota sui rovesciamenti: nel modello (Stadio = P∘MSC∘J) il J-uniforme dello
stadio i equivale al capovolgimento **prima** della distribuzione dello
stadio i (= dopo la raccolta dello stadio i−1); il capovolgimento dopo la
terza raccolta si ingloba nei P dello stadio 3. Con questa mappa la
corrispondenza fisica↔matriciale è esatta su tutte le 1728 combinazioni
(verificata dal selftest — le divergenze prima della correzione erano
1216, lo stesso conteggio del difetto trovato nel programma C).

## Nuovo modulo `core/gioco_reale.py`

Il gioco fisico in forma canonica, allineato al libro e al C v3:
mescolamento (sigla funzionale, riga del tabellone) vs impilamento (gesto,
inversa; CDS↔DSC = Prima Crisi di Seldon); simulazione carta-per-carta;
numerazione della tavola (# = i1+6·i2+36·i3); T algebrica cifra-per-cifra;
ricostruzione del tabellone dagli Assi; statistiche del capitolo 100;
`risolvi_trucco` in forma chiusa; `selftest()` completo.

## Verifica di integrità

`python -m gioco27 --selftest` oppure pulsante «✔ Verifica» nella GUI:
fisica vs algebra (216), fisica vs matrici (1728), ancore #100/#82,
statistiche cap. 100 (periodi 1/63/26/126, 64 auto-inverse, 7 tipi
ciclici), ricostruzione Assi (216/216), trucco (729/729 coppie).

## GUI

* **Percorso lineare**: Inizia qui → Simulatore → Tavola 216 → Anteprima →
  Analisi → Guida (le schede avanzate restano dietro la modalità Esperto).
  Onboarding e azioni rapide aggiornati; glossario con le voci
  Mescolamento e Impilamento.
* **Simulatore riscritto**: niente più ricerca cieca su 216³ ≈ 10 milioni
  di triple in thread — il calcolo è in forma chiusa e istantaneo (al
  passo i la carta è in una colonna nota: serve il mescolamento che la
  manda nella cifra ternaria giusta del bersaglio). Le istruzioni
  distinguono sempre mescolamento e impilamento (prima le istruzioni
  presentavano come "ordine fisico di raccolta" il fattore f1 di una
  tripla di Kronecker arbitraria, in generale non eseguibile con un solo
  gesto). Visualizzazione con le 7 fotografie fisiche del mazzo; pratica
  interattiva che chiede colonna e impilamento e segnala l'errore
  classico della Prima Crisi.
* **Nuova scheda «Tavola 216»**: la tavola delle disposizioni semplici del
  libro con mescolamenti, impilamenti, Assi, periodo, punti fissi, tipo
  ciclico, parità e auto-inverse; filtro live; doppio clic per T e T⁻¹
  complete; ricostruzione della disposizione dalle posizioni degli Assi;
  esportazione CSV.
* **Presentazione trasformata in «Vista esecutore»**: un gobbo a schermo
  intero per chi esegue il trucco — un passo alla volta (frecce/spazio/
  clic), per ogni fase solo il gesto da compiere in caratteri grandi, la
  matematica in una riga piccola in basso. Prima mostrava T = [perm…] a
  tutto schermo: inutilizzabile davanti al pubblico. Si aggiorna da
  Simulatore ed Explorer; riconosce se la T è una disposizione del gioco.

## Robustezza ed efficienza

* `combinations.py`: il rilevamento di reportlab era un `try` vuoto
  (sempre True anche senza libreria) — corretto con l'import reale.
* `kronecker.py`: rimosso lo `sleep(0.001)` per rilasciare il GIL.
* `analysis.py`: rimossa una `np.argsort` inutilizzata nel ciclo interno
  della distribuzione sequenziale (216² chiamate sprecate).
* Validazione input e messaggi d'errore nel simulatore e nella Tavola.
* Versione portata a 3.0.0.

## Test

`tests/test_gioco_reale.py` (8 nuovi test: Prima Crisi, numerazione,
ancore, fisica=algebra, statistiche, ricostruzione Assi, trucco,
validazione). Suite completa: **79 passed, 2 skipped**.
