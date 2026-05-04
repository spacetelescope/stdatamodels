import pytest

from stdatamodels import dqflags
from stdatamodels.basic_utils import multiple_replace
from stdatamodels.jwst.datamodels.dqflags import multiple_replace as dqflags_multiple_replace
from stdatamodels.jwst.datamodels.dqflags import pixel


def test_dqflags():
    assert dqflags.dqflags_to_mnemonics(1, pixel) == {"DO_NOT_USE"}
    assert dqflags.dqflags_to_mnemonics(7, pixel) == {"JUMP_DET", "DO_NOT_USE", "SATURATED"}


def test_multiple_replace_deprecated():
    with pytest.warns(DeprecationWarning, match="The multiple_replace function is deprecated"):
        multiple_replace("button mutton", {"but": "mut", "mutton": "lamb"})
    with pytest.warns(DeprecationWarning, match="The multiple_replace function is deprecated"):
        dqflags_multiple_replace("button mutton", {"but": "mut", "mutton": "lamb"})
