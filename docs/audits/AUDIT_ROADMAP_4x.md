# Audit progettuale di `docs/release/ROADMAP_4.x.md`

**Repository:** `27-card-trick-explorer` · branch `main` · HEAD `2a0a659` (5 commit locali non pubblicati dopo `v4.0.0`)
**Oggetto:** versione *di lavoro, non committata* della roadmap (895 righe), che sostituisce la versione committata `a27ea82` (tabella G1–G12).
**Data:** 5 ottobre 2026 · **Natura:** sola lettura. Nessun file del repository modificato, nessun commit, nessun push.

Metodo: lettura di core, servizi, GUI, test, CI, documenti di chiusura (I1–I7, K, RC2), audit V4 e A1; verifiche numeriche con script **esterni** al repository che importano il core senza scrivere bytecode. La suite GUI e la CI remota **non** sono state eseguite.

---

## 1. Giudizio complessivo

**Solidità — buona sui principi, debole sull'aderenza al codice.** La sezione 5 (convenzioni `T(i)=j`, `A∘B` = prima B, `J ∈ H`, 1 728 Procedure → 216 trasformazioni, gerarchia `H ⊂ Γ ⊂ S₃≀S₃ ⊂ S₂₇`) è corretta e coincide con il core. Ho verificato in modo indipendente che `|⟨H, permutazioni delle cifre⟩| = 1 296`, che Γ (648) vi ha indice 2 e che MSC vi appartiene.

**Completezza — sovrabbondante in 4.1/4.2, carente sulla manutenzione reale.** Circa metà delle voci 4.1/4.2 esiste già, del tutto o in parte, nei servizi (`services/laboratorio.py`, `services/riconoscimento.py`, `services/procedure.py`, `core/algebra.py`, `core/combinations.py`), quasi sempre in forma testuale. La versione committata della roadmap aveva una colonna «Dati già disponibili nella 4.0.0», che nella riscrittura è sparita. È la causa principale delle voci ridondanti.

**Problemi principali**

1. Le voci sono organizzate per *tipo di output* (4.1 = grafica, 4.2 = matematica) e non per *oggetto*. Per questo lo stesso oggetto (fibre, Λ, S_F, classi laterali, generatori) compare due o tre volte in release diverse.
2. Ci sono quattro imprecisioni matematico-terminologiche con un rischio concreto:
   - il wreath product descritto come «permutazione dei blocchi», mentre permuta le **coordinate/livelli**;
   - «Kronecker» usato con tre significati;
   - i simboli `R` e `τ` già occupati con altri significati;
   - un confine del «Dominio Kronecker esteso» che non regge sulle trasformazioni complete.
3. La manutenzione è tarata su uno stato superato: la chiusura con sessione sporca è già fatta e la CI esiste già. Mancano invece debiti più gravi: avvio GUI del bundle mai certificato, core che produce testo localizzato, nessuna gestione centralizzata di stile/DPI, PDF solo A3 senza numerazione, licenze di terze parti nel bundle.
4. I criteri di release riguardano solo l'*apertura*, non la qualità in uscita. Inoltre il lavoro UX1–UX4 già fatto dopo la 4.0.0 non trova posto nelle regole della 4.0.x.

**Opportunità principali**

- **Un modello grafico comune** rende 4.1 grande la metà: tre viste invece di undici voci.
- **Le «famiglie di gesti»** (`FamigliaGesti` esiste già in I1) unificano S_F, il dominio esteso, le Procedure equivalenti e i rovesciamenti.
- **S₃≀S₃ dà una collocazione precisa** all'idea «strutturata ma non realizzabile dal gioco»: sono esattamente i 648 elementi di `W \ Γ`.
- **Il tutor può partire subito su H e Γ** con soli componenti deterministici: traccia di riscrittura, testimoni di non-separabilità, composizione e inversa. Non serve aspettare il wreath product.

---

## 2. Voci già completate o parzialmente completate

| voce roadmap | stato | evidenza nel repository | azione consigliata |
|---|---|---|---|
| 1.1 Decomposizione ciclica | **parziale** (testo colorato, niente grafo) | `gui/cycles_tab.py` (ordine, tipo, cicli colorati, `_CYCLE_PALETTE`), `core/analysis.py` | Diventa una modalità della «vista posizioni» (§5) |
| 1.2 Orbite | **parziale**: solo ⟨T⟩ | `cycles_tab.py` sotto-scheda Orbite. Manca ⟨S⟩ per S scelto | Fondere con 1.1/1.10. Nota: H e Γ sono transitivi sulle 27 posizioni (L51), quindi solo i sottogruppi *propri* danno orbite informative |
| 1.3 Cayley di H | **modello presente, vista testuale** | `services/laboratorio.py:941-1046`: `Grafo` (adiacenza, distanze, distribuzione, diametro), `cammino`, grafo `cayley_h` con generatori fissi (trasposizioni per livello), non orientato, archi senza etichetta; `gui/laboratorio_tab.py:381` | Estendere il modello (generatori scelti, archi orientati ed etichettati, dominio Γ) prima di disegnarlo |
| 1.4 Classi laterali | **dati e vista testuale presenti** | `lab.classi_laterali()`, `lab.etichetta(p).r`, `riconoscimento.classe_estesa`; sotto-scheda «Classi laterali e stadi» | Diventa colorazione/partizione del grafo di gruppo, non una vista autonoma |
| 1.5 Transizioni complete/intermedie | **dati presenti** | `lab.stadi()` (`laboratorio.py:839-896`): prefissi j = 1, 2, 3 con/senza rovesci, molteplicità, classe laterale; verificato da `_v_stadi` | Fondere con 2.1 (S_F) |
| 1.6 Grafi da generatori | assente | — | Fondere con 1.3: stesso servizio (chiusura BFS + grafo di Cayley/Schreier) |
| 1.7 Fibre digitali | **calcolo presente, vista testuale** | `riconoscimento.somme_di_fibra`, `COSTANTI_C = (108, 90, 36)`; `riconoscimento_tab.py:177-398` (scheda Somme); Guida, L97 chiuso in I7 | Fondere 1.7 + 1.8 + 1.9(Λ) + 2.3 + 2.4 in **una** voce «Fibre» |
| 1.8 Trasporto e ricostruzione | **presente** | `criterio_somme` (`.ricostruita`, `.coincide`), App. D Teor. 6.4; proprietà `_v_somme` nel Laboratorio | Idem |
| 1.9 / 2.3 Λ_{i,u} | **già calcolata, non nominata** | `somme_di_fibra(p, INDIETRO)` = somme delle preimmagini = `C_i + 3^{2+i}·M_i⁻¹(u)`; selettore avanti/indietro in Riconoscimento | Solo notazione: chiamare Λ ciò che esiste. Togliere le due voci |
| 1.10 Orbite carte/posizioni | **parziale** | `cycles_tab` (orbita di una carta), `tabellone.flusso_carta` (I2), `services/successione.py` (J, L90) | Fondere nella vista posizioni |
| 1.11 Relazioni fra tabelloni | **parziale e vaga** | `tabellone.ritorno`, `realizza`, tabellone inverso (I2/J), `conjugacy_dialog.py` | Ridurre a «relazioni nominate» (inverso, coniugio, composizione, ritorno) come archi del grafo di gruppo, oppure eliminare |
| 2.1 S_F | **parziale** | `lab.stadi()` enumera i prefissi; `⟨S_F⟩ = Γ` non verificata; definizione assente nel repository | Definirla dal libro (§6), poi fondere con 2.7 |
| 2.2 Forma canonica di J | **aperta, piccola** | `CanonicalForm` esclude J (`algebra.py:118-125`; `_analyze_normal_form` restituisce kind `'J'`/`'composta'`, `:988`); il parser accetta già `R_U` (`:1238`) | Spostare tra le piccole correzioni (4.0.x o primo passo 4.1) |
| 2.4 Laboratorio delle fibre | **parziale** | Riconoscimento › Somme + proprietà `somme` del Laboratorio | Fondere in «Fibre» |
| 2.5 Forma normale in Γ | **completata** | `CanonicalForm` K∘MSC^k con `compose`, `to_perm`, traccia; `classe_estesa`; `etichetta`; `_v_forma_normale`, `_v_normale` (verifiche esaustive) | **Rimuovere.** «Confronto fra decomposizioni equivalenti» non ha senso con una forma normale unica; se si intendono le 46 656 decomposizioni a tre stadi, esistono già (dialogo Decomposizioni) |
| 2.6 Procedure equivalenti | **servizio completo, GUI assente** | `services/procedure.py` (I1): `classe_trasformazione` (8), `fibra_bersaglio` (64/8), `confronta`, costi k1/k2/k3, strategia storica/sicura. DP11 decisa (`NOTE_VERSIONE_4.0.0.md`: «relazione, non tavola»). I7 §14: «variante sicura … ancora senza vista» | Riclassificare da «estensione matematica» a «vista su servizio esistente»: piccola, anticipabile |
| 2.7 Dominio Kronecker esteso | **in gran parte presente come «famiglia estesa»** (libro cap. 9) | `core/combinations.py:18-105` (filtri `p0..p2`, `j0..j2`, `j_uniform`, preset Gioco Reale); `permutations.compute_stage`: Stage = (p2⊗p1⊗p0)∘MSC∘(j2⊗j1⊗j0), DP3 = A; `constants.J_OPTS = ["I_3","R_U"]` | Riformulare (§6): il modello dei rovesciamenti locali **esiste ed è fissato** |
| 2.8 b^m / 2.9 rettangolare | assenti | Il core è cablato su 27: circa 186 letterali `27` e 108 `216` in `core/` + `services/` | Fuori dalla serie 4.x (L94, L99 «OLTRE 4.0» nell'audit V4) |
| D 4.3 Chiusura con sessione dirty | **completata** in `e0af6df` | `app._on_close` → `_sessione_conferma_sostituzione` → `dialoghi_stato.conferma_abbandono` (Salva / Non salvare / Annulla); `tests/test_ux1_stato.py` t06–t08, `test_clean_non_chiede_conferma` | **Rimuovere** (registrarla nelle note della prossima versione) |
| D 4.6 Verifica bundle Windows | **parziale** | `ci.yml` job `windows`: selftest dell'exe, LICENSE, licenza DejaVu, nessun PDF | Licenze e assenza PDF già fatte. Mancano avvio GUI, export, multiprocessing, sessioni |
| D 4.7 Script di build | assente | Nessuna cartella `scripts/`; lo ZIP in `dist/` è stato fatto a mano | Fondere con 4.8 |
| D 4.8 Automazione release | **parziale** | La CI produce sdist, wheel e bundle come *artifact di workflow* | Manca: trigger su tag, ZIP, SHA-256, bozza di Release |
| D 4.1 `ui_call` | aperta | `gui/common.py:56-82` (`after(0)` **e** `winfo_exists()` chiamati dal thread di lavoro); il pattern sicuro coda + `after` esiste già in `distribution_tab.py`/`decomposition.py`; `services/lavoro.py` censisce «cinque esecuzioni diverse» | Sale di priorità (§8) |
| D 4.2 `fsync` | aperta | `core/parallel.py:471-508`: nessun `flush`/`fsync` | Invariata, piccola |
| D 4.4 Alias legacy | stabile | `appartiene_a_G`, `DECOMPOSIZIONI_PER_TARGET_IN_G`, `classe_estesa`; `tests/test_alias_nomi.py` | Invariata, bassa priorità |
| D 4.5 Warning setuptools | aperta | `gioco27/assets` senza `__init__.py`; `packages.find include=["gioco27*"]` + `package-data` | Banale: chiudere subito |

**Infrastruttura già disponibile che cambia la difficoltà del lavoro futuro**

- Modello `Grafo` con BFS, distanze e cammino minimo deterministico.
- Emettitore SVG scritto a mano: `export_group_dialog.py` (heatmap, griglia, istogramma).
- Riscrittore simbolico con traccia passo-passo (`Rewriter.normalize_with_trace`, `RewriteStep`).
- Testimoni di non-separabilità (`riconoscimento.Conflitto`).
- Catalogo di proprietà con dominio e metodo di verifica (`laboratorio.CATALOGO`).
- `Revisioni` per l'obsolescenza dei lavori.
- Test di layout a 1280×720, 1366×768 e 1920×1080 (`test_layout_accessibilita_h2.py`, 93 test).
- Rasterizzazione PDF nei test (pypdfium2).
- CI su 5 versioni di Python, più packaging e Windows.

---

## 3. Problemi della roadmap attuale

**P1 — Roadmap non ancorata al codice esistente**
- *Perché conta:* si pianificano come nuove cose che vanno solo esposte o estese. Le stime e l'assegnazione alle release risultano gonfiate.
- *Modifica:* reintrodurre per ogni voce una riga «Base esistente» (modulo/servizio) e uno stato (`assente` / `servizio` / `vista testuale` / `completa`).

**P2 — Duplicazioni**
- *Dove:* Λ compare in 1.9, 2.3 e nella lista priorità; le fibre in 1.7–1.8 e in 2.4; S_F in 1.5 e in 2.1; le classi laterali/forma normale in 1.4 e in 2.5; i generatori in 1.2, 1.3 e 1.6.
- *Perché conta:* lo stesso oggetto finisce in due release con due definizioni di «fatto».
- *Modifica:* una voce per oggetto (vedi §5 e §6).

**P3 — Divisione «grafica vs matematica» fra 4.1 e 4.2**
- *Perché conta:* vista e servizio di uno stesso oggetto si progettano insieme. Separarli in due release produce viste che poi vanno rifatte (per esempio il grafo delle transizioni 1.5 «prepara» S_F 2.1).
- *Modifica:* organizzare per oggetto/tema. Il principio «nessuna logica nella GUI» resta, ma ogni voce comprende servizio e vista.

**P4 — Wreath product: «blocchi» è sbagliato**
- *Il problema:* in 3.2–3.4 (e nel brief) l'elemento esterno «permuta i blocchi» e si chiede di «prevedere l'immagine di un blocco». Il S₃≀S₃ che contiene Γ (ordine 1 296, App. A/§5.1.7 del libro, L40) agisce sulle 27 posizioni con l'**azione prodotto**: il fattore esterno permuta le **tre cifre ternarie (livelli)**, non i tre blocchi B₀, B₁, B₂ da 9 carte. MSC (µ(n) = 9n₀ + 3n₂ + n₁) è la rotazione delle cifre.
- *Verifica:* `⟨H, permutazioni delle cifre⟩` ha 1 296 elementi, contiene MSC e Γ con indice 2. Il rovesciamento di un solo mazzetto da 9 **non** vi appartiene.
- *Perché conta:* l'errore entrerebbe nel core, nella GUI e negli esercici del tutor. Un S₃≀S₃ «a blocchi» (azione imprimitiva) agisce su 9 punti, non su 27.
- *Modifica:* sostituire «blocchi» con «livelli/coordinate» e aggiungere la frase: «azione prodotto; il fattore esterno σ ∈ S₃ permuta le cifre (n₂, n₁, n₀)».

**P5 — «Kronecker» ha tre significati**
- *Il problema:*
  - nel core significa sia «∈ H» (`try_kron_decompose`, «prodotto di Kronecker GEN3³») sia «decomposizione a tre stadi A₂∘MSC∘A₁∘MSC∘A₀∘MSC» (`find_all_kron_decompositions`, che ha 46 656 soluzioni se T ∈ H e 0 altrimenti);
  - la roadmap aggiunge un terzo uso, «decomponibilità strutturale secondo Kronecker» per un dominio esteso.
- *Perché conta:* il confine concettuale richiesto da 2.7 dipende proprio da questa parola.
- *Modifica:* registro dei termini (§10). Riservare «separabile/∈ H» alle trasformazioni e «stadio di Kronecker» ai gesti.

**P6 — Collisioni di notazione**
- *Il problema:*
  - `R` indica il rovesciamento locale (`R_U`, App. A J = R⊗R⊗R, Guida §20 `R^{u_i}`), ma anche MSC (docstring di `services/laboratorio.py`, libro §11.7 `h∘R^r`) e la trasformazione totale (`compute_R`, `R_label`);
  - `τ` in 2.5 è il generatore di C₃, ma in Riconoscimento `τ_level` è una riga locale (`i18n: recognition.guides.row`);
  - `ϑ` (App. A) è l'automorfismo di rotazione;
  - 2.2 scrive «J = R⊗R⊗R» mentre `laboratorio.scheda_j` scrive `DCS⊗DCS⊗DCS`.
- *Perché conta:* 4.2 e 4.3 aggiungono proprio formule su questi oggetti. Il tutor dovrà mostrarle.
- *Modifica:* registro della notazione come prerequisito di 4.2 e 4.3. Ogni simbolo con un solo significato nell'interfaccia; nei testi utente MSC resta «MSC».

**P7 — Confine del dominio esteso impreciso sulle trasformazioni**
- *Il problema:* dopo 3 stadi ogni storia della famiglia estesa produce un elemento di H, e ogni elemento di H è realizzato da 8 Procedure del gioco. A livello di trasformazione completa non esiste quindi nulla di «non realizzabile».
- *Perché conta:* «motivo strutturale della non realizzabilità» è vuoto per T complete.
- *Modifica:* vedi §6, quattro livelli distinti.

**P8 — S_F definita in modo ambiguo**
- *Il problema:* le cardinalità cambiano con la definizione (verificate):
  - se S_F = trasformazioni cumulative «dopo uno o più stadi» senza limite, l'insieme coincide con Γ: le unioni dei prefissi del gioco crescono 12 → 84 → 300 → 504 → **648** (1…5 stadi). «Non presentarla come gruppo» diventa irrilevante;
  - se ci si limita a ≤ 3 stadi, sono 300 elementi (258 senza rovesciamenti);
  - se S_F = trasformazioni di **un** stadio della famiglia F, sono 12 (gioco), 6 (senza rovesci), 216 (estesa); in tutti i casi ⟨S_F⟩ = Γ.
- *Modifica:* prendere la definizione dal libro, citandola in `riferimenti.py`, prima di qualunque implementazione.

**P9 — Dipendenze dichiarate sbagliate, quelle reali non dichiarate**
- *Il problema:* 3.1 subordina 4.3 al dominio esteso, ma la famiglia estesa vive tutta dentro Γ e il wreath product non ne ha bisogno. Mancano invece: modello grafico prima di 1.2–1.6; palette/stile prima delle viste a colori; tracce strutturate (codici) prima del tutor; rappresentazione di W nel core prima dell'Explorer di W.
- *Modifica:* sezione «Dipendenze» esplicita (§9).

**P10 — Criteri di release solo d'apertura e vaghi**
- *Il problema:* «realmente utilizzabili» non è verificabile. Non ci sono criteri di uscita che riusino la pratica A1–A5 (audit matematico, terminologico, IT, EN). La 4.0.x vieta «nuove funzioni sostanziali», ma i 5 commit UX dopo la 4.0.0 (+1 400 righe di i18n e guidance) non sono solo bug fix.
- *Modifica:* aggiungere criteri di chiusura (§10) e una regola esplicita sul lavoro UX.

**P11 — Manutenzione tarata su uno stato superato**
- *Il problema:* la chiusura dirty è indicata ad alta priorità ma è fatta; `ui_call` è «da pianificare con cautela» proprio mentre 4.1 aggiunge calcoli in background; l'avvio GUI dell'eseguibile non è mai stato certificato (RC2 §7) ed è in priorità media.
- *Modifica:* §8.

**P12 — In 4.2 si mescolano lavori e «valutazioni»**
- *Il problema:* b^m, caso rettangolare e «J solo se migliora» non sono pianificabili come voci di release.
- *Modifica:* sezione separata «Esplorazioni oltre la 4.x».

**P13 — Vincoli persi nella riscrittura**
- *Il problema:* la versione committata imponeva un equivalente testuale per ogni grafo, il colore mai come unico canale, i riferimenti al libro solo tramite `riferimenti.py` e il fatto che S₂₇ non si enumera. Il nuovo §1.12 non li riporta.
- *Modifica:* reintegrarli.

**P14 — Formule non visualizzabili su GitHub (pratico, non solo editoriale)**
- *Il problema:* i delimitatori `\( \)` / `\[ \]` e la macro `\MSC` non vengono resi su GitHub.
- *Modifica:* usare `$…$`/`$$…$$` e scrivere `\mathrm{MSC}`.

---

## 4. Elementi mancanti

**Funzionali**
- Viste per servizi già pronti: le 8 Procedure di una riga, la fibra carta→bersaglio (64/8), la variante sicura (I1, debito I7 §14).
- Raggiungibilità per famiglia e per lunghezza: «quali trasformazioni intermedie raggiunge il gioco in k stadi» (vedi §6).
- Esportazione dei grafi come un solo servizio (SVG + testo), non un export per vista.

**Matematici**
- Registro della notazione e dei termini (P5, P6).
- Definizione di S_F dal libro (P8).
- Il «destino» dei rovesciamenti (parità in M₂, L38 parziale; formula A13 oggi solo nella Guida §20) come servizio con codici.
- Caratterizzazione di `W \ Γ`.
- Dipendenza delle metriche di Cayley (distanza, diametro) dai generatori, da rendere esplicita nelle viste.

**GUI/UX**
- Consolidamento visuale:
  - 245 tuple di font cablate, 318 colori esadecimali cablati, 7 dialoghi con `geometry("…")` fissa;
  - nessuna gestione DPI su Windows;
  - famiglie Segoe UI/Consolas disponibili solo su Windows; solo `uifont.py` usa font con nome.
- Palette accessibile per cicli, classi laterali e fibre (oggi `_CYCLE_PALETTE` è locale a `cycles_tab.py`).
- Widget grafo accessibile: tastiera, alternativa testuale, selezione → dettaglio.

**Output/documenti**
- PDF solo **A3 orizzontale** (`combinations.py:275,300,566`; `detail_pdf.py:424,441`).
- Nessuna numerazione di pagina, intestazione o piè di pagina (nessun `getPageNumber`).
- Formati eterogenei (PDF reportlab, HTML stampabile del protocollo, HTML/LaTeX, SVG manuale, TXT, CSV/XLSX, JSON + manifest) senza profili d'uso dichiarati.

**Architettura**
- Il core produce testo localizzato: `Rewriter` chiama `tr()` per le regole (`algebra.py:785-947`), e anche le etichette PDF in `combinations` sono localizzate. È l'opposto della convenzione dei servizi (codici stabili, testo nella GUI) ed è un prerequisito diretto del tutor.
- Esecuzione asincrona non unificata (`ui_call`).
- Astrazione «famiglia di gesti» limitata al gioco classico (`FamigliaGesti` in I1); i filtri dell'Analisi descrivono la famiglia estesa per un'altra via.

**Test/packaging/release**
- Smoke GUI del bundle.
- Bundle costruito da un ambiente pulito: oggi contiene `PIL`, `lxml`, `charset_normalizer`, che vengono da dipendenze di test.
- Note di licenza di terze parti (numpy, pikepdf/qpdf, reportlab, openpyxl, pypdf, Tcl/Tk, Python): punto aperto 3 di K, mai chiuso.
- Pipeline tag → artefatti + SHA-256.
- Budget di prestazione per grafi da 648 vertici.
- Esito CI dei 5 commit locali: non verificabile da qui.

---

## 5. Valutazione 4.1

**L'ordine attuale non è quello giusto: va prima un modello grafico comune.** Tutte le voci 4.1 sono istanze di tre tipi di grafo, che differiscono per l'insieme dei vertici:

| Vista | Vertici | Voci assorbite | Base esistente |
|---|---|---|---|
| **A. Posizioni** | 27 posizioni (o carte) | 1.1 cicli, 1.2 orbite di ⟨T⟩ e di ⟨S⟩ (grafo di Schreier), 1.10 traiettorie, 1.9 T/T⁻¹ (archi invertiti) | `cycles_tab`, `analysis.cycle_decomposition`, `tabellone.flusso_carta`, `successione` |
| **B. Gruppo** | 216 (H) o 648 (Γ) | 1.3 Cayley, 1.6 generatori, 1.4 classi laterali (partizione/colore), 1.5 percorsi dei prefissi, 1.11 relazioni nominate | `lab.Grafo`, `cammino`, `classi_laterali`, `stadi`, `etichetta` |
| **C. Fibre** | 9 fibre × 3 livelli (bipartito F_{i,t} → F_{i,M_i(t)}) | 1.7, 1.8, 1.9 (Λ), 2.3, 2.4 | `somme_di_fibra`, `criterio_somme`, scheda Somme |

**Infrastruttura da introdurre prima delle viste (milestone M0)**
1. Un `GrafoStrutturale` nei servizi: vertici tipati, archi orientati ed **etichettati** dal generatore o dalla relazione, partizioni (classi laterali, orbite), suggerimenti di disposizione, serializzazione in testo. Estende `lab.Grafo`, oggi non orientato e senza etichette.
2. Un servizio `sottogruppo_generato(S, dominio)` con chiusura BFS e grafo di Cayley/Schreier. Bastano H e Γ, che sono piccoli.
3. Un solo widget Tk Canvas: tastiera, selezione → dettaglio, alternativa testuale obbligatoria, esportazione SVG con l'emettitore di `export_group_dialog.py` reso modulo comune.
4. Disposizioni **algebriche invece di un motore generico**, così non servono dipendenze (networkx, graphviz). Con le trasposizioni per livello, il Cayley di H è `K₃,₃ □ K₃,₃ □ K₃,₃` e si dispone come prodotto 6×6×6; Γ come tre anelli di classi laterali; le fibre come grafo bipartito a 3 righe. Con generatori arbitrari si accetta una disposizione ad anelli per distanza dalla radice (`lab.Grafo.distribuzione` esiste già).

**Cosa tenere, cambiare, fondere, anticipare, rinviare**
- **Tenere:** principio guida, convenzione `T(i)=j`, distinzione Tavola (enumerativa) / grafo (relazionale).
- **Fondere:** undici voci in **M0 + tre viste**.
- **Anticipare:** la vista Fibre prima del grafo di Cayley. Ha più valore didattico (teorema di ricostruzione, L97 era P0 nell'audit V4), poco rischio di disposizione, e i calcoli esistono già.
- **Rinviare/ridurre:** 1.11. «Tabelloni equivalenti» non ha una definizione; restano solo relazioni nominate.
- **Nota su 1.2 e 1.10:** per una sola T, la traiettoria di una carta e l'orbita di una posizione sono **lo stesso insieme** (il ciclo), percorso in versi opposti (T contro T⁻¹). La distinzione diventa sostanziale solo per una *successione* di trasformazioni diverse (servizio `successione`). Va detto così, altrimenti si rischiano due viste identiche.
- **Criterio di apertura 4.1.0:** sostituire «cicli, orbite, almeno un grafo di gruppo» con «M0 + vista A + una fra B e C», con i criteri di qualità del §10.

---

## 6. Valutazione 4.2 (in particolare il Dominio Kronecker esteso)

### 6.1 Che cosa esiste già

La famiglia «estesa» del libro (cap. 9: 1 728 configurazioni per stadio, 1 728³ storie, Teor. 9.55–9.57) **è già il dominio dell'Analisi**:
- Stage = (p₂⊗p₁⊗p₀)∘MSC∘(j₂⊗j₁⊗j₀), con pᵢ ∈ S₃ e jᵢ ∈ {I, R_U} (`permutations.compute_stage`, `combinations.FiltroStadio`);
- `j_uniform` restringe ai rovesciamenti globali;
- il preset Gioco Reale (1 728 Procedure) è la famiglia vincolata (p₁ = p₀ = id, j uniforme; `procedure.py` DP3).

Il «modello dei rovesciamenti locali» che 2.7 chiede di formalizzare (zero, uno, due o tre rovesciamenti per livello) è **già formalizzato**: J per livello prima di MSC (DP3 = A, audit A1 `d18c3bf`). La frase «senza fissare a priori l'ordine algebrico… finché non sia verificata la convenzione nel core» è superata: la convenzione è verificata.

### 6.2 Fatti verificati (script esterno, core del repository)

| prefisso (stadi) | famiglia estesa: trasformazioni distinte | gioco classico: distinte | dove |
|---|---|---|---|
| 1 | 216 (tutta H∘MSC) | 12 | H∘MSC |
| 2 | 216 (tutta H∘MSC²) | 72 | H∘MSC² |
| 3 | 216 (tutta H) | 216 | H |

Altri fatti:
- In un solo stadio la famiglia estesa produce 1 728 configurazioni ma solo 216 trasformazioni, 8 per ciascuna. J per livello ∈ H, quindi `P∘MSC∘J = (P∘ϑ(J))∘MSC`: **numero e posizione dei rovesciamenti non sono mai leggibili dalla trasformazione**, ma solo dalla parola.
- Il rovesciamento di un **solo** mazzetto da 9 non sta in Γ e neppure in S₃≀S₃.
- Il gioco raggiunge tutta H∘MSC in 4 stadi: la «realizzabilità» dipende dalla lunghezza ammessa.

### 6.3 Conseguenza: il confine giusto ha quattro livelli, non due

1. **Parola/configurazione** (gesti): una configurazione della famiglia estesa può non essere una Procedura. Qui hanno senso il conteggio e la posizione dei rovesciamenti e la «ricerca della Procedura equivalente» (per T completa ne esistono sempre 8: `classe_trasformazione`).
2. **Trasformazione intermedia a lunghezza fissata**: per 1 o 2 stadi il gioco raggiunge 12 e 72 delle 216. È **l'unico punto in cui «non realizzabile dal gioco» ha senso per una trasformazione**, ed è relativo alla lunghezza.
3. **Strutturata ma irraggiungibile**: `W \ Γ` (648 elementi: fattori locali + permutazione *dispari* delle cifre). Nessuna parola di nessuna famiglia di stadi di Kronecker la produce, perché tutte restano in Γ. È la formulazione precisa di «decomponibile secondo Kronecker ma non corrispondente a una Procedura».
4. **Fuori dalla struttura**: taglio (traslazione, già trattato come «fuori da H e Γ» in I7), rovesciamento di un singolo mazzetto, ridistribuzioni non uniformi.

### 6.4 Collocazione e riformulazione

- Rinominare 2.7 in **«Famiglie di gesti e realizzabilità»**: usa il lessico del libro («famiglia estesa / vincolata») ed evita il nuovo significato di «Kronecker».
- Fondere in questa voce **2.1 (S_F) e 2.6 (Procedure equivalenti)**. Tutte e tre richiedono lo stesso servizio: una `FamigliaGesti` generalizzata (quali livelli liberi, J per livello o uniforme) che alimenta filtri dell'Analisi, Procedure, S_F, prefissi raggiungibili e riepilogo dei rovesciamenti (formula A13).
- Il livello 3 (`W \ Γ`) appartiene a 4.3 e ne diventa il ponte naturale. È la ragione per cui la dipendenza vera è **4.2 → 4.3 solo per il lessico**, non per il codice.
- Resta prima di b^m: corretto.

### 6.5 Il resto di 4.2

- **2.2 J canonica:** piccola correzione del `Rewriter` (trattare l'atomo J come `DCS⊗DCS⊗DCS`). Fuori da 4.2.
- **2.3 Λ, 2.4 Laboratorio fibre:** confluiscono nella vista Fibre (4.1).
- **2.5:** rimuovere.
- **2.8, 2.9:** fuori dalla serie (§10).

---

## 7. Valutazione 4.3 (wreath product e tutor)

### 7.1 Una sezione autonoma per S₃≀S₃: sì, con tre correzioni

1. **Azione prodotto, livelli e non blocchi** (P4).
2. **Contenuto esatto:** W = Γ ⊔ Γ∘σ, con σ una trasposizione di cifre. Quello che aggiunge rispetto a Γ sono le permutazioni dispari delle coordinate. Didatticamente vale soprattutto come «struttura senza gesto» (§6.3, livello 3) e come chiave del perché G = S₃³ è il sottogruppo base (nucleo di φ, indice 6 — L40, mai coperto).
3. **Prerequisiti di core, prima di qualunque GUI:**
   - rappresentazione `(K, σ)` con σ ∈ S₃ come estensione di `CanonicalForm` (oggi `(K, k)` con k ∈ C₃) e di `rotate_kron_factors` a permutazioni arbitrarie dei fattori;
   - legge di composizione e inversa verificate esaustivamente sui 1 296 elementi;
   - riconoscitore concreto → astratto: generalizzazione di `separabile` con identificazione di quale cifra dell'immagine dipende da quale cifra della sorgente; il `Conflitto` esistente dà già i testimoni;
   - appartenenza H / Γ / W come verifiche del Laboratorio (aggiungere `Dominio.W`);
   - orbite, stabilizzatori e classi di coniugio di W: banali per enumerazione (1 296).

### 7.2 Tutor: la sezione è giusta come obiettivo, ma è legata alla cosa sbagliata

Quasi tutto il valore del tutor (composizione, inversa, appartenenza ad H/Γ, lettura dei fattori, classi laterali, forma normale) è disponibile **oggi** su H e Γ. Legarlo a W lo rinvia senza ragione. Propongo di separarlo:

- **T1 — Spiegazione dell'oggetto corrente** (H/Γ): «schede» deterministiche che leggono servizi esistenti (fattori, r, testimone di non-separabilità, traccia di riscrittura, Procedure che la realizzano).
- **T2 — Esercizi con correzione motivata** (H/Γ): generazione con seed (riproducibile, come gli esperimenti J); risposte strutturate (scelta, permutazione, fattore, esponente); correzione per confronto con il core; spiegazione = differenza fra risposta e risultato, mostrata nei livelli concreto ↔ fattori ↔ forma normale.
- **T3 — Estensione a W** (dopo il core di W).

**Deterministico (tutto il necessario):** generazione degli esercizi, verifica delle risposte, passaggi intermedi, controesempi, scala di suggerimenti a modello, bilinguismo tramite il catalogo.

**Componente linguistica (LLM):** servirebbe solo per risposte a testo libero e dialogo aperto. La sconsiglio per la 4.x:
- programma desktop offline e GPL;
- riproducibilità e testabilità (la suite è il cuore del progetto);
- coerenza IT/EN;
- principio «nessun risultato non formalizzato nel core».

Al massimo, come idea fuori ambito: «esporta il contesto dell'oggetto» in testo per un assistente esterno.

**Servizi che devono esistere prima della GUI del tutor**
- Tracce **strutturate** (codice regola + operandi, testo composto dalla GUI): oggi `RewriteStep.rule` è già una stringa localizzata prodotta nel core.
- Un modello `Esercizio` / `Risposta` / `Correzione` nei servizi, con codici stabili.
- Generatore con seed.
- Registro della notazione.

**Rischi**
- **Ampiezza:** il tutor è un secondo prodotto. I contenuti bilingui pesano (oggi `i18n.py` ha 4 951 righe, Guida 41 sezioni).
- **Sovrapposizione** con Guida, glossario e `guidance.py` appena completati (UX4).
- **Esercizi banali o ripetitivi** se non c'è un progetto didattico (livelli, prerequisiti, progressione).
- **Deriva della notazione** fra libro, core e tutor.
- **Costo dei test GUI** (la suite gira già file per file sotto Xvfb).
- **Confusione blocchi/livelli** (P4) amplificata negli esercizi.

---

## 8. Manutenzione tecnica: priorità reali

**P0 — prima di nuove funzioni (consolidamento 4.0.x)**
1. **Pubblicare e certificare lo stato attuale:** 5 commit UX1–UX4 non pubblicati e roadmap non committata. Decidere la versione (§11) e far girare la CI.
2. **Smoke GUI del bundle Windows.** RC2 §7: «l'avvio GUI completo dell'eseguibile non è … certificabile»; la CI esegue solo `--selftest`. Serve una modalità `--smoke-gui` (costruisce l'App, la rende, la chiude con codice 0) richiamata dalla CI sull'exe. È il rischio più alto per chi scarica lo ZIP.
3. **`ui_call` e threading.** Unificare sul pattern coda + `after` che esiste già (`distribution_tab`, `decomposition`). Oggi `ui_call` chiama `winfo_exists()` e `after()` dal thread di lavoro. Va fatto prima di 4.1, che aggiungerà lavori in background (chiusure di sottogruppi, disposizioni). Costo prevedibile: 8 chiamate `run_in_thread` e circa 30 riferimenti in 9 file di test.
4. **Warning setuptools:** banale.

**P1 — prima della 4.1.0**
5. **Pipeline di release riproducibile** (fonde 4.7 e 4.8): un solo script locale (`build` pulita → wheel/sdist → PyInstaller → ZIP → SHA-256 → riepilogo) richiamato anche da un workflow su tag che crea una **bozza** di Release. La pubblicazione resta all'autore.
6. **Igiene del bundle e licenze:** build da ambiente con sole dipendenze runtime + export (via PIL, lxml, charset_normalizer); file `THIRD_PARTY_LICENSES` generato.
7. **Testo fuori dal core:** almeno per la traccia di riscrittura (prerequisito del tutor) e per le etichette dei grafi nuovi.
8. **`fsync`** in `atomic_write`: piccolo. Su Windows la sincronizzazione della directory non è disponibile; documentarlo.

**P2**
9. Alias e nomi legacy: invariata. Aggiungere `compute_R`/`R_label` (nome fuorviante, P6) all'elenco dei nomi da affiancare con un alias.
10. Test del bundle per export PDF/XLSX, multiprocessing e sessioni (dopo P0.2).

**Da rimuovere:** 4.3 «Conferma alla chiusura» (fatta).

**Due nuovi filoni di qualità: sì, ma piccoli e a milestone**
- **A. Qualità visuale della GUI** (senza riscrittura né cambio di toolkit):
  - A1 *design tokens*: font con nome, colori e spaziature in un solo modulo e stili ttk; migrazione meccanica di 245 font e 318 colori;
  - A2 politica delle finestre: dimensioni relative allo schermo + `minsize` al posto delle 7 `geometry()` fisse; gestione DPI su Windows; fallback dei font fuori Windows;
  - A3 rifinitura per vista con revisione su screenshot a 1280×720, 1366×768, 1920×1080, 2560×1440.

  A1 deve precedere le viste 4.1, che hanno bisogno di una palette accessibile comune.
- **B. Qualità delle stampe/PDF:** merita una voce propria; i test attuali verificano l'integrità, non la leggibilità.
  - B1 tre profili d'uso: *consultazione* (HTML/schermo), *stampa* (PDF), *archivio* (CSV/JSON + manifest, già solidi);
  - B2 modello di pagina comune: intestazione con titolo, versione e parametri; piè di pagina «pagina x/y»; A4 verticale/orizzontale oltre ad A3;
  - B3 tabelle lunghe con intestazioni ripetute e segnalibri PDF;
  - B4 formule e figure (incluso SVG → PDF per i grafi 4.1);
  - B5 test: rasterizzazione di pagine campione (pypdfium2 già presente) + estrazione del testo per numerazione e sconfinamenti.

---

## 9. Ordine di sviluppo consigliato

1. **Consolidamento** (patch 4.0.x o equivalente): P0.1–P0.4; J nella forma canonica (2.2); aggiornamento della roadmap.
2. **Fondamenta trasversali:**
   - registro della notazione e dei termini (P4–P6, definizione di S_F);
   - design tokens e palette (A1);
   - tracce e spiegazioni come dati;
   - pipeline di release (P1.5–6);
   - modello di pagina PDF (B2).
3. **Visualizzazione strutturale** (4.1): M0 (modello grafico + widget + SVG/testo) → vista Posizioni → vista Fibre → vista Gruppo.
4. **Famiglie di gesti e realizzabilità** (4.2): servizio `FamigliaGesti` generalizzato → S_F e ⟨S_F⟩ = Γ come proprietà del Laboratorio → raggiungibilità per lunghezza → vista delle Procedure equivalenti (8/64, variante sicura) → riepilogo dei rovesciamenti. Le viste riusano il grafo di gruppo (percorsi dei prefissi).
5. **Tutor T1–T2 su H/Γ.** Può partire in parallelo a 4 una volta chiuso il punto 2.
6. **S₃≀S₃** (4.3): core `(K, σ)` → verifiche nel Laboratorio → Explorer di W con `W \ Γ` come «strutturate ma irraggiungibili» → tutor T3.
7. **Qualità visuale A2–A3 e PDF B3–B5:** filoni continui, con una scadenza dentro ogni release (le viste nuove escono già conformi).

**Dipendenze principali**
- Prima del grafo di Cayley servono: modello grafico + servizio di sottogruppo generato + widget + palette + `ui_call` unificato.
- Prima del dominio esteso servono: registro dei termini + definizione di S_F + `FamigliaGesti` generalizzata.
- Prima del tutor W servono: tracce strutturate + modello Esercizio + core di W + registro della notazione.

---

## 10. Modifiche suggerite a `ROADMAP_4.x.md` (non applicate)

**Aggiungere**
- Per ogni voce: «Base esistente» e «Stato».
- Sezione «Registro della notazione e dei termini»: R, τ, ϑ, MSC, «Kronecker», «separabile», «blocco» vs «livello», S_F.
- Sezione «Dipendenze» (§9).
- Filoni «Qualità visuale GUI» (A1–A3) e «Qualità degli output» (B1–B5).
- In §1.12: equivalente testuale obbligatorio, colore mai unico canale, riferimenti solo tramite `riferimenti.py`, budget di prestazione (648 vertici), etichette dei grafi senza testo nel core.
- Debiti: smoke GUI del bundle, igiene del bundle e licenze di terze parti, testo localizzato nel core, esecuzione asincrona unificata, gestione DPI.
- §7: **criteri di chiusura** per ogni release minore — CI verde (matrice + Windows con smoke GUI), audit mirati A1/A2 (e A3/A4 per i testi nuovi) sulle parti nuove, sezioni della Guida e test di allineamento, layout alle geometrie dichiarate, IT/EN completi.

**Rimuovere**
- 2.5 Forma normale in Γ (completata).
- D 4.3 Chiusura con sessione dirty (completata).
- Da 4.6: «licenze incluse» e «assenza dei PDF fonte» (già in CI).

**Spostare**
- 2.2 J canonica → consolidamento.
- 2.8 b^m e 2.9 rettangolare → nuova sezione «Esplorazioni oltre la serie 4.x».
- Il livello `W \ Γ` del dominio esteso → 4.3.

**Fondere**
- 1.1 + 1.2 + 1.9 + 1.10 → «Vista delle posizioni».
- 1.3 + 1.4 + 1.5 + 1.6 + 1.11 (ridotta) → «Vista del gruppo».
- 1.7 + 1.8 + 2.3 + 2.4 → «Fibre, somme e ricostruzione (Σ e Λ)».
- 2.1 + 2.6 + 2.7 → «Famiglie di gesti e realizzabilità».
- D 4.7 + 4.8 → «Pipeline di release riproducibile».

**Rinominare**
- «Dominio Kronecker esteso su 27 carte» → «Famiglie di gesti e realizzabilità» (lessico del cap. 9).
- 4.3 → «S₃≀S₃ (azione prodotto) e tutor algebrico», con il tutor in milestone T1–T3.

**Precisare**
- 3.2–3.4: «livelli/coordinate» al posto di «blocchi»; σ ∈ S₃ permuta le cifre.
- 3.1: togliere la dipendenza dal dominio esteso e sostituirla con «core di W verificato».
- 2.7: i quattro livelli del confine (§6.3) e il fatto che la convenzione dei rovesciamenti è già fissata (DP3 = A).
- 2.2: «J = DCS⊗DCS⊗DCS (in App. A: R⊗R⊗R, con R = rovesciamento locale)».
- §6 priorità di manutenzione: P0/P1/P2 del §8.
- Formule: `$…$` e `\mathrm{MSC}`.

---

## 11. Questioni da decidere insieme

1. **Versione dei commit UX1–UX4:** 4.0.1 (allargando la regola 4.0.x ai «difetti di usabilità») oppure primo blocco della 4.1? La regola attuale li esclude dalla 4.0.x.
2. **Definizione di S_F:** insieme degli stadi di una famiglia F, oppure dei prefissi cumulativi (e con quale lunghezza massima)? Va presa dal libro.
3. **Nome e perimetro di 2.7:** adottare «famiglia estesa / vincolata» del libro e i quattro livelli del §6.3? In particolare: la realizzabilità per trasformazioni intermedie va giudicata a **lunghezza fissata** o «in un numero qualsiasi di stadi»?
4. **Notazione nell'interfaccia:** quale simbolo per la rotazione delle cifre (MSC, R, τ) e quale per il rovesciamento locale (R_U, DCS)? Il registro può nascere solo da questa scelta.
5. **Tutor:** separarlo dal wreath product e farlo partire su H/Γ (T1–T2), oppure tenerlo dentro la 4.3? Confermare l'esclusione di componenti linguistiche generative nella 4.x.
6. **Ruolo di W nel programma:** solo Explorer/Laboratorio (struttura senza gesto) o anche collegamento esplicito a fenomeni fisici? Il secondo richiederebbe di modellare gesti che oggi non esistono.
7. **Ampiezza del filone PDF:** introdurre l'A4 come formato predefinito di stampa (con A3 opzionale) oppure mantenere A3 per i PDF dettagliati, che ne hanno bisogno per densità?
