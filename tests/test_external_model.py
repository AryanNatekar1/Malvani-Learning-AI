"""Tests for the optional language model and the leash it runs on.

None of these reach the network: the client is injected. What they check is
the boundary — that a model which invents loses what it invented, that a
missing key or package degrades instead of failing, and that nothing about a
learner is sent.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

import external_model
from external_model import (
    API_KEY_VARIABLE,
    CLAIMS_SCHEMA,
    SYSTEM_PROMPT,
    ExternalModelWriter,
    model_status,
)
from grounded_answer import Passage

ROOT = Path(__file__).resolve().parent.parent

GRAVITY = Passage(
    text=(
        "Gravity gives every falling object the same acceleration regardless "
        "of its mass, so a heavy stone and a light pebble released together "
        "reach the ground at the same moment."
    ),
    title="Gravity",
    url="https://en.wikipedia.org/wiki/Gravity",
)


class FakeBlock:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class FakeResponse:
    def __init__(self, payload, stop_reason: str = "end_turn") -> None:
        self.content = [FakeBlock(json.dumps(payload))]
        self.stop_reason = stop_reason


class FakeClient:
    """Stands in for anthropic.Anthropic. Records what it was asked."""

    def __init__(self, payload=None, stop_reason="end_turn", error=None) -> None:
        self.payload = payload if payload is not None else {"claims": []}
        self.stop_reason = stop_reason
        self.error = error
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return FakeResponse(self.payload, self.stop_reason)


def writer(**kwargs) -> ExternalModelWriter:
    return ExternalModelWriter(client=FakeClient(**kwargs))


class LeashTests(unittest.TestCase):
    """The model may rearrange what a source said. Nothing else."""

    def test_a_supported_sentence_survives(self) -> None:
        answer = writer(
            payload={
                "claims": [
                    {"text": "A heavy stone and a light pebble reach the ground together.",
                     "passage": 0}
                ]
            }
        ).write("gravity", [GRAVITY])
        self.assertEqual(len(answer.claims), 1)
        self.assertEqual(answer.dropped, ())

    def test_an_invented_sentence_is_dropped(self) -> None:
        """The failure this file exists to contain."""
        answer = writer(
            payload={
                "claims": [
                    {"text": "Gravity was first measured in Sindhudurg in 1642.", "passage": 0}
                ]
            }
        ).write("gravity", [GRAVITY])
        self.assertTrue(answer.is_empty)
        self.assertEqual(len(answer.dropped), 1)
        self.assertIn("not going to guess", answer.as_student_text())

    def test_a_sentence_citing_a_passage_that_does_not_exist_is_dropped(self) -> None:
        answer = writer(
            payload={"claims": [{"text": "Anything at all.", "passage": 9}]}
        ).write("gravity", [GRAVITY])
        self.assertTrue(answer.is_empty)

    def test_the_schema_forbids_prose_without_a_citation(self) -> None:
        item = CLAIMS_SCHEMA["properties"]["claims"]["items"]
        self.assertEqual(sorted(item["required"]), ["passage", "text"])
        self.assertFalse(item["additionalProperties"])

    def test_the_instructions_forbid_adding_anything(self) -> None:
        lowered = SYSTEM_PROMPT.lower()
        self.assertIn("you are not a source", lowered)
        self.assertIn("never add a fact", lowered)
        self.assertIn("return no claims at all", lowered)


class DegradationTests(unittest.TestCase):
    """Every failure has the same correct answer: carry on without a model."""

    def test_no_passages_means_no_call(self) -> None:
        client = FakeClient()
        answer = ExternalModelWriter(client=client).write("gravity", [])
        self.assertTrue(answer.is_empty)
        self.assertEqual(client.calls, [])

    def test_a_network_failure_returns_an_empty_answer(self) -> None:
        answer = writer(error=OSError("no route to host")).write("gravity", [GRAVITY])
        self.assertTrue(answer.is_empty)

    def test_a_malformed_reply_returns_an_empty_answer(self) -> None:
        client = FakeClient()
        client.create = lambda **kw: FakeResponse.__new__(FakeResponse)  # no content
        answer = ExternalModelWriter(client=client).write("gravity", [GRAVITY])
        self.assertTrue(answer.is_empty)

    def test_a_refusal_returns_an_empty_answer(self) -> None:
        answer = writer(
            payload={"claims": [{"text": "something", "passage": 0}]},
            stop_reason="refusal",
        ).write("gravity", [GRAVITY])
        self.assertTrue(answer.is_empty)

    def test_no_key_reports_unavailable_rather_than_failing(self) -> None:
        """Checked with the package present, since that is the other branch.

        On a machine without `anthropic` installed the package message comes
        first, which is correct and is covered by the next test.
        """
        with mock.patch.dict(sys.modules, {"anthropic": mock.Mock()}):
            with mock.patch.dict("os.environ", {API_KEY_VARIABLE: ""}, clear=False):
                status = model_status()
        self.assertFalse(status.available)
        self.assertIn(API_KEY_VARIABLE, status.reason)
        self.assertIn("Nothing else in the app needs it", status.reason)

    def test_a_key_and_the_package_together_report_ready(self) -> None:
        with mock.patch.dict(sys.modules, {"anthropic": mock.Mock()}):
            with mock.patch.dict("os.environ", {API_KEY_VARIABLE: "test-key"}, clear=False):
                status = model_status()
        self.assertTrue(status.available)
        self.assertTrue(status.model)

    def test_a_missing_package_is_explained_not_raised(self) -> None:
        real_import = __import__

        def no_anthropic(name, *args, **kwargs):
            if name == "anthropic":
                raise ImportError("not installed")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", no_anthropic):
            status = model_status()
        self.assertFalse(status.available)
        self.assertIn("pip install anthropic", status.reason)

    def test_an_unavailable_model_still_returns_the_passages(self) -> None:
        """So the caller can fall back to selecting sentences itself."""
        with mock.patch.object(
            external_model, "model_status",
            return_value=external_model.ModelStatus(False, "no key"),
        ):
            answer = ExternalModelWriter().write("gravity", [GRAVITY])
        self.assertTrue(answer.is_empty)
        self.assertEqual(answer.passages, (GRAVITY,))


class PrivacyTests(unittest.TestCase):
    def test_only_the_topic_and_the_passages_are_sent(self) -> None:
        client = FakeClient(payload={"claims": []})
        ExternalModelWriter(client=client).write("gravity", [GRAVITY])
        sent = json.dumps(client.calls[0])
        self.assertIn("gravity", sent)
        self.assertIn("Gravity gives every falling object", sent)
        for private in ("progress", "myths", "quizCorrect", "student_profile", "local_data"):
            with self.subTest(field=private):
                self.assertNotIn(private, sent)

    def test_no_key_is_committed_to_the_repository(self) -> None:
        source = (SRC_DIR / "external_model.py").read_text(encoding="utf-8")
        self.assertNotIn("sk-ant", source)
        self.assertIn('os.environ.get(API_KEY_VARIABLE', source)


class PrinciplesFileTests(unittest.TestCase):
    """The rules are only worth writing down if they point at the code."""

    def setUp(self) -> None:
        self.text = (ROOT / "PRINCIPLES.md").read_text(encoding="utf-8")

    def test_it_names_the_files_that_enforce_each_rule(self) -> None:
        for path in (
            "src/grounded_answer.py",
            "src/external_model.py",
            "src/language_engine.py",
            "src/student_engine.py",
            "data/lesson_drafts/",
            "sw.js",
        ):
            with self.subTest(path=path):
                self.assertIn(path, self.text)

    def test_every_file_it_points_at_exists(self) -> None:
        import re

        referenced = set(re.findall(r"`((?:src|tests|data)/[\w./]+)`", self.text))
        self.assertTrue(referenced)
        for path in sorted(referenced):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).exists(), f"{path} is named but missing")

    def test_it_states_the_rule_the_others_serve(self) -> None:
        flattened = " ".join(self.text.split())
        self.assertIn("may never make something up", flattened)


if __name__ == "__main__":
    unittest.main()
