"""
Test duplicated schema information is in sync.
"""

import asdf
import pytest

# keyword schema file
# - is this a single or multiple enum? (can it be inferred)
# - what's the path (can it be inferred, no, because of the referencefile schema for name)
# is there a pattern file (not all have them)
# - all are a single regex
# - what's the path? (can it be inferred)
# core schema location
# - single or multiple enum? (can it be inferred)
# - what's the path


comparisons = {
    "band": {
        "keyword": ("keyword_band.schema", "meta.instrument.band"),
        "pattern": ("keyword_pband.schema", "meta.instrument.p_band"),
        "core": ("core.schema", "meta.instrument.band"),
    },
    "channel": {
        "keyword": ("keyword_channel.schema", "meta.instrument.channel"),
        "pattern": ("keyword_pchannel.schema", "meta.instrument.p_channel"),
        "core": ("core.schema", "meta.instrument.channel"),
    },
    "coronmsk": {
        "keyword": ("keyword_coronmsk.schema", "meta.instrument.coronagraph"),
        # no p*
        "core": ("core.schema", "meta.instrument.coronagraph"),
    },
    "detector": {
        "keyword": ("referencefile.schema", "meta.instrument.detector"),
        "pattern": ("keyword_pdetector.schema", "meta.instrument.p_detector"),
        "core": ("core.schema", "meta.instrument.detector"),
    },
    "exptype": {
        "keyword": ("keyword_exptype.schema", "meta.exposure.type"),
        "pattern": ("keyword_pexptype.schema", "meta.exposure.p_exptype"),
        "core": ("core.schema", "meta.exposure.type"),
    },
    "filter": {
        "keyword": ("keyword_filter.schema", "meta.instrument.filter"),
        "pattern": ("keyword_pfilter.schema", "meta.instrument.p_filter"),
        "core": ("core.schema", "meta.instrument.filter"),
    },
    "grating": {
        "keyword": ("keyword_grating.schema", "meta.instrument.grating"),
        "pattern": ("keyword_pgrating.schema", "meta.instrument.p_grating"),
        "core": ("core.schema", "meta.instrument.grating"),
    },
    "lampmode": {
        "keyword": ("keyword_lampmode.schema", "meta.instrument.lamp_mode"),
        # no p*
        "core": ("core.schema", "meta.instrument.lamp_mode"),
    },
    # - lampstate -
    # keyword_lampstate.schema.yaml single enum meta.instrument.lamp_state
    # np p*
    # not in core
    "module": {
        "keyword": ("keyword_module.schema", "meta.instrument.module"),
        # no p*
        "core": ("core.schema", "meta.instrument.module"),
    },
    "name": {
        "keyword": ("referencefile.schema", "meta.instrument.name"),
        # no p*
        "core": ("core.schema", "meta.instrument.name"),
    },
    "noutputs": {
        "keyword": ("keyword_noutputs.schema", "meta.exposure.noutputs"),
        # no p*
        "core": ("core.schema", "meta.exposure.noutputs"),
    },
    "pupil": {
        "keyword": ("keyword_pupil.schema", "meta.instrument.pupil"),
        "pattern": ("keyword_ppupil.schema", "meta.instrument.p_pupil"),
        "core": ("core.schema", "meta.instrument.pupil"),
    },
    "readpatt": {
        "keyword": ("keyword_readpatt.schema", "meta.exposure.readpatt"),
        "pattern": ("keyword_preadpatt.schema", "meta.exposure.p_readpatt"),
        "core": ("core.schema", "meta.exposure.readpatt"),
    },
    "subarray": {
        "keyword": ("subarray.schema", "meta.subarray.name"),
        "pattern": ("keyword_psubarray.schema", "meta.subarray.p_subarray"),
        "core": ("core.schema", "meta.subarray.name"),
    },
}

SCHEMA_URI_BASE = "http://stsci.edu/schemas/jwst_datamodel"


def parse_pattern(regex_string):
    return {i.strip("\\ ") for i in regex_string.strip("^(").split(")")[0].split("|")}


def parse_schema_items(subschema):
    # enum -> one enum
    # pattern -> regex
    # anyOf -> multiple enum
    if "enum" in subschema:
        return set(subschema["enum"])
    if "pattern" in subschema:
        return parse_pattern(subschema["pattern"])
    if "anyOf" in subschema:
        return set.union(*[parse_schema_items(i) for i in subschema["anyOf"]])
    raise Exception("Not supported")  # noqa: TRY002


def read_schema_items(name, path):
    schema = asdf.schema.load_schema(f"{SCHEMA_URI_BASE}/{name}")
    # walk schema consuming path
    cursor = schema
    for subpath in path.split("."):
        if "properties" in cursor:
            cursor = cursor["properties"]
        if subpath not in cursor:
            raise Exception("I'm lost...")  # noqa: TRY002
        cursor = cursor[subpath]
    return parse_schema_items(cursor)


@pytest.mark.parametrize("key", comparisons.keys())
def test_schemas_match(key):
    items = {}
    for schema_type, (schema_name, schema_path) in comparisons[key].items():
        items[schema_type] = read_schema_items(schema_name, schema_path)
    # make sure all items match
    ref_values = items.pop("keyword")
    for _, other_values in items.items():
        assert other_values == ref_values
