"""Tests for versioned documentation selection and artifact assembly."""

import json
import runpy
from pathlib import Path

import pytest

from util import build_versioned_docs


def test_docs_conf_reads_project_and_docs_metadata(monkeypatch):
    for name in (
        "DOCS_SITE_URL",
        "DOCS_PROJECT_PATH",
        "DOCS_CHANNEL",
        "DOCS_VERSION",
        "DOCS_CURRENT_PATH",
        "DOCS_CURRENT_LABEL",
        "DOCS_VERSIONS_JSON",
    ):
        monkeypatch.delenv(name, raising=False)

    config = runpy.run_path("docs/conf.py")

    assert config["project"] == "pynfse-nacional"
    assert config["author"] == "Project Maintainer"
    assert config["copyright"] == "2026, Project Maintainer"
    assert config["DOCS_SITE_URL"] == "https://roberto-mello.github.io"
    assert config["DOCS_PROJECT_PATH"] == "/pynfse-nacional"
    assert config["DOCS_VERSION"] == "0.9.5"
    assert config["docs_changelog_url"] == "/pynfse-nacional/appendix/changelog.html"


def test_docs_conf_environment_overrides_metadata(monkeypatch):
    monkeypatch.setenv("DOCS_SITE_URL", "https://docs.example.test")
    monkeypatch.setenv("DOCS_PROJECT_PATH", "/project-docs")
    monkeypatch.setenv("DOCS_VERSION", "9.9.9")
    monkeypatch.setenv("DOCS_CURRENT_PATH", "9.9.9")

    config = runpy.run_path("docs/conf.py")

    assert config["DOCS_SITE_URL"] == "https://docs.example.test"
    assert config["DOCS_PROJECT_PATH"] == "/project-docs"
    assert config["DOCS_VERSION"] == "9.9.9"
    assert config["docs_changelog_url"] == "/project-docs/9.9.9/appendix/changelog.html"


def test_docs_conf_supports_historical_pyproject_without_docs_metadata(
    tmp_path, monkeypatch
):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "historical-project"
version = "0.1.0"
authors = [{name = "Historical Maintainer"}]

[project.urls]
Documentation = "https://docs.example.test/historical-project/"
""".lstrip(),
        encoding="utf-8",
    )
    conf_path = docs_dir / "conf.py"
    conf_path.write_text(
        Path("docs/conf.py").read_text(encoding="utf-8"), encoding="utf-8"
    )

    for name in (
        "DOCS_SITE_URL",
        "DOCS_PROJECT_PATH",
        "DOCS_CHANNEL",
        "DOCS_VERSION",
        "DOCS_CURRENT_PATH",
        "DOCS_CURRENT_LABEL",
        "DOCS_VERSIONS_JSON",
    ):
        monkeypatch.delenv(name, raising=False)

    config = runpy.run_path(str(conf_path))

    assert config["project"] == "historical-project"
    assert config["author"] == "Historical Maintainer"
    assert config["copyright"] == "2026, Historical Maintainer"


def test_parse_release_tag_accepts_only_stable_semver_tags():
    release = build_versioned_docs.parse_release_tag("v1.2.3")

    assert release is not None
    assert release.version == (1, 2, 3)
    assert release.label == "1.2.3"
    assert build_versioned_docs.parse_release_tag("v1.2.3-rc1") is None
    assert build_versioned_docs.parse_release_tag("release-1.2.3") is None
    assert build_versioned_docs.parse_release_tag("v01.2.3") is None


def test_select_release_tags_sorts_semantically_and_keeps_newest_five():
    tags = [
        "v0.9.1",
        "v0.9.10",
        "v0.9.2",
        "v1.0.0",
        "v2.0.0",
        "v0.9.4",
        "v0.9.3",
        "v0.9.5-rc1",
        "not-a-release",
    ]

    releases = build_versioned_docs.select_release_tags(tags)

    assert [release.tag for release in releases] == [
        "v2.0.0",
        "v1.0.0",
        "v0.9.10",
        "v0.9.4",
        "v0.9.3",
    ]


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        (["v0.1.0", "v0.2.0"], ["v0.2.0", "v0.1.0"]),
        (
            ["v0.1.0", "v0.2.0", "v0.3.0", "v0.4.0", "v0.5.0"],
            ["v0.5.0", "v0.4.0", "v0.3.0", "v0.2.0", "v0.1.0"],
        ),
    ],
)
def test_select_release_tags_handles_fewer_than_or_equal_to_five(tags, expected):
    releases = build_versioned_docs.select_release_tags(tags)

    assert [release.tag for release in releases] == expected


def test_build_manifest_orders_latest_releases_and_development():
    releases = build_versioned_docs.select_release_tags(["v0.9.2", "v0.9.4", "v0.9.3"])

    assert build_versioned_docs.build_manifest(releases) == [
        {"label": "latest", "url": "/pynfse-nacional/latest/"},
        {"label": "0.9.4", "url": "/pynfse-nacional/0.9.4/"},
        {"label": "0.9.3", "url": "/pynfse-nacional/0.9.3/"},
        {"label": "0.9.2", "url": "/pynfse-nacional/0.9.2/"},
        {"label": "development", "url": "/pynfse-nacional/development/"},
    ]


def test_ensure_changelog_navigation_updates_historical_appendix(tmp_path):
    appendix = tmp_path / "docs/appendix"
    appendix.mkdir(parents=True)
    index = appendix / "index.md"
    index.write_text(
        """# Apêndice

```{toctree}

troubleshooting
```
""",
        encoding="utf-8",
    )

    build_versioned_docs.ensure_changelog_navigation(tmp_path)

    updated = index.read_text(encoding="utf-8")
    assert "[Registro de alterações](changelog)" in updated
    assert "\nchangelog\n" in updated


def test_trim_changelog_for_release_keeps_selected_release_and_predecessors(tmp_path):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        """# Registro de alterações

## 0.9.5 - 2026-07-14

- Mudanças mais recentes.

## 0.9.4 - 2026-07-12

- Mudanças da versão selecionada.

## [0.9.0] - 2026-07-02

- Mudanças anteriores.

[0.9.0]: https://example.test/0.9.0
""",
        encoding="utf-8",
    )

    build_versioned_docs.trim_changelog_for_release(tmp_path, "0.9.4")

    trimmed = changelog.read_text(encoding="utf-8")
    assert "## 0.9.5 -" not in trimmed
    assert "## 0.9.4 -" in trimmed
    assert "## [0.9.0] -" in trimmed
    assert "[0.9.0]: https://example.test/0.9.0" in trimmed


def test_build_site_assembles_channels_and_aliases(tmp_path, monkeypatch):
    releases = build_versioned_docs.select_release_tags(
        ["v0.9.1", "v0.9.2", "v0.9.3", "v0.9.4", "v1.0.0"]
    )
    calls = []

    def fake_build_ref(
        repo: Path,
        ref: str,
        output: Path,
        *,
        environment: dict[str, str],
        worktree_root: Path,
        versioning_source: Path,
        changelog_version: str | None = None,
    ) -> None:
        del repo, worktree_root, versioning_source, changelog_version
        calls.append((ref, environment["DOCS_CURRENT_LABEL"]))
        output.mkdir(parents=True)
        manifest = json.loads(environment["DOCS_VERSIONS_JSON"])
        links = " ".join(item["url"] for item in manifest)
        (output / "index.html").write_text(
            f"{environment['DOCS_CURRENT_LABEL']} {links}", encoding="utf-8"
        )

    monkeypatch.setattr(
        build_versioned_docs, "discover_release_tags", lambda repo: releases
    )
    monkeypatch.setattr(build_versioned_docs, "resolve_ref", lambda repo, ref: ref)
    monkeypatch.setattr(build_versioned_docs, "build_ref", fake_build_ref)

    output = tmp_path / "site"
    selected = build_versioned_docs.build_site(tmp_path, output)

    assert selected == releases
    assert calls == [
        ("v1.0.0", "1.0.0"),
        ("v0.9.4", "0.9.4"),
        ("v0.9.3", "0.9.3"),
        ("v0.9.2", "0.9.2"),
        ("v0.9.1", "0.9.1"),
        ("v1.0.0", "latest"),
        ("master", "development"),
    ]
    assert {path.name for path in output.iterdir() if path.is_dir()} == {
        "1.0.0",
        "0.9.4",
        "0.9.3",
        "0.9.2",
        "0.9.1",
        "latest",
        "development",
    }
    assert (output / "index.html").read_text(encoding="utf-8").startswith("latest ")
    assert (
        (output / "latest/index.html").read_text(encoding="utf-8").startswith("latest ")
    )
    assert (
        (output / "1.0.0/index.html").read_text(encoding="utf-8").startswith("1.0.0 ")
    )
    assert (
        (output / "development/index.html")
        .read_text(encoding="utf-8")
        .startswith("development ")
    )


def test_build_site_requires_at_least_one_release_tag(tmp_path, monkeypatch):
    monkeypatch.setattr(build_versioned_docs, "discover_release_tags", lambda repo: [])

    with pytest.raises(RuntimeError, match="no annotated"):
        build_versioned_docs.build_site(tmp_path, tmp_path / "site")
