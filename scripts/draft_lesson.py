"""Draft a lesson for a topic the library does not cover yet.

    py scripts/draft_lesson.py "dispersion of light" --subject Physics

Searches Wikipedia, keeps only the sentences a retrieved passage supports,
and writes a draft to data/lesson_drafts/ for a teacher to correct. Nothing it
writes is a finished lesson and nothing it writes reaches a student: drafts
live outside data/lessons/, so the app's loader never sees them.

This exists because the drafting pipeline was otherwise unreachable. Searching
and grounding worked, and a teacher had no way to run either, which left the
one route by which the hand-written library could grow faster than one person
typing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from extractive_answer import extract_claims
from grounded_answer import ground_claims
from lesson_drafting import DEFAULT_DRAFT_DIR, draft_lesson
from wikipedia_retrieval import LANGUAGE_EDITIONS, WikipediaRetrievalProvider

SUBJECTS = ("Physics", "Mathematics", "Chemistry", "Biology", "Computer Science")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Draft a lesson from searched sources, for a teacher to review.",
        epilog="Nothing this writes is reviewed, and nothing reaches a student.",
    )
    parser.add_argument("topic", help='the topic to draft, e.g. "dispersion of light"')
    parser.add_argument(
        "--subject", default="Physics", choices=SUBJECTS, help="which subject it belongs to"
    )
    parser.add_argument(
        "--language",
        default="English",
        choices=sorted(LANGUAGE_EDITIONS),
        help="which Wikipedia to read; Marathi and Hindi are written by speakers",
    )
    parser.add_argument(
        "--sentences", type=int, default=4, help="how many sentences to keep (default 4)"
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_DRAFT_DIR, help="where to write the draft"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="show the draft without writing it"
    )
    args = parser.parse_args(argv)

    print(f'Searching {args.language} Wikipedia for "{args.topic}"...')
    provider = WikipediaRetrievalProvider(language=args.language)
    passages = list(provider.search(args.topic, limit=4))
    if not passages:
        print(
            "\nNothing came back. Either there is no connection, or the search "
            "found nothing usable.\nNo draft written."
        )
        return 1

    print(f"  found {len(passages)} article(s):")
    for passage in passages:
        print(f"    - {passage.title}")

    answer = ground_claims(
        extract_claims(args.topic, passages, limit=args.sentences), passages
    )
    print(f"\nKept {len(answer.claims)} sentence(s); dropped {len(answer.dropped)}.")
    for dropped in answer.dropped:
        print(f"  dropped (unsupported): {dropped[:90]}")

    draft = draft_lesson(args.topic, args.subject, answer)
    if draft is None:
        print(
            "\nNo sentence was supported by a source, so there is nothing "
            "honest to write.\nNo draft written."
        )
        return 1

    print("\n--- what the draft says ---")
    print(answer.as_student_text())

    if draft.linked_places:
        print("\nSuggested places (matched by subject matter, not chosen by a person):")
        for place in draft.linked_places:
            print(f"  - {place.name}")
    else:
        print("\nNo documented place matched this topic.")

    if args.dry_run:
        print("\nDry run: nothing written.")
        return 0

    path = draft.write(args.out)
    # --out may point anywhere, and relative_to raises rather than giving up,
    # so fall back to the full path instead of crashing after a successful write.
    try:
        shown = path.relative_to(PROJECT_DIR)
    except ValueError:
        shown = path
    print(f"\nWritten to {shown}")
    print("\nBefore this can become a lesson, somebody has to:")
    for index, note in enumerate(draft.reviewer_notes, start=1):
        print(f"  {index}. {note}")
    print(
        "  then write the quiz, challenge and observation by hand, and move the\n"
        "     file into data/lessons/<subject>/ with verification_status set\n"
        "     once a teacher has actually checked it."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
