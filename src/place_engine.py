"""Documented regional places, and the science behind how they came to be.

This is the other half of region-based learning, and it works on a different
rule from an observation activity.

An observation says "if you can find still water" — it asserts nothing about
where a learner is, because the app cannot know that. A place record does the
opposite: it names a real, documented, publicly known location and explains the
science of it. That is allowed precisely because it is not a claim about any
individual learner. Sindhudurg Fort stands off Malvan whether or not the
student reading about it has ever been there.

The discipline that keeps it honest is different too. A place record must
carry its sources, and must list what a local teacher still has to confirm —
`needs_local_check`. Dates, rainfall figures, harvest timings and local names
are exactly the things a distant author gets subtly wrong, so they are named
as open questions rather than quietly presented as fact.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lesson_models import LessonFormatError


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PLACE_DIR = PROJECT_DIR / "data" / "places"


@dataclass(frozen=True)
class PlaceQuestion:
    """One question about a place, and the science that answers it."""

    ask: str
    answer: str
    links_to: str = ""

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "PlaceQuestion":
        try:
            return cls(
                ask=str(value["ask"]),
                answer=str(value["answer"]),
                links_to=str(value.get("links_to", "")),
            )
        except KeyError as error:
            raise LessonFormatError(
                f"Place question is missing the required field: {error.args[0]}"
            ) from error


@dataclass(frozen=True)
class Place:
    """A documented location, and what it can teach."""

    identifier: str
    name: str
    where: str
    known_for: str
    how_it_formed: str
    questions: tuple[PlaceQuestion, ...]
    subjects: tuple[str, ...] = ()
    also_called: tuple[str, ...] = ()
    go_and_look: str = ""
    sources: tuple[str, ...] = ()
    needs_local_check: tuple[str, ...] = ()
    verification_status: str = "NEEDS_REVIEW"

    @property
    def linked_topics(self) -> tuple[str, ...]:
        """Lesson topics this place connects to, in order, without repeats."""
        seen: list[str] = []
        for question in self.questions:
            if question.links_to and question.links_to not in seen:
                seen.append(question.links_to)
        return tuple(seen)

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Place":
        try:
            sources = tuple(str(item) for item in value.get("sources", []))
            if not sources:
                raise LessonFormatError(
                    f"Place {value.get('id', '<unknown>')} must name at least one source. "
                    "A place record states public facts, so it carries its evidence."
                )
            questions = tuple(
                PlaceQuestion.from_mapping(item) for item in value.get("the_science", [])
            )
            if not questions:
                raise LessonFormatError(
                    f"Place {value.get('id', '<unknown>')} teaches nothing without at "
                    "least one question under 'the_science'."
                )
            return cls(
                identifier=str(value["id"]),
                name=str(value["name"]),
                where=str(value["where"]),
                known_for=str(value["known_for"]),
                how_it_formed=str(value["how_it_formed"]),
                questions=questions,
                subjects=tuple(str(item) for item in value.get("subjects", [])),
                also_called=tuple(str(item) for item in value.get("also_called", [])),
                go_and_look=str(value.get("go_and_look", "")),
                sources=sources,
                needs_local_check=tuple(
                    str(item) for item in value.get("needs_local_check", [])
                ),
                verification_status=str(value.get("verification_status", "NEEDS_REVIEW")),
            )
        except KeyError as error:
            raise LessonFormatError(
                f"Place record is missing the required field: {error.args[0]}"
            ) from error


def load_places(directory: Path = DEFAULT_PLACE_DIR) -> tuple[Place, ...]:
    """Load every place record, sorted by name for a stable display order."""
    if not directory.is_dir():
        return ()
    places: list[Place] = []
    for path in sorted(directory.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise LessonFormatError(f"{path.name} is not valid JSON: {error}") from error
        places.append(Place.from_mapping(record))
    identifiers = [place.identifier for place in places]
    if len(set(identifiers)) != len(identifiers):
        raise LessonFormatError("Two place records share an id.")
    return tuple(sorted(places, key=lambda place: place.name))


def places_for_topic(topic: str, directory: Path = DEFAULT_PLACE_DIR) -> tuple[Place, ...]:
    """Return the places whose science connects to a given lesson topic."""
    normalized = topic.strip().lower()
    return tuple(
        place for place in load_places(directory) if normalized in place.linked_topics
    )
