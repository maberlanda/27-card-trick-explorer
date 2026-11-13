# Roadmap della serie 4.x

Questo documento raccoglie gli sviluppi pianificati dopo la
[4.0.3](../archive/releases/NOTE_VERSIONE_4.0.3.md) di *Gioco delle 27 carte*.

La 4.0.3 consolida la distribuzione Windows e l'interfaccia sulla base
dei PDF ridisegnati nella 4.0.2.

## Principio di evoluzione delle versioni

Lo sviluppo è **lineare e cumulativo**: ogni `4.n+1` deriva dall'ultima stabile
`4.n.x` e conserva le funzionalità precedenti, salvo cambiamenti esplicitamente
motivati. Le correzioni e la manutenzione confluiscono nella versione di
sviluppo corrente, senza backport ordinario né riapertura delle linee chiuse.
La 4.0.3 conclude il ciclo di manutenzione 4.0.x e costituisce la base della
4.1. Il cambio del numero minore segnala un nuovo nucleo funzionale
significativo. Le estensioni
dello stesso nucleo possono confluire nella linea corrente. La numerazione
delle milestone successive si decide quando il lavoro è pronto per il rilascio.

L'audit `docs/audits/AUDIT_ROADMAP_4x.md` documenta la valutazione progettuale
del 5 ottobre 2026. Le decisioni recepite sono riportate qui. Le altre
proposte restano da discutere.

La roadmap è organizzata in quattro aree:

1. **4.1 — visualizzazione strutturale e grafi**
2. **4.2 — estensioni matematiche e strumenti di analisi**
3. **4.3 — wreath product e tutor algebrico**
4. **Debiti tecnici e manutenzione**

L'ordine può essere adattato durante lo sviluppo, ma va mantenuta la distinzione fra nuove funzioni, ampliamenti matematici e manutenzione.

---

# 1. Versione 4.1 — visualizzazione strutturale e grafi

## Obiettivo generale

La 4.1 deve trasformare strutture già calcolate dal programma in **oggetti visuali esplorabili**, senza cambiare il modello matematico consolidato nella 4.0.0.

Principio guida:

> mostrare graficamente relazioni che il programma sa già calcolare.

La GUI non deve duplicare la logica matematica: i grafi devono essere alimentati dai servizi e dagli oggetti del core.

## Perimetro della 4.1.0

La 4.1.0 comprende **M0, la Vista Posizioni e la Vista Fibre**. Le due viste
verificano il modello comune su strutture diverse: Posizioni lo applica agli
archi di una permutazione su 27 posizioni, Fibre al trasporto tra fibre
raggruppate per livello e alle relazioni con somme e ricostruzione. Insieme
costituiscono il primo nucleo di visualizzazione strutturale.

La Vista Gruppo è una **milestone successiva della linea 4.1.x**, senza
numero di patch assegnato. Rimane parte della visualizzazione strutturale e
dei grafi. I criteri di uscita della 4.1.0 sono al §7.

## M0 — Infrastruttura grafica comune

- Modello condiviso per i vertici, gli archi orientati e le partizioni
  richiesti da Posizioni e Fibre. I dati matematici provengono dal core e
  dai servizi esistenti.
- Componenti condivisi per la visualizzazione, la selezione, il dettaglio,
  la navigazione da tastiera e la rappresentazione testuale equivalente.
- Palette, stile e modalità di interazione comuni alle nuove viste, con
  etichette o altri segnali oltre al colore. Il lavoro riguarda i componenti
  delle nuove viste.
- Estendibilità per la Vista Gruppo. Chiusura di sottogruppi arbitrari,
  grafi di Cayley completi, disposizione su 216 o 648 vertici, metriche di
  Cayley e confronto fra generatori rientrano nella milestone che li usa.

## 1.1 Vista Posizioni — Decomposizione ciclica grafica

Il caso iniziale è una singola permutazione $T$ sulle 27 posizioni.
Il grafo ha 27 vertici e archi orientati $i\to T(i)$.

- mostrare la decomposizione ciclica;
- rappresentare ogni ciclo come componente grafica;
- distinguere punti fissi, 2-cicli, 3-cicli e cicli più lunghi;
- mostrare ordine della trasformazione, tipo ciclico, numero e lunghezza dei cicli;
- fornire una rappresentazione testuale equivalente del grafo;
- permettere la selezione e la navigazione anche da tastiera;
- selezionando un nodo, mostrare origine, immagine e ciclo di appartenenza.

Si può inoltre collegare il grafo alle rappresentazioni esistenti della
permutazione, compresa la matrice quando disponibile.

La visualizzazione deve rispettare la convenzione:

```math
T(i)=j
```

cioè il contenuto inizialmente nella posizione $i$ termina nella posizione $j$.

### Criterio di accettazione

La decomposizione mostrata graficamente deve coincidere esattamente con quella calcolata dal core per tutte le trasformazioni testate.

## 1.2 Vista Posizioni — Orbite di una trasformazione

Per la 4.1.0 la vista mostra le orbite della singola trasformazione $T$.
Le orbite determinate da più generatori o da un sottogruppo selezionato
rientrano nella milestone della Vista Gruppo (§1.6).

Funzioni desiderate:

- calcolo automatico delle orbite;
- visualizzazione a componenti connesse;
- evidenza delle lunghezze;
- selezione di un nodo con dettaglio della traiettoria;
- distinzione fra punti fissi, orbite corte e orbite lunghe;
- export SVG.

La vista deve distinguere con chiarezza orbite di **posizioni** e traiettorie di **carte**.

## Vista Gruppo — milestone successiva della linea 4.1.x

La vista può crescere dal Cayley di $H$ (216 vertici) al gruppo
$\Gamma$ (648 vertici), con generatori selezionabili quando opportuno,
archi etichettati, classi laterali, prefissi, relazioni nominate ed eventuali
grafi di Schreier. La disposizione, il budget di prestazione e la
navigazione accessibile su queste dimensioni si verificano in questa
milestone, insieme a cammini, distanze e diametro.

### 1.3 Grafo di Cayley di $H$

Aggiungere un vero grafo di Cayley per

```math
H\cong S_3^3,\qquad |H|=216.
```

Funzioni:

- scelta dell'insieme di generatori;
- visualizzazione dei 216 vertici;
- archi associati ai generatori;
- evidenza dell'identità;
- ricerca di un elemento;
- percorso dall'identità a un elemento;
- distanza rispetto ai generatori scelti;
- dettaglio della trasformazione selezionata;
- eventuali filtri per sottogruppi o proprietà.

La Tavola 216 e il grafo di Cayley restano strumenti distinti:

- la Tavola è enumerativa;
- il grafo è relazionale.

### 1.4 Le tre classi laterali di $H$ in $\Gamma$

Visualizzare:

```math
\Gamma
=
H
\sqcup
H\circ\mathrm{MSC}
\sqcup
H\circ\mathrm{MSC}^2,
```

con

```math
|\Gamma|=648,\qquad [\Gamma:H]=3.
```

Le classi laterali possono essere rappresentate come partizioni
riconoscibili tramite regioni, livelli, etichette e colore.
I passaggi indotti da $\mathrm{MSC}$ possono collegare le tre parti.

Per un elemento selezionato mostrare:

- appartenenza alla classe laterale;
- forma normale;
- fattore appartenente a $H$;
- potenza di $\mathrm{MSC}$;
- classificazione completa/intermedia.

Questa vista deve rendere evidente la differenza fra $H$ e $\Gamma$.

### 1.5 Grafo delle trasformazioni complete e intermedie

Costruire un grafo delle trasformazioni cumulative ottenute durante una procedura.

Scopi:

- mostrare i prefissi di procedura;
- distinguere trasformazioni complete e intermedie;
- visualizzare il passaggio tra le tre componenti di $\Gamma$;
- mostrare l'effetto dell'aggiunta di uno stadio;
- preparare una futura rappresentazione esplicita di $\mathcal S_F$.

### 1.6 Grafi generati da insiemi di generatori

Consentire il confronto fra più insiemi di generatori.

Per ciascuno:

- costruire il grafo relativo;
- mostrare gli elementi raggiungibili;
- calcolare componenti connesse;
- mostrare distanze e diametro, se significativi;
- confrontare il comportamento di generatori diversi.

I grafi di Schreier possono mostrare l'azione dei generatori sulle
posizioni, quando la distinzione dal grafo di Cayley è utile alla lettura.
La funzione ha carattere esplorativo e usa le definizioni del gioco.

## 1.7 Vista Fibre — Struttura digitale

Aggiungere una vista dedicata alle fibre

```math
F_{i,t}=\pi_i^{-1}(\{t\}).
```

Nel caso classico:

- tre coordinate ternarie;
- tre famiglie;
- nove fibre;
- nove elementi per fibra.

Mostrare:

- coordinata fissata;
- coordinate libere;
- elementi della fibra;
- somma della fibra;
- immagine sotto $T$;
- fibra di arrivo.

Raggruppare le fibre per livello e rappresentare il trasporto con archi
dalla fibra di origine a quella di arrivo. Per le trasformazioni separabili
vale la relazione:

```math
T(F_{i,t})=F_{i,M_i(t)}.
```

## 1.8 Vista Fibre — Trasporto e ricostruzione

Integrare la vista delle fibre con:

```math
\Sigma_{i,t}(T)
=
C_i+b^{m-1+i}M_i(t)
```

e

```math
M_i(t)
=
\frac{\Sigma_{i,t}(T)-C_i}{b^{m-1+i}}.
```

Nel caso classico:

```math
C_0=108,\qquad C_1=90,\qquad C_2=36.
```

Mostrare per ogni asse:

- fibra iniziale;
- somma osservata;
- valore ricostruito;
- fattore locale risultante.

Collegare esplicitamente questa vista al teorema di ricostruzione del libro.
Mostrare $\Sigma_{i,t}$ e, per le somme inverse, $\Lambda_{i,u}$
nei casi in cui sono definite, usando i risultati dei servizi esistenti.

## 1.9 Confronto visuale facoltativo $T$ / $T^{-1}$

Quando è utile al caso mostrato, affiancare la trasformazione diretta e
l'inversa:

- grafi affiancati;
- archi invertiti;
- confronto delle decomposizioni cicliche;
- confronto delle fibre;
- evidenza delle preimmagini.

Per la Vista Fibre, la quantità inversa già definita nei casi applicabili è

```math
\Lambda_{i,u}
=
C_i+b^{m-1+i}M_i^{-1}(u).
```

## 1.10 Orbite di carte e posizioni

Distinguere sempre:

- posizione fisica;
- etichetta della carta;
- traiettoria della carta;
- orbita della posizione.

Convenzioni:

- posizioni interne: 0–26;
- carte mostrate all'utente: 1–27 quando appropriato.

Una vista grafica può mostrare la successione delle posizioni attraversate da una carta e il ritorno eventuale alla posizione iniziale.

## 1.11 Relazioni fra tabelloni

Nella milestone della Vista Gruppo, valutare relazioni nominate tra
tabelloni o rappresentazioni ternarie, come inversa, composizione o ritorno:

- corrispondenza fra righe, colonne e fibre;
- trasformazioni che collegano due tabelloni;
- permutazioni indotte;
- collegamento con i fattori locali.

Obiettivo didattico:

```math
\text{gesti fisici}
\to
\text{tabellone}
\to
\text{fibre e somme}
\to
\text{fattori locali}.
```

## 1.12 Requisiti comuni della 4.1

Le nuove visualizzazioni devono:

- usare il core esistente come fonte dei risultati;
- evitare logica matematica duplicata nella GUI;
- avere un equivalente testuale e usare il colore insieme ad altri segnali informativi;
- essere navigabili e utilizzabili da tastiera;
- avere testi completi in italiano e inglese;
- funzionare alle geometrie minime già supportate;
- avere export SVG quando sensato;
- evitare dipendenze pesanti se possibile;
- degradare chiaramente se manca una dipendenza opzionale;
- avere test distinti per modello matematico, modello grafico e GUI.

Per i nuovi lavori grafici asincroni riusare il passaggio degli aggiornamenti
al thread Tk descritto nel §4.1.

---

# 2. Versione 4.2 — estensioni matematiche e strumenti di analisi

## 2.1 Rappresentazione esplicita di $\mathcal S_F$

Introdurre un oggetto o servizio dedicato alla famiglia delle trasformazioni cumulative ottenute dopo uno o più stadi di una procedura ammessa.

Vincolo fondamentale:

```math
\mathcal S_F
```

non va presentata inizialmente come gruppo.

Il gruppo generato è invece:

```math
\Gamma_{3,3}
=
\langle\mathcal S_F\rangle.
```

Funzioni possibili:

- enumerazione dei prefissi;
- classificazione per lunghezza;
- distinzione finale/intermedia;
- appartenenza a $H$ o alle altre classi di $\Gamma$;
- generazione del sottogruppo;
- statistiche;
- collegamento con il grafo delle transizioni.

## 2.2 Forma canonica del rovesciamento globale $J$

Valutare una rappresentazione strutturale:

```math
J=R\otimes R\otimes R.
```

Vincoli:

- $J\in H$;
- nessun ampliamento del gruppo;
- nessuna modifica semantica per l'utente;
- compatibilità con dati persistiti e test esistenti.

Va implementata solo se migliora chiarezza o manutenzione.

## 2.3 Quantità inverse $\Lambda_{i,u}$

La Vista Fibre della 4.1.0 espone le somme inverse nei casi già gestiti
dai servizi. Per eventuali estensioni analitiche, valutare altri impieghi di

```math
\Lambda_{i,u}
=
C_i+b^{m-1+i}M_i^{-1}(u).
```

Possibili usi:

- ricostruzione inversa;
- confronto $T$ / $T^{-1}$;
- fibre di origine;
- diagnostica;
- Laboratorio.

## 2.4 Laboratorio delle fibre

La visualizzazione di fibre, somme e ricostruzione rientra nella 4.1.0.
Per un eventuale approfondimento analitico nel Laboratorio, valutare:

- mostrare le firme strutturate;
- distinguere singola $\Sigma_{i,t}$ e famiglia delle firme;
- confrontare trasformazioni;
- verificare separabilità e appartenenza a $H$.

Va preservato il fatto che la singola $\Sigma_{i,t}$ non è, da sola, un invariante globale.

## 2.5 Forma normale in $\Gamma$

Il core calcola la forma normale e l'Explorer la espone già. Il Laboratorio
ne verifica l'unicità nel dominio $\Gamma$. La struttura è:

```math
\Gamma_{3,3}
=
S_3^3\rtimes\langle\tau\rangle,
\qquad
\langle\tau\rangle\cong C_3.
```

Eventuali ampliamenti riguardano i collegamenti tra la forma normale,
la classe laterale e gli strumenti di analisi delle Procedure.

## 2.6 Procedure equivalenti

Approfondire la distinzione fra:

- 1 728 Procedure fisiche;
- 216 trasformazioni complete distinte in $H$.

Possibili strumenti:

- classi di equivalenza delle Procedure;
- molteplicità;
- ricerca inversa trasformazione → Procedure;
- filtri;
- rappresentazione grafica delle equivalenze.

## 2.7 Dominio Kronecker esteso su 27 carte

Estendere l'analisi oltre le sole Procedure ammesse dal gioco classico, restando nel dominio delle trasformazioni su 27 posizioni che ammettono una decomposizione strutturale secondo Kronecker.

Obiettivo concettuale:

- distinguere nettamente **Procedura del gioco**, **realizzabilità fisica** e **decomponibilità strutturale secondo Kronecker**;
- trattare come oggetti di studio anche trasformazioni separabili che non corrispondono a una Procedura lecita del gioco dei 27;
- mantenere invariata la semantica del gioco classico nelle aree che lo rappresentano.

Prima dell'implementazione va formalizzato il modello dei rovesciamenti locali. In particolare, per i tre livelli deve essere possibile descrivere configurazioni con:

- nessun rovesciamento;
- un solo rovesciamento;
- due rovesciamenti;
- tre rovesciamenti;

senza fissare a priori nella GUI l'ordine algebrico dei fattori finché non sia verificata la convenzione corretta nel core.

Per ogni trasformazione appartenente a questo dominio mostrare, quando definito:

- fattori locali;
- eventuali rovesciamenti locali;
- trasformazione globale $T$;
- appartenenza a $H$, $\Gamma_{3,3}$ o ad altri insiemi già definiti dal progetto;
- decomponibilità secondo Kronecker;
- realizzabilità mediante una Procedura del gioco classico;
- Procedure equivalenti, quando esistono;
- motivo strutturale della non realizzabilità nel gioco, quando non esistono.

L'interfaccia dovrebbe collocare questa capacità nell'area Explorer/Laboratorio, evitando di sovraccaricare il Simulatore del gioco classico.

Questa estensione deve precedere una generalizzazione a $b^m$: prima si amplia e si chiarisce il dominio strutturale del caso $3^3=27$, poi si valuta l'estensione del numero di coordinate e della base.

## 2.8 Generalizzazione a $b^m$

Possibile estensione di grande portata.

Dal caso classico

```math
3^3=27
```

a configurazioni

```math
b^m.
```

Prima dell'implementazione devono essere definiti con precisione:

- dominio;
- mescolamento;
- fattori locali;
- gruppo;
- fibre;
- somme;
- ricostruzione;
- interfaccia;
- limiti computazionali.

Può richiedere una release maggiore o un ramo sperimentale.

## 2.9 Caso rettangolare

Valutare separatamente il supporto operativo al caso rettangolare del libro.

Preservare la distinzione:

- permutazione locale $P$;
- trasformazione globale $T_P$.

Prima dell'implementazione definire i casi supportati e quali risultati restano validi.

---

# 3. Versione 4.3 — wreath product e tutor algebrico

## 3.1 Obiettivo generale

La 4.3 deve rendere esplorabile la struttura del wreath product che contiene le trasformazioni del progetto, senza confondere il livello astratto con le permutazioni concrete delle 27 posizioni.

Il riferimento strutturale resta:

```math
G
\xrightarrow{\text{realizzazione}}
H
\subset
\Gamma_{3,3}
\subset
S_3\wr S_3
\subset
S_{27}.
```

Il passaggio a questa area deve avvenire soltanto dopo che il dominio Kronecker esteso su 27 carte è stato formalizzato e reso stabile.

## 3.2 Explorer del wreath product

Aggiungere una rappresentazione esplicita degli elementi del wreath product che permetta di leggere nello stesso oggetto:

- componente esterna $\sigma\in S_3$ che permuta le tre coordinate ternarie nell'azione prodotto;
- fattori locali;
- azione sulle coordinate;
- permutazione concreta sulle 27 posizioni;
- composizione;
- inversa;
- identità;
- appartenenza a $H$ e $\Gamma_{3,3}$;
- eventuale appartenenza al dominio Kronecker esteso definito nella 4.2.

L'Explorer deve mantenere sincronizzati almeno quattro livelli di lettura:

```math
\text{oggetto concreto / gesto}
\longleftrightarrow
\text{permutazione di 27 elementi}
\longleftrightarrow
\text{fattori locali}
\longleftrightarrow
\text{elemento del wreath product}.
```

Le conversioni fra questi livelli devono essere fornite dal core o da servizi dedicati, non ricostruite indipendentemente dalla GUI.

## 3.3 Tutor algebrico contestuale

Affiancare all'Explorer un tutor algebrico capace di spiegare l'oggetto corrente e non soltanto formule generiche.

Il tutor deve poter guidare, a richiesta, su domande come:

- qual è il fattore esterno;
- quali coordinate ternarie vengono permutate;
- come si leggono i fattori locali;
- perché un elemento appartiene o non appartiene a $H$;
- perché un elemento appartiene o non appartiene a $\Gamma_{3,3}$;
- come si calcola una composizione;
- come si calcola l'inversa;
- come si passa dalla notazione astratta alla permutazione sulle 27 posizioni;
- come si collega l'oggetto al dominio Kronecker e, quando applicabile, alle Procedure del gioco.

Il tutor non deve sostituire il libro né presentare spiegazioni monolitiche. Deve procedere per livelli di approfondimento, a partire dall'oggetto selezionato.

## 3.4 Modalità didattica

Prevedere esercizi contestuali generati dagli oggetti già calcolati dal programma, per esempio:

- riconoscere il fattore esterno;
- prevedere come vengono riordinate le coordinate ternarie;
- stabilire l'appartenenza a un sottogruppo;
- calcolare un'inversa;
- prevedere una composizione;
- riconoscere la rappresentazione concreta corrispondente.

La correzione deve essere motivata e mostrare il passaggio fra i diversi livelli di rappresentazione, non limitarsi a un esito corretto/errato.

## 3.5 Requisiti comuni della 4.3

- nessuna duplicazione della logica matematica nella GUI;
- notazione coerente con il core e con il libro;
- distinzione esplicita fra oggetto astratto e permutazione concreta;
- navigazione da tastiera;
- italiano e inglese;
- test separati per algebra, conversioni, tutor e GUI;
- esempi generati da oggetti realmente calcolati dal programma;
- nessuna introduzione di risultati matematici non formalizzati nel core.

---

# 4. Debiti tecnici e manutenzione

## 4.1 Threading Tk e `ui_call`

I lavori avviati con `run_in_thread` accodano gli aggiornamenti. Il thread
Tk li consegna tramite `after()` e annulla il controllo della coda quando il
widget viene distrutto. I nuovi lavori grafici possono usare lo stesso schema.

## 4.2 `atomic_write` e `fsync`

Valutare:

- flush esplicito;
- `fsync`;
- eventuale sincronizzazione della directory dopo rename atomico.

Obiettivo: aumentare la robustezza del salvataggio in caso di crash o perdita improvvisa di alimentazione.

## 4.3 Conferma alla chiusura con sessione modificata

Completata nella 4.0.1. Alla chiusura di una sessione con modifiche non
salvate il programma offre **Salva**, **Non salvare** e **Annulla**.

## 4.4 Alias e nomi legacy

Restano per compatibilità:

- `appartiene_a_G`;
- eventuali identificatori storici;
- `classe_estesa` nei dati persistiti.

Politica:

- non rompere file esistenti;
- mantenere alias documentati;
- usare i nomi correnti nelle nuove API;
- valutare deprecazioni solo in una release futura.

## 4.5 Warning setuptools su `gioco27.assets`

La build 4.0.0 segnala che `gioco27.assets` è riconosciuta come directory importabile ma non è esplicitamente presente nella configurazione dei package.

Gli asset sono comunque inclusi correttamente:

- `DejaVuSans.ttf`;
- `DejaVuSans-Bold.ttf`;
- `LICENSE-DejaVu.txt`.

Il warning non è un blocker, ma va eliminato in una revisione del packaging.

Qualunque soluzione deve mantenere verdi i test della wheel e della sdist.

## 4.6 Verifica automatica del bundle Windows

Il workflow Windows esegue i selftest sull'eseguibile e verifica l'avvio
della GUI e la produzione dei due PDF delle configurazioni. Verifica anche
le licenze del programma e del font e l'assenza dei PDF fonte.

Estendere la copertura a export XLSX, multiprocessing e caricamento e
salvataggio delle sessioni.

## 4.7 Script di build e pulizia

Valutare script dedicati per:

- build pulita;
- pulizia `build/` e `dist/`;
- PyInstaller;
- ZIP Windows;
- SHA-256;
- riepilogo artefatti.

## 4.8 Automazione della release

Possibile workflow futuro a partire da un tag stabile:

1. test;
2. wheel;
3. sdist;
4. PyInstaller Windows;
5. selftest;
6. ZIP;
7. SHA-256;
8. riepilogo artefatti;
9. caricamento degli asset nella GitHub Release.

La pubblicazione definitiva deve comunque restare sotto controllo dell'autore.

---

# 5. Principi da preservare

## 5.1 Convenzione delle permutazioni

```math
T(i)=j
```

significa che il contenuto inizialmente nella posizione $i$ termina nella posizione $j$.

Per la matrice:

```math
M[T[i],i]=1.
```

Per la composizione:

```math
A\circ B
```

significa prima $B$, poi $A$.

## 5.2 Gerarchia strutturale

Preservare:

```math
G
\xrightarrow{\text{realizzazione}}
H
\subset
\Gamma_{3,3}
\subset
S_3\wr S_3
\subset
S_{27}.
```

Con:

```math
G\cong S_3^3,
\qquad
H\cong G,
\qquad
|H|=216,
```

e:

```math
\Gamma_{3,3}
=
\langle H,\mathrm{MSC}\rangle
=
\langle\mathcal S_F\rangle,
\qquad
|\Gamma_{3,3}|=648.
```

## 5.3 Gaia

Il nome narrativo **Gaia** resta associato alle trasformazioni complete, cioè a $G$ / $H$ secondo il livello astratto o concreto.

Non associare Gaia a $\Gamma$.

## 5.4 Rovesciamento globale

```math
J\in H.
```

Il rovesciamento globale non amplia il gruppo.

## 5.5 Procedure e trasformazioni

Preservare la distinzione:

- 1 728 Procedure fisiche;
- 216 trasformazioni complete distinte in $H$.

Non introdurre una “Tavola 1 728” di trasformazioni distinte.

## 5.6 Compatibilità dei dati

Le versioni successive devono, per quanto possibile:

- leggere esperimenti 3.1.3;
- leggere esperimenti 4.0.0;
- conservare le chiavi persistite necessarie;
- distinguere differenza di versione da differenza di contenuto scientifico.

---

# 6. Ordine di priorità suggerito

## 4.1

1. **M0:** infrastruttura comune per Posizioni e Fibre.
2. **Vista Posizioni:** grafo di una singola trasformazione, cicli e punti fissi.
3. **Vista Fibre:** livelli, trasporto, somme e ricostruzione. Con questa
   vista si completa il perimetro della **4.1.0**.
4. **Vista Gruppo:** milestone successiva della linea 4.1.x, da sviluppare
   progressivamente a partire dal Cayley di $H$.

## 4.2

1. $\mathcal S_F$ esplicita;
2. eventuali approfondimenti analitici nel Laboratorio delle fibre (§2.4);
3. eventuali usi ulteriori di $\Lambda_{i,u}$ (§2.3);
4. forma canonica di $J$;
5. equivalenze fra Procedure;
6. dominio Kronecker esteso su 27 carte;
7. valutazione di $b^m$;
8. valutazione del caso rettangolare.

## 4.3

1. rappresentazione esplicita degli elementi del wreath product;
2. sincronizzazione fra fattori locali, azione sulle coordinate e permutazione sulle 27 posizioni;
3. appartenenza e confronto con $H$, $\Gamma_{3,3}$ e dominio Kronecker esteso;
4. tutor algebrico contestuale;
5. modalità didattica con esercizi e correzione motivata.

## Manutenzione

Priorità alta:

- warning setuptools;
- automazione build/release.

Priorità media:

- `fsync`;
- test più completi del bundle Windows.

---

# 7. Criteri di rilascio

## 4.1.0

La 4.1.0 può essere candidata al rilascio quando **M0, Vista Posizioni e
Vista Fibre** soddisfano i criteri seguenti.

### M0

- Le due viste usano lo stesso modello grafico per rappresentare vertici,
  archi e partizioni. I test del modello verificano la corrispondenza fra
  grafi, rappresentazioni testuali e dati di origine.
- La GUI legge i risultati dal core o dai servizi. Cicli, punti fissi,
  somme e ricostruzioni sono calcolati dal livello matematico esistente.
- In entrambe le viste si può raggiungere e selezionare un elemento da
  tastiera, leggerne il dettaglio e consultare l'equivalente testuale.
  Etichette o altri segnali rendono riconoscibili le distinzioni affidate
  anche al colore.

### Vista Posizioni

- Per i casi verificati, i 27 vertici e gli archi $i\to T(i)$ rispettano
  la convenzione $T(i)=j$. Cicli e punti fissi coincidono con il core.
- Selezionando un nodo si ottengono origine, immagine e ciclo di
  appartenenza corretti. Se è disponibile il confronto con $T^{-1}$,
  gli archi dell'inversa risultano invertiti rispetto a quelli di $T$.

### Vista Fibre

- Nei casi verificati, fibre e partizioni per livello, trasporto, somme e
  ricostruzione coincidono con i risultati dei servizi esistenti.
- Le etichette $\Sigma$ e $\Lambda$ compaiono soltanto nei casi in cui le
  rispettive quantità sono definite. La GUI presenta i dati e le relazioni
  forniti dal livello matematico.

### Qualità comune

- IT/EN completi e Guida e documentazione allineate alle viste disponibili.
- Test pertinenti superati, distinti per dati matematici, modello grafico e
  GUI. Verifiche di tastiera e accessibilità alle geometrie minime dichiarate.
- Export SVG verificato dove previsto. Controlli CI e di rilascio della
  linea corrente soddisfatti.

La verifica della Vista Gruppo appartiene alla relativa milestone della
linea 4.1.x.

## 4.2.0

Apertura quando si introduce almeno una nuova capacità matematica o analitica strutturale, non soltanto una nuova rappresentazione grafica.

## 4.3.0

Apertura quando esiste una rappresentazione stabile e verificata di almeno un nucleo del wreath product, con conversione esplicita fra livello astratto e permutazione sulle 27 posizioni.

Il tutor algebrico può crescere progressivamente, ma la 4.3.0 non deve essere aperta sulla sola base di testi didattici: deve poggiare su un modello algebrico e su servizi del core già verificati.

---

# 8. Fuori ambito immediato

Non sono obiettivi automatici della serie 4.x:

- riscrittura completa della GUI;
- cambio di toolkit grafico;
- generalizzazione indiscriminata oltre il dominio matematico definito;
- rottura volontaria della compatibilità con gli esperimenti esistenti;
- replica del libro dentro il programma.

Qualunque sviluppo di questo tipo richiede una decisione progettuale separata.

---

# 9. Stato iniziale della roadmap

Alla pubblicazione della 4.0.0:

- la base matematica è consolidata;
- $H$ e $\Gamma$ sono distinti correttamente;
- la Fase P ha riallineato programma e libro;
- la suite finale è verde;
- wheel, sdist e bundle Windows sono stati costruiti;
- la 4.0.0 è pubblicata come release stabile;
- i grafi veri e propri sono intenzionalmente rinviati alla serie successiva.

La 4.0.0 ha avviato la roadmap. La base della 4.1 integra il consolidamento
dell'interfaccia della 4.0.1, i PDF ridisegnati della 4.0.2 e le correzioni di
distribuzione, layout e aggiornamento dell'interfaccia della 4.0.3.
