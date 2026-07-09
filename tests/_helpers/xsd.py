"""Helpers for loading vendored NFSe XSD fixtures."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from lxml import etree

FIXTURES_ROOT = Path(__file__).resolve().parents[1] / "fixtures"
XSD_ROOT = FIXTURES_ROOT / "xsd" / "nfse_v1.01" / "Schemas" / "1.01"
# Unpatched official SEFIN schema (only the TSSerieDPS libxml2 typo is fixed).
# See tests/fixtures/xsd_official/README.md.
OFFICIAL_XSD_ROOT = FIXTURES_ROOT / "xsd_official" / "Schemas" / "1.01"
SAMPLES_ROOT = FIXTURES_ROOT / "samples"


@lru_cache(maxsize=None)
def load_schema(
    schema_filename: str, root: Path | None = None
) -> etree.XMLSchema:
    """Load and cache one vendored NFSe XMLSchema instance."""

    schema_path = (root or XSD_ROOT) / schema_filename
    return etree.XMLSchema(etree.parse(str(schema_path)))


def load_dps_schema() -> etree.XMLSchema:
    return load_schema("DPS_v1.01.xsd")


def load_nfse_schema() -> etree.XMLSchema:
    return load_schema("NFSe_v1.01.xsd")


def load_official_dps_schema() -> etree.XMLSchema:
    """Load the unpatched official DPS schema from ``xsd_official``.

    Unlike ``load_dps_schema`` this fixture is NOT mutated to accept
    library-invented elements, so it rejects DPS XML that the official SEFIN
    validator would also reject (e.g. E1235 from ``regApIBSCBSSN``).
    """

    return load_schema("DPS_v1.01.xsd", root=OFFICIAL_XSD_ROOT)


def sample_path(filename: str) -> Path:
    return SAMPLES_ROOT / filename
