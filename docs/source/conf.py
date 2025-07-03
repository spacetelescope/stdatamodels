from pathlib import Path
import os
import sys
from configparser import ConfigParser
from datetime import datetime
import importlib
import tomllib

REPO_ROOT = Path(__file__).parent.parent.parent

# Modules that automodapi will document need to be available
# in the path:
sys.path.insert(0, str(REPO_ROOT/"src"/"stdatamodels"))

with open(REPO_ROOT / "pyproject.toml", 'rb') as configuration_file:
    setup_metadata = tomllib.load(configuration_file)['project']

project = setup_metadata["name"]
author = setup_metadata["authors"][0]["name"]
copyright = f"{datetime.now().year}, {author}"

package = importlib.import_module(setup_metadata["name"])
version = package.__version__.split("-", 1)[0]
release = package.__version__

extensions = [
    "sphinx_automodapi.automodapi",
    "sphinxcontrib.jquery",
    "numpydoc",
    "sphinx_asdf",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "astropy": ("https://docs.astropy.org/en/stable/", None),
    "asdf": ("https://asdf.readthedocs.io/en/stable/", None),
}

autosummary_generate = True
numpydoc_show_class_members = False
autoclass_content = "both"

html_logo = 'static/stsci_pri_combo_mark_white.png'
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": True,
    "sticky_navigation": False,
}
html_domain_indices = True
html_sidebars = {"**": ["globaltoc.html", "relations.html", "searchbox.html"]}
html_use_index = True

nitpicky = True
nitpick_ignore = [
    ("py:class", "stdatamodels.jwst.datamodels.wcs_ref_models._SimpleModel"),
    ("py:class", "jwst.datamodels.wcs_ref_models._SimpleModel"),
    ("py:class", "stdatamodels.properties.ObjectNode"),
    ("py:class", "stdatamodels.properties.Node"),
]