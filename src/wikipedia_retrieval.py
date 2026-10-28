"""Retrieve passages from Wikipedia, with no API key and no dependencies.

This is the first real source behind `RetrievalProvider`. Wikipedia was chosen
for reasons that matter to this project rather than convenience: it needs no
key, so nothing secret ever enters the repository; every passage has a stable
public URL a student or teacher can open and check; and it is available in
Marathi and Hindi as well as English, so the same code path serves a learner
who is not reading in English.

It is not treated as authoritative. Nothing here decides whether an article is
any good — passages go through `ground_claims`, which attaches a citation to
every surviving sentence, and the student-facing text says the answer was
assembled rather than taught. Wikipedia is a starting point a reader can
verify, which is a much weaker and more honest claim than "a source of truth".

Offline behaviour is deliberate. Every network failure returns no passages
rather than raising, because the app's promise is that it keeps working on a
weak connection. A failed search must degrade to "I could not find this",
which is the same honest answer an empty search gives, and must never take the
rest of the app down with it.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from grounded_answer import Passage, RetrievalProvider


# Wikipedia asks automated clients to identify themselves and say where to
# complain. An honest agent string is a condition of being allowed to use it.
USER_AGENT = (
    "MalvaniLearningAI/1.0 "
    "(educational project; https://github.com/AryanNatekar1/Malvani-Learning-AI)"
)

# Short extracts are usually disambiguation stubs or list pages, which carry
# no explanation and would only dilute what a generator has to work with.
MINIMUM_EXTRACT_CHARACTERS = 120

DEFAULT_TIMEOUT_SECONDS = 8.0

# Wikipedia editions this project might realistically read. Keyed by the
# language names already used throughout the app.
LANGUAGE_EDITIONS = {
    "English": "en",
    "Marathi": "mr",
    "Hindi": "hi",
    "Konkani": "gom",
}


class WikipediaRetrievalProvider(RetrievalProvider):
    """Search one Wikipedia edition and return citable passages."""

    def __init__(
        self,
        language: str = "English",
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        opener=None,
    ) -> None:
        self.edition = LANGUAGE_EDITIONS.get(language, "en")
        self.timeout = timeout
        # Injectable so tests never touch the network.
        self._open = opener or urllib.request.urlopen

    @property
    def endpoint(self) -> str:
        return f"https://{self.edition}.wikipedia.org/w/api.php"

    def search(self, query: str, limit: int = 5) -> tuple[Passage, ...]:
        """Find articles in this edition, reaching through English if needed.

        Searching a smaller edition directly answered four of ten school
        topics in Marathi, not because the articles were missing but because
        its search could not match an English query against them: gravity,
        electric current, food chain, monsoon and percentage all exist in
        Marathi and none were found.

        So a non-English lookup also asks English Wikipedia which article the
        query means, then follows the interlanguage link editors have already
        drawn to the Marathi or Hindi version of that same article. The
        content is still written by speakers of the language; only the way of
        finding it borrows English's better search.
        """
        query = query.strip()
        if not query:
            return ()
        limit = max(1, min(limit, 10))
        if self.edition == "en":
            return self._direct_search(query, limit)

        # The cross-language link goes first, not last. A smaller edition's
        # search ranks badly against a query in another script: asked for
        # "gravity", Marathi Wikipedia returned a person's name, a disused
        # physics term and nothing about gravity, which filled every slot with
        # junk while गुरुत्वाकर्षण sat one editor-maintained link away.
        found = self._search_through_english(query, limit)
        seen = {passage.title for passage in found}
        for passage in self._direct_search(query, limit):
            if len(found) >= limit:
                break
            if passage.title not in seen:
                found += (passage,)
                seen.add(passage.title)
        return found

    def _direct_search(self, query: str, limit: int) -> tuple[Passage, ...]:
        """Search this edition on its own terms.

        One request does both jobs: `generator=search` finds the articles and
        `prop=extracts|info` returns their opening text and canonical URL, so
        a lookup costs a single round trip on a slow connection.
        """
        parameters = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": str(limit),
            "prop": "extracts|info",
            "exintro": "1",
            "explaintext": "1",
            "inprop": "url",
            "redirects": "1",
        }
        payload = self._fetch(parameters)
        if payload is None:
            return ()
        pages = payload.get("query", {}).get("pages", [])
        if not isinstance(pages, list):
            return ()

        # The API returns pages in arbitrary order; `index` preserves the
        # relevance ranking the search actually produced.
        pages = sorted(pages, key=lambda page: page.get("index", 999))
        return self._passages_from(pages)

    def _search_through_english(self, query: str, limit: int) -> tuple[Passage, ...]:
        """Ask English which articles the query means, then take their twins.

        `langlinks` is the mapping Wikipedia's own editors maintain between
        the same article in different languages, so this is not a translation
        and nothing is guessed: it is the Marathi article an editor said
        corresponds to the English one.
        """
        found = self._fetch(
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": str(limit),
                "prop": "langlinks",
                "lllang": self.edition,
                "lllimit": str(limit),
                "redirects": "1",
            },
            host="en.wikipedia.org",
        )
        if found is None:
            return ()
        pages = found.get("query", {}).get("pages", [])
        if not isinstance(pages, list):
            return ()
        pages = sorted(pages, key=lambda page: page.get("index", 999))

        titles = []
        for page in pages:
            for link in page.get("langlinks") or []:
                title = str(link.get("title") or "").strip()
                if title and title not in titles:
                    titles.append(title)
        if not titles:
            return ()
        return self._extracts_for_titles(titles[:limit])

    def _extracts_for_titles(self, titles: list[str]) -> tuple[Passage, ...]:
        """Fetch intro extracts for named articles in this edition."""
        payload = self._fetch(
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "titles": "|".join(titles),
                "prop": "extracts|info",
                "exintro": "1",
                "explaintext": "1",
                "inprop": "url",
                "redirects": "1",
            }
        )
        if payload is None:
            return ()
        pages = payload.get("query", {}).get("pages", [])
        if not isinstance(pages, list):
            return ()
        # `titles` loses the order asked for, so restore the ranking English
        # gave, which reflects how well each article matched the query.
        position = {title: index for index, title in enumerate(titles)}
        pages.sort(key=lambda page: position.get(str(page.get("title")), 999))
        return self._passages_from(pages)

    def _passages_from(self, pages: list[dict]) -> tuple[Passage, ...]:
        passages: list[Passage] = []
        for page in pages:
            extract = str(page.get("extract") or "").strip()
            url = str(page.get("fullurl") or "").strip()
            title = str(page.get("title") or "").strip()
            if len(extract) < MINIMUM_EXTRACT_CHARACTERS or not url or not title:
                continue
            if "may refer to" in extract[:200].lower():
                continue
            try:
                passages.append(Passage(text=extract, title=title, url=url))
            except ValueError:
                continue
        return tuple(passages)

    def _fetch(self, parameters: dict[str, str], host: str | None = None) -> dict | None:
        """Return decoded JSON, or None for any failure at all.

        Broad by intention. A lesson app on a rural connection must treat a
        DNS failure, a timeout, a captive portal returning HTML and a changed
        API shape identically: no passages, app still running.
        """
        endpoint = f"https://{host}/w/api.php" if host else self.endpoint
        url = f"{endpoint}?{urllib.parse.urlencode(parameters)}"
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with self._open(request, timeout=self.timeout) as response:
                raw = response.read()
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
            return None
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return decoded if isinstance(decoded, dict) else None
