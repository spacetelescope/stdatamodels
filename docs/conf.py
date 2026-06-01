# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import importlib
import tomllib
import datetime
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

with open(Path(__file__).parent.parent / "pyproject.toml", "rb") as metadata_file:
    metadata = tomllib.load(metadata_file)["project"]

project = metadata["name"]
author = "Space Telescope Science Institute"
copyright = f"{datetime.datetime.today().year}, {author}"

package = importlib.import_module(metadata["name"])
try:
    version = package.__version__.split("-", 1)[0]
    # The full version, including alpha/beta/rc tags.
    release = package.__version__
except AttributeError:
    version = "dev"
    release = "dev"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "autoapi.extension",
    "numpydoc",
    "pytest_doctestplus.sphinx.doctestplus",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# reST default role used for single backticks (`text`)
default_role = "obj"

# -- HTML output configuration ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_theme_options = {
    "collapse_navigation": True,
    "sticky_navigation": False,
    "style_external_links": True,
}
html_logo = "_static/stsci_pri_combo_mark_dark_bkgd.png"
html_last_updated_fmt = "%b %d, %Y"
html_sidebars = {"**": ["globaltoc.html", "relations.html", "searchbox.html"]}
html_domain_indices = True
html_use_index = True

# -- EPUB output configuration -----------------------------------------------

epub_show_urls = "footnote"

# -- linkcheck configuration -------------------------------------------------

linkcheck_retry = 5
linkcheck_ignore = [
    "http://stsci.edu/schemas/fits-schema/",  # Old schema from CHANGES.rst
    "https://outerspace.stsci.edu",  # CI blocked by service provider
    "https://jira.stsci.edu/",  # Internal access only
    r"https://.*\.readthedocs\.io",  # 429 Client Error: Too Many Requests
    "https://doi.org",  # CI blocked by service provider (timeout)
]
linkcheck_timeout = 180
linkcheck_anchors = False
linkcheck_report_timeouts_as_broken = True
linkcheck_allow_unauthorized = False

# Enable nitpicky mode - which ensures that all references in the docs resolve.
nitpicky = True

# -- numpydoc configuration --------------------------------------------------

# Don't show summaries of the members in each class along with the class' docstring
numpydoc_show_class_members = False

# -- sphinx-autoapi configuration --------------------------------------------
# https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html

autoapi_dirs = ["../src"]
autoapi_root = "api"
autoapi_generate_api_docs = False
autoapi_member_order = "bysource"
autoapi_python_class_content = "both"

# -- sphinx.ext.intersphinx configuration ------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    "asdf": ("https://asdf.readthedocs.io/en/stable/", None),
    "astropy": ("https://docs.astropy.org/en/stable/", None),
    "drizzle": ("https://spacetelescope-drizzle.readthedocs.io/en/latest/", None),
    "gwcs": ("https://gwcs.readthedocs.io/en/stable/", None),
    "matplotlib": ("https://matplotlib.org/", None),
    "numpy": ("https://numpy.org/devdocs", None),
    "photutils": ("https://photutils.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
    "scipy": ("https://scipy.github.io/devdocs", None),
    "stcal": ("https://stcal.readthedocs.io/en/latest/", None),
    "stdatamodels": ("https://stdatamodels.readthedocs.io/en/latest/", None),
    "stpipe": ("https://stpipe.readthedocs.io/en/latest/", None),
    "synphot": ("https://synphot.readthedocs.io/en/latest/", None),
    "tweakwcs": ("https://tweakwcs.readthedocs.io/en/latest/", None),
}
intersphinx_disabled_domains = ["std"]
