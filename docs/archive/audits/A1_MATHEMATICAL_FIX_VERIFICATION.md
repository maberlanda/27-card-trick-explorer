# A1-FIX — Verifica delle correzioni matematiche

**Prodotto:** Gioco delle 27 carte — release candidate 4.0.0

**Data:** 2026-09-26

**Perimetro:** esclusivamente i cinque issue matematici e le tre tensioni di
fonte registrati dall'audit A1 finale.

L'audit storico `A1_FINAL_MATHEMATICAL_AUDIT.md` e il relativo CSV non sono
stati modificati. Questa nota documenta separatamente le correzioni.

## 1. Stato iniziale e fonti

- HEAD iniziale: `6d9dd96f715565b3923d470af8a1ddf5b1160698`.
- Working tree iniziale: soltanto `Articolo.pdf` e `LIBRO_MAIN.pdf`, entrambi
  non tracciati.
- `Articolo.pdf`, SHA-256
  `293BA88C1942A2D7CFDC44B29BB6AD5B7B9B87D4A449B3A7009BFBAABFC8D5A9`.
- `LIBRO_MAIN.pdf`, SHA-256
  `1E1C9A7E4A8B19E723EBEA39EF4F636AEBA2E954E7C4900F2D322E7663235E6A`.

Passaggi primari riletti: Articolo pp. PDF 4–9; Libro p. PDF 12 per la
convenzione matriciale, p. PDF 217 per A13 e pp. PDF 401–416 per il modello
esteso, i rovesciamenti e il criterio delle somme.

## 2. Verifica dei cinque issue

| issue | causa | correzione e superfici | oracolo e regressione | esito |
|---|---|---|---|---|
| `A1-MATH-01` | La descrizione di un punto `(i,j)` nella matrice di `T⁻¹` scambiava partenza e arrivo. | `guide.s17.right.body`, IT/EN: colonna `j` = partenza, riga `i` = arrivo. | `test_a1_math_01_inverse_matrix_uses_column_as_start_and_row_as_arrival`: usa `C9⁻¹=C18`, non involutiva, e controlla una cella orientata della matrice. | **VERIFIED FIXED: YES** |
| `A1-MATH-02` | Convivevano la numerazione pubblica approvata a base 0 e vecchie etichette a base 1; due formule mostravano inoltre i fattori in ordine inverso. | Tutte le superfici correnti interessate in `i18n.py`, le etichette della matrice in `gui/explorer_tab.py` e la documentazione corrente di `CanonicalForm` ora usano l'ordine alto-basso `P₂⊗P₁⊗P₀` / `(f₂,f₁,f₀)`. Gli assert storici di i18n sono stati riallineati. | `test_a1_math_02_public_kronecker_order_matches_ternary_oracle`: tripla asimmetrica e formula ternaria indipendente su tutte le 27 posizioni; controllo delle superfici IT/EN e della vista Explorer. | **VERIFIED FIXED: YES** |
| `A1-MATH-03` | La formula dell'inversa usava `rot₂ₖ`, confondendo il trasporto di un blocco attraverso `MSCᵏ` con quello necessario dopo l'inversione. | `guide.s17.inverse_formula`, IT/EN: `T⁻¹ = rotₖ(K⁻¹) ∘ MSC^{(3-k) mod 3}`, con definizione esplicita di rotazione sinistra. | `test_a1_math_03_inverse_formula_rotates_by_k_for_every_exponent`: oracolo indipendente per `k=0,1,2`, fattori asimmetrici, identità sia a sinistra sia a destra; la vecchia formula viene anche dimostrata falsa per `k=1,2`. | **VERIFIED FIXED: YES** |
| `A1-MATH-04` | Due passaggi della Guida collocavano ambiguamente `Jᵢ` fra gli stadi, non prima della distribuzione dello stesso stadio come stabilito da DP3=A. | `guide.s01.steps` e `guide.s05.intro`, IT/EN, ora descrivono esplicitamente `Jᵢ → MSC → Pᵢ` nello stadio `i`. | `test_a1_math_04_reversal_is_before_the_deal_of_the_same_stage`: stadio con `ε=1` e raccolta non commutante, confrontato con gli oracoli indipendenti pre-distribuzione e post-raccolta. | **VERIFIED FIXED: YES** |
| `A1-MATH-05` | A8 affermava la separabilità della trasformazione relativa senza la premessa che entrambi i mazzi gemelli derivassero da trasformazioni in `H`. | `guide.i5.other`, IT/EN: la trasformazione relativa è sempre definita per due mazzi con le stesse carte; appartiene a `H` soltanto sotto la premessa `T_A,T_B∈H`; per mazzi arbitrari la vista la verifica. | `test_a1_math_05_a8_separability_requires_twin_decks_from_h`: coppia di righe della Tavola con relativo in `H` e controesempio arbitrario `C1`, non separabile. | **VERIFIED FIXED: YES** |

## 3. Chiarimento delle tensioni di fonte

| tensione | chiarimento e superfici | verifica | esito |
|---|---|---|---|
| `A1-SRC-01` | `guide.i1.reversals`, IT/EN: l'Articolo base tratta il sottocaso senza rovesciamenti; l'Appendice D estende il modello con il rovesciamento prima della distribuzione ed è la convenzione operativa del programma. | Test testuale dedicato e regressione numerica `A1-MATH-04`. | **VERIFIED CLARIFIED: YES** |
| `A1-SRC-02` | `guide.i5.directions`, IT/EN: l'Articolo, Oss. 5.3, limita la ricostruzione alla classe separabile; il criterio per una permutazione arbitraria è il successivo Teor. 6.4 dell'Appendice D. | Test testuale dedicato; i riconoscitori diretto e per somme restano coperti dai test I5. | **VERIFIED CLARIFIED: YES** |
| `A1-SRC-03` | `guide.i3.errors`, IT/EN: A13 presenta il taglio come gesto esterno al gruppo; nel modello specifico su 27 posizioni la verifica esaustiva precisa le eccezioni `C9,C18∈H⊂Γ`, mentre le altre 24 traslazioni non banali sono fuori da `Γ`. | `test_a1_source_tensions_are_explicit_and_match_the_oracles` enumera tutte le 26 traslazioni non banali. | **VERIFIED CLARIFIED: YES** |

## 4. Modifiche e commit applicativi

- `34435eb` — `fix(A1): correct matrix and inverse formula statements`
- `d18c3bf` — `fix(A1): align Kronecker and reversal conventions`
- `4a1d8a5` — `fix(A1): qualify A8 and source scopes`
- `a1f25e5` — `test(A1): protect corrected mathematical statements`
- `a5f9b49` — `test(A1): verify inverse identities on both sides`

File applicativi e di test modificati:

- `gioco27/i18n.py`
- `gioco27/gui/explorer_tab.py`
- `gioco27/core/algebra.py` (sola documentazione interna delle convenzioni)
- `tests/test_i18n.py`
- `tests/test_a1_math_fixes.py`

## 5. Verifica automatica

La regressione A1 dedicata copre ogni issue e tutte le tensioni di fonte.
Prima della correzione la selezione di suite richiesta produceva
`201 passed, 6 skipped, 1 failed`: l'unico errore era l'inventario K0, che non
comprendeva ancora i due deliverable A1 appena aggiunti. L'inventario è stato
aggiornato meccanicamente senza modificare l'audit storico.

- Suite mirata A1 + compartimenti richiesti:
  `208 passed, 6 skipped in 6.68s`.
- Suite completa: `2057 passed, 320 skipped in 122.91s`.
- Nessun fallimento finale.

## 6. Integrità del filesystem

I due PDF fonte sono rimasti non tracciati, non rinominati e con le impronte
SHA-256 iniziali. Non sono stati creati artefatti di packaging e non è stato
eseguito alcun push.
