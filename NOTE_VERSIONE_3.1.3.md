# Gioco delle 27 carte — note della versione 3.1.3

> **3.1.3** — aggiornamento patch della serie 3.1.x: interfaccia bilingue
> italiano/inglese completa. Nessun cambiamento nei calcoli, nei dati o negli
> schemi dei file esportati.
>
> Punto di partenza: **3.1.2**. Le tappe precedenti (3.1.0 e 3.1.1) sono
> descritte in `NOTE_VERSIONE_3.1.1.md`.

## Sintesi

La 3.1.3 completa l'internazionalizzazione dell'applicazione. Tutto il testo
che l'utente legge (schede, finestre, pulsanti, aiuti, Guida, messaggi che
compaiono dopo un calcolo, un export o una verifica, contenuti esportati)
passa dal sistema di traduzione del programma ed è disponibile in italiano e
in inglese.

La release consolida anche la qualità dell'interfaccia bilingue: dopo la
traduzione è stata fatta una verifica manuale con l'interfaccia in inglese e
poi un audit finale di callback e output dinamici, correggendo i testi
italiani residui che emergevano solo usando il programma.

## Novità principali

### Lingua dell'interfaccia

* **Interfaccia completa italiano/inglese.** L'italiano resta la lingua
  predefinita.
* **Selettore della lingua** in Impostazioni. La scelta viene salvata nella
  configurazione e applicata al successivo avvio; le configurazioni prive
  della voce continuano a partire in italiano.
* **Fallback inglese → italiano**: se una voce inglese mancasse, viene
  mostrato il testo italiano invece di un errore.
* **Cataloghi simmetrici**: stesse chiavi e stessi segnaposto nelle due
  lingue.

### Schede, finestre e testi

* Localizzate tutte le principali schede e finestre: Inizia qui, filtri degli
  stadi (P/J), Simulatore, Tavola 216, Anteprima, Analisi, Explorer (con i
  sotto-tab Numerico, Traccia riscrittura, Forma algebrica, Passi parziali,
  Forma canonica, Matrice, Mescolamento), Cicli, Distribuzione, Decomposizioni,
  Protocollo, Presentazione, Tavola di Cayley, Classi di coniugio,
  Impostazioni, dialoghi di export.
* Localizzati i **testi didattici lunghi**: glossario esteso, banner d'aiuto,
  spiegazioni dei filtri, introduzioni di Cayley e Coniugio.
* **Guida completa bilingue**: tutte le 33 sezioni, con indice, ancore di
  navigazione e formule invariate. La Guida segue la lingua attiva.

### Export

* Localizzati i contenuti esportati **HTML, PDF, TXT, LaTeX e SVG**
  (protocollo, analisi, decomposizioni, Cayley, Coniugio, riepiloghi), inclusi
  i PDF prodotti in parallelo, che ricevono la lingua attiva.
* Localizzati i dialoghi degli export massivi: conferme, limiti di sicurezza,
  barra di stato, annullamento ed errori.

### Output dinamici

* Localizzati gli **output generati dopo un'azione**: callback, messaggi di
  stato e di errore, riepiloghi e diagnostica visibile.
* **Pulsante Verifica / Verify**: il rapporto della verifica di integrità, il
  messaggio di incoerenza e il tooltip restavano in italiano con l'interfaccia
  inglese. Ora seguono la lingua attiva; il rapporto restituito da
  `selftest()` resta un dato invariato (usato anche da riga di comando).
* **Anteprima ed Explorer**: corrette le stringhe residue della scheda
  Anteprima, del riepilogo del sotto-tab Numerico, della Traccia riscrittura
  (legenda R1–R4, nota sull'ordine, spiegazioni di ogni passo) e dei Passi
  parziali (per esempio «Atomo» → «Atom»).
* **Audit finale**: corretti anche i residui trovati ispezionando callback e
  output — errori di parsing dell'Explorer, dettaglio della Tavola 216 e
  ricostruzione dagli Assi, etichette dei filtri P/J, nota della
  Distribuzione, tipo delle classi di coniugio, anteprima del dialogo
  LaTeX/SVG, titolo degli errori nei thread di lavoro.

### Cosa non cambia

* **Formule, simboli e codici** restano invariati in entrambe le lingue
  (`MSC`, `GEN3`, `SCD_U`…`DCS_U`, `I_3`, `R_U`, `T`, `T⁻¹`, `A0/A1/A2`,
  `S/C/D`, `Z(G)`, `⟨A,B⟩`).
* **Dati e schemi CSV/Excel** restano stabili: intestazioni come
  `T_permutazione`, `Stage0..2`, `A0..A2` e i nomi dei fogli Excel non vengono
  tradotti, perché fanno parte del formato dei file.
* Le etichette fisse in stile programma C del PDF dettagliato (`DISP_INIZIO`,
  `ROVESCIAMENTO`, `MOLTIPLICAZIONE`, «TABELLONE DI T») restano come prima.

## Qualità e test

Baseline finale verificata su Windows:

| Voce | Valore |
|---|---|
| Chiavi del catalogo italiano | 1288 |
| Chiavi del catalogo inglese | 1288 |
| Test passati | 673 |
| Test saltati | 5 |

I cataloghi sono simmetrici (stesse chiavi, stessi segnaposto nominati). I
test coprono:

* **i18n**: lingua predefinita, cambio lingua, fallback, parità dei cataloghi e
  dei segnaposto, configurazione;
* **Guida**: contenuto completo nelle due lingue, struttura, ancore,
  riferimenti interni, formule, allineamento con le etichette reali;
* **audit finale**: output del pulsante Verifica in tutti i rami, export,
  errori dell'Explorer, Tavola 216, filtri, dialoghi;
* **output dinamici**: Anteprima, riepilogo Numerico, Traccia riscrittura,
  Passi parziali, con controllo che i risultati non dipendano dalla lingua;
* **regressioni principali**: una guardia verifica che le stringhe italiane
  corrette non ricompaiano nei sorgenti.

## Compatibilità

* I **dati e i risultati matematici non cambiano**: permutazioni, forme
  normali, decomposizioni, periodi e statistiche sono identici alla 3.1.2 in
  entrambe le lingue.
* **Formule e codici** restano invariati.
* **CSV ed Excel** mantengono schema e intestazioni stabili dove servono alla
  compatibilità.
* La configurazione esistente resta valida; la lingua è una voce in più.
* È un **aggiornamento patch** della serie 3.1.x.

## Riferimenti storici

La 3.1.0 aveva introdotto la numerazione a base 0 di stadi e fattori, gli
export a flusso con limiti di sicurezza e numerosi miglioramenti di
prestazioni; la 3.1.1 aveva documentato la convenzione sui nomi doppi e
aggiunto l'annullamento degli export. I dettagli sono in
`NOTE_VERSIONE_3.1.1.md`.
