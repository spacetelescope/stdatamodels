import pytest
from astropy.nddata.bitmask import interpret_bit_flags as ap_interpret_bit_flags
from stdatamodels import dqflags
from stdatamodels.jwst.datamodels.dqflags import pixel


def test_dqflags():
    assert dqflags.dqflags_to_mnemonics(1, pixel) == {"DO_NOT_USE"}
    assert dqflags.dqflags_to_mnemonics(7, pixel) == {"JUMP_DET", "DO_NOT_USE", "SATURATED"}
    with pytest.warns(DeprecationWarning):
        assert dqflags.interpret_bit_flags("DO_NOT_USE + WARM", mnemonic_map=pixel) == 4097
    assert ap_interpret_bit_flags("DO_NOT_USE+WARM", flag_name_map=pixel) == 4097
