"""Unit tests for schema-fidelity download size bounds."""

from __future__ import annotations

import pytest

from tests.schema_fidelity._helpers import SchemaFetchError, fetch_bytes


class _FakeResponse:
    def __init__(self, payload: bytes, content_length: str | None = None) -> None:
        self._payload = payload
        self._offset = 0
        self.headers = {}
        if content_length is not None:
            self.headers["Content-Length"] = content_length

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            chunk = self._payload[self._offset :]
            self._offset = len(self._payload)
            return chunk
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_fetch_bytes_rejects_content_length_over_limit(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(request, timeout=30.0):  # noqa: ANN001
        return _FakeResponse(b"x" * 10, content_length="1000")

    monkeypatch.setattr("tests.schema_fidelity._helpers.urlopen", fake_urlopen)

    with pytest.raises(SchemaFetchError, match="Content-Length"):
        fetch_bytes("https://example.invalid/schema.zip", max_bytes=100)


def test_fetch_bytes_rejects_stream_over_limit(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(request, timeout=30.0):  # noqa: ANN001
        return _FakeResponse(b"y" * 250)

    monkeypatch.setattr("tests.schema_fidelity._helpers.urlopen", fake_urlopen)

    with pytest.raises(SchemaFetchError, match="max_bytes"):
        fetch_bytes("https://example.invalid/schema.zip", max_bytes=100)


def test_fetch_bytes_allows_payload_under_limit(monkeypatch: pytest.MonkeyPatch):
    payload = b"ok-payload"

    def fake_urlopen(request, timeout=30.0):  # noqa: ANN001
        return _FakeResponse(payload, content_length=str(len(payload)))

    monkeypatch.setattr("tests.schema_fidelity._helpers.urlopen", fake_urlopen)

    assert fetch_bytes("https://example.invalid/schema.zip", max_bytes=100) == payload


def test_fetch_bytes_ignores_non_integer_content_length(
    monkeypatch: pytest.MonkeyPatch,
):
    payload = b"small"

    def fake_urlopen(request, timeout=30.0):  # noqa: ANN001
        return _FakeResponse(payload, content_length="not-a-number")

    monkeypatch.setattr("tests.schema_fidelity._helpers.urlopen", fake_urlopen)

    assert fetch_bytes("https://example.invalid/schema.zip", max_bytes=100) == payload
