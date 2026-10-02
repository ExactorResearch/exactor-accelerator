import unittest
from exactor_accelerator.core.hypercube import (
    HypercubeTerm,
    ExactorHypercubeReducer,
    ExactorSimplificationResult,
)


class TestExactorHypercubeSuite(unittest.TestCase):
    """
    Comprehensive test suite validating the discrete Boolean minimization engine,
    soundness, completeness, Don't Care handling, XOR pattern extraction,
    and edge cases on the B^k hypercube.
    """

    def test_term_creation_and_matching(self):
        """Validates term initialization, minterm decoding, and bit vector matching."""
        # 3 variables: minterm 5 is binary 101
        term = HypercubeTerm.from_minterm(5, 3)
        self.assertEqual(term.states, [1, 0, 1])
        self.assertTrue(term.matches(5))
        self.assertFalse(term.matches(4))  # 100
        self.assertTrue(term.matches_vector([1, 0, 1]))
        self.assertFalse(term.matches_vector([1, 1, 1]))

    def test_term_combination_hamming_distance(self):
        """Checks adjacency combination: 000 + 001 -> 00- (Hamming distance = 1)."""
        t0 = HypercubeTerm.from_minterm(0, 3)  # 000
        t1 = HypercubeTerm.from_minterm(1, 3)  # 001
        comb = t0.try_combine(t1)
        self.assertIsNotNone(comb)
        self.assertEqual(comb.states, [0, 0, HypercubeTerm.STATE_DC])
        self.assertTrue(comb.matches(0))
        self.assertTrue(comb.matches(1))
        self.assertFalse(comb.matches(2))

        # Distance > 1 cannot combine: 000 (0) and 011 (3)
        t3 = HypercubeTerm.from_minterm(3, 3)
        self.assertIsNone(t0.try_combine(t3))

        # Different lengths must raise error
        with self.assertRaises(ValueError):
            HypercubeTerm([0, 1], 3)

    def test_empty_minterms(self):
        """Empty minterms must yield FALSE and evaluate to 0 everywhere."""
        reducer = ExactorHypercubeReducer(["A", "B"])
        result = reducer.minimize([])
        self.assertEqual(result.initial_minterm_count, 0)
        self.assertEqual(result.final_term_count, 0)
        self.assertEqual(result.formula_expr, "FALSE")
        self.assertEqual(result.evaluate([0, 0]), 0)
        self.assertEqual(result.evaluate([1, 1]), 0)
        self.assertEqual(result.evaluate_dict({"A": 1, "B": 1}), 0)

    def test_tautology_full_hypercube(self):
        """All 2^k minterms must minimize to TRUE (a single term with all Don't Cares)."""
        variables = ["A", "B", "C"]
        all_minterms = list(range(8))  # 0..7
        reducer = ExactorHypercubeReducer(variables)
        result = reducer.minimize(all_minterms)

        self.assertEqual(result.initial_minterm_count, 8)
        self.assertEqual(result.final_term_count, 1)
        # Term must have only Don't Care states
        self.assertEqual(result.terms[0].states, [HypercubeTerm.STATE_DC] * 3)
        self.assertEqual(result.formula_expr, "TRUE")
        for m in all_minterms:
            vec = [(m >> (2 - i)) & 1 for i in range(3)]
            self.assertEqual(result.evaluate(vec), 1)

    def test_single_variable_function(self):
        """Function f(A) = A: minterm 1 (binary 1) over variable A."""
        reducer = ExactorHypercubeReducer(["A"])
        result = reducer.minimize([1])
        self.assertEqual(result.formula_expr, "(A)")
        self.assertEqual(result.evaluate([1]), 1)
        self.assertEqual(result.evaluate([0]), 0)

        # Function f(A) = NOT A: minterm 0
        result_not = reducer.minimize([0])
        self.assertEqual(result_not.formula_expr, "(NOT A)")
        self.assertEqual(result_not.evaluate([0]), 1)
        self.assertEqual(result_not.evaluate([1]), 0)

    def test_and_gate_soundness_and_completeness(self):
        """Function f(A, B) = A AND B: only minterm 3 (11) is ON."""
        reducer = ExactorHypercubeReducer(["A", "B"])
        result = reducer.minimize([3])
        self.assertEqual(result.final_term_count, 1)
        self.assertEqual(result.terms[0].states, [1, 1])
        self.assertIn("A", result.formula_expr)
        self.assertIn("B", result.formula_expr)

        # Truth table check
        for a in (0, 1):
            for b in (0, 1):
                expected = 1 if (a == 1 and b == 1) else 0
                self.assertEqual(result.evaluate([a, b]), expected)
                self.assertEqual(result.evaluate_dict({"A": a, "B": b}), expected)

    def test_or_gate_minimization(self):
        """Function f(A, B) = A OR B: minterms 1 (01), 2 (10), 3 (11)."""
        reducer = ExactorHypercubeReducer(["A", "B"])
        result = reducer.minimize([1, 2, 3])

        # Should minimize to 2 terms: A or B (or equivalent prime implicants)
        self.assertLessEqual(result.final_term_count, 2)
        # Truth table verification
        for a in (0, 1):
            for b in (0, 1):
                expected = 1 if (a or b) else 0
                self.assertEqual(result.evaluate([a, b]), expected, f"Failed on A={a}, B={b}")

    def test_dont_care_simplification(self):
        """
        Don't Care terms allow expansion to a larger subcube.
        Minterms: [0] (00)
        Don't Care: [1] (01)
        00 and 01 combine to 0- (NOT A), eliminating variable B.
        """
        reducer = ExactorHypercubeReducer(["A", "B"])
        result = reducer.minimize(minterms=[0], dont_cares=[1])

        self.assertEqual(result.final_term_count, 1)
        self.assertEqual(result.terms[0].states, [0, HypercubeTerm.STATE_DC])
        self.assertEqual(result.evaluate([0, 0]), 1)
        self.assertEqual(result.evaluate([0, 1]), 1)
        self.assertEqual(result.evaluate([1, 0]), 0)
        self.assertEqual(result.evaluate([1, 1]), 0)

    def test_xor_symmetry_detection(self):
        """Function f(A, B) = A XOR B: minterms 1 (01) and 2 (10)."""
        reducer = ExactorHypercubeReducer(["A", "B"])
        result = reducer.minimize([1, 2])

        # Verifies XOR clause detection
        self.assertEqual(len(result.xor_clauses), 1)
        self.assertIn("XOR", result.xor_clauses[0])

        # Correct evaluation for all inputs
        self.assertEqual(result.evaluate([0, 0]), 0)
        self.assertEqual(result.evaluate([0, 1]), 1)
        self.assertEqual(result.evaluate([1, 0]), 1)
        self.assertEqual(result.evaluate([1, 1]), 0)

    def test_multiplexer_4var_canonical(self):
        """
        4-variable 2-to-1 Multiplexer with Enable:
        Vars: [E, S, D0, D1]
        Output = E AND ((NOT S AND D0) OR (S AND D1))
        """
        variables = ["E", "S", "D0", "D1"]
        minterms = []
        for e in (0, 1):
            for s in (0, 1):
                for d0 in (0, 1):
                    for d1 in (0, 1):
                        out = e & ((d1 if s else d0))
                        if out == 1:
                            m = (e << 3) | (s << 2) | (d0 << 1) | d1
                            minterms.append(m)

        reducer = ExactorHypercubeReducer(variables)
        result = reducer.minimize(minterms)

        # Must reproduce exact multiplexer output for all 16 combinations
        for m in range(16):
            vec = [(m >> (3 - i)) & 1 for i in range(4)]
            expected = 1 if m in minterms else 0
            self.assertEqual(
                result.evaluate(vec),
                expected,
                f"Mux mismatch at minterm {m} (bits={vec})",
            )

    def test_serialization_to_dict(self):
        """Verifies that audit dict contains all metadata fields."""
        reducer = ExactorHypercubeReducer(["A", "B"])
        result = reducer.minimize([1, 2])
        res_dict = result.to_dict()

        self.assertIn("variables", res_dict)
        self.assertIn("formula_expr", res_dict)
        self.assertIn("compression_ratio", res_dict)
        self.assertIn("terms", res_dict)
        self.assertIn("stats", res_dict)
        self.assertIn("execution_time_ms", res_dict["stats"])


if __name__ == "__main__":
    unittest.main()
