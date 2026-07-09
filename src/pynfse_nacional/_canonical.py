"""Pinned canonical sources for schema-fidelity checks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanonicalSource:
    """A gov.br source tracked by drift-detection tests."""

    name: str
    url: str
    sha256: str
    fixture_path: str | None = None


NFSE_XSD_PROD = CanonicalSource(
    name="xsd_production",
    url=(
        "https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/"
        "documentacao-atual/nfse-esquemas_xsd-v1-01-20260209.zip"
    ),
    sha256="e7935cbd9470527c6cc32984c1b2263e614183bf0139ce2733eaaed2de9a8072",
)

NFSE_XSD_PRODREST = CanonicalSource(
    name="xsd_prodrest",
    url=(
        "https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/"
        "producao-restrita/nfse-esquemas_xsd-prodrest-v1-01-20260209.zip"
    ),
    sha256="6a4962d9be644719a914764a901c58ce3f938f016150ce682a7a08fe3ad32bc8",
)

ANEXO_A = CanonicalSource(
    name="anexo_a",
    url=(
        "https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/"
        "documentacao-atual/anexo_a-municipio_ibge-paises_iso2-v1-00-"
        "snnfse-20251210.xlsx"
    ),
    sha256="238b715ab2dcc2c9e0857c44d69048e0af806b45ec8499568342de4a37f4419d",
    fixture_path=(
        "tests/fixtures/annexes/"
        "anexo_a-municipio_ibge-paises_iso2-v1-00-snnfse-20251210.xlsx"
    ),
)

ANEXO_B = CanonicalSource(
    name="anexo_b",
    url=(
        "https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/"
        "documentacao-atual/anexo_b-nbs2-lista_servico_nacional-snnfse-v1-01-"
        "20260122.xlsx"
    ),
    sha256="e74b0be8ad204e458932efb1716225a3fb5703a84e5475ce5c4c6789d1c61b1a",
    fixture_path=(
        "tests/fixtures/annexes/"
        "anexo_b-nbs2-lista_servico_nacional-snnfse-v1-01-20260122.xlsx"
    ),
)

ANEXO_C = CanonicalSource(
    name="anexo_c",
    url=(
        "https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/"
        "documentacao-atual/anexo_c-indop_ibscbs-snnfse-v1-01-20260122.xlsx"
    ),
    sha256="0f34500df82637d83cd05d76eb939cbc2a18651c9740f303fa36c48c57cb34bd",
    fixture_path=(
        "tests/fixtures/annexes/"
        "anexo_c-indop_ibscbs-snnfse-v1-01-20260122.xlsx"
    ),
)

MANUAL_CONTRIBUINTES = CanonicalSource(
    name="manual_contribuintes",
    url=(
        "https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/"
        "documentacao-atual/manual-contribuintes-emissor-publico-api-sistema-"
        "nacional-nfs-e-v1-2-out2025.pdf"
    ),
    sha256="ac2f36e34ff565cc36d67c5d67415c33cc09f27b2dea006e8da9bcd2ddce5581",
)

CANONICAL_SOURCES = (
    NFSE_XSD_PROD,
    NFSE_XSD_PRODREST,
    ANEXO_A,
    ANEXO_B,
    ANEXO_C,
    MANUAL_CONTRIBUINTES,
)
