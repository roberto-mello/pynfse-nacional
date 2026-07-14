#!/usr/bin/env python3
"""Build the versioned documentation site used by GitHub Pages."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PROJECT_PATH = "/pynfse-nacional"
VERSIONING_FILES = (
    Path("docs/conf.py"),
    Path("docs/_templates/version-switcher.html"),
    Path("docs/_static/version-switcher.css"),
)
RELEASE_TAG_PATTERN = re.compile(
    r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)


@dataclass(frozen=True, order=True)
class ReleaseTag:
    """A validated stable release tag and its semantic version."""

    version: tuple[int, int, int]
    tag: str

    @property
    def label(self) -> str:
        """Return the public version label without the ``v`` prefix."""

        return self.tag[1:]


def parse_release_tag(tag: str) -> ReleaseTag | None:
    """Parse a stable release tag, rejecting prereleases and other tags."""

    match = RELEASE_TAG_PATTERN.fullmatch(tag)
    if not match:
        return None
    version = tuple(int(part) for part in match.groups())
    return ReleaseTag(version=version, tag=tag)


def select_release_tags(tags: Iterable[str], *, limit: int = 5) -> list[ReleaseTag]:
    """Return the newest stable tags in descending semantic-version order."""

    if limit < 1:
        raise ValueError("release limit must be at least 1")

    releases = {
        release.tag: release
        for tag in tags
        if (release := parse_release_tag(tag)) is not None
    }
    return sorted(releases.values(), reverse=True)[:limit]


def public_path(suffix: str, *, project_path: str = PROJECT_PATH) -> str:
    """Return a site-root-relative URL for a published channel."""

    return f"{project_path.rstrip('/')}/{suffix.strip('/')}/"


def build_manifest(
    releases: Iterable[ReleaseTag], *, project_path: str = PROJECT_PATH
) -> list[dict[str, str]]:
    """Build the navigation manifest shared by every rendered version."""

    release_list = list(releases)
    return [
        {"label": "latest", "url": public_path("latest", project_path=project_path)},
        *(
            {
                "label": release.label,
                "url": public_path(release.label, project_path=project_path),
            }
            for release in release_list
        ),
        {
            "label": "development",
            "url": public_path("development", project_path=project_path),
        },
    ]


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    """Run a command and stream its output."""

    subprocess.run(command, cwd=cwd, env=env, check=True)


def git_output(repo: Path, *args: str) -> str:
    """Run Git and return trimmed stdout."""

    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def discover_release_tags(repo: Path) -> list[ReleaseTag]:
    """Return the newest annotated stable tags available in ``repo``."""

    tags = git_output(
        repo,
        "for-each-ref",
        "--format=%(refname:short)",
        "refs/tags",
    ).splitlines()
    annotated_tags = [
        tag
        for tag in tags
        if parse_release_tag(tag) and git_output(repo, "cat-file", "-t", tag) == "tag"
    ]
    return select_release_tags(annotated_tags)


def build_environment(
    manifest: list[dict[str, str]],
    *,
    channel: str,
    current_path: str,
    current_label: str,
    version: str | None = None,
) -> dict[str, str]:
    """Build the environment consumed by ``docs/conf.py``."""

    environment = {
        "DOCS_CHANNEL": channel,
        "DOCS_CURRENT_LABEL": current_label,
        "DOCS_CURRENT_PATH": current_path,
        "DOCS_VERSIONS_JSON": json.dumps(manifest, separators=(",", ":")),
    }
    if version is not None:
        environment["DOCS_VERSION"] = version
    return environment


def build_ref(
    repo: Path,
    ref: str,
    output: Path,
    *,
    environment: dict[str, str],
    worktree_root: Path,
    versioning_source: Path,
) -> None:
    """Build one Git ref from an isolated archive and lockfile."""

    checkout = worktree_root / re.sub(r"[^A-Za-z0-9_.-]+", "-", ref)
    checkout.mkdir(parents=True)
    archive_path = worktree_root / f"{checkout.name}.tar"
    with archive_path.open("wb") as archive_file:
        subprocess.run(
            ["git", "archive", ref],
            cwd=repo,
            check=True,
            stdout=archive_file,
        )
    with tarfile.open(archive_path) as archive:
        archive.extractall(checkout)
    try:
        for relative_path in VERSIONING_FILES:
            destination = checkout / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(versioning_source / relative_path, destination)
        run(["uv", "sync", "--group", "docs", "--frozen"], cwd=checkout)
        run(
            [
                "uv",
                "run",
                "--no-sync",
                "sphinx-build",
                "-b",
                "html",
                "-W",
                "--keep-going",
                "docs",
                str(output),
            ],
            cwd=checkout,
            env={**os.environ, **environment},
        )
    finally:
        shutil.rmtree(checkout, ignore_errors=True)
        archive_path.unlink(missing_ok=True)


def copy_build(source: Path, destination: Path) -> None:
    """Copy a rendered site directory into the assembled artifact."""

    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)


def resolve_ref(repo: Path, ref: str) -> str:
    """Resolve a requested ref, falling back to the remote master ref."""

    try:
        git_output(repo, "rev-parse", "--verify", ref)
    except subprocess.CalledProcessError:
        if ref != "master":
            raise
        fallback = "origin/master"
        git_output(repo, "rev-parse", "--verify", fallback)
        return fallback
    return ref


def build_site(
    repo: Path,
    output: Path,
    *,
    development_ref: str = "master",
    release_limit: int = 5,
) -> list[ReleaseTag]:
    """Assemble stable, latest, root, and development documentation."""

    releases = discover_release_tags(repo)
    if not releases:
        raise RuntimeError("no annotated vMAJOR.MINOR.PATCH release tags found")
    if release_limit != 5:
        releases = releases[:release_limit]

    manifest = build_manifest(releases)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="pynfse-docs-") as temp_dir:
        build_root = Path(temp_dir)
        worktree_root = build_root / "worktrees"
        worktree_root.mkdir()

        for release in releases:
            rendered = build_root / release.label
            build_ref(
                repo,
                release.tag,
                rendered,
                environment=build_environment(
                    manifest,
                    channel="release",
                    current_path=release.label,
                    current_label=release.label,
                    version=release.label,
                ),
                worktree_root=worktree_root,
                versioning_source=repo,
            )
            copy_build(rendered, output / release.label)

        latest = releases[0]
        latest_rendered = build_root / "latest"
        build_ref(
            repo,
            latest.tag,
            latest_rendered,
            environment=build_environment(
                manifest,
                channel="latest",
                current_path="latest",
                current_label="latest",
                version=latest.label,
            ),
            worktree_root=worktree_root,
            versioning_source=repo,
        )
        copy_build(latest_rendered, output / "latest")
        copy_build(latest_rendered, output)

        development_rendered = build_root / "development"
        build_ref(
            repo,
            resolve_ref(repo, development_ref),
            development_rendered,
            environment=build_environment(
                manifest,
                channel="development",
                current_path="development",
                current_label="development",
            ),
            worktree_root=worktree_root,
            versioning_source=repo,
        )
        copy_build(development_rendered, output / "development")

    return releases


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Git repository containing release tags (default: current directory)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("site"),
        help="Assembled site directory (default: site)",
    )
    parser.add_argument(
        "--development-ref",
        default="master",
        help="Git ref used for development docs (default: master)",
    )
    parser.add_argument(
        "--release-limit",
        type=int,
        default=5,
        help="Maximum stable releases to publish (default: 5)",
    )
    return parser.parse_args()


def main() -> int:
    """Build and assemble the versioned documentation site."""

    args = parse_args()
    releases = build_site(
        args.repo.resolve(),
        args.output.resolve(),
        development_ref=args.development_ref,
        release_limit=args.release_limit,
    )
    print("Published releases:", ", ".join(release.label for release in releases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
