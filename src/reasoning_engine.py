"""Transparent, local feedback for a student's written reasoning attempt.

This is deliberately not an LLM evaluator. It checks lesson-authored cue words
and response length, then gives limited, honest feedback that encourages a
retry. It must not be presented as a full assessment of a student's thinking.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from lesson_models import Lesson


@dataclass(frozen=True)
class ReasoningFeedback:
    """A deterministic feedback result for one reasoning attempt."""

    category: str
    message: str
    retry_recommended: bool
    hint: str | None = None


def _normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    """Match a cue as complete words instead of a substring inside another word."""
    normalized_phrase = _normalized_text(phrase)
    return f" {normalized_phrase} " in f" {text} "


EXPLANATORY_WORDS = {
    "because",
    "so",
    "therefore",
    "pull",
    "pulls",
    "cause",
    "causes",
    "make",
    "makes",
    "mean",
    "means",
    "when",
    "if",
    "is",
    "are",
}


class ReasoningEngine:
    """Classify a response using only explicit cues provided by a lesson."""

    def evaluate(self, lesson: Lesson, student_reasoning: str) -> ReasoningFeedback:
        """Give safe, limited feedback and never fabricate semantic understanding."""
        normalized_reasoning = _normalized_text(student_reasoning)
        reasoning_words = normalized_reasoning.split()
        if len(reasoning_words) < 5 or not any(
            word in EXPLANATORY_WORDS for word in reasoning_words
        ):
            return ReasoningFeedback(
                category="insufficient_reasoning",
                message=(
                    "Write a complete explanation, not just key words. Name the cause, "
                    "the effect, and how they connect."
                ),
                retry_recommended=True,
                hint=self._lesson_hint(lesson),
            )

        guide = lesson.reasoning_guide
        if guide is None:
            return ReasoningFeedback(
                category="needs_teacher_review",
                message=(
                    "Your reasoning was recorded as an attempt, but this lesson does not yet "
                    "have a local feedback guide. Compare your explanation with the concept and hint."
                ),
                retry_recommended=True,
                hint=self._lesson_hint(lesson),
            )

        if any(
            _contains_phrase(normalized_reasoning, keyword)
            for keyword in guide.misconception_keywords
        ):
            return ReasoningFeedback(
                category="misconception",
                message=guide.misconception_feedback,
                retry_recommended=True,
                hint=self._lesson_hint(lesson),
            )

        matched_keywords = [
            keyword
            for keyword in guide.required_keywords
            if _contains_phrase(normalized_reasoning, keyword)
        ]
        if len(matched_keywords) == len(guide.required_keywords):
            return ReasoningFeedback(
                category="key_ideas_present",
                message=(
                    f"Your answer included the key lesson ideas: {', '.join(matched_keywords)}. "
                    "This local check cannot fully grade reasoning, so reread your explanation "
                    "and make sure it clearly connects cause and effect."
                ),
                retry_recommended=True,
            )
        if matched_keywords:
            missing = [keyword for keyword in guide.required_keywords if keyword not in matched_keywords]
            return ReasoningFeedback(
                category="partially_correct",
                message=(
                    f"{guide.partial_feedback} Try including: {', '.join(missing)}."
                ),
                retry_recommended=True,
                hint=self._lesson_hint(lesson),
            )
        return ReasoningFeedback(
            category="needs_hint",
            message=(
                "That does not yet connect to the key idea in this lesson. "
                "Use the hint and explain the cause in your own words."
            ),
            retry_recommended=True,
            hint=self._lesson_hint(lesson),
        )

    @staticmethod
    def _lesson_hint(lesson: Lesson) -> str | None:
        if lesson.challenge is None:
            return None
        return lesson.challenge.hint
