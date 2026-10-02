import unittest
import numpy as np

from main import GAConfig, gaussian_mutation, rastrigin, repair_bounds, run_ga


class Lab1Tests(unittest.TestCase):
    def test_rastrigin_global_minimum(self):
        value = rastrigin(np.zeros((1, 9)))[0]
        self.assertAlmostEqual(float(value), 0.0, places=12)

    def test_repair_bounds(self):
        config = GAConfig()
        values = np.array([[100.0] * 9, [-100.0] * 9])
        repaired = repair_bounds(values, config)
        self.assertTrue(np.all(repaired <= config.upper_bound))
        self.assertTrue(np.all(repaired >= config.lower_bound))

    def test_reproducibility(self):
        config = GAConfig(generations=20)
        first = run_ga(12345, config)
        second = run_ga(12345, config)
        self.assertAlmostEqual(first["final_best"], second["final_best"], places=12)
        self.assertTrue(np.allclose(first["best_vector"], second["best_vector"]))

    def test_dimension(self):
        config = GAConfig()
        result = run_ga(31415, config)
        self.assertEqual(len(result["best_vector"]), 9)

    def test_budget(self):
        config = GAConfig(generations=20)
        result = run_ga(1, config)
        self.assertEqual(result["evaluations"], config.evaluation_budget)


if __name__ == "__main__":
    unittest.main()
