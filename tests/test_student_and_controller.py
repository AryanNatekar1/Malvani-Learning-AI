"""Tests for local-only progress persistence and application controller flow."""

import sqlite3
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from app_controller import AppController, LearningPreferences
from context_engine import VERIFIED, ContextRecord, ContextRepository
from problem_scenario_engine import ProblemScenarioRepository, load_problem_scenarios
from student_engine import ProfileStore, SQLiteProfileStore, StudentProfile


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

    def test_problem_solver_is_separate_from_challenge_and_quiz_then_unlocks_go_deeper(self) -> None:
        """The new model flow must not overwrite existing lesson learning state."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            profile_path = Path(temporary_directory) / "profile.json"
            controller = AppController(profile_store=ProfileStore(profile_path))
            controller.answer_question("Explain momentum")
            controller.lesson_action("challenge")
            challenge_session = controller.current_problem_session
            controller.start_quiz()
            quiz_session = controller.quiz_session

            opened = controller.start_problem_solver()
            self.assertIn("Illustrative computer-model values", opened.text)
            self.assertIs(controller.current_problem_session, challenge_session)
            self.assertIs(controller.quiz_session, quiz_session)
            view = controller.problem_solver_view()
            assert view is not None
            self.assertEqual((view.current_step_number, view.total_steps), (1, 3))
            self.assertFalse(controller.can_go_deeper())

            blank = controller.submit_problem_solver_attempt("   ")
            assert blank is not None
            self.assertIsNone(blank.correct)
            self.assertEqual(controller.profile.problem_solver_attempts, 0)
            self.assertIn("Try one answer", controller.reveal_problem_solver_solution().text)
            self.assertIn("FIRST, WORK THE MODEL", controller.start_go_deeper().text)

            wrong = controller.submit_problem_solver_attempt("9")
            assert wrong is not None
            self.assertFalse(wrong.correct)
            self.assertEqual(controller.profile.problem_solver_attempts, 1)
            self.assertEqual(controller.profile.problem_solver_correct, 0)
            solution = controller.reveal_problem_solver_solution()
            self.assertIn("MODEL SOLUTION", solution.text)
            self.assertIn("does not prove", solution.text)
            self.assertTrue(controller.can_go_deeper())

            go_deeper = controller.start_go_deeper()
            self.assertIn("GO DEEPER: RESEARCH QUESTION", go_deeper.text)
            self.assertIn("not observations from your area", go_deeper.text)
            check_in = controller.submit_research_response(
                "hypothesis",
                "If velocity doubles while mass stays fixed, momentum doubles.",
            )
            self.assertIn("cannot determine whether it is scientifically correct", check_in.text)
            self.assertEqual(controller.profile.research_stages_completed, 1)
            saved = profile_path.read_text(encoding="utf-8")
            self.assertNotIn("If velocity doubles", saved)
            self.assertIn("Problem Solver model-step attempts: 1", controller.progress_text())

    def test_problem_solver_state_resets_for_same_topic_reload_and_topic_change(self) -> None:
        """A same-topic full lesson reload must not leave stale solver controls alive."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = AppController(
                profile_store=ProfileStore(Path(temporary_directory) / "profile.json")
            )
            controller.answer_question("Explain momentum")
            controller.start_problem_solver()
            version_before_reload = controller.learning_state_version
            self.assertIsNotNone(controller.current_scenario_session)

            controller.answer_question("Explain momentum")
            self.assertGreater(controller.learning_state_version, version_before_reload)
            self.assertIsNone(controller.current_scenario_session)

            controller.start_problem_solver()
            self.assertIsNotNone(controller.current_scenario_session)
            controller.answer_question("Explain force")
            self.assertIsNone(controller.current_scenario_session)
            self.assertFalse(controller.problem_scenario_available())

    def test_controller_problem_solver_matches_the_active_lesson_subject_and_topic(self) -> None:
        """A same-named future topic in another subject must not leak into Physics."""
        scenario = load_problem_scenarios()[0]
        wrong_subject = replace(
            scenario,
            identifier="computer-science.momentum.wrong-subject",
            subject="Computer Science",
            title="Wrong-subject momentum model",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = AppController(
                profile_store=ProfileStore(Path(temporary_directory) / "profile.json"),
                scenario_repository=ProblemScenarioRepository([wrong_subject, scenario]),
            )
            controller.answer_question("Explain momentum")
            response = controller.start_problem_solver()
            self.assertIn("Compare Two Model Carts", response.text)
            self.assertNotIn("Wrong-subject", response.text)

    def test_problem_solver_and_research_text_are_absent_from_sqlite(self) -> None:
        """Model responses and research writing never cross the local event boundary."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "learning.db"
            store = SQLiteProfileStore(database_path)
            controller = AppController(profile_store=store)
            controller.answer_question("Explain momentum")
            controller.start_problem_solver()
            raw_attempt = "this unique model attempt must never be saved"
            controller.submit_problem_solver_attempt(raw_attempt)
            controller.reveal_problem_solver_solution()
            controller.start_go_deeper()
            raw_hypothesis = "this unique research hypothesis must never be saved"
            controller.submit_research_response("hypothesis", raw_hypothesis)

            database_bytes = database_path.read_bytes()
            self.assertNotIn(raw_attempt.encode("utf-8"), database_bytes)
            self.assertNotIn(raw_hypothesis.encode("utf-8"), database_bytes)
            self.assertEqual(store.event_count("scenario_attempt"), 1)
            self.assertEqual(store.event_count("research_hypothesis_completed"), 1)
            connection = sqlite3.connect(database_path)
            try:
                rows = connection.execute(
                    "SELECT event_type, topic, correct FROM learning_events "
                    "WHERE event_type LIKE 'scenario_%' OR event_type LIKE 'research_%'"
                ).fetchall()
            finally:
                connection.close()
            self.assertTrue(rows)
            self.assertTrue(all(len(row) == 3 for row in rows))

    def test_research_check_ins_follow_the_guided_order_without_saving_writing(self) -> None:
        """A later prompt cannot claim progress before the preceding thinking step."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "learning.db"
            store = SQLiteProfileStore(database_path)
            controller = AppController(profile_store=store)
            controller.answer_question("Explain momentum")
            controller.start_problem_solver()
            for answer in ("6.0", "p = 6 kg m/s", "equal"):
                feedback = controller.submit_problem_solver_attempt(answer)
                assert feedback is not None
                self.assertTrue(feedback.correct)
            controller.start_go_deeper()

            view = controller.research_view()
            assert view is not None
            self.assertEqual(view.next_stage, "hypothesis")
            private_out_of_order_text = "my private reflection must not be saved"
            blocked = controller.submit_research_response("reflection", private_out_of_order_text)
            self.assertIn("guided order", blocked.text)
            self.assertEqual(controller.profile.research_stages_completed, 0)
            self.assertEqual(store.event_count("research_reflection_completed"), 0)
            self.assertNotIn(private_out_of_order_text.encode("utf-8"), database_path.read_bytes())

            recorded = controller.submit_research_response(
                "hypothesis",
                "If velocity rises while mass stays fixed, momentum rises.",
            )
            self.assertIn("writing check-in recorded", recorded.text)
            self.assertEqual(controller.profile.research_stages_completed, 1)
            self.assertEqual(store.event_count("research_hypothesis_completed"), 1)
            next_view = controller.research_view()
            assert next_view is not None
            self.assertEqual(next_view.next_stage, "analysis")

            later_check_ins = (
                (
                    "analysis",
                    "Mass stayed fixed, velocity changed, and model momentum increased.",
                    "proposal",
                ),
                (
                    "proposal",
                    "Keep mass fixed, change velocity, and record model momentum.",
                    "reflection",
                ),
                (
                    "reflection",
                    "A real moving object would need real measurements and assumptions.",
                    None,
                ),
            )
            for stage, writing, expected_next_stage in later_check_ins:
                response = controller.submit_research_response(stage, writing)
                self.assertIn("writing check-in recorded", response.text)
                view = controller.research_view()
                assert view is not None
                self.assertEqual(view.next_stage, expected_next_stage)
                self.assertNotIn(writing.encode("utf-8"), database_path.read_bytes())

            self.assertEqual(controller.profile.research_stages_completed, 4)
            self.assertEqual(store.event_count("research_reflection_completed"), 1)
            duplicate = controller.submit_research_response(
                "reflection",
                "A replacement reflection must not be saved.",
            )
            self.assertIn("already recorded", duplicate.text)
            self.assertEqual(controller.profile.research_stages_completed, 4)
            self.assertEqual(store.event_count("research_reflection_completed"), 1)


if __name__ == "__main__":
    unittest.main()
