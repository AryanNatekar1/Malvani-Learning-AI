"""The contract a generated answer must satisfy before a student sees it.

The project is moving toward answering questions it has no hand-written lesson
for: search the web, filter what comes back, and let a language model shape the
presentation. That is the only way the content side ever scales past what one
person can write by hand.

It is also the fastest way to start lying to students, so the rule here is
narrow and absolute:

    The model is never the source. It may only rearrange material that
    came from somewhere citable.

Everything below enforces that. A generator does not return prose; it returns
claims, each attributed to a retrieved passage. Anything it cannot attribute is
stripped before display and reported separately, so a dropped claim is visible
to a reviewer instead of silently vanishing.

What this module does NOT do, deliberately:

* It does not call a search engine or a model. Those are plugged in behind
  `RetrievalProvider`, and the default refuses rather than inventing.
* It does not decide whether a source is any good. Judging a source is a
  separate problem, and pretending a URL equals a fact would defeat the point.
* It does not prove a claim is true. The support check is lexical, which
  catches wholesale fabrication and nothing subtler. It is a floor, not a
  guarantee, and the reviewer notes say so in the student-facing output.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


# Words carry no evidence on their own, so they are ignored when checking
# whether a claim actually overlaps the passage it cites. The Devanagari
# entries are ordinary grammar shared by Marathi and Hindi — and, is, not,
# this, in — used only for scoring and never shown to anyone, so none of this
# is a claim about what a word means.
STOPWORDS = frozenset(
    """
    a an and are as at be been but by can could did do does for from had has
    have how i if in into is it its may might more most much must no not of on
    one only or other our out should so some such than that the their them
    over then there these they this those through to too under until up use used
    using very was we were what when where which while who why will with would
    you your
    आणि आहे आहेत या यात याचा ते तो ती हे हा ही एक मध्ये वर पण किंवा असे असा
    अशी होते होता नाही ना का जे ज्या त्या त्याच्या म्हणून म्हणजे सुद्धा
    और है हैं का की के को में से यह वह नहीं पर जो कि भी हो था थी थे
    """.split()
)

# A claim must share at least this fraction of its meaningful words with the
# passage it cites. Set low on purpose: the aim is to catch a model inventing
# a sentence wholesale, not to force it to quote.
MINIMUM_SUPPORT = 0.4

# Devanagari vowel signs are combining marks, which Python does not count as
# alphanumeric, so a plain \w breaks गुरुत्वाकर्षण into fragments at every
# matra and [A-Za-z0-9] misses it entirely. Naming the block keeps the word
# whole.
#
# This mattered more than it looks. With the old ASCII-only pattern every
# Devanagari claim had zero meaningful words, scored zero support, and was
# dropped — so the gate silently rejected all Marathi and Hindi content while
# reporting nothing unusual. Any future translated lesson would have hit the
# same wall.
DEVANAGARI = r"ऀ-ॿ"
WORD_RE = re.compile(rf"(?:[^\W_]|[{DEVANAGARI}])+", re.UNICODE)

# Devanagari words are written with combining marks that each count as a
# character, so a Latin "longer than two" threshold keeps more noise.
MINIMUM_WORD_LENGTH = 3


@dataclass(frozen=True)
class Passage:
    """A retrieved piece of text, and where it came from.

    `url` is required. A passage with no traceable origin cannot support a
    claim, because a reader has no way to check it.
    """

    text: str
    title: str
    url: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("A passage with no text cannot support anything.")
        if not self.url.strip():
            raise ValueError(
                "A passage must carry its source URL, or a reader cannot check it."
            )


@dataclass(frozen=True)
class Claim:
    """One statement, and the index of the passage it is drawn from."""

    text: str
    passage_index: int


@dataclass(frozen=True)
class GroundedAnswer:
    """An answer that has been through the gate.

    `claims` survived attribution. `dropped` did not, and is kept rather than
    discarded so a reviewer can see what the model tried to assert without
    support — which is the most useful signal there is about a generator.
    """

    claims: tuple[Claim, ...]
    passages: tuple[Passage, ...]
    dropped: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        """True when nothing survived, so the caller must say "I don't know"."""
        return not self.claims

    def cited_passages(self) -> tuple[Passage, ...]:
        """Only the sources actually used, in first-citation order."""
        seen: list[int] = []
        for claim in self.claims:
            if claim.passage_index not in seen:
                seen.append(claim.passage_index)
        return tuple(self.passages[index] for index in seen)

    def as_student_text(self) -> str:
        """Render for a student, with sources attached and status stated.

        The draft notice is not decoration. A student has no way to tell a
        retrieved-and-arranged answer from a reviewed lesson, so the answer
        has to say which it is.
        """
        if self.is_empty:
            return (
                "I could not find this in a source I can show you, so I am not "
                "going to guess. Try a lesson in the app, or ask your teacher."
            )
        used = self.cited_passages()
        numbering = {id(passage): number for number, passage in enumerate(used, start=1)}
        lines = []
        for claim in self.claims:
            passage = self.passages[claim.passage_index]
            lines.append(f"{claim.text} [{numbering[id(passage)]}]")
        body = " ".join(lines)
        sources = "\n".join(
            f"[{number}] {passage.title} — {passage.url}"
            for number, passage in enumerate(used, start=1)
        )
        return (
            f"{body}\n\nSources:\n{sources}\n\n"
            "This answer was assembled from the sources above, not written by a "
            "teacher. Check it before relying on it for coursework."
        )


def _meaningful_words(text: str) -> set[str]:
    return {
        word
        for word in (match.group(0).lower() for match in WORD_RE.finditer(text))
        if word not in STOPWORDS and len(word) >= MINIMUM_WORD_LENGTH
    }


def support_ratio(claim_text: str, passage: Passage) -> float:
    """Fraction of a claim's meaningful words that appear in its passage.

    A blunt instrument. It reliably catches a claim that shares nothing with
    the text it cites, and it cannot catch a plausible distortion of that
    text. Treated as a floor, never as verification.
    """
    claim_words = _meaningful_words(claim_text)
    if not claim_words:
        return 0.0
    passage_words = _meaningful_words(passage.text)
    return len(claim_words & passage_words) / len(claim_words)


def ground_claims(
    proposed: list[tuple[str, int]],
    passages: list[Passage],
    minimum_support: float = MINIMUM_SUPPORT,
) -> GroundedAnswer:
    """Keep only the claims a retrieved passage actually supports.

    `proposed` is what a generator produced: pairs of claim text and the index
    of the passage it says that claim came from. A claim is dropped when its
    index is out of range or when it shares too little with the passage it
    points at. Dropping is the default; surviving is what has to be earned.
    """
    kept: list[Claim] = []
    dropped: list[str] = []
    for text, index in proposed:
        if not text.strip():
            continue
        if not 0 <= index < len(passages):
            dropped.append(text)
            continue
        if support_ratio(text, passages[index]) < minimum_support:
            dropped.append(text)
            continue
        kept.append(Claim(text=text.strip(), passage_index=index))
    return GroundedAnswer(
        claims=tuple(kept), passages=tuple(passages), dropped=tuple(dropped)
    )


class RetrievalProvider(ABC):
    """Where passages come from. No implementation ships yet."""

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> tuple[Passage, ...]:
        """Return passages that may bear on the query, each with its source."""


class UnavailableRetrievalProvider(RetrievalProvider):
    """The default: no search configured, and no pretending otherwise.

    Returning nothing is the correct behaviour, not a stub to be filled in
    with placeholder text. An empty result makes `ground_claims` produce an
    empty answer, which the app renders as "I could not find this" — the same
    outcome a real search with no usable hits should produce.
    """

    def search(self, query: str, limit: int = 5) -> tuple[Passage, ...]:
        return ()
