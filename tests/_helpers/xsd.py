"""Helpers for loading the official vendored NFSe XSD fixtures."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from lxml import etree

FIXTURES_ROOT = Path(__file__).resolve().parents[1] / "fixtures"
XSD_ROOT = FIXTURES_ROOT / "xsd_official" / "Schemas" / "1.01"
SAMPLES_ROOT = FIXTURES_ROOT / "samples"


@lru_cache(maxsize=None)
def load_schema(schema_filename: str) -> etree.XMLSchema:
    """Load and cache one vendored NFSe XMLSchema instance."""

    schema_path = XSD_ROOT / schema_filename
    return etree.XMLSchema(etree.parse(str(schema_path)))


def load_dps_schema() -> etree.XMLSchema:
    return load_schema("DPS_v1.01.xsd")


def load_nfse_schema() -> etree.XMLSchema:
    return load_schema("NFSe_v1.01.xsd")


def sample_path(filename: str) -> Path:
    return SAMPLES_ROOT / filename
