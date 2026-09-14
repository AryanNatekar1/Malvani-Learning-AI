"""Tests for structured teaching responses, culture safety, and language fallback."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from culture_engine import context_availability_notice, student_context_text
from knowledge_engine import get_structured_lesson
from language_engine import (
    CONTRIBUTED_LANGUAGE_DIR,
    INTERFACE_TEXT,
    SUPPORTED_LANGUAGES,
    interface_text,
    load_contributed_interface_text,
    resolve_lesson_language,
)
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

    def test_every_supported_language_resolves_without_inventing_content(self) -> None:
        """No lesson has reviewed non-English text yet, so all must fall back."""
        for language in SUPPORTED_LANGUAGES:
            with self.subTest(language=language):
                resolution = resolve_lesson_language(self.lesson, language)
                self.assertEqual(resolution.resolved, "English")
                if language == "English":
                    self.assertIsNone(resolution.notice)
                else:
                    self.assertIn(language, resolution.notice or "")

    def test_konkani_and_malvani_have_no_built_in_labels(self) -> None:
        """Guessing at a dialect's spelling is the invention this project refuses."""
        for language in ("Konkani", "Malvani"):
            with self.subTest(language=language):
                self.assertNotIn(language, INTERFACE_TEXT)
                self.assertEqual(interface_text("progress", language), "Progress")

    def test_hindi_labels_are_translated_not_passed_through(self) -> None:
        self.assertEqual(interface_text("progress", "Hindi"), "प्रगति")
        self.assertNotEqual(
            interface_text("start_learning", "Hindi"),
            interface_text("start_learning", "English"),
        )

    def test_unreviewed_contributed_language_file_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Malvani.json"
            path.write_text(
                json.dumps(
                    {
                        "language": "Malvani",
                        "verification_status": "NEEDS_REVIEW",
                        "reviewed_by": "",
                        "interface_text": {"progress": "draft-word"},
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(load_contributed_interface_text(Path(directory)), {})

    def test_reviewed_contributed_language_file_supplies_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Malvani.json"
            path.write_text(
                json.dumps(
                    {
                        "language": "Malvani",
                        "verification_status": "VERIFIED",
                        "reviewed_by": "A named Malvani speaker",
                        "source": "native speaker, Sindhudurg",
                        "interface_text": {"progress": "reviewed-word", "blank": "   "},
                    }
                ),
                encoding="utf-8",
            )
            contributed = load_contributed_interface_text(Path(directory))
            self.assertEqual(contributed["Malvani"]["progress"], "reviewed-word")
            self.assertNotIn("blank", contributed["Malvani"])

    def test_malformed_language_file_does_not_stop_the_app(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "Broken.json").write_text("{not json", encoding="utf-8")
            self.assertEqual(load_contributed_interface_text(Path(directory)), {})

    def test_shipped_language_templates_are_not_usable_as_is(self) -> None:
        """The example files must stay inert until a speaker reviews a copy."""
        self.assertEqual(load_contributed_interface_text(CONTRIBUTED_LANGUAGE_DIR), {})

    def test_solution_is_only_shown_by_explicit_action(self) -> None:
        response = self.engine.build_response(self.lesson, "Class 9", "English", action="solution")
        self.assertIn("SOLUTION", response.as_text())
        self.assertIn("jump higher", response.as_text())


if __name__ == "__main__":
    unittest.main()
