# Gioco delle 27 carte — note della versione 4.0.2

> **4.0.2 — release stabile di affinamento della serie 4.0.x.**
> La matematica e le funzionalità restano invariate; la release ridisegna i
> due PDF di export delle configurazioni e pulisce il repository.
> Punto di partenza: `NOTE_VERSIONE_4.0.1.md`.

## PDF dettagliato delle configurazioni

* Layout A3 orizzontale ridisegnato e misurato: normalmente due configurazioni
  per pagina, con paginazione adattiva e configurazioni mai spezzate.
* Tabella universale P₀/P₁/P₂/J₀/J₁/J₂ per ogni stadio, con la stessa
  geometria per il gioco classico e per i casi generali; gli alias del gioco
  classico compaiono solo quando la configurazione è davvero una Procedura.
* Trasposte limitate localmente alle prime 8, con il conteggio di quelle
  restanti; intestazione, legenda comune, versione e numero di pagina.
* Rimosse duplicazioni e vecchie classificazioni improprie; spazio della
  pagina usato in modo più leggibile.

## PDF matriciale

* Una configurazione per pagina A3, con i tre stadi affiancati: matrici P, J e
  risultato dello stadio.
* Riepilogo della trasformazione T: matrice finale, ordine, punti fissi,
  involutività, posizioni e settori degli Assi, mappa completa origine →
  destinazione e decomposizione in cicli, con ordine(T) = mcm delle lunghezze
  dei cicli.
* Supporto coerente a P e J generali, oltre al gioco classico.

## Interfaccia

* Nuovi nomi degli export nel menu Genera: **PDF matriciale** (prima «PDF») e
  **PDF dettagliato delle configurazioni** (prima «PDF dettagliato (stile C:
  carte+matrici)»); in inglese **Matrix PDF** e **Detailed configuration PDF**.
  Guida, tooltip e dialoghi di salvataggio usano gli stessi nomi.

## Repository

* Eliminati artefatti temporanei, build, cache e anteprime locali dello
  sviluppo; `.gitignore` aggiornato.

## Verifica e distribuzione

* Certificazione eseguita una sola volta sul contenuto definitivo, con le
  procedure del repository: analisi statica, baseline matematica, selftest,
  suite completa file per file, test dei PDF, packaging e installazione pulita.
* ZIP Windows autonomo, wheel e sdist derivati dal commit definitivo della
  release; checksum SHA-256 nelle note GitHub. Eseguibile Windows verificato
  con il selftest previsto dal programma.
* Versione da un'unica fonte (`gioco27.__version__`), usata da GUI, CLI,
  esperimenti, metadata Python e piè di pagina dei PDF. Compatibilità degli
  esperimenti conservata.
