import requests

from acquisition import FallbackSource, StatefulHttpFetcher


class DummyResponse:
    def __init__(self, status_code=200, text="", headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


class DummySession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, headers=None, timeout=None):
        self.calls.append((url, headers or {}, timeout))
        return self.responses.pop(0)


def test_stateful_fetcher_hashes_content_without_backend():
    session = DummySession([DummyResponse(200, "hello")])
    fetcher = StatefulHttpFetcher(
        source_name="Test",
        session=session,
        timeout=3,
    )
    result = fetcher.fetch("https://example.com")
    assert result.changed
    assert result.content_hash
    assert result.status_code == 200


def test_fallback_source_moves_to_next_adapter():
    class Broken:
        def fetch(self):
            raise RuntimeError("blocked")

    class Working:
        def fetch(self):
            yield "ok"

    source = FallbackSource(
        "test",
        [("html", Broken()), ("search", Working())],
    )
    assert list(source.fetch()) == ["ok"]
    assert source.active_strategy == "search"
