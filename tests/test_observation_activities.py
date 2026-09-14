"""Tests for the 'observe around you' activities.

These guard the rule that makes region-based learning honest: the app invites
a learner to look at their own surroundings, but never asserts what is there.
"""

import json
import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from knowledge_engine import load_structured_lessons
from lesson_models import LessonFormatError, ObservationActivity

LESSON_DIR = Path(__file__).resolve().parent.parent / "data" / "lessons"


class ObservationActivityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lessons = load_structured_lessons(LESSON_DIR)

    def test_every_lesson_has_an_observation(self) -> None:
        for lesson in self.lessons:
            with self.subTest(topic=lesson.topic):
                self.assertIsNotNone(
                    lesson.observe_around_you,
                    f"{lesson.topic} has no observe_around_you activity",
                )

    def test_observations_are_complete(self) -> None:
        for lesson in self.lessons:
            activity = lesson.observe_around_you
            assert activity is not None
            with self.subTest(topic=lesson.topic):
                self.assertTrue(activity.invitation.strip())
                self.assertTrue(activity.what_to_do.strip())
                self.assertTrue(activity.what_to_notice.strip())
                self.assertTrue(activity.concept_link.strip())

    def test_observations_do_not_assert_what_is_near_the_learner(self) -> None:
        """The app cannot see where a learner is, so it must not claim to.

        Phrases like "near your school" would be a fabricated local fact, the
        same thing the project refuses to do with Malvani words or cultural
        claims. An observation must stay conditional and let the learner
        supply the place.
        """
        forbidden = (
            "near your school",
            "near your home",
            "in your village",
            "in your town",
            "your nearby",
            "the pond near",
            "your local pond",
        )
        for lesson in self.lessons:
            activity = lesson.observe_around_you
            assert activity is not None
            text = " ".join(
                [
                    activity.invitation,
                    activity.what_to_do,
                    activity.what_to_notice,
                    activity.concept_link,
                ]
            ).lower()
            for phrase in forbidden:
                with self.subTest(topic=lesson.topic, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_observations_need_only_ordinary_things(self) -> None:
        """A learner with no money and no laboratory must still be able to do it."""
        unaffordable = ("laboratory", "lab equipment", "buy ", "purchase", "sensor")
        for lesson in self.lessons:
            activity = lesson.observe_around_you
            assert activity is not None
            haystack = (activity.invitation + " " + " ".join(activity.needs)).lower()
            for phrase in unaffordable:
                with self.subTest(topic=lesson.topic, phrase=phrase):
                    self.assertNotIn(phrase, haystack)

    def test_activity_rejects_a_missing_required_field(self) -> None:
        with self.assertRaises(LessonFormatError):
            ObservationActivity.from_mapping(
                {"invitation": "x", "what_to_do": "y", "what_to_notice": "z"}
            )

    def test_activity_keeps_an_empty_safety_note_as_none(self) -> None:
        activity = ObservationActivity.from_mapping(
            {
                "invitation": "a",
                "what_to_do": "b",
                "what_to_notice": "c",
                "concept_link": "d",
                "safety_note": "",
            }
        )
        self.assertIsNone(activity.safety_note)
        self.assertEqual(activity.needs, ())

    def test_the_web_app_reads_the_same_observation_text(self) -> None:
        """The browser app and desktop app must not drift into separate content."""
        gravity = next(lesson for lesson in self.lessons if lesson.topic == "gravity")
        assert gravity.observe_around_you is not None
        raw = json.loads(
            (LESSON_DIR / "physics" / "gravity.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            raw["observe_around_you"]["concept_link"],
            gravity.observe_around_you.concept_link,
        )


if __name__ == "__main__":
    unittest.main()
