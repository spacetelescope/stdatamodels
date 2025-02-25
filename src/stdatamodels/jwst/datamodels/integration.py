"""Create the entry points for ASDF support for the `jwst.datamodels`."""

import importlib.resources


from asdf.resource import DirectoryResourceMapping
from stdatamodels.jwst import datamodels


def get_resource_mappings():
    """
    Get the `jwst.datamodels` resource mappings, that is the schemas for the datamodels.

    This method is registered with the `asdf.resource_mappings` entry point for
    the `jwst_datamodel`.

    Returns
    -------
    list of `asdf.resource.ResourceMapping` instances
        List containing the `jwst.datamodels` schemas.
    """
    resources_root = importlib.resources.files(datamodels)
    if not resources_root.is_dir():
        raise RuntimeError(f"Missing resources directory: {resources_root=}")

    return [
        DirectoryResourceMapping(
            resources_root / "schemas",
            "http://stsci.edu/schemas/jwst_datamodel/",
        )
    ]
