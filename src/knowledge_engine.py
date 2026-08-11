"""Find and load the local lessons used by Malvani Learning AI.

The original ``data/*.txt`` files remain the terminal-chatbot baseline.
Structured JSON lessons are an additive format used by the new teaching GUI.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from lesson_models import Lesson, LessonFormatError


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
LESSONS_DIR = DATA_DIR / "lessons"

# Longer aliases must be checked before their shorter parts.  Punctuation is
# normalized before matching, so "Newton's laws" is handled correctly.
TOPIC_KEYWORDS = {
    "newton s laws": "newton",
    "newton laws": "newton",
    "newton law": "newton",
    "gravity": "gravity",
    "energy": "energy",
    "force": "force",
    "motion": "motion",
    "newton": "newton",
    "friction": "friction",
    "acceleration": "acceleration",
    "velocity": "velocity",
    "momentum": "momentum",
    "work": "work",
}

_UNVERIFIED_CONTEXT_HEADERS = {"sindhudurg example:", "culture connection:"}
_KNOWN_LESSON_HEADERS = {
    "concept:",
    "simple explanation:",
    "detailed explanation:",
    "examples:",
    "real life use:",
    "think question:",
    "career connection:",
    "challenge:",
    "first law:",
    "second law:",
    "third law:",
    "formula:",
}


def _normalized_words(text: str) -> str:
    """Lowercase text and turn punctuation into word separators."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def find_topic(question: str) -> str | None:
    """Return the first supported topic mentioned as complete words.

    This is intentionally a lightweight offline matcher.  It does not attempt
    to understand every possible question; the optional AI layer can improve
    intent handling later without changing the verified lesson store.
    """
    normalized_question = _normalized_words(question)

    # "work out" is ordinary conversational English, not automatically the
    # Physics topic "work".  This narrow rule prevents a common false match.
    if "work out" in normalized_question:
        return None

    aliases = dict(TOPIC_KEYWORDS)
    # New structured lessons can add aliases without editing the terminal
    # chatbot.  If an editor is still drafting malformed JSON, legacy lookup
    # remains available rather than preventing the original chatbot from running.
    try:
        for lesson in load_structured_lessons():
            aliases.setdefault(lesson.topic, lesson.topic)
            for alias in lesson.aliases:
                aliases.setdefault(_normalized_words(alias), lesson.topic)
    except LessonFormatError:
        pass

    for keyword, topic in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", normalized_question):
            return topic

    return None


def load_lesson(topic: str, data_dir: Path = DATA_DIR) -> str | None:
    """Return the original plain-text lesson, or None when its file is absent."""
    lesson_path = data_dir / f"{topic}.txt"
    try:
        return lesson_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def load_student_lesson(topic: str, data_dir: Path = DATA_DIR) -> str | None:
    """Load a legacy lesson with unverified regional claims hidden from students.

    Original files remain unchanged for migration and reviewer work. This is a
    display-only safety layer for the terminal chatbot and the legacy GUI path.
    """
    content = load_lesson(topic, data_dir)
    if content is None:
        return None
    return _hide_unverified_legacy_context(content)


def _hide_unverified_legacy_context(content: str) -> str:
    """Remove labelled local/cultural draft sections from legacy output."""
    lines = content.splitlines()
    output: list[str] = []
    hiding_context = False
    notice_added = False

    for line in lines:
        normalized_line = line.strip().lower()
        if normalized_line in _UNVERIFIED_CONTEXT_HEADERS:
            hiding_context = True
            if not notice_added:
                output.extend(
                    [
                        "Local Context Status:",
                        "A local/cultural draft is hidden until it has a source and verification.",
                        "",
                    ]
                )
                notice_added = True
            continue
        if hiding_context and normalized_line in _KNOWN_LESSON_HEADERS:
            hiding_context = False
        if not hiding_context:
            output.append(line)

    return "\n".join(output).strip()


def load_structured_lessons(lessons_dir: Path = LESSONS_DIR) -> tuple[Lesson, ...]:
    """Load all JSON lessons, reporting malformed content clearly to editors."""
    if not lessons_dir.exists():
        return ()

    lessons: list[Lesson] = []
    seen_identifiers: set[str] = set()
    seen_topics: set[str] = set()
    for lesson_path in sorted(lessons_dir.rglob("*.json")):
        try:
            raw_lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise LessonFormatError(f"Invalid JSON in {lesson_path}: {error.msg}") from error
        if not isinstance(raw_lesson, dict):
            raise LessonFormatError(f"Invalid lesson {lesson_path}: root value must be an object.")

        try:
            lesson = Lesson.from_mapping(raw_lesson)
        except LessonFormatError as error:
            raise LessonFormatError(f"Invalid lesson {lesson_path}: {error}") from error
        if lesson.identifier in seen_identifiers:
            raise LessonFormatError(f"Duplicate lesson id: {lesson.identifier}")
        if lesson.topic.lower() in seen_topics:
            raise LessonFormatError(f"Duplicate lesson topic: {lesson.topic}")
        seen_identifiers.add(lesson.identifier)
        seen_topics.add(lesson.topic.lower())
        lessons.append(lesson)

    return tuple(lessons)


def get_structured_lesson(topic: str, lessons_dir: Path = LESSONS_DIR) -> Lesson | None:
    """Return a migrated lesson by canonical topic name, if one exists."""
    normalized_topic = _normalized_words(topic)
    for lesson in load_structured_lessons(lessons_dir):
        if _normalized_words(lesson.topic) == normalized_topic:
            return lesson
    return None


def available_subjects(lessons_dir: Path = LESSONS_DIR) -> tuple[str, ...]:
    """List subjects that have actual structured lessons, not empty folders."""
    return tuple(sorted({lesson.subject for lesson in load_structured_lessons(lessons_dir)}))
