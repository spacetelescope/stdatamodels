from asdf import schema as mschema
import numpy as np
from numpy.testing import assert_array_almost_equal

from stdatamodels.jwst._kwtool import dmd
from stdatamodels.jwst.datamodels import JwstDataModel


def test_data_array(tmp_path):
    """Test lots of things"""
    path = str(tmp_path / "data_array.fits")
    data_array_schema = {
        "allOf": [
            mschema.load_schema(
                "http://stsci.edu/schemas/jwst_datamodel/core.schema", resolve_references=True
            ),
            {
                "type": "object",
                "properties": {
                    "arr": {
                        "title": "An array of data",
                        "type": "array",
                        "fits_hdu": ["FOO", "DQ"],
                        "items": {
                            "title": "entry",
                            "type": "object",
                            "properties": {
                                "data": {
                                    "fits_hdu": "FOO",
                                    "default": 0.0,
                                    "max_ndim": 2,
                                    "datatype": "float64",
                                },
                                "dq": {"fits_hdu": "DQ", "default": 1, "datatype": "uint8"},
                            },
                        },
                    }
                },
            },
        ]
    }

    rng = np.random.default_rng(42)
    array1 = rng.random((5, 5))
    array2 = rng.random((5, 5))
    array3 = rng.random((5, 5))

    with JwstDataModel(schema=data_array_schema) as x:
        x.arr.append(x.arr.item())
        x.arr[0].data = array1
        assert len(x.arr) == 1
        x.arr.append(x.arr.item(data=array2))
        assert len(x.arr) == 2
        x.arr.append({})
        assert len(x.arr) == 3
        x.arr[2].data = array3
        del x.arr[1]
        assert len(x.arr) == 2
        x.save(path)

    path2 = str(tmp_path / "data_array2.fits")
    with JwstDataModel(path, schema=data_array_schema) as x:
        assert len(x.arr) == 2
        assert_array_almost_equal(x.arr[0].data, array1)
        assert_array_almost_equal(x.arr[1].data, array3)

        del x.arr[0]
        assert len(x.arr) == 1

        x.arr = []
        assert len(x.arr) == 0
        x.arr.append({"data": np.empty((5, 5))})
        assert len(x.arr) == 1
        x.arr.extend(
            [
                x.arr.item(data=np.empty((5, 5))),
                x.arr.item(data=np.empty((5, 5)), dq=np.empty((5, 5), dtype=np.uint8)),
            ]
        )
        assert len(x.arr) == 3
        del x.arr[1]
        assert len(x.arr) == 2
        x.save(path2)

    from astropy.io import fits

    with fits.open(path2) as hdulist:
        x = set()
        for hdu in hdulist:
            x.add((hdu.header.get("EXTNAME"), hdu.header.get("EXTVER")))

        assert x == {("FOO", 2), ("FOO", 1), ("ASDF", None), ("DQ", 2), (None, None)}


def test_ami_wcsinfo():
    """
    The ami and wcsinfo schemas contain duplicate information
    since ami products don't otherwise contain a SCI extension.
    This test checks that the schema entries for the duplicated
    information stays in sync.
    """
    wcsinfo_schema = mschema.load_schema("http://stsci.edu/schemas/jwst_datamodel/wcsinfo.schema")
    ami_schema = mschema.load_schema("http://stsci.edu/schemas/jwst_datamodel/ami.schema")
    ami_def = ami_schema["allOf"][1]["properties"]["meta"]["properties"]["guidestar"]["properties"]
    wcsinfo_def = wcsinfo_schema["properties"]["meta"]["properties"]["wcsinfo"]["properties"]
    for keyword in ("roll_ref", "v3yangle", "vparity"):
        ami = ami_def["fgs_"+keyword]
        wcsinfo = wcsinfo_def[keyword]
        for key in (set(ami.keys()) | set(wcsinfo.keys())) - {"fits_hdu"}:
            assert ami[key] == wcsinfo[key]


def test_duplicate_keywords():
    """Test that FITS keywords are not used more than once."""
    datamodel_keywords = dmd.load()

    errors = {}
    for keyword, entry in datamodel_keywords.items():
        # this has a duplicate
        if keyword == ("SCI", "SRCTYPE"):
            continue

        # find schema "paths" to each keyword
        paths = {".".join(i["path"]) for i in entry}

        # Remove "items" paths, these are acceptable reuses
        # for things like MultiSlitModel where each slit will
        # have it's own SCI extension when the keywords will
        # be reused.
        paths = [p for p in paths if ".items" not in p]

        if len(paths) > 1:
            errors[keyword] = paths

    assert not errors
