"""Resolve test certificate credentials."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _REPO_ROOT / ".env"


def load_test_env() -> None:
    """Load the repository .env file when present."""

    if _ENV_PATH.exists():
        load_dotenv(_ENV_PATH, override=False)


def cert_path() -> str:
    """Return the configured test certificate path."""

    return os.environ.get("NFSE_TEST_CERT_PATH", "")


def cert_password() -> str:
    """Return the configured test certificate password."""

    password = os.environ.get("NFSE_TEST_CERT_PASSWORD", "")
    if password:
        return password

    try:
        import keyring
    except Exception:
        keyring = None

    if keyring is not None:
        try:
            password = keyring.get_password("pynfse-nacional-tests", "cert-password")
        except Exception:
            password = None

        if password:
            return password

    return ""


load_test_env()
