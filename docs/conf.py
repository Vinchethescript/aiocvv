import os
import re

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "aiocvv"
copyright = "2024, Vinche.zsh"

with open(
    os.path.join(os.path.dirname(__file__), "..", project, "__init__.py"),
    "r",
    encoding="utf-8",
) as f:
    kwargs = {
        var.strip("_"): val
        for var, val in re.findall(
            r'^(__\w+__)\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE
        )
    }

author = kwargs["author"]
release = kwargs["version"]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx_autodoc_typehints"]

autodoc_typehints = "description"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
