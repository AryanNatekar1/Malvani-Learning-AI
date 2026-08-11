"""Tests for local lesson lookup and loading."""

import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from knowledge_engine import (
    available_subjects,
    find_topic,
    get_structured_lesson,
    load_lesson,
    load_structured_lessons,
)


class KnowledgeEngineTests(unittest.TestCase):
    def test_finds_a_known_topic(self) -> None:
        self.assertEqual(find_topic("What is gravity?"), "gravity")

    def test_returns_none_for_an_unknown_topic(self) -> None:
        self.assertIsNone(find_topic("What is plate tectonics?"))

    def test_returns_none_when_a_knowledge_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_data_dir = Path(temporary_directory)
            self.assertIsNone(load_lesson("gravity", temporary_data_dir))

    def test_recognizes_newton_laws_with_an_apostrophe(self) -> None:
        self.assertEqual(find_topic("Explain Newton's laws of motion"), "newton")

    def test_does_not_match_homework_as_physics_work(self) -> None:
        self.assertIsNone(find_topic("How do I work out this homework answer?"))

    def test_loads_migrated_structured_lessons(self) -> None:
        lesson = get_structured_lesson("gravity")
        self.assertIsNotNone(lesson)
        assert lesson is not None
        self.assertEqual(lesson.subject, "Physics")
        self.assertEqual(lesson.topic, "gravity")
        self.assertGreaterEqual(len(load_structured_lessons()), 8)
        self.assertEqual(
            available_subjects(),
            ("Biology", "Chemistry", "Computer Science", "Mathematics", "Physics"),
        )

    def test_finds_topics_from_new_subject_lessons(self) -> None:
        self.assertEqual(find_topic("Can you explain fractions?"), "fractions")
        self.assertEqual(find_topic("What is photosynthesis?"), "photosynthesis")
        self.assertEqual(find_topic("Teach me an algorithm"), "algorithms")


if __name__ == "__main__":
    unittest.main()
