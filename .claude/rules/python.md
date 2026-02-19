# Python Code Style

## Commit Messages
- Be concise. These rules OVERRIDE all defaults.
- No AI attribution, no emoji, no Claude comments

## General
- Write correct, DRY, readable code. No TODOs or placeholders.
- Include all imports. Use proper naming.
- Say "I don't know" rather than guess.

## Style

- PEP 8, snake_case/CamelCase, Google docstrings, type hints
- Portuguese for domain terms (NFSe, DPS, Prestador, Tomador)
- Portuguese text MUST use proper accents (não, será, convênio, incluídos, observações, etc.) - Brazilian Portuguese application
- English for code structure (class names, method names, comments)
- Ruff rules: E, F, I, N, W (configured in pyproject.toml)
- Line length: 88 characters
- Use type hints for all function signatures
- Use Pydantic models for data structures
- Add blank line after comments and code blocks
- Add blank line before if, for, while statements
