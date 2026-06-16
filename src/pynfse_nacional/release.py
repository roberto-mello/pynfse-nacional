"""Release helper for building and publishing with uv."""

from __future__ import annotations

import argparse
import configparser
import os
import shutil
import subprocess
from pathlib import Path

REPOSITORIES = {
    "pypi": {
        "publish_url": "https://upload.pypi.org/legacy/",
        "check_url": "https://pypi.org/simple",
    },
    "testpypi": {
        "publish_url": "https://test.pypi.org/legacy/",
        "check_url": "https://test.pypi.org/simple",
    },
}


def project_root() -> Path:
    """Return the repository root."""

    return Path(__file__).resolve().parents[2]


def pypirc_path() -> Path:
    """Return the default PyPI config file path."""

    return Path.home() / ".pypirc"


def load_pypi_token(repository: str) -> str | None:
    """Load a PyPI token from environment variables or ~/.pypirc."""

    env_token = os.environ.get("UV_PUBLISH_TOKEN")
    if env_token:
        return env_token

    path = pypirc_path()
    if not path.exists():
        return None

    parser = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
    parser.read(path)

    repo_config = REPOSITORIES[repository]
    candidates = [repository]
    for section in parser.sections():
        if section not in candidates:
            configured_url = parser.get(section, "repository", fallback="")
            if configured_url == repo_config["publish_url"]:
                candidates.append(section)

    for section in candidates:
        if not parser.has_section(section):
            continue
        username = parser.get(section, "username", fallback="")
        password = parser.get(section, "password", fallback="")
        if username == "__token__" and password:
            return password
    return None


def clean_dist(dist_dir: Path) -> None:
    """Remove stale build artifacts while preserving the directory marker."""

    dist_dir.mkdir(parents=True, exist_ok=True)
    for entry in dist_dir.iterdir():
        if entry.name == ".gitignore":
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def build_command(dist_dir: Path) -> list[str]:
    """Return the uv build command."""

    return [
        "uv",
        "build",
        "--sdist",
        "--wheel",
        "--out-dir",
        str(dist_dir),
    ]


def publish_command(
    dist_dir: Path,
    repository: str,
    *,
    dry_run: bool,
    token: str | None,
) -> list[str]:
    """Return the uv publish command."""

    repo_config = REPOSITORIES[repository]
    command = [
        "uv",
        "publish",
        str(dist_dir / "*"),
        "--publish-url",
        repo_config["publish_url"],
        "--check-url",
        repo_config["check_url"],
    ]
    if token:
        command.extend(["--token", token])
    if dry_run:
        command.append("--dry-run")
    return command


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse release command arguments."""

    parser = argparse.ArgumentParser(
        prog="release",
        description="Build and publish a release with uv.",
    )
    parser.add_argument(
        "--repository",
        choices=tuple(REPOSITORIES),
        default="pypi",
        help="Destination repository (default: pypi).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and validate without uploading.",
    )
    parser.add_argument(
        "--keep-dist",
        action="store_true",
        help="Preserve existing dist/ artifacts before building.",
    )
    return parser.parse_args(argv)


def run(command: list[str], *, cwd: Path) -> None:
    """Run a release command and stream output to the terminal."""

    subprocess.run(command, cwd=cwd, check=True)


def main(argv: list[str] | None = None) -> int:
    """Build distributions and publish them with uv."""

    args = parse_args(argv)
    root = project_root()
    dist_dir = root / "dist"
    token = load_pypi_token(args.repository)

    if not args.keep_dist:
        clean_dist(dist_dir)
    else:
        dist_dir.mkdir(parents=True, exist_ok=True)

    run(build_command(dist_dir), cwd=root)
    if not token:
        raise SystemExit(
            f"No token found for {args.repository}. Set UV_PUBLISH_TOKEN or add "
            f"[{args.repository}] username = __token__ and password = <token> to "
            f"{pypirc_path()}."
        )

    run(
        publish_command(
            dist_dir,
            args.repository,
            dry_run=args.dry_run,
            token=token,
        ),
        cwd=root,
    )
    return 0
