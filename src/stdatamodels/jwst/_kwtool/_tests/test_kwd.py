"""
Tests here use the fake_kwd fixture in conftest
"""

import pytest


@pytest.fixture(params=[("PRIMARY", "TITLE"), ("SCI", "OBS_IDD"), ("PRIMARY", "ENG_QUAL")])
def keyword_list(request, fake_kwd):
    return fake_kwd[request.param]


@pytest.fixture()
def keyword(keyword_list):
    """
    The real keyword dictionary will contain multiple entries for 1 "keyword"
    (a FITS_HDU, FITS_KEYWORD pair). The test dictionary does not, this
    fixture helps to test just the first found entry.
    """
    return keyword_list[0]


def test_fits_keyword_count(fake_kwd):
    assert len(fake_kwd) == 3


def test_found(keyword_list):
    """
    This uses the keyword_list fixture to make sure that the test dictionary
    only contains one entry per keyword pair (an assumption made by the
    keyword fixture above).
    """
    assert len(keyword_list) == 1


@pytest.mark.parametrize("missing_key", ["allOf", "properties"])
def test_path_sanitized(missing_key, keyword):
    assert missing_key not in keyword["path"]
