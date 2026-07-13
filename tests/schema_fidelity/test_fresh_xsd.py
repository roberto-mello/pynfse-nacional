"""Fresh XSD drift tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from pynfse_nacional._canonical import NFSE_XSD_PROD, NFSE_XSD_PRODREST
from tests.schema_fidelity._helpers import (
    SchemaFetchError,
    fetch_bytes,
    local_xsd_files,
    official_xsd_files,
)

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "xsd_official"


@pytest.mark.parametrize(
    "source",
    [NFSE_XSD_PROD, NFSE_XSD_PRODREST],
    ids=lambda source: source.name,
)
def test_fresh_official_xsd_matches_vendored_fixture(source):
    """Fresh official zips must match the vendored XSD fixture."""

    try:
        zip_bytes = fetch_bytes(source.url)
    except SchemaFetchError as exc:
        pytest.skip(f"Network unavailable for {source.name}: {exc}")

    fresh_files = official_xsd_files(zip_bytes)
    fixture_files = local_xsd_files(FIXTURE_ROOT)

    # Exact key-set match: vendored fixture must not silently omit (or invent)
    # XSD files relative to the official zip.
    only_fresh = sorted(fresh_files.keys() - fixture_files.keys())
    only_fixture = sorted(fixture_files.keys() - fresh_files.keys())
    assert fresh_files.keys() == fixture_files.keys(), (
        f"key-set drift: only-in-fresh={only_fresh} only-in-fixture={only_fixture}"
    )

    for relative_path, fixture_bytes in fixture_files.items():
        assert fresh_files[relative_path] == fixture_bytes, relative_path
