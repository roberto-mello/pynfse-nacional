"""Pinned-source checksum tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from pynfse_nacional._canonical import CANONICAL_SOURCES
from tests.schema_fidelity._helpers import SchemaFetchError, fetch_bytes, sha256_hex


@pytest.mark.parametrize("source", CANONICAL_SOURCES, ids=lambda source: source.name)
def test_canonical_source_sha256(source):
    """Downloaded canonical sources must match the pinned checksum."""

    try:
        data = fetch_bytes(source.url)
    except SchemaFetchError as exc:
        pytest.skip(f"Network unavailable for {source.name}: {exc}")

    assert sha256_hex(data) == source.sha256

    if source.fixture_path is None:
        return

    fixture_path = Path(source.fixture_path)
    assert fixture_path.exists()
    assert sha256_hex(fixture_path.read_bytes()) == source.sha256
