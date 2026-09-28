# A5 — Controllo trasversale finale

Data: 28 settembre 2026. Prodotto: Gioco delle 27 carte, release candidate
4.0.0.

## 1. Stato iniziale

Il controllo è iniziato sul ramo `main`, con HEAD
`6b314950c8e04b867c6033fa7b6cd89a3f00059d` (`docs(A4): close English
language verification`) e `origin/main` fermo a
`6e77210f31e467f0915e3cca0af4c9ef39328e44` (`docs(K): close technical
release compartment`). Il ramo locale era avanti di 23 commit. I file
tracciati erano puliti.

PDF invariati e non tracciati.

## 2. Metodo differenziale

A5 ha assunto come base gli esiti già verificati di A1/A1-FIX, A2/A2-FIX,
A3/A3-FIX e A4/A4-FIX. Il controllo si è concentrato sui punti di contatto
fra i quattro cicli: testi matematici, terminologia controllata, coppie IT/EN,
superfici rivolte all'utente, formati di export e identificatori macchina.

Non sono stati ripetuti gli audit completi, non sono state rilette in modo
indiscriminato tutte le chiavi dei cataloghi e non sono stati rigenerati gli
export. Ogni rilievo è stato soltanto registrato: A5 non contiene correzioni.

## 3. Punti matematici ricontrollati

Sono stati ricontrollati 18 punti, confrontando implementazione, Guida,
glossario e testi adiacenti quando presenti.

| N. | Punto | Esito |
|---:|---|---|
| 1 | Convenzione `T[card] = destination position` | coerente |
| 2 | Composizione `(a ∘ b)[i] = a[b[i]]` | coerente |
| 3 | Matrice `M(a ∘ b) = M(a) @ M(b)` | coerente |
| 4 | `MSC³ = I` | coerente |
| 5 | 216 trasformazioni del dominio `H` del libro | coerente |
| 6 | 648 elementi di `Γ` | coerente |
| 7 | 1 728 Procedure, non trasformazioni | coerente salvo A5-MEDIUM-01 |
| 8 | Posizioni indicizzate `0..26` | coerente |
| 9 | Posizione fissa di `J`: 13 | coerente |
| 10 | Ordine pubblico dei fattori, senza il vecchio calco | coerente |
| 11 | Convenzione `P₂ ⊗ P₁ ⊗ P₀` | coerente |
| 12 | DP3: `Jᵢ → MSC → Pᵢ` nello stesso stadio | coerente |
| 13 | `T⁻¹ = rot_k(K⁻¹) ∘ MSC^((3−k) mod 3)` | coerente |
| 14 | Inversa e rovesciamento distinti | coerente |
| 15 | Corollario 5.2: recupero delle raccolte con `ε` noto | coerente |
| 16 | Somme sulle fibre nella formulazione operativa dell'Appendice D | coerente |
| 17 | A8: separabilità limitata al dominio dichiarato | coerente |
| 18 | `C_N`, `C_N⁻¹`, ritorno compresso, replay a ritroso e cronologia distinti | coerente |

I test mirati hanno inoltre confermato la convenzione matriciale,
l'omomorfismo, l'ordine di `MSC`, le cardinalità 216 e 648 e il conteggio
dei 1 728 oggetti di stadio. Non sono emerse contraddizioni matematiche.

## 4. Terminologia

Le distinzioni italiane fra carta, posizione e indice; disposizione,
trasformazione, permutazione e Procedura; distribuzione e raccolta; stadio,
fase, passo e tappa; inversa e rovesciamento restano operative. Le
corrispondenti distinzioni inglesi sono preservate nei testi controllati.

`permutation vector`, `canonical form` e `block signature` indicano ancora
oggetti diversi. Le sigle `MSC`, `R_U` e `C_N⁻¹` sono usate con significato
stabile. Sono però emersi due residui fra superfici diverse, registrati nella
sezione 10.

## 5. Equivalenza IT/EN

Il campione differenziale ha coperto i testi modificati da A4-FIX, le nuove
etichette del PDF, le descrizioni leggibili dei CSV, l'aiuto della CLI per i
token stabili e i passaggi bilingui contenenti formule. Formule, condizioni,
eccezioni e identificatori hanno lo stesso significato nelle due lingue.

L'inglese mantiene la notazione ricca dove il canale la consente e conserva
ASCII o identificatori italiani soltanto nei contratti che lo richiedono. Un
calco inglese residuo in quattro testi rivolti all'utente è registrato come
A5-MEDIUM-02.

## 6. UI, Guida, glossario e CLI

Il confronto mirato ha incluso 216 trasformazioni, 1 728 Procedure, `H`,
`Γ`, `S₂₇`, `MSC`, rovesciamento, inversa, posizione 13, riconoscimento,
ritorno compresso, replay a ritroso e Sessione/L90.

I concetti matematici e L90 risultano compatibili fra le superfici. Restano
due incoerenze testuali circoscritte: la Guida e un tooltip chiamano i 1 728
oggetti anche “sequenze/combinazioni”; il glossario e un errore CLI inglesi
usano `succession` dove le altre superfici usano `sequence`.

## 7. Export

Sono stati riutilizzati gli esiti verificati di A4-FIX e sono stati ispezionati
in modo rappresentativo i percorsi di testo semplice, formato ricco Unicode,
LaTeX e formato macchina. `S₂₇`/`S₃`, `T⁻¹`, `MSCᵏ`, `⊗` e `∘` mantengono
la resa prevista per il rispettivo canale.

CSV e JSON conservano gli identificatori stabili. Non essendo emersa
un'anomalia specifica di export, non sono stati rigenerati i dieci campioni.

## 8. Contratti tecnici

Lo schema JSON resta `gioco27.esperimento`, con `schema_version = 1`. Colonne
CSV, chiavi JSON, nomi dei fogli XLSX, token CLI e convenzioni di
serializzazione risultano invariati. I testi inglesi spiegano i token stabili
senza rinominarli.

Il controllo architetturale conferma che `core.permutations` non dipende da
i18n; la localizzazione delle descrizioni CSV resta nel livello di export. I
test mirati di schema e dipendenze sono verdi.

## 9. Tensioni delle fonti

Restano dichiarate, e non presentate come errori risolti:

1. l'assenza di rovesciamenti nell'articolo breve e il rovesciamento prima
   della distribuzione nell'Appendice D;
2. l'ambito dell'Osservazione 5.3 e la formulazione operativa più generale
   delle somme sulle fibre nell'Appendice D;
3. l'affermazione generale del libro sui tagli fuori dal gruppo e le eccezioni
   `C9`/`C18`.

Non è emerso alcun problema A5-SOURCE.

## 10. Problemi trovati

### A5-MEDIUM-01 — i 1 728 oggetti non sono sempre chiamati Procedure

Il titolo della sezione e le principali superfici usano correttamente
“1 728 Procedure”. Tuttavia `guide.s10.count` parla di “1 728 sequenze
distinte” / `1,728 distinct sequences`, mentre `tooltip.verify` usa “1728
combinazioni” / `1,728 combinations`. La compresenza di tre nomi per lo
stesso insieme controllato contrasta con la distinzione terminologica di A2
e può far interpretare i 1 728 oggetti come trasformazioni o aggregati
generici. Nessuna correzione è stata applicata.

### A5-MEDIUM-02 — calco inglese `succession` residuo

`glossary.long.return`, `glossary.long.arrangement`,
`glossary.short.checkpoint` e `cli.error.sequence` usano ancora `succession`
per una sequenza L90. Guida, UI e aiuto dei token stabili usano invece il
termine naturale e controllato `sequence`. Il residuo attraversa glossario e
CLI e può suggerire una distinzione inesistente. Gli identificatori macchina
italiani, incluso `successione`, non sono coinvolti e devono restare
invariati. Nessuna correzione è stata applicata.

| Classe | Numero |
|---|---:|
| A5-HIGH | 0 |
| A5-MEDIUM | 2 |
| A5-LOW | 0 |
| A5-ARCH | 0 |
| A5-DOC | 0 |
| A5-SOURCE | 0 |

## 11. Limiti

A5 è un controllo differenziale e non una nuova esecuzione integrale di
A1–A4. La suite completa, già conclusa prima di A5 con 2 105 test superati,
318 esclusi e 0 errori, non è stata rilanciata. Non sono stati rigenerati
export, pacchetti o eseguibili e non è stata avviata la verifica tecnica
finale.

I due rilievi non sono stati corretti e A5-FIX non è stato avviato. Non è
stato eseguito alcun push.

## 12. Stato Git e filesystem

Il controllo ha creato esclusivamente questo documento. Prima del commit di
chiusura, nessun altro file tracciato risulta modificato. I due PDF sorgente
restano gli unici file non tracciati e non sono stati aperti, modificati,
copiati o rimossi.

Il controllo `git diff --check` e lo stato Git conclusivo sono registrati al
momento della chiusura del commit A5.

## 13. Conclusione

A5 è concluso come audit diagnostico. I 18 punti matematici, i contratti
tecnici, le dipendenze architetturali e le tensioni delle fonti risultano
coerenti. Non emergono problemi HIGH, ARCH, DOC o SOURCE.

La chiusura non dichiara zero issue: restano due incoerenze MEDIUM, entrambe
testuali e circoscritte alla coerenza fra superfici. Sono documentate con
evidenza concreta e rinviate a un eventuale A5-FIX separato. La verifica
tecnica finale verso RC2 non è iniziata.
