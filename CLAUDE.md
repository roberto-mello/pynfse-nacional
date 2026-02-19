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
- reportlab + qrcode for PDF generation (optional extra: `pynfse-nacional[pdf]`)

## Project Structure

```
src/pynfse_nacional/
  client.py           # Main NFSeClient class with mTLS support
  models.py           # Pydantic models (DPS, NFSe, Prestador, Tomador, etc.)
  xml_builder.py      # XML generation for DPS
  xml_signer.py       # XML digital signature service
  pdf_generator.py    # PDF rendering for NFSe documents
  constants.py        # API URLs, endpoints, enums
  exceptions.py       # Custom exceptions
  utils.py            # Compression/encoding utilities

tests/
  test_*.py           # pytest tests
```

## Development Commands

This project uses **uv** for package management.

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/pynfse_nacional

# Lint
uv run ruff check src tests

# Format
uv run ruff format src tests

# Add a dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>
```

## Key Concepts

- **DPS**: Declaracao de Prestacao de Servicos (service declaration submitted to generate NFSe)
- **NFSe**: Nota Fiscal de Servicos Eletronica (the actual electronic invoice)
- **Prestador**: Service provider (the company issuing the invoice)
- **Tomador**: Service recipient (the client receiving the invoice)
- **mTLS**: Mutual TLS authentication using PKCS12 certificates (.pfx/.p12)
- **Ambiente**: Environment - homologacao (staging) or producao (production)

## Planning New Features

When planning new features or modifications to the NFSe integration:

1. **Read the official documentation** - The README contains links to official sources:
   - [Portal NFSe Nacional](https://www.gov.br/nfse) - Portal principal
   - [Documentação Técnica](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/) - Biblioteca de documentos
   - [Documentação Atual](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual) - Versão mais recente
   - [Schemas XSD](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260122.zip) - Esquemas XML
   - [APIs - Produção e Homologação](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao) - Endpoints
   - [Manual de Contribuintes](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/manual-contribuintes-emissor-publico-api-sistema-nacional-nfs-e-v1-2-out2025.pdf) - Guia de integração

2. **Check community implementations** for reference:
   - [PoC NFSe Nacional](https://github.com/nfe/poc-nfse-nacional) - Implementação de referência oficial

3. **Understand the XML structure** by examining the XSD schemas before implementing new elements

4. **Follow existing patterns** in the codebase for consistency (xml_builder.py, models.py)
