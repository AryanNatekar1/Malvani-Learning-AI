"""Offline quiz scoring for structured lesson questions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from lesson_models import QuizQuestion


def _normalize_answer(answer: str) -> str:
    """Normalize simple learner responses without trying to judge open essays."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", answer.lower())).strip()


@dataclass(frozen=True)
class QuizEvaluation:
    """Result of one local quiz answer."""

    correct: bool
    message: str
    explanation: str
    can_retry: bool


def evaluate_answer(question: QuizQuestion, submitted_answer: str) -> QuizEvaluation:
    """Evaluate a multiple-choice, numeric, true/false, or exact short answer."""
    normalized_submitted = _normalize_answer(submitted_answer)
    normalized_correct = {_normalize_answer(answer) for answer in question.correct_answers}
    correct = normalized_submitted in normalized_correct

    if correct:
        message = "Correct. Good reasoning."
    else:
        message = "Not quite. Try the hint, then attempt the question again."
    return QuizEvaluation(
        correct=correct,
        message=message,
        explanation=question.explanation,
        can_retry=not correct,
    )


class QuizSession:
    """Small stateful session for one lesson's ordered quiz questions."""

    def __init__(self, questions: tuple[QuizQuestion, ...]) -> None:
        self.questions = questions
        self.current_index = 0
        self.correct_count = 0
        self.attempt_count = 0
        self._attempts_by_question: dict[int, int] = {}
        self._hints_by_question: dict[int, int] = {}

    @property
    def current_question(self) -> QuizQuestion | None:
        if self.current_index >= len(self.questions):
            return None
        return self.questions[self.current_index]

    @property
    def is_complete(self) -> bool:
        return self.current_question is None

    def submit(self, answer: str) -> QuizEvaluation | None:
        """Score one answer; advance only after a correct answer.

        A wrong answer remains on the same question so the student can use the
        hint and retry instead of being rushed past the learning opportunity.
        """
        question = self.current_question
        if question is None:
            return None
        result = evaluate_answer(question, answer)
        self.attempt_count += 1
        self._attempts_by_question[self.current_index] = (
            self._attempts_by_question.get(self.current_index, 0) + 1
        )
        if result.correct:
            self.correct_count += 1
            self.current_index += 1
        return result

    def hint(self) -> str | None:
        """Return the next authored hint for the active question."""
        question = self.current_question
        if question is None:
            return None
        hint_count = self._hints_by_question.get(self.current_index, 0)
        hint_index = min(hint_count, len(question.progressive_hints) - 1)
        self._hints_by_question[self.current_index] = hint_count + 1
        return question.progressive_hints[hint_index]

    def can_reveal_current(self) -> bool:
        """Allow an escape path after two real attempts or two hint requests."""
        if self.current_question is None:
            return False
        return (
            self._attempts_by_question.get(self.current_index, 0) >= 2
            or self._hints_by_question.get(self.current_index, 0) >= 2
        )

    def reveal_and_continue(self) -> QuizEvaluation | None:
        """Reveal the stored explanation and move on without claiming mastery."""
        question = self.current_question
        if question is None or not self.can_reveal_current():
            return None
        self.current_index += 1
        return QuizEvaluation(
            correct=False,
            message="The explanation is now shown. Mark this as a topic to review and continue.",
            explanation=question.explanation,
            can_retry=False,
        )
