"""Tests for offline quiz and guided-problem behavior."""

import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from knowledge_engine import get_structured_lesson
from problem_engine import GuidedProblemSession
from quiz_engine import QuizSession, evaluate_answer


class QuizAndProblemTests(unittest.TestCase):
    def setUp(self) -> None:
        lesson = get_structured_lesson("momentum")
        assert lesson is not None
        self.lesson = lesson

    def test_numerical_quiz_accepts_units_or_number(self) -> None:
        question = self.lesson.quiz_questions[0]
        self.assertTrue(evaluate_answer(question, "12 kg m/s").correct)
        self.assertTrue(evaluate_answer(question, "12").correct)
        self.assertFalse(evaluate_answer(question, "15").correct)

    def test_quiz_session_tracks_completion(self) -> None:
        session = QuizSession(self.lesson.quiz_questions)
        result = session.submit("12")
        assert result is not None
        self.assertTrue(result.correct)
        self.assertTrue(session.is_complete)
        self.assertEqual(session.correct_count, 1)

    def test_quiz_keeps_wrong_answer_on_same_question_for_retry(self) -> None:
        session = QuizSession(self.lesson.quiz_questions)
        result = session.submit("15")
        assert result is not None
        self.assertTrue(result.can_retry)
        self.assertFalse(session.is_complete)
        self.assertEqual(session.current_index, 0)
        session.submit("12")
        self.assertTrue(session.is_complete)

    def test_quiz_reveals_after_meaningful_attempts(self) -> None:
        session = QuizSession(self.lesson.quiz_questions)
        session.submit("15")
        session.submit("14")
        self.assertTrue(session.can_reveal_current())
        result = session.reveal_and_continue()
        assert result is not None
        self.assertIn("review", result.message.lower())
        self.assertTrue(session.is_complete)

    def test_problem_gives_hint_before_solution(self) -> None:
        assert self.lesson.challenge is not None
        session = GuidedProblemSession(self.lesson.challenge)
        feedback = session.submit_attempt("9")
        self.assertFalse(feedback.correct)
        self.assertIn("mass", session.hint())
        self.assertIn("10 kg m/s", session.solution())

    def test_problem_hints_progress_instead_of_repeating(self) -> None:
        assert self.lesson.challenge is not None
        session = GuidedProblemSession(self.lesson.challenge)
        self.assertNotEqual(session.hint(), session.hint())


if __name__ == "__main__":
    unittest.main()
