import os

import pytest


@pytest.fixture
def jail_environ():
    """Lock changes to the environment."""
    original = os.environ.copy()
    try:
        yield
    finally:
        os.environ = original  # noqa: B003
