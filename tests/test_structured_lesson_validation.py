"""Tests for clear structured-lesson validation errors."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from knowledge_engine import load_structured_lessons
from lesson_models import LessonFormatError


class StructuredLessonValidationTests(unittest.TestCase):
    def test_rejects_lesson_without_english_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            lesson_path = Path(temporary_directory) / "bad.json"
            lesson_path.write_text(
                json.dumps(
                    {
                        "id": "test.bad",
                        "title": "Bad",
                        "subject": "Physics",
                        "topic": "bad",
                        "levels": ["Beginner"],
                        "content": {"Marathi": {"simple_explanation": "x"}},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(LessonFormatError):
                load_structured_lessons(Path(temporary_directory))

    def test_rejects_lesson_without_language_review_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            lesson_path = Path(temporary_directory) / "missing-language-metadata.json"
            lesson_path.write_text(
                json.dumps(
                    {
                        "id": "test.metadata",
                        "title": "Metadata test",
                        "subject": "Physics",
                        "topic": "metadata",
                        "levels": ["Beginner"],
                        "content": {"English": {"simple_explanation": "x"}},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(LessonFormatError):
                load_structured_lessons(Path(temporary_directory))


if __name__ == "__main__":
    unittest.main()
