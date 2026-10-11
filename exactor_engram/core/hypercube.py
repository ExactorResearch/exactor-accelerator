"""
Local Fallback Boolean Hypercube B^k Minimizer.
Operates strictly in discrete Boolean logic without floating-point arithmetic.
Implements standard tabular prime implicant combination and greedy set cover
as a local fallback when the remote EXACTOR Core API / binary is not configured.
"""

from typing import List, Dict, Any, Set, Tuple, Optional
import time


class HypercubeTerm:
    """
    Represents a generalized subcube / product term in B^k.
    Each variable is in one of three states:
      0: Inactive / Negated (NOT V)
      1: Active / Asserted (V)
      2: Don't Care (-)
    """

    STATE_0 = 0
    STATE_1 = 1
    STATE_DC = 2

    def __init__(self, states: List[int], num_vars: int):
        if len(states) != num_vars:
            raise ValueError(f"States length {len(states)} must match num_vars {num_vars}")
        self.states = list(states)
        self.num_vars = num_vars
        self.covered_minterms: Set[int] = set()

    @classmethod
    def from_minterm(cls, minterm: int, num_vars: int) -> "HypercubeTerm":
        """Builds a 0-dimensional term (a single vertex) from an integer minterm."""
        states = []
        for i in range(num_vars):
            bit = (minterm >> (num_vars - 1 - i)) & 1
            states.append(bit)
        term = cls(states, num_vars)
        term.covered_minterms.add(minterm)
        return term

    def matches(self, minterm: int) -> bool:
        """Tests if an integer minterm belongs to this subcube."""
        for i in range(self.num_vars):
            expected = self.states[i]
            if expected == self.STATE_DC:
                continue
            actual_bit = (minterm >> (self.num_vars - 1 - i)) & 1
            if actual_bit != expected:
                return False
        return True

    def matches_vector(self, bit_vector: List[int]) -> bool:
        """Tests if a bit vector [v0, v1, ...] belongs to this subcube."""
        for i in range(self.num_vars):
            expected = self.states[i]
            if expected != self.STATE_DC and bit_vector[i] != expected:
                return False
        return True

    def try_combine(self, other: "HypercubeTerm") -> Optional["HypercubeTerm"]:
        """
        Attempts to combine two adjacent subcubes in the hypercube differing by exactly one bit.
        Returns a new subcube with Don't Care at the differing bit, or None.
        """
        diff_idx = -1
        for i in range(self.num_vars):
            s1 = self.states[i]
            s2 = other.states[i]
            if s1 != s2:
                if (s1 == self.STATE_DC) or (s2 == self.STATE_DC):
                    return None
                if diff_idx != -1:
                    return None  # Differ by more than 1 bit
                diff_idx = i

        if diff_idx == -1:
            return None  # Identical

        new_states = list(self.states)
        new_states[diff_idx] = self.STATE_DC
        combined = HypercubeTerm(new_states, self.num_vars)
        combined.covered_minterms = self.covered_minterms.union(other.covered_minterms)
        return combined

    def to_string(self, var_names: List[str]) -> str:
        """Formats the term into human-readable Boolean algebra (e.g. A & !B)."""
        literals = []
        for i, s in enumerate(self.states):
            v_name = var_names[i] if i < len(var_names) else f"V{i}"
            if s == self.STATE_1:
                literals.append(v_name)
            elif s == self.STATE_0:
                literals.append(f"NOT {v_name}")
        return " AND ".join(literals) if literals else "TRUE"

    def to_mask_tuple(self) -> Tuple[int, ...]:
        return tuple(self.states)

    def __hash__(self) -> int:
        return hash(tuple(self.states))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, HypercubeTerm):
            return self.states == other.states
        return False


class ExactorSimplificationResult:
    """Immutable audit record of the Exactor minimization output."""

    def __init__(
        self,
        variables: List[str],
        terms: List[HypercubeTerm],
        initial_minterm_count: int,
        final_term_count: int,
        formula_expr: str,
        xor_clauses: List[str],
        stats: Dict[str, Any],
    ):
        self.variables = variables
        self.terms = terms
        self.initial_minterm_count = initial_minterm_count
        self.final_term_count = final_term_count
        self.formula_expr = formula_expr
        self.xor_clauses = xor_clauses
        self.stats = stats

    def evaluate(self, bit_vector: List[int]) -> int:
        """Evaluates a bit vector against the simplified Boolean expression."""
        # Check standard sum-of-products terms
        for term in self.terms:
            if term.matches_vector(bit_vector):
                return 1
        return 0

    def evaluate_dict(self, prop_dict: Dict[str, int]) -> int:
        """Evaluates a dictionary of proposition names -> 0/1 against the rule."""
        bit_vec = [prop_dict.get(v, 0) for v in self.variables]
        return self.evaluate(bit_vec)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variables": self.variables,
            "formula_expr": self.formula_expr,
            "xor_clauses": self.xor_clauses,
            "initial_minterms": self.initial_minterm_count,
            "final_terms": self.final_term_count,
            "compression_ratio": (
                round(1.0 - (self.final_term_count / max(1, self.initial_minterm_count)), 4)
                if self.initial_minterm_count > 0
                else 0.0
            ),
            "terms": [t.to_string(self.variables) for t in self.terms],
            "stats": self.stats,
        }


class ExactorHypercubeReducer:
    """
    Local Fallback Boolean Hypercube Minimizer.
    Minimizes Boolean functions on B^k using standard tabular combination and greedy cover.
    """

    def __init__(self, variables: List[str]):
        self.variables = variables
        self.num_vars = len(variables)

    def minimize(
        self, minterms: List[int], dont_cares: Optional[List[int]] = None
    ) -> ExactorSimplificationResult:
        """
        Executes the Boolean function reduction algorithm.
        Inputs:
          minterms: ON-set integers in [0, 2^k - 1]
          dont_cares: optional DC-set integers
        """
        start_time = time.perf_counter()
        minterms_set = set(minterms)
        dc_set = set(dont_cares or [])
        all_care_set = minterms_set.union(dc_set)

        if not minterms_set:
            return ExactorSimplificationResult(
                variables=self.variables,
                terms=[],
                initial_minterm_count=0,
                final_term_count=0,
                formula_expr="FALSE",
                xor_clauses=[],
                stats={"execution_time_ms": 0.1, "iterations": 0},
            )

        # Detect trivial full ON-set
        if len(minterms_set) == (1 << self.num_vars) and self.num_vars <= 16:
            full_term = HypercubeTerm([HypercubeTerm.STATE_DC] * self.num_vars, self.num_vars)
            return ExactorSimplificationResult(
                variables=self.variables,
                terms=[full_term],
                initial_minterm_count=len(minterms_set),
                final_term_count=1,
                formula_expr="TRUE",
                xor_clauses=[],
                stats={"execution_time_ms": 0.1, "iterations": 1},
            )

        # Step 1: Initialize 0-dimensional cubes
        current_terms = [HypercubeTerm.from_minterm(m, self.num_vars) for m in all_care_set]
        prime_implicants: Set[HypercubeTerm] = set()
        iterations = 0
        terms_generated = len(current_terms)
        terms_eliminated = 0

        # Step 2: Tabular adjacent combination loop
        # Repeatedly combine adjacent terms differing by 1 bit until convergence
        while current_terms:
            iterations += 1
            combined_this_round: Set[HypercubeTerm] = set()
            covered_in_round: Set[HypercubeTerm] = set()
            next_terms_dict: Dict[Tuple[int, ...], HypercubeTerm] = {}

            # Partition terms by number of 1-bits for fast O(n) candidate matching
            count_groups: Dict[int, List[HypercubeTerm]] = {}
            for t in current_terms:
                c1 = sum(1 for s in t.states if s == HypercubeTerm.STATE_1)
                count_groups.setdefault(c1, []).append(t)

            sorted_counts = sorted(count_groups.keys())
            for c_idx in sorted_counts:
                group_a = count_groups[c_idx]
                group_b = count_groups.get(c_idx + 1, [])
                for ta in group_a:
                    for tb in group_b:
                        comb = ta.try_combine(tb)
                        if comb is not None:
                            terms_generated += 1
                            covered_in_round.add(ta)
                            covered_in_round.add(tb)
                            mask = comb.to_mask_tuple()
                            if mask not in next_terms_dict:
                                next_terms_dict[mask] = comb
                            else:
                                next_terms_dict[mask].covered_minterms.update(comb.covered_minterms)

            # Terms that could not be combined with anything are prime implicants
            for t in current_terms:
                if t not in covered_in_round:
                    # Check that this term actually covers at least one ON-set minterm
                    if any(m in minterms_set for m in t.covered_minterms):
                        prime_implicants.add(t)

            terms_eliminated += len(covered_in_round)
            current_terms = list(next_terms_dict.values())

            # Stop if iterations exceed safety threshold
            if iterations > 32:
                break

        # Step 3: Minimal Set Covering for the ON-set
        uncovered = set(minterms_set)
        selected_terms: List[HypercubeTerm] = []

        # Find essential prime implicants first
        minterm_to_primes: Dict[int, List[HypercubeTerm]] = {m: [] for m in minterms_set}
        for pi in prime_implicants:
            for m in pi.covered_minterms:
                if m in minterm_to_primes:
                    minterm_to_primes[m].append(pi)

        # Essential ones
        for m, primes in minterm_to_primes.items():
            if len(primes) == 1:
                essential = primes[0]
                if essential not in selected_terms:
                    selected_terms.append(essential)
                    uncovered.difference_update(essential.covered_minterms)

        # Greedy cover for remaining uncovered minterms
        remaining_primes = [p for p in prime_implicants if p not in selected_terms]
        while uncovered and remaining_primes:
            remaining_primes.sort(
                key=lambda p: len(p.covered_minterms.intersection(uncovered)), reverse=True
            )
            best_prime = remaining_primes.pop(0)
            cov_count = len(best_prime.covered_minterms.intersection(uncovered))
            if cov_count == 0:
                break
            selected_terms.append(best_prime)
            uncovered.difference_update(best_prime.covered_minterms)

        # Step 4: XOR Pattern Extraction
        # Look for parity symmetry across pairs of terms
        xor_clauses: List[str] = []
        term_strs = [t.to_string(self.variables) for t in selected_terms]

        # Detect parity / XOR pairs: e.g. (A & !B) OR (!A & B) -> A XOR B
        consumed_indices = set()
        for i in range(len(selected_terms)):
            if i in consumed_indices:
                continue
            for j in range(i + 1, len(selected_terms)):
                if j in consumed_indices:
                    continue
                ti = selected_terms[i]
                tj = selected_terms[j]
                # Check if exactly 2 active variables have inverted states and rest are identical DC
                active_i = {k: ti.states[k] for k in range(self.num_vars) if ti.states[k] != HypercubeTerm.STATE_DC}
                active_j = {k: tj.states[k] for k in range(self.num_vars) if tj.states[k] != HypercubeTerm.STATE_DC}
                if len(active_i) == 2 and len(active_j) == 2 and active_i.keys() == active_j.keys():
                    vars_pair = list(active_i.keys())
                    v0, v1 = vars_pair[0], vars_pair[1]
                    s_i0, s_i1 = active_i[v0], active_i[v1]
                    s_j0, s_j1 = active_j[v0], active_j[v1]
                    # XOR pattern: (1,0) and (0,1)
                    if (s_i0 != s_i1) and (s_j0 != s_j1) and (s_i0 != s_j0):
                        v_name0 = self.variables[v0]
                        v_name1 = self.variables[v1]
                        xor_clauses.append(f"({v_name0} XOR {v_name1})")
                        consumed_indices.add(i)
                        consumed_indices.add(j)
                        break

        # Step 5: Format formula string
        formula_parts = []
        if xor_clauses:
            formula_parts.extend(xor_clauses)
        for idx, t in enumerate(selected_terms):
            if idx not in consumed_indices:
                formula_parts.append(f"({t.to_string(self.variables)})")

        formula_expr = " OR ".join(formula_parts) if formula_parts else "FALSE"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        stats = {
            "execution_time_ms": round(elapsed_ms, 3),
            "iterations": iterations,
            "terms_generated": terms_generated,
            "terms_eliminated": terms_eliminated,
            "prime_implicants_found": len(prime_implicants),
            "xor_patterns_detected": len(xor_clauses),
        }

        return ExactorSimplificationResult(
            variables=self.variables,
            terms=selected_terms,
            initial_minterm_count=len(minterms_set),
            final_term_count=len(selected_terms),
            formula_expr=formula_expr,
            xor_clauses=xor_clauses,
            stats=stats,
        )
