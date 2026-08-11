"""Small data models for editable, structured local lessons.

Lessons are stored as JSON because the standard library can read it without
adding a dependency.  JSON also makes quiz answers and verification metadata
unambiguous while remaining approachable for a student editor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class LessonFormatError(ValueError):
    """Raised when a lesson JSON file does not have the expected shape."""


VERIFICATION_STATUSES = {"VERIFIED", "COMMUNITY_PROVIDED", "NEEDS_REVIEW", "UNAVAILABLE"}
QUESTION_TYPES = {"multiple_choice", "true_false", "numerical", "short_answer"}


@dataclass(frozen=True)
class ContextEntry:
    """A local or cultural context with an explicit verification status."""

    text: str
    region: str
    verification_status: str
    source: str | None = None
    appropriate_usage: str = ""

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ContextEntry":
        try:
            status = str(value["verification_status"])
            source = value.get("source")
            if status not in VERIFICATION_STATUSES:
                raise LessonFormatError(f"Unsupported verification status: {status}")
            if status == "VERIFIED" and not source:
                raise LessonFormatError("Verified context needs a non-empty source.")
            return cls(
                text=str(value["text"]),
                region=str(value.get("region", "Not specified")),
                verification_status=status,
                source=source,
                appropriate_usage=str(value.get("appropriate_usage", "")),
            )
        except KeyError as error:
            raise LessonFormatError(
                f"Context entry is missing the required field: {error.args[0]}"
            ) from error


@dataclass(frozen=True)
class TranslationMetadata:
    """Review metadata for a specific lesson-language variant."""

    verification_status: str
    source: str | None = None

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "TranslationMetadata":
        status = str(value.get("verification_status", ""))
        source = value.get("source")
        if status not in VERIFICATION_STATUSES:
            raise LessonFormatError(f"Unsupported translation verification status: {status}")
        if status == "VERIFIED" and not source:
            raise LessonFormatError("Verified translation metadata needs a non-empty source.")
        return cls(verification_status=status, source=source)


@dataclass(frozen=True)
class Challenge:
    """A guided practice task.  Its solution is shown only on request."""

    question: str
    hint: str
    solution: str
    accepted_answers: tuple[str, ...] = ()
    progressive_hints: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Challenge":
        try:
            accepted_answers = tuple(str(answer) for answer in value.get("accepted_answers", []))
            hint = str(value["hint"])
            progressive_hints = tuple(
                str(item) for item in value.get("progressive_hints", [hint])
            )
            if not progressive_hints:
                raise LessonFormatError("Challenge needs at least one progressive hint.")
            return cls(
                question=str(value["question"]),
                hint=hint,
                solution=str(value["solution"]),
                accepted_answers=accepted_answers,
                progressive_hints=progressive_hints,
            )
        except KeyError as error:
            raise LessonFormatError(
                f"Challenge is missing the required field: {error.args[0]}"
            ) from error


@dataclass(frozen=True)
class ReasoningGuide:
    """Transparent cues used by the deterministic reasoning-feedback system."""

    required_keywords: tuple[str, ...]
    misconception_keywords: tuple[str, ...] = ()
    correct_feedback: str = "You connected the key idea to the question."
    partial_feedback: str = "You have started well. Add one more key idea to explain why."
    misconception_feedback: str = "Check the concept again and use the hint before trying once more."

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ReasoningGuide":
        required_keywords = tuple(str(keyword) for keyword in value.get("required_keywords", []))
        if not required_keywords:
            raise LessonFormatError("Reasoning guide needs at least one required keyword.")
        return cls(
            required_keywords=required_keywords,
            misconception_keywords=tuple(
                str(keyword) for keyword in value.get("misconception_keywords", [])
            ),
            correct_feedback=str(value.get("correct_feedback", cls.correct_feedback)),
            partial_feedback=str(value.get("partial_feedback", cls.partial_feedback)),
            misconception_feedback=str(
                value.get("misconception_feedback", cls.misconception_feedback)
            ),
        )


@dataclass(frozen=True)
class QuizQuestion:
    """A local, answerable quiz question stored with a lesson."""

    identifier: str
    question: str
    question_type: str
    correct_answers: tuple[str, ...]
    explanation: str
    hint: str
    options: tuple[str, ...] = ()
    difficulty: str = "Beginner"
    progressive_hints: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "QuizQuestion":
        required_fields = ["id", "question", "type", "correct_answers", "explanation", "hint"]
        missing_fields = [field_name for field_name in required_fields if field_name not in value]
        if missing_fields:
            raise LessonFormatError(
                "Quiz question is missing required field(s): " + ", ".join(missing_fields)
            )

        question_type = str(value["type"])
        correct_answers = tuple(str(answer) for answer in value["correct_answers"])
        if question_type not in QUESTION_TYPES:
            raise LessonFormatError(f"Unsupported quiz question type: {question_type}")
        if not correct_answers:
            raise LessonFormatError("Quiz question needs at least one correct answer.")
        options = tuple(str(option) for option in value.get("options", []))
        if question_type == "multiple_choice" and not options:
            raise LessonFormatError("Multiple-choice quiz question needs options.")
        hint = str(value["hint"])
        progressive_hints = tuple(
            str(item) for item in value.get("progressive_hints", [hint])
        )
        if not progressive_hints:
            raise LessonFormatError("Quiz question needs at least one progressive hint.")

        return cls(
            identifier=str(value["id"]),
            question=str(value["question"]),
            question_type=question_type,
            correct_answers=correct_answers,
            explanation=str(value["explanation"]),
            hint=hint,
            options=options,
            difficulty=str(value.get("difficulty", "Beginner")),
            progressive_hints=progressive_hints,
        )


@dataclass(frozen=True)
class Lesson:
    """A structured lesson with only the fields currently used by the app."""

    identifier: str
    title: str
    subject: str
    topic: str
    aliases: tuple[str, ...]
    levels: tuple[str, ...]
    content: dict[str, dict[str, Any]]
    language_metadata: dict[str, TranslationMetadata]
    real_world_use: tuple[str, ...] = ()
    common_misconceptions: tuple[str, ...] = ()
    think_question: str = ""
    reasoning_guide: ReasoningGuide | None = None
    challenge: Challenge | None = None
    career_connections: tuple[str, ...] = ()
    further_exploration: tuple[str, ...] = ()
    local_example: ContextEntry | None = None
    culture_connection: ContextEntry | None = None
    quiz_questions: tuple[QuizQuestion, ...] = ()
    sources: tuple[str, ...] = ()
    verification_status: str = "NEEDS_REVIEW"

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Lesson":
        required_fields = [
            "id",
            "title",
            "subject",
            "topic",
            "levels",
            "content",
            "language_metadata",
        ]
        missing_fields = [field_name for field_name in required_fields if field_name not in value]
        if missing_fields:
            raise LessonFormatError(
                "Lesson is missing required field(s): " + ", ".join(missing_fields)
            )

        content = value["content"]
        if not isinstance(content, dict) or not content:
            raise LessonFormatError("Lesson content must be a non-empty language mapping.")
        if "English" not in content:
            raise LessonFormatError("Lesson content must include an English fallback.")
        if not all(isinstance(sections, dict) for sections in content.values()):
            raise LessonFormatError("Each language content value must be a section mapping.")

        language_metadata_raw = value["language_metadata"]
        if not isinstance(language_metadata_raw, dict):
            raise LessonFormatError("Lesson language_metadata must be a language mapping.")
        if set(language_metadata_raw) != set(content):
            raise LessonFormatError(
                "Lesson language_metadata must contain exactly the same languages as content."
            )
        language_metadata = {
            str(language): TranslationMetadata.from_mapping(metadata)
            for language, metadata in language_metadata_raw.items()
        }

        verification_status = str(value.get("verification_status", "NEEDS_REVIEW"))
        if verification_status not in VERIFICATION_STATUSES:
            raise LessonFormatError(f"Unsupported lesson verification status: {verification_status}")
        sources = tuple(str(source) for source in value.get("sources", []))
        if verification_status == "VERIFIED" and not sources:
            raise LessonFormatError("Verified lesson needs at least one source.")
        aliases = tuple(str(alias) for alias in value.get("aliases", []))
        normalized_aliases = [alias.strip().lower() for alias in aliases]
        if any(not alias for alias in normalized_aliases) or len(set(normalized_aliases)) != len(aliases):
            raise LessonFormatError("Lesson aliases must be non-empty and unique.")

        local_example = value.get("local_example")
        culture_connection = value.get("culture_connection")
        reasoning_guide = value.get("reasoning_guide")
        challenge = value.get("challenge")

        return cls(
            identifier=str(value["id"]),
            title=str(value["title"]),
            subject=str(value["subject"]),
            topic=str(value["topic"]),
            aliases=aliases,
            levels=tuple(str(level) for level in value["levels"]),
            content={str(language): dict(section) for language, section in content.items()},
            language_metadata=language_metadata,
            real_world_use=tuple(str(item) for item in value.get("real_world_use", [])),
            common_misconceptions=tuple(
                str(item) for item in value.get("common_misconceptions", [])
            ),
            think_question=str(value.get("think_question", "")),
            reasoning_guide=(
                ReasoningGuide.from_mapping(reasoning_guide) if reasoning_guide else None
            ),
            challenge=Challenge.from_mapping(challenge) if challenge else None,
            career_connections=tuple(str(item) for item in value.get("career_connections", [])),
            further_exploration=tuple(str(item) for item in value.get("further_exploration", [])),
            local_example=ContextEntry.from_mapping(local_example) if local_example else None,
            culture_connection=(
                ContextEntry.from_mapping(culture_connection) if culture_connection else None
            ),
            quiz_questions=tuple(
                QuizQuestion.from_mapping(question) for question in value.get("quiz_questions", [])
            ),
            sources=sources,
            verification_status=verification_status,
        )

    def content_for(self, requested_language: str) -> tuple[dict[str, Any], str]:
        """Return language content and the language actually selected."""
        if requested_language in self.content:
            return self.content[requested_language], requested_language
        return self.content["English"], "English"
