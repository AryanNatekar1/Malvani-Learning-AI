"""Tests for the local, formula-bound interactive visual learning helpers."""

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from visual_learning import (
    PREDICTION_GREATER,
    PREDICTION_SAME,
    PREDICTION_SMALLER,
    compare_momentum_size,
    evaluate_momentum_prediction,
    make_momentum_state,
    momentum_description,
    momentum_prediction_pending_description,
)


class MomentumVisualLearningTests(unittest.TestCase):
    def test_momentum_uses_the_stored_relationship_between_mass_and_velocity(self) -> None:
        state = make_momentum_state(2, 5)
        self.assertEqual(state.momentum, 10)
        self.assertEqual(state.direction, "right")
        self.assertIn("10 kg m/s right", momentum_description(state))

    def test_negative_velocity_changes_direction_without_hiding_the_sign_meaning(self) -> None:
        state = make_momentum_state(3, -4)
        self.assertEqual(state.momentum, -12)
        self.assertEqual(state.direction, "left")
        self.assertIn("12 kg m/s left", momentum_description(state))

    def test_zero_velocity_has_zero_momentum(self) -> None:
        state = make_momentum_state(6, 0)
        self.assertEqual(state.momentum, 0)
        self.assertIn("at rest", momentum_description(state))

    def test_mass_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            make_momentum_state(0, 5)

    def test_visual_state_rejects_non_finite_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            make_momentum_state(float("nan"), 5)
        with self.assertRaisesRegex(ValueError, "finite"):
            make_momentum_state(2, float("inf"))

    def test_prediction_comparison_reports_greater_smaller_and_same_momentum_sizes(
        self,
    ) -> None:
        reference = make_momentum_state(2, 5)

        self.assertEqual(
            compare_momentum_size(reference, make_momentum_state(4, 3)),
            PREDICTION_GREATER,
        )
        self.assertEqual(
            compare_momentum_size(reference, make_momentum_state(2, 3)),
            PREDICTION_SMALLER,
        )
        self.assertEqual(
            compare_momentum_size(reference, make_momentum_state(5, 2)),
            PREDICTION_SAME,
        )

    def test_prediction_result_reveals_size_and_keeps_direction_distinct(self) -> None:
        reference = make_momentum_state(2, 5)
        candidate = make_momentum_state(5, -2)

        result = evaluate_momentum_prediction("same", reference, candidate)

        self.assertTrue(result.correct)
        self.assertEqual(result.actual, PREDICTION_SAME)
        self.assertIn("direction is different", result.message)

    def test_prediction_rejects_unknown_choice_and_pending_text_hides_candidate_result(
        self,
    ) -> None:
        reference = make_momentum_state(2, 5)
        candidate = make_momentum_state(4, 3)

        with self.assertRaisesRegex(ValueError, "greater, smaller, or the same"):
            evaluate_momentum_prediction("maybe", reference, candidate)
        pending = momentum_prediction_pending_description(reference, candidate)
        self.assertIn("Prediction pending", pending)
        self.assertNotIn("12 kg m/s", pending)


if __name__ == "__main__":
    unittest.main()
