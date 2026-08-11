"""A tiny local neural network for recognising learning-interface intents.

This module is deliberately small and dependency-free so that it can run
offline alongside the existing file-based lessons.  It recognises only five
*interface* intents: asking for a lesson, a hint, a challenge, a solution, or
a quiz.

Important limitations:

* This is a small feed-forward neural network, not an LLM.
* It does not know school subjects, cultural facts, Marathi, or Malvani.
* It must never be used as a source of factual answers.  The knowledge and
  teaching engines remain responsible for verified educational content.
* An ``unknown`` result means the interface should use a safe fallback rather
  than guess what the student meant.

The training examples are intentionally non-cultural UI requests.  Local
cultural knowledge belongs in reviewed lesson data, not in this classifier.
"""

from __future__ import annotations

import math
import random
import re
from collections.abc import Iterable
from functools import lru_cache


INTENTS = ("lesson", "hint", "challenge", "solution", "quiz")
"""The supported learning-interface actions."""

UNKNOWN_INTENT = "unknown"
"""Returned when the small local model cannot classify a request safely."""

MINIMUM_CONFIDENCE = 0.60
"""The lowest confidence accepted from the local classifier."""

_RANDOM_SEED = 20260808
_TOKEN_PATTERN = re.compile(r"[a-z]+(?:'[a-z]+)?")

# These examples describe UI actions only.  They deliberately contain no
# cultural claims, translations, or factual lesson content.
TRAINING_EXAMPLES = (
    ("explain gravity", "lesson"),
    ("what is momentum", "lesson"),
    ("teach me force", "lesson"),
    ("help me understand motion", "lesson"),
    ("simple explanation please", "lesson"),
    ("tell me about energy", "lesson"),
    ("show the lesson", "lesson"),
    ("give me a hint", "hint"),
    ("i need a hint", "hint"),
    ("help me solve this", "hint"),
    ("can you guide me", "hint"),
    ("small clue please", "hint"),
    ("do not give the answer just a hint", "hint"),
    ("what should i try next", "hint"),
    ("give me a challenge", "challenge"),
    ("ask me a practice problem", "challenge"),
    ("give me a question to solve", "challenge"),
    ("test my thinking", "challenge"),
    ("give me a harder problem", "challenge"),
    ("i want an exercise", "challenge"),
    ("challenge me", "challenge"),
    ("show the solution", "solution"),
    ("give me the answer", "solution"),
    ("what is the solution", "solution"),
    ("reveal the steps", "solution"),
    ("show how to solve it", "solution"),
    ("i am ready for the answer", "solution"),
    ("explain the answer", "solution"),
    ("start a quiz", "quiz"),
    ("give me a quiz", "quiz"),
    ("ask multiple choice questions", "quiz"),
    ("test me with a quiz", "quiz"),
    ("begin a practice quiz", "quiz"),
    ("quiz me on physics", "quiz"),
    ("i want a test", "quiz"),
)


def tokenize(text: str) -> list[str]:
    """Return lowercase English-style word tokens from ``text``."""
    return _TOKEN_PATTERN.findall(text.lower())


def _build_vocabulary(examples: Iterable[tuple[str, str]]) -> tuple[str, ...]:
    """Build a stable vocabulary from the fixed training examples."""
    words = {word for text, _intent in examples for word in tokenize(text)}
    return tuple(sorted(words))


class FeedForwardIntentClassifier:
    """A beginner-readable neural classifier with one hidden layer.

    The input is a bag-of-words vector.  It flows through a tanh hidden layer
    and a softmax output layer.  Training uses gradient descent and a fixed
    random seed, making the resulting local model deterministic.
    """

    def __init__(
        self,
        vocabulary: tuple[str, ...],
        intents: tuple[str, ...] = INTENTS,
        hidden_size: int = 10,
        seed: int = _RANDOM_SEED,
    ) -> None:
        self.vocabulary = vocabulary
        self.intents = intents
        self.hidden_size = hidden_size
        self._word_index = {word: index for index, word in enumerate(vocabulary)}
        self._intent_index = {intent: index for index, intent in enumerate(intents)}

        generator = random.Random(seed)
        self.input_to_hidden = [
            [generator.uniform(-0.15, 0.15) for _word in vocabulary]
            for _unit in range(hidden_size)
        ]
        self.hidden_biases = [0.0 for _unit in range(hidden_size)]
        self.hidden_to_output = [
            [generator.uniform(-0.15, 0.15) for _unit in range(hidden_size)]
            for _intent in intents
        ]
        self.output_biases = [0.0 for _intent in intents]

    def vectorize(self, text: str) -> list[float]:
        """Convert text to a binary bag-of-words input vector."""
        vector = [0.0 for _word in self.vocabulary]
        for word in tokenize(text):
            index = self._word_index.get(word)
            if index is not None:
                vector[index] = 1.0
        return vector

    def train(
        self,
        examples: Iterable[tuple[str, str]],
        epochs: int = 250,
        learning_rate: float = 0.12,
    ) -> None:
        """Train the network using deterministic gradient descent.

        There is intentionally no random reshuffling here.  Combined with the
        fixed seed in ``__init__``, that keeps the small local model repeatable
        for students who want to inspect or rerun its training.
        """
        prepared_examples = [
            (self.vectorize(text), self._intent_index[intent])
            for text, intent in examples
        ]

        for _epoch in range(epochs):
            for features, target_index in prepared_examples:
                hidden_values, probabilities = self._forward(features)
                output_deltas = [
                    probability - float(index == target_index)
                    for index, probability in enumerate(probabilities)
                ]

                # Calculate hidden-layer errors before changing output weights.
                hidden_deltas = []
                for hidden_index, hidden_value in enumerate(hidden_values):
                    downstream_error = sum(
                        output_deltas[output_index]
                        * self.hidden_to_output[output_index][hidden_index]
                        for output_index in range(len(self.intents))
                    )
                    hidden_deltas.append(
                        downstream_error * (1.0 - hidden_value * hidden_value)
                    )

                for output_index, output_delta in enumerate(output_deltas):
                    for hidden_index, hidden_value in enumerate(hidden_values):
                        self.hidden_to_output[output_index][hidden_index] -= (
                            learning_rate * output_delta * hidden_value
                        )
                    self.output_biases[output_index] -= learning_rate * output_delta

                for hidden_index, hidden_delta in enumerate(hidden_deltas):
                    for word_index, feature_value in enumerate(features):
                        self.input_to_hidden[hidden_index][word_index] -= (
                            learning_rate * hidden_delta * feature_value
                        )
                    self.hidden_biases[hidden_index] -= learning_rate * hidden_delta

    def predict(self, text: str) -> tuple[str, float]:
        """Return the best supported intent, or a safe ``unknown`` fallback."""
        if not text or not text.strip():
            return UNKNOWN_INTENT, 0.0

        features = self.vectorize(text)
        if not any(features):
            return UNKNOWN_INTENT, 0.0

        _hidden_values, probabilities = self._forward(features)
        best_index = max(range(len(probabilities)), key=probabilities.__getitem__)
        confidence = probabilities[best_index]

        if confidence < MINIMUM_CONFIDENCE:
            return UNKNOWN_INTENT, confidence

        return self.intents[best_index], confidence

    def _forward(self, features: list[float]) -> tuple[list[float], list[float]]:
        """Run one input vector through the hidden and output layers."""
        hidden_values = [
            math.tanh(
                sum(weight * value for weight, value in zip(weights, features))
                + bias
            )
            for weights, bias in zip(self.input_to_hidden, self.hidden_biases)
        ]
        logits = [
            sum(weight * value for weight, value in zip(weights, hidden_values))
            + bias
            for weights, bias in zip(self.hidden_to_output, self.output_biases)
        ]
        return hidden_values, _softmax(logits)


def _softmax(logits: list[float]) -> list[float]:
    """Convert output scores into probabilities without numeric overflow."""
    largest_logit = max(logits)
    exponentials = [math.exp(logit - largest_logit) for logit in logits]
    total = sum(exponentials)
    return [value / total for value in exponentials]


def build_trained_model() -> FeedForwardIntentClassifier:
    """Create the deterministic local model used by ``predict_intent``."""
    model = FeedForwardIntentClassifier(_build_vocabulary(TRAINING_EXAMPLES))
    model.train(TRAINING_EXAMPLES)
    return model


@lru_cache(maxsize=1)
def _get_model() -> FeedForwardIntentClassifier:
    """Train once on first AI use so the desktop window can open promptly."""
    return build_trained_model()


def predict_intent(text: str) -> tuple[str, float]:
    """Classify a student UI request without generating a factual answer.

    The caller should use the returned label to choose an interaction flow.
    It should still ask the knowledge and teaching engines for the actual
    lesson, hint, challenge, solution, or quiz content.
    """
    return _get_model().predict(text)
