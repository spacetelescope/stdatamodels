import importlib.resources

import asdf
import pytest


@pytest.fixture(scope="session", autouse=True)
def register_schemas():
    """Register the schemas directory with asdf."""
    schemas_root = importlib.resources.files("stdatamodels") / "_tests" / "schemas"
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
