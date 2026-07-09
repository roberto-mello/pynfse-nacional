"""Regenerate the unpatched official NFSe XSD fixture from the gov.br zip.

Unlike ``tests/fixtures/xsd/_patch_xsd.py``, this script MUST NOT invent
elements, enumeration values, or attributes. It applies only the single
upstream typo fix that libxml2 cannot parse: the broken ``^`` / ``$``
anchors inside ``TSSerieDPS`` (see ``.agents/rules/schema-fidelity.md``).

Every other divergence between the official schema and the library's emitted
XML is a real schema violation that this fixture exists to catch. Do not
"fix" the fixture to accept such XML here. Fix the code instead.

Regeneration:

    python tests/fixtures/xsd_official/_generate_official_fixture.py \\
        <path-to-nfse-esquemas_xsd-v1-01-20260209.zip> \\
        tests/fixtures/xsd_official

Source zip:

- https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260209.zip
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
import zipfile
from pathlib import Path

# Official XSD ships TSSerieDPS with literal ^ and $ inside the xs:pattern.
# libxml2 treats those anchors as literal characters, so any plain DPS serie
# (e.g. "3") fails local validation even though SEFIN's official validator
# accepts it. This is a documented upstream typo, not an invented element.
_BROKEN_TSSERIEDPS_PATTERN = b'value="^0{0,4}\\d{1,5}$"'
_FIXED_TSSERIEDPS_PATTERN = b'value="0{0,4}\\d{1,5}"'


def apply_official_typo_fix(data: bytes) -> bytes:
    """Apply only the TSSerieDPS typo fix. Nothing else.

    Operates on raw bytes so the vendored files keep their original line
    endings (the upstream zip uses CRLF) -- only the typo substitution
    changes byte content, keeping regeneration diffs minimal. Returns the
    input unchanged when the broken pattern is absent (e.g. for XSD files
    that do not declare TSSerieDPS). ``extract_and_fix`` asserts the patch
    hit at least one file across the whole zip -- that catches upstream
    drift loudly without false-firing on unrelated XSDs.
    """

    return data.replace(_BROKEN_TSSERIEDPS_PATTERN, _FIXED_TSSERIEDPS_PATTERN)


def _assert_safe_members(archive: zipfile.ZipFile, base_dir: Path) -> None:
    """Reject zip members that escape base_dir (path traversal guard)."""

    for member in archive.namelist():
        resolved = (base_dir / member).resolve()
        try:
            resolved.relative_to(base_dir.resolve())
        except ValueError as exc:
            raise ValueError(
                f"Refusing to extract unsafe zip member: {member!r}"
            ) from exc


def extract_and_fix(zip_path: Path, target_dir: Path) -> None:
    # Clear any prior extraction under target_dir so a renamed/dropped XSD
    # in a future zip cannot leave stale files behind. The generator script
    # and README at the target root are preserved.
    target_dir.mkdir(parents=True, exist_ok=True)

    for child in target_dir.iterdir():
        if child.name in {"Schemas", "Componente_Schemas", "Componente_recepcao"}:
            shutil.rmtree(child)

    patched_hits = 0
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with zipfile.ZipFile(zip_path) as archive:
            _assert_safe_members(archive, tmp_path)
            archive.extractall(tmp_dir)

        extracted_root = tmp_path
        for source_path in extracted_root.rglob("*.xsd"):
            data = source_path.read_bytes()
            patched = apply_official_typo_fix(data)
            if patched != data:
                patched_hits += 1

            relative_path = source_path.relative_to(extracted_root)
            target_path = target_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(patched)

    if patched_hits == 0:
        raise ValueError(
            "TSSerieDPS typo pattern not found in any XSD -- the upstream zip "
            "changed. Verify the new zip and update _BROKEN_TSSERIEDPS_PATTERN "
            "(or confirm the typo was fixed upstream)."
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract the official NFSe XSD zip and apply only the TSSerieDPS "
            "libxml2 typo fix. Invented elements are deliberately NOT patched."
        )
    )
    parser.add_argument("zip_path", type=Path, help="Path to the official XSD zip")
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Directory where unpatched official XSD files should be written",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    extract_and_fix(args.zip_path, args.target_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
