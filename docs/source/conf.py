# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# -- Point to root of code
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# -- Documentation Properties
project = "quiz_demo"
copyright = "2026, Stuart Williams"
author = "Stuart Williams"
release = "1.01"

# -- List of my favorite extensions
extensions = [
    "sphinx_markdown_builder",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_new_tab_link",
]

# -- Options to enable Google format
napoleon_google_docstring = True

# -- My favorite documentation theme
html_theme = "conestack"

# -- My Custom Logo The configuration path is relative to the conf.py directory
html_logo = "_static/blogo.svg"

# -- Replace title text
html_title = "Quiz Demo Documentation"
html_short_title = "Quiz"

# Suppress spurious markdown warning for '*'
suppress_warnings = ["sphinx_markdown_builder.unknown_node", "misc.unknown_node"]

# Defaults
html_static_path = ["_static"]
templates_path = ["_templates"]
exclude_patterns = []
