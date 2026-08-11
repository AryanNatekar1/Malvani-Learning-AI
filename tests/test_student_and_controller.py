"""Tests for local-only progress persistence and application controller flow."""

import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from app_controller import AppController, LearningPreferences
from student_engine import ProfileStore, StudentProfile


class StudentAndControllerTests(unittest.TestCase):
    def test_profile_records_aggregate_progress(self) -> None:
        profile = StudentProfile()
        profile.record_lesson("gravity")
        profile.record_question("gravity", False)
        self.assertEqual(profile.topics_studied, ["gravity"])
        self.assertEqual(profile.accuracy, 0.0)
        self.assertEqual(profile.weak_topics(), ["gravity"])

    def test_profile_store_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = ProfileStore(Path(temporary_directory) / "profile.json")
            profile = StudentProfile(class_level="Class 9", preferred_language="Marathi")
            profile.record_question("momentum", True)
            store.save(profile)
            loaded = store.load()
            self.assertEqual(loaded.class_level, "Class 9")
            self.assertEqual(loaded.questions_correct, 1)

    def test_controller_runs_structured_lesson_and_quiz_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = AppController(
                profile_store=ProfileStore(Path(temporary_directory) / "profile.json")
            )
            controller.save_preferences(
                LearningPreferences("Malvani", "Class 9", "Physics", True)
            )
            response = controller.answer_question("What is momentum?")
            self.assertTrue(response.is_structured)
            self.assertIn("Showing English", response.text)
            quiz = controller.start_quiz()
            assert quiz is not None
            self.assertEqual(quiz.topic, "momentum")
            result = controller.submit_quiz_answer("12")
            assert result is not None
            self.assertTrue(result.correct)
            self.assertIn("Correct submissions: 1", controller.progress_text())

    def test_controller_retains_legacy_topic_support(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = AppController(
                profile_store=ProfileStore(Path(temporary_directory) / "profile.json")
            )
            response = controller.answer_question("Explain acceleration")
            self.assertFalse(response.is_structured)
            self.assertIn("Acceleration", response.text)


if __name__ == "__main__":
    unittest.main()
