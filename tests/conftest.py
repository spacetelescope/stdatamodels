"""Project default for pytest"""
import pytest

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
