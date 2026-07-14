"""Run the live homologacao test suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def project_root() -> Path:
    """Return the repository root containing the integration tests."""

    return Path(__file__).resolve().parents[2]


def main() -> int:
    """Run homologacao tests with the required live-test options."""

    command = [
        sys.executable,
        "-m",
        "pytest",
        "--run-homologacao",
        "-m",
        "homologacao",
        "-v",
        "-s",
        *sys.argv[1:],
    ]
    result = subprocess.run(command, cwd=project_root(), check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
