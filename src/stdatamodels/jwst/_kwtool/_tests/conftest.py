import json

import pytest

from stdatamodels.jwst._kwtool import dmd, kwd
from stdatamodels.jwst.datamodels import ImageModel


@pytest.fixture(scope="module")
def fake_kwd_path(tmp_path_factory):
    kwd_path = tmp_path_factory.mktemp("kwd")

    # make 1 top file and 3 ref file
    _top = {
        "type": "object",
        "title": "root",
        "properties": {
            "meta": {
                "title": "FGS Keywords Schema Metadata",
                "type": "object",
                "properties": {
                    "program": {
                        "title": "Programmatic information",
                        "type": "object",
                        "properties": {"$ref": "core.program.schema.json"},
                    },
                    "observation": {
                        "title": "Observation identifiers",
                        "type": "object",
                        "properties": {
                            "allOf": [
                                {
                                    "$ref": "core.observation.schema.json",
                                },
                                {
                                    "$ref": "science.observation.schema.json",
                                },
                            ],
                        },
                    },
                },
            }
        },
    }
    _core_program = {
        "title": {
            "fits_keyword": "TITLE",
            "title": "Proposal title",
            "description": "na",  # actual is longer
            "type": "string",
            "units": "",
            "example": "Cryo2 SIC NIRISS",
            "default_value": "UNKNOWN",
            "source": "Proposal and Planning System (PPS)",
            "sw_source": "PPS:dms_program_view.title",
            "calculation": "",
            "destination": ["ScienceCommon.title", "GuideStar.title"],
            "sql_dtype": "nvarchar(200)",
            "si": "Multiple",
            "mode": "All",
            "level": "1b",
            "fits_hdu": "PRIMARY",
            "section": "Programmatic information",
            "misc": "",
            "comment_line": "/ Program information",
        },
    }
    _core_observation = {
        "obs_id": {
            "fits_keyword": "OBS_IDD",  # modified to trigger compare error
            # modified title to trigger compare error
            "title": "Programmatic observation identifier modified",
            "description": "na",  # actual is longer
            "type": "integer",  # modified to trigger compare error
            "units": "",
            "example": "V80600004001P0000000002101",
            "default_value": "",
            "special_processing": "VALUE_REQUIRED",
            "source": "Science Image Header",
            "sw_source": "",
            "calculation": "",
            "destination": ["ScienceCommon.obs_id", "GuideStar.obs_id"],
            "sql_dtype": "nvarchar(26)",
            "si": "Multiple",
            "mode": "All",
            "level": "1a",
            "fits_hdu": "SCI",  # modified to trigger compare error
            "section": "Observation identifiers",
            "misc": "",
        }
    }
    _science_observation = {
        "engineering_quality": {
            "fits_keyword": "ENG_QUAL",
            "title": "Engineering DB quality indicator",
            "description": "na",  # actual is longer
            "type": "string",
            "enum": ["OK", "SUSPECT", "NOT_IN_DATAMODEL"],  # modified to trigger compare error
            "units": "",
            "example": "OK",
            "default_value": "OK",
            "source": "Science Data Processing (SDP)",
            "sw_source": "",
            "calculation": "",
            "destination": ["ScienceCommon.eng_qual"],
            "sql_dtype": "nvarchar(15)",
            "si": "ALL",
            "mode": "All",
            "level": "1b",
            "fits_hdu": "PRIMARY",
            "section": "Observation identifiers",
            "misc": "",
            "comment_line": "/ Visit information",
        },
    }
    for fn, schema in [
        ("top.fgs.schema.json", _top),
        ("core.program.schema.json", _core_program),
        ("core.observation.schema.json", _core_observation),
        ("science.observation.schema.json", _science_observation),
    ]:
        schema_path = kwd_path / fn
        with open(schema_path, "w") as f:
            json.dump(schema, f)
    return kwd_path


@pytest.fixture(scope="module")
def fake_kwd(fake_kwd_path):
    return kwd.load(fake_kwd_path)


@pytest.fixture(scope="module")
def limit_dmd_models():
    # we can't use the monkeypatch fixture as it's function scoped
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(dmd, "_get_subclasses", lambda k, s: [ImageModel])
        yield


@pytest.fixture(scope="module")
def fake_dmd(limit_dmd_models):
    """Make a fake datamodel dictionary that includes only 1 datamodel: ImageModel."""
    return dmd.load()
