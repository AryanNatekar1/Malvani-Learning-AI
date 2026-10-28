"""The optional language model, and the leash it runs on.

Everything else in this project works with no model, no key and no account.
This file is the one place a hosted model is allowed in, and it exists because
selecting sentences has a ceiling: it cannot simplify prose written for adults,
reorder an explanation to build from what a learner already knows, or join two
sources into one idea. A model can. A model can also write a fluent paragraph
that no source supports, which is the failure this whole project is built to
refuse.

So the model is never asked for facts. It is given passages that were already
retrieved, and asked only to rearrange them — and every sentence it returns
must name the passage it came from. The result then goes through
`ground_claims` exactly as an extractive answer does, and anything a passage
does not support is dropped before a learner sees it. The model is a writer
working from sources it did not choose and cannot add to.

Three things follow from that, and all three are deliberate:

* No key is stored in this repository. It is read from the environment, and
  with none set this provider reports itself unavailable and the app carries
  on with the extractive path.
* The `anthropic` package is an optional dependency. The core app still has
  none, so a school can run the whole thing from a clone with nothing
  installed; importing is deferred so a missing package is a clear message
  rather than an import error at startup.
* Nothing about a learner is sent. The topic and the retrieved passages go;
  their name, answers, progress and writing stay on their machine.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from grounded_answer import GroundedAnswer, Passage, ground_claims

# Read from the environment, never from a file in the repository.
API_KEY_VARIABLE = "ANTHROPIC_API_KEY"
MODEL_VARIABLE = "MALVANI_MODEL"

DEFAULT_MODEL = "claude-opus-5-5"

# A school laptop on a slow line should fail quickly and fall back, rather
# than leave a learner looking at a spinner.
DEFAULT_TIMEOUT_SECONDS = 45.0

# The schema is the leash. Prose cannot come back; only sentences, each
# carrying the index of the passage it was drawn from.
CLAIMS_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": (
                            "One sentence a learner can read, saying something "
                            "the cited passage supports."
                        ),
                    },
                    "passage": {
                        "type": "integer",
                        "description": "Index of the passage this sentence comes from.",
                    },
                },
                "required": ["text", "passage"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["claims"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """\
You rewrite retrieved encyclopaedia text for a student aged 13 to 16 who is \
reading in their second language.

You are not a source. Every sentence you write must be supported by one of the \
numbered passages you are given, and must name that passage. If the passages do \
not answer the question, return no claims at all. Never add a fact from your own \
knowledge, however certain you are of it, and never add an example, a number, a \
date, or a place name that is not in the passages.

Write plainly. Short sentences. Prefer the ordinary word to the technical one, \
and when a technical term is unavoidable, say what it means in the same breath. \
Lead with what the thing is before any detail about it.

Do not open with a greeting, do not address the reader, and do not say what you \
are about to do.\
"""


@dataclass(frozen=True)
class ModelStatus:
    """Whether the optional model can be used, and why not when it cannot."""

    available: bool
    reason: str
    model: str = ""


def model_status() -> ModelStatus:
    """Report availability without calling anything or raising.

    Separated from the provider so a settings screen can say what is wrong —
    no key, or no package — instead of showing a failure at the moment a
    learner asks a question.
    """
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return ModelStatus(
            False,
            "The anthropic package is not installed. The app works without it; "
            "run 'py -m pip install anthropic' to enable the model.",
        )
    if not os.environ.get(API_KEY_VARIABLE, "").strip():
        return ModelStatus(
            False,
            f"No API key found. Set {API_KEY_VARIABLE} in your environment to "
            "enable the model. Nothing else in the app needs it.",
        )
    return ModelStatus(True, "Ready.", os.environ.get(MODEL_VARIABLE) or DEFAULT_MODEL)


class ExternalModelWriter:
    """Rewrites retrieved passages for a learner, and cites every sentence."""

    def __init__(
        self,
        model: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client=None,
    ) -> None:
        self.model = model or os.environ.get(MODEL_VARIABLE) or DEFAULT_MODEL
        self.timeout = timeout
        self._client = client  # injected in tests; never reaches the network

    def write(
        self, topic: str, passages: list[Passage], sentences: int = 4
    ) -> GroundedAnswer:
        """Return an answer built only from what the passages support.

        Returns an empty answer rather than raising, for any reason at all: no
        key, no package, no network, a refusal, a malformed reply. The caller
        renders an empty answer as "I could not find this in a source I can
        show you", which is the right thing to say in every one of those cases.
        """
        if not passages:
            return GroundedAnswer(claims=(), passages=())

        client = self._client
        if client is None:
            status = model_status()
            if not status.available:
                return GroundedAnswer(claims=(), passages=tuple(passages))
            import anthropic

            client = anthropic.Anthropic(timeout=self.timeout)

        numbered = "\n\n".join(
            f"[{index}] {passage.title}\n{passage.text}"
            for index, passage in enumerate(passages)
        )
        request = (
            f"Topic the student asked about: {topic}\n\n"
            f"Passages:\n\n{numbered}\n\n"
            f"Write at most {sentences} sentences explaining this topic to the "
            f"student, using only these passages. Give each sentence the index "
            f"of the passage that supports it."
        )

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": request}],
                output_config={
                    "format": {"type": "json_schema", "schema": CLAIMS_SCHEMA}
                },
            )
            # Safety classifiers can decline; that is a 200 with no content to read.
            if getattr(response, "stop_reason", None) == "refusal":
                return GroundedAnswer(claims=(), passages=tuple(passages))
            text = next(
                block.text for block in response.content if block.type == "text"
            )
            proposed = [
                (str(claim["text"]), int(claim["passage"]))
                for claim in json.loads(text).get("claims", [])
            ]
        except Exception:
            # Deliberately broad. A lesson app must not fall over because a
            # hosted service changed a field name or a line went down, and
            # every failure here has the same correct answer: use no model.
            return GroundedAnswer(claims=(), passages=tuple(passages))

        # The same gate an extractive answer passes through. A model that
        # writes a fluent sentence no passage supports loses it here.
        return ground_claims(proposed, passages)
