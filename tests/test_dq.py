from stdatamodels import dqflags
from stdatamodels.jwst.datamodels.dqflags import pixel


def test_dqflags():
    assert dqflags.dqflags_to_mnemonics(1, pixel) == {"DO_NOT_USE"}
    assert dqflags.dqflags_to_mnemonics(7, pixel) == {"JUMP_DET", "DO_NOT_USE", "SATURATED"}
