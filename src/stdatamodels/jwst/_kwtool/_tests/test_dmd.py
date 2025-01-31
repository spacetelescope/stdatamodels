"""
monkeypatch _get_subclasses to only return 1 datamodel (to make things easier)
separately test _get_subclasses
"""

import pytest

from stdatamodels.jwst.datamodels import DarkModel, JwstDataModel, ReferenceFileModel
from stdatamodels.jwst._kwtool import dmd


def test_get_subclasses():
    # more of a smoke test
    assert DarkModel in dmd._get_subclasses(JwstDataModel)


def test_get_subclasses_ignore():
    assert DarkModel not in dmd._get_subclasses(JwstDataModel, {ReferenceFileModel})


@pytest.fixture(params=[("PRIMARY", "TITLE"), ("PRIMARY", "OBS_ID"), ("PRIMARY", "ENG_QUAL")])
def keyword_list(request, fake_dmd):
    """
    There are many more keywords than the ones used here. These
    were chosen to match the ones added in the fake keyword dictionary.
    """
    return fake_dmd[request.param]


@pytest.fixture()
def keyword(keyword_list):
    """
    The real datamodel dictionary will contain multiple entries for 1 "keyword"
    (a FITS_HDU, FITS_KEYWORD pair). The test dictionary does not, this
    fixture helps to test just the first found entry.
    """
    return keyword_list[0]


def test_found(keyword_list):
    """
    This uses the keyword_list fixture to make sure that the test dictionary
    only contains one entry per keyword pair (an assumption made by the
    keyword fixture above).
    """
    assert len(keyword_list) == 1
