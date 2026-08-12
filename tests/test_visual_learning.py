"""Tests for the local, formula-bound interactive visual learning helpers."""

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from visual_learning import make_momentum_state, momentum_description


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


if __name__ == "__main__":
    unittest.main()
