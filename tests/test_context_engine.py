"""Tests for manual, privacy-safe educational context selection."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from context_engine import (
    NEEDS_REVIEW,
    VERIFIED,
    ContextFormatError,
    ContextRecord,
    ContextRepository,
    load_context_records,
)


def verified_water_context() -> ContextRecord:
    """A deliberately generic record used only as test data, not a local claim."""
    return ContextRecord(
        identifier="water-body-observation",
        title="Water-body observation",
        category="environment",
        educational_prompt=(
            "Use an observed water surface as an optional starting point for a "
            "waves investigation."
        ),
        topics=("waves",),
        verification_status=VERIFIED,
        source="Teacher-reviewed classroom activity guide",
        region="Sindhudurg",
    )


class ContextEngineTests(unittest.TestCase):
    def test_verified_source_backed_manual_context_is_available(self) -> None:
        repository = ContextRepository([verified_water_context()])

        selection = repository.select_manual("WATER-BODY-OBSERVATION")

        self.assertTrue(selection.is_available)
        assert selection.context is not None
        self.assertEqual(selection.context.title, "Water-body observation")
        self.assertEqual(selection.context.category, "environment")
        self.assertEqual(selection.context.region, "Sindhudurg")
        self.assertEqual(selection.context.source, "Teacher-reviewed classroom activity guide")
        self.assertIn("waves investigation", selection.context.educational_prompt)
        self.assertIsNone(selection.notice)
        self.assertEqual(repository.student_options(), (selection.context,))

    def test_unreviewed_or_unsourced_records_are_never_student_options(self) -> None:
        unreviewed = ContextRecord(
            identifier="draft-pond",
            title="Unreviewed pond claim",
            category="environment",
            educational_prompt="Do not show this draft prompt.",
            topics=("waves",),
            verification_status=NEEDS_REVIEW,
            source="Draft notes",
            region="Sindhudurg",
        )
        unsourced = ContextRecord(
            identifier="missing-source",
            title="Unsourced verified claim",
            category="environment",
            educational_prompt="Do not show this unsourced prompt.",
            topics=("waves",),
            verification_status=VERIFIED,
            source=None,
            region="Sindhudurg",
        )
        repository = ContextRepository([unreviewed, unsourced])

        self.assertEqual(repository.student_options(), ())
        for identifier in ("draft-pond", "missing-source"):
            with self.subTest(identifier=identifier):
                selection = repository.select_manual(identifier)
                self.assertFalse(selection.is_available)
                self.assertIsNone(selection.context)
                self.assertIn("without a local claim", selection.notice or "")
                self.assertNotIn("Unreviewed pond claim", selection.notice or "")
                self.assertNotIn("prompt", selection.notice or "")

    def test_missing_or_unknown_manual_selection_has_an_honest_fallback(self) -> None:
        repository = ContextRepository([verified_water_context()])

        no_selection = repository.select_manual(None)
        unknown_selection = repository.select_manual("made-up-location")

        self.assertFalse(no_selection.is_available)
        self.assertIn("No local context was selected", no_selection.notice or "")
        self.assertFalse(unknown_selection.is_available)
        self.assertIn("not available", unknown_selection.notice or "")
        self.assertIn("without a local claim", unknown_selection.notice or "")

    def test_loads_local_json_records_without_any_network_or_location_access(self) -> None:
        raw_record = {
            "id": "water-observation",
            "title": "Water observation",
            "category": "environment",
            "educational_prompt": "Ask what changes can be observed over time.",
            "topics": ["waves"],
            "verification_status": VERIFIED,
            "source": "Reviewed school science resource",
            "region": "Konkan",
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            context_path = Path(temporary_directory) / "water.json"
            context_path.write_text(json.dumps([raw_record]), encoding="utf-8")

            records = load_context_records(Path(temporary_directory))
            repository = ContextRepository.from_directory(Path(temporary_directory))

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].identifier, "water-observation")
        self.assertEqual(repository.select_manual("water-observation").context.source, raw_record["source"])

    def test_verified_json_record_requires_a_real_source(self) -> None:
        with self.assertRaises(ContextFormatError):
            ContextRecord.from_mapping(
                {
                    "id": "missing-source",
                    "title": "Missing source",
                    "category": "environment",
                    "educational_prompt": "A prompt",
                    "topics": ["waves"],
                    "verification_status": VERIFIED,
                    "source": "  ",
                }
            )

    def test_json_record_requires_explicit_topic_scope(self) -> None:
        with self.assertRaises(ContextFormatError):
            ContextRecord.from_mapping(
                {
                    "id": "untargeted-context",
                    "title": "Untargeted context",
                    "category": "environment",
                    "educational_prompt": "A context cannot apply to every lesson by default.",
                    "verification_status": NEEDS_REVIEW,
                }
            )

    def test_context_is_never_selected_for_an_unrelated_topic(self) -> None:
        repository = ContextRepository([verified_water_context()])

        selection = repository.select_manual("water-body-observation", topic="gravity")

        self.assertFalse(selection.is_available)
        self.assertIn("not available for this lesson", selection.notice or "")
        self.assertEqual(repository.student_options(topic="gravity"), ())
        self.assertEqual(len(repository.student_options(topic="waves")), 1)


if __name__ == "__main__":
    unittest.main()
