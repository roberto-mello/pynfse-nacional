"""Regenerate vendored NFSe XSD fixtures from the official gov.br zip."""

from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path

_BROKEN_TSSERIEDPS_PATTERN = 'value="^0{0,4}\\d{1,5}$"'
_FIXED_TSSERIEDPS_PATTERN = 'value="0{0,4}\\d{1,5}"'


def patch_xsd_text(text: str) -> str:
    return text.replace(_BROKEN_TSSERIEDPS_PATTERN, _FIXED_TSSERIEDPS_PATTERN)


def extract_and_patch(zip_path: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(tmp_dir)

        extracted_root = Path(tmp_dir)
        for source_path in extracted_root.rglob("*.xsd"):
            relative_path = source_path.relative_to(extracted_root)
            target_path = target_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(
                patch_xsd_text(source_path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Patch the official NFSe XSD zip for local libxml2 validation."
    )
    parser.add_argument("zip_path", type=Path, help="Path to the official XSD zip")
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Directory where vendored XSD files should be written",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    extract_and_patch(args.zip_path, args.target_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
