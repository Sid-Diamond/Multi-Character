"""Offline mathematical and saved-dataset checks for posterior sign grids."""

import copy
import csv
from fractions import Fraction
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from scipy.integrate import quad
from scipy.special import betaincc, betaln

import analysis
from analysis._shared import FRAMINGS, PROJECT, load_baselines
from analysis.multi_agent_grid import observed_counts
from analysis.uncertainty_grid import (_adaptive, calculate, colour_matrix, percentage,
                                       posterior_shape, posterior_sign_probabilities)


class PosteriorMathematicsTests(unittest.TestCase):
    def test_prior_applied_once_and_count_validation(self):
        self.assertEqual(posterior_shape(0, 25), (0.5, 25.5))
        self.assertEqual(posterior_shape(25, 25), (25.5, 0.5))
        for counts in [(1, 0), (-1, 25), (26, 25), (0.5, 25), (True, 25)]:
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                posterior_shape(*counts)

    def test_shared_parameter_and_distinct_identical_distributions_differ(self):
        # With a uniform group posterior, the positive tail is (1-p)^2
        # for a shared uniform baseline, or (1-p_a)(1-p_b) for two baselines.
        shared = posterior_sign_probabilities((1, 1), (1, 1))
        distinct = posterior_sign_probabilities((1, 1), (1, 1), (1, 1))
        self.assertAlmostEqual(shared["p_positive"], 1 / 3, places=12)
        self.assertAlmostEqual(distinct["p_positive"], 1 / 4, places=12)
        self.assertEqual(shared["integration_dimensions"], 1)
        self.assertEqual(distinct["integration_dimensions"], 2)

    def test_mixed_pair_exchange_symmetry(self):
        first = posterior_sign_probabilities((3.5, 5.5), (2.5, 6.5), (4.5, 4.5))
        second = posterior_sign_probabilities((3.5, 5.5), (4.5, 4.5), (2.5, 6.5))
        self.assertAlmostEqual(first["p_positive"], second["p_positive"], places=12)

    def test_against_independent_density_quadrature(self):
        # Integrate the two posterior densities explicitly rather than using
        # Jacobi rules. Shapes > 1 keep this independent check inexpensive.
        group, shape_a, shape_b = (12.5, 13.5), (6.5, 24.5), (3.5, 27.5)

        def density(x, a, b):
            return np.exp((a - 1) * np.log(x) + (b - 1) * np.log1p(-x) - betaln(a, b))

        def outer(x):
            value = quad(lambda y: density(y, *shape_b) * betaincc(*group, x + (1 - x) * y),
                         0, 1, epsabs=1e-10, epsrel=1e-10)[0]
            return density(x, *shape_a) * value

        reference = quad(outer, 0, 1, epsabs=1e-10, epsrel=1e-10)[0]
        result = posterior_sign_probabilities(group, shape_a, shape_b)
        self.assertAlmostEqual(result["p_positive"], reference, places=9)

    def test_singular_zero_count_posteriors_have_adaptive_fallback(self):
        for baseline_b in [None, (0.5, 30.5)]:
            with self.subTest(shared=baseline_b is None):
                result = posterior_sign_probabilities((0.5, 25.5), (0.5, 30.5), baseline_b,
                                                       initial_order=2, max_order=8)
                self.assertEqual(result["quadrature_method"], "adaptive_algebraic")
                self.assertTrue(0 < result["p_positive"] < 1)
                self.assertAlmostEqual(result["p_positive"] + result["p_negative"], 1, places=10)

    def test_small_negative_tail_survives_when_positive_rounds_to_one(self):
        result = posterior_sign_probabilities((100.5, 0.5), (0.5, 100.5))
        self.assertGreater(result["p_negative"], 0)
        self.assertLess(result["p_negative"], 1e-15)

    def test_percentage_labels_do_not_imply_absolute_certainty(self):
        self.assertEqual(percentage(None), "—")
        self.assertEqual(percentage(0.951), "95.1%")
        self.assertEqual(percentage(1 - 1e-12), ">99.9%")
        self.assertEqual(percentage(1e-12), "<0.1%")


class SavedDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = PROJECT / "outputs/multi_agent/all_pairs_combined/analysis"
        cls.counts = observed_counts(cls.folder / "trials.csv")
        cls.rows = calculate(cls.counts, load_baselines()["feb_data"])

    def test_all_45_cells_converge_and_probabilities_are_complements(self):
        self.assertEqual(len(self.rows), 45)
        self.assertEqual(sum(r["integration_dimensions"] == 1 for r in self.rows), 18)
        self.assertEqual(sum(r["integration_dimensions"] == 2 for r in self.rows), 27)
        for row in self.rows:
            with self.subTest(framing=row["framing"], a=row["identity_a"], b=row["identity_b"]):
                self.assertLessEqual(row["numerical_diagnostic"], row["absolute_tolerance"])
                self.assertAlmostEqual(row["p_positive"] + row["p_negative"], 1, places=12)
                if row["raw_direction"]:
                    key = "p_positive" if row["raw_direction"] > 0 else "p_negative"
                    self.assertEqual(row["support_raw_direction"], row[key])

    def test_exact_zero_is_neutral_but_its_posterior_is_retained(self):
        neutral = [r for r in self.rows if r["raw_direction"] == 0]
        self.assertEqual(len(neutral), 1)
        row = neutral[0]
        self.assertEqual((row["framing"], row["identity_a"], row["identity_b"]),
                         ("threat", "Minimal", "collective_excludes"))
        self.assertEqual(row["delta_raw_fraction"], "0")
        self.assertIsNone(row["support_raw_direction"])
        self.assertEqual(row["percentage_label"], "—")
        self.assertFalse(row["shared_baseline"])
        self.assertNotAlmostEqual(row["p_positive"], 0.5, places=3)

    def test_all_saved_cells_match_adaptive_quadrature(self):
        for row in self.rows:
            with self.subTest(framing=row["framing"], a=row["identity_a"], b=row["identity_b"]):
                group = row["group_alpha"], row["group_beta"]
                shape_a = row["baseline_alpha_a"], row["baseline_beta_a"]
                shape_b = None if row["shared_baseline"] else (row["baseline_alpha_b"], row["baseline_beta_b"])
                probabilities, error = _adaptive(group, shape_a, shape_b, 1e-9)
                np.testing.assert_allclose([row["p_positive"], row["p_negative"]],
                                           probabilities, atol=1e-9, rtol=0)

    def test_collective_variants_share_parameter_and_do_not_duplicate_counts(self):
        for row in self.rows:
            if row["identity_a"] == "collective_excludes" and row["identity_b"] == "collective_includes":
                self.assertTrue(row["shared_baseline"])
                self.assertEqual(row["baseline_trials_a"], 60 if row["framing"] == "pooled" else 30)
                self.assertEqual(row["baseline_alpha_a"], row["baseline_positives_a"] + 0.5)

    def test_pooled_counts_and_shared_symmetric_colour_scale(self):
        for row in self.rows:
            if row["framing"] == "pooled":
                self.assertEqual(row["completed_groups"], 50)
                self.assertEqual(row["baseline_trials_a"], 60)
                k = sum(self.counts[(f, row["identity_a"], row["identity_b"])][0] for f in FRAMINGS[:2])
                self.assertEqual(row["group_alpha"], k + 0.5)
        for framing in FRAMINGS:
            matrix = colour_matrix(self.rows, framing)
            np.testing.assert_allclose(matrix, matrix.T, equal_nan=True)
            self.assertLessEqual(np.nanmax(abs(matrix)), 1)
            self.assertEqual(np.isnan(matrix).sum(), 2 if framing == "threat" else 0)

    def test_matches_original_unsmoothed_february_grid(self):
        path = self.folder / "Feb no smoothing/multi_agent_grid_feb_data_values.csv"
        with path.open(newline="", encoding="utf-8-sig") as stream:
            old = {(r["framing"], r["identity_a"], r["identity_b"]): r for r in csv.DictReader(stream)}
        for row in self.rows:
            original = old[(row["framing"], row["identity_a"], row["identity_b"])]
            self.assertAlmostEqual(row["delta_raw"], float(original["delta"]), places=14)
            self.assertEqual(row["raw_direction"], (Fraction(row["delta_raw_fraction"]) > 0)
                             - (Fraction(row["delta_raw_fraction"]) < 0))


class AnalysisRoutingTests(unittest.TestCase):
    def setUp(self):
        self.config = {"data_mode": "multi_agent", "batch_name": "all_pairs_combined",
                       "p_c_choice": "feb_data", "multi_agent_grid": False,
                       "baseline_bar_chart": False, "uncertainty_grid": True}

    def test_uncertainty_only_route_and_smoothing_independence(self):
        with patch("analysis.uncertainty_grid.create", return_value=[]) as create:
            for smoothing in ["none", "jeffreys"]:
                config = copy.deepcopy(self.config)
                config.update(smoothing=smoothing, grid_metric="log_relative_risk")
                self.assertEqual(analysis.run(config), [])
            self.assertEqual(create.call_count, 2)

    def test_douglas_is_rejected_before_generating_outputs(self):
        self.config["p_c_choice"] = "Douglas"
        with self.assertRaisesRegex(ValueError, "feb_data"):
            analysis.run(self.config)

    def test_old_configuration_can_omit_new_switch(self):
        self.config.pop("uncertainty_grid")
        self.config["multi_agent_grid"] = True
        with patch("analysis.multi_agent_grid.create", return_value=[]):
            self.assertEqual(analysis.run(self.config), [])


if __name__ == "__main__":
    unittest.main()
