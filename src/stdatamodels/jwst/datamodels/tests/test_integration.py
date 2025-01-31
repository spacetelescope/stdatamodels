import importlib.resources

import asdf
import pytest
import yaml

from stdatamodels.jwst.datamodels import JwstDataModel
import stdatamodels.schema


DATAMODEL_SCHEMAS = list(
    importlib.resources.files("stdatamodels.jwst.datamodels.schemas").glob("*.yaml")
)
# transform schemas are nested in a directory with a '.'
TRANSFORM_SCHEMAS = list(
    next(
        importlib.resources.files("stdatamodels.jwst.transforms.resources.schemas").iterdir()
    ).glob("**/*.yaml")
)

SCHEMAS = DATAMODEL_SCHEMAS + TRANSFORM_SCHEMAS

TRANSFORM_MANIFESTS = list(
    importlib.resources.files("stdatamodels.jwst.transforms.resources.manifests").glob("*.yaml")
)

RESOURCES = SCHEMAS + TRANSFORM_MANIFESTS


def datamodel_associated_schemas():
    """
    Get all schemas directly associated with a datamodel
    """
    schema_urls = []
    for subclass in JwstDataModel.__subclasses__():
        if subclass.schema_url:
            schema_urls.append(subclass.schema_url)
    return schema_urls


@pytest.mark.parametrize("resource", RESOURCES)
def test_resource_id(resource):
    """
    Test that all "resources" (schemas, and manifests) are
    registered with asdf using the "id" in the resource.
    """
    with open(resource, "rb") as f:
        contents = f.read()
    schema = yaml.safe_load(contents.decode("ascii"))
    resource_manager = asdf.get_config().resource_manager

    # check that asdf is aware of the "id"
    assert schema["id"] in resource_manager, (
        f"id[{schema['id']}] for resource[{resource}] was not registered with asdf"
    )

    # and that using the "id" to fetch the resource returns the contents of the file
    assert resource_manager[schema["id"]] == contents, (
        f"id[{schema['id']}] for resource[{resource}] did not return the contents of the resource"
    )


@pytest.mark.parametrize("manifest_filename", TRANSFORM_MANIFESTS)
def test_manifest_tag_versions(manifest_filename):
    with open(manifest_filename, "rb") as f:
        contents = f.read()
    manifest = yaml.safe_load(contents.decode("ascii"))

    for tag_def in manifest["tags"]:
        tag_uri = tag_def["tag_uri"]
        tag_name, tag_version = asdf.versioning.split_tag_version(tag_uri)
        schema_uri = tag_def["schema_uri"]
        schema_name, schema_version = asdf.versioning.split_tag_version(schema_uri)
        # although not generally required for stdatamodels transforms all
        # tag versions should match schema version
        assert tag_version == schema_version


@pytest.mark.parametrize("datamodel_schema_file", datamodel_associated_schemas())
def test_schema_refs_base(datamodel_schema_file):
    """
    Each datamodel schema should either reference:
        - http://stsci.edu/schemas/jwst_datamodel/core.schema (for data models)
        - http://stsci.edu/schemas/jwst_datamodel/referencefile.schema (for reference files)
    But not both
    """

    # these schemas don't reference either core.schema or referencefile.schema
    if datamodel_schema_file in [
        "http://stsci.edu/schemas/jwst_datamodel/slitdata.schema",
        "http://stsci.edu/schemas/jwst_datamodel/extract1dimage.schema",
    ]:
        return

    schema = asdf.schema.load_schema(datamodel_schema_file, resolve_references=True)

    def cb(subschema, path, combiner, ctx, recurse):
        if not isinstance(subschema, dict):
            return
        if "id" not in subschema:
            return
        ctx["ids"].add(subschema["id"])

    seen_ids = set()
    stdatamodels.schema.walk_schema(schema, cb, ctx={"ids": seen_ids})

    if "http://stsci.edu/schemas/jwst_datamodel/core.schema" in seen_ids:
        assert "http://stsci.edu/schemas/jwst_datamodel/referencefile.schema" not in seen_ids
    elif "http://stsci.edu/schemas/jwst_datamodel/referencefile.schema" in seen_ids:
        assert "http://stsci.edu/schemas/jwst_datamodel/core.schema" not in seen_ids
    else:
        assert False
