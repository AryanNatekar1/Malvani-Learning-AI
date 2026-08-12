"""Explainable next-step recommendations from local learning evidence.

This module intentionally does not predict ability or claim mastery.  It uses
only recorded quiz submissions, the active lesson, and author-provided
``further_exploration`` links that point to an installed lesson.  Every
recommendation includes the reason a student can see and question.
"""

from __future__ import annotations

from dataclasses import dataclass

from lesson_models import Lesson
from student_engine import StudentProfile


@dataclass(frozen=True)
class LearningRecommendation:
    """One small, evidence-based next step for the local learning workflow."""

    kind: str
    title: str
    message: str
    reason: str
    topic: str | None = None

    def as_text(self) -> str:
        """Render the recommendation consistently for text-based UI sections."""
        return f"{self.title}\n{self.message}\nReason: {self.reason}"


def build_recommendation(
    profile: StudentProfile,
    lessons: tuple[Lesson, ...],
    current_lesson: Lesson | None = None,
) -> LearningRecommendation:
    """Choose a transparent recommendation from recorded local evidence.

    Review takes priority over an optional exploration link because a low
    answer-attempt result is stronger evidence that a learner may benefit from
    another look.  The engine does not infer a prerequisite unless the lesson
    author explicitly supplied an installed next-topic link.
    """
    lesson_by_topic = {lesson.topic.lower(): lesson for lesson in lessons}
    weak_topic = _weak_topic(profile, lesson_by_topic)
    if weak_topic is not None:
        topic, lesson = weak_topic
        attempts = profile.topic_attempts[topic]
        correct = profile.topic_correct.get(topic, 0)
        accuracy = (correct / attempts) * 100
        return LearningRecommendation(
            kind="review",
            topic=lesson.topic,
            title=f"Review {lesson.title}",
            message=(
                "Revisit the simple explanation, then use a hint and retry the local quiz."
            ),
            reason=(
                f"{correct} of {attempts} recorded quiz submissions were correct "
                f"({accuracy:.0f}% answer-attempt accuracy)."
            ),
        )

    next_lesson = _installed_next_lesson(current_lesson, lessons)
    if next_lesson is not None and current_lesson is not None:
        return LearningRecommendation(
            kind="explore",
            topic=next_lesson.topic,
            title=f"Explore {next_lesson.title} next",
            message="Open the next lesson when you are ready for a connected idea.",
            reason=(
                f"{next_lesson.title} is listed in the {current_lesson.title} lesson's "
                "authored next-step topics."
            ),
        )

    if profile.topics_studied:
        return LearningRecommendation(
            kind="continue",
            topic=None,
            title="Continue a local lesson",
            message="Choose a lesson and try its think question or challenge.",
            reason=(
                f"You have opened {len(profile.topics_studied)} local lesson"
                f"{'s' if len(profile.topics_studied) != 1 else ''}; no low quiz result is recorded."
            ),
        )

    return LearningRecommendation(
        kind="start",
        topic=None,
        title="Choose your first lesson",
        message="Open a topic, read the concept, and try the think question.",
        reason="No local learning activity has been recorded yet.",
    )


def _weak_topic(
    profile: StudentProfile, lesson_by_topic: dict[str, Lesson]
) -> tuple[str, Lesson] | None:
    """Return the lowest recorded quiz accuracy for an installed lesson."""
    candidates: list[tuple[float, int, str, Lesson]] = []
    for topic, attempts in profile.topic_attempts.items():
        lesson = lesson_by_topic.get(topic.lower())
        if lesson is None or attempts <= 0:
            continue
        correct = profile.topic_correct.get(topic, 0)
        accuracy = correct / attempts
        if accuracy < 0.6:
            # Lower accuracy is more urgent; more attempts then make the
            # signal stronger. The topic keeps ordering deterministic.
            candidates.append((accuracy, -attempts, topic, lesson))
    if not candidates:
        return None
    _accuracy, _attempts, topic, lesson = min(candidates)
    return topic, lesson


def _installed_next_lesson(
    current_lesson: Lesson | None, lessons: tuple[Lesson, ...]
) -> Lesson | None:
    """Find the first authored next topic that exists in the local library."""
    if current_lesson is None:
        return None
    for next_topic in current_lesson.further_exploration:
        normalized_next = _normalize(next_topic)
        for lesson in lessons:
            if normalized_next == _normalize(lesson.topic):
                return lesson
            if any(normalized_next == _normalize(alias) for alias in lesson.aliases):
                return lesson
    return None


def _normalize(text: str) -> str:
    """Compare authored topic links without punctuation/case differences."""
    return " ".join("".join(character if character.isalnum() else " " for character in text.lower()).split())
