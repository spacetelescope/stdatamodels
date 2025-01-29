from pathlib import Path
import json
import os
import sys

import pytest
import requests
from urllib.parse import quote as urlencode

from stdatamodels.jwst._kwtool import cli


def fetch_keyword_dictionary():
    # Fetch the latest versioned keyword dictionary from MAST
    # This uses an "unofficial" service as there is no
    # officially supported way to query the keyword dictionary.
    request_data = urlencode(
        json.dumps(
            {
                "service": "Mast.Jwst.Keywords",
                "timeout": 10,
                "params": {},
                "format": "json",
                "page": 1,
                "pagesize": 1000,
            }
        )
    )
    response = requests.post(
        "https://mast.stsci.edu/api/v0/invoke",
        data=f"request={request_data}",
        headers={"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"},
        timeout=10,
    ).json()
    del response["msg"]
    del response["status"]
    return response


def dump_keyword_dictionary(path="."):
    path = Path(path)
    if not path.exists():
        path.mkdir()
    for fn, data in fetch_keyword_dictionary().items():
        with open(path / fn, "w") as f:
            json.dump(data, f)


@pytest.fixture(scope="module")
def local_kwd(tmp_path_factory):
    jwstkd = tmp_path_factory.mktemp("jwstkd")
    dump_keyword_dictionary(jwstkd)
    return jwstkd


@pytest.fixture(scope="module")
def report_path(tmp_path_factory, local_kwd):
    # move to a new, empty directory
    temp_cwd = tmp_path_factory.mktemp("cwd")
    os.chdir(temp_cwd)

    output_dir = tmp_path_factory.mktemp("output")
    output_path = output_dir / "my_report.html"

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(sys, "argv", [sys.argv[0], str(local_kwd), "-o", str(output_path)])
        cli._from_cmdline()

    return output_path


def test_report(report_path):
    assert report_path.exists()
