#!/usr/bin/env python3
from setuptools import setup

package_data = {
    "": [
        "*.yaml",
    ]
}

setup(
    use_scm_version={"write_to": "src/stdatamodels/_version.py"},
    package_data=package_data,
)
