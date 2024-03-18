import sys

import importlib.resources as importlib_resources

import asdf
import pytest
import yaml


METASCHEMAS = list(
    importlib_resources.files("stdatamodels.jwst.datamodels.metaschema").glob("*.yaml")
)

DATAMODEL_SCHEMAS = list(
    importlib_resources.files("stdatamodels.jwst.datamodels.schemas").glob("*.yaml")
)
# transform schemas are nested in a directory with a '.'
TRANSFORM_SCHEMAS = list(
    next(
        importlib_resources.files(
            "stdatamodels.jwst.transforms.resources.schemas"
        ).iterdir()
    ).glob("**/*.yaml")
)

SCHEMAS = METASCHEMAS + DATAMODEL_SCHEMAS + TRANSFORM_SCHEMAS

TRANSFORM_MANIFESTS = list(
    importlib_resources.files("stdatamodels.jwst.transforms.resources.manifests").glob(
        "*.yaml"
    )
)

RESOURCES = SCHEMAS + TRANSFORM_MANIFESTS


@pytest.mark.parametrize("resource", RESOURCES)
def test_resource_id(resource):
    """
    Test that all "resources" (schemas, metaschemas and manifests) are
    registered with asdf using the "id" in the resource.
    """
    with open(resource, "rb") as f:
        contents = f.read()
    schema = yaml.safe_load(contents.decode("ascii"))
    resource_manager = asdf.get_config().resource_manager

    # check that asdf is aware of the "id"
    assert (
        schema["id"] in resource_manager
    ), f"id[{schema['id']}] for resource[{resource}] was not registered with asdf"

    # and that using the "id" to fetch the resource returns the contents of the file
    assert (
        resource_manager[schema["id"]] == contents
    ), f"id[{schema['id']}] for resource[{resource}] did not return the contents of the resource"
