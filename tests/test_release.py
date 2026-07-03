"""Tests for the release helper."""

import subprocess
from pathlib import Path

from pynfse_nacional import release


def test_build_command_uses_dist_dir():
    dist_dir = Path("/tmp/project/dist")

    assert release.build_command(dist_dir) == [
        "uv",
        "build",
        "--sdist",
        "--wheel",
        "--out-dir",
        str(dist_dir),
    ]


def test_publish_command_targets_pypi_by_default():
    dist_dir = Path("/tmp/project/dist")

    assert release.publish_command(dist_dir, "pypi", dry_run=False) == [
        "uv",
        "publish",
        str(dist_dir / "*"),
        "--publish-url",
        "https://upload.pypi.org/legacy/",
        "--check-url",
        "https://pypi.org/simple",
    ]


def test_project_uses_valid_python_classifier():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")

    assert "Development Status :: 5 - Production/Stable" in text


def test_main_cleans_builds_and_publishes(tmp_path, monkeypatch):
    calls = []

    def fake_run(command, *, cwd):
        calls.append((command, cwd))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(release, "project_root", lambda: tmp_path)
    monkeypatch.setattr(release, "run", fake_run)
    monkeypatch.setattr(release, "load_pypi_token", lambda repository: "pypi-token")

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / ".gitignore").write_text("*\n", encoding="utf-8")
    (dist_dir / "old.whl").write_text("stale", encoding="utf-8")

    exit_code = release.main(["--repository", "testpypi", "--dry-run"])

    assert exit_code == 0
    assert (dist_dir / ".gitignore").exists()
    assert not (dist_dir / "old.whl").exists()
    assert calls == [
        (
            [
                "uv",
                "build",
                "--sdist",
                "--wheel",
                "--out-dir",
                str(dist_dir),
            ],
            tmp_path,
        ),
        (
            [
                "uv",
                "publish",
                str(dist_dir / "*"),
                "--publish-url",
                "https://test.pypi.org/legacy/",
                "--check-url",
                "https://test.pypi.org/simple",
                "--token",
                "pypi-token",
                "--dry-run",
            ],
            tmp_path,
        ),
    ]


def test_load_pypi_token_reads_pypirc(tmp_path, monkeypatch):
    pypirc = tmp_path / ".pypirc"
    pypirc.write_text(
        "[pypi]\nusername = __token__\npassword = secret-token\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(release, "pypirc_path", lambda: pypirc)
    monkeypatch.delenv("UV_PUBLISH_TOKEN", raising=False)

    assert release.load_pypi_token("pypi") == "secret-token"


def test_load_pypi_token_prefers_matching_repository_url(tmp_path, monkeypatch):
    pypirc = tmp_path / ".pypirc"
    pypirc.write_text(
        (
            "[pypi]\n"
            "username = __token__\n"
            "password = # placeholder value\n\n"
            "[pynfse-nacional]\n"
            "repository = https://upload.pypi.org/legacy/\n"
            "username = __token__\n"
            "password = pypi-secret-token\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(release, "pypirc_path", lambda: pypirc)
    monkeypatch.delenv("UV_PUBLISH_TOKEN", raising=False)

    assert release.load_pypi_token("pypi") == "pypi-secret-token"
