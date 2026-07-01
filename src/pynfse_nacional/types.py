"""Shared type aliases for NFSe Nacional models."""

from decimal import Decimal
from typing import Annotated

from pydantic import Field

Percent2V2 = Annotated[
    Decimal,
    Field(
        ge=Decimal("0"),
        le=Decimal("99.99"),
        max_digits=4,
        decimal_places=2,
        allow_inf_nan=False,
    ),
]

Money15V2 = Annotated[
    Decimal,
    Field(
        ge=Decimal("0"),
        le=Decimal("999999999999999.99"),
        max_digits=17,
        decimal_places=2,
        allow_inf_nan=False,
    ),
]

Percent3V2 = Annotated[
    Decimal,
    Field(
        ge=Decimal("0"),
        le=Decimal("999.99"),
        max_digits=5,
        decimal_places=2,
        allow_inf_nan=False,
    ),
]

