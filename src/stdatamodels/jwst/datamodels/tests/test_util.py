from stdatamodels.jwst.datamodels import util

import pytest


@pytest.mark.parametrize("func_name", [
    "get_available_memory",
    "get_available_memory_linux",
    "get_available_memory_darwin",
])
def test_deprecated(func_name):
    with pytest.warns(DeprecationWarning, match=f"{func_name} is deprecated"):
        getattr(util, func_name)()
