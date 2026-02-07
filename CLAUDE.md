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

## Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync --no-daemon   # Sync with git
```

### Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync --no-daemon
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
