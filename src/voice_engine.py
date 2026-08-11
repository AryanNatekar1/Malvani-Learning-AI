"""Optional voice-provider boundary; the local app remains fully usable without it."""

from __future__ import annotations

from abc import ABC, abstractmethod


class VoiceProvider(ABC):
    """Interface for a future speech-to-text/text-to-speech implementation."""

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether this voice provider can be used on the current device."""

    @abstractmethod
    def unavailable_reason(self) -> str | None:
        """Explain any unavailable state without pretending voice is enabled."""


class DisabledVoiceProvider(VoiceProvider):
    """Safe default when no reviewed voice service or local model is installed."""

    @property
    def is_available(self) -> bool:
        return False

    def unavailable_reason(self) -> str:
        return (
            "Voice is not installed in the offline prototype. Text learning remains available."
        )
