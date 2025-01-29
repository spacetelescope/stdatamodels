from asdf import schema as mschema
import numpy as np
from numpy.testing import assert_array_almost_equal

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

    array1 = np.random.rand(5, 5)
    array2 = np.random.rand(5, 5)
    array3 = np.random.rand(5, 5)

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
        x.save(path)

    from astropy.io import fits

    with fits.open(path) as hdulist:
        x = set()
        for hdu in hdulist:
            x.add((hdu.header.get("EXTNAME"), hdu.header.get("EXTVER")))

        assert x == set([("FOO", 2), ("FOO", 1), ("ASDF", None), ("DQ", 2), (None, None)])


def test_ami_wcsinfo():
    """
    The ami and wcsinfo schemas contain duplicate information
    since ami products don't otherwise contain a SCI extension.
    This test checks that the schema entries for the duplicated
    information stays in sync.
    """
    wcsinfo_schema = mschema.load_schema("http://stsci.edu/schemas/jwst_datamodel/wcsinfo.schema")
    ami_schema = mschema.load_schema("http://stsci.edu/schemas/jwst_datamodel/ami.schema")
    ami_def = ami_schema["allOf"][1]["properties"]["meta"]["properties"]["ami"]["properties"]
    wcsinfo_def = wcsinfo_schema["properties"]["meta"]["properties"]["wcsinfo"]["properties"]
    for keyword in ("roll_ref", "v3yangle", "vparity"):
        ami = ami_def[keyword]
        wcsinfo = wcsinfo_def[keyword]
        for key in set(ami.keys()) | set(wcsinfo.keys()) - {"fits_hdu"}:
            assert ami[key] == wcsinfo[key]
