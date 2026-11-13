# A1 — Audit finale di correttezza matematica

**Prodotto:** Gioco delle 27 carte — release candidate 4.0.0

**Data:** 2026-09-26

**Esito del gate:** **A1 CONCLUSO CON ISSUE APERTI**

**Natura del lavoro:** audit soltanto; nessuna correzione applicata

## 1. Stato e perimetro

L'audit è partito dal ramo `main`, HEAD `589c5855badac7d521426ddfd7987409b2709939`, con `origin/main` a `6e77210f31e467f0915e3cca0af4c9ef39328e44` e ramo locale avanti di tre commit. Il working tree conteneva soltanto i due file fonte intenzionalmente non tracciati, `Articolo.pdf` e `LIBRO_MAIN.pdf`.

Sono state inventariate e verificate le affermazioni matematiche correnti esposte da GUI, Guida, glossario, onboarding, tooltip/help, README, note 4.0.0, CLI, diagnostica e formati di export. I documenti `docs/history/` sono stati usati soltanto per ricostruire decisioni e convenzioni, non come testo corrente da giudicare.

Il risultato è un inventario di **160** formule, affermazioni ed esempi. Sono emersi:

- 2 issue `MATH-HIGH`;
- 3 issue `MATH-MEDIUM`;
- 3 `SOURCE-TENSION`;
- nessun `MATH-BLOCKER`, `MATH-LOW`, `NOT-MATH` o contenuto matematico non verificabile.

Le cinque issue matematiche sono limitate a formulazioni user-facing. I calcoli del core, i servizi, la CLI e gli output numerici campionati hanno dato risultati coerenti con gli oracoli indipendenti.

## 2. Fonti

### 2.1 Fonti primarie

| fonte | ruolo nell'audit | impronta SHA-256 | stato |
|---|---|---|---|
| `Articolo.pdf` | definizione di separabilità, fattorizzazione, somme di fibra, classi | `293BA88C1942A2D7CFDC44B29BB6AD5B7B9B87D4A449B3A7009BFBAABFC8D5A9` | letto, non modificato, non tracciato |
| `LIBRO_MAIN.pdf` | modello fisico, Tavola, gruppi, Procedure, guide, App. D | `1E1C9A7E4A8B19E723EBEA39EF4F636AEBA2E954E7C4900F2D322E7663235E6A` | letto, non modificato, non tracciato |

Passaggi controllati direttamente: Articolo pp. PDF 4–9; Libro pp. PDF 50–54, 66–67, 183–190, 217, 271–273, 282–285 e 409–416. Sono state confrontate anche le formule e le tabelle circostanti, non soltanto le frasi citate dal prodotto.

### 2.2 Fonti di progetto

Sono stati letti `README.md`, `docs/README.md`, `docs/release/NOTE_VERSIONE_4.0.0.md`, l'audit di copertura V4, la sua matrice e i documenti decisionali pertinenti. Le decisioni fissano l'interpretazione software; non sono state usate per sostituire una prova matematica primaria.

## 3. Convenzioni

Le verifiche usano le convenzioni approvate e ne controllano la coerenza sulle superfici:

| oggetto | convenzione verificata |
|---|---|
| posizioni | `0..26`, con 0 in cima |
| indirizzo ternario | `n=9n₂+3n₁+n₀` |
| trasformazione | `T[carta/indice iniziale]=posizione destinazione` |
| mazzo | `deck[posizione]=carta`; per il mazzo ordinato, il mazzo finale è `T⁻¹` |
| composizione | `(a∘b)[i]=a[b[i]]`, prima `b`, poi `a` |
| matrice | `M(T)[T(i),i]=1`; `M(a∘b)=M(a)M(b)` |
| MSC | `MSC(n)=9(n mod 3)+floor(n/3)` |
| fattori | ordine dei fattori alto→basso `P₂⊗P₁⊗P₀` |
| rovesciamento | DP3=A: `Jᵢ` prima della distribuzione dello stadio `i` |
| gruppi | `H` 216, `Γ` 648, `S27` ambiente |

La mancata uniformità dell'indicizzazione dei fattori in alcune stringhe user-facing è registrata come `A1-MATH-02`.

## 4. Metodo

Ogni riga dell'allegato CSV distingue:

- **FONTE:** formula o enunciato nel libro/articolo;
- **CODICE:** convenzione e risultato implementato;
- **TEST:** copertura esistente e sua indipendenza effettiva;
- **ESECUZIONE:** CLI, servizi, suite o output realmente generato;
- **INFERENZA:** derivazione matematica o enumerazione indipendente.

Gli oracoli usati comprendono lettura diretta delle fonti, calcolo simbolico, enumerazioni scritte separatamente dalle funzioni sotto audit, confronto con il core, test storici e generazione reale di export. La suite completa ha dato **2.051 passed, 320 skipped**; gli skip dipendono prevalentemente da display/ambiente e non hanno lasciato scoperta alcuna legge matematica, perché i relativi dati sono stati verificati a livello di servizio, struttura esportata o rendering campione.

Le enumerazioni principali sono state:

- 27 posizioni e tutte le fibre ternarie;
- 216 elementi di H, incluse 46.656 composizioni;
- 648 elementi di Γ, incluse 419.904 composizioni;
- 1.728 Procedure;
- 729 coppie carta/bersaglio;
- 26 traslazioni non banali;
- 27 classi interne e la loro fusione in 7 tipi ciclici;
- tutti i vertici/archi e le distanze dei tre grafi I6.

## 5. Inventario delle formule

L'inventario normativo è `docs/audits/A1_FINAL_MATHEMATICAL_AUDIT.csv`. Contiene 160 righe, identificatori `A1-001`…`A1-160` e tutte le colonne richieste.

| classificazione | righe |
|---|---:|
| `CORRETTA` | 152 |
| `CORRETTA MA AMBIGUA` | 1 |
| `CORRETTA SOLO SOTTO CONVENZIONE ESPLICITA` | 1 |
| `IMPRECISA` | 1 |
| `ERRATA` | 2 |
| `TENSIONE FRA FONTI` | 3 |
| `INCOMPLETA` | 0 |
| `NON VERIFICABILE` | 0 |

Le duplicazioni IT/EN sono state trattate come una sola affermazione quando sono traduzioni matematicamente identiche della stessa chiave; le superfici coinvolte sono elencate insieme. Gli esempi numerati distinti e i controesempi hanno invece una verifica propria.

## 6. Base 3 / MSC

La codifica ternaria è biiettiva su `0..26`; cifre e pesi sono coerenti in Guida, tabellone e core. La macchina che dimentica soddisfa

`P' = floor(P/3)+9s`,

e dopo tre stadi

`P₃=9s₂+3s₁+s₀`.

Il calcolo spiega sia la perdita `27→9→3→1`, sia l'indipendenza finale dall'indirizzo iniziale, salvo l'informazione osservata/adattata durante le fasi. L'esempio #100/carta 19 è corretto:

`(2,0,1)→(2,2,0)→(1,2,2)→(2,1,2)=23`, con colonne `1,0,2=rev ω(19)`.

Per MSC sono corretti il vettore numerico, la rotazione `(i₂,i₁,i₀)→(i₀,i₂,i₁)`, MSC², `MSC³=I` e la relazione di trasporto. La formula volutamente marcata «errata (non usare)» è davvero falsa e quindi non costituisce un issue.

## 7. Permutazioni / matrici

Le convenzioni di T, T⁻¹, deck, composizione, cicli, ordine, punti fissi e orbite sono coerenti nel core e negli output. Le righe didattiche #100, #91, #56, #62 e #195 sono state ricalcolate, incluse inverse, ordini e tipi ciclici.

Le matrici numeriche rispettano `M[T(i),i]=1`, la composizione matriciale e `M(T⁻¹)=M(T)ᵀ`. Sono però presenti due errori testuali e un'imprecisione di indicizzazione:

- `A1-MATH-01`: la descrizione di un punto `(i,j)` in `M(T⁻¹)` inverte origine e destinazione;
- `A1-MATH-02`: l'ordine dei fattori viene indicizzato in tre modi incompatibili senza dichiarare il cambio;
- `A1-MATH-03`: la rotazione dei fattori nella formula canonica di `T⁻¹` è nel verso sbagliato.

Le griglie, le inverse numeriche e le trasformazioni calcolate non risultano affette.

## 8. H / Γ / S27

Sono confermati:

- `H≅S₃³`, `|H|=216`, chiusura, inverse e transitività;
- ordini in H: `{1:1, 2:63, 3:26, 6:126}`;
- punti fissi in H: `{27:1, 9:9, 3:27, 1:27, 0:152}`;
- 64 elementi auto-inversi;
- 27 classi di coniugio interne, centro banale;
- 7 tipi ciclici ambientali con cardinalità `1,9,27,27,26,54,72`;
- `Γ=H⊔H∘MSC⊔H∘MSC²`, `|Γ|=648`;
- ordini in Γ: `{1:1, 2:63, 3:98, 6:342, 9:144}`.

Le 419.904 composizioni di Γ sono chiuse e ogni elemento ha inversa. Nessuna superficie corrente dice «H ha 7 classi»: il prodotto distingue correttamente le 27 classi interne dai 7 tipi ciclici di S27.

## 9. Procedure / rovesciamenti

Le `216×8=1.728` Procedure formano 216 fibre globali di 8, con una sola Procedura senza rovesciamenti per trasformazione. Per ogni coppia carta/bersaglio la fibra ha 64 Procedure, 8 T distinte e 8 Procedure semplici. La strategia storica coincide con il Simulatore su 729/729 coppie; la variante sicura differisce in 386/729.

Le formule del Corollario 5.2 sono riportate correttamente:

- `uᵢ=Σ_{h=0..i} ε_h mod 2`;
- `vᵢ=Σ_{h=i+1..m−1} ε_h mod 2`;
- `Qᵢ=R^{vᵢ}∘Sᵢ∘R^{uᵢ}`;
- `Sᵢ=R^{vᵢ}∘Qᵢ∘R^{uᵢ}`.

L'esempio App. D 7.2 è corretto e porta `5→25`. L'intera caratterizzazione è verificata sulle 1.728 Procedure.

`A1-MATH-04` riguarda soltanto la descrizione fisica introduttiva: «rovescia dopo la raccolta, prima dello stadio successivo» è equivalente a DP3=A sugli intervalli interni mediante reindicizzazione, ma non ai bordi senza l'adattatore esplicito. Le formule successive usano correttamente DP3=A.

## 10. Errori / spettatore

Per I3 sono corretti:

- E1 soltanto per CDS/DSC;
- #111 con E1 in fase 1 → posizione 19 e #112;
- #111 con E1 in fase 3 → posizione 11 e #147;
- CSD³ con E2 in fase 1/2/3 → 25/22/13;
- E2 finale `J∘T=#172`;
- E4 per 0→13, colonna 1/SCD → posizione 12;
- massimo 36 recuperi dopo fase 1 e 6 dopo fase 2;
- impossibilità di recuperare E1/E4 nelle fasi successive;
- esistenza del recupero E3 dichiarato e ritorno `#172⁻¹`.

Per I4 sono confermati `27→9→3→1`, l'ordine delle cifre osservate, la separazione fra dinamica fisica e informativa e il protocollo B12. L'esempio osservato `(DSC,DSC,CSD)` dà i mescolamenti `(CDS,CDS,CSD)`, riga #100, e il ritorno dichiarato.

## 11. Riconoscimento / somme di fibra

Il riconoscimento diretto implementa esattamente la Def. 4.1: a ogni livello la cifra d'arrivo deve dipendere solo dalla cifra d'origine. I risultati esaustivi sono `216/216` separabili in H e `216/648` in Γ.

Con DP1=C, il riferimento operativo per le somme è App. D, Teor. 6.4:

`ρ̂ᵢ(t)=(Σᵢ,ₜ−Cᵢ)/3^(2+i)`, con `C₀=108`, `C₁=90`, `C₂=36`.

La condizione è necessaria e sufficiente soltanto quando, a ogni livello, i candidati sono interi, appartengono a `{0,1,2}`, sono distinti e formano una permutazione. Il controesempio «somme equilibrate» produce `(1,1,1)` e dimostra correttamente che l'integralità da sola non basta.

L'esempio comune alle fonti è stato ricalcolato:

| livello | somme | fattore ricostruito |
|---:|---|---|
| 0 | 117, 126, 108 | (1,2,0) |
| 1 | 144, 117, 90 | (2,1,0) |
| 2 | 117, 36, 198 | (1,0,2) |

Le somme dei blocchi `36,117,198`, gli intervalli `28..36`, `100..108`, `172..180` e l'esempio `S₈=104→j=1→x=13` sono corretti.

## 12. Traslazioni / due mazzi / guide

L'enumerazione di `C_k(x)=x+k mod 27` dà:

- `C9=#144` e `C18=#108`, entrambe in H e Γ;
- le altre 24 traslazioni non banali sono fuori sia da H sia da Γ;
- C1 supera il livello 0 e fallisce ai livelli 1 e 2.

La formula A8 `T_rel=T_B∘T_A⁻¹` è corretta. `A1-MATH-05` riguarda la frase «la trasformazione relativa è sempre separabile»: è vera per i mazzi gemelli della fonte, cioè quando `T_A,T_B∈H`, ma non per due mazzi arbitrari ammessi dall'input generale. Con A ordinato e B pari al mazzo finale di C1 si ottiene `T_rel=C1`, non separabile. La vista calcola correttamente l'esito; manca la premessa nel testo della Guida.

Le due guide `q₀=2`, `q₂=22` danno la terza posizione 15. I fattori del ritorno sono `τ₂=SCD`, `τ₁=SDC`, `τ₀=CDS` e `R(0..2)=(1,2,0)`. La somma delle guide è 39 su tutto H e Γ, ma non su S27.

## 13. L90 / successioni

Per una successione cronologica vale

`C_N=T^(N)∘…∘T^(1)` e `R=C_N⁻¹`.

Il ritorno compresso riporta all'origine; la ricostruzione della storia richiede invece le inverse dei singoli passi nell'ordine inverso. Il prodotto mantiene correttamente le due nozioni separate e non attribuisce memoria storica a `C_N`.

L'esempio `(#100,0), (#56,5), (#17,5)` è stato eseguito da CLI e ricalcolato: righe effettive `[100,56,11]`, cumulativo #117, ritorno `CDS SDC CDS`.

## 14. Laboratorio I6

Il catalogo dichiara il dominio di ogni proprietà e distingue verifica esaustiva, teorema e controesempio. Sono stati ricontrollati in particolare:

- ordini di H e i 144 elementi d'ordine 9 in Γ;
- centro banale;
- J: #215, classe #27 `(T,T,T)`, ordine 2, unico fisso 13;
- classi laterali di 216 elementi;
- fasi `12→12`, `144→72`, `1.728→216`;
- controesempio A4: nessuna T∈H manda simultaneamente 0→0 e 1→3;
- controesempi S27 per punti fissi e somma delle guide.

Le etichette «verificato esaustivamente» restano circoscritte ai domini finiti effettivamente enumerati; non vengono presentate come dimostrazioni su S27.

## 15. Grafi / classi / stadi / 6×6

| struttura | vertici | archi | grado | diametro | verifica |
|---|---:|---:|---:|---:|---|
| Cayley S3 con trasposizioni | 6 | 9 | 3 | 2 | BFS completo; K₃,₃ |
| H, una trasposizione per livello | 216 | 972 | 9 | 6 | BFS completo |
| Cronache, cambio di una raccolta | 216 | 1.620 | 15 | 3 | BFS completo |

La tavola locale coincide 36/36 con la fonte; ogni risultato ha 6 decomposizioni `P∘Q`. Senza rovesciamenti le configurazioni/trasformazioni ai tre prefissi sono `6/6`, `36/36`, `216/216`; con rovesciamenti sono `12/12`, `144/72`, `1.728/216`, nelle classi laterali `H∘MSC`, `H∘MSC²`, `H`.

## 16. Esempi

Tutti gli esempi numerati correnti individuati nelle superfici matematiche sono stati ricalcolati:

| esempio | risultato verificato |
|---|---|
| #0 | identità, auto-inversa |
| #56 / #62 | inverse reciproche |
| #78 | auto-inversa |
| #82 | ancora: Assi `(10,8,21)` |
| #91 | fattori `(SDC,DSC,CSD)`, gemello con #100 |
| #93 | inversa di #100 |
| #100 | `(CDS,CDS,CSD)`, Assi `(13,8,18)`, ordine 6 |
| #108 | C18 |
| #111 / #112 / #147 | scenari E1 corretti |
| #142 / #177 | inverse reciproche |
| #144 | C9 |
| #172 | trasformazione E2 finale `J∘T` |
| #185 | equivalente della procedura con ε=(0,0,1) dichiarata |
| #193 | auto-inversa |
| #195 / #196 | inverse reciproche; chiarimento deck/T |
| #215 | J, ordine 2, unico fisso 13 |
| #17 / #11 / #117 | esempio di successione L90 ricalcolato |

Sono inoltre verificati l'esempio #100/carta 19, `T₁₀₀(10)=5`, `T₁₀₀⁻¹(10)=6`, `S₈=104`, App. D Es. 7.1, App. D Es. 7.2, q₀/q₂ e i casi E1–E4.

## 17. Controesempi

| proposizione negata | controesempio | esito |
|---|---|---|
| il tabellone inverso è il diretto letto al contrario | #100: 5 contro 6 all'ingresso 10 | valido |
| stessa carta al bersaglio implica stessa T | carta 0→13 con 8 T diverse | valido |
| candidati interi bastano per il criterio delle somme | somme equilibrate `(1,1,1)` | valido |
| C1 appartiene alla classe del gioco | conflitti ai livelli 1 e 2 | valido |
| gli ordini di H valgono anche in Γ | elemento di Γ d'ordine 9 | valido |
| i punti fissi di H valgono in S27 | scambio 25↔26: 25 fissi | valido |
| la somma guide 39 vale in S27 | scambio 25↔26: somma 38 | valido |
| due carte possono essere forzate ovunque in H | vincoli 0→0 e 1→3 senza soluzione | valido |
| ogni T∈Γ ha decomposizione a tre stadi in H | MSC: 0 decomposizioni | valido |

I controesempi delle issue `A1-MATH-01`, `A1-MATH-03` e `A1-MATH-05` sono riportati nelle rispettive schede al §22.

## 18. Export

Sono stati prodotti in directory temporanee automatiche e poi rimossi campioni effettivi di:

- CSV combinazioni;
- PDF standard, esteso e dettagliato;
- XLSX analisi;
- LaTeX permutazioni e coniugio;
- SVG frecce/griglia di coniugio;
- TXT riepilogo;
- HTML protocollo;
- JSON esperimento con reload verificato.

Strutture, formule e numeri sono coerenti con il core, con l'eccezione delle formule user-facing già registrate in `A1-MATH-01` e `A1-MATH-03` quando la Guida viene usata come spiegazione. Nessun output temporaneo è rimasto nel repository o fuori da esso come workspace persistente.

## 19. CLI

Sono stati eseguiti output human-readable e JSON per `selftest`, `recognize`, `property` e `sequence`, oltre a `export` CSV di un esperimento verificato. Risultati salienti:

- versione `4.0.0`;
- selftest interamente `OK`;
- identità: separabile, #0, k=0, somme vere;
- C9: separabile, #144, k=0, somme vere;
- ordini H: vero su 216;
- ordini Γ: falso, controesempio d'ordine 9, dominio 648;
- successione campione: tre righe, cumulativo #117, ritorno corretto;
- CSV `sequence` ed `export` con tre righe e manifest coerenti.

CLI e GUI condividono le stesse convenzioni matematiche e gli stessi dati di servizio.

## 20. Numeri globali

| numero | significato verificato |
|---:|---|
| 3 | base, cifre, colonne, stadi |
| 9 | elementi per fibra digitale |
| 27 | posizioni e carte |
| 216 | `6³`, trasformazioni di H |
| 648 | `3·216`, elementi di Γ |
| 1.728 | `216·8`, Procedure ordinarie; anche configurazioni estese per singolo stadio |
| 46.656 | `216²`, decomposizioni per T∈H |
| 419.904 | `648²`, coppie di Γ |
| 23.887.872 | `46.656·8³`, storie estese per T |
| 729 | `27²`, coppie carta/bersaglio |
| 64 | Procedure per una coppia carta/bersaglio; anche elementi auto-inversi di H, con significati distinti |
| 8 | Procedure per T; T distinte per fibra carta/bersaglio; preimmagini di un blocco esteso, secondo il contesto |
| 27 classi | coniugio interno di H |
| 7 tipi | tipi ciclici ambientali di S27 incontrati da H |
| 10.077.696 | `216³`, terne di blocchi A₀,A₁,A₂ totali |
| 5.159.780.352 | `1.728³`, combinazioni estese complete |
| 972 / 1.620 | archi dei grafi H / Cronache |

I casi in cui lo stesso numero ha più significati sono esplicitati; non è stata trovata una confusione numerica corrente fra 1.728 Procedure e 216 trasformazioni.

## 21. Tensioni fra fonti

### A1-SRC-01 — Perimetro dei rovesciamenti

L'Articolo conclude sotto l'ipotesi di assenza di rovesciamenti; l'Appendice D del Libro estende il modello con rovesciamenti e blocchi effettivi. È una differenza reale di perimetro. Il prodotto segue correttamente App. D e DP3=A.

### A1-SRC-02 — Criterio delle somme

L'Articolo, Oss. 5.3, non assume la sola compatibilità numerica delle somme come criterio per una permutazione arbitraria. L'Appendice D, Teor. 6.4, dimostra il criterio iff aggiungendo la condizione che i candidati ricostruiti siano permutazioni locali. DP1=C è rispettata: il prodotto cita App. D e mostra anche il controesempio all'integralità da sola.

### A1-SRC-03 — Tagli C9/C18

Il Libro A13 afferma in modo generale che il taglio non appartiene al gruppo del Gioco. L'enumerazione mostra due eccezioni: C9=#144 e C18=#108 appartengono a H. Il prodotto usa la formulazione calcolata «solo C9 e C18», quindi non propaga l'affermazione assoluta della fonte.

## 22. Errori trovati

### A1-MATH-01 — Direzione di un punto nella matrice di T⁻¹ (`MATH-HIGH`)

- **Posizione:** `gioco27/i18n.py`, chiave `guide.s17.right.body`, IT e EN.
- **Testo corrente:** un punto `(i,j)` di `T⁻¹` significherebbe che la carta in `i` torna in `j`.
- **Corretto:** con la convenzione dichiarata `M[i,j]=1 ⇔ T(j)=i`, un punto `(i,j)` di `M(T⁻¹)` significa che l'ingresso `j` va in `i`.
- **Prova:** per C9, `T⁻¹=C18`; il punto `(18,0)` rappresenta `0→18`, non `18→0`.
- **Impatto:** spiegazione dell'orientazione righe/colonne falsa; matrici e calcoli corretti.
- **Test insufficiente:** i test verificano le matrici, non la semantica della frase localizzata.

### A1-MATH-02 — Indicizzazione incoerente dei fattori (`MATH-MEDIUM`)

- **Posizioni:** `filter.intro`, `cayley.help.intro`, `guide.s16.subtabs.items`, `guide.s17.inverse_formula`, IT e EN.
- **Testi correnti:** compaiono `P₂⊗P₁⊗P₀`, `P₃⊗P₂⊗P₁` e `P₀⊗P₁⊗P₂` come se fossero la stessa convenzione.
- **Corretto:** la convenzione pubblica fissata è alto→basso `P₂⊗P₁⊗P₀`; un'eventuale numerazione storica 1..3 deve essere dichiarata, non mescolata con 0..2.
- **Prova:** `kronecker3` e le formule di livello agiscono su pesi 9,3,1 in quell'ordine.
- **Impatto:** rischio di leggere o ricostruire i fattori al contrario; nessun errore numerico nel core.
- **Test insufficiente:** i test di presenza/i18n congelano le stringhe ma non ne confrontano l'indicizzazione matematica.

### A1-MATH-03 — Rotazione errata nella forma canonica di T⁻¹ (`MATH-HIGH`)

- **Posizione:** `guide.s17.inverse_formula`, IT e EN.
- **Formula corrente:** `T⁻¹=rot_{2k}(K⁻¹)∘MSC^{(3−k) mod 3}`.
- **Formula corretta:** `T⁻¹=rot_k(K⁻¹)∘MSC^{(3−k) mod 3}`, con `rot_n` rotazione sinistra dei tre fattori.
- **Derivazione:** da `MSC∘K=rot₂(K)∘MSC`, si ha `MSC^{-k}∘K⁻¹=rot_{-2k}(K⁻¹)∘MSC^{-k}` e `−2k≡k (mod 3)`.
- **Prova esecutiva:** per `K=(CDS⊗SDC⊗DCS)`, la formula corrente fallisce già all'indice 0 sia per k=1 sia per k=2; `rot_k` coincide con l'inversa su tutti i 27 ingressi.
- **Impatto:** formula esplicativa falsa; l'inversa numerica/matriciale prodotta dal programma è corretta.
- **Test insufficiente:** nessun test valuta semanticamente la formula renderizzata.

### A1-MATH-04 — Momento del rovesciamento ambiguo nella procedura introduttiva (`MATH-MEDIUM`)

- **Posizioni:** `guide.s01.steps`, con eco in `guide.s05.intro`, IT e EN.
- **Testo corrente:** il mazzo viene rovesciato dopo la raccolta, prima dello stadio successivo.
- **Convenzione corretta:** `Stageᵢ=Pᵢ∘MSC∘Jᵢ`, quindi `Jᵢ` agisce prima della distribuzione dello stadio `i`.
- **Prova:** l'adattatore fra convenzioni A/B è verificato sulle 1.728 Procedure, ma richiede uno spostamento degli indici e fattori di bordo.
- **Impatto:** rischio di attribuire εᵢ allo stadio sbagliato; le sezioni formali successive sono corrette.
- **Test insufficiente:** esistono test dell'adattatore, non un controllo di coerenza semantica fra le due descrizioni della Guida.

### A1-MATH-05 — Premessa mancante per A8 (`MATH-MEDIUM`)

- **Posizione:** `guide.i5.other`, IT e EN.
- **Testo corrente:** per i mazzi gemelli la relativa è «sempre separabile», senza esplicitare `T_A,T_B∈H` nello stesso blocco che presenta input arbitrari A/B.
- **Corretto:** `T_B∘T_A⁻¹∈H` se A e B derivano dallo stesso ordine iniziale tramite trasformazioni di H; per due mazzi arbitrari la relativa può non essere separabile.
- **Prova:** A ordinato e B uguale al mazzo finale di C1 producono relativa C1, che è fuori H e Γ.
- **Impatto:** generalizzazione indebita nella spiegazione; la vista verifica correttamente il caso concreto.
- **Test insufficiente:** i test A8 usano coppie provenienti da H e non mettono alla prova la portata della frase.

## 23. Rischi e test insufficienti

1. I test i18n verificano soprattutto presenza, sincronizzazione IT/EN e stringhe attese; non sono un oracolo semantico per formule come `rot_{2k}` o per la direzione `(i,j)`.
2. Diversi test confrontano servizi con il core condiviso. L'audit li ha integrati con derivazioni e enumerazioni indipendenti, ma il test ordinario resta meno indipendente dell'audit.
3. Il selftest è un eccellente controllo di regressione, non una prova sufficiente delle frasi della Guida.
4. Gli export sono stati campionati realmente; non è ragionevole materializzare 5.159.780.352 combinazioni. La copertura strutturale deriva invece dall'enumerazione di tutte le 216 T possibili e dalle proprietà dimostrate dei fattori.
5. S27 non è enumerabile in pratica. Le affermazioni universali usano teoremi delle fonti; le negazioni usano controesempi espliciti nel dominio.

## 24. Copertura

| area | inventariato | verificato | corretto | ambiguo/impreciso/solo-convenzione | errore | tensione fonti | non verificabile |
|---|---:|---:|---:|---:|---:|---:|---:|
| base 3 | 8 | 8 | 8 | 0 | 0 | 0 | 0 |
| MSC | 8 | 8 | 8 | 0 | 0 | 0 | 0 |
| permutazioni | 13 | 13 | 13 | 0 | 0 | 0 | 0 |
| matrici | 8 | 8 | 5 | 1 | 2 | 0 | 0 |
| H/Γ/S27 | 15 | 15 | 15 | 0 | 0 | 0 | 0 |
| Procedure | 10 | 10 | 10 | 0 | 0 | 0 | 0 |
| reversals | 9 | 9 | 7 | 1 | 0 | 1 | 0 |
| errori | 10 | 10 | 10 | 0 | 0 | 0 | 0 |
| spettatore | 6 | 6 | 6 | 0 | 0 | 0 | 0 |
| riconoscimento | 11 | 11 | 10 | 0 | 0 | 1 | 0 |
| somme di fibra | 10 | 10 | 10 | 0 | 0 | 0 | 0 |
| traslazioni | 5 | 5 | 4 | 0 | 0 | 1 | 0 |
| due mazzi | 5 | 5 | 4 | 1 | 0 | 0 | 0 |
| guide | 6 | 6 | 6 | 0 | 0 | 0 | 0 |
| L90/J | 8 | 8 | 8 | 0 | 0 | 0 | 0 |
| I6 | 9 | 9 | 9 | 0 | 0 | 0 | 0 |
| grafi | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| export | 8 | 8 | 8 | 0 | 0 | 0 | 0 |
| CLI | 6 | 6 | 6 | 0 | 0 | 0 | 0 |
| **totale** | **160** | **160** | **152** | **3** | **2** | **3** | **0** |

## 25. Limiti

- Non è stata eseguita un'enumerazione di S27; le proprietà universali dipendono dalle prove delle fonti e i fallimenti da controesempi verificati.
- Gli export enormi sono coperti per struttura e mediante campioni reali, non materializzati integralmente.
- L'audit non valuta qualità terminologica, stile italiano o stile inglese, salvo quando una scelta di parole cambia il contenuto matematico.
- Nessuna issue è stata corretta in questo compartimento.

## 26. Git / filesystem

- Lavoro svolto esclusivamente nel repository corrente e in temporanei automatici.
- Nessun workspace manuale esterno, backup, reset, rebase o push.
- `Articolo.pdf` e `LIBRO_MAIN.pdf` sono rimasti intatti, non spostati e non tracciati; le impronte finali coincidono con quelle iniziali.
- Nessun estratto PDF persistente è stato creato.
- I soli file creati sono questo rapporto e il CSV associato.
- Il commit documentale previsto è `docs(A1): audit final mathematical correctness` e deve contenere soltanto i due deliverable A1.

## 27. Gate

| gate | esito | evidenza sintetica |
|---|---|---|
| A1-G1 | PASS | fonti e SHA-256 registrati |
| A1-G2 | PASS | convenzioni fissate al §3 |
| A1-G3 | PASS | superfici correnti inventariate |
| A1-G4 | PASS | 160 righe nel CSV |
| A1-G5 | PASS | esempi al §16 e nel CSV |
| A1-G6 | PASS | controesempi al §17 |
| A1-G7 | PASS | numeri globali al §20 |
| A1-G8 | PASS | base 3, 27 ingressi |
| A1-G9 | PASS | MSC, potenze e trasporto |
| A1-G10 | PASS | T/T⁻¹/composizione |
| A1-G11 | PASS | matrici verificate; issue documentate |
| A1-G12 | PASS | H/Γ/S27 e 419.904 prodotti |
| A1-G13 | PASS | 1.728 Procedure e fibre |
| A1-G14 | PASS | Cor. 5.2 su 1.728 Procedure |
| A1-G15 | PASS | I3 ricalcolato |
| A1-G16 | PASS | I4 su 729 coppie |
| A1-G17 | PASS | I5 diretto su H/Γ |
| A1-G18 | PASS | Teor. 6.4: fonte, prova, oracolo indipendente |
| A1-G19 | PASS | C1..C26 enumerati |
| A1-G20 | PASS | A8 e guide verificate |
| A1-G21 | PASS | L90/J ricalcolati |
| A1-G22 | PASS | catalogo I6 eseguito |
| A1-G23 | PASS | grafi, stadi e 6×6 completi |
| A1-G24 | PASS | nove famiglie di export campionate |
| A1-G25 | PASS | CLI human/JSON/CSV campionata |
| A1-G26 | PASS | tre tensioni registrate |
| A1-G27 | PASS | ogni issue ha derivazione o controesempio |
| A1-G28 | PASS | nessuna correzione implementata |
| A1-G29 | PASS | nessun push |
| A1-G30 | PASS | filesystem conforme |
| A1-G31 | PASS | PDF intatti e non tracciati |
| A1-G32 | PASS | rapporto MD presente |
| A1-G33 | PASS | allegato CSV presente |

**Decisione:** il compartimento A1 è concluso come audit. Le issue restano aperte per un compartimento di correzione successivo; non sono state modificate in A1.
