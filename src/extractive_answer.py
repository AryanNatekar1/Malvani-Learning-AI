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

Two failures looked unfixable by word-counting and were not. A search for
dispersion of light used to return a sentence about telecommunication signals
in coaxial cable, and "monsoon" returned one about a television contestant of
that name. Both were counting words in a flattened block of text and throwing
away the structure the encyclopaedia had already written: a lead paragraph
defines its subject, and later paragraphs branch into other senses of the same
word. Scoring by which paragraph a sentence came from fixed both, because the
distinction was never lexical.

What remains is genuinely beyond selection. It cannot simplify a sentence
written for adults, reorder an explanation to build from what a learner
already knows, or join two sources into one idea. It cannot tell that "phase
velocity" will lose a Class 9 reader in the first line.

Those are what a language model adds, and when one is configured it should
replace this step and pass through the same gate — a model's output has to
earn its citations, where this one has them already. Until then this is good
enough for its actual job, which is drafting for a teacher to correct, and not
good enough to put in front of a student unreviewed. The draft written by
`lesson_drafting` says so in its reviewer notes.
"""

from __future__ import annotations

import re

# Share the tokenizer with the gate rather than keeping a second copy. They
# drifted once already: this module learned to read Devanagari while the gate
# still could not, so every Marathi sentence was selected and then silently
# dropped for having no supported words.
from grounded_answer import (
    DEVANAGARI,
    MINIMUM_WORD_LENGTH,
    STOPWORDS,
    WORD_RE,
    Passage,
)

# Devanagari ends a sentence with a danda (।) and has no capital letters, so
# an ASCII-only splitter found no sentences at all in Marathi and returned
# nothing without erroring — a silent failure, which is the worst kind. A
# danda always ends a sentence; Latin punctuation only counts when a capital
# or digit follows, which keeps abbreviations from splitting mid-sentence.
# Marathi Wikipedia in practice writes a full stop rather than a danda, so
# both have to end a sentence, and the character that follows may be
# Devanagari rather than a capital. Requiring a capital was why an entire
# 1,200-character Marathi article counted as one sentence and was discarded
# for being too long.
SENTENCE_SPLIT = re.compile(
    rf"(?<=[।])\s+|(?<=[.!?])\s+(?=[A-Z0-9{DEVANAGARI}])"
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

# How fast a sentence's influence falls with its paragraph's position in the
# article. Set high deliberately: the gap between "this is what the word
# means" and "the word also has this other use" is the gap between a usable
# answer and a confusing one.
PARAGRAPH_DECAY = 0.9


def _words(text: str) -> set[str]:
    return {
        word
        for word in (m.group(0).lower() for m in WORD_RE.finditer(text))
        if word not in STOPWORDS and len(word) >= MINIMUM_WORD_LENGTH
    }


def sentences(text: str) -> list[str]:
    """Split a passage into sentences worth showing a learner."""
    found = []
    for raw in SENTENCE_SPLIT.split(text.replace("\n", " ")):
        candidate = " ".join(raw.split())
        if MINIMUM_SENTENCE_CHARACTERS <= len(candidate) <= MAXIMUM_SENTENCE_CHARACTERS:
            found.append(candidate)
    return found


def paragraphs(text: str) -> list[str]:
    """Split a passage into paragraphs, keeping the order they were written in.

    An encyclopaedia lead is structured, and flattening it threw that away.
    The first paragraph defines the subject; later ones qualify it and branch
    into specialist senses. Knowing which paragraph a sentence came from is a
    stronger signal than anything counting its words can produce.
    """
    return [block for block in (b.strip() for b in text.split("\n")) if block]


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
        depth = 0
        for paragraph_index, paragraph in enumerate(paragraphs(passage.text)):
            for position, sentence in enumerate(sentences(paragraph)):
                depth += 1
                sentence_words = _words(sentence)
                if not sentence_words:
                    continue
                overlap = len(wanted & sentence_words)
                if not overlap:
                    continue
                score = float(overlap)
                # A lead paragraph defines its subject; later ones qualify it
                # and wander into other senses of the same word. This is what
                # finally separated rainbows from optical fibre in a search
                # for dispersion of light — both paragraphs are about
                # dispersion and light, and only one is the definition.
                score *= 1.0 / (1.0 + PARAGRAPH_DECAY * paragraph_index)
                # Within a paragraph, the opening sentence carries the claim.
                if position == 0:
                    score *= LEAD_SENTENCE_BONUS
                # The search engine already ranked these articles, and
                # discarding that was a mistake: a search for photosynthesis
                # put a sentence about C4 carbon fixation ahead of the
                # definition, purely because it was shorter.
                score *= 1.0 / (1.0 + RANK_DECAY * passage_index)
                # Only a mild length penalty. A stronger one favours terse
                # specialist statements over the fuller sentence that explains.
                score /= len(sentence_words) ** 0.25
                scored.append((score, -depth, -passage_index, sentence, passage_index))

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
    if not chosen and _written_in_another_script(query, passages):
        chosen = _opening_sentences(passages, limit)
    chosen.sort(key=lambda pair: pair[1])
    return chosen


def _written_in_another_script(query: str, passages: list[Passage]) -> bool:
    """True when the query and the passages cannot share words at all.

    This is the difference between "the scoring could not see" and "there is
    nothing here". A Latin query against a Devanagari article has no possible
    overlap however relevant the article is, and the right answer is to use
    the article. A Latin query against a Latin article that shares no words is
    simply off-topic, and the right answer is to say so — a passage about
    mangoes must never be returned for a question about dispersion.
    """
    query_devanagari = bool(re.search(f"[{DEVANAGARI}]", query))
    passage_devanagari = any(
        re.search(f"[{DEVANAGARI}]", passage.text) for passage in passages
    )
    return query_devanagari != passage_devanagari


def _opening_sentences(passages: list[Passage], limit: int) -> list[tuple[str, int]]:
    """Take how the best-ranked article opens.

    Used only when scoring was structurally unable to work. An encyclopaedia
    opens with its definition, so its first sentences are a reasonable answer
    when relevance cannot be measured rather than merely came out low.
    """
    for passage_index, passage in enumerate(passages):
        opening = []
        for paragraph in paragraphs(passage.text):
            for sentence in sentences(paragraph):
                opening.append((sentence, passage_index))
                if len(opening) >= limit:
                    return opening
            if opening:
                return opening
    return []
