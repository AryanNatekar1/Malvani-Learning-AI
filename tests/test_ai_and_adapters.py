"""Tests for provider fallback, visuals, and optional-voice availability."""

import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from ai_provider import OfflineAIProvider, UnavailableExternalAIProvider
from media_engine import get_visual
from voice_engine import DisabledVoiceProvider


class AIAndAdapterTests(unittest.TestCase):
    def test_offline_provider_routes_but_does_not_generate_facts(self) -> None:
        result = OfflineAIProvider().generate_response("Give me a hint")
        self.assertEqual(result.intent, "hint")
        self.assertIn("Offline intent model", result.message)

    def test_external_provider_falls_back_honestly(self) -> None:
        result = UnavailableExternalAIProvider().generate_response("Explain gravity")
        self.assertEqual(result.intent, "unknown")
        self.assertIn("No external AI provider", result.message)

    def test_visuals_and_voice_are_explicit_about_availability(self) -> None:
        self.assertIsNotNone(get_visual("gravity"))
        self.assertIsNone(get_visual("energy"))
        voice = DisabledVoiceProvider()
        self.assertFalse(voice.is_available)
        self.assertIn("not installed", voice.unavailable_reason())


if __name__ == "__main__":
    unittest.main()
