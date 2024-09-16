from pathlib import Path

import asdf
import pytest
import yaml

from stdatamodels.fits_support import _get_validators
from stdatamodels.schema import walk_schema


# relative paths to schema directories
SCHEMA_RELATIVE_PATHS = [
    "../datamodels/schemas",
    "../transforms/resources/schemas/stsci.edu/jwst_pipeline",
]


def _get_schema_ids():
    root_path = Path(__file__).parent
    schema_ids = []
    for schema_relative_path in SCHEMA_RELATIVE_PATHS:
        path = root_path / schema_relative_path
        for schema_path in path.glob("*.yaml"):
            with open(schema_path, "r") as f:
                schema_ids.append(yaml.load(f, yaml.SafeLoader)["id"])
    return schema_ids


SCHEMA_IDS = _get_schema_ids()


@pytest.fixture(scope="module")
def known_validators():
    # what validators do we understand?
    # since we aren't going to use these we can feed it
    # anything in place of a valid hdulist
    class Foo:
        pass

    validators = _get_validators(Foo())[0]
    known_validators = set(validators.keys())
    return known_validators


@pytest.fixture(scope="module")
def valid_keywords(known_validators):
    return known_validators | {
        "id",
        "$schema",
        "title",
        "description",
        "default",
        "examples",
        "blend_table",
        "blend_rule",
        "fits_hdu",
        "definitions",
        "allow_extra_columns",
    }


def test_found_schemas():
    """
    Make sure we found some schemas
    """
    assert SCHEMA_IDS


@pytest.mark.parametrize("schema_id", SCHEMA_IDS)
def test_schema_contains_only_known_keywords(schema_id, valid_keywords):
    # load the schema from asdf instead of the file to
    # verify that asdf knows about the schema
    schema = asdf.schema.load_schema(schema_id)


    def callback(schema, path, combiner, ctx, recurse):
        extra = schema.keys() - ctx["valid_keywords"]
        assert not extra, f"{extra} found at {path} in {schema_id}"

    ctx = {"valid_keywords": valid_keywords}
    walk_schema(schema, callback, ctx)
