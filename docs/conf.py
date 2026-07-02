from __future__ import annotations

from pathlib import Path
import sys

project = "pynfse-nacional"
author = "Project Maintainer"
copyright = "2026, Project Maintainer"

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))

from pynfse_nacional import __version__  # noqa: E402

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_title = "pynfse-nacional"
html_baseurl = "https://robmello.github.io/pynfse-nacional/"
html_static_path = []
html_css_files = []

autosummary_generate = False
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}

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

release = __version__
version = __version__
