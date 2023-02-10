#!/usr/bin/env python3
from setuptools import setup

package_data = {
    "": [
        "*.yaml",
    ],
    # Include the transforms schemas
    "stdatamodels.jwst.transforms": [
        "resources/schemas/stsci.edu/jwst_pipeline/*.yaml",
    ],
}

setup(
    use_scm_version={"write_to": "src/stdatamodels/_version.py"},
    package_data=package_data,
)
