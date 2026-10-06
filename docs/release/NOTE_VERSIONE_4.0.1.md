# Gioco delle 27 carte — note della versione 4.0.1

> **4.0.1 — release stabile di consolidamento e miglioramento UX della 4.0.0.**
> La matematica e le funzionalità precedenti restano invariate; gli interventi
> rendono più chiari i percorsi, lo stato del lavoro e gli effetti dei comandi.
> Punto di partenza: `NOTE_VERSIONE_4.0.0.md`.

## Stato, sessioni e risultati

* Protezione del lavoro non salvato con **Salva / Non salvare / Annulla**
  prima di chiudere o sostituire una sessione; titoli e note partecipano allo stato.
* Reset con perimetro esplicito: **Reset filtri** e **Reset tutto** distinguono
  le impostazioni di ricerca dal lavoro corrente.
* Selezione di una riga e pubblicazione della trasformazione T sono distinte;
  origine e validità del risultato indicano quando occorre ricalcolare.
* Export più prevedibili: ambito tutte/visibili, conflitti con file esistenti,
  conferme e riepiloghi coerenti, con limiti e omissioni dichiarati.

## Percorsi e aiuto

* **Inizia qui** propone Esegui il trucco, Riconosci un mazzo e Studia una
  trasformazione, con carta/posizione 0–26 e mescolamento/impilamento spiegati.
* **Pratica** chiarisce feedback, cambio modalità, piano iniziale/attivo e
  recupero; il collegamento dalla Tavola apre la pratica della riga scelta.
* **Spettatore** rende più espliciti gli ingressi della sessione e l'esito.
* **Riconoscimento** è utilizzabile autonomamente; **Laboratorio** esplicita
  proprietà e domini senza richiedere una formula nell'Explorer.
* Tooltip per mouse e tastiera, spiegazioni dei controlli disabilitati e
  aiuto contestuale rimandano agli approfondimenti senza popup ordinari.
* Guida con indice, ricerca e **Torna al lavoro**, allineata ai percorsi
  iniziali; Presentazione chiarisce la differenza fra Esc e Chiudi.
* Correzioni linguistiche e terminologia coerente in italiano e inglese americano.

## Layout e consolidamento tecnico

* Barra adattiva: pulsanti visibili e raggiungibili anche con conteggi lunghi;
  corrette la sovrapposizione dei contenitori ai controlli e la cache delle
  dimensioni dopo cambiamenti del messaggio di stato.
* Rimozione selettiva dei binding Tk anche su Python 3.10: reinstallare gli
  aiuti conserva i callback funzionali e il ridimensionamento delle viste.
* Layout Explorer/Matrice e Riconoscimento corretti senza ridurre le matrici
  o allentare il requisito di raggiungibilità a 1280×720.
* Test e fixture riallineati ai contratti UX correnti, mantenendo le verifiche
  sostanziali di dati, stato, concorrenza, export e correttezza matematica.

## Verifica e distribuzione

* Controlli mirati di layout: **185 PASS**; installazione e packaging finale:
  **9 PASS**, con verifica TLS attiva.
* ZIP Windows autonomo, wheel e sdist derivati dal commit definitivo della
  release; checksum SHA-256 nelle note GitHub. Eseguibile Windows verificato
  con il selftest previsto dal programma.
* Versione da un'unica fonte (`gioco27.__version__`), usata da GUI, CLI,
  esperimenti e metadata Python. Compatibilità degli esperimenti conservata.
* Roadmap e relativo audit pubblicati come documenti progettuali: sviluppo
  lineare e cumulativo dalla stabile corrente, senza applicare ulteriori
  proposte dell'audit in questa release.
