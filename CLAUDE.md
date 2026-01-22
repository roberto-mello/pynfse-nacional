# pynfse-nacional

Python library for Brazilian NFSe Nacional (Padrao Nacional) API integration.

## Project Overview

This library provides a client for issuing, querying, and canceling electronic service invoices (NFSe) through Brazil's national NFSe system (SEFIN API).

## Tech Stack

- Python 3.10+
- httpx for HTTP requests with mTLS
- lxml for XML handling
- signxml for XML digital signatures
- cryptography for certificate handling
- pydantic for data validation

## Project Structure

```
src/pynfse_nacional/
  client.py       # Main NFSeClient class with mTLS support
  models.py       # Pydantic models (DPS, NFSe, Prestador, Tomador, etc.)
  xml_builder.py  # XML generation for DPS
  xml_signer.py   # XML digital signature service
  constants.py    # API URLs, endpoints, enums
  exceptions.py   # Custom exceptions
  utils.py        # Compression/encoding utilities

tests/
  test_*.py       # pytest tests
```

## Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/pynfse_nacional

# Lint
ruff check src tests

# Format
ruff format src tests
```

## Code Style

- Follow ruff linter rules (E, F, I, N, W)
- Line length: 88 characters
- Use type hints for all function signatures
- Use Pydantic models for data structures
- Add blank line after comments and code blocks
- Add blank line before if, for, while statements
- Portuguese for domain terms (NFSe, DPS, Prestador, Tomador)
- English for code structure (class names, method names, comments)

## Key Concepts

- **DPS**: Declaracao de Prestacao de Servicos (service declaration submitted to generate NFSe)
- **NFSe**: Nota Fiscal de Servicos Eletronica (the actual electronic invoice)
- **Prestador**: Service provider (the company issuing the invoice)
- **Tomador**: Service recipient (the client receiving the invoice)
- **mTLS**: Mutual TLS authentication using PKCS12 certificates (.pfx/.p12)
- **Ambiente**: Environment - homologacao (staging) or producao (production)

## Testing

- Use pytest with pytest-asyncio
- Integration tests require valid certificates (skipped by default)
- Unit tests mock the HTTP client and XML signing
