"""Tests for Wikipedia retrieval.

None of these touch the network. The opener is injected, so the tests run on a
disconnected machine and in CI at the same speed, and they can simulate the
failures that matter — timeouts, captive portals, a changed API — which a live
test could not do reliably.
"""

import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from grounded_answer import ground_claims
from wikipedia_retrieval import (
    MINIMUM_EXTRACT_CHARACTERS,
    USER_AGENT,
    WikipediaRetrievalProvider,
)


def fake_response(payload: object):
    """Stand in for the context manager urlopen returns."""
    body = json.dumps(payload).encode("utf-8")

    class _Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    return _Response(body)


def page(title: str, extract: str, index: int = 1, url: str | None = None) -> dict:
    return {
        "title": title,
        "extract": extract,
        "index": index,
        "fullurl": url or f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
    }


DISPERSION = (
    "Dispersion is the phenomenon in which the phase velocity of a wave depends "
    "on its frequency. In optics, dispersion causes white light to separate into "
    "its constituent colours when it passes through a prism, because each colour "
    "is refracted by a different amount."
)


class SearchTests(unittest.TestCase):
    def provider(self, payload, record=None):
        def opener(request, timeout=None):
            if record is not None:
                record.append(request)
            return fake_response(payload)

        return WikipediaRetrievalProvider(opener=opener)

    def test_a_search_returns_citable_passages(self) -> None:
        provider = self.provider({"query": {"pages": [page("Dispersion", DISPERSION)]}})
        passages = provider.search("dispersion of light")
        self.assertEqual(len(passages), 1)
        self.assertEqual(passages[0].title, "Dispersion")
        self.assertTrue(passages[0].url.startswith("https://en.wikipedia.org/wiki/"))

    def test_results_keep_the_relevance_order_the_search_gave(self) -> None:
        provider = self.provider(
            {
                "query": {
                    "pages": [
                        page("Third", DISPERSION, index=3),
                        page("First", DISPERSION, index=1),
                        page("Second", DISPERSION, index=2),
                    ]
                }
            }
        )
        self.assertEqual(
            [p.title for p in provider.search("x")], ["First", "Second", "Third"]
        )

    def test_stub_extracts_are_skipped(self) -> None:
        provider = self.provider({"query": {"pages": [page("Stub", "Too short.")]}})
        self.assertEqual(provider.search("x"), ())
        self.assertGreater(MINIMUM_EXTRACT_CHARACTERS, len("Too short."))

    def test_disambiguation_pages_are_skipped(self) -> None:
        text = "Dispersion may refer to several things in science and " + "x " * 60
        provider = self.provider({"query": {"pages": [page("Dispersion", text)]}})
        self.assertEqual(provider.search("dispersion"), ())

    def test_a_page_without_a_url_is_skipped(self) -> None:
        bad = page("No URL", DISPERSION)
        bad["fullurl"] = ""
        provider = self.provider({"query": {"pages": [bad]}})
        self.assertEqual(provider.search("x"), ())

    def test_an_empty_query_makes_no_request(self) -> None:
        requests: list = []
        provider = self.provider({"query": {"pages": []}}, record=requests)
        self.assertEqual(provider.search("   "), ())
        self.assertEqual(requests, [])

    def test_the_request_identifies_the_project(self) -> None:
        """Wikipedia asks automated clients to say who they are."""
        requests: list = []
        provider = self.provider(
            {"query": {"pages": [page("Dispersion", DISPERSION)]}}, record=requests
        )
        provider.search("dispersion")
        self.assertEqual(requests[0].get_header("User-agent"), USER_AGENT)
        self.assertIn("Malvani", USER_AGENT)


class FailureTests(unittest.TestCase):
    """Every failure must degrade to "no passages", never to an exception."""

    def _provider_raising(self, error: Exception) -> WikipediaRetrievalProvider:
        def opener(request, timeout=None):
            raise error

        return WikipediaRetrievalProvider(opener=opener)

    def test_no_network_returns_nothing(self) -> None:
        provider = self._provider_raising(urllib.error.URLError("no route to host"))
        self.assertEqual(provider.search("dispersion of light"), ())

    def test_a_timeout_returns_nothing(self) -> None:
        provider = self._provider_raising(TimeoutError("timed out"))
        self.assertEqual(provider.search("dispersion of light"), ())

    def test_an_http_error_returns_nothing(self) -> None:
        provider = self._provider_raising(
            urllib.error.HTTPError("u", 503, "busy", {}, None)  # type: ignore[arg-type]
        )
        self.assertEqual(provider.search("dispersion of light"), ())

    def test_a_captive_portal_returning_html_returns_nothing(self) -> None:
        """A hotel or college wifi login page is not JSON, and must not crash."""

        class _HTML(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def opener(request, timeout=None):
            return _HTML(b"<html><body>Please sign in</body></html>")

        provider = WikipediaRetrievalProvider(opener=opener)
        self.assertEqual(provider.search("dispersion of light"), ())

    def test_an_unexpected_api_shape_returns_nothing(self) -> None:
        def opener(request, timeout=None):
            return fake_response({"query": {"pages": "not a list"}})

        self.assertEqual(
            WikipediaRetrievalProvider(opener=opener).search("anything"), ()
        )

    def test_a_failed_search_produces_an_honest_refusal(self) -> None:
        """The end-to-end consequence: no sources means no answer, not a guess."""
        provider = self._provider_raising(urllib.error.URLError("offline"))
        passages = list(provider.search("dispersion of light"))
        answer = ground_claims([("White light is a mixture of colours.", 0)], passages)
        self.assertTrue(answer.is_empty)
        self.assertIn("not going to guess", answer.as_student_text())


class LanguageTests(unittest.TestCase):
    def test_each_supported_language_maps_to_its_own_edition(self) -> None:
        for language, expected in (
            ("English", "en"),
            ("Marathi", "mr"),
            ("Hindi", "hi"),
        ):
            with self.subTest(language=language):
                provider = WikipediaRetrievalProvider(language=language)
                self.assertEqual(provider.edition, expected)
                self.assertIn(expected, provider.endpoint)

    def test_an_unknown_language_falls_back_to_english(self) -> None:
        """Malvani has no Wikipedia, and inventing one would be worse."""
        self.assertEqual(WikipediaRetrievalProvider(language="Malvani").edition, "en")


if __name__ == "__main__":
    unittest.main()
