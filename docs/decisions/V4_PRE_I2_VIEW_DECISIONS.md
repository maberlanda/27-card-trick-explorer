# V4 — Decisioni pre-I2: tabellone, livello ternario e collegamenti fra viste

> **Natura del documento.** Memo di analisi che rende I2 implementabile. Non implementa nulla.
>
> * Nessun file di codice, test, GUI, i18n, guida, formato o export è stato modificato.
> * Le raccomandazioni sono proposte da approvare, non decisioni prese.
> * Le decisioni che richiedono l'approvazione dell'utente sono raccolte al § 21.

**Etichette di provenienza**:

| Etichetta | Significato |
|---|---|
| **FONTE** | libro `LIBRO_MAIN.pdf` (pagina stampata) o documento già autorevole del repository |
| **CODICE** | lettura del codice corrente |
| **TEST** | test esistenti |
| **ESEC** | verifica eseguita ora con Python inline, senza creare file |
| **INFERENZA** | deduzione argomentata dalle voci precedenti |
| **RACCOMANDAZIONE** | proposta di prodotto, non un fatto |

**Convenzioni**: quelle dell'audit V4, di DP3 = A e di I1.

* posizioni 0..26; `n = 9·n2 + 3·n1 + n0`;
* `T[carta] = posizione finale`; `(a∘b)[i] = a[b[i]]`;
* S = 0, C = 1, D = 2.

---

## 1. Stato di ingresso

ESEC:

| Voce | Valore |
|---|---|
| branch | `main` |
| HEAD | `f38ebea docs(I1): close procedure and equivalence compartment` |
| `origin/main` | `54445af` |
| commit avanti | 72 |
| working tree tracciato | pulito |
| non tracciati | solo `Articolo.pdf` e `LIBRO_MAIN.pdf` |
| `pytest tests/test_baseline_matematica.py` | **25 passed** |

I test pertinenti eseguiti in questa fase sono riportati al § 22.

## 2. Fonti consultate

**Documenti del repository** (FONTE):

* `V4_MATHEMATICAL_DIDACTIC_COVERAGE_AUDIT.md`: § 10 (base 3), § 16 (collegamenti), § 21 (DP1–DP12), § 22.2 e
  § 22.3 (compartimenti), § 14.3 (catalogo E1–E6);
* righe della matrice: L05, L06, L07, L08, L09, L10, L18, L21, L35, L36, L38, L39, L41, L42 e L58, più L60 e A02,
  emerse come direttamente necessarie;
* `V4_PRE_I1_PRODUCT_DECISIONS.md`;
* `I1_PROCEDURE_EQUIVALENCES_CLOSED.md`.

**Libro** (FONTE; pagina stampata = pagina PDF − 28):

| Sezione | Pagine | Contenuto |
|---|---|---|
| § 1.5.2 | p. 21 | indirizzo ternario, 19 = (2,0,1) ↔ DSC |
| § 1.6 | pp. 22–27 | la macchina che dimentica |
| § 1.7 | — | registro a scorrimento `(n2,n1,n0) → (s0,n2,n1) → (s1,s0,n2) → (s2,s1,s0)` |
| § 1.8 | — | codifica ω, Oss. 1.4 (indirizzo contro sequenza operativa), SCD = 5, DSC = 19, CDS = 15 |
| § 1.9 | — | Prop. 1.6, storia delle distribuzioni = rev ω(n), storia delle raccolte → indirizzo finale |
| § 2.4.1–2.4.5 | — | tabellone con l'ultimo in alto, colonne-Assi, lettura gerarchica, Prima Crisi, #56 e #62 |
| § 2.4.7 | — | Prop. 2.28, tre leggi delle posizioni |
| § 2.5 | — | rovesciamento |
| § 4.9.1 | — | tabella n → Π(n) → n' |
| § 4.10 e 4.10.1 | — | tabellone inverso nello stesso ordine temporale; esempio 10 → 24 → 10 |
| § 5.1.5 | p. 117 | flusso delle coordinate con R^ε, MSC, P |
| § 5.1.6 | — | tabellone inverso |
| § 7.1.2 | pp. 179–185 | A2 Leggere e invertire, «contachilometri», caso #91, operazioni (E), (R), (I) |

**Codice** (CODICE):

* core: `gioco_reale.py` (`digits3`, `MESCOLAMENTO`, `IMPILAMENTO_DI`, `T_da_tabellone`, `T_da_partita`,
  `esegui_partita`, `tabellone_da_assi`, `riga_tavola`, `tavola_216`), `detail.py` (`num_to_sector`),
  `permutations.py` (`compute_T_perm`, `make_csv_row`), `algebra.py` (`Controller`, `_prep_explorer_expr`);
* services: `services/procedure.py` (I1);
* GUI: `tavola_tab.py`, `explorer_tab.py`, `simulator_tab.py`, `cycles_tab.py`, `app.py` (`_notify_T_changed`,
  `_seleziona_scheda`, `_wrap_tab`, `_apply_livello`), `scorrimento.py` (`AreaScorrevole`), `glossary.py`
  (`TAB_HELP`).

**Test** (TEST): `test_layout_accessibilita_h2.py`, `test_guida_allineata.py`, `test_servizi_g1.py`,
`test_static.py`, `test_tabellone_inverso.py`, `test_gioco_reale.py`, i test di I1.

L'`Articolo.pdf` non è pertinente per I2: vi comparirebbe solo la regola dello stadio (A02), già coperta dal libro.

---

## 3. Discrepanza I2/I3 e raccomandazione

### 3.1 Che cosa dicono i documenti

**FONTE, audit § 22.3.**

* **I2 — Tabellone e livello ternario (viste).** Comprende:
  * griglia 3×3 diretta e inversa, lettura gerarchica, colonne-Assi;
  * convertitore numero ↔ terna ↔ parola;
  * macchina che dimentica e flusso delle cifre «anche per lo stadio con rovesciamento, § 5.1.5»;
  * rev ω(n); tabella n → Π(n) → n';
  * (R) e procedura di ritorno;
  * navigazione Tavola ↔ Explorer ↔ Simulatore ↔ Cicli.

  *Non comprende* errori né spettatore.
* **I3 — Traccia fisica, errori e recupero.** Comprende:
  * catalogo E1–E6 e «l'errore accade»;
  * confronto piano/eseguito;
  * **rovesciamenti nelle viste fisiche**;
  * recupero.

**FONTE, `I1_PROCEDURE_EQUIVALENCES_CLOSED.md` § 10.**

* Debito 1: il «rovesciamento finale» «Servirà in **I2** per l'errore E2 alla fase 3».
* Debito 5: prompt fisico «capovolgi, poi distribuisci» e `adattamento_fisico` nel Simulatore «appartengono a
  **I2**».

### 3.2 Come si è prodotta la discrepanza (INFERENZA sui testi)

Il memo pre-I1 ha usato «I2» come abbreviazione di «Simulatore con rovesciamenti», in quattro punti:

* riga 232, criterio «Semplicità I1/I2/I3»: «I2 (Simulatore) con un adattatore banale verso l'oracolo fisico»;
* riga 588: «finché Simulatore e Pratica non supportano i rovesciamenti (I2)»;
* riga 692: «formulazione esatta del prompt fisico in I2»;
* riga 701: «quando I2 li supporterà».

Nello stesso criterio attribuisce a «I3» l'inversione (Cor. 5.2), che nell'audit non è un compartimento. Lo
slittamento viene dall'audit stesso: § 21 DP3 elenca fra i punti d'impatto «Simulatore con rovesciamenti, errori
E2, Tavola estesa» senza assegnarli a un compartimento. Il memo pre-I1 ha poi scelto «I2» come etichetta del
Simulatore esteso, e la chiusura di I1 ha ereditato l'etichetta nei debiti 1 e 5.

**Nessun documento ha ridefinito formalmente i compartimenti**: la definizione autorevole resta quella del § 22.3
dell'audit.

### 3.3 Raccomandazione (RACCOMANDAZIONE)

Il perimetro dell'audit resta invariato. Si registra che le etichette «I2» del memo pre-I1 (righe 232, 588, 692,
701) e dei debiti 1 e 5 di I1 § 10 vanno lette come **I3** (viste fisiche, errori, recupero).

| Compartimento | Contenuto |
|---|---|
| **I2** | tabellone + base 3 + collegamenti fra rappresentazioni (viste di lettura) |
| **I3** | errori fisici E1–E6, «l'errore accade», rovesciamento finale T' = J∘T come E2 alla fase 3, confronto piano/eseguito, recupero, Pratica divergente, prompt fisico del rovesciamento nel Simulatore/Pratica |

Il flusso delle cifre di uno stadio con rovesciamento **canonico** (DP3 = A) resta in I2 per il § 22.3: è una
visualizzazione della legge, non un errore. I documenti precedenti **non** vengono corretti retroattivamente;
questa nota è la traccia della riconciliazione.

## 4. Perimetro I2

**Dentro** (RACCOMANDAZIONE, conforme all'audit § 22.3):

1. convertitore n ↔ (n2,n1,n0) ↔ parola {S,C,D}³;
2. tabellone 3×3 diretto e inverso, con striscia cronologica, colonne-Assi e lettura gerarchica («contachilometri»);
3. lettura cifra per cifra di una posizione collegata alla griglia;
4. macchina che dimentica e flusso delle cifre, anche con rovesciamenti **canonici** (ε, DP3 = A);
5. storia delle distribuzioni = rev ω(n) (e la sua forma corretta con ε ≠ 0) distinta dalla storia delle raccolte;
6. tabella n → Π(n) → n' delle 27 posizioni;
7. operazione (R) «realizza questo tabellone» e procedura di ritorno, tramite I1;
8. navigazione minima Tavola ↔ Explorer, Simulatore → Tavola, Tavola ↔ Cicli.

**Fuori**: § 18.

## 5. Gap dell'audit coperti da I2

| Riga | Gap dell'audit (FONTE) | Copertura in I2 (RACCOMANDAZIONE) |
|---|---|---|
| L05 | nessun convertitore interattivo numero ↔ terna ↔ parola | convertitore (§ 8) |
| L06 | nessuna vista gerarchica delle posizioni | lettura gerarchica nella griglia e nella tabella delle 27 posizioni |
| L07 | parola SCD solo nel PDF | parola nel convertitore e in ogni riga della tabella |
| L08 | ricorrenza non mostrata passo per passo | macchina che dimentica (§ 9) |
| L09 | flusso delle cifre assente | registro a scorrimento (§ 9) |
| L10 | non si dice che le colonne sono n0, n1, n2 | storia delle distribuzioni (§ 9.4) |
| L18 | nessuna vista 3×3 del tabellone né lettura «contachilometri» | tabellone diretto e inverso (§ 10) |
| L21 | nessuna lettura cifra per cifra | lettura cifra per cifra (§ 10.4) |
| L35 | nessuna tabella ternaria posizione per posizione | tabella n → Π(n) → n' (§ 11) |
| L36 | ritorno come tre raccolte non offerto | procedura di ritorno (§ 13) |
| L38 | parità dei rovesciamenti non esposta | **parziale**: il flusso con ε mostra il complemento; la regola di parità in M2 come enunciato resta per I6/I7 |
| L39 | diagramma di flusso dello stadio assente | flusso dello stadio R^ε → MSC → P (§ 9.3) |
| L41 | — (già COMPLETO) | nessun cambio; la Tavola continua a usare `tabellone_da_assi` |
| L42 | forma µ(n) e L_i∘MSC non mostrate | **parziale**: il registro mostra `(n2,n1,n0) ↦ (·,n2,n1)`; la formula µ è un'etichetta del flusso |
| L58 | (R) e ritorno assenti | (R) e ritorno (§§ 12–13) |
| § 16 | Explorer → Tavola, Tavola isolata, Simulatore → Tavola debole, posizione → parola | navigazione (§ 14) |

## 6. Autorità matematiche esistenti

Ogni calcolo che I2 mostra ha **già** un'autorità: I2 non deve introdurre formule proprie.

| Calcolo mostrato | Autorità (CODICE) | Verifica |
|---|---|---|
| n ↔ (n2,n1,n0) | `gioco_reale.digits3` | V1 |
| n ↔ parola | oggi `detail.num_to_sector` (minuscolo, solo PDF) e la lettera `SIGLE`/`_LETT`; vedi § 8.3 | V2 |
| righe del tabellone | `riga_tavola(n)["mescolamenti"]` (cronologiche) e `MESCOLAMENTO` | V3 |
| tabellone inverso | `IMPILAMENTO_DI` e `riga_tavola(n)["T_inv"]` | V6 |
| T di una riga | `riga_tavola(n)["T"]` = `T_da_tabellone`; oracolo fisico `T_da_partita` | V3, V5 |
| colonne-Assi | `riga_tavola(n)["assi"]` | V4 |
| riga dagli Assi | `tabellone_da_assi` | V7 |
| T di una procedura con ε | `servizio_procedure().trasformazione(p)` (I1 → `compute_T_perm`) | V11 |
| traccia per stadio (posizioni, colonne) | `esegui_partita` tramite `adattamento_fisico` (I1, DP3) | V9, V10, V11 |
| (R) | `servizio_procedure().classe_trasformazione(T)` → unica procedura semplice | V7 |
| ritorno | T⁻¹ da `riga_tavola(n)["T_inv"]` o dall'inversa del core, poi (R) | V8 |
| T → espressione dell'Explorer | `compute_T_perm(params)[1]` + `algebra._prep_explorer_expr`, lo stesso percorso di Analisi e Decomposizioni | ESEC 1728/1728 (§ 16) |
| appartenenza di una T dell'Explorer alle 216 | `classe_trasformazione` (solleva `TrasformazioneFuoriDominio`) | V7 |

**Ricorrenza della macchina che dimentica** (INFERENZA e RACCOMANDAZIONE): `P_{k+1} = ⌊P_k/3⌋ + 9·s_k` non va
**calcolata** da una seconda implementazione.

* La traccia autorevole è la simulazione fisica (`esegui_partita`, via `adattamento_fisico` per ε).
* La vista mostra per ogni stadio: posizione prima, colonna, altezza ⌊Q/3⌋, destinazione `s_k` letta da
  `MESCOLAMENTO`, posizione dopo.
* La formula è un'etichetta verificata dai test contro la traccia (V10, V11), non un motore parallelo.

---

## 7. Decisioni UI da prendere

### 7.1 Dove vive I2: confronto delle alternative (INFERENZA sul codice misurato)

**Misura** (ESEC, applicazione vera sotto xvfb a 1280×720):

* ogni scheda ha **1256 × 489 px** utili;
* la Tavola chiede 911 × 359 px e il suo Treeview occupa 1225 × 318;
* le colonne fisse della Tavola sommano 876 px, quindi **restano circa 380 px** in larghezza.

| Alternativa | Didattica | Duplicazione | Navigazione | 1280×720 | H2 | Testabilità | Rischio di sovraccarico |
|---|---|---|---|---|---|---|---|
| A. Estendere la Tavola con colonne e righe in più | bassa: la griglia 3×3 non sta in una cella | bassa | già lì | la tabella perde colonne | Treeview già accessibile | buona | **alto** |
| B. Sotto-vista «Tabellone/Cifre» legata alla Tavola (pannello a destra) | alta: la riga selezionata alimenta griglia, cifre e flusso | nessuna | naturale (selezione di riga) | circa 380 px, sufficienti per la griglia; stretti per il flusso e la tabella a 27 righe | da costruire (Text/Label, nessun Canvas) | buona | medio |
| C. Nuova scheda autonoma | alta | media: riselezionare la disposizione | un salto di scheda in più | spazio pieno | nuova scheda nel censimento H2 | buona | basso per la Tavola, ma **impone** `TAB_HELP`, banner e sezione di guida (`test_ogni_scheda_ha_un_riferimento_alla_guida`, `test_glossario_tab_help_copre_tutte_le_schede`), cioè lavoro di **I7** e una decisione sui livelli (**DP7**: in quale modalità compare) |
| D. Combinazione minima: la Tavola ospita un **pannello ternario riusabile** (frame puro, alimentato da un presenter senza Tk) con tre schede interne | come B | nessuna: lo stesso frame può essere istanziato altrove in futuro | come B | pannello ridimensionabile (`ttk.Panedwindow` orizzontale) con tre schede interne | una sola alternativa testuale per ogni componente | presenter testabile senza Tk; frame testabile con xvfb | medio-basso |

**RACCOMANDAZIONE: D.**

* Il `Treeview` resta com'è a sinistra.
* A destra c'è un pannello ternario ridimensionabile con tre schede interne:
  1. **Tabellone**: striscia cronologica, griglia diretta e inversa, colonne-Assi, (R) e ritorno;
  2. **Una carta**: convertitore, lettura cifra per cifra, macchina che dimentica e storia delle distribuzioni;
  3. **27 posizioni**: la tabella n → Π(n) → n'.
* Motivi:
  * non tocca schede, livelli o guida;
  * la Tavola è già visibile in Principiante, e l'audit colloca tabellone e cifre al livello Base (§ 22.1);
  * non aggiunge Canvas;
  * riusa `AreaScorrevole`, già attorno alla scheda.
* Nessun sotto-tab viene aggiunto all'Explorer, perché `test_numero_di_sottotab_explorer` imporrebbe una modifica
  della guida (I7).

### 7.2 Nomi e terminologia (vincoli DP2 e DP8)

* Termini ammessi, del libro ma non narrativi e già in uso nel programma: «tabellone», «tabellone inverso»,
  «mescolamento», «impilamento», «Assi», «indirizzo», «parola», «cifre».
* Nessun nuovo testo con «Seldon», «Giullare», «Cronaca», «Gaia», né con i nomi dei gruppi (G/H/Γ).
* La distinzione diretto/inverso va detta in modo neutro: «mescolamento ≠ impilamento solo per CDS ↔ DSC».
* L'avviso esistente del Simulatore con «Prima Crisi di Seldon» resta com'è (non si tocca).

### 7.3 Chiavi i18n

I2 aggiungerà etichette. **RACCOMANDAZIONE**:

* chiavi nuove solo nel catalogo `i18n.py`, simmetriche IT/EN (contratto H1);
* nessuna modifica a guida, glossario, `TAB_HELP` o onboarding.

La descrizione nella guida dei nuovi pannelli è un debito dichiarato per I7. **Richiede approvazione** (§ 21, D-I2-6).

---

## 8. Convertitore ternario

### 8.1 Contratto (FONTE, § 1.8.1 e Oss. 1.4)

* **Ordine delle cifre mostrato**: `(n2, n1, n0)`, cifra più significativa a sinistra, con i pesi 9, 3, 1 scritti
  sotto.
* **Parola**: `ω(n) = λ(n2) λ(n1) λ(n0)`, nello stesso ordine; λ(0) = S, λ(1) = C, λ(2) = D.
* **Inversa**: `ω⁻¹(abc) = 9ν(a) + 3ν(b) + ν(c)`.
* **Base 0**: posizioni 0..26. Il programma usa già la base 0 («posizioni 0–26, dal dorso»); l'eventuale
  «n-esima carta = posizione n−1» non va introdotto qui (L03, fuori perimetro).
* **Ordine**: l'ordine numerico coincide con l'ordine lessicografico con S < C < D (ESEC 27/27; attenzione: **non**
  con l'ordine alfabetico, dove C < D < S).

### 8.2 Esempi fissi (FONTE ed ESEC)

| n | terna | parola | fonte |
|---|---|---|---|
| 0 | (0,0,0) | SSS | § 1.8.2 |
| 13 | (1,1,1) | CCC | § 1.8.2 |
| 26 | (2,2,2) | DDD | § 1.8.2 |
| **19** | **(2,0,1)** | **DSC** | § 1.5.2 e § 1.8.2 |
| 5 | (0,1,2) | SCD | § 1.8.3 |
| 15 | (1,2,0) | CDS | § 1.8.3 |

### 8.3 Autorità unica

**Stato** (CODICE):

* le cifre hanno una sola autorità, `gioco_reale.digits3`;
* la parola esiste solo come `detail.num_to_sector` (minuscolo, per il PDF).

ESEC: `num_to_sector(n).upper()` coincide con la parola costruita da `digits3` in 27/27.

**RACCOMANDAZIONE (I2a)**:

* una sola funzione pubblica nel core `gioco_reale` (per esempio `parola(n)` e la sua inversa), costruita **sopra**
  `digits3` e l'alfabeto S, C, D già usato da `_LETT`;
* `detail.num_to_sector` delega a essa, con uscita identica (minuscolo, verificato 27/27 e dai test di export);
* **divieto** di un terzo convertitore nella GUI o nel presenter.

**Ambiguità da rendere impossibile**:

* «DSC» come **indirizzo** (posizione 19: blocco D, terzina S, posto C) e «DSC» come **mescolamento** (la
  permutazione `(2,0,1)` di S3) sono due oggetti diversi con lo stesso alfabeto (FONTE: Oss. 1.4 e § 1.8.2, «La
  parola DSC non registra tre eventi successivi»);
* la vista etichetta sempre il ruolo, «indirizzo» o «mescolamento»;
* nel convertitore compare solo la parola-indirizzo.

## 9. Macchina che dimentica e flusso delle cifre

### 9.1 Contratto (FONTE, § 1.6 e § 1.7)

```
P_{k+1} = ⌊P_k / 3⌋ + 9·s_k            s_k = S_{k+1}(P_k mod 3)    (valore di MESCOLAMENTO)
(n2,n1,n0) → (s0,n2,n1) → (s1,s0,n2) → (s2,s1,s0)      P3 = 9·s2 + 3·s1 + s0
```

### 9.2 Forma della vista (RACCOMANDAZIONE)

* È parte della scheda interna **«Una carta»** del pannello ternario, non una vista autonoma. Condivide la carta
  selezionata con convertitore e lettura cifra per cifra.
* **Controlli**:
  * carta (0..26, spinbox);
  * disposizione (dalla riga selezionata della Tavola);
  * tre caselle ε1, ε2, ε3 per il flusso canonico (§ 9.3, **soggette a D-I2-5**);
  * «◀ passo», «passo ▶», «inizio»;
  * nessuna animazione temporizzata obbligatoria.
* **Rappresentazione a registro**: tre caselle, sempre con i pesi 9, 3, 1.
  * La cifra che **esce** è indicata con «← esce n0» (simbolo e parola, non solo colore).
  * La cifra che **entra** è indicata con «entra s0 →».
  * Accanto compaiono P_k, la colonna osservata, l'altezza ⌊P_k/3⌋ e la destinazione s_k del mazzetto.
* **Alternativa testuale** (H2): un `Text` di sola lettura, raggiungibile con Tab, con **tutti** i passi scritti,
  per esempio «Fase 1: P0 = 19 = (2,0,1); colonna 1 (C); altezza 6; mescolamento CDS manda C in 2; P1 = 24 =
  (2,2,0); esce 1, entra 2». Il testo è sempre presente, non solo a richiesta; il pannello grafico ne è una resa
  equivalente.
* **Senza animazione e con ridimensionamento**:
  * lo stato è discreto (passo 0..3), quindi il resize ridisegna solo il layout;
  * un eventuale «▶ riproduci» è facoltativo, usa `after` annullabile, si ferma su qualunque input e non è mai
    l'unico modo per avanzare.

### 9.3 Flusso con rovesciamento canonico (DP3 = A)

**FONTE, § 5.1.5**: `R^ε ⊗ R^ε ⊗ R^ε` agisce sulle tre cifre senza spostarle, poi MSC le ruota, poi P agisce sulla
prima.

**Per la carta, uno stadio con ε = 1 è**: complemento `d ↦ 2 − d` sulle tre cifre, poi il passo ordinario
`Q = 26 − P`, `P' = ⌊Q/3⌋ + 9·S(Q mod 3)`.

* **Modello**: la sola `ProceduraGioco` di I1 (ε prima della distribuzione).
* **Traccia**: `esegui_partita` tramite `adattamento_fisico`, cioè un oracolo, non un secondo modello:
  * carta equivalente `26 − c` se ε1;
  * posizione registrata complementata se ε dello stadio successivo.
* **Divieti**: nessuna `ProceduraB`, nessun «dopo la raccolta» come modello, nessun rovesciamento finale, nessun
  cambio di `R[m]`.

ESEC V11: posizioni finali, intermedie e colonne osservate coincidono con il core e con l'oracolo su tutte le 1728
procedure × 27 carte.

### 9.4 Storia delle distribuzioni contro storia delle raccolte

**FONTE, Prop. 1.6**: le colonne osservate sono `(n0, n1, n2) = rev ω(n)`, indipendenti dalle raccolte. La storia
delle raccolte `(s0, s1, s2)` scrive l'indirizzo finale `(s2, s1, s0)`.

ESEC:

* **senza rovesciamenti** vale su 216 × 27 = **5832/5832**;
* **con ε canonico non vale letteralmente**: vale in 13824/46656 casi;
* la forma corretta, verificata **46656/46656**, è: la colonna della distribuzione k è `n_k` complementata se la
  parità di ε1 + … + ε_{k+1} è dispari.

**RACCOMANDAZIONE**:

* la vista mostra due righe separate, «distribuzioni (lette nel tempo)» e «raccolte (scrivono l'indirizzo)»;
* con ε ≠ 0 la riga delle distribuzioni mostra la complementazione e dichiara che rev ω(n) vale per ε = 0.

Questa è una conseguenza della legge, non un errore: non entra in I3.

---

## 10. Tabellone diretto e inverso

### 10.1 Fatti (FONTE, § 2.4.1, § 2.4.5, § 2.4.7, § 4.10, § 7.1.2)

* **Righe**: mescolamenti (sigle funzionali), con l'**ultimo in alto**.
  * Riga superiore = fase 3 = peso 9 = cifra n2.
  * Riga centrale = fase 2 = peso 3 = n1.
  * Riga inferiore = fase 1 = peso 1 = n0.
* **Colonne**: la colonna d letta dall'alto è `T(d,d,d)`, cioè le posizioni finali di A♠ (0), A♣ (13) e A♥ (26).
* **Lettura gerarchica**, riga alta più lenta: produce le 27 terne in ordine, cioè la lista **T[0], T[1], …,
  T[26]** delle destinazioni.
* **Tabellone inverso**: le stesse righe **nello stesso ordine** con ogni sigla sostituita dalla sua inversa (CDS
  ↔ DSC), cioè le righe degli impilamenti. Le sue colonne dicono **quale carta** arriva in 0, 13, 26.

### 10.2 Una tensione nella fonte, registrata e non corretta

Il libro (§ 2.4.4 e § 2.4.5) chiama «configurazione finale» sia la lista prodotta dalla lettura gerarchica sia il
mazzo finale.

ESEC:

* la lettura gerarchica del tabellone **diretto** dà `T` (destinazioni);
* il **mazzo** finale (carta in posizione q) è `T⁻¹`, cioè la lettura del tabellone **inverso**;
* le due coincidono solo quando T è auto-inversa (64/216 righe): è il caso di #78 al § 2.4.4;
* il vettore stampato al § 2.4.5 per l'esecuzione corretta di #56 («4 3 5 7 6 8 1 0 2 …») è il **mazzo**, mentre
  quello dell'esecuzione ingenua («7 6 8 1 0 2 4 3 5 …») è `T` di #56 (= mazzo di #62).

La fonte è coerente se letta con la distinzione del § 2.4.5. **RACCOMANDAZIONE**: la UI nomina sempre le due
letture:

* «destinazione di ogni carta (T)» sul diretto;
* «carta in ogni posizione (mazzo finale, T⁻¹)» sull'inverso.

### 10.3 Cronologia contro ordine visivo

**Problema** (CODICE):

* la colonna «Mescolamenti» della Tavola elenca S1 S2 S3 in ordine cronologico;
* il dettaglio (doppio clic) scrive «Tabellone (dal basso verso l'alto): riga 1: S1 …»;
* l'espressione dell'Explorer scrive `S3 … o MSC o S2 … o MSC o S1 …` (composizione, ultimo a sinistra).

Sono tre ordini in tre punti.

| Soluzione | Pro | Contro |
|---|---|---|
| 1. Solo griglia 3×3 con S3 in alto | fedele al libro | chi viene dalla colonna «Mescolamenti» legge S1 S2 S3 e vede S3 in alto: facile invertire |
| 2. Solo striscia cronologica | coerente con la Tavola | perde la lettura per colonne e per livelli: il tabellone non c'è |
| **3. Entrambe, collegate** | ogni riga visiva porta l'etichetta «fase k · peso · cifra»; la striscia porta «fase 1 → fase 2 → fase 3»; stessa evidenziazione sui due lati | occupa un po' più di spazio (circa 60 px) |

**RACCOMANDAZIONE: soluzione 3.**

* **In alto**: la striscia cronologica «fase 1: S1 (impila I1) → fase 2: S2 (impila I2) → fase 3: S3 (impila
  I3)».
* **Sotto**: la griglia diretta con righe etichettate:
  * «fase 3 · ×9 · n2» in alto;
  * «fase 2 · ×3 · n1» al centro;
  * «fase 1 · ×1 · n0» in basso.
* Le colonne portano l'intestazione «0/S 1/C 2/D» e il piede «A♠→T(0), A♣→T(13), A♥→T(26)».
* Selezionando una fase nella striscia si evidenzia la riga corrispondente della griglia, e viceversa, con un
  marcatore testuale «▶», non solo con il colore.
* Accanto c'è l'inverso con la stessa impaginazione e l'etichetta «impilamenti (= inverso)».

Il dettaglio esistente (Toplevel) **non** va modificato in I2 (compatibilità): è un debito di terminologia per I7.

### 10.4 Lettura cifra per cifra collegata alla griglia

Per la carta n = (n2,n1,n0) selezionata:

* la griglia marca con «▶» la cella (riga fase 3, colonna n2), la cella (fase 2, n1) e la cella (fase 1, n0);
* sotto compare, come testo, `T(n2,n1,n0) = (B3(n2), B2(n1), B1(n0)) = (…)₃ = n'`, con B_k la riga della fase k.

Non è una formula isolata: le tre celle marcate **sono** i tre fattori. Esempio fisso (FONTE, § 7.1.2): per #100,
`10 = (1,0,1)` porta a `(0,1,2) = 5`.

---

## 11. Tabella n → Π(n) → n'

**FONTE, § 4.9.1**: 27 righe con n, terna iniziale, «000 ↦ 210», n'; ESEC su #193 (SDC, CSD, DCS), dove n = 1 dà
23 e la sequenza completa coincide.

**Contratto (RACCOMANDAZIONE)**, colonne sempre visibili:

* n;
* terna (n2 n1 n0);
* parola ω(n);
* terna finale (b2 b1 b0);
* parola finale;
* n'.

**Su selezione di una riga**: l'azione locale per cifra («fase 3: n2 = 1 ↦ 2; fase 2: n1 = 0 ↦ 1; fase 1: n0 = 1
↦ 2») e le celle marcate nella griglia (§ 10.4), cioè lo stesso stato della scheda «Una carta».

**Layout**: un `Treeview` di 27 righe con barra propria, dentro la scheda interna. A 1280×720 l'altezza utile è
circa 380 px, quindi scorre, e questo è accettato da H2 purché si raggiunga. La larghezza è di circa 360 px con
colonne strette. Le righe sono raggruppate visivamente per n2 (tre blocchi da 9) con un separatore testuale, non
solo con il colore.

**Alternativa testuale**: il `Treeview` è già testo ed è raggiungibile con Tab. Il riepilogo della riga selezionata
va in un'etichetta leggibile.

## 12. Operazione (R) «realizza questo tabellone»

**Definizione (RACCOMANDAZIONE, nessun nuovo solutore)**:

```
T  →  servizio_procedure().classe_trasformazione(T)     (8 procedure, I1)
   →  l'unica p con p.semplice                           (esattamente una: I1-G9)
   →  p.mescolamenti (S1,S2,S3), p.impilamenti, p.numero_tavola
```

ESEC **V7**, 216/216:

* la procedura semplice ottenuta ha gli stessi mescolamenti di `riga_tavola(n)`;
* realizza T fisicamente (`T_da_partita`);
* coincide con `tabellone_da_assi(assi)`.

**FONTE, § 7.1.2 (R)**: «si cerca nella tavola la riga che produce T, se ne leggono i tre mescolamenti … e li si
esegue con (E)».

**Uso**:

* per le righe della Tavola, (R) è l'identità, perché la riga è già la procedura: serve per le T che arrivano da
  **altrove** (Explorer, Cicli, procedure con ε);
* se `TrasformazioneFuoriDominio`, l'azione è disabilitata con il motivo scritto («T non è una disposizione della
  Tavola»).

**Divieti**: niente `procedura_sicura`, niente `risolvi_trucco` (che risolve carta → bersaglio, non T), nessuna
strategia nuova.

## 13. Procedura di ritorno

**Definizione (RACCOMANDAZIONE)**:

```
T  →  T⁻¹ (riga_tavola(n)["T_inv"], o l'inversa già esposta dal core)  →  (R) su T⁻¹
```

Nessuna inversione reimplementata. ESEC **V8**, 216/216:

* la procedura ottenuta realizza T⁻¹ (`T_da_partita`);
* `T⁻¹∘T = id` e `T∘T⁻¹ = id`;
* i suoi **mescolamenti sono esattamente gli impilamenti della riga originale**, nello stesso ordine cronologico
  (216/216). È la «scorciatoia per il ritorno» del libro (FONTE, § 7.1.2 (R): «per realizzare T⁻¹ si impilano
  proprio le righe di T … senza alcuno scambio») e la cascata di inverse locali nello stesso ordine temporale
  (§ 4.10).

**Trappola da rendere visibile** (ESEC):

* invertire soltanto l'**ordine testuale** (S3, S2, S1) realizza T⁻¹ solo in **24/216** righe;
* invertire l'ordine **e** le sigle realizza T⁻¹ in **36/216**;
* la regola giusta è: stesso ordine, sigle inverse.

**RACCOMANDAZIONE per la vista**:

* «Ritorno» mostra la procedura (fase 1..3, mescolamenti e impilamenti) e il suo numero #;
* offre «vai alla riga #k», e nella Tavola la riga del ritorno viene evidenziata;
* una riga di testo dichiara «stesso ordine delle fasi; ogni sigla sostituita dalla sua inversa (CDS ↔ DSC)».

Esempi fissi (ESEC e FONTE):

| Riga | Ritorno | Fonte |
|---|---|---|
| #100 (CDS,CDS,CSD) | #93 (DSC,DSC,CSD) | § 7.1.2; 10 → 5, T⁻¹(10) = 6 |
| #56 | #62 | § 2.4.5, nota App. C |
| #177 (DSC,DCS,CDS) | #142 (CDS,DCS,DSC) | § 4.10.1, 10 → 24 → 10 |
| #91 | #97 | § 7.1.2 |
| #78, #193, #0 | sé stesse (auto-inverse) | — |

## 14. Navigazione

**Meccanismi esistenti** (CODICE):

* `App._notify_T_changed(perm)` aggiorna Cicli e Presentazione e memorizza `_last_T_perm` (Protocollo). Oggi la
  chiamano Explorer, Anteprima e Simulatore; **non** la Tavola.
* `App._seleziona_scheda(chiave)` porta una scheda in primo piano per chiave stabile (H1).
* Verso l'Explorer si inserisce un'espressione in `_explorer_entry`, si seleziona la scheda e si calcola. È il
  pattern già usato da Analisi e Decomposizioni.
* Explorer e Cicli sono **nascosti in Principiante** (`_advanced_tabs`).

**Insieme minimo di azioni (RACCOMANDAZIONE)**:

| Da | A | Azione | Meccanismo | Condizione |
|---|---|---|---|---|
| Tavola (riga) | Explorer | «Apri nell'Explorer» | espressione da `compute_T_perm(params)[1]` + `_prep_explorer_expr`; ESEC: ritorno alla stessa T in **1728/1728** procedure | solo in modalità Esperto |
| Explorer | Tavola | «Mostra nella Tavola» | `classe_trasformazione(T)` → (R) → selezione ed evidenza della riga | abilitata solo se T è fra le 216; altrimenti il motivo è scritto |
| Tavola (riga) | Cicli (e Presentazione e Protocollo) | «Usa come T corrente» | `_notify_T_changed(T)`; poi, in Esperto, «Apri nei Cicli» | esplicita, **non** a ogni selezione: la sola selezione non deve cambiare lo stato di altre viste |
| Cicli | Tavola | «Mostra nella Tavola» | come da Explorer | T fra le 216 |
| Simulatore | Tavola | «Mostra la disposizione #n nella Tavola» | `plan["numero"]` già calcolato | sempre |

**Cicli bidirezionali ottenuti**: Tavola ↔ Explorer; Tavola ↔ Cicli; Simulatore → Tavola. Explorer ↔ Cicli
esiste già.

**Tavola → Simulatore non è proposto** (INFERENZA): il Simulatore risolve una coppia carta → bersaglio con
`risolvi_trucco`, e una riga della Tavola non è una coppia. Per ogni carta c il piano storico di (c, T[c]) è
spesso un'altra riga, perché la fibra ha 8 procedure semplici. Una «pratica di questa disposizione» richiederebbe
un Simulatore guidato da un piano fissato: è materia di I3/Pratica, non di I2.

**Principiante**: le azioni verso schede nascoste non compaiono, e nessun cambio di livello viene introdotto (DP7
non toccata).

## 15. H2 e layout

**Pattern esistenti da riusare** (CODICE e TEST):

* `AreaScorrevole` attorno a ogni scheda;
* alternative testuali come `Text` di sola lettura con `takefocus`, secondo il modello di
  `ExplorerTabMixin._matrice_in_testo` e di `DistributionFrame.istogramma_in_testo`;
* censimento dei Canvas (`CANVAS` in H2);
* «il colore non è l'unico portatore» (`test_il_colore_non_e_l_unico_portatore_di_informazione`);
* raggiungibilità a 1280×720 (`test_m04_il_contenuto_delle_schede_e_raggiungibile`, oggi parametrizzato su
  simulatore ed explorer).

**Contratto H2 per I2 (RACCOMANDAZIONE)**:

| Elemento | Resa | Alternativa testuale equivalente |
|---|---|---|
| tabellone 3×3 diretto e inverso | griglia di `ttk.Label` (non Canvas) | funzione pura che restituisce il testo completo (righe con fase, peso, cifra; colonne-Assi; lettura), mostrata in un `Text` raggiungibile con Tab |
| flusso delle cifre / macchina | registro di etichette | log completo dei passi (§ 9.2), sempre visibile |
| eventuale animazione | facoltativa, annullabile | il log e i pulsanti passo-passo: nessuna informazione solo animata |
| tabella a 27 righe | `Treeview` | è testo; riepilogo della riga selezionata in un'etichetta |
| stato selezionato | marcatore «▶» + evidenziazione | etichetta «selezionata: carta n, fase k» |

**Gate specifici per I2** (da scrivere prima del codice):

* a 1280×720, 1366×768 e 1920×1080 nessun controllo del pannello resta fuori portata (estendere la
  parametrizzazione a `"tavola"`);
* le barre compaiono solo quando servono;
* resize del `Panedwindow` senza cicli di layout;
* ogni nuovo controllo prende il focus con Tab e l'ordine di Tab segue l'ordine visivo;
* ogni alternativa testuale è presente nella vista, di sola lettura e raggiungibile;
* nessun nuovo Canvas; se ne servisse uno, va censito in `CANVAS` come «informativo» con la sua alternativa;
* layout in inglese (`test_il_layout_regge_anche_in_inglese`).

**Baseline nota**: `test_lo_scorrimento_si_accende_quando_il_testo_cresce` fallisce con Tk 9.0.4 (metriche dei
font) e passa nell'ambiente H2 di riferimento (Tk 8.6). **Non si corregge.** I2 è accettabile solo se questo resta
l'**unico** fallimento.

---

## 16. Verifiche V1–V11

Tutte ESEC con Python inline, senza file creati.

| # | Verifica | Oracolo indipendente | Esito |
|---|---|---|---|
| V1 | n ↔ `digits3` ↔ n | `9a + 3b + c` | **27/27** |
| V2 | n ↔ parola ↔ n; parola = `num_to_sector(n).upper()`; ordine lessicografico con S < C < D; 19 → DSC, (2,0,1) | `ω⁻¹` del libro | **27/27** |
| V3 | lettura gerarchica del tabellone (righe S3/S2/S1, riga alta più lenta) = T | `T_da_partita` (simulazione fisica) e `riga_tavola["T"]` | **216/216** |
| V4 | colonne del tabellone = (T[0], T[13], T[26]) = `riga_tavola["assi"]` | simulazione fisica | **216/216** |
| V5 | legge cifra per cifra = T[n] | simulazione fisica | **5832/5832** |
| V6 | tabellone inverso (impilamenti, stesso ordine) → T⁻¹ | inversa per ricerca `T.index` e `riga_tavola["T_inv"]` | **216/216** |
| V7 | (R) via I1: unica procedura semplice della classe = riga, realizza T, = `tabellone_da_assi` | simulazione fisica | **216/216** |
| V8 | ritorno via I1 realizza T⁻¹; `T⁻¹∘T = T∘T⁻¹ = id`; ritorno = impilamenti originali | simulazione fisica | **216/216** (216/216) |
| V8b | trappole: ordine testuale invertito / ordine invertito + sigle inverse realizzano T⁻¹ | idem | 24/216 / 36/216 |
| V9 | storia delle distribuzioni = rev ω(n), per ogni raccolta | colonne della traccia `esegui_partita` | **5832/5832** (216 procedure × 27 carte) |
| V10 | macchina che dimentica: ricorrenza e registro `(n2,n1,n0) → … → (s2,s1,s0)` | posizioni nella traccia `esegui_partita` | **5832/5832** e **5832/5832** |
| V11 | flusso con ε canonico: finale = `servizio.trasformazione` (core); intermedie e colonne = oracolo via `adattamento_fisico` | core e oracolo fisico | **46656/46656**; intermedie **46656/46656**; colonne **139968/139968** |
| V11b | storia con ε: complemento per parità del prefisso di ε / Prop. 1.6 letterale | idem | **46656/46656** / 13824/46656 |
| Nav | espressione dell'Explorer da `compute_T_perm` → `Controller.process` → stessa T | `servizio.trasformazione` | **1728/1728** |

**Dominio di V10** (richiesto): tutte le 216 procedure semplici × 27 carte iniziali × 3 stadi. Per ogni stadio
`s_k = MESCOLAMENTO[S_k][P_k mod 3]` e la posizione dopo la raccolta confrontata con la traccia fisica.

## 17. Casi fissi didattici

Tutti ricavati dalle fonti e ricontrollati in ESEC.

| Caso | Contenuto | Fonte | Uso nei test I2 |
|---|---|---|---|
| F1 | 19 = (2,0,1) = DSC; ω⁻¹(DSC) = 19 | § 1.5.2, § 1.8.2 | convertitore |
| F2 | SCD = 5, DSC = 19, CDS = 15 (stesse lettere, posti diversi) | § 1.8.3 | convertitore; distinzione indirizzo/mescolamento |
| F3 | #78 = (SCD, SDC, CSD), Assi 9, 7, 23; lettura = T = mazzo (auto-inversa) | § 2.4.4 | griglia; mostra che i due vettori coincidono solo qui |
| F4 | #56 = (CSD, DSC, SDC), Assi (7, 18, 14), e #62 = (CSD, CDS, SDC), Assi (4, 24, 11), l'uno inverso dell'altro; mazzo corretto «4 3 5 7 6 8 1 0 2 …» | § 2.4.5, nota App. C | diretto/inverso non auto-inversi; ritorno |
| F5 | #193 = (SDC, CSD, DCS): tabella 27 righe, 1 ↦ 23, sequenza «21 23 22 18 …» | § 4.9.1 | tabella n → Π(n) → n' |
| F6 | #177 = (DSC, DCS, CDS) ↔ #142 = (CDS, DCS, DSC): 10 → 24 → 10 | § 4.10.1 | ritorno, esempio diretto e inverso |
| F7 | #100 = (CDS, CDS, CSD), Assi (13, 8, 18); 10 → 5; T⁻¹(10) = 6; inverso (CSD, DSC, DSC) dall'alto; ritorno #93 | § 7.1.2; ancora del selftest | lettura cifra per cifra; ritorno |
| F8 | #100, carta 19: registro (2,0,1) → (2,2,0) → (1,2,2) → (2,1,2) = 23; colonne osservate 1, 0, 2 = rev(DSC) | ESEC su F7 + § 1.7, Prop. 1.6 | macchina che dimentica; storia delle distribuzioni |
| F9 | #91 = (SDC, DSC, CSD): 0 → 15, 1 → 17, 2 → 16 | § 7.1.2 | lettura «contachilometri» |
| F10 | § 2.5 = (SCD, DCS, SCD) con ε = (0,0,1) (DP3 = A): Assi 20, 13, 6, stessa T di #185 | § 2.5, memo pre-I1 § 3.3 | flusso con rovesciamento canonico; (R) su T con ε |
| F11 | (CSD, CSD, CSD) con ε = (1,0,0) contro ε = (0,1,0): Assi (26,0,13) contro (25,2,12) | memo pre-I1 § 3.3 | discrimina ε1 (mazzo iniziale) da ε2 |
| F12 | #82, Assi (10, 8, 21) | § 5.1.9–11, selftest | ricostruzione dagli Assi (invariata) |
| F13 | #0 identità | — | controllo, **non** unico esempio |

## 18. Fuori perimetro

I2 **non** fa nulla di quanto segue:

* nessuna simulazione degli errori E1–E6, né «l'errore accade», né conseguenze fisiche di un errore;
* nessun rovesciamento finale T' = J∘T, né come errore E2 né come gesto;
* nessun recupero dopo un errore;
* nessuna Pratica fisicamente divergente;
* nessun prompt fisico di rovesciamento nel Simulatore (tutto questo è I3);
* nessuno spettatore adattivo (I4);
* nessuna Tavola 1728 e nessun elenco delle 8 procedure di una riga (DP11 aperta; § 21 D-I2-5);
* nessun cambio del solutore storico `risolvi_trucco`;
* nessuna adozione della `procedura_sicura`;
* nessun cambio a `R[m]`, ai formati, agli export o al dettaglio esistente della Tavola;
* nessuna soluzione implicita della divergenza R[m] / R[k] dell'App. C;
* nessuna rinomina G/H/Γ/G_ext e nessun nuovo lessico narrativo;
* nessuna revisione di guida, glossario, onboarding o livelli (I7);
* nessun undo/redo (J3);
* nessuna generalizzazione a b^k.

---

## 19. Piano di implementazione a sottocompartimenti

Sequenza test-first a minor rischio (RACCOMANDAZIONE). Ogni passo è un commit o una piccola serie di commit
annullabile.

### I2a — Contratto ternario puro e oracoli

* **File**:
  * `gioco27/core/gioco_reale.py`: `parola(n)` e l'inversa sopra `digits3`;
  * `gioco27/core/detail.py`: delega di `num_to_sector`, uscita invariata;
  * `gioco27/services/tabellone.py`, nuovo presenter senza Tk: modelli immutabili `Tabellone` (righe visive,
    striscia, colonne-Assi, inverso, lettura gerarchica), `LetturaCifre(n)`, `TabellaPosizioni` (27 righe),
    `FlussoCarta(procedura, carta)` dalla traccia fisica via `adattamento_fisico`, `realizza(T)` (R) e
    `ritorno(T)` tramite I1; e funzioni `…_in_testo` pure per le alternative H2;
  * `tests/test_tabellone_ternario_i2.py`.
* **Contratti**: §§ 8–13.
* **Test prima**: V1–V11 come test permanenti con oracoli indipendenti; casi F1–F13; trappole V8b (24 e 36);
  presenter senza `tkinter` (processo separato); nessun ciclo; export PDF invariato (test esistenti).
* **Gate**: G-I2a-1…: 27/27, 216/216, 5832, 46656; `services → gui/tkinter = 0`.
* **Dipendenze**: I1.
* **Rollback**: revert dei file nuovi e della delega.

### I2b — Pannello «Tabellone» nella Tavola

* **File**: `gioco27/gui/tavola_tab.py` (`Panedwindow` + pannello), eventuale `gioco27/gui/pannello_ternario.py`,
  chiavi i18n.
* **Contratti**: § 10 (striscia + griglia diretta e inversa, etichette di fase/peso/cifra, colonne-Assi, due
  letture nominate); § 12 e § 13 come azioni del pannello.
* **Test prima**: il pannello mostra per #100, #56, #78 le righe del presenter; l'alternativa testuale è nella
  vista ed è raggiungibile; la selezione di riga aggiorna il pannello; H2 a tre dimensioni; nessun Canvas nuovo;
  la Tavola, il CSV e il dettaglio restano invariati.
* **Dipendenze**: I2a.
* **Rollback**: revert di `tavola_tab.py` e delle chiavi.

### I2c — Scheda «Una carta» e scheda «27 posizioni»

* **Contratti**: convertitore, lettura cifra per cifra collegata alla griglia, macchina che dimentica
  passo-passo, storia delle distribuzioni e delle raccolte, flusso con ε (**se approvato D-I2-5**), tabella n →
  Π(n) → n'.
* **Test prima**:
  * F1, F2, F5, F8, F10;
  * il log testuale contiene tutti i passi;
  * nessuna informazione solo nel colore;
  * «riproduci» (se c'è) si ferma e non è necessario;
  * resize.
* **Dipendenze**: I2a, I2b.
* **Rollback**: revert del frame.

### I2d — Navigazione

* **File**:
  * `tavola_tab.py` («Apri nell'Explorer», «Usa come T corrente», «Apri nei Cicli»);
  * `explorer_tab.py` e `cycles_tab.py` («Mostra nella Tavola»);
  * `simulator_tab.py` («Mostra la disposizione #n»);
  * `app.py` (un solo metodo `_mostra_nella_tavola(numero)` e il cablaggio).
* **Contratti**: § 14; gating per Principiante; nessuna notifica di T alla sola selezione.
* **Test prima**:
  * andata e ritorno Tavola → Explorer → Tavola su #100 e su una T con ε (F10 → #185);
  * T fuori dalle 216: azione disabilitata con motivo;
  * Simulatore (0 → 13) → riga #86;
  * in Principiante le azioni verso schede nascoste non compaiono;
  * Presentazione e Protocollo ricevono T solo con «Usa come T corrente».
* **Dipendenze**: I2a (R); I2b.
* **Rollback**: revert per file.

### I2e — Integrazione H2/layout e chiusura

* **Contenuto**:
  * estensione dei test H2 (tavola a tre dimensioni, focus, ordine di Tab, inglese);
  * suite completa file per file;
  * `I2_BOARD_TERNARY_CLOSED.md`.
* **Gate**: § 20; unico fallimento ammesso quello Tk 9 noto.

La suddivisione proposta dal prompt (I2a…I2f) è stata ridotta a cinque passi: (R) e ritorno sono dati del
presenter (I2a) e azioni del pannello del tabellone (I2b), senza un compartimento a sé.

## 20. Gate PRE-I2

| # | Gate | Esito |
|---|---|---|
| G1 | perimetro I2/I3 riconciliato documentalmente | ✔ § 3 |
| G2 | errori E1–E6 esclusi da I2 | ✔ §§ 3.3, 18 |
| G3 | nessuna DP aperta risolta implicitamente | ✔ § 21.1 |
| G4 | DP3 = A preservata | ✔ § 9.3 |
| G5 | nessun secondo modello del rovesciamento | ✔ § 9.3 |
| G6 | autorità matematica esistente identificata per ogni calcolo | ✔ § 6 |
| G7 | contratto del convertitore ternario definito | ✔ § 8 |
| G8 | contratto della macchina che dimentica definito | ✔ § 9 |
| G9 | contratto del tabellone diretto e inverso definito | ✔ § 10 |
| G10 | ordine cronologico contro ordine visivo non ambiguo | ✔ § 10.3 |
| G11 | contratto n → Π(n) → n' definito | ✔ § 11 |
| G12 | operazione (R) definita senza nuovo solutore | ✔ § 12, V7 |
| G13 | ritorno T⁻¹ definito | ✔ § 13, V8 |
| G14 | strategia storica invariata | ✔ |
| G15 | `procedura_sicura` non adottata implicitamente | ✔ |
| G16 | DP11 non anticipata | ✔ (con la decisione D-I2-5 esplicita) |
| G17 | navigazione minima proposta | ✔ § 14 |
| G18 | H2 definito per ogni nuova visualizzazione | ✔ § 15 |
| G19 | layout 1280×720 considerato (misurato) | ✔ §§ 7.1, 11, 15 |
| G20 | verifiche V1–V11 eseguite | ✔ § 16 |
| G21 | casi fissi tratti dalle fonti | ✔ § 17 |
| G22 | invarianti architetturali preservabili | ✔ § 22 |
| G23 | baseline matematica verde | ✔ 25/25 |
| G24 | il fallimento Tk 9, se presente, resta l'unico noto | ✔ § 22 |
| G25 | nessun codice, test, GUI, i18n o formato modificato in PRE-I2 | ✔ |
| G26 | I2 non implementato | ✔ |
| G27 | I3+ non iniziati | ✔ |
| G28 | PDF non tracciati invariati | ✔ |
| G29 | nessun accesso fuori dal repository | ✔ |
| G30 | nessun push | ✔ |
| G31 | tensione della fonte sulla «configurazione finale» registrata e non corretta | ✔ § 10.2 |
| G32 | la validità ristretta di Prop. 1.6 con ε ≠ 0 registrata come legge, non come errore | ✔ § 9.4 |
| G33 | nessun obbligo di modificare guida o `TAB_HELP` introdotto dalla struttura UI scelta | ✔ § 7.1 (D) |

## 21. Decisioni ancora aperte

### 21.1 DP1–DP12: quali bloccano I2

| DP | Bloccante? | Motivo (FONTE, CODICE, TEST) |
|---|---|---|
| DP1 | **No** | I2 usa i capp. 1, 2, 4, 5, 7 del libro; App. D e articolo servono solo per DP3, già chiusa |
| DP2 | **No**, a patto che I2 non nomini gruppi | «Mostra nella Tavola» usa `classe_trasformazione` senza dire «G»; nessuna etichetta G/H/Γ |
| DP6 | **No** | riguarda I3 |
| DP7 | **No**, con una condizione | I2 non cambia livelli né `_advanced_tabs`. Aggiungere contenuto alla Tavola, già visibile in Principiante, **non** decide DP7; le azioni verso Explorer e Cicli sono mostrate solo in Esperto. Collocare il pannello in Principiante è coerente con l'audit § 22.1 (tabellone e cifre al livello Base), ma **va approvato** (D-I2-2) |
| DP8 | **No** | nessun lessico narrativo nuovo (§ 7.2) |
| DP9 | Non pertinente | — |
| DP10 | Non pertinente | — |
| DP11 | **No**, se il flusso con ε resta una visualizzazione di **una** procedura | elencare le 8 procedure di una riga coincide con un'opzione di DP11 («solo come fibra delle 8 procedure di una riga») e quindi **non** va fatto in I2 (D-I2-5) |
| DP12 | Non pertinente | — |

**Nessuna delle ipotesi del prompt risulta falsa.** DP7 e DP11 hanno però un confine concreto, che si traduce
nelle decisioni D-I2-2 e D-I2-5 qui sotto.

### 21.2 Decisioni di I2 che richiedono approvazione

| # | Decisione | Raccomandazione | Alternative |
|---|---|---|---|
| D-I2-1 | Perimetro I2/I3 | I2 = tabellone + base 3 + collegamenti; I3 = errori, rovesciamento finale, prompt fisico, recupero (§ 3.3) | lasciare in I2 i debiti 1 e 5 di I1 |
| D-I2-2 | Collocazione UI | D: pannello ternario a tre schede interne nella Tavola, visibile anche in Principiante; azioni verso Explorer/Cicli solo in Esperto | A, B, C (§ 7.1) |
| D-I2-3 | Doppia rappresentazione del tabellone | striscia cronologica + griglia con S3 in alto, etichette fase/peso/cifra, inverso affiancato (§ 10.3) | solo griglia; solo cronologia |
| D-I2-4 | Autorità della parola | nuova `gioco_reale.parola(n)` con delega di `num_to_sector` (uscita invariata) (§ 8.3) | usare `num_to_sector(n).upper()` come autorità |
| D-I2-5 | Rovesciamenti canonici nel flusso | tre caselle ε nella scheda «Una carta» per **una** procedura; T risultante mostrata con (R) verso la riga; **nessun** elenco delle 8 procedure della classe | flusso con ε solo da una T arrivata dall'Explorer; rinviare il flusso con ε fino a DP11 |
| D-I2-6 | Testi | nuove chiavi nel solo catalogo i18n (IT/EN simmetriche); guida e glossario come debito I7 | aggiornare subito la guida (anticipa I7) |
| D-I2-7 | Navigazione | insieme minimo del § 14; niente Tavola → Simulatore; notifica di T solo su «Usa come T corrente» | notificare a ogni selezione; aggiungere Tavola → Simulatore con piano fissato (I3) |
| D-I2-8 | Animazione | solo passo-passo; «riproduci» facoltativo e annullabile | nessuna animazione; animazione automatica |

**Blocker reali**: **nessuno** di natura matematica o architetturale. L'unico vincolo pratico è l'approvazione di
D-I2-1…D-I2-8, in particolare D-I2-1 (perimetro), D-I2-2 (collocazione) e D-I2-5 (confine DP11).

## 22. Test e baseline

Stesso ambiente e metodo dell'audit: VM, CPython 3.12.14, Tk 9.0.4, xvfb, un file per volta.

| File | Esito |
|---|---|
| `test_baseline_matematica.py` | 25 passed |
| `test_gioco_reale.py` | 9 passed |
| `test_tabellone_inverso.py` | 20 passed |
| `test_dominio_selftest.py` | 7 passed |
| `test_procedure_i1_caratterizzazione.py` | 18 passed |
| `test_procedure_i1_servizio.py` | 41 passed |
| `test_procedure_i1_strategie.py` | 19 passed |
| `test_layout_accessibilita_h2.py` | 65 passed, **1 failed**: `test_lo_scorrimento_si_accende_quando_il_testo_cresce`, il noto fallimento ambientale Tk 9, unico |
| `test_static.py` (pyflakes) | 2 passed |
| `test_servizi_g1.py` (architettura) | 44 passed |
| `test_guida_allineata.py` | 27 passed |
| `test_i18n.py` | 77 passed |
| `test_presentation_i18n_h1.py` | 65 passed |
| `test_lifecycle_persistenza_g2.py` | 45 passed |
| `test_stato_concorrenza_c.py` | 36 passed |

Nessun file di test riferisce direttamente `TavolaFrame`; i test della Tavola sono quelli i18n, H1 e G2 elencati.
Non ci sono modifiche di codice, quindi la suite completa non è stata rieseguita per intero. Riferimento:
chiusura I1, 1505 passed, 1 skipped, 1 fallimento Tk noto.

**Architettura** (ESEC, analisi AST inline):

| Invariante | Valore |
|---|---|
| core → services | 0 |
| core → gui | 0 |
| services → gui | 0 |
| services → tkinter | 0 |

`test_servizi_g1` verifica anche l'assenza di cicli. Nessun parser nuovo è previsto: l'Explorer resta l'unico
parser, raggiunto con `_prep_explorer_expr`.

## 23. Stato Git

Prima del commit (ESEC):

```
## main...origin/main [ahead 72]
?? Articolo.pdf
?? LIBRO_MAIN.pdf
```

Commit previsto, unico: `docs(v4): analyze pre-I2 board and ternary views`, con il solo file
`V4_PRE_I2_VIEW_DECISIONS.md`.

* I PDF restano non tracciati.
* Nessun push.
* Dopo il commit saranno 73 commit avanti.
