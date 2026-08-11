"""End-to-end tests for the offline learn-think-try-retry flow."""

import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from ai_provider import OfflineAIProvider
from app_controller import AppController, LearningPreferences
from knowledge_engine import load_student_lesson
from quiz_engine import QuizSession
from reasoning_engine import ReasoningEngine
from student_engine import ProfileStore, SQLiteProfileStore


class LearningLoopTests(unittest.TestCase):
    def _controller(self, directory: str) -> AppController:
        return AppController(profile_store=ProfileStore(Path(directory) / "profile.json"))

    def test_challenge_gates_solution_and_uses_progressive_hints(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = self._controller(temporary_directory)
            controller.answer_question("What is gravity?")
            self.assertIn("Start the challenge first", controller.lesson_action("solution").text)

            controller.lesson_action("challenge")
            self.assertIn("Try the challenge first", controller.lesson_action("solution").text)
            first_hint = controller.lesson_action("hint").text
            second_hint = controller.lesson_action("hint").text
            self.assertNotEqual(first_hint, second_hint)
            self.assertIn("SOLUTION", controller.lesson_action("solution").text)
            self.assertEqual(controller.profile.hints_used, 2)

    def test_challenge_attempt_unlocks_solution_and_records_real_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = self._controller(temporary_directory)
            controller.answer_question("What is momentum?")
            controller.lesson_action("challenge")
            feedback = controller.submit_challenge_attempt("11")
            assert feedback is not None
            self.assertFalse(feedback.correct)
            self.assertIn("10 kg m/s", controller.lesson_action("solution").text)
            self.assertEqual(controller.profile.challenge_attempts, 1)

    def test_reasoning_feedback_is_limited_and_does_not_accept_keyword_nonsense(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = self._controller(temporary_directory)
            controller.answer_question("What is gravity?")
            nonsense = controller.check_reasoning("Earth gravity banana nonsense words")
            assert nonsense is not None
            self.assertEqual(nonsense.category, "insufficient_reasoning")
            useful = controller.check_reasoning(
                "Gravity pulls the object toward Earth because Earth attracts it."
            )
            assert useful is not None
            self.assertEqual(useful.category, "key_ideas_present")
            self.assertIn("cannot fully grade", useful.message)
            self.assertEqual(controller.profile.reasoning_attempts, 2)

    def test_subject_change_clears_lesson_specific_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = self._controller(temporary_directory)
            controller.answer_question("What is gravity?")
            controller.lesson_action("challenge")
            controller.save_preferences(
                LearningPreferences("English", "Class 8", "Mathematics", True)
            )
            self.assertIsNone(controller.current_topic)
            self.assertIsNone(controller.current_problem_session)
            response = controller.answer_question("What is gravity?")
            self.assertIn("available in Physics", response.text)
            self.assertIsNone(controller.current_topic)

    def test_text_quiz_intent_starts_quiz_after_a_lesson_is_open(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = self._controller(temporary_directory)
            controller.answer_question("What is force?")
            response = controller.answer_question("Start a quiz")
            self.assertTrue(response.start_quiz)
            self.assertIsNotNone(controller.quiz_view())

    def test_library_lists_and_opens_real_subject_lessons(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = self._controller(temporary_directory)
            mathematics_lessons = controller.available_lessons("Mathematics")
            self.assertEqual([lesson.topic for lesson in mathematics_lessons], ["fractions"])
            response = controller.open_library_lesson("fractions")
            self.assertTrue(response.is_structured)
            self.assertEqual(controller.preferences().subject, "Mathematics")
            self.assertEqual(controller.current_topic, "fractions")

    def test_quiz_retries_then_reveals_without_claiming_mastery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = self._controller(temporary_directory)
            controller.answer_question("What is gravity?")
            controller.start_quiz()
            first = controller.submit_quiz_answer("Friction")
            assert first is not None
            self.assertTrue(first.can_retry)
            self.assertIsNotNone(controller.quiz_view().question if controller.quiz_view() else None)
            controller.submit_quiz_answer("Magnetism")
            self.assertTrue(controller.can_reveal_quiz_explanation())
            revealed = controller.reveal_quiz_explanation()
            assert revealed is not None
            self.assertFalse(revealed.correct)
            self.assertIn("review", revealed.message.lower())
            self.assertTrue(controller.quiz_view().question is None if controller.quiz_view() else False)
            self.assertEqual(controller.profile.questions_correct, 0)
            self.assertEqual(controller.profile.questions_attempted, 2)

    def test_sqlite_store_persists_profile_and_aggregate_events(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = SQLiteProfileStore(Path(temporary_directory) / "learning.db")
            controller = AppController(profile_store=store)
            controller.answer_question("What is gravity?")
            controller.lesson_action("challenge")
            controller.lesson_action("hint")
            self.assertEqual(store.event_count("lesson_opened"), 1)
            self.assertEqual(store.event_count("challenge_hint"), 1)
            reloaded = SQLiteProfileStore(Path(temporary_directory) / "learning.db").load()
            self.assertEqual(reloaded.hints_used, 1)

    def test_legacy_student_render_hides_unverified_local_sections(self) -> None:
        content = load_student_lesson("gravity")
        assert content is not None
        self.assertIn("Local Context Status", content)
        self.assertNotIn("Devgad", content)
        self.assertNotIn("mango harvesting season", content.lower())

    def test_offline_provider_rejects_neural_false_positive_without_explicit_cue(self) -> None:
        provider = OfflineAIProvider()
        self.assertEqual(provider.generate_response("How do I change language?").intent, "unknown")
        self.assertEqual(provider.generate_response("show me a picture").intent, "unknown")


if __name__ == "__main__":
    unittest.main()
