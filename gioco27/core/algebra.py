"""
Motore algebrico e simbolico: Parser, Rewriter, Evaluator, Controller.
"""
import csv
import numpy as np
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Tuple


# =============================================================================
# MOTORE ALGEBRICO E SIMBOLICO  (da gioco27_parser_explorer.py)
# =============================================================================

@dataclass
class RewriteStep:
    """
    Un singolo passo strutturato della traccia di riscrittura simbolica.

    Campi:
      rule       — nome/etichetta della regola applicata
      expr_before — rappresentazione testuale dell'espressione prima della regola
      expr_after  — rappresentazione testuale dell'espressione dopo la regola
      detail      — eventuale nota esplicativa aggiuntiva
    """
    rule:        str
    expr_before: str
    expr_after:  str
    detail:      str = ""
    state_after: str = ""   # espressione COMPLETA dopo il passo (la riscrittura
                            # in prima/dopo puo' riguardare solo un sottotermine)

    def format(self) -> str:
        """Formatta il passo come stringa leggibile multi-riga."""
        lines = [f"[{self.rule}]"]
        if self.detail:
            lines.append(f"  nota   : {self.detail}")
        lines.append(f"  prima  : {self.expr_before}")
        lines.append(f"  dopo   : {self.expr_after}")
        return "\n".join(lines)


@dataclass
class EvalStep:
    """
    Un singolo passo parziale della valutazione numerica.

    Campi:
      index       — indice del passo (0 = primo termine valutato)
      description — descrizione dell'operazione eseguita
      perm        — permutazione parziale risultante
      signature   — firma canonica parziale
    """
    index:       int
    description: str
    perm:        List[int]
    signature:   str = ""

    def perm_str(self) -> str:
        """Formato compatto della permutazione in righe da 9."""
        lines = []
        for s in range(0, len(self.perm), 9):
            chunk = self.perm[s:s+9]
            lines.append("  ".join(f"{v:2d}" for v in chunk))
        return "\n".join(lines)

    def format(self) -> str:
        """Formatta il passo come stringa leggibile multi-riga."""
        lines = [
            f"  Passo {self.index}: {self.description}",
            f"  perm  : {self.perm_str()}",
        ]
        if self.signature:
            lines.append(f"  firma : {self.signature[:60]}{'…' if len(self.signature)>60 else ''}")
        return "\n".join(lines)


@dataclass
class NormalFormInfo:
    """
    Informazioni strutturate sulla forma normale algebrica dell'espressione.

    Campi:
      kind              — tipo della forma: 'I', 'K', 'MSC', 'MSC^2',
                          'K o MSC', 'K o MSC^2', 'J', 'composta'
      msc_exponent      — esponente residuo di MSC modulo 3 (0, 1, 2)
      kron_factors_repr — lista delle rappresentazioni testuali dei fattori
                          del Kronecker residuo (3 elementi o vuota)
      kron_repr         — rappresentazione del blocco Kronecker completo
      symbolic          — forma normale come stringa simbolica leggibile
      already_normal    — True se l'espressione era già in forma normale
    """
    kind:               str       = "composta"
    msc_exponent:       int       = 0
    kron_factors_repr:  List[str] = field(default_factory=list)
    kron_repr:          str       = ""
    symbolic:           str       = ""
    already_normal:     bool      = False


# =============================================================================
# FORMA CANONICA GLOBALE
# =============================================================================

@dataclass
class CanonicalForm:
    """
    Forma canonica globale di un'espressione nel sottosistema {Kronecker, MSC}.

    Ogni espressione priva di J che si compone con Kronecker e MSC può essere
    ridotta a una e una sola forma canonica:

        K ∘ MSC^k       con K = P1 ⊗ P2 ⊗ P3,  k ∈ {0,1,2}

    Struttura interna:
      kron_factors — lista di tre permutazioni di tipo 3 (P1, P2, P3)
      msc_exp      — esponente residuo di MSC (0, 1 o 2)

    Metodi principali:
      compose(other)  — legge di composizione canonica senza passare per la matrice
      to_perm()       — calcola la permutazione di tipo 27 corrispondente
      symbolic()      — rappresentazione testuale leggibile
      signature()     — firma canonica della permutazione risultante

    Legge di composizione  (A, k1) ∘ (B, k2):
      Il blocco B deve essere "trasportato" attraverso MSC^k1 prima di comporsi
      con A.  Trasportare B di 1 passo significa ruotare i suoi fattori di 1 posto
      a sinistra (regola verificata: K ∘ MSC = MSC ∘ rot1(K)).
      Quindi:
        (A, k1) ∘ (B, k2)  =  (A ∘ rot_{k1}(B),  (k1 + k2) mod 3)

      dove rot_n denota la rotazione sinistra di n posizioni dei fattori.

    Nota: per la regola MSC ∘ K = rot2(K) ∘ MSC (rotazione sinistra di 2),
    il trasporto di K attraverso un MSC^k accumula rotazioni di k*2 mod 3 = k*2 mod 3.
    Poiché rot2 è l'inversa di rot1 in Z/3Z, e rot2^k = rot_{2k mod 3},
    la formula di composizione risultante è:
        kron_result = A ∘ rot_{2*k1 mod 3}(B)
    """

    kron_factors: List[List[int]]  # [P1, P2, P3], ciascuno di lunghezza 3
    msc_exp:      int              # 0, 1 o 2

    def __post_init__(self):
        # Normalizza msc_exp
        self.msc_exp = self.msc_exp % 3

    # ── Legge di composizione canonica ────────────────────────────────────────

    def compose(self, other: 'CanonicalForm') -> 'CanonicalForm':
        """
        Compone (self) ∘ (other) usando la legge canonica:

            (K1, k1) ∘ (K2, k2)  =  (K1 ∘ rot_{2*k1 mod 3}(K2),  (k1+k2) mod 3)

        Nessuna moltiplicazione di matrici 27×27: opera solo sui fattori di tipo 3
        e sugli interi k.

        La rotazione dei fattori di K2 di (2*k1 mod 3) posti verso sinistra
        corrisponde al trasporto di K2 attraverso MSC^k1:
          MSC^k1 ∘ K2 = rot_{2*k1}(K2) ∘ MSC^k1
        """
        # Numero di rotazioni sinistra da applicare a K2: 2*k1 mod 3
        rot_steps = (2 * self.msc_exp) % 3

        # Ruota i fattori di K2
        rotated_k2 = AlgebraEngine.rotate_kron_factors(other.kron_factors, rot_steps)

        # Componi fattore per fattore: (P1 ∘ Q1', P2 ∘ Q2', P3 ∘ Q3')
        new_factors = [
            AlgebraEngine.compose(self.kron_factors[i], rotated_k2[i])
            for i in range(3)
        ]

        # Nuovo esponente MSC
        new_exp = (self.msc_exp + other.msc_exp) % 3

        return CanonicalForm(kron_factors=new_factors, msc_exp=new_exp)

    # ── Conversione a permutazione 27×27 ─────────────────────────────────────

    def to_perm(self) -> List[int]:
        """
        Calcola la permutazione di tipo 27 corrispondente alla forma canonica.
        Usa la composizione: K ∘ MSC^k.
        """
        # Calcola il Kronecker
        kron_perm = AlgebraEngine.kronecker3(*self.kron_factors)

        if self.msc_exp == 0:
            return kron_perm

        # Calcola MSC^k
        msc = AlgebraEngine.MSC_PERM
        msc_k = list(AlgebraEngine.ID27)
        for _ in range(self.msc_exp):
            msc_k = AlgebraEngine.compose(msc, msc_k)

        # K ∘ MSC^k = K(MSC^k(x))
        return AlgebraEngine.compose(kron_perm, msc_k)

    # ── Rappresentazioni ─────────────────────────────────────────────────────

    def kron_factor_names(self) -> List[str]:
        """Nomi simbolici dei tre fattori del Kronecker."""
        return [_perm_to_gen3_name(f) for f in self.kron_factors]

    def kron_symbolic(self) -> str:
        """Rappresentazione simbolica del blocco Kronecker."""
        names = self.kron_factor_names()
        return f"({' ⊗ '.join(names)})"

    def symbolic(self) -> str:
        """Forma canonica come stringa simbolica leggibile."""
        kron_str = self.kron_symbolic()
        is_identity_kron = all(list(f) == [0, 1, 2] for f in self.kron_factors)

        if self.msc_exp == 0:
            return kron_str if not is_identity_kron else "I"
        elif self.msc_exp == 1:
            if is_identity_kron:
                return "MSC"
            return f"{kron_str} ∘ MSC"
        else:  # msc_exp == 2
            if is_identity_kron:
                return "MSC²"
            return f"{kron_str} ∘ MSC²"

    def signature(self) -> str:
        """Firma canonica della permutazione 27×27 corrispondente."""
        return AlgebraEngine.perm_signature(self.to_perm())

    def is_identity(self) -> bool:
        """True se questa forma canonica è l'identità."""
        return (self.msc_exp == 0
                and all(list(f) == [0, 1, 2] for f in self.kron_factors))

    @staticmethod
    def identity() -> 'CanonicalForm':
        """Restituisce la forma canonica identità."""
        return CanonicalForm(
            kron_factors=[[0,1,2],[0,1,2],[0,1,2]],
            msc_exp=0
        )

    @staticmethod
    def from_kron_and_exp(k1: List[int], k2: List[int], k3: List[int],
                           exp: int) -> 'CanonicalForm':
        """Factory: costruisce da tre fattori e un esponente."""
        return CanonicalForm(kron_factors=[k1, k2, k3], msc_exp=exp % 3)


def _build_canonical_form(nf_info: 'NormalFormInfo') -> Optional[CanonicalForm]:
    """
    Tenta di costruire una CanonicalForm a partire da una NormalFormInfo.
    Restituisce None se l'espressione non è nel sottosistema canonizzabile
    (es. contiene J, o è 'composta' con termini non ridotti).
    """
    kind = nf_info.kind
    if kind in ('J', 'composta'):
        return None

    # Identità
    if kind == 'I':
        return CanonicalForm.identity()

    # Solo MSC
    if kind == 'MSC':
        return CanonicalForm(kron_factors=[[0,1,2],[0,1,2],[0,1,2]], msc_exp=1)
    if kind == 'MSC^2':
        return CanonicalForm(kron_factors=[[0,1,2],[0,1,2],[0,1,2]], msc_exp=2)

    # Caso con Kronecker: ricava i tre fattori
    msc_exp = nf_info.msc_exponent
    if not nf_info.kron_factors_repr:
        return None

    # I fattori sono stringhe simboliche; le convertiamo in permutazioni numeriche
    factors_perm = []
    for name in nf_info.kron_factors_repr:
        name = name.strip()
        if name in AlgebraEngine.GEN3:
            factors_perm.append(list(AlgebraEngine.GEN3[name]))
        else:
            # Potrebbe essere "[a,b,c]" — tenta parsing
            try:
                vals = [int(x) for x in name.strip('[]').split(',')]
                if len(vals) == 3:
                    factors_perm.append(vals)
                else:
                    return None
            except Exception:
                return None

    if len(factors_perm) != 3:
        return None

    return CanonicalForm(kron_factors=factors_perm, msc_exp=msc_exp)



class AlgebraEngine:
    """
    Gestisce tutte le operazioni sulle permutazioni.

    Le permutazioni sono rappresentate come liste Python [p0, p1, ..., pN-1]
    dove p[i] = j significa "l'elemento in posizione i va in posizione j".
    """

    # --- Permutazioni base di tipo 3 (generatori di S3) ---

    GEN3 = {
        # Identità: S→S, C→C, D→D
        "SCD_U": [0, 1, 2],
        # Scambio C↔D
        "SDC_U": [0, 2, 1],
        # Scambio S↔C
        "CSD_U": [1, 0, 2],
        # Ciclo S→C→D→S
        "CDS_U": [1, 2, 0],
        # Ciclo inverso S→D→C→S
        "DSC_U": [2, 0, 1],
        # Scambio S↔D
        "DCS_U": [2, 1, 0],
    }

    # --- Permutazioni base di tipo 27 ---

    # MSC: distribuzione a 3 colonne (permutazione del mescolamento principale)
    MSC_PERM = [
        0,  9, 18,  1, 10, 19,  2, 11, 20,
        3, 12, 21,  4, 13, 22,  5, 14, 23,
        6, 15, 24,  7, 16, 25,  8, 17, 26
    ]

    # J: inversione completa del mazzo
    J_PERM = list(range(26, -1, -1))  # [26, 25, ..., 0]

    # Identità di tipo 27
    ID27 = list(range(27))
    # Identità di tipo 3
    ID3  = [0, 1, 2]

    @staticmethod
    def compose(a: List[int], b: List[int]) -> List[int]:
        """
        Composizione a ∘ b = a(b(x)).
        Prima si applica b, poi a.
        """
        return [a[b[i]] for i in range(len(b))]

    @staticmethod
    def identity(n: int) -> List[int]:
        """Restituisce la permutazione identità di dimensione n."""
        return list(range(n))

    @staticmethod
    def inverse_perm(p: List[int]) -> List[int]:
        """Calcola la permutazione inversa di p."""
        inv = [0] * len(p)
        for i, v in enumerate(p):
            inv[v] = i
        return inv

    @staticmethod
    def transpose_perm(p: List[int]) -> List[int]:
        """
        Per una matrice di permutazione, la trasposta coincide con l'inversa.
        """
        return AlgebraEngine.inverse_perm(p)

    @staticmethod
    def kronecker3(p1: List[int], p2: List[int], p3: List[int]) -> List[int]:
        """
        Prodotto di Kronecker di tre permutazioni 3×3.

        La convenzione adottata è coerente con il programma C:
        Le 27 posizioni sono indicizzate come i*9 + j*3 + k (i,j,k ∈ {0,1,2}).
        Il Kronecker (p1 ⊗ p2 ⊗ p3) mappa:
            (i, j, k)  →  (p1[i], p2[j], p3[k])
        """
        result = [0] * 27
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    src = i * 9 + j * 3 + k
                    dst = p1[i] * 9 + p2[j] * 3 + p3[k]
                    result[src] = dst
        return result

    @staticmethod
    def perm_to_matrix(p: List[int]) -> np.ndarray:
        """Converte un vettore di permutazione in matrice 0/1.

        Convenzione colonnare (matrice che agisce su vettori colonna):
            P e_i = e_{p[i]}   ==>   M[p[i], i] = 1
        cioè la 1 sta in riga = arrivo p[i], colonna = partenza i.
        Con questa convenzione il prodotto matriciale corrisponde alla
        composizione:  P_p @ P_q = P_{p∘q}  con (p∘q)[i] = p[q[i]].
        """
        n = len(p)
        M = np.zeros((n, n), dtype=int)
        for i, v in enumerate(p):
            M[v][i] = 1          # M[p[i], i] = 1  (NON M[i, p[i]])
        return M

    @staticmethod
    def perm_signature(p: List[int]) -> str:
        """Firma canonica: stringa CSV del vettore di permutazione."""
        return ",".join(str(x) for x in p)

    @staticmethod
    def find_period(p: List[int], max_iter: int = 200) -> Optional[int]:
        """
        Calcola il periodo della permutazione p:
        il minimo k > 0 tale che p^k = identità.
        Restituisce None se non trovato entro max_iter.
        """
        n = len(p)
        current = list(p)
        identity = list(range(n))
        for k in range(1, max_iter + 1):
            if current == identity:
                return k
            current = AlgebraEngine.compose(current, p)
        return None

    @staticmethod
    def rotate_kron_factors(factors: List[List[int]], steps: int = 1) -> List[List[int]]:
        """
        Ruota ciclicamente verso sinistra i fattori del Kronecker.
        steps=1: (p1, p2, p3) → (p2, p3, p1)
        steps=2: (p1, p2, p3) → (p3, p1, p2)
        """
        n = len(factors)
        s = steps % n
        return factors[s:] + factors[:s]


# =============================================================================
# RAPPRESENTAZIONE SIMBOLICA (AST)
# =============================================================================

class SymbolicExpr:
    """
    Nodo dell'albero sintattico dell'espressione.

    kind può essere:
      'atom'    — simbolo terminale (MSC, J, SCD_U, ...)
      'compose' — composizione A ∘ B
      'kron'    — prodotto di Kronecker (esattamente 3 fattori di tipo 3)
      'value'   — nodo foglia con valore già calcolato (permutazione numerica)
    """
    def __init__(self, kind: str, value=None, children=None,
                 name: str = "", ptype: int = 0):
        self.kind     = kind
        self.value    = value      # vettore di permutazione (List[int])
        self.children = children or []
        self.name     = name       # nome simbolico per la normalizzazione
        self.ptype    = ptype      # 3 o 27

    def __repr__(self):
        if self.kind == 'atom':
            return self.name
        if self.kind == 'compose':
            inner = " ∘ ".join(repr(c) for c in self.children)
            return f"({inner})"
        if self.kind == 'kron':
            inner = " ⊗ ".join(repr(c) for c in self.children)
            return f"({inner})"
        if self.kind == 'value':
            return f"[perm:{self.ptype}]"
        return f"<{self.kind}>"

    def clone(self) -> 'SymbolicExpr':
        """Copia profonda del nodo."""
        children_copy = [c.clone() for c in self.children]
        return SymbolicExpr(
            self.kind,
            value=list(self.value) if self.value is not None else None,
            children=children_copy,
            name=self.name,
            ptype=self.ptype
        )


# =============================================================================
# HELPER GLOBALE: nome simbolico di una permutazione di tipo 3
# =============================================================================

def _perm_to_gen3_name(perm: List[int]) -> str:
    """
    Cerca tra i generatori GEN3 quello con la stessa permutazione.
    Se non trovato, restituisce la stringa '[perm:3]'.
    """
    for name, val in AlgebraEngine.GEN3.items():
        if list(perm) == list(val):
            return name
    return f"[{','.join(str(x) for x in perm)}]"


# =============================================================================
# REWRITER SIMBOLICO (NORMALIZZATORE)
# =============================================================================

class Rewriter:
    """
    Applica le regole di semplificazione simbolica.

    Regole implementate:
      R1: MSC ∘ (P1⊗P2⊗P3) = (P3⊗P1⊗P2) ∘ MSC   (trasporto: rotazione sinistra di 2 = destra di 1)
      R2: MSC² ∘ (P1⊗P2⊗P3) = (P2⊗P3⊗P1) ∘ MSC²  (trasporto: rotazione sinistra di 1)
      R3: MSC³ = I
      R4: I ∘ X = X ∘ I = X   (eliminazione identità)

    La regola di trasporto è verificata algebricamente:
      MSC ∘ K(P1,P2,P3) = K(P3,P1,P2) ∘ MSC    [rotazione sinistra di 2]
      K ∘ MSC           = MSC ∘ K(P2,P3,P1)    [rotazione sinistra di 1]

    La forma normale prodotta è:
      (fattori Kronecker composti) ∘ MSC^k
    quando possibile, altrimenti l'espressione composta valutata numericamente.
    """

    def __init__(self, engine: AlgebraEngine):
        self.eng = engine

    # -------------------------------------------------------------------------
    # Normalizzazione top-level
    # -------------------------------------------------------------------------

    def normalize(self, expr: SymbolicExpr) -> Tuple[str, SymbolicExpr]:
        """
        Normalizza l'espressione.
        Restituisce (descrizione_testuale_forma_normale, expr_normalizzata).
        """
        steps = []

        # Passo 1: appiattire le composizioni annidate
        flat = self._flatten_compose(expr)
        steps.append("Composizione appiattita")

        # Passo 2: tentare di raccogliere MSC a destra
        collected, changed = self._collect_msc_right(flat)
        if changed:
            steps.append("MSC raccolto a destra (regola di trasporto)")

        # Passo 3: ridurre le potenze di MSC (MSC^3 = I)
        reduced, msc_steps = self._reduce_msc_powers(collected)
        if msc_steps:
            steps.append(f"Potenza MSC ridotta (MSC^3=I): {msc_steps}")

        # Passo 4: comporre i fattori Kronecker rimasti a sinistra
        final, kron_steps = self._compose_kron_sequence(reduced)
        if kron_steps:
            steps.append("Fattori Kronecker composti")

        description = " → ".join(steps) if steps else "Nessuna semplificazione applicata"
        return description, final

    # -------------------------------------------------------------------------
    # Appiattimento composizioni
    # -------------------------------------------------------------------------

    def _flatten_compose(self, expr: SymbolicExpr) -> SymbolicExpr:
        """
        Trasforma composizioni annidate in una lista piatta:
        (A ∘ (B ∘ C)) → [A, B, C]
        """
        if expr.kind != 'compose':
            return expr

        flat_children = []
        for child in expr.children:
            flat_child = self._flatten_compose(child)
            if flat_child.kind == 'compose':
                flat_children.extend(flat_child.children)
            else:
                flat_children.append(flat_child)

        return SymbolicExpr('compose', children=flat_children, ptype=expr.ptype)

    # -------------------------------------------------------------------------
    # Trasporto di MSC verso destra
    # -------------------------------------------------------------------------

    def _collect_msc_right(self, expr: SymbolicExpr) -> Tuple[SymbolicExpr, bool]:
        """
        Tenta di raccogliere tutti gli atomi MSC verso la destra della composizione
        applicando ripetutamente la regola di trasporto:
            MSC ∘ K = rotate(K) ∘ MSC
        dove rotate() ruota di 1 posto a sinistra i fattori del Kronecker.
        """
        if expr.kind != 'compose':
            return expr, False

        changed_total = False
        terms = [c.clone() for c in expr.children]

        # Applica ripetutamente la regola finché non ci sono più MSC da spostare
        made_progress = True
        while made_progress:
            made_progress = False
            new_terms = []
            i = 0
            while i < len(terms):
                t = terms[i]
                # Se è MSC e c'è un Kronecker dopo di lui
                if t.kind == 'atom' and t.name == 'MSC' and i + 1 < len(terms):
                    next_t = terms[i + 1]
                    if next_t.kind == 'kron':
                        # Applica R1: MSC ∘ K(P1,P2,P3) → K(P3,P1,P2) ∘ MSC
                        # Rotazione sinistra di 2 (equivalente a destra di 1)
                        # Verificata algebricamente: MSC ∘ K == rot2(K) ∘ MSC
                        rotated_k = SymbolicExpr(
                            'kron',
                            children=AlgebraEngine.rotate_kron_factors(next_t.children, 2),
                            ptype=27
                        )
                        new_terms.append(rotated_k)
                        new_terms.append(t)   # MSC viene dopo
                        i += 2
                        made_progress = True
                        changed_total = True
                        continue
                new_terms.append(t)
                i += 1
            terms = new_terms

        if len(terms) == 1:
            return terms[0], changed_total

        result = SymbolicExpr('compose', children=terms, ptype=27)
        return result, changed_total

    # -------------------------------------------------------------------------
    # Riduzione potenze MSC
    # -------------------------------------------------------------------------

    def _reduce_msc_powers(self, expr: SymbolicExpr) -> Tuple[SymbolicExpr, str]:
        """
        Riduce sequenze di MSC consecutivi:
            MSC^3 = I  →  elimina dal termine
            MSC^2 resta
        Restituisce l'espressione ridotta e una stringa descrittiva delle riduzioni.
        """
        if expr.kind != 'compose':
            return expr, ""

        steps_desc = []
        terms = list(expr.children)
        new_terms = []
        i = 0
        while i < len(terms):
            t = terms[i]
            if t.kind == 'atom' and t.name == 'MSC':
                # Conta quanti MSC consecutivi ci sono
                count = 0
                j = i
                while j < len(terms) and terms[j].kind == 'atom' and terms[j].name == 'MSC':
                    count += 1
                    j += 1
                reduced_count = count % 3
                if count != reduced_count:
                    steps_desc.append(f"MSC^{count} → MSC^{reduced_count}")
                for _ in range(reduced_count):
                    new_terms.append(SymbolicExpr('atom', name='MSC', ptype=27,
                                                  value=list(AlgebraEngine.MSC_PERM)))
                i = j
            else:
                new_terms.append(t)
                i += 1

        # Rimuovi identità rimanenti (MSC^0)
        new_terms = [t for t in new_terms if not (t.kind == 'atom' and t.name == 'I')]

        if not new_terms:
            id_node = SymbolicExpr('atom', name='I', ptype=27,
                                   value=list(AlgebraEngine.ID27))
            return id_node, " | ".join(steps_desc)

        if len(new_terms) == 1:
            return new_terms[0], " | ".join(steps_desc)

        return SymbolicExpr('compose', children=new_terms, ptype=27), " | ".join(steps_desc)

    # -------------------------------------------------------------------------
    # Composizione dei Kronecker consecutivi
    # -------------------------------------------------------------------------

    def _compose_kron_sequence(self, expr: SymbolicExpr, notes=None) -> Tuple[SymbolicExpr, bool]:
        """
        Compone numericamente Kronecker consecutivi nella sequenza composizione.
        Due Kronecker K1 ∘ K2 vengono uniti in K(P1∘P1', P2∘P2', P3∘P3').

        Se `notes` è una lista, vi aggiunge una riga esplicativa per ogni
        fusione, con il calcolo di ciascun fattore (es. «SCD_U ∘ DCS_U = DCS_U»).
        """
        if expr.kind != 'compose':
            return expr, False

        terms = list(expr.children)
        changed = False
        made_progress = True
        while made_progress:
            made_progress = False
            new_terms = []
            i = 0
            while i < len(terms):
                t = terms[i]
                if (t.kind == 'kron' and i + 1 < len(terms)
                        and terms[i+1].kind == 'kron'):
                    # Componi i due Kronecker: (K1 ∘ K2) fattore per fattore
                    k1, k2 = t, terms[i+1]
                    composed_children = []
                    for f1, f2 in zip(k1.children, k2.children):
                        v1 = f1.value if f1.value else AlgebraEngine.GEN3.get(f1.name, [0,1,2])
                        v2 = f2.value if f2.value else AlgebraEngine.GEN3.get(f2.name, [0,1,2])
                        comp_val = AlgebraEngine.compose(v1, v2)
                        # Cerca se corrisponde a un generatore noto
                        sym_name = _perm_to_gen3_name(comp_val)
                        child = SymbolicExpr('atom', name=sym_name, ptype=3, value=comp_val)
                        composed_children.append(child)
                    merged = SymbolicExpr('kron', children=composed_children, ptype=27)
                    if notes is not None:
                        per_factor = "  |  ".join(
                            f"{f1.name} ∘ {f2.name} = {c.name}"
                            for f1, f2, c in zip(k1.children, k2.children,
                                                 composed_children))
                        notes.append(f"{repr(k1)} ∘ {repr(k2)} → {repr(merged)}\n"
                                     f"      fattore per fattore:  {per_factor}")
                    new_terms.append(merged)
                    i += 2
                    made_progress = True
                    changed = True
                else:
                    new_terms.append(t)
                    i += 1
            terms = new_terms

        if len(terms) == 1:
            return terms[0], changed
        return SymbolicExpr('compose', children=terms, ptype=27), changed

    # -------------------------------------------------------------------------
    # Normalizzazione con traccia completa
    # -------------------------------------------------------------------------

    def normalize_with_trace(self, expr: SymbolicExpr) \
            -> Tuple[SymbolicExpr, List[RewriteStep], NormalFormInfo]:
        """
        Normalizza l'espressione e produce una traccia strutturata completa.

        Restituisce:
          (ast_normalizzato, lista_passi_RewriteStep, NormalFormInfo)

        Ogni passo registra: regola, espressione prima, espressione dopo, note.
        """
        trace: List[RewriteStep] = []

        expr_in = repr(expr)

        # ── Passo 0: stato iniziale ────────────────────────────────────────
        trace.append(RewriteStep(
            rule="Espressione iniziale",
            expr_before="—",
            expr_after=expr_in,
            detail=("Input originale dopo il parsing.\n"
                    "      La composizione ∘ si legge da DESTRA a SINISTRA: il termine più a destra agisce per primo sul mazzo."),
            state_after=expr_in,
        ))

        # ── Passo 1: appiattimento composizioni ───────────────────────────
        flat = self._flatten_compose(expr)
        flat_str = repr(flat)
        if flat_str != expr_in:
            trace.append(RewriteStep(
                rule="Appiattimento composizioni",
                expr_before=expr_in,
                expr_after=flat_str,
                detail=("La composizione è associativa: le parentesi attorno a ∘ "
                        "non cambiano il risultato e vengono eliminate."),
                state_after=flat_str,
            ))
        current = flat
        current_str = flat_str


        # ── Passo 1b: rimozione degli atomi I ─────────────────────────────
        # I ∘ X = X ∘ I = X. Va fatto PRIMA del trasporto MSC: una I
        # frapposta (es. MSC ∘ I ∘ K) impedirebbe di riconoscere l'adiacenza
        # MSC∘K e lascerebbe l'espressione solo parzialmente normalizzata,
        # con fattori errati nella forma algebrica (bug v2.8.1).
        if current.kind == 'compose':
            kept = [t for t in current.children
                    if not (t.kind == 'atom' and t.name == 'I')]
            if len(kept) != len(current.children):
                if not kept:
                    cleaned = SymbolicExpr('atom', name='I', ptype=27,
                                           value=list(AlgebraEngine.ID27))
                elif len(kept) == 1:
                    cleaned = kept[0]
                else:
                    cleaned = SymbolicExpr('compose', children=kept, ptype=27)
                trace.append(RewriteStep(
                    rule="Rimozione identità",
                    expr_before=current_str,
                    expr_after=repr(cleaned),
                    detail="I ∘ X = X ∘ I = X: gli atomi I vengono eliminati.",
                    state_after=repr(cleaned),
                ))
                current = cleaned
                current_str = repr(current)
        # ── Passi 2+: trasporto di MSC attraverso i Kronecker ─────────────
        step_num = 0
        made_progress = True
        while made_progress:
            made_progress = False
            if current.kind != 'compose':
                break
            terms = list(current.children)
            new_terms = []
            i = 0
            while i < len(terms):
                t = terms[i]
                if (t.kind == 'atom' and t.name == 'MSC'
                        and i + 1 < len(terms)
                        and terms[i+1].kind == 'kron'):
                    k_node = terms[i+1]
                    rot_children = AlgebraEngine.rotate_kron_factors(
                        k_node.children, 2)
                    rotated_k = SymbolicExpr('kron', children=rot_children,
                                             ptype=27)
                    step_num += 1
                    before_expr = repr(SymbolicExpr('compose',
                        children=[t, k_node], ptype=27))
                    after_expr  = repr(SymbolicExpr('compose',
                        children=[rotated_k, t], ptype=27))
                    new_terms.append(rotated_k)
                    new_terms.append(t)
                    # stato completo dopo questo scambio: la parte già
                    # processata + i termini ancora da esaminare
                    state_terms = new_terms + terms[i+2:]
                    state_expr = (state_terms[0] if len(state_terms) == 1
                                  else SymbolicExpr('compose',
                                                    children=state_terms,
                                                    ptype=27))
                    names = [c.name or "?" for c in k_node.children]
                    if names[0] == names[1] == names[2]:
                        rot_note = "  — fattori tutti uguali: il blocco resta identico."
                    else:
                        rot_note = "."
                    detail_r1 = (
                        "Regola R1:  MSC ∘ (a ⊗ b ⊗ c)  =  (c ⊗ a ⊗ b) ∘ MSC\n"
                        "      MSC ruota le cifre ternarie della posizione, quindi nello scavalcarlo i fattori ruotano: l'ultimo passa in testa.\n"
                        f"      Qui (a,b,c) = ({names[0]}, {names[1]}, {names[2]}) "
                        f"→ ({names[2]}, {names[0]}, {names[1]}){rot_note}\n"
                        "      Obiettivo: spostare tutte le MSC a destra, per poter fondere i blocchi Kronecker rimasti adiacenti.")
                    trace.append(RewriteStep(
                        rule=f"Trasporto MSC (passo {step_num})",
                        expr_before=before_expr,
                        expr_after=after_expr,
                        detail=detail_r1,
                        state_after=repr(state_expr),
                    ))
                    i += 2
                    made_progress = True
                    continue
                new_terms.append(t)
                i += 1
            if made_progress:
                current = (new_terms[0] if len(new_terms) == 1
                           else SymbolicExpr('compose', children=new_terms,
                                             ptype=27))
                current_str = repr(current)

        # ── Passo: riduzione potenze MSC (MSC^3 = I) ─────────────────────
        if current.kind == 'compose':
            terms = list(current.children)
            new_terms = []
            reduction_notes = []
            i = 0
            while i < len(terms):
                t = terms[i]
                if t.kind == 'atom' and t.name == 'MSC':
                    count = 0
                    j = i
                    while j < len(terms) and terms[j].kind=='atom' and terms[j].name=='MSC':
                        count += 1; j += 1
                    reduced = count % 3
                    if count != reduced:
                        reduction_notes.append(
                            f"MSC^{count} → MSC^{reduced} (MSC^3=I)")
                    for _ in range(reduced):
                        new_terms.append(SymbolicExpr('atom', name='MSC',
                            ptype=27, value=list(AlgebraEngine.MSC_PERM)))
                    i = j
                else:
                    new_terms.append(t); i += 1
            new_terms = [t for t in new_terms
                         if not (t.kind=='atom' and t.name=='I')]
            if not new_terms:
                new_terms = [SymbolicExpr('atom', name='I', ptype=27,
                                          value=list(AlgebraEngine.ID27))]
            reduced_expr = (new_terms[0] if len(new_terms)==1
                            else SymbolicExpr('compose', children=new_terms,
                                              ptype=27))
            if reduction_notes:
                trace.append(RewriteStep(
                    rule="Riduzione potenze MSC",
                    expr_before=current_str,
                    expr_after=repr(reduced_expr),
                    detail=("Regola R2:  MSC ∘ MSC ∘ MSC = I\n"
                            "      (tre distribuzioni in colonne riportano il mazzo all'ordine di partenza: l'esponente conta mod 3)\n"
                            "      " + "  |  ".join(reduction_notes)),
                    state_after=repr(reduced_expr),
                ))
            current = reduced_expr
            current_str = repr(current)

        # ── Passo: composizione Kronecker consecutivi ─────────────────────
        kron_notes = []
        composed, changed_kron = self._compose_kron_sequence(current, notes=kron_notes)
        if changed_kron:
            detail = ("Regola R3:  (a ⊗ b ⊗ c) ∘ (d ⊗ e ⊗ f)  =  (a∘d ⊗ b∘e ⊗ c∘f)\n"
                      "      (due blocchi Kronecker adiacenti si fondono componendo i fattori posizione per posizione)")
            if kron_notes:
                detail += "\n      " + "\n      ".join(kron_notes)
            trace.append(RewriteStep(
                rule="Composizione Kronecker consecutivi",
                expr_before=current_str,
                expr_after=repr(composed),
                detail=detail,
                state_after=repr(composed),
            ))
            current = composed
            current_str = repr(current)

        # ── Passo finale: forma normale ────────────────────────────────────
        nf_info = self._analyze_normal_form(current)
        trace.append(RewriteStep(
            rule="Forma normale finale",
            expr_before=current_str,
            expr_after=nf_info.symbolic,
            detail=(f"Tipo: {nf_info.kind}  |  esponente MSC residuo: "
                    f"{nf_info.msc_exponent} (mod 3)\n"
                    "      Forma normale K ∘ MSCᵏ: un unico blocco Kronecker seguito da k ∈ {0,1,2} mescolamenti.\n"
                    "      Due espressioni sono equivalenti se e solo se hanno la stessa forma normale."),
            state_after=nf_info.symbolic,
        ))

        return current, trace, nf_info

    # -------------------------------------------------------------------------
    # Analisi della forma normale
    # -------------------------------------------------------------------------

    def _analyze_normal_form(self, expr: SymbolicExpr) -> NormalFormInfo:
        """
        Analizza l'AST normalizzato e produce una NormalFormInfo strutturata.
        Distingue: I, MSC, MSC^2, K, K∘MSC, K∘MSC^2, J, composta.
        """
        info = NormalFormInfo()
        info.already_normal = True

        # Caso: atomo singolo
        if expr.kind == 'atom':
            if expr.name == 'I':
                info.kind = 'I'; info.msc_exponent = 0
                info.symbolic = 'I'; return info
            if expr.name == 'MSC':
                info.kind = 'MSC'; info.msc_exponent = 1
                info.symbolic = 'MSC'; return info
            if expr.name == 'J':
                info.kind = 'J'; info.msc_exponent = 0
                info.symbolic = 'J'; return info

        # Caso: Kronecker singolo
        if expr.kind == 'kron':
            info.kind = 'K'; info.msc_exponent = 0
            info.kron_factors_repr = [repr(c) for c in expr.children]
            info.kron_repr = repr(expr)
            info.symbolic  = info.kron_repr
            return info

        # Caso: composizione — analizza i termini
        if expr.kind == 'compose':
            terms = expr.children
            kron_terms = [t for t in terms if t.kind == 'kron']
            msc_terms  = [t for t in terms if t.kind == 'atom' and t.name == 'MSC']
            other      = [t for t in terms
                          if not (t.kind == 'kron'
                                  or (t.kind == 'atom' and t.name in ('MSC','I')))]

            msc_exp = len(msc_terms) % 3
            info.msc_exponent = msc_exp

            # La fusione fattore-per-fattore dei Kronecker (sotto) è valida
            # solo se NESSUN kron compare dopo un MSC: i termini devono avere
            # la forma K ∘ ... ∘ K ∘ MSC^k. Se un kron segue un MSC,
            # l'espressione NON è in forma normale e fonderli ignorando l'MSC
            # darebbe fattori errati (bug v2.8.1).
            seen_msc = False
            kron_after_msc = False
            for t in terms:
                if t.kind == 'atom' and t.name == 'MSC':
                    seen_msc = True
                elif t.kind == 'kron' and seen_msc:
                    kron_after_msc = True
                    break

            if not other and not kron_after_msc:
                # Solo Kronecker + MSC
                if kron_terms:
                    # Componi tutti i Kronecker in uno solo (numerico)
                    composed_k = kron_terms[0]
                    for kt in kron_terms[1:]:
                        # componi fattore per fattore
                        new_children = []
                        for f1, f2 in zip(composed_k.children, kt.children):
                            v1 = (f1.value if f1.value
                                  else AlgebraEngine.GEN3.get(f1.name, [0,1,2]))
                            v2 = (f2.value if f2.value
                                  else AlgebraEngine.GEN3.get(f2.name, [0,1,2]))
                            cv = AlgebraEngine.compose(v1, v2)
                            nm = _perm_to_gen3_name(cv)
                            new_children.append(
                                SymbolicExpr('atom', name=nm, ptype=3, value=cv))
                        composed_k = SymbolicExpr('kron',
                                                   children=new_children, ptype=27)
                    info.kron_factors_repr = [repr(c) for c in composed_k.children]
                    info.kron_repr = repr(composed_k)
                    if msc_exp == 0:
                        info.kind = 'K'
                        info.symbolic = info.kron_repr
                    elif msc_exp == 1:
                        info.kind = 'K o MSC'
                        info.symbolic = f"{info.kron_repr} ∘ MSC"
                    else:
                        info.kind = 'K o MSC^2'
                        info.symbolic = f"{info.kron_repr} ∘ MSC²"
                else:
                    # Solo MSC
                    if msc_exp == 0:
                        info.kind = 'I'; info.symbolic = 'I'
                    elif msc_exp == 1:
                        info.kind = 'MSC'; info.symbolic = 'MSC'
                    else:
                        info.kind = 'MSC^2'; info.symbolic = 'MSC²'
            else:
                # Forma non riducibile a K ∘ MSC^k
                info.kind = 'composta'
                info.already_normal = False
                info.symbolic = repr(expr)

            return info

        # Fallback
        info.kind = 'composta'; info.symbolic = repr(expr)
        return info


# =============================================================================
# PARSER
# =============================================================================

class ParseError(Exception):
    """Errore di parsing con messaggio leggibile."""


class Token:
    """Un token del lexer."""
    def __init__(self, kind: str, value: str):
        self.kind  = kind   # 'ATOM', 'COMPOSE', 'KRON', 'LPAREN', 'RPAREN', 'EOF'
        self.value = value

    def __repr__(self):
        return f"Token({self.kind},{self.value!r})"


class Lexer:
    """Tokenizzatore per le espressioni simboliche."""

    # R_U e I_3 sono i nomi dei fattori J usati nella notazione di gioco
    # (Stage = P o MSC o J): numericamente R_U = DCS_U e I_3 = SCD_U, ma
    # vengono accettati come alias di tipo 3 per poter incollare nell'Explorer
    # le espressioni di turno cosi' come appaiono nell'Analisi.
    VALID_ATOMS = (set(AlgebraEngine.GEN3.keys())
                   | {'MSC', 'J', 'I'} | {'R_U', 'I_3'})

    def tokenize(self, text: str) -> List[Token]:
        """Converte la stringa in lista di token."""
        tokens = []
        i = 0
        text = text.strip()
        while i < len(text):
            c = text[i]

            # Salta spazi
            if c.isspace():
                i += 1
                continue

            # Parentesi (le quadre, usate nelle Stage string dell'Analisi,
            # sono equivalenti alle tonde)
            if c in '([':
                tokens.append(Token('LPAREN', '('))
                i += 1
                continue
            if c in ')]':
                tokens.append(Token('RPAREN', ')'))
                i += 1
                continue

            # Operatori Unicode
            if c == '∘':
                tokens.append(Token('COMPOSE', '∘'))
                i += 1
                continue
            if c == '⊗':
                tokens.append(Token('KRON', '⊗'))
                i += 1
                continue

            # @ come alias ASCII di ∘ (composizione)
            if c == '@':
                tokens.append(Token('COMPOSE', '@'))
                i += 1
                continue

            # Identificatori e operatori ASCII
            if c.isalpha() or c == '_':
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                    j += 1
                word = text[i:j]

                if word == 'o':
                    tokens.append(Token('COMPOSE', 'o'))
                elif word == 'x':
                    tokens.append(Token('KRON', 'x'))
                elif word in self.VALID_ATOMS:
                    tokens.append(Token('ATOM', word))
                else:
                    raise ParseError(
                        f"Simbolo sconosciuto: '{word}'\n"
                        f"Simboli validi: {sorted(self.VALID_ATOMS)}"
                    )
                i = j
                continue

            raise ParseError(f"Carattere non riconosciuto: '{c}' (posizione {i})")

        tokens.append(Token('EOF', ''))
        return tokens


class Parser:
    """
    Parser discendente ricorsivo per le espressioni simboliche.

    Grammatica (precedenza crescente verso il basso):
      expr   ::= term (COMPOSE term)*
      term   ::= factor (KRON factor)*
      factor ::= ATOM | '(' expr ')'
    """

    def __init__(self, engine: AlgebraEngine):
        self.eng = engine
        self.lexer = Lexer()
        self.tokens: List[Token] = []
        self.pos = 0

    def parse(self, text: str) -> SymbolicExpr:
        """Entry point: parsa il testo e restituisce l'AST."""
        self.tokens = self.lexer.tokenize(text)
        self.pos = 0
        result = self._parse_expr()
        if self._current().kind != 'EOF':
            raise ParseError(
                f"Token inatteso dopo la fine dell'espressione: "
                f"'{self._current().value}'"
            )
        return result

    # -------------------------------------------------------------------------
    # Helpers di navigazione
    # -------------------------------------------------------------------------

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _consume(self, kind: str = None) -> Token:
        tok = self._current()
        if kind and tok.kind != kind:
            raise ParseError(
                f"Atteso '{kind}', trovato '{tok.kind}' ('{tok.value}')"
            )
        self.pos += 1
        return tok

    # -------------------------------------------------------------------------
    # Produzione di nodi AST con tipo
    # -------------------------------------------------------------------------

    def _make_atom(self, name: str) -> SymbolicExpr:
        """Crea un nodo atomo con il valore e il tipo corretti."""
        if name == 'MSC':
            return SymbolicExpr('atom', name='MSC', ptype=27,
                                value=list(AlgebraEngine.MSC_PERM))
        if name == 'J':
            return SymbolicExpr('atom', name='J', ptype=27,
                                value=list(AlgebraEngine.J_PERM))
        if name == 'I':
            return SymbolicExpr('atom', name='I', ptype=27,
                                value=list(AlgebraEngine.ID27))
        if name == 'R_U':   # alias di gioco: inversione su {0,1,2} (= DCS_U)
            return SymbolicExpr('atom', name='DCS_U', ptype=3,
                                value=[2, 1, 0])
        if name == 'I_3':   # alias di gioco: identita' su {0,1,2} (= SCD_U)
            return SymbolicExpr('atom', name='SCD_U', ptype=3,
                                value=[0, 1, 2])
        if name in AlgebraEngine.GEN3:
            return SymbolicExpr('atom', name=name, ptype=3,
                                value=list(AlgebraEngine.GEN3[name]))
        raise ParseError(f"Simbolo interno non riconosciuto: '{name}'")

    # -------------------------------------------------------------------------
    # Regole grammaticali
    # -------------------------------------------------------------------------

    def _parse_expr(self) -> SymbolicExpr:
        """expr ::= term (COMPOSE term)*

        Il nodo compose viene costruito N-ARIO (un solo nodo con n figli)
        invece che come albero binario annidato a sinistra: con catene
        lunghe (centinaia di termini) l'albero annidato mandava in
        RecursionError flatten/repr/eval, che sono ricorsivi sulla
        profondità dell'AST.
        """
        left = self._parse_kron()
        terms = [left]
        while self._current().kind == 'COMPOSE':
            self._consume('COMPOSE')
            right = self._parse_kron()
            # Controllo di tipo
            if terms[-1].ptype != right.ptype:
                raise ParseError(
                    f"Composizione tra oggetti di tipo diverso: "
                    f"tipo {terms[-1].ptype} ∘ tipo {right.ptype}\n"
                    f"La composizione richiede oggetti dello stesso tipo."
                )
            terms.append(right)
        if len(terms) == 1:
            return terms[0]
        return SymbolicExpr('compose', children=terms, ptype=terms[0].ptype)

    def _parse_kron(self) -> SymbolicExpr:
        """term ::= factor (KRON factor)*"""
        left = self._parse_factor()
        factors = [left]
        while self._current().kind == 'KRON':
            self._consume('KRON')
            right = self._parse_factor()
            if right.ptype != 3:
                raise ParseError(
                    f"Il prodotto di Kronecker richiede oggetti di tipo 3, "
                    f"ma '{right.name or repr(right)}' è di tipo {right.ptype}."
                )
            factors.append(right)

        if len(factors) == 1:
            return factors[0]

        # Validazione: esattamente 3 fattori
        if len(factors) != 3:
            raise ParseError(
                f"Il prodotto di Kronecker richiede esattamente 3 fattori, "
                f"trovati {len(factors)}."
            )
        # Tutti di tipo 3
        for f in factors:
            if f.ptype != 3:
                raise ParseError(
                    f"Tutti i fattori del Kronecker devono essere di tipo 3, "
                    f"ma '{f.name}' è di tipo {f.ptype}."
                )
        return SymbolicExpr('kron', children=factors, ptype=27)

    def _parse_factor(self) -> SymbolicExpr:
        """factor ::= ATOM | '(' expr ')'"""
        tok = self._current()
        if tok.kind == 'ATOM':
            self._consume('ATOM')
            return self._make_atom(tok.value)
        if tok.kind == 'LPAREN':
            self._consume('LPAREN')
            expr = self._parse_expr()
            if self._current().kind != 'RPAREN':
                raise ParseError(
                    "Parentesi non chiusa: manca ')' dopo l'espressione."
                )
            self._consume('RPAREN')
            return expr
        if tok.kind == 'EOF':
            raise ParseError("Espressione incompleta: atteso un termine.")
        raise ParseError(
            f"Token inatteso: '{tok.value}' (tipo: {tok.kind})"
        )


# =============================================================================
# EVALUATOR
# =============================================================================

class Evaluator:
    """Valuta un AST producendo il vettore di permutazione finale."""

    def __init__(self, engine: AlgebraEngine):
        self.eng = engine

    def evaluate(self, expr: SymbolicExpr) -> List[int]:
        """Valuta ricorsivamente l'AST e restituisce la permutazione risultante."""
        if expr.kind == 'atom' or expr.kind == 'value':
            if expr.value is None:
                raise ValueError(f"Nodo senza valore: {expr.name}")
            return list(expr.value)

        if expr.kind == 'kron':
            if len(expr.children) != 3:
                raise ValueError("Il Kronecker deve avere esattamente 3 fattori.")
            p1 = self.evaluate(expr.children[0])
            p2 = self.evaluate(expr.children[1])
            p3 = self.evaluate(expr.children[2])
            return AlgebraEngine.kronecker3(p1, p2, p3)

        if expr.kind == 'compose':
            # A ∘ B: prima B, poi A
            # children = [A, B], quindi valutiamo da destra a sinistra
            # ma la composizione è: result = A(B(x))
            result = self.evaluate(expr.children[-1])
            for child in reversed(expr.children[:-1]):
                a = self.evaluate(child)
                result = AlgebraEngine.compose(a, result)
            return result

        raise ValueError(f"Tipo di nodo sconosciuto: {expr.kind}")

    def evaluate_with_trace(self, expr: SymbolicExpr) \
            -> Tuple[List[int], List[EvalStep]]:
        """
        Valuta l'AST registrando i passi parziali.

        Restituisce:
          (permutazione_finale, lista_EvalStep)

        Ogni EvalStep contiene indice, descrizione, permutazione parziale,
        firma canonica parziale.
        """
        steps: List[EvalStep] = []

        def _describe(node: SymbolicExpr) -> str:
            """Etichetta leggibile di un nodo."""
            if node.kind == 'atom':
                return node.name
            if node.kind == 'kron':
                return repr(node)
            if node.kind == 'compose':
                return f"composizione ({len(node.children)} termini)"
            return repr(node)

        def _eval_traced(node: SymbolicExpr) -> List[int]:
            if node.kind in ('atom', 'value'):
                p = list(node.value)
                sig = AlgebraEngine.perm_signature(p)
                steps.append(EvalStep(
                    index=len(steps),
                    description=f"Atomo: {node.name or repr(node)}",
                    perm=p,
                    signature=sig
                ))
                return p

            if node.kind == 'kron':
                p1 = _eval_traced(node.children[0])
                p2 = _eval_traced(node.children[1])
                p3 = _eval_traced(node.children[2])
                result = AlgebraEngine.kronecker3(p1, p2, p3)
                sig = AlgebraEngine.perm_signature(result)
                steps.append(EvalStep(
                    index=len(steps),
                    description=(f"Kronecker ⊗: "
                                 f"{repr(node.children[0])} ⊗ "
                                 f"{repr(node.children[1])} ⊗ "
                                 f"{repr(node.children[2])}"),
                    perm=result,
                    signature=sig
                ))
                return result

            if node.kind == 'compose':
                # Valuta da destra a sinistra
                current = _eval_traced(node.children[-1])
                for child in reversed(node.children[:-1]):
                    a = _eval_traced(child)
                    list(current)
                    current = AlgebraEngine.compose(a, current)
                    sig = AlgebraEngine.perm_signature(current)
                    steps.append(EvalStep(
                        index=len(steps),
                        description=(f"Composizione ∘: "
                                     f"{_describe(child)}  ∘  "
                                     f"[risultato precedente]"),
                        perm=current,
                        signature=sig
                    ))
                return current

            raise ValueError(f"Nodo sconosciuto: {node.kind}")

        final_perm = _eval_traced(expr)
        return final_perm, steps


# =============================================================================
# CONTROLLER (collega parser, rewriter, evaluator)
# =============================================================================

class Controller:
    """
    Coordina parsing, normalizzazione e valutazione.
    Restituisce un dizionario ricco con dati simbolici, algebrici e numerici.
    """

    def __init__(self):
        self.eng       = AlgebraEngine()
        self.parser    = Parser(self.eng)
        self.rewriter  = Rewriter(self.eng)
        self.evaluator = Evaluator(self.eng)

    def process(self, text: str) -> dict:
        """
        Processa un'espressione testuale.

        Campi del dizionario restituito (tutti quelli preesistenti + nuovi):

        Preesistenti:
          ok, error, normalized_str, norm_steps, perm, matrix,
          signature, period, inverse_perm, transpose_perm

        Nuovi:
          rewrite_trace       — lista di RewriteStep (traccia simbolica completa)
          partial_perms       — lista di permutazioni parziali (List[List[int]])
          partial_signatures  — lista di firme parziali (List[str])
          partial_descriptions — lista di descrizioni dei passi parziali
          normal_form         — NormalFormInfo (forma algebrica strutturata)
          normal_form_kind    — tipo stringa della forma normale
          msc_exponent        — esponente residuo di MSC mod 3
          kron_factors_repr   — lista rappresentazioni fattori Kronecker residui
        """
        result = {
            # ── Preesistenti ──────────────────────────────────────────────
            'ok':              False,
            'error':           '',
            'normalized_str':  '',
            'norm_steps':      '',
            'perm':            None,
            'matrix':          None,
            'signature':       '',
            'period':          None,
            'inverse_perm':    None,
            'transpose_perm':  None,
            # ── Nuovi ─────────────────────────────────────────────────────
            'rewrite_trace':        [],
            'partial_perms':        [],
            'partial_signatures':   [],
            'partial_descriptions': [],
            'normal_form':          None,
            'normal_form_kind':     '',
            'msc_exponent':         0,
            'kron_factors_repr':    [],
            # ── Forma canonica globale ─────────────────────────────────────
            'canonical_form':       None,   # oggetto CanonicalForm, se disponibile
            'canonical_available':  False,  # True se la forma canonica è stata costruita
            'canonical_symbolic':   '',     # rappresentazione testuale leggibile
        }

        try:
            # 0. Pre-pulizia: tollera il prefisso «T =» delle stringhe
            #    prodotte dall'Analisi (e' solo un'etichetta).
            text = text.strip()
            if text.startswith("T ="):
                text = text[3:].strip()

            # 1. Parsing
            ast = self.parser.parse(text)

            # 2. Normalizzazione con traccia completa
            norm_ast, rewrite_trace, nf_info = \
                self.rewriter.normalize_with_trace(ast)

            result['normalized_str']  = repr(norm_ast)
            result['norm_steps']      = self._format_trace_summary(rewrite_trace)
            result['rewrite_trace']   = rewrite_trace
            result['normal_form']     = nf_info
            result['normal_form_kind']    = nf_info.kind
            result['msc_exponent']        = nf_info.msc_exponent
            result['kron_factors_repr']   = nf_info.kron_factors_repr

            # Costruzione forma canonica globale
            cf = _build_canonical_form(nf_info)
            if cf is not None:
                result['canonical_form']      = cf
                result['canonical_available'] = True
                result['canonical_symbolic']  = cf.symbolic()
            else:
                result['canonical_available'] = False
                result['canonical_symbolic']  = (
                    "Non disponibile (espressione contiene J o non riducibile)"
                    if nf_info.kind in ('J', 'composta')
                    else "Non disponibile"
                )

            # 3. Valutazione con traccia dei passi parziali
            perm, eval_steps = self.evaluator.evaluate_with_trace(norm_ast)

            # Verifica coerenza dimensionale
            if len(perm) not in (3, 27):
                raise ValueError(f"Permutazione di dimensione inattesa: {len(perm)}")
            if len(perm) == 3:
                raise ValueError(
                    "Il risultato è di tipo 3. "
                    "Usare un prodotto di Kronecker per ottenere una "
                    "trasformazione di tipo 27.")

            result['partial_perms']         = [s.perm for s in eval_steps]
            result['partial_signatures']    = [s.signature for s in eval_steps]
            result['partial_descriptions']  = [s.description for s in eval_steps]

            result['perm']      = perm
            result['signature'] = AlgebraEngine.perm_signature(perm)
            result['matrix']    = AlgebraEngine.perm_to_matrix(perm)

            # 4. Inversa e trasposta
            result['inverse_perm']   = AlgebraEngine.inverse_perm(perm)
            result['transpose_perm'] = AlgebraEngine.transpose_perm(perm)

            # 5. Periodo (limite 200)
            result['period'] = AlgebraEngine.find_period(perm, max_iter=200)

            result['ok'] = True

        except ParseError as e:
            result['error'] = f"Errore di parsing:\n{e}"
        except ValueError as e:
            result['error'] = f"Errore di valutazione:\n{e}"
        except Exception as e:
            result['error'] = f"Errore interno:\n{type(e).__name__}: {e}"

        return result

    def _format_trace_summary(self, trace: List[RewriteStep]) -> str:
        """Formatta la traccia come stringa sintetica per il pannello norm_steps."""
        if not trace:
            return "Nessun passo di riscrittura."
        return "  →  ".join(s.rule for s in trace)


# =============================================================================
# GUI
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# ANALISI MOLTEPLICITA'  (in-memory)
# ─────────────────────────────────────────────────────────────────────────────

def analizza_righe(righe):
    """Raggruppa per T_permutazione e conta le sequenze Stage distinte.

    Usa la notazione Stage-level "T = [Stage3] o [Stage2] o [Stage1]"
    che distingue (P, J) anche quando la composizione Ai = P∘J coincide,
    dando la granularità corretta come in analisi_sequenze.py.
    """
    gruppi = defaultdict(lambda: {"simboliche": set(), "perm_str": ""})
    for r in righe:
        perm_str = r.get("T_permutazione", "")
        s1 = r.get("Stage1", "")
        s2 = r.get("Stage2", "")
        s3 = r.get("Stage3", "")
        if s1 or s2 or s3:
            t_sim = f"T = [{s3}] o [{s2}] o [{s1}]"
        else:
            t_sim = r.get("T_simbolica", "")
        try:
            perm_tuple = tuple(int(x) for x in perm_str.strip("[]").split(","))
        except ValueError:
            continue
        gruppi[perm_tuple]["simboliche"].add(t_sim)
        gruppi[perm_tuple]["perm_str"] = perm_str
    risultati = []
    for pt, g in gruppi.items():
        risultati.append({
            "perm_tuple": pt,
            "perm_str":   g["perm_str"],
            "simboliche": sorted(g["simboliche"]),
            "n_sim":      len(g["simboliche"]),
        })
    risultati.sort(key=lambda r: (-r["n_sim"], r["perm_tuple"]))
    return risultati


def analizza_csv(input_path):
    """Legge un CSV COMBINAZIONI (sep=;) e restituisce i risultati di analizza_righe.

    Compatibile con il CSV prodotto da write_csv() / il file COMBINAZIONI_DEL_MODELLO.
    Legge T_simbolica (colonna ridotta Ai) per il raggruppamento, e Stage1/2/3
    per il pannello di dettaglio, esattamente come fa l'analisi in-memoria.
    """
    import csv as _csv

    def _col(header, kw):
        kw = kw.lower()
        for i, h in enumerate(header):
            if kw in h.lower():
                return i
        return None

    righe = []
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = _csv.reader(f, delimiter=";", quotechar='"')
        header = next(reader)
        idx_s1   = _col(header, "stage1")
        idx_s2   = _col(header, "stage2")
        idx_s3   = _col(header, "stage3")
        idx_tsim = _col(header, "t_simbolica")
        idx_perm = _col(header, "t_permutazione")
        for row in reader:
            if not row:
                continue
            def _get(i):
                return row[i].strip() if i is not None and i < len(row) else ""
            righe.append({
                "Stage1":         _get(idx_s1),
                "Stage2":         _get(idx_s2),
                "Stage3":         _get(idx_s3),
                "T_simbolica":    _get(idx_tsim),
                "T_permutazione": _get(idx_perm),
            })
    return analizza_righe(righe)


def _prep_explorer_expr(t_sim):
    """Prepara una T_simbolica per il campo Explorer.
    Normalizza qualunque operatore di composizione a 'o' (lettera),
    e qualunque Kronecker a 'x' (lettera), indipendentemente dalla sorgente.
    """
    expr = t_sim.strip()
    if expr.startswith("T = "):
        expr = expr[4:]
    # NB (v2.8.4): R_U e I_3 NON vengono più sostituiti — il parser li
    # accetta come alias nativi, così l'Explorer mostra la notazione di
    # gioco esattamente come appare nell'Analisi.
    # Normalizza operatori: ∘ e @ → o (con spazi)
    expr = expr.replace(" ∘ ", " o ").replace("∘", " o ")
    expr = expr.replace(" @ ", " o ").replace("@", " o ")
    # Normalizza Kronecker: ⊗ → x (con spazi)
    expr = expr.replace(" ⊗ ", " x ").replace("⊗", " x ")
    return expr


# ─────────────────────────────────────────────────────────────────────────────
# ESPORTAZIONE ANALISI
# ─────────────────────────────────────────────────────────────────────────────

def scrivi_output(risultati, output_path):
    header = [
        "T_permutazione  [lista 0..26]",
        "T_simboliche_distinte  [separate da , ]",
        "n_sim_distinte  [molteplicita della permutazione]",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";", quotechar='"',
                       quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow(header)
        for r in risultati:
            w.writerow([r["perm_str"], " , ".join(r["simboliche"]), str(r["n_sim"])])


def scrivi_excel(risultati, output_path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    wb       = Workbook()
    HDR_FILL = PatternFill("solid", fgColor="1F4E79")
    HDR_FONT = Font(bold=True, color="FFFFFF", size=10)
    ALT_FILL = PatternFill("solid", fgColor="D6E4F0")
    BORDER   = Border(bottom=Side(style="thin", color="AAAAAA"),
                      right=Side(style="thin",  color="AAAAAA"))
    def _fmt(ws, i, nc):
        fill = ALT_FILL if i % 2 == 0 else None
        for c in range(1, nc+1):
            cell = ws.cell(i+1, c)
            if fill: cell.fill = fill
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = BORDER
    def _hdr(ws, hdrs):
        ws.append(hdrs)
        for c in range(1, len(hdrs)+1):
            cell = ws.cell(1, c)
            cell.font = HDR_FONT; cell.fill = HDR_FILL
            cell.alignment = Alignment(horizontal="center", wrap_text=True)
    ws1 = wb.active
    ws1.title = "Perm -> Simboliche"
    _hdr(ws1, ["T_permutazione", "T_simboliche_distinte", "n_sim_distinte"])
    for i, r in enumerate(risultati, 1):
        ws1.append([r["perm_str"], " , ".join(r["simboliche"]), r["n_sim"]])
        _fmt(ws1, i, 3)
    ws1.column_dimensions["A"].width = 40
    ws1.column_dimensions["B"].width = 120
    ws1.column_dimensions["C"].width = 14
    ws1.freeze_panes = "A2"
    ws1.auto_filter.ref = f"A1:C{len(risultati)+1}"
    ws2 = wb.create_sheet("Simbolica -> Perm")
    _hdr(ws2, ["T_simbolica", "T_permutazione", "n_sim_distinte"])
    righe_inv = sorted(
        [(sim, r["perm_str"], r["n_sim"]) for r in risultati for sim in r["simboliche"]],
        key=lambda x: x[0])
    for i, (sim, perm, n) in enumerate(righe_inv, 1):
        ws2.append([sim, perm, n])
        _fmt(ws2, i, 3)
    ws2.column_dimensions["A"].width = 120
    ws2.column_dimensions["B"].width = 40
    ws2.column_dimensions["C"].width = 14
    ws2.freeze_panes = "A2"
    ws2.auto_filter.ref = f"A1:C{len(righe_inv)+1}"
    wb.save(output_path)


