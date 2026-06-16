"""Metadata tests for package version alignment."""

import re
from pathlib import Path

from pynfse_nacional import __version__


def test_package_version_matches_pyproject():
    """The runtime version should match the project metadata version."""
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)

    assert match is not None
    assert __version__ == match.group(1)
