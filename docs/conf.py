"""Sphinx configuration for aridkpi documentation."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ── Project information ──────────────────────────────────────────────────────
project = "aridkpi"
author = "Gustavo Javier Barea Paci"
copyright = f"{datetime.now().year}, {author}"
release = "0.1.0"
version = "0.1.0"

# ── General configuration ────────────────────────────────────────────────────
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "en"

# ── HTML output ──────────────────────────────────────────────────────────────
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_show_sourcelink = True

# ── Autodoc / Napoleon ───────────────────────────────────────────────────────
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": False,
    "show-inheritance": True,
}
autosummary_generate = True
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_use_rtype = False

# ── Intersphinx ──────────────────────────────────────────────────────────────
intersphinx_mapping = {
    "python":     ("https://docs.python.org/3/", None),
    "numpy":      ("https://numpy.org/doc/stable/", None),
    "pandas":     ("https://pandas.pydata.org/docs/", None),
    "scipy":      ("https://docs.scipy.org/doc/scipy/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
}

# ── Doctest ──────────────────────────────────────────────────────────────────
doctest_global_setup = """
import pandas as pd
import numpy as np
"""
