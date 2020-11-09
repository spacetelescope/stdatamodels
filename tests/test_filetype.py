import io
import json

import pytest
import asdf
from astropy.io import fits

from stdatamodels.filetype import check


@pytest.mark.parametrize(
    "filename,expected_filetype",
    [
        ("test_file.fits", "fits"),
        ("test_file.fits.gz", "fits"),
        ("test_file.json", "asn"),
        ("test_file.json.gz", "asn"),
        ("test_file.asdf", "asdf"),
        ("test_file.asdf.gz", "asdf"),
        ("stpipe.MyPipeline.fits", "fits"),
        ("stpipe.MyPipeline.fits.gz", "fits"),
    ],
)
def test_supported_filename(filename, expected_filetype):
    assert check(filename) == expected_filetype


@pytest.mark.parametrize("filename", ["test_file", "test_file.mp4"])
def test_unsupported_filename(filename):
    with pytest.raises(ValueError):
        check(filename)


def test_seekable_file_object():
    buff = io.BytesIO()
    with asdf.AsdfFile() as af:
        af.write_to(buff)
    buff.seek(0)
    assert check(buff) == "asdf"

    buff = io.BytesIO()
    hdul = fits.HDUList(fits.PrimaryHDU())
    hdul.writeto(buff)
    buff.seek(0)
    assert check(buff) == "fits"

    buff = io.BytesIO()
    buff.write(json.dumps({"foo": "bar"}).encode("utf-8"))
    buff.seek(0)
    assert check(buff) == "asn"

    # Too short
    buff = io.BytesIO(b"FOO")
    with pytest.raises(ValueError):
        check(buff)


def test_non_seekable_object():
    with pytest.raises(ValueError):
        check(object())
