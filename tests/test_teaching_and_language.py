"""Tests for structured teaching responses, culture safety, and language fallback."""

import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from culture_engine import context_availability_notice, student_context_text
from knowledge_engine import get_structured_lesson
from language_engine import interface_text, resolve_lesson_language
from teaching_engine import TeachingEngine


class TeachingAndLanguageTests(unittest.TestCase):
    def setUp(self) -> None:
        lesson = get_structured_lesson("gravity")
        assert lesson is not None
        self.lesson = lesson
        self.engine = TeachingEngine()

    def test_beginner_response_uses_simple_explanation(self) -> None:
        response = self.engine.build_response(self.lesson, "Beginner", "English")
        text = response.as_text()
        self.assertIn("Gravity is the force", text)
        self.assertIn("TRY IT", text)
        self.assertNotIn("SOLUTION", text)

    def test_unverified_context_is_hidden_from_students(self) -> None:
        assert self.lesson.local_example is not None
        self.assertIsNone(student_context_text(self.lesson.local_example))
        self.assertIsNotNone(context_availability_notice(self.lesson.local_example))
        response = self.engine.build_response(self.lesson, "Class 9", "English")
        self.assertNotIn("A mango falling", response.as_text())
        self.assertIn("SINDHUDURG CONNECTION", response.as_text())
        self.assertIn("verified Sindhudurg or Konkan connection", response.as_text())
        self.assertNotIn("draft exists", response.as_text())

    def test_malvani_falls_back_without_claiming_translation(self) -> None:
        resolution = resolve_lesson_language(self.lesson, "Malvani")
        self.assertEqual(resolution.resolved, "English")
        self.assertIn("Reviewed Malvani", resolution.notice or "")
        self.assertEqual(interface_text("start_learning", "Malvani"), "Start Learning")

    def test_solution_is_only_shown_by_explicit_action(self) -> None:
        response = self.engine.build_response(self.lesson, "Class 9", "English", action="solution")
        self.assertIn("SOLUTION", response.as_text())
        self.assertIn("jump higher", response.as_text())


if __name__ == "__main__":
    unittest.main()
