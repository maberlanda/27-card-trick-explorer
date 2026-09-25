# V4 PRE-I5 — Decisioni DP1 e DP10

Documento preparatorio per il compartimento I5 (decodifica e riconoscimento). Analizza **solo** DP1 e DP10 e
formula raccomandazioni, **non** decisioni approvate. Nessun codice, test, guida, i18n o documento precedente è
stato modificato; I5 non è iniziato.

**Etichette**:

| Etichetta | Significato |
|---|---|
| **FONTE** | `LIBRO_MAIN.pdf` o `Articolo.pdf`, letti direttamente |
| **CODICE** | lettura del codice corrente |
| **TEST** | test del repository |
| **ESEC** | esecuzioni inline in questa sessione, senza file persistenti |
| **INFERENZA** | deduzione argomentata |
| **RACCOMANDAZIONE** | proposta da approvare; non è una fonte |

## 1. Stato d'ingresso

ESEC:

| Voce | Valore |
|---|---|
| branch | `main` |
| HEAD | `c30cfd6 test(ui): protect explorer matrix size and content-driven height` |
| `origin/main` | `54445af` |
| ahead | 105 |
| working tree tracciato | pulito |
| non tracciati | `Articolo.pdf`, `LIBRO_MAIN.pdf` (fonti intenzionali) |

## 2. Fonti lette

| Fonte | Parti lette direttamente |
|---|---|
| `Articolo.pdf` | Sommario, § 1; § 4, Def. 4.1, Teor. 4.2, Cor. 4.3; § 5, Teor. 5.1, Cor. 5.2, **Oss. 5.3**; § 6, Es. 6.1; righe sui rovesciamenti («Non sono ammessi rovesciamenti») |
| `LIBRO_MAIN.pdf` | indice delle appendici: **App. D = «Articolo originale – Permutazioni digitalmente separabili»**; App. D § 5.2–5.3 (rovesciamenti, famiglia estesa `⟨H_{b,m}, M_m⟩ ≅ H_{b,m} ⋊ C_m`); App. D § 6: Teor. 6.1, Cor. 6.2, Oss. 6.3, **Teor. 6.4 con dimostrazione**, Oss. 6.5; App. D § 7, tabella C_i ed Es. 7.1; cap. 7 A8 (§ 7.1.8), A13 (§ 7.1.13), B4 (ACAAN col taglio), B7 (limite onesto), C5 (falso taglio), C6 («quando entra qualcosa di estraneo») |
| progetto | `V4_MATHEMATICAL_DIDACTIC_COVERAGE_AUDIT.md` § 2.2, § 18, § 21 (DP1, DP10), piano I5; `I3_PHYSICAL_ERRORS_RECOVERY_CLOSED.md` § 12, § 26; `I4_SPECTATOR_INFORMATION_CLOSED.md` |
| codice | `core/gioco_reale.py`, `core/kronecker.py` (`try_kron_decompose`), `core/algebra.py` (`CanonicalForm`, `msc_exp`), `services/procedure.py` (`classe_trasformazione`), `services/tabellone.py` (`numero_di`, `realizza`), `services/errori.py` (E6) |

## 3. DP1 — fatti verificati

### 3.1 Le due fonti

**Il modello di partenza.**
* FONTE, Articolo § 2: «Non sono ammessi rovesciamenti del mazzo».
* FONTE, App. D § 5: introduce il rovesciamento prima della distribuzione (storie ε, molteplicità 2^m), la formula
  di inversione `Q_i = R^{v_i} ∘ S_i ∘ R^{u_i}` e la famiglia estesa con la rotazione delle cifre M.

**Contenuto comune alle due versioni**, FONTE, stesso testo con numerazione diversa:

| Articolo | App. D | Enunciato essenziale |
|---|---|---|
| Def. 4.1 | Def. 4.1 | π ∈ S_{b^m} è digitalmente separabile se esistono ρ_i ∈ S_b con `d_i(π(x)) = ρ_i(d_i(x))` per ogni x e ogni i |
| Teor. 4.2 | Teor. 4.2 | caratterizzazione intrinseca: codice unico ⇔ `d_i ∘ π` costante sulle fibre ⇔ permutazione dei blocchi ⇔ `P_{m−1} ⊗ … ⊗ P_0` |
| Teor. 5.1 | Teor. 6.1 | per π separabile, `Σ_{i,t}(π) = Σ_{x ∈ F_{i,t}} π(x) = C_i + b^{m−1+i} ρ_i(t)`, con `C_i = b^{m−2}·b(b−1)/2·Σ_{j≠i} b^j` |
| Cor. 5.2 | Cor. 6.2 | **dentro la classe separabile** le Σ determinano π: `ρ_i(t) = (Σ_{i,t} − C_i)/b^{m−1+i}`; mappa iniettiva sulla classe |
| **Oss. 5.3** | — | «La sola compatibilità numerica delle somme con la formula non viene qui assunta come criterio di riconoscimento per una permutazione arbitraria di S_{b^m}» |
| — | Oss. 6.3 | la famiglia delle Σ è sufficiente, non se ne afferma la minimalità |
| — | **Teor. 6.4** | criterio di riconoscimento, § 3.2 |
| — | Oss. 6.5 | le Σ ricostruiscono il codice effettivo, **non** una decomposizione nei blocchi né una storia dei controlli |

### 3.2 Le tre affermazioni

| | Affermazione | Articolo | App. D |
|---|---|---|---|
| **A** | dentro la classe separabile, le Σ ricostruiscono univocamente i ρ_i | ✔ Cor. 5.2 | ✔ Cor. 6.2 |
| **B** | date Σ compatibili (candidati che sono permutazioni), esiste una π separabile con quei fattori | implicita: la costruzione `f(x) = Σ b^i ρ_i(d_i(x))` è Teor. 4.2 + 5.1 | ✔ esplicita nella dimostrazione di 6.4 |
| **C** | per π **arbitraria** in S_{b^m}, il test sulle Σ è **sufficiente** per concludere che π è separabile | **non affermata** (Oss. 5.3 la esclude dalle assunzioni, senza negarla) | ✔ **Teor. 6.4** |

**Teorema 6.4**, FONTE, App. D § 6, in forma essenziale:
* **dominio**: π ∈ S_{b^m} **arbitraria**;
* **candidati**: per ogni i e ogni t ∈ D_b, `ρ̂_i(t) = (Σ_{i,t}(π) − C_i) / b^{m−1+i}`;
* **criterio**: π è separabile ⇔ per ogni livello i, `(ρ̂_i(t))_t` è una permutazione di D_b;
* **ricostruzione**: in tal caso `π(x) = Σ_i b^i ρ̂_i(d_i(x))`.

«Essere una permutazione di D_b» comprende l'**integralità**: i candidati devono essere interi in {0, …, b−1}, tutti
distinti.

**Passaggio della sufficienza**, verificato riga per riga. Ricostruzione con INFERENZA a supporto; il testo è
FONTE:
1. `f(x) = Σ_i b^i ρ̂_i(d_i(x))` è separabile e, per il Teor. 6.1, `Σ_{i,t}(f) = Σ_{i,t}(π)`.
2. `Σ_x π(x) f(x) = Σ_i b^i Σ_t ρ̂_i(t) Σ_{i,t}(π) = Σ_i b^i Σ_t ρ̂_i(t) Σ_{i,t}(f) = Σ_x f(x)²`.
3. π e f permutano lo stesso insieme, quindi `Σ π² = Σ f²`.
4. Da qui `Σ_x (π(x) − f(x))² = 0`, cioè π = f.

Il passaggio è corretto e usa solo l'uguaglianza delle somme, la biiettività di π e la separabilità di f.

**Rovesciamenti.** La differenza «con o senza rovesciamenti» **non tocca** il Teor. 6.4. Il criterio riguarda la
classe delle permutazioni separabili, qualunque storia le abbia prodotte. In App. D § 5 le storie con ε finiscono
nella stessa classe `H_{b,m}`, e I1 lo verifica sul codice (le procedure con rovesciamenti restano fra le 216).
INFERENZA, coerente con FONTE.

### 3.3 Verifica con oracolo indipendente (b = m = 3)

ESEC, script inline, nessun file:
* **oracolo**: Def. 4.1 applicata direttamente (le cifre di π(x) dipendono solo dalle cifre dello stesso livello di
  x);
* **criterio**: Teor. 6.4 in aritmetica razionale esatta (`Fraction`).

| Verifica | Esito |
|---|---|
| `C_0, C_1, C_2` | 108, 90, 36, come nella tabella di App. D § 7 |
| Tavola del programma (216 righe, `riga_tavola`) | 216/216 separabili, criterio vero |
| ρ̂_i ricostruiti = sigle della riga (`MESCOLAMENTO`, B0 = primo mescolamento) | 216/216 |
| classe estesa `{g ∘ M^k}` (M = rotazione delle cifre) | 648 elementi; separabili 216, criterio vero 216, accordo 648/648. Le 432 con k ≠ 0 **non** sono separabili, come in App. D § 5.3 |
| campione casuale S27, seme 2026 | 200 000 permutazioni: 0 separabili, 0 disaccordi |
| negativi mirati: g ∘ trasposizione di due posizioni | 216 × 351 = 75 816 casi, 0 disaccordi |
| negativo con candidati **interi** ma non permutazioni | trovato per ricerca locale: somme tutte 117, candidati (1,1,1) a ogni livello; non separabile, criterio falso. Esercita la clausola «è una permutazione», non basta «è intero» |
| tentativi di ingannare il criterio (π ≠ f con le stesse Σ di una f nella Tavola) | 60 ricerche locali: nessun caso trovato, coerente con la dimostrazione |
| Es. 7.1 di App. D (= Es. 6.1 dell'Articolo), ρ0 = (0 1 2), ρ1 = (0 2), ρ2 = (0 1) | Σ = [[117, 126, 108], [144, 117, 90], [117, 36, 198]]; la riga 0 coincide col testo |
| traslazione `C_1` (x ↦ x+1 mod 27) | candidati [[1, 2, 0], [1/3, 4/3, 4/3], [1/9, 10/9, 16/9]]: il livello 0 «passa», i livelli 1 e 2 no, per effetto dei riporti |

### 3.4 Orientazione delle somme

CODICE e ESEC. Nel programma `T[carta] = posizione finale`, quindi π = T; il mazzo finale è T⁻¹.

| Senso | Oggetto | Somma | Ricostruisce |
|---|---|---|---|
| **avanti** | π = T | per ogni fibra di **posizioni iniziali** `F_{i,t}`, la somma delle **immagini** π(x) | ρ_i, cioè le sigle della riga |
| **indietro** | π⁻¹ = mazzo finale | per ogni fibra di **posizioni finali**, la somma delle **preimmagini** | ρ_i⁻¹ |

ESEC:
* i candidati «indietro» sono gli inversi dei candidati «avanti» in 216/216 righe;
* differiscono in **152** righe, esattamente quelle con almeno una sigla CDS o DSC (216 − 4³ = 152).

Scambiare i due sensi dà quindi un risultato sbagliato ma plausibile: è la trappola della Prima crisi (libro
§ 2.4.5–2.4.8). Il criterio di appartenenza dà lo stesso esito nei due sensi (la classe è chiusa per inversione); la
**lettura dei fattori** no.

**Blocchi e fibre.** Per i = 2 le fibre `F_{2,t}` sono i **blocchi** di posizioni consecutive 9t…9t+8; per i = 0
sono le classi di resto (i mazzetti). Le somme dei blocchi del § 1.10 del libro (36/117/198) sono le Σ_{2,t}
dell'identità, cioè la riga i = 2 della tabella di App. D § 7. ESEC.

### 3.5 Divergenze registrate

1. L'audit (§ 2.2) indicava le due versioni come «AMBIGUA» sulla precedenza. La fonte mostra che **non si
   contraddicono**: App. D aggiunge C, l'Articolo non la nega. FONTE.
2. L'Oss. 5.3 dell'Articolo non esiste in App. D, dove al suo posto c'è l'Oss. 6.3 (non minimalità). FONTE.

## 4. DP1 — opzioni

| | DP1-A · Articolo autorevole | DP1-B · App. D autorevole per la 4.0 | DP1-C · entrambe, versione breve ed estesa distinte |
|---|---|---|---|
| **Vantaggi** | testo breve, già pubblicato come articolo; nessuna affermazione oltre A/B | contiene C, dimostrata e verificata (§ 3.3); include rovesciamenti e famiglia estesa, coerenti col programma (DP3) | massima fedeltà: ogni affermazione è citata dove sta; l'utente vede che C è un risultato aggiunto |
| **Svantaggi** | le somme non possono essere un test di appartenenza: il riconoscimento per somme diventa solo «ricostruzione se già si sa che π è nella classe» | lascia implicito che l'Articolo è più prudente; chi legge solo l'Articolo trova l'Oss. 5.3 | due numerazioni (5.x / 6.x) da gestire nei testi e nei test |
| **Impatto su I5** | test di appartenenza **solo** diretto (Def. 4.1); le Σ calcolano i fattori su input già riconosciuto; nessun «criterio per somme» | criterio per somme come secondo test di appartenenza, con diagnostica per livello | come B nel comportamento; cambiano citazioni e riferimenti: A/B → Articolo § 5 **e** App. D § 6; C → solo App. D Teor. 6.4 |
| **Impatto su I6/I7** | il catalogo delle proprietà (I6) e la guida (I7) non possono dire «le somme riconoscono la classe» | I6/I7 possono enunciare C citando App. D | I7 deve spiegare la differenza fra le versioni: un paragrafo breve |
| **Rischio di confusione per l'utente** | medio: la funzione «somme» esiste ma «non vale» su input arbitrari | basso nel programma, medio per chi confronta i testi | basso, se la UI dice «criterio (App. D, Teor. 6.4)» e mai «Articolo, Teor. 5.x» per C |

## 5. DP1 — raccomandazione

**RACCOMANDAZIONE: DP1-C**, con il Teor. 6.4 di App. D come criterio operativo delle somme in I5:
* A e B si citano in entrambe le versioni;
* C si cita **solo** da App. D.

Motivi:
* C è dimostrata nella fonte, la dimostrazione è corretta (§ 3.2) e l'oracolo la conferma senza eccezioni
  (§ 3.3);
* l'Articolo non la nega;
* la scelta non cancella la versione breve.

In I5 il test **primario** di appartenenza resta quello diretto (Def. 4.1 / Teor. 4.2). Il criterio per somme è un
secondo percorso, e un test esaustivo deve verificare che i due concordino.

## 6. DP10 — fatti verificati

### 6.1 Taglio (A13)

**FONTE, § 7.1.13 A13.**
* Tagliare sposta tutte le posizioni di una quantità k modulo 27.
* Per portare la carta da p a n−1 si taglia di `k = (p − (n−1)) mod 27`.
* «Il taglio non appartiene al gruppo del Gioco, ed è proprio per questo che lo completa».

**FONTE, altri passi.**
* § 7.2 B4, ACAAN: «Il taglio ruota il mazzo, non cambia la struttura».
* § 7.3 C5/C6: `p′ ≡ p − k (mod 27)`, con il segno che dipende dalla convenzione; un taglio noto si registra o si
  compensa, un taglio ignoto rompe il riferimento.
* B7: tagli sconosciuti sono «mosse non appartenenti al Gioco».

**Rilevato di nuovo sul codice corrente**, ESEC e CODICE:

| Traslazione | Separabile (oracolo) | Criterio 6.4 | Nella classe estesa (648) | Riga della Tavola |
|---|---|---|---|---|
| C_9 (x ↦ x+9) | sì | sì | sì | **#144** (SCD, SCD, CDS) |
| C_18 (x ↦ x+18) | sì | sì | sì | **#108** (SCD, SCD, DSC) |
| C_9 nel verso opposto (x ↦ x−9) | sì | sì | sì | #108 |
| le altre 24 C_k | no | no | **no** | — (`numero_di` → None) |

Il test `test_e6_traslazioni_mod_27` resta valido; gli stessi fatti sono in I3 § 12.

**Divergenza con la fonte.** La frase di A13 «il taglio non appartiene al gruppo del Gioco» vale per 24
traslazioni su 26. I tagli di 9 e 18 carte **sono** disposizioni della Tavola: ruotano i nonetti, cioè B2 è una
3-rotazione e B1 = B0 = SCD. INFERENZA confermata da ESEC. Va registrata, non corretta nella fonte.

Il taglio va quindi guardato in cinque modi distinti:

| Aspetto | Stato |
|---|---|
| **operazione fisica** | gesto reale, libero, non è una raccolta del Gioco (FONTE) |
| **permutazione** | traslazione ciclica `C_k` delle posizioni modulo 27; il verso dipende dalla convenzione (FONTE C6) |
| **appartenenza** | 2 su 26 nella classe separabile; 24 fuori sia dalla classe separabile sia da quella estesa (ESEC) |
| **controesempio per il riconoscimento** | `C_1` ha il livello 0 «buono» e i livelli 1–2 no: mostra perché serve il test su tutti i livelli (ESEC) |
| **atomo del linguaggio** | oggi non esiste. I3 ha fissato: E6 solo catalogo e diagnostica, nessun atomo «taglio», nessuna estensione del linguaggio (TEST: `not hasattr(er, "taglio")`) |

### 6.2 Mazzi gemelli (A8)

**FONTE, § 7.1.8.** Due mazzi nello stesso ordine sottoposti a mescolamenti A e B: la carta in posizione p nel
primo è nel secondo in `T_B T_A⁻¹(p)`.

INFERENZA: `T_B T_A⁻¹` è un prodotto di due elementi della classe, quindi **appartiene alla classe**. A8 non è
un'operazione fuori dal gruppo: è una **relazione fra due mazzi**. Coincide con l'input «due mazzi» e con la
raggiungibilità v → w che l'audit assegna a I5. È di natura diversa dal taglio.

**PROPOSTA MOTIVATA**, non decisa: scindere DP10 in
* **DP10a — taglio**: operazione fuori dalla classe, salvo k = 9, 18;
* **DP10b — mazzi gemelli**: relazione interna alla classe, già coperta dal perimetro I5 «due mazzi / v → w».

## 7. DP10 — opzioni (taglio)

| | DP10-A · taglio produttivo nella 4.0 | DP10-B · taglio escluso dalla 4.0 | DP10-C · solo esempio o controesempio diagnostico, senza atomo |
|---|---|---|---|
| **I5** | nuovo atomo `C_k` nel linguaggio; riconoscimento di «G ∘ C_k»; decomposizioni con traslazioni | nessuna menzione; i C_k non compaiono nemmeno come input d'esempio | i C_k come **input di esempio** del riconoscitore: 24 rifiutati, con la diagnostica per livello; C_9 e C_18 riconosciuti come #144 e #108 |
| **I6** | proprietà del gruppo allargato `⟨classe, C_1⟩` (tutto S27? da studiare) | nessuna | voce di catalogo «le traslazioni: 2 dentro, 24 fuori», già in E6 |
| **parser / core / algebra** | **sì**: nuovo atomo nel parser (unico parser autorevole), nuove regole di riscrittura, forme canoniche; rischio sui test del linguaggio (E) | no | **no**: le traslazioni si costruiscono come permutazioni e passano dall'input «permutazione» di I5 |
| **allargamento del perimetro** | alto: tocca il linguaggio chiuso in E, la forma canonica, l'export e la Tavola 1728 | nullo | minimo |
| **valore didattico** | alto per ACAAN (A13, B4), ma è magia applicata, non la struttura del Gioco | perde il controesempio più naturale | alto: mostra concretamente «dentro / fuori», l'eccezione 9/18 e il ruolo dei riporti |

## 8. DP10 — raccomandazione

**RACCOMANDAZIONE: DP10-C per il taglio**:
* si mantiene il confine fissato da I3 (E6 catalogo e diagnostica, nessun atomo, linguaggio invariato);
* in I5 le traslazioni entrano solo come input d'esempio del riconoscimento;
* l'eccezione C_9 / C_18 va mostrata esplicitamente, come correzione documentata della frase di A13.

**RACCOMANDAZIONE collegata**: approvare la scissione in DP10a / DP10b, con DP10b (mazzi gemelli) assorbita dal
perimetro I5 «due mazzi / v → w», senza nuove operazioni.

Il calcolo scenico dell'ACAAN (`k = (p − (n−1)) mod 27`) resta fuori da I5. È una possibile voce di I6 o I7, da
valutare dopo.

## 9. Contratto I5 risultante se le raccomandazioni vengono approvate

**Test di appartenenza** (service puro, nomi neutri, nessun G/H/Γ/G_ext nell'API):

| Funzione proposta | Contenuto | Fonte |
|---|---|---|
| `separabile(π)` | test diretto, Def. 4.1: cifre di π(x) dipendenti solo dalla cifra di x dello stesso livello. È il test **primario** | Articolo / App. D Def. 4.1, Teor. 4.2 |
| `fattori_locali(π)` | i ρ_i letti dalle cifre (Oss. 5.3 / 6.3); coincide con `try_kron_decompose` e con `numero_di` → riga | idem |
| `classe_estesa(π)` | l'unico k ∈ {0,1,2} con `π ∘ M^{−k}` separabile, oppure nessuno | App. D § 5.3 |
| `somme_di_fibra(π, verso)` | Σ_{i,t}. `verso="avanti"`: immagini di π sulle fibre di posizione; `verso="indietro"`: le stesse su π⁻¹ | Teor. 5.1 / 6.1 |
| `candidati(π, verso)` e `criterio_somme(π, verso)` | ρ̂_i razionali esatti, esito del Teor. 6.4 **per livello** (intero? permutazione?) | App. D Teor. 6.4 |

Contratti di test:
* `criterio_somme ⇔ separabile` su tutta la classe (216), sulla classe estesa (648) e su un campione con seme di
  S27, più i negativi mirati del § 3.3;
* nei 216 casi, i candidati «indietro» sono gli inversi di quelli «avanti», e differiscono in 152 righe.

**Esempi fissi**:
* Es. 7.1 di App. D (= Es. 6.1 dell'Articolo), con le Σ di § 3.3;
* tabella `C_i = 108, 90, 36` e valori 108/117/126, 90/117/144, 36/117/198;
* somme dei blocchi dell'identità 36/117/198 (§ 1.10);
* `C_1` con i candidati frazionari;
* il caso «somme tutte 117» (candidati interi non permutazioni);
* C_9 → #144, C_18 → #108;
* esempi del libro § 2.4.8 e § 10.2.1 come previsti dall'audit, da trascrivere in I5.

**Classe separabile e classe estesa senza decidere DP2**: nell'API «separabile» (termine della fonte, neutro) e
«classe estesa con rotazione delle cifre». Nessuna etichetta G/H/Γ nei nomi pubblici; eventuali alias si decidono
con DP2.

**Taglio**:
* solo come input-permutazione d'esempio (DP10-C): nessun atomo, nessun cambio al parser;
* E6 invariato;
* l'eccezione 9/18 esposta dalla diagnostica, non da un caso speciale.

**Altri punti del perimetro I5 dell'audit**, da mantenere:
* input di una permutazione o di due mazzi, con A8 come relazione `T_B T_A⁻¹`;
* ricostruzione da due guide;
* raggiungibilità v → w;
* A1 «note due, calcola la terza».

**Fuori da I5, intenzionalmente**:
* minimalità delle somme (Oss. 6.3);
* storie di controlli e decomposizioni dalle somme (Oss. 6.5: non determinabili);
* taglio come atomo e ACAAN;
* famiglie per b^m generale e 21 carte;
* catalogo proprietà (I6);
* guida (I7);
* nomi definitivi (DP2).

## 10. Questioni che richiedono approvazione

1. **DP1**: A, B o C. Raccomandata **C**, con il Teor. 6.4 di App. D come criterio operativo e il test diretto come
   primario.
2. **DP10**: approvare o no la scissione **DP10a** (taglio) / **DP10b** (mazzi gemelli).
3. **DP10a**: A, B o C. Raccomandata **C**: diagnostica senza atomo, confine I3 mantenuto.
4. **DP10b**: assorbire A8 nel perimetro I5 «due mazzi / v → w», senza nuove operazioni.
5. **Nomi neutri** dell'API I5 (`separabile`, `classe_estesa`) fino alla decisione DP2.

Nessun blocker: le fonti sono sufficienti e coerenti per decidere.

## 11. Git status

Prima del commit di questo documento:

```
## main...origin/main [ahead 105]
?? Articolo.pdf
?? LIBRO_MAIN.pdf
```

Dopo il commit: 106 commit avanti, stessi due PDF non tracciati. Nessun push; I5 non iniziato.
