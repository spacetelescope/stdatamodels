"""Project defaults for pytest."""

from pathlib import Path

import pytest

import asdf


def pytest_addoption(parser):
    """Add options to the pytest command line."""
    parser.addoption(
        "--no-crds",
        action="store_true",
        default=False,
        help="Skip tests against crds",
    )


@pytest.fixture(scope="session", autouse=True)
def register_schemas():
    """Register the schemas directory with asdf."""
    schemas_root = Path(__file__).parent / "schemas"
    with asdf.config_context() as config:
        config.add_resource_mapping(
            asdf.resource.DirectoryResourceMapping(schemas_root, "http://example.com/schemas")
        )
        yield


@pytest.fixture(autouse=True)
def patch_env_variables(monkeypatch):
    """Make sure the environment doesn't initially contain these so test results are consistent."""
    for var in [
        "PASS_INVALID_VALUES",
        "STRICT_VALIDATION",
        "VALIDATE_ON_ASSIGNMENT",
    ]:
        monkeypatch.delenv(var, raising=False)
