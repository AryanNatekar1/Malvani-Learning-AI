"""Tests for documented regional place records.

A place record is allowed to name a real location, unlike an observation
activity, because it states public geography rather than a claim about where
any particular learner is. The price of that freedom is evidence: every record
carries sources, and says what a local teacher still needs to confirm.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from knowledge_engine import load_structured_lessons
from lesson_models import LessonFormatError
from place_engine import Place, load_places, places_for_topic

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class PlaceEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.places = load_places(DATA_DIR / "places")

    def test_places_load(self) -> None:
        self.assertGreater(len(self.places), 0)

    def test_every_place_carries_its_evidence(self) -> None:
        for place in self.places:
            with self.subTest(place=place.identifier):
                self.assertTrue(place.sources, "a place must name its sources")
                self.assertTrue(place.questions, "a place must teach something")
                self.assertTrue(place.how_it_formed.strip())

    def test_every_place_names_what_still_needs_checking(self) -> None:
        """A distant author gets local detail subtly wrong; say so up front."""
        for place in self.places:
            with self.subTest(place=place.identifier):
                self.assertTrue(
                    place.needs_local_check,
                    f"{place.identifier} claims nothing needs local confirmation, "
                    "which is almost never true of regional content",
                )

    def test_places_stay_draft_until_reviewed(self) -> None:
        for place in self.places:
            with self.subTest(place=place.identifier):
                self.assertEqual(place.verification_status, "NEEDS_REVIEW")

    def test_linked_topics_point_at_real_lessons(self) -> None:
        """A place must not link to a lesson that does not exist."""
        topics = {lesson.topic for lesson in load_structured_lessons(DATA_DIR / "lessons")}
        for place in self.places:
            for topic in place.linked_topics:
                with self.subTest(place=place.identifier, topic=topic):
                    self.assertIn(topic, topics)

    def test_linked_topics_are_deduplicated_in_order(self) -> None:
        place = Place.from_mapping(
            {
                "id": "place.test",
                "name": "Test",
                "where": "Nowhere",
                "known_for": "x",
                "how_it_formed": "y",
                "sources": ["a source"],
                "the_science": [
                    {"ask": "a", "answer": "b", "links_to": "force"},
                    {"ask": "c", "answer": "d", "links_to": "work"},
                    {"ask": "e", "answer": "f", "links_to": "force"},
                    {"ask": "g", "answer": "h"},
                ],
            }
        )
        self.assertEqual(place.linked_topics, ("force", "work"))

    def test_lookup_by_topic(self) -> None:
        found = places_for_topic("atoms", DATA_DIR / "places")
        self.assertTrue(found)
        for place in found:
            self.assertIn("atoms", place.linked_topics)
        self.assertEqual(places_for_topic("not-a-topic", DATA_DIR / "places"), ())

    def test_a_place_without_sources_is_rejected(self) -> None:
        with self.assertRaises(LessonFormatError):
            Place.from_mapping(
                {
                    "id": "place.bad",
                    "name": "Bad",
                    "where": "x",
                    "known_for": "y",
                    "how_it_formed": "z",
                    "the_science": [{"ask": "a", "answer": "b"}],
                }
            )

    def test_a_place_that_teaches_nothing_is_rejected(self) -> None:
        with self.assertRaises(LessonFormatError):
            Place.from_mapping(
                {
                    "id": "place.bad",
                    "name": "Bad",
                    "where": "x",
                    "known_for": "y",
                    "how_it_formed": "z",
                    "sources": ["a source"],
                    "the_science": [],
                }
            )

    def test_duplicate_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            record = {
                "id": "place.same",
                "name": "Same",
                "where": "x",
                "known_for": "y",
                "how_it_formed": "z",
                "sources": ["a source"],
                "the_science": [{"ask": "a", "answer": "b"}],
            }
            for name in ("one.json", "two.json"):
                (Path(directory) / name).write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaises(LessonFormatError):
                load_places(Path(directory))

    def test_missing_directory_is_not_an_error(self) -> None:
        self.assertEqual(load_places(Path("no-such-directory")), ())


if __name__ == "__main__":
    unittest.main()
