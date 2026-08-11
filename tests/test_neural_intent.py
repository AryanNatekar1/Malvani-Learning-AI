"""Tests for the local feed-forward UI intent classifier."""

import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from neural_intent import UNKNOWN_INTENT, build_trained_model, predict_intent


class NeuralIntentTests(unittest.TestCase):
    def test_classifies_each_supported_interface_intent(self) -> None:
        examples = {
            "Please explain gravity simply.": "lesson",
            "Can I have a hint?": "hint",
            "Give me a practice challenge.": "challenge",
            "Show me the solution now.": "solution",
            "Start a physics quiz.": "quiz",
        }

        for text, expected_intent in examples.items():
            with self.subTest(text=text):
                intent, confidence = predict_intent(text)
                self.assertEqual(intent, expected_intent)
                self.assertGreaterEqual(confidence, 0.60)
                self.assertLessEqual(confidence, 1.0)

    def test_uses_unknown_for_empty_or_unrecognised_requests(self) -> None:
        for text in ("", "   ", "zorb blim flarn"):
            with self.subTest(text=text):
                intent, confidence = predict_intent(text)
                self.assertEqual(intent, UNKNOWN_INTENT)
                self.assertEqual(confidence, 0.0)

    def test_training_is_deterministic(self) -> None:
        first_model = build_trained_model()
        second_model = build_trained_model()

        self.assertEqual(
            first_model.predict("Give me a hint"),
            second_model.predict("Give me a hint"),
        )
        self.assertEqual(first_model.input_to_hidden, second_model.input_to_hidden)


if __name__ == "__main__":
    unittest.main()
