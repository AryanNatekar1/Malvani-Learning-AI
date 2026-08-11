"""Language selection and honest fallback for lessons and interface labels."""

from __future__ import annotations

from dataclasses import dataclass

from lesson_models import Lesson


SUPPORTED_LANGUAGES = ("English", "Marathi", "Malvani")

# These are interface labels, not educational or Malvani translations.
INTERFACE_TEXT = {
    "English": {
        "start_learning": "Start Learning",
        "language": "Language",
        "level": "Class / Level",
        "subject": "Subject",
        "ask_question": "Ask a question",
        "submit_answer": "Submit Answer",
        "progress": "Progress",
        "settings": "Settings",
    },
    "Marathi": {
        "start_learning": "शिकणे सुरू करा",
        "language": "भाषा",
        "level": "इयत्ता / स्तर",
        "subject": "विषय",
        "ask_question": "प्रश्न विचारा",
        "submit_answer": "उत्तर पाठवा",
        "progress": "प्रगती",
        "settings": "सेटिंग्ज",
    },
}


@dataclass(frozen=True)
class LanguageResolution:
    """The requested and actual language used to render a lesson."""

    requested: str
    resolved: str
    notice: str | None = None


def resolve_lesson_language(lesson: Lesson, requested_language: str) -> LanguageResolution:
    """Resolve reviewed language content without inventing a translation.

    English is the current local draft-content baseline. A non-English lesson
    variant must be explicitly marked `VERIFIED` with a source before the
    student-facing app renders it as that language.
    """
    requested_metadata = lesson.language_metadata.get(requested_language)
    can_use_requested_language = (
        requested_language == "English"
        or (
            requested_language in lesson.content
            and requested_metadata is not None
            and requested_metadata.verification_status == "VERIFIED"
            and bool(requested_metadata.source)
        )
    )
    if can_use_requested_language:
        return LanguageResolution(requested_language, requested_language)

    _, resolved_language = lesson.content_for("English")

    return LanguageResolution(
        requested=requested_language,
        resolved=resolved_language,
        notice=(
            f"Reviewed {requested_language} lesson text is not available for this topic. "
            f"Showing {resolved_language} instead."
        ),
    )


def interface_text(key: str, requested_language: str) -> str:
    """Return a translated interface label or English fallback.

    There are intentionally no unverified Malvani labels in this codebase.
    """
    language_labels = INTERFACE_TEXT.get(requested_language, INTERFACE_TEXT["English"])
    return language_labels.get(key, INTERFACE_TEXT["English"].get(key, key))
