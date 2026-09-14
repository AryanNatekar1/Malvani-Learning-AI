"""Language selection and honest fallback for lessons and interface labels."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from lesson_models import Lesson


PROJECT_DIR = Path(__file__).resolve().parent.parent
CONTRIBUTED_LANGUAGE_DIR = PROJECT_DIR / "data" / "languages"

# Malvani is a variety of Konkani spoken in Sindhudurg, so the two are listed
# separately on purpose: a student who reads standard (Goan) Konkani is not
# necessarily served by Malvani text, and the reverse is also true.
SUPPORTED_LANGUAGES = ("English", "Marathi", "Hindi", "Konkani", "Malvani")

# These are interface labels, not educational or Malvani translations.
#
# Only languages whose labels come from a standard written form appear here.
# Konkani and Malvani are deliberately absent: Malvani is largely a spoken
# variety with no settled spelling, so guessing at labels would be exactly the
# invention this project refuses to do. Both fall back to English until a
# speaker contributes a reviewed file under data/languages/ — see
# load_contributed_interface_text().
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
    "Hindi": {
        "start_learning": "सीखना शुरू करें",
        "language": "भाषा",
        "level": "कक्षा / स्तर",
        "subject": "विषय",
        "ask_question": "प्रश्न पूछें",
        "submit_answer": "उत्तर भेजें",
        "progress": "प्रगति",
        "settings": "सेटिंग्स",
    },
}


def load_contributed_interface_text(
    directory: Path = CONTRIBUTED_LANGUAGE_DIR,
) -> dict[str, dict[str, str]]:
    """Load reviewed interface labels contributed as data rather than code.

    A speaker of Konkani or Malvani can add labels without touching Python, but
    the same rule applies as to lesson text: a file is only used once a named
    reviewer has signed it off, so an in-progress draft cannot reach a student.
    Anything malformed is skipped rather than raised, because a bad contributed
    file must not stop the app from opening.
    """
    contributed: dict[str, dict[str, str]] = {}
    if not directory.is_dir():
        return contributed
    for path in sorted(directory.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(record, dict):
            continue
        language = record.get("language")
        labels = record.get("interface_text")
        if not isinstance(language, str) or not isinstance(labels, dict):
            continue
        if record.get("verification_status") != "VERIFIED":
            continue
        if not str(record.get("reviewed_by") or "").strip():
            continue
        usable = {
            key: value
            for key, value in labels.items()
            if isinstance(key, str) and isinstance(value, str) and value.strip()
        }
        if usable:
            contributed[language] = usable
    return contributed


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


@lru_cache(maxsize=1)
def _cached_contributed_interface_text() -> dict[str, dict[str, str]]:
    """Cache contributed labels; the GUI asks for a label on every redraw.

    A newly added or edited language file is picked up on the next app start,
    or immediately after calling `refresh_contributed_languages()`.
    """
    return load_contributed_interface_text()


def refresh_contributed_languages() -> None:
    """Forget cached contributed labels so edited files are re-read."""
    _cached_contributed_interface_text.cache_clear()


def interface_text(key: str, requested_language: str) -> str:
    """Return a translated interface label or English fallback.

    There are intentionally no unverified Malvani labels in this codebase.
    Reviewed contributed labels win over the built-in table, so a speaker can
    correct a label without a code change; an unreviewed file is ignored.
    """
    contributed = _cached_contributed_interface_text()
    language_labels = {
        **INTERFACE_TEXT.get(requested_language, {}),
        **contributed.get(requested_language, {}),
    }
    if key in language_labels:
        return language_labels[key]
    return INTERFACE_TEXT["English"].get(key, key)
