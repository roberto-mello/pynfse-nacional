"""Current gov.br XSD URL sentinel."""

from __future__ import annotations

import re

import pytest

from pynfse_nacional._canonical import NFSE_XSD_PROD, NFSE_XSD_PRODREST
from tests.schema_fidelity._helpers import SchemaFetchError, fetch_text

_URL_PATTERN = re.compile(r"https://www\.gov\.br/[^\"']+nfse-esquemas_xsd-[^\"']+\.zip")


@pytest.mark.parametrize(
    "page_url, expected_url",
    [
        (
            "https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual",
            NFSE_XSD_PROD.url,
        ),
        (
            "https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/producao-restrita",
            NFSE_XSD_PRODREST.url,
        ),
    ],
)
def test_documentation_pages_pin_xsd_urls(page_url: str, expected_url: str):
    """Gov.br docs pages must advertise the pinned XSD URL."""

    try:
        html = fetch_text(page_url)
    except SchemaFetchError as exc:
        pytest.skip(f"Network unavailable for {page_url}: {exc}")

    match = _URL_PATTERN.search(html)
    assert match is not None
    assert match.group(0) == expected_url
