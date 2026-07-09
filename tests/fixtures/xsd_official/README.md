# Unpatched official NFSe XSD fixture

Source package:

- `https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260209.zip`

## Purpose

This fixture is the **unpatched** official SEFIN schema. It exists to catch
library code that emits elements the official schema does not declare
(e.g. `regApIBSCBSSN`, `opSimpNac=4`, `tpNFSeCredito`, `tpNFSeDebito`,
`finNFSe=1/2`). The patched fixture at `tests/fixtures/xsd/nfse_v1.01/`
accepts those invented elements, which is how the E1235 production rejection
shipped green in 0.9.0. See beads `pynfse-a90` / `pynfse-a90.2`.

## What is patched here

Only the `TSSerieDPS` `xs:pattern` typo. The official XSD ships
`value="^0{0,4}\d{1,5}$"` with literal `^` / `$` anchors. libxml2 treats
those anchors as literal characters, so every plain DPS serie (e.g. `"3"`)
fails local validation even though SEFIN's official validator accepts it.
This is a documented upstream typo (see `.agents/rules/schema-fidelity.md`)
and the only fix permitted on this fixture.

## What is NOT patched here

Everything else. In particular the following are deliberately **absent** from
this fixture, even though the patched fixture adds them, so that this fixture
rejects any library code that emits them:

- `regApIBSCBSSN` element inside `TCRegTrib` (invented; causes E1235).
- `TSOpSimpNac` enumeration value `4` (invented; only 1/2/3 are official).
- `TSRTCTpNFSeCredito` / `TSRTCTpNFSeDebito` simple types and their
  `tpNFSeCredito` / `tpNFSeDebito` elements inside `TCRTCInfoIBSCBS`.
- `TSRTCFinNFSe` enumeration values `1` and `2` (only `0` is official).

Never extend this fixture to accept such XML. Fix the code instead.

## Layout

- Vendored files live under `tests/fixtures/xsd_official/Schemas/`
- Both `1.00` and `1.01` schema folders are kept so relative imports and
  includes resolve exactly like the upstream zip.

## Regeneration

Download the official zip above and run:

```bash
python tests/fixtures/xsd_official/_generate_official_fixture.py \
    <path-to-nfse-esquemas_xsd-v1-01-20260209.zip> \
    tests/fixtures/xsd_official
```

The generator applies only the `TSSerieDPS` typo fix. It MUST NOT invent
elements. Adding any other patch here defeats the purpose of the fixture.