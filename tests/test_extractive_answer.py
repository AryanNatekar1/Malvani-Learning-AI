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


class DevanagariTests(unittest.TestCase):
    """Marathi and Hindi broke every stage of this silently.

    An ASCII tokenizer found no words, so an ASCII sentence splitter found no
    sentences, so nothing was selected and nothing was reported. These pin
    each stage separately, because the failure was invisible end to end.
    """

    MARATHI = (
        "वस्तुमान असलेल्या कोणत्याही दोन वस्तूंच्या एकमेकांकडे आकर्षिल्या "
        "जाण्याच्या प्रवृत्तीला गुरुत्वाकर्षण असे म्हणतात. वजन म्हणजे "
        "जमिनीच्या दिशेने असणाऱ्या गुरुत्वाकर्षणामुळे मिळणारे त्वरण होय."
    )

    def test_a_devanagari_word_is_not_split_at_its_vowel_marks(self) -> None:
        from extractive_answer import _words

        found = _words("गुरुत्वाकर्षण म्हणजे वस्तुमान")
        self.assertIn("गुरुत्वाकर्षण", found)
        self.assertIn("वस्तुमान", found)
        # Fragments produced by the old tokenizer must not appear.
        self.assertNotIn("वरण", found)

    def test_grammar_words_are_treated_as_stopwords(self) -> None:
        from extractive_answer import _words

        self.assertNotIn("आणि", _words("गुरुत्वाकर्षण आणि वस्तुमान"))

    def test_marathi_splits_into_sentences(self) -> None:
        """A full stop ends a Marathi sentence, with no capital to follow it."""
        self.assertEqual(len(sentences(self.MARATHI)), 2)

    def test_a_danda_ends_a_sentence(self) -> None:
        text = (
            "गुरुत्वाकर्षण म्हणजे दोन वस्तूंमधील आकर्षण होय। "
            "वजन हे गुरुत्वाकर्षणामुळे मिळणारे त्वरण आहे।"
        )
        self.assertEqual(len(sentences(text)), 2)

    def test_marathi_claims_survive_the_grounding_gate(self) -> None:
        """The gate had its own ASCII tokenizer and dropped all of them."""
        marathi = passage(self.MARATHI, title="गुरुत्वाकर्षण", slug="mr")
        proposed = extract_claims("गुरुत्वाकर्षण", [marathi], limit=2)
        self.assertTrue(proposed, "nothing selected from Marathi text")
        answer = ground_claims(proposed, [marathi])
        self.assertEqual(answer.dropped, ())
        self.assertTrue(answer.claims)

    def test_english_still_works_after_the_unicode_change(self) -> None:
        proposed = extract_claims("photosynthesis", [MAIN], limit=2)
        self.assertTrue(proposed)
        self.assertIn("Photosynthesis is the process", proposed[0][0])


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
