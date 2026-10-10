"""Tests for selecting sentences rather than writing them.

These use fixed passages rather than live search, so they test the selection
rules and not Wikipedia's ranking on a given day. The properties asserted are
the ones the design depends on: selected text is verbatim, so grounding holds
by construction; no single source may dominate; and the same sentence is not
repeated from two articles that happen to define the term the same way.
"""

import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from extractive_answer import extract_claims, sentences
from grounded_answer import Passage, ground_claims


def passage(text: str, title: str = "Article", slug: str = "a") -> Passage:
    return Passage(text=text, title=title, url=f"https://example.org/{slug}")


MAIN = passage(
    "Photosynthesis is the process by which green plants use sunlight to make "
    "food from carbon dioxide and water. The process releases oxygen as a "
    "by-product. Chlorophyll in the leaves absorbs the light energy that "
    "drives the reaction.",
    title="Photosynthesis",
    slug="photosynthesis",
)
SPECIALIST = passage(
    "C4 carbon fixation is one of three known photosynthetic processes of "
    "carbon fixation in plants. It reduces photorespiration by concentrating "
    "carbon dioxide around the enzyme RuBisCO in a specialised cell layer.",
    title="C4 carbon fixation",
    slug="c4",
)


class SentenceSplittingTests(unittest.TestCase):
    def test_sentences_are_separated(self) -> None:
        self.assertEqual(len(sentences(MAIN.text)), 3)

    def test_fragments_and_headings_are_skipped(self) -> None:
        self.assertEqual(sentences("Overview. See also. Notes."), [])

    def test_a_very_long_sentence_is_skipped(self) -> None:
        self.assertEqual(sentences("Photosynthesis " + "word " * 200 + "."), [])


class SelectionTests(unittest.TestCase):
    def test_selected_text_is_verbatim_so_grounding_holds(self) -> None:
        """The central property: selection cannot invent, by construction."""
        proposed = extract_claims("photosynthesis", [MAIN, SPECIALIST], limit=4)
        self.assertTrue(proposed)
        for text, index in proposed:
            self.assertIn(text, [MAIN, SPECIALIST][index].text)
        answer = ground_claims(proposed, [MAIN, SPECIALIST])
        self.assertEqual(answer.dropped, ())
        self.assertEqual(len(answer.claims), len(proposed))

    def test_the_definition_is_preferred_over_specialist_detail(self) -> None:
        """Earlier this picked a terse C4 sentence over the actual definition."""
        proposed = extract_claims("photosynthesis", [MAIN, SPECIALIST], limit=2)
        self.assertIn("Photosynthesis is the process", proposed[0][0])

    def test_no_single_source_may_dominate(self) -> None:
        proposed = extract_claims("photosynthesis", [MAIN, SPECIALIST], limit=4)
        from collections import Counter

        counts = Counter(index for _, index in proposed)
        self.assertTrue(all(count <= 2 for count in counts.values()))

    def test_near_duplicate_sentences_are_not_repeated(self) -> None:
        """Related articles restate the same definition; one copy is enough."""
        echo = passage(
            "Photosynthesis is the process by which green plants use sunlight "
            "to make food from carbon dioxide and water.",
            title="Plant biology",
            slug="echo",
        )
        proposed = extract_claims("photosynthesis", [MAIN, echo], limit=4)
        texts = [text for text, _ in proposed]
        self.assertEqual(len(texts), len(set(texts)))
        self.assertEqual(
            sum("green plants use sunlight" in text for text in texts), 1
        )

    def test_claims_are_returned_in_source_order(self) -> None:
        proposed = extract_claims("photosynthesis", [MAIN, SPECIALIST], limit=4)
        indexes = [index for _, index in proposed]
        self.assertEqual(indexes, sorted(indexes))

    def test_the_limit_is_respected(self) -> None:
        self.assertLessEqual(
            len(extract_claims("photosynthesis", [MAIN, SPECIALIST], limit=2)), 2
        )

    def test_an_unrelated_query_selects_nothing(self) -> None:
        self.assertEqual(extract_claims("tectonic plates", [MAIN], limit=3), [])

    def test_no_passages_selects_nothing(self) -> None:
        self.assertEqual(extract_claims("photosynthesis", [], limit=3), [])

    def test_an_empty_query_selects_nothing(self) -> None:
        self.assertEqual(extract_claims("   ", [MAIN], limit=3), [])


if __name__ == "__main__":
    unittest.main()
