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
   - [Schemas XSD](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260209.zip) - Esquemas XML
   - [APIs - Produção e Homologação](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao) - Endpoints
   - [Manual de Contribuintes](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/manual-contribuintes-emissor-publico-api-sistema-nacional-nfs-e-v1-2-out2025.pdf) - Guia de integração

2. **Check community implementations** for reference:
   - [PoC NFSe Nacional](https://github.com/nfe/poc-nfse-nacional) - Implementação de referência oficial

3. **Understand the XML structure** by examining the XSD schemas before implementing new elements

4. **Follow existing patterns** in the codebase for consistency (xml_builder.py, models.py)

## Security and Data Handling

- Use synthetic, schema-valid CNPJ, CPF, IM, names, addresses, contacts, NFSe
  access keys, XML, and PDF fixtures. Never commit real taxpayer, patient,
  invoice, or medical data, even when the data came from homologacao.
- Keep live homologacao credentials and any registered issuer CNPJ/IM in the
  git-ignored `.env` or a secret manager. Run live tests only with the explicit
  `--run-homologacao` flag because they call SEFIN and may issue an NFSe.
- Never commit `.pfx`/`.p12` files, private keys, certificate passwords, API
  tokens, local certificate paths, personal email addresses, or generated
  response artifacts. Treat `.beads`/`.lavra` logs, databases, backups, and
  memory files as potentially sensitive local state.
- Before committing, scan the staged diff for secrets and personal data with
  `git diff --cached` and `rg`. A later deletion is not remediation: if
  sensitive data was committed, stop and rewrite every affected branch/tag
  with `git filter-repo`, expire reflogs, prune unreachable objects, and
  rotate any exposed credential.
- Do not push rewritten history without coordinating the force-push and
  checking all remote branches and tags. Assume previously published data may
  already have been copied.

## Release Checklist

Use [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) before cutting a release.
It contains the pre-release checks, tagging steps, and post-release verification
needed to ship a version safely.
<!-- END BEADS INTEGRATION -->
[bd prime] If this output is truncated by your host, read the full persisted hook output before continuing; it may contain project memories and session rules not visible in the preview.

## Beads Workflow Context

### 🚨 SESSION CLOSE PROTOCOL 🚨

**CRITICAL**: Before saying "done" or "complete", you MUST run this checklist:

```
[ ] 1. bd close <id1> <id2> ...   (close completed issues)
[ ] 2. run quality gates        (tests, linters, builds when relevant)
[ ] 3. git status               (check what changed)
[ ] 4. report handoff           (changed files, validation, proposed commit if authorized)
```

### Core Rules
- **Default**: Use beads for ALL task tracking (`bd create`, `bd ready`, `bd close`)
- **Prohibited**: Do NOT use TodoWrite, TaskCreate, or markdown files for task tracking
- **Workflow**: Create beads issue BEFORE writing code, mark in_progress when starting
- **Memory**: Use `bd comments add pynfse-aaa "insight"` for persistent knowledge across sessions. Do NOT use MEMORY.md files. Search with `.lavra/memories/recall.sh "<keywords>"`.
- Persistence you don't need beats lost context
- Profile model: conservative/minimal report handoff; team-maintainer may commit only when explicitly enabled
- Git workflow: conservative by default on ephemeral branches
- Session management: check `bd ready` for available work

### Finding Work
- `bd ready` - Show issues ready to work (no blockers)
- `bd list --status=open` - All open issues
- `bd list --status=in_progress` - Your active work
- `bd show <id>` - Detailed issue view with dependencies

### Creating & Updating
- `bd create --title="Summary of this issue" --description="Why this issue exists and what needs to be done" --type=task|bug|feature --priority=2` - New issue
  - Priority: 0-4 or P0-P4 (0=critical, 2=medium, 4=backlog). NOT "high"/"medium"/"low"
- `bd create ... --parent=<id>` - Hierarchical child (task under epic, subtask under task; inherits parent labels)
- `bd update <id> --claim` - Claim work
- `bd update <id> --assignee=username` - Assign to someone
- `bd update <id> --title/--description/--notes/--design` - Update fields inline
- `bd close <id>` - Mark complete
- `bd close <id1> <id2> ...` - Close multiple issues at once (more efficient)
- `bd close <id> --reason="explanation"` - Close with reason
- **Tip**: When creating multiple issues/tasks/epics, use parallel subagents for efficiency
- **WARNING**: Do NOT use `bd edit` - it opens $EDITOR (vim/nano) which blocks agents

### Dependencies & Blocking
- `bd dep add <issue> <depends-on>` - Add dependency (issue depends on depends-on)
- `bd blocked` - Show all blocked issues
- `bd show <id>` - See what's blocking/blocked by this issue

### Sync & Collaboration
- `bd dolt pull` - Pull beads updates from Dolt remote
- `bd dolt push` - Push beads to Dolt remote
- `bd search <query>` - Search issues by keyword

### Project Health
- `bd stats` - Project statistics (open/closed/blocked counts)
- `bd doctor` - Check for issues (sync problems, missing hooks)
- `bd doctor --check=conventions` - Check for convention drift (lint, stale, orphans)

### Quality Tools
- `bd create --validate` - Check description has required sections
- `bd create --acceptance="criteria"` - Set acceptance criteria (checked by --validate)
- `bd create --design="decisions"` - Record design decisions
- `bd create --notes="context"` - Add supplementary notes

### Lifecycle & Hygiene
- `bd defer <id> --until="date"` - Defer work to a future date
- `bd supersede <id> --with=<new-id>` - Mark issue as superseded
- `bd close <id> --suggest-next` - Show newly unblocked issues after closing
- `bd stale` - Find issues with no recent activity
- `bd orphans` - Find issues with broken dependencies
- `bd preflight` - Pre-PR checks (lint, stale, orphans)
- `bd human <id>` - Flag for human decision (list/respond/dismiss)

## Common Workflows

**Starting work:**
```bash
bd ready           # Find available work
bd show <id>       # Review issue details
bd update <id> --claim  # Claim it
```

**Completing work:**
```bash
bd close <id1> <id2> ...    # Close all completed issues at once
bd dolt pull                # Pull latest beads from main
git status                  # Report changed files and proposed commit; wait for authority
# Merge to main locally only when the active instructions grant that authority
```

**Creating dependent work:**
```bash
# Run bd create commands in parallel (use subagents for many items)
bd create --title="Implement feature X" --description="Why this issue exists and what needs to be done" --type=feature
bd create --title="Write tests for X" --description="Why this issue exists and what needs to be done" --type=task
bd dep add beads-yyy beads-xxx  # Tests depend on Feature (Feature blocks tests)
```
