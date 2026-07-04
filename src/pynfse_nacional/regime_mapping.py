"""Canonical Simples Nacional regime mapping."""

from __future__ import annotations

from typing import Final

RegimeMapping = dict[str, dict[str, str | None]]

REGIME_TO_SIMPLES_NACIONAL: Final[RegimeMapping] = {
    "normal": {
        "opSimpNac": "1",
        "regApTribSn": None,
        "regApIbsCbsSn": None,
    },
    "mei": {
        "opSimpNac": "2",
        "regApTribSn": None,
        "regApIbsCbsSn": None,
    },
    "simples_nacional": {
        "opSimpNac": "3",
        "regApTribSn": "1",
        "regApIbsCbsSn": "1",
    },
    "simples_excesso": {
        "opSimpNac": "3",
        "regApTribSn": "2",
        "regApIbsCbsSn": "2",
    },
}
