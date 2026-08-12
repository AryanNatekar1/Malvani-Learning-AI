"""Answer narrow follow-up questions from a currently open local lesson.

This is deliberately a deterministic helper, not a conversational language
model.  It recognises a small set of common follow-up requests and returns
only material that lesson authors have already stored in a ``Lesson``.

For example, after opening the Gravity lesson, a student can ask "Why?",
"Give an example", or "What careers use this?".  Questions outside those
patterns return ``None`` so a caller can give an honest fallback instead of
guessing.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from language_engine import LanguageResolution, resolve_lesson_language
from lesson_models import Lesson


DEFINITION = "definition"
EXPLANATION = "explanation"
FORMULA = "formula"
EXAMPLE = "example"
APPLICATIONS = "applications"
MISCONCEPTION = "misconception"
CAREERS = "careers"
NEXT_STEPS = "next_steps"

FOLLOW_UP_TYPES = (
    DEFINITION,
    EXPLANATION,
    FORMULA,
    EXAMPLE,
    APPLICATIONS,
    MISCONCEPTION,
    CAREERS,
    NEXT_STEPS,
)
"""The bounded follow-up requests this offline engine understands."""


@dataclass(frozen=True)
class RelatedQuestionResponse:
    """A stored lesson answer selected for a recognised follow-up request.

    ``lesson_verification_status`` is carried to the caller so the UI can
    display its normal draft/review notice.  The engine does not claim that a
    draft lesson has been academically reviewed.
    """

    question_type: str
    title: str
    text: str
    language: LanguageResolution
    lesson_verification_status: str


def classify_related_question(question: str) -> str | None:
    """Classify one common follow-up request, or return ``None`` safely.

    The checks use clear phrases rather than trying to infer unrestricted
    natural-language meaning.  More specific requests are checked before
    broad explanation phrases, so "What is the formula?" is a formula request
    rather than a general definition request.
    """
    normalized = _normalize(question)
    if not normalized:
        return None

    if _contains_any(normalized, ("formula", "equation")):
        return FORMULA
    if _contains_any(
        normalized,
        (
            "misconception",
            "misconceptions",
            "common mistake",
            "common mistakes",
            "common error",
            "common errors",
            "wrong idea",
            "wrong ideas",
            "misunderstanding",
        ),
    ):
        return MISCONCEPTION
    if _contains_any(
        normalized,
        (
            "career",
            "careers",
            "job",
            "jobs",
            "profession",
            "professions",
            "future work",
        ),
    ):
        return CAREERS
    if _contains_any(
        normalized,
        (
            "next step",
            "next steps",
            "what next",
            "learn next",
            "explore next",
            "further exploration",
            "after this",
        ),
    ):
        return NEXT_STEPS
    if _contains_any(
        normalized,
        (
            "application",
            "applications",
            "real world",
            "real life use",
            "real life uses",
            "uses",
            "useful for",
            "used for",
        ),
    ):
        return APPLICATIONS
    if _contains_any(
        normalized,
        ("example", "examples", "instance", "illustrate", "illustration"),
    ):
        return EXAMPLE
    if _contains_any(
        normalized,
        (
            "why",
            "how",
            "how does",
            "how do",
            "how can",
            "explain",
            "explanation",
            "detailed",
            "tell me more",
            "understand it",
        ),
    ):
        return EXPLANATION
    if _contains_any(
        normalized,
        ("what is", "define", "definition", "what does", "meaning", "mean"),
    ):
        return DEFINITION
    return None


def answer_related_question(
    lesson: Lesson,
    question: str,
    requested_language: str = "English",
) -> RelatedQuestionResponse | None:
    """Return a stored answer for a related question about ``lesson``.

    ``None`` has two safe meanings: the question was not one of the bounded
    types above, or this lesson does not yet contain material for that type.
    A caller should use an honest fallback rather than make up an answer.
    """
    question_type = classify_related_question(question)
    if question_type is None:
        return None

    language = resolve_lesson_language(lesson, requested_language)
    content, _selected_language = lesson.content_for(language.resolved)
    answer = _answer_for_type(lesson, content, question_type)
    if answer is None:
        return None

    title, text = answer
    return RelatedQuestionResponse(
        question_type=question_type,
        title=title,
        text=text,
        language=language,
        lesson_verification_status=lesson.verification_status,
    )


def _answer_for_type(
    lesson: Lesson,
    content: dict[str, object],
    question_type: str,
) -> tuple[str, str] | None:
    """Choose the appropriate existing lesson field for one request type."""
    simple_explanation = _text(content.get("simple_explanation"))
    detailed_explanation = _text(content.get("detailed_explanation"))

    if question_type == DEFINITION:
        return _one_text("SIMPLE EXPLANATION", simple_explanation)
    if question_type == EXPLANATION:
        return _one_text("DETAILED EXPLANATION", detailed_explanation or simple_explanation)
    if question_type == FORMULA:
        formula = _find_formula(detailed_explanation) or _find_formula(simple_explanation)
        return _one_text("FORMULA IN THIS LESSON", formula)
    if question_type == EXAMPLE:
        return _one_text("EVERYDAY EXAMPLE", _text(content.get("everyday_example")))
    if question_type == APPLICATIONS:
        return _list_text("REAL-WORLD USE", lesson.real_world_use)
    if question_type == MISCONCEPTION:
        return _list_text("COMMON MISCONCEPTIONS", lesson.common_misconceptions)
    if question_type == CAREERS:
        return _list_text("CAREER CONNECTIONS", lesson.career_connections)
    if question_type == NEXT_STEPS:
        return _list_text("EXPLORE NEXT", lesson.further_exploration)
    return None


def _normalize(text: str) -> str:
    """Return lower-case words separated by single spaces."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    """Match whole phrases so short fragments do not cause accidental routes."""
    padded_text = f" {text} "
    return any(f" {phrase} " in padded_text for phrase in phrases)


def _text(value: object) -> str:
    """Convert a non-empty stored text value into a trimmed string."""
    return str(value).strip() if value else ""


def _one_text(title: str, text: str) -> tuple[str, str] | None:
    """Return a section only when the lesson actually has stored text."""
    return (title, text) if text else None


def _list_text(title: str, values: tuple[str, ...]) -> tuple[str, str] | None:
    """Render an existing lesson list as student-readable bullets."""
    if not values:
        return None
    return title, "\n".join(f"- {value}" for value in values)


def _find_formula(text: str) -> str:
    """Extract a plainly written equation from existing explanation text.

    Lesson data currently has no separate formula field.  This intentionally
    recognises only explicit ``name = expression`` equations, such as
    ``F = ma`` and ``p = m x v``.  It never derives or invents a formula.
    """
    match = re.search(r"\b[A-Za-z][A-Za-z0-9_]*\s*=\s*[^.?!]+", text)
    return match.group(0).strip(" ,;:") if match else ""
