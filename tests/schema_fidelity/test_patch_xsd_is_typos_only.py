"""Patch-lint for the official XSD fixture."""

from __future__ import annotations

from pathlib import Path

from tests.fixtures.xsd_official._generate_official_fixture import (
    apply_official_typo_fix,
)
from tests.schema_fidelity._helpers import local_xsd_files

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "xsd_official"

_BROKEN_TSSERIEDPS_PATTERN = b'value="^0{0,4}\\d{1,5}$"'
_FIXED_TSSERIEDPS_PATTERN = b'value="0{0,4}\\d{1,5}"'


def _count_markers(data: bytes) -> tuple[int, int, int]:
    text = data.decode("utf-8")
    return (
        text.count('<xs:element name="'),
        text.count('<xs:enumeration value="'),
        text.count('<xs:complexType name="'),
    )


def test_official_fixture_only_changes_the_known_tserie_dps_typo():
    """Typos-only patch may not invent new schema shape.

    Exercises ``apply_official_typo_fix()`` directly (not a reimplemented
    bytes.replace) so drift in the generator is caught by this test.
    """

    files = local_xsd_files(FIXTURE_ROOT)
    changed = 0

    for relative_path, original in files.items():
        # Re-break the known typo so we can re-apply the real patch function.
        broken = original.replace(
            _FIXED_TSSERIEDPS_PATTERN,
            _BROKEN_TSSERIEDPS_PATTERN,
            1,
        )
        patched = apply_official_typo_fix(broken)

        if broken != original:
            changed += 1
            # Only the TSSerieDPS pattern bytes may change.
            assert patched == original, relative_path
            assert broken.count(_BROKEN_TSSERIEDPS_PATTERN) >= 1, relative_path
            assert patched.count(_FIXED_TSSERIEDPS_PATTERN) >= 1, relative_path
        else:
            # Files without the typo must be unchanged by the patch.
            assert patched == broken == original, relative_path

        assert _count_markers(patched) == _count_markers(broken), relative_path

    assert changed >= 1, "expected at least one file with the TSSerieDPS typo"
