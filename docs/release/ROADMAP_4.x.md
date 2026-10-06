# Roadmap della serie 4.x

Questo documento raccoglie gli sviluppi pianificati **successivi alla release stabile 4.0.1** di *Gioco delle 27 carte*.

La 4.0.1 consolida l'interfaccia della 4.0.0 e costituisce la base stabile corrente. Le nuove funzionalità elencate qui non fanno parte della 4.0.1.

## Principio di evoluzione delle versioni

Lo sviluppo è **lineare e cumulativo**: ogni `4.n+1` deriva dall'ultima stabile
`4.n.x` e conserva le funzionalità precedenti, salvo cambiamenti esplicitamente
motivati. Non è previsto un ramo parallelo ordinario di manutenzione.
Una serie `4.n.x` chiusa non viene riaperta: le nuove correzioni confluiscono
nella versione corrente. Il cambio del numero minore segnala un nuovo nucleo
funzionale significativo; la prossima serie 4.1 parte quindi dalla 4.0.1.

L'audit `docs/audits/AUDIT_ROADMAP_4x.md` documenta la valutazione progettuale
del 5 ottobre 2026. Le sue ulteriori proposte restano da discutere e non sono
applicate automaticamente dalla pubblicazione della 4.0.1.

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

## 1.1 Decomposizione ciclica grafica

Per ogni permutazione \(T\):

- mostrare la decomposizione ciclica;
- rappresentare ogni ciclo come componente grafica;
- distinguere punti fissi, 2-cicli, 3-cicli e cicli più lunghi;
- mostrare ordine della trasformazione, tipo ciclico, numero e lunghezza dei cicli;
- permettere il passaggio fra forma ciclica, permutazione 0–26, eventuale matrice e grafo;
- selezionando un nodo, mostrare origine, immagine e ciclo di appartenenza.

La visualizzazione deve rispettare la convenzione:

\[
T(i)=j
\]

cioè il contenuto inizialmente nella posizione \(i\) termina nella posizione \(j\).

### Criterio di accettazione

La decomposizione mostrata graficamente deve coincidere esattamente con quella calcolata dal core per tutte le trasformazioni testate.

## 1.2 Grafi delle orbite

Aggiungere una rappresentazione grafica delle orbite dell'azione di:

- una trasformazione;
- un insieme di generatori;
- un sottogruppo selezionato.

Funzioni desiderate:

- calcolo automatico delle orbite;
- visualizzazione a componenti connesse;
- evidenza delle lunghezze;
- selezione di un nodo con dettaglio della traiettoria;
- distinzione fra punti fissi, orbite corte e orbite lunghe;
- export SVG.

La vista deve distinguere con chiarezza orbite di **posizioni** e traiettorie di **carte**.

## 1.3 Grafo di Cayley di \(H\)

Aggiungere un vero grafo di Cayley per

\[
H\cong S_3^3,\qquad |H|=216.
\]

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

## 1.4 Le tre classi laterali di \(H\) in \(\Gamma\)

Visualizzare:

\[
\Gamma
=
H
\sqcup
H\circ\MSC
\sqcup
H\circ\MSC^2,
\]

con

\[
|\Gamma|=648,\qquad [\Gamma:H]=3.
\]

Possibili rappresentazioni:

- tre regioni;
- tre livelli;
- tre componenti con passaggi indotti da \(\MSC\).

Per un elemento selezionato mostrare:

- appartenenza alla classe laterale;
- forma normale;
- fattore appartenente a \(H\);
- potenza di \(\MSC\);
- classificazione completa/intermedia.

Questa vista deve rendere evidente la differenza fra \(H\) e \(\Gamma\).

## 1.5 Grafo delle trasformazioni complete e intermedie

Costruire un grafo delle trasformazioni cumulative ottenute durante una procedura.

Scopi:

- mostrare i prefissi di procedura;
- distinguere trasformazioni complete e intermedie;
- visualizzare il passaggio tra le tre componenti di \(\Gamma\);
- mostrare l'effetto dell'aggiunta di uno stadio;
- preparare una futura rappresentazione esplicita di \(\mathcal S_F\).

## 1.6 Grafi generati da insiemi di generatori

Consentire il confronto fra più insiemi di generatori.

Per ciascuno:

- costruire il grafo relativo;
- mostrare gli elementi raggiungibili;
- calcolare componenti connesse;
- mostrare distanze e diametro, se significativi;
- confrontare il comportamento di generatori diversi.

Questa funzione è esplorativa: non deve introdurre nuove definizioni matematiche del gioco.

## 1.7 Fibre digitali

Aggiungere una vista dedicata alle fibre

\[
F_{i,t}=\pi_i^{-1}(\{t\}).
\]

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
- immagine sotto \(T\);
- fibra di arrivo.

Relazione fondamentale:

\[
T(F_{i,t})=F_{i,M_i(t)}.
\]

## 1.8 Trasporto delle fibre e ricostruzione

Integrare la vista delle fibre con:

\[
\Sigma_{i,t}(T)
=
C_i+b^{m-1+i}M_i(t)
\]

e

\[
M_i(t)
=
\frac{\Sigma_{i,t}(T)-C_i}{b^{m-1+i}}.
\]

Nel caso classico:

\[
C_0=108,\qquad C_1=90,\qquad C_2=36.
\]

Mostrare per ogni asse:

- fibra iniziale;
- somma osservata;
- valore ricostruito;
- fattore locale risultante.

Collegare esplicitamente questa vista al teorema di ricostruzione del libro.

## 1.9 Confronto visuale \(T\) / \(T^{-1}\)

Aggiungere una modalità di confronto fra trasformazione diretta e inversa:

- grafi affiancati;
- archi invertiti;
- confronto delle decomposizioni cicliche;
- confronto delle fibre;
- evidenza delle preimmagini.

Preparare l'eventuale uso di

\[
\Lambda_{i,u}
=
C_i+b^{m-1+i}M_i^{-1}(u).
\]

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

Aggiungere strumenti per confrontare più tabelloni o rappresentazioni ternarie:

- corrispondenza fra righe, colonne e fibre;
- trasformazioni che collegano due tabelloni;
- tabelloni equivalenti;
- permutazioni indotte;
- collegamento con i fattori locali.

Obiettivo didattico:

\[
\text{gesti fisici}
\to
\text{tabellone}
\to
\text{fibre e somme}
\to
\text{fattori locali}.
\]

## 1.12 Requisiti comuni della 4.1

Le nuove visualizzazioni devono:

- usare il core esistente come fonte dei risultati;
- evitare logica matematica duplicata nella GUI;
- essere navigabili da tastiera;
- rispettare italiano e inglese;
- funzionare alle geometrie minime già supportate;
- avere export SVG quando sensato;
- evitare dipendenze pesanti se possibile;
- degradare chiaramente se manca una dipendenza opzionale;
- avere test distinti per modello matematico, modello grafico e GUI.

---

# 2. Versione 4.2 — estensioni matematiche e strumenti di analisi

## 2.1 Rappresentazione esplicita di \(\mathcal S_F\)

Introdurre un oggetto o servizio dedicato alla famiglia delle trasformazioni cumulative ottenute dopo uno o più stadi di una procedura ammessa.

Vincolo fondamentale:

\[
\mathcal S_F
\]

non va presentata inizialmente come gruppo.

Il gruppo generato è invece:

\[
\Gamma_{3,3}
=
\langle\mathcal S_F\rangle.
\]

Funzioni possibili:

- enumerazione dei prefissi;
- classificazione per lunghezza;
- distinzione finale/intermedia;
- appartenenza a \(H\) o alle altre classi di \(\Gamma\);
- generazione del sottogruppo;
- statistiche;
- collegamento con il grafo delle transizioni.

## 2.2 Forma canonica del rovesciamento globale \(J\)

Valutare una rappresentazione strutturale:

\[
J=R\otimes R\otimes R.
\]

Vincoli:

- \(J\in H\);
- nessun ampliamento del gruppo;
- nessuna modifica semantica per l'utente;
- compatibilità con dati persistiti e test esistenti.

Va implementata solo se migliora chiarezza o manutenzione.

## 2.3 Quantità inverse \(\Lambda_{i,u}\)

Aggiungere, se utile:

\[
\Lambda_{i,u}
=
C_i+b^{m-1+i}M_i^{-1}(u).
\]

Possibili usi:

- ricostruzione inversa;
- confronto \(T\)/\(T^{-1}\);
- fibre di origine;
- diagnostica;
- Laboratorio.

## 2.4 Laboratorio delle fibre

Estendere il Laboratorio per:

- elencare le fibre;
- calcolare le somme;
- mostrare le firme strutturate;
- distinguere singola \(\Sigma_{i,t}\) e famiglia delle firme;
- ricostruire i fattori;
- confrontare trasformazioni;
- verificare separabilità e appartenenza a \(H\).

Va preservato il fatto che la singola \(\Sigma_{i,t}\) non è, da sola, un invariante globale.

## 2.5 Forma normale in \(\Gamma\)

Rendere esplorabile:

\[
\Gamma_{3,3}
=
S_3^3\rtimes\langle\tau\rangle,
\qquad
\langle\tau\rangle\cong C_3.
\]

Funzioni:

- decomposizione automatica;
- fattore in \(H\);
- esponente di \(\tau\);
- classe laterale;
- confronto fra decomposizioni equivalenti.

## 2.6 Procedure equivalenti

Approfondire la distinzione fra:

- 1 728 Procedure fisiche;
- 216 trasformazioni complete distinte in \(H\).

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
- trasformazione globale \(T\);
- appartenenza a \(H\), \(\Gamma_{3,3}\) o ad altri insiemi già definiti dal progetto;
- decomponibilità secondo Kronecker;
- realizzabilità mediante una Procedura del gioco classico;
- Procedure equivalenti, quando esistono;
- motivo strutturale della non realizzabilità nel gioco, quando non esistono.

L'interfaccia dovrebbe collocare questa capacità nell'area Explorer/Laboratorio, evitando di sovraccaricare il Simulatore del gioco classico.

Questa estensione deve precedere una generalizzazione a \(b^m\): prima si amplia e si chiarisce il dominio strutturale del caso \(3^3=27\), poi si valuta l'estensione del numero di coordinate e della base.

## 2.8 Generalizzazione a \(b^m\)

Possibile estensione di grande portata.

Dal caso classico

\[
3^3=27
\]

a configurazioni

\[
b^m.
\]

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

- permutazione locale \(P\);
- trasformazione globale \(T_P\).

Prima dell'implementazione definire i casi supportati e quali risultati restano validi.

---

# 3. Versione 4.3 — wreath product e tutor algebrico

## 3.1 Obiettivo generale

La 4.3 deve rendere esplorabile la struttura del wreath product che contiene le trasformazioni del progetto, senza confondere il livello astratto con le permutazioni concrete delle 27 posizioni.

Il riferimento strutturale resta:

\[
G
\xrightarrow{\text{realizzazione}}
H
\subset
\Gamma_{3,3}
\subset
S_3\wr S_3
\subset
S_{27}.
\]

Il passaggio a questa area deve avvenire soltanto dopo che il dominio Kronecker esteso su 27 carte è stato formalizzato e reso stabile.

## 3.2 Explorer del wreath product

Aggiungere una rappresentazione esplicita degli elementi del wreath product che permetta di leggere nello stesso oggetto:

- componente esterna che permuta i blocchi;
- fattori locali;
- azione sui blocchi;
- permutazione concreta sulle 27 posizioni;
- composizione;
- inversa;
- identità;
- appartenenza a \(H\) e \(\Gamma_{3,3}\);
- eventuale appartenenza al dominio Kronecker esteso definito nella 4.2.

L'Explorer deve mantenere sincronizzati almeno quattro livelli di lettura:

\[
\text{oggetto concreto / gesto}
\longleftrightarrow
\text{permutazione di 27 elementi}
\longleftrightarrow
\text{fattori locali}
\longleftrightarrow
\text{elemento del wreath product}.
\]

Le conversioni fra questi livelli devono essere fornite dal core o da servizi dedicati, non ricostruite indipendentemente dalla GUI.

## 3.3 Tutor algebrico contestuale

Affiancare all'Explorer un tutor algebrico capace di spiegare l'oggetto corrente e non soltanto formule generiche.

Il tutor deve poter guidare, a richiesta, su domande come:

- qual è il fattore esterno;
- quali blocchi vengono permutati;
- come si leggono i fattori locali;
- perché un elemento appartiene o non appartiene a \(H\);
- perché un elemento appartiene o non appartiene a \(\Gamma_{3,3}\);
- come si calcola una composizione;
- come si calcola l'inversa;
- come si passa dalla notazione astratta alla permutazione sulle 27 posizioni;
- come si collega l'oggetto al dominio Kronecker e, quando applicabile, alle Procedure del gioco.

Il tutor non deve sostituire il libro né presentare spiegazioni monolitiche. Deve procedere per livelli di approfondimento, a partire dall'oggetto selezionato.

## 3.4 Modalità didattica

Prevedere esercizi contestuali generati dagli oggetti già calcolati dal programma, per esempio:

- riconoscere il fattore esterno;
- prevedere l'immagine di un blocco;
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

Con Tcl/Tk 8.6 il comportamento è stabile; con Tcl/Tk 9 sono emerse fragilità nelle chiamate GUI da thread di lavoro.

Possibile soluzione:

- coda dedicata;
- esecuzione esclusiva nel thread Tk;
- `after()` o dispatcher;
- eliminazione della dipendenza dal comportamento interno di Tcl.

È una modifica delicata perché cambia un contratto già coperto dai test.

## 4.2 `atomic_write` e `fsync`

Valutare:

- flush esplicito;
- `fsync`;
- eventuale sincronizzazione della directory dopo rename atomico.

Obiettivo: aumentare la robustezza del salvataggio in caso di crash o perdita improvvisa di alimentazione.

## 4.3 Conferma alla chiusura con sessione modificata

Se la sessione è dirty e non salvata, offrire:

- Salva;
- Non salvare;
- Annulla.

Integrare con cronologia, stato dirty/clean e salvataggio esperimenti.

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

Estendere la copertura automatica a:

- smoke test GUI Windows;
- export PDF;
- export XLSX;
- multiprocessing;
- caricamento/salvataggio sessioni;
- licenze incluse;
- assenza dei PDF fonte.

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

\[
T(i)=j
\]

significa che il contenuto inizialmente nella posizione \(i\) termina nella posizione \(j\).

Per la matrice:

\[
M[T[i],i]=1.
\]

Per la composizione:

\[
A\circ B
\]

significa prima \(B\), poi \(A\).

## 5.2 Gerarchia strutturale

Preservare:

\[
G
\xrightarrow{\text{realizzazione}}
H
\subset
\Gamma_{3,3}
\subset
S_3\wr S_3
\subset
S_{27}.
\]

Con:

\[
G\cong S_3^3,
\qquad
H\cong G,
\qquad
|H|=216,
\]

e:

\[
\Gamma_{3,3}
=
\langle H,\MSC\rangle
=
\langle\mathcal S_F\rangle,
\qquad
|\Gamma_{3,3}|=648.
\]

## 5.3 Gaia

Il nome narrativo **Gaia** resta associato alle trasformazioni complete, cioè a \(G\)/\(H\) secondo il livello astratto o concreto.

Non associare Gaia a \(\Gamma\).

## 5.4 Rovesciamento globale

\[
J\in H.
\]

Il rovesciamento globale non amplia il gruppo.

## 5.5 Procedure e trasformazioni

Preservare la distinzione:

- 1 728 Procedure fisiche;
- 216 trasformazioni complete distinte in \(H\).

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

1. decomposizione ciclica grafica;
2. grafi delle orbite;
3. grafo di Cayley di \(H\);
4. classi laterali di \(H\) in \(\Gamma\);
5. fibre digitali e loro trasporto;
6. confronto \(T/T^{-1}\);
7. relazioni fra tabelloni;
8. grafi delle transizioni complete/intermedie.

## 4.2

1. \(\mathcal S_F\) esplicita;
2. Laboratorio delle fibre;
3. forma normale in \(\Gamma\);
4. \(\Lambda_{i,u}\);
5. forma canonica di \(J\);
6. equivalenze fra Procedure;
7. dominio Kronecker esteso su 27 carte;
8. valutazione di \(b^m\);
9. valutazione del caso rettangolare.

## 4.3

1. rappresentazione esplicita degli elementi del wreath product;
2. sincronizzazione fra fattori locali, azione sui blocchi e permutazione sulle 27 posizioni;
3. appartenenza e confronto con \(H\), \(\Gamma_{3,3}\) e dominio Kronecker esteso;
4. tutor algebrico contestuale;
5. modalità didattica con esercizi e correzione motivata.

## Manutenzione

Priorità alta:

- warning setuptools;
- automazione build/release;
- dirty-session close.

Priorità media:

- `fsync`;
- test più completi del bundle Windows.

Priorità strutturale, da pianificare con cautela:

- `ui_call` e threading Tk/Tcl 9.

---

# 7. Criteri per aprire una nuova release

## 4.0.x

Solo:

- correzioni di bug;
- regressioni;
- problemi di packaging;
- compatibilità;
- sicurezza;
- documentazione correttiva.

Nessuna nuova funzione sostanziale.

## 4.1.0

Apertura quando esiste almeno un primo nucleo coerente di visualizzazioni strutturali realmente utilizzabili, preferibilmente:

- cicli;
- orbite;
- almeno un grafo di gruppo.

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
- \(H\) e \(\Gamma\) sono distinti correttamente;
- la Fase P ha riallineato programma e libro;
- la suite finale è verde;
- wheel, sdist e bundle Windows sono stati costruiti;
- la 4.0.0 è pubblicata come release stabile;
- i grafi veri e propri sono intenzionalmente rinviati alla serie successiva.

La 4.0.0 ha avviato questa roadmap; la base corrente è ora la 4.0.1, che ne
consolida l'interfaccia senza cambiare il nucleo matematico. Lo sviluppo futuro
aggiunge capacità alla versione corrente senza riaprire le serie già chiuse.
