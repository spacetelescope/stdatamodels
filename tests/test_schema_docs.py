"""Test that docs contain links to the latest schemas."""

import pathlib
import re

import pytest

REPO_PATH = pathlib.Path(__file__).parent.parent
DOCS_PATH = REPO_PATH / "docs"
TRANSFORMS_DOCS = DOCS_PATH / "source" / "jwst" / "transforms" / "index.rst"
TRANSFORMS_RESOURCES_PATH = REPO_PATH / "src" / "stdatamodels" / "jwst" / "transforms" / "resources"
TRANSFORMS_SCHEMAS_PATH = TRANSFORMS_RESOURCES_PATH / "schemas" / "stsci.edu" / "jwst_pipeline"
LEGACY_TRANSFORMS_SCHEMAS_PATH = (
    TRANSFORMS_RESOURCES_PATH / "legacy" / "schemas" / "stsci.edu" / "jwst_pipeline"
)


def schema_path_to_basename_and_version(path):
    basename, version = path.stem.split("-", maxsplit=1)
    return basename, tuple(map(int, version.split(".")))


def latest_schemas(resource_path):
    latest_schema_paths_by_basename = {}
    for schema_path in resource_path.glob("*.yaml"):
        basename, version = schema_path_to_basename_and_version(schema_path)
        if basename not in latest_schema_paths_by_basename:
            latest_schema_paths_by_basename[basename] = schema_path
            continue
        _, other_version = schema_path_to_basename_and_version(
            latest_schema_paths_by_basename[basename]
        )
        if version > other_version:
            latest_schema_paths_by_basename[basename] = schema_path
    return latest_schema_paths_by_basename.values()


@pytest.fixture()
def latest_transforms_schemas():
    return [path.stem for path in latest_schemas(TRANSFORMS_SCHEMAS_PATH)]


@pytest.fixture()
def latest_legacy_transforms_schemas():
    return [path.stem for path in latest_schemas(LEGACY_TRANSFORMS_SCHEMAS_PATH)]


def iter_autoschema_blocks():
    in_autoschema_block = False
    schema_root = None
    schemas = []
    with TRANSFORMS_DOCS.open() as f:
        for line in f:
            # skip empty lines
            if not line.strip():
                continue

            # check if entering an autoschema block
            if not in_autoschema_block:
                if line.startswith(".. asdf-autoschemas::"):
                    in_autoschema_block = True
                continue

            # if line is not indented, no longer in autoschema block
            if not re.match(r"\s", line):
                yield schema_root, schemas
                in_autoschema_block = False
                schema_root = None
                schemas = []
                continue

            # in an autoschema block
            if ":schema_root:" in line:
                schema_root = line.strip().split()[-1]
            elif line.strip().startswith(":"):  # allow other directives
                continue
            else:
                schemas.append(line.strip())
    if schema_root:
        yield schema_root, schemas


@pytest.fixture()
def documented_transforms_schemas():
    for root, schemas in iter_autoschema_blocks():
        if "legacy" not in root:
            return schemas
    raise Exception("Failed to find transforms schemas autoschemas block")


@pytest.fixture()
def documented_legacy_transforms_schemas():
    for root, schemas in iter_autoschema_blocks():
        if "legacy" in root:
            return schemas
    raise Exception("Failed to find legacy transforms schemas autoschemas block")


def test_transforms_schemas_versions(latest_transforms_schemas, documented_transforms_schemas):
    assert set(latest_transforms_schemas) == set(documented_transforms_schemas)


def test_legacy_transforms_schemas_versions(
    latest_legacy_transforms_schemas, documented_legacy_transforms_schemas
):
    assert set(latest_legacy_transforms_schemas) == set(documented_legacy_transforms_schemas)
