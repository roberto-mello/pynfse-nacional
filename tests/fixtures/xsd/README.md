# Vendored NFSe XSD fixtures

Source package:
- `https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260209.zip`

Why patch:
- `tiposSimples_v1.01.xsd` ships `TSSerieDPS` with literal `^` and `$` inside the
  `xs:pattern` value.
- libxml2 treats those anchors as literal characters, so plain DPS series values
  like `3` fail local validation even though the official SEFIN validator accepts
  them.
- The vendored `TCRegTrib` / `TSOpSimpNac` tree predates the IBSCBS Simples
  additions used by this library, so local validation also needs
  `regApIBSCBSSN` plus `opSimpNac=4`.
- The vendored `TCRTCInfoIBSCBS` / `TSRTCFinNFSe` tree also predates the
  crédito/débito adjustment fields, so local validation must add
  `finNFSe=1/2` plus `tpNFSeCredito` / `tpNFSeDebito`.

Layout:
- Vendored files live under `tests/fixtures/xsd/nfse_v1.01/Schemas/`
- Both `1.00` and `1.01` schema folders are kept so relative imports and includes
  resolve exactly like the upstream zip

Regeneration:
- Download the official zip above.
- Run `python tests/fixtures/xsd/_patch_xsd.py <zip-path> tests/fixtures/xsd/nfse_v1.01`

The patch script strips the broken `^` / `$` anchors from `TSSerieDPS`, adds the
`opSimpNac=4` enumeration, inserts `regApIBSCBSSN` into `TCRegTrib`, and extends
the IBSCBS adjustment schema with `finNFSe=1/2` and companion
`tpNFSeCredito` / `tpNFSeDebito` elements so the vendored schema matches the
IBSCBS paths covered by local tests.
