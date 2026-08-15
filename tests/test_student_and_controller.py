"""Tests for local-only progress persistence and application controller flow."""

import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from app_controller import AppController, LearningPreferences
from context_engine import VERIFIED, ContextRecord, ContextRepository
from student_engine import ProfileStore, StudentProfile


class FailingProfileStore:
    """Test double for a local storage device that cannot be written."""

    def load(self) -> StudentProfile:
        return StudentProfile()

    def save(self, _profile: StudentProfile) -> None:
        raise OSError("storage unavailable")

    def record_event(
        self, _event_type: str, _topic: str | None = None, _correct: bool | None = None
    ) -> None:
        raise OSError("storage unavailable")


class UnreadableProfileStore:
    """Test double for a local storage device that cannot be read at startup."""

    def load(self) -> StudentProfile:
        raise OSError("storage unavailable")

    def save(self, _profile: StudentProfile) -> None:
        pass


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

    def test_profile_store_ignores_unknown_or_malformed_local_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "profile.json"
            path.write_text(
                '{"class_level": "Class 9", "questions_attempted": -1, '
                '"topic_attempts": {"momentum": "many"}, "unknown": "ignored"}',
                encoding="utf-8",
            )
            profile = ProfileStore(path).load()
            self.assertEqual(profile.class_level, "Class 9")
            self.assertEqual(profile.questions_attempted, 0)
            self.assertEqual(profile.topic_attempts, {})

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

    def test_controller_progress_uses_an_explainable_local_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = AppController(
                profile_store=ProfileStore(Path(temporary_directory) / "profile.json")
            )
            controller.answer_question("What is momentum?")
            controller.start_quiz()
            result = controller.submit_quiz_answer("0")
            assert result is not None
            recommendation = controller.learning_recommendation()
            self.assertEqual(recommendation.kind, "review")
            self.assertEqual(recommendation.topic, "momentum")
            self.assertIn("0 of 1", recommendation.reason)
            self.assertIn("Reason:", controller.progress_text())

    def test_controller_keeps_learning_when_local_progress_cannot_be_saved(self) -> None:
        controller = AppController(profile_store=FailingProfileStore())
        response = controller.answer_question("What is gravity?")
        self.assertTrue(response.is_structured)
        notice = controller.persistence_notice()
        assert notice is not None
        self.assertIn("could not be saved", notice)
        self.assertIn("Local storage note", controller.dashboard_text())

    def test_controller_starts_a_safe_session_when_local_progress_cannot_be_read(self) -> None:
        controller = AppController(profile_store=UnreadableProfileStore())
        self.assertEqual(controller.profile.topics_studied, [])
        notice = controller.persistence_notice()
        assert notice is not None
        self.assertIn("could not be read", notice)

    def test_manual_context_is_topic_scoped_and_never_saved_as_profile_data(self) -> None:
        """A reviewed manual choice is useful, but not a stored location proxy."""
        context = ContextRecord(
            identifier="momentum-cart-model",
            title="Computer cart model",
            category="physics model",
            educational_prompt=(
                "Use two labelled carts in a computer model to compare mass, velocity, "
                "and momentum."
            ),
            topics=("momentum",),
            verification_status=VERIFIED,
            source="Teacher-reviewed classroom model",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            profile_path = Path(temporary_directory) / "profile.json"
            controller = AppController(
                profile_store=ProfileStore(profile_path),
                context_repository=ContextRepository([context]),
            )

            selection = controller.select_manual_context("momentum-cart-model")
            self.assertTrue(selection.is_available)
            self.assertIsNone(controller.active_manual_context())
            momentum = controller.answer_question("Explain momentum")

            self.assertIn("MANUAL LEARNING CONTEXT", momentum.text)
            self.assertIn("You selected this learning context manually", momentum.text)
            self.assertIn("Teacher-reviewed classroom model", momentum.text)
            self.assertIn("momentum-cart-model", controller.selected_manual_context_id or "")
            self.assertNotIn("momentum-cart-model", profile_path.read_text(encoding="utf-8"))

            gravity = controller.answer_question("Explain gravity")
            self.assertNotIn("MANUAL LEARNING CONTEXT", gravity.text)
            self.assertIsNone(controller.active_manual_context())


if __name__ == "__main__":
    unittest.main()
