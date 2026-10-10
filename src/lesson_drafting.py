"""Turn a searched topic into a lesson draft in this project's own shape.

A student asks for dispersion of light. There is no lesson for it, so the app
searches, filters what comes back, and assembles a draft that looks like every
other lesson here: an explanation, a connection to this region, something to go
and watch. That is the only way the library grows faster than one person can
type.

The important design decision is which parts a machine is allowed to produce,
because they are not equally safe:

  explanation      from retrieved sources, every claim cited     generated
  real-world use   from retrieved sources                        generated
  region link      matched against places we already documented  NOT generated
  observation      chosen from a reviewed pattern, never invented  constrained
  verification     always NEEDS_REVIEW                           never machine

The region link is the one that would quietly ruin this project. Asked to
connect dispersion of light to Sindhudurg, a language model will write
something fluent about fishermen and monsoon skies, and it will be invention
wearing local clothes — the exact failure the whole app is built to refuse. So
a draft never writes a regional connection. It only points at places already
documented in data/places/, which carry their own sources and their own list
of what a teacher still has to confirm.

A draft is also never finished. It is written to disk as NEEDS_REVIEW with the
sources attached, which turns this from an answer machine into a drafting tool:
a teacher reviews, corrects and promotes it, and the hand-written library grows
with a human still in the loop.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from grounded_answer import GroundedAnswer
from place_engine import Place, load_places


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DRAFT_DIR = PROJECT_DIR / "data" / "lesson_drafts"

WORD_RE = re.compile(r"[A-Za-z0-9]+")

# Ordinary English that carries no topical signal. Without this, a place gets
# matched to a lesson because both happened to use the words "when" and
# "different", which is how an early version connected dispersion of light to
# a lesson about red soil.
GENERIC = frozenset(
    """
    about above after again against along also always amount another any area
    around because become becomes been before being below between both call
    called came carry carries cannot change changes come comes could different
    does doing done down during each either else enough even ever every
    everything far few find finds first form forms found from further gave give
    gives going gone good great hand have having here highhold hold holds
    however inside into itself just keep keeps kept know known large last late
    later least leave leaves left less level like little long look looks lose
    loses made make makes many more most much must near need needs never next
    none nothing often once only onto other others over part parts past place
    places point points put rather really right same says seen several shall
    should show shows side since size small some something soon still stop
    stops such take takes than that their them then there these they thing
    things think this those three through time times together took toward turn
    turns twice under until upon used uses using very want ways well were what
    when where which while whole will with within without work works would
    """.split()
)

# A word shared by this fraction of all place records or more describes the
# region in general rather than this topic, so it cannot evidence a match.
COMMON_WORD_SHARE = 0.5

# How many distinctive words a place and a topic must share to be suggested.
# Three rather than two, chosen by trying both: at two, dispersion of light
# was matched to a lesson about mangoes on the strength of the single word
# "sunlight". A wrong suggestion costs a reviewer's trust in all the others,
# so this errs toward suggesting nothing.
MINIMUM_SHARED_KEYWORDS = 3


def _keywords(text: str) -> set[str]:
    return {
        word
        for word in (m.group(0).lower() for m in WORD_RE.finditer(text))
        if len(word) > 3 and word not in GENERIC
    }


def _place_text(place: Place) -> str:
    return " ".join(
        [place.name, place.known_for, place.how_it_formed]
        + [question.ask + " " + question.answer for question in place.questions]
    )


@dataclass(frozen=True)
class DraftLesson:
    """A machine-assembled lesson, incomplete by design and marked as such."""

    topic: str
    title: str
    subject: str
    answer: GroundedAnswer
    linked_places: tuple[Place, ...] = ()
    suggested_observation: str | None = None
    reviewer_notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_usable(self) -> bool:
        """A draft with no supported claim is not a draft, it is nothing."""
        return not self.answer.is_empty

    def to_lesson_record(self) -> dict:
        """Render in the same schema a hand-written lesson uses.

        Deliberately missing: quiz questions, a challenge, a reasoning guide.
        Those need a teacher's judgement about what a learner should struggle
        with, and a plausible-looking machine attempt at them would be worse
        than their absence, because it would look finished.
        """
        if not self.is_usable:
            raise ValueError(
                "Refusing to write a lesson draft with no supported claims."
            )
        explanation = " ".join(claim.text for claim in self.answer.claims)
        sources = [
            f"{passage.title} — {passage.url}"
            for passage in self.answer.cited_passages()
        ]
        record: dict = {
            "id": f"draft.{self.topic.replace(' ', '-')}",
            "title": self.title,
            "subject": self.subject,
            "topic": self.topic,
            "levels": ["Class 8", "Class 9", "Class 10"],
            "content": {
                "English": {
                    "simple_explanation": self.answer.claims[0].text,
                    "detailed_explanation": explanation,
                }
            },
            "language_metadata": {
                "English": {"verification_status": "NEEDS_REVIEW", "source": None}
            },
            "sources": sources,
            # A machine cannot verify its own output, so this value is fixed.
            "verification_status": "NEEDS_REVIEW",
            "generated": {
                "assembled_by": "retrieval and arrangement, not a teacher",
                "claims_dropped_as_unsupported": list(self.answer.dropped),
                "reviewer_notes": list(self.reviewer_notes),
            },
        }
        if self.linked_places:
            record["generated"]["suggested_places"] = [
                {"id": place.identifier, "name": place.name}
                for place in self.linked_places
            ]
        if self.suggested_observation:
            record["generated"]["suggested_observation"] = self.suggested_observation
        return record

    def write(self, directory: Path = DEFAULT_DRAFT_DIR) -> Path:
        """Save the draft for review. Never writes into data/lessons/.

        Drafts live apart from reviewed lessons so nothing machine-assembled
        can be picked up by the app's lesson loader by accident.
        """
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.topic.replace(' ', '_')}.json"
        path.write_text(
            json.dumps(self.to_lesson_record(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path


def match_places(
    topic: str, answer: GroundedAnswer, directory: Path | None = None
) -> tuple[Place, ...]:
    """Find documented places whose science genuinely overlaps this topic.

    Matching, not writing. The connection to this region can only be made to
    somewhere already researched and sourced; if nothing matches, the draft
    simply has no regional section, which is the honest outcome rather than a
    prompt to invent one.
    """
    places = load_places(directory) if directory else load_places()
    if not places:
        return ()
    wanted = _keywords(topic) | _keywords(
        " ".join(claim.text for claim in answer.claims)
    )
    if not wanted:
        return ()

    # Drop words most of the places use anyway. "Monsoon" says something about
    # which place; "coast" in a district-wide coastal corpus says nothing.
    vocabularies = {place.identifier: _keywords(_place_text(place)) for place in places}
    ceiling = max(1, int(len(places) * COMMON_WORD_SHARE))
    everywhere = {
        word
        for word in set().union(*vocabularies.values())
        if sum(word in vocab for vocab in vocabularies.values()) > ceiling
    }
    distinctive = wanted - everywhere
    if not distinctive:
        return ()

    scored: list[tuple[int, Place]] = []
    for place in places:
        overlap = len(distinctive & vocabularies[place.identifier])
        if overlap >= MINIMUM_SHARED_KEYWORDS:
            scored.append((overlap, place))
    scored.sort(key=lambda pair: (-pair[0], pair[1].name))
    return tuple(place for _, place in scored[:3])


def draft_lesson(
    topic: str,
    subject: str,
    answer: GroundedAnswer,
    title: str | None = None,
    place_directory: Path | None = None,
) -> DraftLesson | None:
    """Assemble a draft, or return None when there is nothing honest to say."""
    if answer.is_empty:
        return None
    places = match_places(topic, answer, place_directory)
    notes = [
        "Every sentence here came from a source listed above; none was written "
        "by a teacher. Read it before any student does.",
        "No quiz, challenge or reasoning guide was generated. Those need a "
        "decision about what a learner should struggle with.",
    ]
    if places:
        notes.append(
            "The suggested places were matched by overlapping subject matter, "
            "not chosen by a person. Check the connection is real before using it."
        )
    else:
        notes.append(
            "No documented place matched this topic, so the draft has no "
            "regional connection. Add one only if you can source it."
        )
    if answer.dropped:
        notes.append(
            f"{len(answer.dropped)} claim(s) were dropped as unsupported. They "
            "are recorded in the draft — worth reading, as they show what the "
            "generator was willing to assert without evidence."
        )
    return DraftLesson(
        topic=topic,
        title=title or topic.title(),
        subject=subject,
        answer=answer,
        linked_places=places,
        reviewer_notes=tuple(notes),
    )
