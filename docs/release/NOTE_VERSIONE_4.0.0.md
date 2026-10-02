# Gioco delle 27 carte — note della versione 4.0.0

> **4.0.0 — release stabile.** Gli audit finali A1–A5 (matematico,
> terminologico, linguistico italiano e inglese, verifica incrociata) sono
> conclusi, con le correzioni verificate in `docs/audits/`. Dopo la RC2 la
> Fase P ha riallineato nomenclatura e riferimenti al libro (sezione
> «Fase P»); anche la Fase P è conclusa.
>
> Punto di partenza: **3.1.3** (`NOTE_VERSIONE_3.1.3.md`). Il dettaglio di ogni
> passo è nei documenti di chiusura in `docs/history/`; il resoconto tecnico
> della fase di preparazione della release candidate è
> `K_RELEASE_CANDIDATE_CLOSED.md`.

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
  cache che distingue validità e completezza, sistema di ripiego per i
  caratteri pronto all'uso.
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
* **Riconoscimento (I5)** — da una permutazione alla riga della Tavola,
  all'appartenenza a Γ, al criterio delle somme.
* **Laboratorio matematico (I6)** — proprietà verificate su un dominio
  dichiarato (S₃, H, Γ, S₂₇, Procedure), controesempi, classi, piccoli grafi.
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

## Fase P — allineamento con il libro (dopo la RC2)

La Fase P confronta il programma con il libro (`LIBRO_MAIN`, dopo la Fase G
del libro: contatori azzerati a ogni capitolo). La prima iterazione non ha
trovato errori matematici; la seconda riallinea nomi, testi e riferimenti,
senza cambiare alcun calcolo.

* **Nomenclatura H/Γ nel core**: `kronecker.appartiene_a_H` indica ora il
  gruppo di **216** elementi (H) e il nuovo `kronecker.appartiene_a_Gamma`
  quello di **648** (Γ = ⟨H, MSC⟩ = H ⊔ H∘MSC ⊔ H∘MSC²).
  `appartiene_a_G` resta come **alias legacy** di `appartiene_a_H`;
  `DECOMPOSIZIONI_PER_TARGET_IN_H` affianca il vecchio nome `…_IN_G`.
  *Cambiamento incompatibile per l'API interna*: fino alla RC2
  `appartiene_a_H` indicava Γ; chi lo usava in quel senso deve passare a
  `appartiene_a_Gamma`.
* **Γ nell'interfaccia**: il Riconoscimento, la CLI (`recognize`) e la Guida
  dicono **Γ** (la scheda si chiama «Γ (classe estesa)»). La chiave JSON
  `classe_estesa` degli esperimenti (schema 1) resta invariata: i file già
  salvati si aprono e si verificano come prima.
* **Riferimenti al libro**: i numeri correnti stanno solo in
  `gioco27/riferimenti.py` (chiavi semantiche, titolo, etichetta LaTeX,
  sezione); i testi usano un segnaposto risolto all'avvio. Aggiornati:
  forma normale delle trasformazioni intermedie (ora Teor. 11.10),
  uniformità del Gioco ordinario (ora Prop. 9.5), auto-inversività
  (ora Prop. 5.2); aggiunta la ricostruzione mediante le fibre digitali
  (Teor. 11.12).
* **Articolo originale e App. D** (iterazione 3): le citazioni «Articolo» con
  numerazione 5.x/6.1 si riferiscono alla versione originale dell'articolo
  (`Articolo.pdf` del 10 settembre 2026, sorgente `8a2e41a`, non pubblicata
  formalmente) e ora lo dichiarano; i numeri stanno in
  `RIFERIMENTI_ARTICOLO_ORIGINALE`, con l'equivalente in App. D quando è
  identico (Teor. 5.1 → App. D Teor. 6.1, Es. 6.1 → App. D Es. 7.1).
  L'osservazione 5.3 non ha un equivalente identico in App. D e resta citata
  come fonte originale. La «fig. 6.8» di un test (numerazione precedente alla
  Fase G del libro) è la griglia delle 27 classi di coniugio, oggi figura 6.3
  (`fig:coniugio-griglia`), con chiave `griglia_classi_coniugio`.
* **Fasi e stadi**: l'interfaccia numera le fasi 1–3, il modello matematico gli
  stadi h = 0, 1, 2 (fase k ↔ h = k − 1); il glossario lo dichiara.
* **Testi**: firma di blocco e somme di fibra descritte come firme
  strutturate, non come invarianti individuali; nella verifica del protocollo
  i numeri delle carte 1–27 sono distinti dalle posizioni 0–26; docstring del
  core con indici 0–2 (A0, A1, A2; f2, f1, f0) e tavola di Cayley di H
  216×216.
* **Roadmap**: le visualizzazioni a grafo sono pianificate per una release
  successiva (`docs/release/ROADMAP_4.x.md`), non fanno parte della 4.0.0.

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

* Alcuni identificatori interni conservano il nome storico G del gruppo di
  216 (alias `appartiene_a_G`, `DECOMPOSIZIONI_PER_TARGET_IN_G`, nomi
  `classe_estesa`/`ClasseEstesa` del servizio e della chiave JSON): non sono
  visibili all'utente e restano per compatibilità (sezione «Fase P»).
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
