"""Helpers for schema-fidelity tests."""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from tests.fixtures.xsd_official._generate_official_fixture import (
    apply_official_typo_fix,
)


class SchemaFetchError(RuntimeError):
    """Raised when a network fetch cannot be completed."""


def fetch_bytes(url: str, timeout: float = 30.0) -> bytes:
    """Fetch URL bytes or raise ``NetworkUnavailable``."""

    request = Request(
        url,
        headers={"User-Agent": "pynfse-nacional-schema-fidelity"},
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SchemaFetchError(str(exc)) from exc


def fetch_text(url: str, timeout: float = 30.0) -> str:
    """Fetch UTF-8 text from URL or raise ``NetworkUnavailable``."""

    return fetch_bytes(url, timeout=timeout).decode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Return the SHA-256 hex digest for bytes."""

    return hashlib.sha256(data).hexdigest()


def local_xsd_files(root: Path) -> dict[str, bytes]:
    """Return vendored XSD bytes keyed by relative path."""

    files: dict[str, bytes] = {}
    for path in sorted(root.rglob("*.xsd")):
        files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def official_xsd_files(zip_bytes: bytes) -> dict[str, bytes]:
    """Return patched official XSD bytes keyed by archive path."""

    files: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        for member in archive.namelist():
            if not member.endswith(".xsd") or member.endswith("/"):
                continue

            files[member] = apply_official_typo_fix(archive.read(member))

    return files
