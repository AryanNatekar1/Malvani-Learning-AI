"""Guided-problem flow that gives hints before solutions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from lesson_models import Challenge


def _normalized_answer(answer: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", answer.lower())).strip()


@dataclass(frozen=True)
class AttemptFeedback:
    """Feedback after an attempt, without automatically exposing the solution."""

    correct: bool | None
    message: str


class GuidedProblemSession:
    """Keep the challenge, attempts, and solution reveal as separate actions."""

    def __init__(self, challenge: Challenge) -> None:
        self.challenge = challenge
        self.attempts = 0
        self.hint_requests = 0

    def submit_attempt(self, answer: str) -> AttemptFeedback:
        """Assess answers only when the lesson defines accepted answers."""
        self.attempts += 1
        if not self.challenge.accepted_answers:
            return AttemptFeedback(
                correct=None,
                message="Write down your reasoning, then compare it with the hint or solution.",
            )

        normalized = _normalized_answer(answer)
        accepted = {_normalized_answer(value) for value in self.challenge.accepted_answers}
        if normalized in accepted:
            return AttemptFeedback(True, "Correct. You solved it independently.")
        return AttemptFeedback(False, "Not yet. Use the hint and try once more before viewing the solution.")

    def hint(self) -> str:
        """Return the next authored scaffold, not the full answer."""
        hint_index = min(self.hint_requests, len(self.challenge.progressive_hints) - 1)
        self.hint_requests += 1
        return self.challenge.progressive_hints[hint_index]

    def solution(self) -> str:
        """Return the stored solution only when the learner asks for it."""
        return self.challenge.solution
