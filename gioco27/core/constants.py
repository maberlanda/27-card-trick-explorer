"""
Costanti simboliche del gioco delle 27 carte.
GEN3 (PERM3), MSC_PERM, P_OPTS, J_OPTS.
"""


# Le 6 permutazioni possibili per i fattori P su {0,1,2} = {S,C,D}
P_OPTS = ["SCD_U", "SDC_U", "CSD_U", "CDS_U", "DSC_U", "DCS_U"]
# Le 2 permutazioni possibili per i fattori J (identità o inversione)
J_OPTS = ["I_3", "R_U"]
ANY    = "*"   # wildcard nei filtri: significa "tutte le opzioni disponibili"

# Permutazioni su {0,1,2} come liste: [a,b,c] significa 0→a, 1→b, 2→c
# dove 0=S(sinistra), 1=C(centro), 2=D(destra)
# Relazioni algebriche utili:
#   SCD_U = I_3 (alias dell'identità)
#   SDC_U, CSD_U, DCS_U: involuzioni (X∘X = I)
#   CDS_U = DSC_U⁻¹  (inversi l'uno dell'altro)
PERM3 = {
    "SCD_U": [0, 1, 2],   # identità: S→S, C→C, D→D
    "SDC_U": [0, 2, 1],   # scambia C↔D
    "CSD_U": [1, 0, 2],   # scambia S↔C
    "CDS_U": [1, 2, 0],   # rotazione ciclica S→C, C→D, D→S
    "DSC_U": [2, 0, 1],   # rotazione inversa S→D, C→S, D→C
    "DCS_U": [2, 1, 0],   # scambia S↔D (involuzione)
}
PERM3_J = {
    "I_3": [0, 1, 2],   # identità: nessuna inversione
    "R_U": [2, 1, 0],   # inversione completa: 0↔2, 1 fisso
}

# ── Colori per i nomi delle matrici di GEN3 ──────────────────────────────────
PERM3_COLORS = {
    "SCD_U": "#006400",   # verde scuro
    "SDC_U": "#00008B",   # blu scuro
    "CSD_U": "#8B0000",   # rosso scuro
    "CDS_U": "#7B00A0",   # viola
    "DSC_U": "#B8520A",   # arancione scuro
    "DCS_U": "#006060",   # teal
}


# MSC 27×27: permutazione di "messa in colonne"
# Convenzione matriciale: MSC[row, col] = 1 significa che la carta in
# posizione col viene spostata in posizione row.
#
# In ternario: col = (i₂,i₁,i₀)  -->  row = (i₀,i₂,i₁)
# Quindi _MSC_PERM[col] = row = 9*i₀ + 3*i₂ + i₁
_MSC_PERM = [0,9,18,1,10,19,2,11,20,3,12,21,4,13,22,
             5,14,23,6,15,24,7,16,25,8,17,26]
