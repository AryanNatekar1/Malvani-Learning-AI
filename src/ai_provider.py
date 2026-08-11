"""Provider-neutral AI interface with a safe, local offline implementation.

No network provider is configured by default.  The offline provider uses the
small neural intent model only to route UI actions; it never generates facts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from neural_intent import UNKNOWN_INTENT, predict_intent


INTENT_CUES = {
    "lesson": ("explain", "teach", "show the lesson", "understand", "what is"),
    "hint": ("hint", "clue", "guide me", "help me solve"),
    "challenge": ("challenge", "practice problem", "exercise", "test my thinking"),
    "solution": ("solution", "show the answer", "give me the answer", "reveal"),
    "quiz": ("quiz", "start a test", "practice test"),
}


@dataclass(frozen=True)
class AIResult:
    """A provider response suitable for routing, not a factual lesson answer."""

    intent: str
    confidence: float
    message: str


class AIProvider(ABC):
    """Interface for optional future local or hosted AI adapters."""

    @abstractmethod
    def generate_response(self, student_message: str) -> AIResult:
        """Interpret a request without becoming the factual source of truth."""


class OfflineAIProvider(AIProvider):
    """Dependency-free fallback that works without an API key or network."""

    def generate_response(self, student_message: str) -> AIResult:
        intent, confidence = predict_intent(student_message)
        if intent != UNKNOWN_INTENT and not _has_explicit_intent_cue(student_message, intent):
            intent = UNKNOWN_INTENT
            confidence = 0.0
        if intent == UNKNOWN_INTENT:
            return AIResult(
                intent=intent,
                confidence=confidence,
                message=(
                    "Offline AI could not confidently classify that request. "
                    "Please ask about a supported topic or use a learning button."
                ),
            )
        return AIResult(
            intent=intent,
            confidence=confidence,
            message=f"Offline intent model selected: {intent}.",
        )


def _has_explicit_intent_cue(student_message: str, intent: str) -> bool:
    """Keep the narrow neural model advisory instead of trusting false positives."""
    normalized_message = " ".join(student_message.lower().split())
    return any(cue in normalized_message for cue in INTENT_CUES.get(intent, ()))


class UnavailableExternalAIProvider(AIProvider):
    """Honest fallback placeholder until a configured provider is deliberately added."""

    def generate_response(self, student_message: str) -> AIResult:
        return AIResult(
            intent=UNKNOWN_INTENT,
            confidence=0.0,
            message=(
                "No external AI provider is configured. The local lessons and "
                "offline learning tools remain available."
            ),
        )
