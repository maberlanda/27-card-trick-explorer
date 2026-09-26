# Gioco delle 27 carte — note della versione 4.0.0 (release candidate)

> **4.0.0 RC** — release candidate **tecnicamente pronta per l'audit finale**
> matematico, terminologico e linguistico, che resta da eseguire: finché non
> è concluso questa non è la 4.0 definitiva.
>
> Punto di partenza: **3.1.3** (`NOTE_VERSIONE_3.1.3.md`). Il dettaglio di ogni
> passo è nei documenti di chiusura in `docs/history/`; il resoconto tecnico
> della release candidate è `K_RELEASE_CANDIDATE_CLOSED.md`.

## Sintesi

La 4.0 porta il programma da strumento di analisi a percorso didattico e di
ricerca completo: quattro livelli, il modello delle Procedure di gioco, la
Tavola con il livello ternario, gli errori fisici e lo spettatore, il
riconoscimento, un laboratorio di proprietà con dominio dichiarato ed
esperimenti riproducibili. Prima di aggiungere funzioni, una serie di
compartimenti di stabilizzazione (A–H) ha consolidato calcoli, file, stato e
interfaccia; K ha reso il pacchetto installabile e verificabile.

## Stabilizzazione (A–H)

* **A — baseline**: suite e analisi statica verdi, stato Git riconciliato.
* **B — integrità I/O**: pubblicazione atomica dei file, temporanei univoci,
  cache che distingue validità e completezza, fallback dei font utilizzabile.
* **C — stato e concorrenza**: risposte tardive che non ripopolano lo stato,
  pratica su una sessione congelata, ogni lavoro con uno stato conclusivo.
* **D — dominio**: selftest indipendente da `assert`, contratti di
  validazione ai confini delle API matematiche, Tk fuori dal dominio,
  numerazione a base 0 coerente.
* **E — linguaggio e simulazione**: un solo linguaggio delle espressioni, con
  AST, valutazione e traccia comuni a Explorer e Mescolamento.
* **F — analisi**: ingressi validati, un solo contratto per i filtri,
  preflight e budget prima dell'aggregazione.
* **G — servizi e ciclo di vita**: servizi applicativi separati dalla GUI,
  revisioni dei lavori, salvataggio affidabile della configurazione.
* **H — presentazione e accessibilità**: messaggi localizzati composti dai dati
  del core; layout adattivo a 1280×720, 1366×768, 1920×1080; tastiera e
  alternative testuali.

## Novità (I1–I7, J)

* **Procedure (I1)** — modello immutabile delle Procedure (mescolamenti e
  rovesciamenti), relazioni fra procedure, strategie.
* **Tavola e tabellone ternario (I2)** — pannello ternario, flusso di una
  carta, collegamenti fra viste.
* **Errori fisici e recupero (I3)** — confronto piano/eseguito, conseguenze
  reali nella Pratica.
* **Spettatore (I4)** — la carta ignota: dinamica fisica e dinamica
  informativa (27 → 9 → 3 → 1) separate.
* **Riconoscimento (I5)** — da una permutazione alla riga della Tavola, alla
  classe estesa, al criterio delle somme.
* **Laboratorio matematico (I6)** — proprietà verificate su un dominio
  dichiarato (S₃, H, Γ, S27, Procedure), controesempi, classi, piccoli grafi.
* **Percorso didattico (I7)** — quattro livelli (Base, Intermedio, Avanzato,
  Laboratorio), Guida riorganizzata come percorso, glossario, aiuti di scheda.
* **Esperimenti (J)** — finestra 🗂 Sessione: esperimento JSON versionato
  (schema 1, convenzioni J1) salvato in modo atomico; all'apertura ogni
  risultato è ricalcolato e il file è accettato solo se VERIFIED; cronologia
  con annulla/ripristina; successione di procedure con cumulativo C_N, ritorno
  compresso e replay (L90); confronto fra esperimenti; CSV con manifest.
* **Riga di comando (J)** — `validate`, `replay`, `recognize`, `property`,
  `sequence`, `export`, `compare`, `selftest`; codici di uscita stabili.

## Cambiamenti visibili della release (K)

* Versione **4.0.0** da un'unica fonte; `--version` nella riga di comando.
* Comandi installati: `gioco27` (GUI) e `gioco27-cli` (riga di comando).
* Export di Cayley e coniugio: il gruppo di 216 si chiama ora **H**
  (`|H| = 216`, `Z(H)`), non più G.
* Senza una libreria di export facoltativa il messaggio dice quale manca e
  come installarla.
* `avvia.bat` usa il Python Launcher (`py -3`) e scarta l'alias del Microsoft
  Store; in caso di errore esegue la diagnostica delle dipendenze.
* `controlla_requisiti.py` distingue Python, Tk, runtime, export e (con
  `--dev`) test/build; è fatale solo ciò che serve davvero.

## Decisioni di prodotto

* **DP11** — la Tavola è di **216 trasformazioni** (H). Le 1 728 Procedure
  di mescolamenti e rovesciamenti sono **Procedure**, non 1 728 trasformazioni
  distinte: nella 4.0 non esiste una Tavola 1 728. Le procedure equivalenti di
  una riga si vedono come relazione (I1/I2), non come tavola.
* **DP12** — `LIBRO_MAIN.pdf` e `Articolo.pdf` sono **fonti esterne**: restano
  non tracciati, non entrano in sdist, wheel o eseguibile PyInstaller e non
  servono al programma. Un esperimento J può registrarne nome, ruolo e
  SHA-256 se i file sono presenti, senza salvarne il percorso.

## Compatibilità

* **Python 3.10 o superiore** (certificati 3.10, 3.11, 3.12, 3.13, 3.14).
* **Esperimenti J**: un file salvato con la versione di programma 3.1.3 si
  carica e si verifica nella 4.0.0 (stesso schema 1 e convenzioni J1); la sola
  versione del programma non rende incompatibile un esperimento (il confronto
  la riporta come `DIFFERENT_PROGRAM_VERSION`).
* **Configurazione**: le impostazioni 3.x si leggono; i vecchi livelli
  «principiante»/«esperto» sono convertiti in Base/Laboratorio.
* **Export**: CSV e formati esistenti invariati nella struttura; cambia la
  nomenclatura nei testi di Cayley/coniugio (G → H).

## Cambiamenti incompatibili

* Python 3.9 non è più supportato (fine vita a ottobre 2025): la suite passa
  ancora su 3.9, ma il pacchetto dichiara `requires-python >= 3.10`.
* I file di **sessione J** con un livello legacy («principiante»/«esperto»)
  sono rifiutati; i file di configurazione continuano a essere convertiti.
* Metadati di licenza: il pacchetto dichiara `GPL-3.0-only` (la vecchia voce
  «Proprietary» di `pyproject.toml` era un residuo dell'importazione 3.1.1).

## Limiti noti

* **Audit finale** matematico, terminologico e linguistico non ancora eseguito.
* Identificatori interni del core con il nome storico G/H (per esempio
  `appartiene_a_G`, e `appartiene_a_H` che indica Γ): non visibili
  all'utente, registrati per l'audit.
* Il salvataggio atomico non esegue `fsync`; nessuna richiesta di conferma
  alla chiusura con una sessione non salvata (debiti J).
* L'eseguibile Windows e la CI sono configurati ma non ancora eseguiti su un
  runner reale; la build PyInstaller verificata è quella Linux.
* I test di layout dipendono dai font disponibili: le soglie sono ora
  indipendenti dalle metriche dei font Windows.

## Riferimenti di prestazione

Tempi misurati con `python tests/benchmark_k.py` (Linux x86_64, 2 CPU,
CPython 3.12.14, numpy 2.5.3). «Fredda» = prima esecuzione nel processo,
«calda» = migliore di 3. Sono una baseline, non una soglia.

| misura | fredda (s) | calda (s) |
|---|---|---|
| selftest completo | 0,137 | 0,049 |
| Tavola 216 + tabellone | 0,117 | 0,024 |
| riconoscimento (48 permutazioni) | 0,019 | 0,007 |
| laboratorio I6 (catalogo completo) | 0,608 | 0,000 (cache) |
| esperimento J (salva + carica con ricalcolo) | 0,034 | 0,003 |
