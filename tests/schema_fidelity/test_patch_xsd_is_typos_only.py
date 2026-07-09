"""Patch-lint for the official XSD fixture."""

from __future__ import annotations

from pathlib import Path

from tests.schema_fidelity._helpers import local_xsd_files

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "xsd_official"


def _count_markers(data: bytes) -> tuple[int, int, int]:
    text = data.decode("utf-8")
    return (
        text.count('<xs:element name="'),
        text.count('<xs:enumeration value="'),
        text.count('<xs:complexType name="'),
    )


def test_official_fixture_only_changes_the_known_tserie_dps_typo():
    """Typos-only patch may not invent new schema shape."""

    files = local_xsd_files(FIXTURE_ROOT)
    changed = 0
    broken_pattern = b'value="^0{0,4}\\d{1,5}$"'
    fixed_pattern = b'value="0{0,4}\\d{1,5}"'

    for relative_path, original in files.items():
        broken = original.replace(fixed_pattern, broken_pattern, 1)
        patched = broken.replace(broken_pattern, fixed_pattern)
        if broken != original:
            changed += 1

        assert _count_markers(patched) == _count_markers(broken), relative_path
        assert patched == original, relative_path

    assert changed >= 1
