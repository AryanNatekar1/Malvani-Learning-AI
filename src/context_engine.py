"""Privacy-safe selection of reviewed educational context.

This module deliberately does not access GPS, the network, device sensors, or
student location.  A caller can offer a small list of context identifiers for
the learner to choose manually.  Only context records that are both verified
and source-backed are converted into student-facing output.

Context data is intentionally separate from lesson data so future location or
community-data work must pass through the same review gate instead of adding
claims directly to a lesson response.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT_DIR = Path(__file__).resolve().parent.parent
CONTEXTS_DIR = PROJECT_DIR / "data" / "contexts"

VERIFIED = "VERIFIED"
COMMUNITY_PROVIDED = "COMMUNITY_PROVIDED"
NEEDS_REVIEW = "NEEDS_REVIEW"
UNAVAILABLE = "UNAVAILABLE"
VERIFICATION_STATUSES = {
    VERIFIED,
    COMMUNITY_PROVIDED,
    NEEDS_REVIEW,
    UNAVAILABLE,
}


class ContextFormatError(ValueError):
    """Raised when editable context JSON does not have the expected shape."""


def _required_text(value: Mapping[str, Any], field_name: str) -> str:
    """Read a required non-empty text field with a helpful editor error."""
    if field_name not in value:
        raise ContextFormatError(f"Context record is missing the required field: {field_name}")
    text = str(value[field_name]).strip()
    if not text:
        raise ContextFormatError(f"Context record field '{field_name}' must not be empty.")
    return text


def _optional_text(value: Mapping[str, Any], field_name: str) -> str | None:
    """Return stripped optional text, treating an empty value as unavailable."""
    raw_value = value.get(field_name)
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    return text or None


@dataclass(frozen=True)
class ContextRecord:
    """An editor-facing, source-attributed context record.

    ``educational_prompt`` must describe how this context may be used in a
    lesson.  It is not a claim about a student's surroundings.  ``region`` is
    optional because some reviewed contexts can be broad rather than tied to a
    named place.
    """

    identifier: str
    title: str
    category: str
    educational_prompt: str
    topics: tuple[str, ...]
    verification_status: str
    source: str | None = None
    region: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ContextRecord":
        """Build a record from JSON without accepting unsourced verification."""
        if not isinstance(value, Mapping):
            raise ContextFormatError("Each context record must be a JSON object.")

        verification_status = _required_text(value, "verification_status")
        if verification_status not in VERIFICATION_STATUSES:
            raise ContextFormatError(
                f"Unsupported context verification status: {verification_status}"
            )

        source = _optional_text(value, "source")
        if verification_status == VERIFIED and source is None:
            raise ContextFormatError("Verified context needs a non-empty source.")

        raw_topics = value.get("topics")
        if not isinstance(raw_topics, list) or not raw_topics:
            raise ContextFormatError("Context record needs a non-empty topics list.")
        topics = tuple(str(topic).strip().lower() for topic in raw_topics)
        if any(not topic for topic in topics) or len(set(topics)) != len(topics):
            raise ContextFormatError("Context record topics must be non-empty and unique.")

        return cls(
            identifier=_required_text(value, "id"),
            title=_required_text(value, "title"),
            category=_required_text(value, "category"),
            educational_prompt=_required_text(value, "educational_prompt"),
            topics=topics,
            verification_status=verification_status,
            source=source,
            region=_optional_text(value, "region"),
        )


@dataclass(frozen=True)
class StudentContext:
    """The limited, transparent context information safe to show a student."""

    identifier: str
    title: str
    category: str
    educational_prompt: str
    source: str
    region: str | None = None


@dataclass(frozen=True)
class ContextSelection:
    """Result of a manual selection with a safe fallback message when needed."""

    context: StudentContext | None
    notice: str | None = None

    @property
    def is_available(self) -> bool:
        """Whether a verified, source-backed context is available to display."""
        return self.context is not None


def is_verified_for_student_display(record: ContextRecord | None) -> bool:
    """Return True only for source-backed records approved for student output.

    This defensive check is repeated at selection time even though JSON
    validation rejects a verified record without a source.  It also protects
    callers that construct ``ContextRecord`` objects in Python.
    """
    return bool(
        record
        and record.verification_status == VERIFIED
        and record.source
        and record.source.strip()
    )


def _student_context(record: ContextRecord) -> StudentContext:
    """Convert an already verified record to the safe public representation."""
    assert record.source is not None
    return StudentContext(
        identifier=record.identifier,
        title=record.title,
        category=record.category,
        educational_prompt=record.educational_prompt,
        source=record.source,
        region=record.region,
    )


class ContextRepository:
    """Read-only local context records and manual-selection lookup.

    There is no default geographic inference.  Call ``select_manual`` only
    with an identifier deliberately selected by the learner or application.
    """

    def __init__(self, records: Iterable[ContextRecord] = ()) -> None:
        self._records: dict[str, ContextRecord] = {}
        for record in records:
            normalized_identifier = record.identifier.strip().lower()
            if not normalized_identifier:
                raise ContextFormatError("Context record identifier must not be empty.")
            if normalized_identifier in self._records:
                raise ContextFormatError(f"Duplicate context id: {record.identifier}")
            self._records[normalized_identifier] = record

    @classmethod
    def from_directory(cls, contexts_dir: Path = CONTEXTS_DIR) -> "ContextRepository":
        """Load editable local JSON files, or an empty repository if absent."""
        return cls(load_context_records(contexts_dir))

    def records(self) -> tuple[ContextRecord, ...]:
        """Return all editor-facing records, including drafts for review tools."""
        return tuple(self._records.values())

    def student_options(self, topic: str | None = None) -> tuple[StudentContext, ...]:
        """Return reviewed choices, optionally only for one lesson topic."""
        normalized_topic = _normalize_topic(topic)
        return tuple(
            _student_context(record)
            for record in self._records.values()
            if is_verified_for_student_display(record)
            and _matches_topic(record, normalized_topic)
        )

    def select_manual(
        self, selected_identifier: str | None, topic: str | None = None
    ) -> ContextSelection:
        """Safely resolve one manually chosen context identifier.

        Unknown choices and drafts use an honest generic fallback.  Their
        titles, prompts, and unverified claims are not exposed to the student.
        """
        if not selected_identifier or not selected_identifier.strip():
            return ContextSelection(
                context=None,
                notice=(
                    "No local context was selected. The lesson will continue "
                    "without a local claim."
                ),
            )

        record = self._records.get(selected_identifier.strip().lower())
        if record is None:
            return ContextSelection(
                context=None,
                notice=(
                    "A verified local learning context is not available for that "
                    "selection. The lesson will continue without a local claim."
                ),
            )

        if not is_verified_for_student_display(record):
            return ContextSelection(
                context=None,
                notice=(
                    "That selection is not available as a verified local learning "
                    "context. The lesson will continue without a local claim."
                ),
            )

        if not _matches_topic(record, _normalize_topic(topic)):
            return ContextSelection(
                context=None,
                notice=(
                    "A verified learning context is not available for this lesson. "
                    "The lesson will continue without a local claim."
                ),
            )

        return ContextSelection(context=_student_context(record))


def load_context_records(contexts_dir: Path = CONTEXTS_DIR) -> tuple[ContextRecord, ...]:
    """Load local JSON records from a folder without networking or device access.

    A file may contain one context object or a list of context objects.  The
    absent default folder is valid because this is an additive prototype.
    """
    if not contexts_dir.exists():
        return ()

    records: list[ContextRecord] = []
    for context_path in sorted(contexts_dir.rglob("*.json")):
        try:
            raw_context = json.loads(context_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ContextFormatError(
                f"Invalid JSON in {context_path}: {error.msg}"
            ) from error

        raw_records = raw_context if isinstance(raw_context, list) else [raw_context]
        for raw_record in raw_records:
            try:
                records.append(ContextRecord.from_mapping(raw_record))
            except ContextFormatError as error:
                raise ContextFormatError(f"Invalid context {context_path}: {error}") from error

    return tuple(records)


def _normalize_topic(topic: str | None) -> str | None:
    """Normalize an optional topic without making a context match more broadly."""
    if topic is None:
        return None
    normalized = topic.strip().lower()
    return normalized or None


def _matches_topic(record: ContextRecord, topic: str | None) -> bool:
    """Return whether a reviewed record is authored for the requested lesson."""
    return topic is None or topic in record.topics
