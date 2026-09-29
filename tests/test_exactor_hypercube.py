import unittest
from exactor_accelerator.core.hypercube import (
    HypercubeTerm,
    ExactorHypercubeReducer,
)


class TestExactorHypercube(unittest.TestCase):

    def test_xor_function_minimization(self):
        # 3-variable XOR function (parity)
        # variables: A, B, C
        # Minterms for A ^ B ^ C: 1 (001), 2 (010), 4 (100), 7 (111)
        variables = ["A", "B", "C"]
        minterms = [1, 2, 4, 7]
        reducer = ExactorHypercubeReducer(variables)
        result = reducer.minimize(minterms)

        self.assertEqual(result.initial_minterm_count, 4)
        self.assertGreater(result.final_term_count, 0)

        # 100% precision audit test
        for m in minterms:
            bit_vec = [(m >> (2 - i)) & 1 for i in range(3)]
            self.assertEqual(result.evaluate(bit_vec), 1, f"Minterm {m} must evaluate to 1")

        # Off-set minterms must evaluate to 0
        for off_m in [0, 3, 5, 6]:
            bit_vec = [(off_m >> (2 - i)) & 1 for i in range(3)]
            self.assertEqual(result.evaluate(bit_vec), 0, f"Off-minterm {off_m} must evaluate to 0")

    def test_term_combination(self):
        # Term 000 and 001 combine to 00-
        t1 = HypercubeTerm.from_minterm(0, 3)
        t2 = HypercubeTerm.from_minterm(1, 3)
        comb = t1.try_combine(t2)
        self.assertIsNotNone(comb)
        self.assertEqual(comb.states, [0, 0, HypercubeTerm.STATE_DC])
        self.assertTrue(comb.matches(0))
        self.assertTrue(comb.matches(1))
        self.assertFalse(comb.matches(2))


if __name__ == "__main__":
    unittest.main()
