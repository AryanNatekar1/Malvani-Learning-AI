"""Tests for assembling a searched topic into a lesson draft.

The worked example throughout is dispersion of light: a real school topic this
project has no lesson for, which is exactly the case the feature exists to
handle.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from grounded_answer import GroundedAnswer, Passage, ground_claims
from lesson_drafting import DraftLesson, draft_lesson, match_places


def dispersion_sources() -> list[Passage]:
    return [
        Passage(
            text=(
                "White light is a mixture of colours. When it passes into glass "
                "or water each colour is refracted, or bent, by a slightly "
                "different amount, so the colours separate. This separation is "
                "called dispersion, and it produces a spectrum."
            ),
            title="Refraction and dispersion",
            url="https://example.org/dispersion",
        ),
        Passage(
            text=(
                "A rainbow forms when sunlight enters a raindrop, is refracted, "
                "reflects from the back of the drop, and is refracted again on "
                "the way out. Because the amount of bending depends on colour, "
                "the light leaves the drop spread into a band of colours."
            ),
            title="How rainbows form",
            url="https://example.org/rainbow",
        ),
    ]


class DraftAssemblyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sources = dispersion_sources()
        self.answer = ground_claims(
            [
                ("White light is a mixture of colours.", 0),
                ("Each colour is refracted by a different amount, so the colours separate.", 0),
                ("A rainbow forms when sunlight is refracted inside a raindrop.", 1),
            ],
            self.sources,
        )

    def test_a_topic_with_no_lesson_produces_a_draft(self) -> None:
        draft = draft_lesson("dispersion of light", "Physics", self.answer)
        self.assertIsNotNone(draft)
        assert draft is not None
        self.assertTrue(draft.is_usable)
        self.assertEqual(draft.subject, "Physics")

    def test_nothing_grounded_means_no_draft_at_all(self) -> None:
        empty = GroundedAnswer(claims=(), passages=())
        self.assertIsNone(draft_lesson("dispersion of light", "Physics", empty))

    def test_a_draft_can_never_mark_itself_verified(self) -> None:
        """A machine cannot review its own output, so the value is fixed."""
        draft = draft_lesson("dispersion of light", "Physics", self.answer)
        assert draft is not None
        record = draft.to_lesson_record()
        self.assertEqual(record["verification_status"], "NEEDS_REVIEW")
        self.assertEqual(
            record["language_metadata"]["English"]["verification_status"],
            "NEEDS_REVIEW",
        )

    def test_a_draft_carries_its_sources(self) -> None:
        draft = draft_lesson("dispersion of light", "Physics", self.answer)
        assert draft is not None
        sources = draft.to_lesson_record()["sources"]
        self.assertTrue(any("example.org/dispersion" in s for s in sources))
        self.assertTrue(any("example.org/rainbow" in s for s in sources))

    def test_a_draft_says_it_was_not_written_by_a_teacher(self) -> None:
        draft = draft_lesson("dispersion of light", "Physics", self.answer)
        assert draft is not None
        generated = draft.to_lesson_record()["generated"]
        self.assertIn("not a teacher", generated["assembled_by"])
        self.assertTrue(generated["reviewer_notes"])

    def test_no_quiz_or_challenge_is_invented(self) -> None:
        """A plausible machine quiz is worse than none, because it looks done."""
        draft = draft_lesson("dispersion of light", "Physics", self.answer)
        assert draft is not None
        record = draft.to_lesson_record()
        for absent in ("quiz_questions", "challenge", "reasoning_guide"):
            self.assertNotIn(absent, record)

    def test_dropped_claims_are_recorded_for_the_reviewer(self) -> None:
        answer = ground_claims(
            [
                ("White light is a mixture of colours.", 0),
                ("Isaac Newton first observed this in Sindhudurg.", 0),
            ],
            self.sources,
        )
        draft = draft_lesson("dispersion of light", "Physics", answer)
        assert draft is not None
        record = draft.to_lesson_record()
        self.assertEqual(len(record["generated"]["claims_dropped_as_unsupported"]), 1)
        self.assertNotIn(
            "Sindhudurg", record["content"]["English"]["detailed_explanation"]
        )


class RegionalConnectionTests(unittest.TestCase):
    """The part that would quietly ruin the project if a model wrote it."""

    def setUp(self) -> None:
        self.answer = ground_claims(
            [
                ("A rainbow forms when sunlight is refracted inside a raindrop.", 1),
                ("Each colour is refracted by a different amount, so the colours separate.", 0),
            ],
            dispersion_sources(),
        )

    def test_regional_links_come_only_from_documented_places(self) -> None:
        places = match_places("dispersion of light", self.answer)
        for place in places:
            # Every match must be a real record carrying its own evidence.
            self.assertTrue(place.sources)
            self.assertTrue(place.needs_local_check)
            self.assertEqual(place.verification_status, "NEEDS_REVIEW")

    def test_no_match_means_no_regional_section_rather_than_an_invented_one(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            draft = draft_lesson(
                "dispersion of light",
                "Physics",
                self.answer,
                place_directory=Path(empty),
            )
            assert draft is not None
            self.assertEqual(draft.linked_places, ())
            record = draft.to_lesson_record()
            self.assertNotIn("suggested_places", record["generated"])
            self.assertTrue(
                any("no documented place" in n.lower() for n in draft.reviewer_notes)
            )

    def test_an_unrelated_topic_matches_nothing(self) -> None:
        """Dispersion of light has no place record, so it must suggest none.

        Matching it to the mango lesson because both mention sunlight is the
        kind of fluent-but-empty regional link this module exists to avoid.
        """
        self.assertEqual(match_places("dispersion of light", self.answer), ())

    def test_a_topic_with_a_real_place_does_match(self) -> None:
        """Precision must not have been bought by matching nothing ever."""
        from grounded_answer import Passage as P

        source = P(
            text=(
                "Laterite forms when heavy monsoon rainfall leaches silica out "
                "of rock, leaving iron oxide which makes the soil red."
            ),
            title="Weathering",
            url="https://example.org/w",
        )
        answer = ground_claims(
            [
                ("Laterite forms when monsoon rainfall leaches silica from rock.", 0),
                ("Iron oxide makes the soil red.", 0),
            ],
            [source],
        )
        names = [place.name for place in match_places("weathering of rock", answer)]
        self.assertTrue(names)
        self.assertIn("The red rock the whole district is built on", names)

    def test_a_matched_place_is_flagged_as_matched_not_chosen(self) -> None:
        draft = draft_lesson("dispersion of light", "Physics", self.answer)
        assert draft is not None
        if draft.linked_places:
            self.assertTrue(
                any("matched by overlapping" in n for n in draft.reviewer_notes)
            )


class DraftStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.answer = ground_claims(
            [("White light is a mixture of colours.", 0)], dispersion_sources()
        )

    def test_drafts_are_written_outside_the_reviewed_lesson_folder(self) -> None:
        """Nothing machine-assembled may be picked up by the lesson loader."""
        draft = draft_lesson("dispersion of light", "Physics", self.answer)
        assert draft is not None
        with tempfile.TemporaryDirectory() as directory:
            path = draft.write(Path(directory))
            self.assertTrue(path.exists())
            self.assertNotIn("data/lessons", path.as_posix())
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(record["verification_status"], "NEEDS_REVIEW")

    def test_an_empty_draft_refuses_to_be_written(self) -> None:
        empty = DraftLesson(
            topic="nothing",
            title="Nothing",
            subject="Physics",
            answer=GroundedAnswer(claims=(), passages=()),
        )
        with self.assertRaises(ValueError):
            empty.to_lesson_record()


if __name__ == "__main__":
    unittest.main()
