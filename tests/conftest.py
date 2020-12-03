"""Project default for pytest"""
from pathlib import Path

import pytest

import asdf

import helpers
from stdatamodels import s3_utils


@pytest.fixture(autouse=True)
def monkey_patch_s3_client(monkeypatch, request):
    # If tmpdir is used in the test, then it is providing the file.  Map to it.
    if "s3_root_dir" in request.fixturenames:
        path = request.getfixturevalue("s3_root_dir")
    else:
        path = None
    monkeypatch.setattr(s3_utils, "_CLIENT", helpers.MockS3Client(path))


@pytest.fixture
def s3_root_dir(tmpdir):
    return tmpdir


@pytest.fixture(scope="session", autouse=True)
def register_schemas():
    schemas_root = Path(__file__).parent/"schemas"
    with asdf.config_context() as config:
        config.add_resource_mapping(
            asdf.resource.DirectoryResourceMapping(schemas_root, "http://example.com/schemas")
        )
        yield


@pytest.fixture(autouse=True)
def patch_env_variables(monkeypatch):
    """
    Make sure the environment doesn't initially contain these so
    that test results are consistent.
    """
    for var in ["PASS_INVALID_VALUES", "STRICT_VALIDATION", "SKIP_FITS_UPDATE", "VALIDATE_ON_ASSIGNMENT"]:
        monkeypatch.delenv(var, raising=False)
