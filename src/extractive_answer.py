"""Build an answer by selecting sentences, not by writing them.

A language model is the obvious way to turn retrieved passages into an
explanation, and eventually it will be the better way. But it needs a key, it
costs money per question, it needs a network round trip a rural connection may
not have, and it can produce a fluent sentence that no source supports.

Selection has none of those problems. Every sentence here is copied verbatim
from a passage that carries a URL, so grounding is not something to be checked
afterwards — it is true by construction. That makes this worth having as the
default rather than as a placeholder: it works offline once passages are
cached, it costs nothing, it cannot invent, and it fails in the one obvious way
instead of several subtle ones.

What it gives up is real, and worth stating plainly rather than discovering
later. Measured against live Wikipedia searches, it reliably finds the
defining sentence for a well-named topic — photosynthesis, electric current,
the water cycle all come back with the definition first. It fails in two ways
that word-counting cannot fix:

* It cannot tell which *sense* of a word a learner wants. A search for
  dispersion of light returns sentences about optical fibre and about
  rainbows, and both genuinely contain "dispersion" and "light".
* It cannot tell an educational article from a coincidence. "Monsoon"
  retrieves a sentence about a television contestant of that name.

It also cannot simplify a sentence written for adults, reorder an explanation
to build from what a learner already knows, or join two sources into one idea.

Those are precisely what a language model adds, and when one is configured it
should replace this step and pass through the same gate — a model's output has
to earn its citations, where this one has them already. Until then this is
good enough for its actual job, which is drafting for a teacher to correct,
and not good enough to put in front of a student unreviewed. The draft written
by `lesson_drafting` says so in its reviewer notes.
"""

from __future__ import annotations

import re

from grounded_answer import Passage

# Split on sentence-ending punctuation followed by a capital. Imperfect with
# abbreviations, which costs a slightly odd fragment and nothing worse.
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
WORD_RE = re.compile(r"[A-Za-z0-9]+")

STOPWORDS = frozenset(
    """
    a an and are as at be but by can could did do does for from had has have
    how i if in into is it its may might of on one or that the their them then
    there these they this to was were what when which who why will with you
    """.split()
)

# Below this a "sentence" is usually a heading or a stray fragment; above it
# the text is too long to read comfortably in a lesson.
MINIMUM_SENTENCE_CHARACTERS = 40
MAXIMUM_SENTENCE_CHARACTERS = 320

# How much to prefer the sentence an article opens with. Enough to beat a
# later sentence of similar density, not enough to promote an irrelevant lead.
LEAD_SENTENCE_BONUS = 1.5

# How fast a passage's influence falls with its position in the search
# results. The top article is usually the article; the fourth is usually a
# related speciality.
RANK_DECAY = 0.6


def _words(text: str) -> set[str]:
    return {
        word
        for word in (m.group(0).lower() for m in WORD_RE.finditer(text))
        if word not in STOPWORDS and len(word) > 2
    }


def sentences(text: str) -> list[str]:
    """Split a passage into sentences worth showing a learner."""
    found = []
    for raw in SENTENCE_SPLIT.split(text.replace("\n", " ")):
        candidate = " ".join(raw.split())
        if MINIMUM_SENTENCE_CHARACTERS <= len(candidate) <= MAXIMUM_SENTENCE_CHARACTERS:
            found.append(candidate)
    return found


def extract_claims(
    query: str, passages: list[Passage], limit: int = 4
) -> list[tuple[str, int]]:
    """Pick the sentences that best answer the query, with their sources.

    Returns the shape `ground_claims` expects, so an extractive answer and a
    generated one are interchangeable from the caller's point of view.

    Two rules shape the selection beyond relevance. A sentence that repeats
    one already chosen is skipped, because encyclopaedia articles on related
    topics restate the same definition and four copies of it is not an
    explanation. And no more than two sentences come from any one passage, so
    a single article cannot crowd out the others and the reader sees that the
    answer rests on more than one source.
    """
    wanted = _words(query)
    if not wanted or not passages:
        return []

    scored: list[tuple[float, int, int, str, int]] = []
    for passage_index, passage in enumerate(passages):
        for position, sentence in enumerate(sentences(passage.text)):
            sentence_words = _words(sentence)
            if not sentence_words:
                continue
            overlap = len(wanted & sentence_words)
            if not overlap:
                continue
            score = float(overlap)
            # An encyclopaedia article opens with its definition and drifts
            # into specialist detail after that. Without this, a search for
            # dispersion of light returned a sentence about coaxial cable,
            # which is the same word in a sense no school student wants.
            if position == 0:
                score *= LEAD_SENTENCE_BONUS
            # The search engine already ranked these articles, and discarding
            # that was a mistake: a search for photosynthesis put a sentence
            # about C4 carbon fixation ahead of the definition in the main
            # article, purely because it was shorter.
            score *= 1.0 / (1.0 + RANK_DECAY * passage_index)
            # Only a mild length penalty. A stronger one favours terse
            # specialist statements over the fuller sentence that explains.
            score /= len(sentence_words) ** 0.25
            scored.append((score, -position, -passage_index, sentence, passage_index))

    scored.sort(reverse=True)

    chosen: list[tuple[str, int]] = []
    seen_words: list[set[str]] = []
    per_passage: dict[int, int] = {}
    for _, _, _, sentence, passage_index in scored:
        if len(chosen) >= limit:
            break
        if per_passage.get(passage_index, 0) >= 2:
            continue
        sentence_words = _words(sentence)
        if any(
            len(sentence_words & previous) / max(len(sentence_words), 1) > 0.7
            for previous in seen_words
        ):
            continue
        chosen.append((sentence, passage_index))
        seen_words.append(sentence_words)
        per_passage[passage_index] = per_passage.get(passage_index, 0) + 1

    # Present in source order rather than score order: the highest-scoring
    # sentence is often a detail, and an explanation should open with the
    # definition the first article leads with.
    chosen.sort(key=lambda pair: pair[1])
    return chosen
