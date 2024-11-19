import pytest
import os


# this submodule is deprecated and contains no tests
collect_ignore = ["schema_editor.py"]


@pytest.fixture
def jail_environ():
    """Lock changes to the environment"""
    original = os.environ.copy()
    try:
        yield
    finally:
        os.environ = original
