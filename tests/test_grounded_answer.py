"""Tests for the gate that stands between a generator and a student.

These encode one rule: a claim with no source does not reach a learner. They
are written now, before any search backend or language model exists, because a
safety gate retrofitted after the generator works is a safety gate that never
quite gets built.
"""

import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from grounded_answer import (
    GroundedAnswer,
    Passage,
    UnavailableRetrievalProvider,
    ground_claims,
    support_ratio,
)


def passage(text: str, title: str = "Example", url: str = "https://example.org/a") -> Passage:
    return Passage(text=text, title=title, url=url)


class PassageTests(unittest.TestCase):
    def test_a_passage_must_carry_its_url(self) -> None:
        with self.assertRaises(ValueError):
            Passage(text="Gravity pulls objects down.", title="x", url="")

    def test_a_passage_must_have_text(self) -> None:
        with self.assertRaises(ValueError):
            Passage(text="   ", title="x", url="https://example.org")


class GroundingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = passage(
            "Gravity gives every falling object the same acceleration regardless "
            "of its mass, so a heavy stone and a light pebble released together "
            "reach the ground at the same moment."
        )

    def test_a_supported_claim_survives(self) -> None:
        answer = ground_claims(
            [("A heavy stone and a light pebble reach the ground together.", 0)],
            [self.source],
        )
        self.assertEqual(len(answer.claims), 1)
        self.assertEqual(answer.dropped, ())

    def test_an_invented_claim_is_dropped(self) -> None:
        """The failure this whole module exists to prevent."""
        answer = ground_claims(
            [("Gravity was discovered in Sindhudurg in 1642.", 0)], [self.source]
        )
        self.assertEqual(answer.claims, ())
        self.assertEqual(len(answer.dropped), 1)
        self.assertTrue(answer.is_empty)

    def test_a_claim_citing_a_passage_that_does_not_exist_is_dropped(self) -> None:
        answer = ground_claims([("Anything at all.", 7)], [self.source])
        self.assertTrue(answer.is_empty)
        self.assertEqual(len(answer.dropped), 1)

    def test_mixed_output_keeps_only_what_is_supported(self) -> None:
        answer = ground_claims(
            [
                ("Every falling object has the same acceleration.", 0),
                ("Lighter objects are pulled upward by the air instead.", 0),
            ],
            [self.source],
        )
        self.assertEqual(len(answer.claims), 1)
        self.assertEqual(len(answer.dropped), 1)
        self.assertIn("upward", answer.dropped[0])

    def test_no_passages_means_no_answer(self) -> None:
        answer = ground_claims([("Gravity pulls things down.", 0)], [])
        self.assertTrue(answer.is_empty)

    def test_support_ratio_is_zero_for_unrelated_text(self) -> None:
        self.assertEqual(
            support_ratio("Photosynthesis happens in chloroplasts.", self.source), 0.0
        )


class StudentOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.first = passage(
            "Laterite forms when heavy seasonal rainfall leaches silica out of "
            "rock, leaving iron and aluminium oxides behind.",
            title="Weathering",
            url="https://example.org/laterite",
        )
        self.second = passage(
            "Iron oxide gives laterite its characteristic red colour.",
            title="Soil colour",
            url="https://example.org/colour",
        )

    def test_an_empty_answer_says_so_instead_of_guessing(self) -> None:
        text = GroundedAnswer(claims=(), passages=()).as_student_text()
        self.assertIn("not going to guess", text)
        self.assertNotIn("Sources:", text)

    def test_every_shown_claim_carries_a_visible_citation(self) -> None:
        answer = ground_claims(
            [
                ("Heavy rainfall leaches silica out of the rock.", 0),
                ("Iron oxide gives laterite its red colour.", 1),
            ],
            [self.first, self.second],
        )
        text = answer.as_student_text()
        self.assertIn("[1]", text)
        self.assertIn("[2]", text)
        self.assertIn("https://example.org/laterite", text)
        self.assertIn("https://example.org/colour", text)

    def test_the_answer_admits_it_was_not_written_by_a_teacher(self) -> None:
        answer = ground_claims(
            [("Heavy rainfall leaches silica out of the rock.", 0)], [self.first]
        )
        self.assertIn("not written by a teacher", answer.as_student_text())

    def test_uncited_sources_are_not_listed(self) -> None:
        """Listing a source nothing came from implies support that is not there."""
        answer = ground_claims(
            [("Heavy rainfall leaches silica out of the rock.", 0)],
            [self.first, self.second],
        )
        text = answer.as_student_text()
        self.assertIn("https://example.org/laterite", text)
        self.assertNotIn("https://example.org/colour", text)

    def test_dropped_claims_never_appear_in_student_output(self) -> None:
        answer = ground_claims(
            [("Laterite is formed by volcanic eruptions.", 0)], [self.first]
        )
        text = answer.as_student_text()
        self.assertNotIn("volcanic", text)
        self.assertEqual(len(answer.dropped), 1)


class RetrievalProviderTests(unittest.TestCase):
    def test_the_default_provider_returns_nothing_rather_than_inventing(self) -> None:
        self.assertEqual(UnavailableRetrievalProvider().search("what is gravity"), ())

    def test_no_search_results_produce_an_honest_refusal(self) -> None:
        provider = UnavailableRetrievalProvider()
        passages = list(provider.search("anything"))
        answer = ground_claims([("Some confident sentence.", 0)], passages)
        self.assertIn("not going to guess", answer.as_student_text())


if __name__ == "__main__":
    unittest.main()
