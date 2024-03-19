import platform

from stdatamodels.jwst.datamodels import util

import pytest


@pytest.mark.parametrize("func_name", [
    "get_available_memory",
    "get_available_memory_linux",
])
def test_deprecated(func_name):
    with pytest.warns(DeprecationWarning, match=f"{func_name} is deprecated"):
        getattr(util, func_name)()


@pytest.mark.skipif(platform.system() != 'Darwin', reason="only runs on darwin")
def test_deprecated_get_available_memory_darwin():
    with pytest.warns(DeprecationWarning, match="get_available_memory_darwin is deprecated"):
        util.get_available_memory_darwin()
