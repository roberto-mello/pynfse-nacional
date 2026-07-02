# Vendored NFSe XSD fixtures

Source package:
- `https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260209.zip`

Why patch:
- `tiposSimples_v1.01.xsd` ships `TSSerieDPS` with literal `^` and `$` inside the
  `xs:pattern` value.
- libxml2 treats those anchors as literal characters, so plain DPS series values
  like `3` fail local validation even though the official SEFIN validator accepts
  them.

Layout:
- Vendored files live under `tests/fixtures/xsd/nfse_v1.01/Schemas/`
- Both `1.00` and `1.01` schema folders are kept so relative imports and includes
  resolve exactly like the upstream zip

Regeneration:
- Download the official zip above.
- Run `python tests/fixtures/xsd/_patch_xsd.py <zip-path> tests/fixtures/xsd/nfse_v1.01`

The patch script strips only the broken `^` / `$` anchors from `TSSerieDPS` and
leaves the rest of the schema tree unchanged.
