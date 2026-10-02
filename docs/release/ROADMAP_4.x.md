# Roadmap dopo la 4.0.0 — visualizzazioni strutturali a grafo

> **FUTURE RELEASE** — nulla di questo documento fa parte della 4.0.0.
> Destinazione indicativa: **4.1 / 4.2**. Le voci sono proposte, non impegni:
> ognuna richiede una decisione di prodotto prima dell'implementazione.

Nella 4.0.0 il Laboratorio mostra soltanto *piccoli grafi in forma testuale*
(elenchi di vertici e archi, nessun Canvas). Una release futura potrà
affiancare a quei dati una **visualizzazione grafica**, mantenendo il principio
della 4.0: la matematica resta nei servizi (`gioco27/services/`), la vista
legge soltanto i campi e li disegna, con alternative testuali accessibili.

## Visualizzazione strutturale a grafo

| # | Sviluppo possibile | Oggetto matematico | Dati già disponibili nella 4.0.0 |
|---|---|---|---|
| G1 | Grafi delle orbite di una trasformazione | orbite di ⟨T⟩ sulle 27 posizioni | decomposizione in cicli (`core.permutations`) |
| G2 | Decomposizione grafica in cicli | cicli disgiunti di T, tipo ciclico | Explorer, protocollo, Laboratorio (tipi) |
| G3 | Grafo di Cayley di H | 216 vertici, archi per generatori scelti | tavola di Cayley 216×216 (`core.group_theory`) |
| G4 | Grafi di sottogruppi selezionati | sottogruppi di H (centralizzatori, stabilizzatori, ⟨g⟩) | classi di coniugio e centro (Laboratorio) |
| G5 | I tre coset di H in Γ | Γ = H ⊔ H∘MSC ⊔ H∘MSC² (forma normale delle trasformazioni intermedie) | vista «Classi laterali e stadi» (Laboratorio) |
| G6 | Transizioni fra trasformazioni complete e intermedie | percorso H → H∘MSC → H∘MSC² → H lungo gli stadi | stadi delle Procedure (I1), classi laterali (I6) |
| G7 | Grafi generati da insiemi scelti di generatori | sottogruppo ⟨S⟩ ⊆ Γ per S scelto dall'utente | composizione in H e Γ (servizi I6) |
| G8 | Grafi delle fibre digitali | fibre F_{i,t} delle 27 posizioni per livello | somme di fibra, criterio delle somme (I5) |
| G9 | Trasporto delle fibre sotto T | fibra (i, t) → fibra (i, M_i(t)) | fattori locali del Riconoscimento (I5) |
| G10 | Confronto grafico fra T e T⁻¹ | stesso grafo con orientazione opposta | T e T⁻¹ nell'Explorer e nel Riconoscimento |
| G11 | Orbite di una carta o di una posizione | traiettoria di una carta lungo ⟨T⟩ o lungo una successione | successione L90 (J), flusso di una carta (I2) |
| G12 | Grafo delle relazioni fra tabelloni | righe della Tavola collegate da relazioni (inverso, coniugio, ritorno) | Tavola 216, tabellone inverso, ritorno (I2, J) |

## Vincoli da rispettare

* **Nessun cambiamento matematico**: i grafi visualizzano dati già calcolati e
  verificati (Tavola 216, H, Γ, fibre); non introducono nuove leggi.
* **Nomenclatura del libro**: H (216), Γ (648), S₂₇; fasi 1–3 nell'interfaccia,
  stadi h = 0, 1, 2 nel modello; posizioni 0–26.
* **Riferimenti al libro** solo tramite `gioco27/riferimenti.py`.
* **Accessibilità**: ogni grafo con un equivalente testuale (vertici, archi,
  legenda) e colori non come unico canale di informazione.
* **Prestazioni**: H ha 216 vertici e Γ 648; i grafi su S₂₇ non si enumerano.

## Fuori dalla 4.0.0

La 4.0.0 si chiude senza queste funzioni. Altre estensioni valutate durante la
Fase P e rimandate, a priorità bassa:

* la famiglia 𝒮_F del libro e la verifica ⟨𝒮_F⟩ = Γ nel Laboratorio;
* la forma canonica dell'Explorer per espressioni che contengono l'atomo J
  (J ∈ H: J = DCS ⊗ DCS ⊗ DCS, riga #215);
* la notazione Λ_{i,u} della lettura inversa.
