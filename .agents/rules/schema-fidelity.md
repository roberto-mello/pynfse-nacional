# Schema Fidelity

NFSe XSD fixtures MUST mirror the official SEFIN schemas byte-for-byte for every element the library emits. Drift breaks production.

## Sources of truth

- Production XSD: `https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260209.zip`
- Produção restrita XSD: `https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/producao-restrita/nfse-esquemas_xsd-prodrest-v1-01-20260209.zip`
- Manual de Contribuintes (latest v1.2 out2025) for rule context.

When in doubt, download both zips, extract, and grep. Both environments share the same TCRegTrib / TSOpSimpNac / TCRTCInfoIBSCBS definitions unless verified otherwise.

## `tests/fixtures/xsd/_patch_xsd.py`

- The patch script MUST only fix upstream typos (e.g. the `TSSerieDPS` broken regex).
- The patch script MUST NEVER invent new elements, types, enumeration values, or attribute names that do not appear in the official zip.
- The patch script MUST NEVER add children to a complex type (e.g. inserting `regApIBSCBSSN` into `TCRegTrib`).
- The patch script MUST NEVER extend an enumeration (e.g. adding `opSimpNac=4`).
- Adding a new patch requires citing the official XSD line where the typo lives. Anything else goes in code, never in the fixture.

## Code that emits DPS XML

- `xml_builder.py` may emit only elements the official XSD declares. Before adding a new `ET.SubElement(...)` call, grep the official XSD for the element name and parent type.
- `models.py` / `models_ibscbs.py` literals must match the official `TS*` enumeration exactly. A missing value in the official schema is a hard blocker, never a sign that the library should "complete" the spec.
- `regime_mapping.py` must not set fields the official schema does not accept.

## Anti-pattern to refuse

> "Local XSD is stale, so patch it to accept the new element we want to emit."

Wrong. If the official schema rejects the element, the code is wrong. Fix the code, not the fixture. Local fixtures exist to catch drift, not to bless it. Inverting this direction causes the exact failure seen in pynfse-a90: green CI, red production, E1235.

## Tests

- At least one DPS emission test MUST validate the produced XML against the **official** XSD from gov.br.
- A test that requires a schema patch to pass is a test of the patch, not of the code. It cannot prove production will accept the XML.

## When the spec disagrees with the code

1. Verify against both official zips (grep, not memory).
2. If code emits something the zips lack: change the code.
3. If the zips genuinely disagree with each other (prod vs prodrest): gate emission by `ambiente` and document the divergence with the source URLs and zip dates.
4. Record the decision as a bead comment and a knowledge entry. Never silently patch a fixture to make a test pass.
