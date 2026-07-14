from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))

with (root / "pyproject.toml").open("rb") as metadata_file:
    pyproject = tomllib.load(metadata_file)

project_metadata = pyproject["project"]
docs_metadata = pyproject.get("tool", {}).get("pynfse_nacional", {}).get("docs", {})
project = project_metadata["name"]
author = project_metadata["authors"][0]["name"]
# Historical release tags predate the custom docs metadata section.
copyright_year = docs_metadata.get("copyright_year", 2026)
copyright = f"{copyright_year}, {author}"
package_version = project_metadata["version"]
documentation_url = urlsplit(project_metadata["urls"]["Documentation"])
default_docs_site_url = f"{documentation_url.scheme}://{documentation_url.netloc}"
default_project_path = documentation_url.path.rstrip("/")

DOCS_SITE_URL = os.environ.get("DOCS_SITE_URL", default_docs_site_url).rstrip("/")
DOCS_PROJECT_PATH = os.environ.get("DOCS_PROJECT_PATH", default_project_path).rstrip(
    "/"
)
DOCS_CHANNEL = os.environ.get("DOCS_CHANNEL", "development")
DOCS_VERSION = os.environ.get("DOCS_VERSION", package_version)
DOCS_CURRENT_PATH = os.environ.get("DOCS_CURRENT_PATH", "")
DOCS_CURRENT_LABEL = os.environ.get(
    "DOCS_CURRENT_LABEL",
    {"release": DOCS_VERSION, "latest": "latest"}.get(DOCS_CHANNEL, "development"),
)


def public_path(suffix: str = "") -> str:
    """Return a site-root-relative path for a documentation channel."""

    path = f"{DOCS_PROJECT_PATH}/{suffix.strip('/')}" if suffix else DOCS_PROJECT_PATH
    return f"{path}/"


def _default_docs_versions() -> list[dict[str, str]]:
    """Return the minimal navigation available to a local docs build."""

    return [
        {"label": "latest", "url": public_path("latest")},
        {"label": DOCS_VERSION, "url": public_path(DOCS_VERSION)},
        {"label": "development", "url": public_path("development")},
    ]


def _load_docs_versions() -> list[dict[str, str]]:
    """Load the version navigation manifest supplied by the build workflow."""

    raw_manifest = os.environ.get("DOCS_VERSIONS_JSON")
    if not raw_manifest:
        return _default_docs_versions()

    try:
        manifest = json.loads(raw_manifest)
    except json.JSONDecodeError as exc:
        raise ValueError("DOCS_VERSIONS_JSON must contain valid JSON") from exc

    if not isinstance(manifest, list) or not all(
        isinstance(item, dict)
        and isinstance(item.get("label"), str)
        and isinstance(item.get("url"), str)
        for item in manifest
    ):
        raise ValueError(
            "DOCS_VERSIONS_JSON must be a list of objects with label and url"
        )
    return manifest


docs_versions = _load_docs_versions()


def _docs_changelog_url() -> str:
    """Return the changelog URL for the current published channel."""

    suffix = (
        f"{DOCS_CURRENT_PATH}/appendix/changelog"
        if DOCS_CURRENT_PATH
        else "appendix/changelog"
    )
    return f"{public_path(suffix).rstrip('/')}.html"


docs_changelog_url = _docs_changelog_url()

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "sphinx_design",
    "sphinx_copybutton",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_title = "pynfse-nacional"
html_baseurl = f"{DOCS_SITE_URL}{public_path(DOCS_CURRENT_PATH).rstrip('/')}/"
html_static_path = ["_static"]
html_css_files = ["version-switcher.css"]
html_extra_path = ["llms.txt"]

html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/search.html",
        "version-switcher.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
        "sidebar/variant-selector.html",
    ]
}

html_context = {
    "docs_channel": DOCS_CHANNEL,
    "docs_changelog_url": docs_changelog_url,
    "docs_current_label": DOCS_CURRENT_LABEL,
    "docs_version": DOCS_VERSION,
    "docs_versions": docs_versions,
}

autosummary_generate = False
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
autodoc_typehints_format = "short"
autodoc_class_signature = "separated"

autodoc_mock_imports = [
    "reportlab",
    "qrcode",
    "PIL",
]

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_preprocess_types = True

myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3

html_theme_options = {
    "sidebar_hide_name": False,
}

release = package_version
version = package_version
