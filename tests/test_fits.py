import pytest
from astropy.io import fits
import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_equal
import asdf.schema
from jsonschema import ValidationError

from stdatamodels import DataModel
from stdatamodels import fits_support

from models import FitsModel, PureFitsModel


def records_equal(a, b):
    a = a.item()
    b = b.item()
    a_size = len(a)
    b_size = len(b)
    equal = a_size == b_size
    for i in range(a_size):
        if not equal: break
        equal = a[i] == b[i]
    return equal


def test_from_new_hdulist():
    with pytest.raises(AttributeError):
        from astropy.io import fits
        hdulist = fits.HDUList()
        with FitsModel(hdulist) as dm:
            dm.foo


def test_from_new_hdulist2():
    from astropy.io import fits
    hdulist = fits.HDUList()
    data = np.empty((50, 50), dtype=np.float32)
    primary = fits.PrimaryHDU()
    hdulist.append(primary)
    science = fits.ImageHDU(data=data, name='SCI')
    hdulist.append(science)
    with FitsModel(hdulist) as dm:
        dq = dm.dq
        assert dq is not None


def test_setting_arrays_on_fits():
    from astropy.io import fits
    hdulist = fits.HDUList()
    data = np.empty((50, 50), dtype=np.float32)
    primary = fits.PrimaryHDU()
    hdulist.append(primary)
    science = fits.ImageHDU(data=data, name='SCI')
    hdulist.append(science)
    with FitsModel(hdulist) as dm:
        dm.data = np.empty((50, 50), dtype=np.float32)
        dm.dq = np.empty((10,), dtype=np.uint32)


def test_from_scratch(tmp_path):
    file_path = tmp_path/"test.fits"

    with FitsModel((50, 50)) as dm:
        data = np.asarray(np.random.rand(50, 50), np.float32)
        dm.data[...] = data

        dm.meta.telescope = "EYEGLASSES"

        dm.to_fits(file_path)

        with FitsModel.from_fits(file_path) as dm2:
            assert dm2.shape == (50, 50)
            assert dm2.meta.telescope == "EYEGLASSES"
            assert dm2.dq.dtype.name == 'uint32'
            assert np.all(dm2.data == data)


def test_extra_fits(tmp_path):
    file_path = tmp_path/"test.fits"

    with FitsModel() as dm:
        dm.save(file_path)

    with fits.open(file_path) as hdul:
        hdul[0].header["FOO"] = "BAR"
        hdul.writeto(file_path, overwrite=True)

    with DataModel(file_path) as dm:
        assert any(h for h in dm.extra_fits.PRIMARY.header if h == ["FOO", "BAR", ""])


def test_hdu_order(tmp_path):
    file_path = tmp_path/"test.fits"

    with FitsModel(data=np.array([[0.0]]),
                   dq=np.array([[0.0]]),
                   err=np.array([[0.0]])) as dm:
        dm.save(file_path)

    with fits.open(file_path, memmap=False) as hdulist:
        assert hdulist[1].header['EXTNAME'] == 'SCI'
        assert hdulist[2].header['EXTNAME'] == 'DQ'
        assert hdulist[3].header['EXTNAME'] == 'ERR'


def test_fits_comments(tmp_path):
    file_path = tmp_path/"test.fits"

    with FitsModel() as dm:
        dm.meta.origin = "STScI"
        dm.save(file_path)

    from astropy.io import fits
    with fits.open(file_path, memmap=False) as hdulist:
        assert any(c for c in hdulist[0].header.cards if c[-1] == "Organization responsible for creating file")


def test_metadata_doesnt_override(tmp_path):
    file_path = tmp_path/"test.fits"

    with FitsModel() as dm:
        dm.save(file_path)

    from astropy.io import fits
    with fits.open(file_path, mode='update', memmap=False) as hdulist:
        hdulist[0].header['ORIGIN'] = 'UNDER THE COUCH'

    with FitsModel(file_path) as dm:
        assert dm.meta.origin == 'UNDER THE COUCH'


def test_non_contiguous_array(tmp_path):
    file_path = tmp_path/"test.fits"

    data = np.arange(60, dtype=np.float32).reshape(5, 12)
    err = data[::-1, ::2]

    with FitsModel() as dm:
        dm.data = data
        dm.err = err
        dm.save(file_path)

    with FitsModel(file_path) as dm:
        assert_array_equal(dm.data, data)
        assert_array_equal(dm.err, err)


def test_table_with_metadata(tmp_path):
    file_path = tmp_path/"test.fits"

    schema = {
        "allOf": [
            asdf.schema.load_schema("http://example.com/schemas/core_metadata", resolve_references=True),
            {"type": "object",
            "properties": {
                "flux_table": {
                    "title": "Photometric flux conversion table",
                    "fits_hdu": "FLUX",
                    "datatype":
                    [
                        {"name": "parameter", "datatype": ['ascii', 7]},
                        {"name": "factor", "datatype": "float64"},
                        {"name": "uncertainty", "datatype": "float64"}
                    ]
                },
                "meta": {
                    "type": "object",
                    "properties": {
                        "fluxinfo": {
                            "title": "Information about the flux conversion",
                            "type": "object",
                            "properties": {
                                "exposure": {
                                    "title": "Description of exposure analyzed",
                                    "type": "string",
                                    "fits_hdu": "FLUX",
                                    "fits_keyword": "FLUXEXP"
                                }
                            }
                        }
                    }
                }
            }
         }
        ]
    }

    class FluxModel(DataModel):
        def __init__(self, init=None, flux_table=None, **kwargs):
            super().__init__(init=init, schema=schema, **kwargs)

            if flux_table is not None:
                self.flux_table = flux_table

    flux_im = [
        ('F560W', 1.0e-5, 1.0e-7),
        ('F770W', 1.1e-5, 1.6e-7),
        ]
    with FluxModel(flux_table=flux_im) as datamodel:
        datamodel.meta.fluxinfo.exposure = 'Exposure info'
        datamodel.save(file_path, overwrite=True)
        del datamodel

    from astropy.io import fits
    with fits.open(file_path, memmap=False) as hdulist:
        assert len(hdulist) == 3
        assert isinstance(hdulist[1], fits.BinTableHDU)
        assert hdulist[1].name == 'FLUX'
        assert hdulist[2].name == 'ASDF'


def test_replace_table(tmp_path):
    file_path = tmp_path/"test.fits"
    file_path2 = tmp_path/"test2.fits"

    schema_narrow = {
        "allOf": [
            asdf.schema.load_schema("http://example.com/schemas/core_metadata", resolve_references=True),
            {
                "type": "object",
                "properties": {
                    "data": {
                        "title": "relative sensitivity table",
                        "fits_hdu": "RELSENS",
                        "datatype": [
                            {"name": "TYPE", "datatype": ["ascii", 16]},
                            {"name": "T_OFFSET", "datatype": "float32"},
                            {"name": "DECAY_PEAK", "datatype": "float32"},
                            {"name": "DECAY_FREQ", "datatype": "float32"},
                            {"name": "TAU", "datatype": "float32"}
                        ]
                    }
                }
            }
        ]
    }

    schema_wide = {
        "allOf": [
            asdf.schema.load_schema("http://example.com/schemas/core_metadata", resolve_references=True),
            {
                "type": "object",
                "properties": {
                    "data": {
                        "title": "relative sensitivity table",
                        "fits_hdu": "RELSENS",
                        "datatype": [
                            {"name": "TYPE", "datatype": ["ascii", 16]},
                            {"name": "T_OFFSET", "datatype": "float64"},
                            {"name": "DECAY_PEAK", "datatype": "float64"},
                            {"name": "DECAY_FREQ", "datatype": "float64"},
                            {"name": "TAU", "datatype": "float64"}
                        ]
                    }
                }
            }
        ]
    }

    x = np.array([("string", 1., 2., 3., 4.)],
                 dtype=[('TYPE', 'S16'),
                        ('T_OFFSET', np.float32),
                        ('DECAY_PEAK', np.float32),
                        ('DECAY_FREQ', np.float32),
                        ('TAU', np.float32)])

    m = DataModel(schema=schema_narrow)
    m.data = x
    m.to_fits(file_path, overwrite=True)

    with fits.open(file_path, memmap=False) as hdulist:
        assert records_equal(x, np.asarray(hdulist[1].data))
        assert hdulist[1].data.dtype[1].str == '>f4'
        assert hdulist[1].header['TFORM2'] == 'E'

    with DataModel(file_path, schema=schema_wide) as m:
        m.to_fits(file_path2, overwrite=True)

    with fits.open(file_path2, memmap=False) as hdulist:
        assert records_equal(x, np.asarray(hdulist[1].data))
        assert hdulist[1].data.dtype[1].str == '>f8'
        assert hdulist[1].header['TFORM2'] == 'D'


def test_table_with_unsigned_int(tmp_path):
    file_path = tmp_path/"test.fits"

    schema = {
        'title': 'Test data model',
        '$schema': 'http://stsci.edu/schemas/fits-schema/fits-schema',
        'type': 'object',
        'properties': {
            'meta': {
                'type': 'object',
                'properties': {}
            },
            'test_table': {
                'title': 'Test table',
                'fits_hdu': 'TESTTABL',
                'datatype': [
                    {'name': 'FLOAT64_COL', 'datatype': 'float64'},
                    {'name': 'UINT32_COL', 'datatype': 'uint32'}
                ]
            }
        }
    }

    with DataModel(schema=schema) as dm:

        float64_info = np.finfo(np.float64)
        float64_arr = np.random.uniform(size=(10,))
        float64_arr[0] = float64_info.min
        float64_arr[-1] = float64_info.max

        uint32_info = np.iinfo(np.uint32)
        uint32_arr = np.random.randint(uint32_info.min, uint32_info.max + 1, size=(10,), dtype=np.uint32)
        uint32_arr[0] = uint32_info.min
        uint32_arr[-1] = uint32_info.max

        test_table = np.array(list(zip(float64_arr, uint32_arr)), dtype=dm.test_table.dtype)

        def assert_table_correct(model):
            for idx, (col_name, col_data) in enumerate([('float64_col', float64_arr), ('uint32_col', uint32_arr)]):
                # The table dtype and field dtype are stored separately, and may not
                # necessarily agree.
                assert np.can_cast(model.test_table.dtype[idx], col_data.dtype, 'equiv')
                assert np.can_cast(model.test_table.field(col_name).dtype, col_data.dtype, 'equiv')
                assert np.array_equal(model.test_table.field(col_name), col_data)

        # The datamodel casts our array to FITS_rec on assignment, so here we're
        # checking that the data survived the casting.
        dm.test_table = test_table
        assert_table_correct(dm)

        # Confirm that saving the table (and converting the uint32 values to signed int w/TZEROn)
        # doesn't mangle the data.
        dm.save(file_path)
        assert_table_correct(dm)

    # Confirm that the data loads from the file intact (converting the signed ints back to
    # the appropriate uint32 values).
    with DataModel(file_path, schema=schema) as dm2:
        assert_table_correct(dm2)


def test_metadata_from_fits(tmp_path):
    file_path = tmp_path/"test.fits"
    file_path2 = tmp_path/"test2.fits"

    mask = np.array([[0, 1], [2, 3]])
    fits.ImageHDU(data=mask, name='DQ').writeto(file_path)
    with FitsModel(file_path) as dm:
        dm.save(file_path2)

    with fits.open(file_path2, memmap=False) as hdulist:
        assert hdulist[2].name == 'ASDF'


def test_get_short_doc():
    assert fits_support.get_short_doc({}) == ""
    assert fits_support.get_short_doc({"title": "Some schema title."}) == "Some schema title."
    assert fits_support.get_short_doc({
        "title": "Some schema title.\nWhoops, another line."
    }) == "Some schema title."
    assert fits_support.get_short_doc({
        "title": "Some schema title.",
        "description": "Some schema description.",
    }) == "Some schema title."
    assert fits_support.get_short_doc({
        "description": "Some schema description.",
    }) == "Some schema description."
    assert fits_support.get_short_doc({
        "description": "Some schema description.\nWhoops, another line.",
    }) == "Some schema description."


def test_ensure_ascii():
    for inp in [b"ABCDEFG", "ABCDEFG"]:
        fits_support.ensure_ascii(inp) == "ABCDEFG"


@pytest.mark.parametrize(
    'which_file, skip_fits_update, expected_exp_type',
    [
        ('just_fits', None,  'FGS_DARK'),
        ('just_fits', False, 'FGS_DARK'),
        ('just_fits', True,  'FGS_DARK'),
        ('model',     None,  'FGS_DARK'),
        ('model',     False, 'FGS_DARK'),
        ('model',     True,  'NRC_IMAGE')
    ]
)
@pytest.mark.parametrize(
    'use_env',
    [False, True]
)
def test_skip_fits_update(tmp_path,
                          monkeypatch,
                          use_env,
                          which_file,
                          skip_fits_update,
                          expected_exp_type):
    """Test skip_fits_update setting"""
    file_path = tmp_path/"test.fits"

    # Setup the FITS file, modifying a header value
    if which_file == "just_fits":
        primary_hdu = fits.PrimaryHDU()
        primary_hdu.header['EXP_TYPE'] = 'NRC_IMAGE'
        primary_hdu.header['DATAMODL'] = "FitsModel"
        hduls = fits.HDUList([primary_hdu])
        hduls.writeto(file_path)
    else:
        model = FitsModel()
        model.meta.exposure.type = 'NRC_IMAGE'
        model.save(file_path)

    with fits.open(file_path) as hduls:
        hduls[0].header['EXP_TYPE'] = 'FGS_DARK'

        if use_env:
            if skip_fits_update is not None:
                monkeypatch.setenv("SKIP_FITS_UPDATE", str(skip_fits_update))
                skip_fits_update = None

        model = FitsModel(hduls, skip_fits_update=skip_fits_update)
        assert model.meta.exposure.type == expected_exp_type


def test_from_hdulist(tmp_path):
    file_path = tmp_path/"test.fits"

    with FitsModel() as dm:
        dm.save(file_path)

    with fits.open(file_path, memmap=False) as hdulist:
        with FitsModel(hdulist) as dm:
            dm.data
        assert not hdulist.fileinfo(0)['file'].closed


def test_open_fits_model_s3(s3_root_dir):
    path = str(s3_root_dir.join("test.fits"))
    with DataModel() as dm:
        dm.save(path)

    model = DataModel("s3://test-s3-data/test.fits")
    assert isinstance(model, DataModel)


def test_data_array(tmp_path):
    file_path = tmp_path/"test.fits"
    file_path2 = tmp_path/"test2.fits"

    data_array_schema = {
        "allOf": [
            asdf.schema.load_schema("http://example.com/schemas/core_metadata", resolve_references=True),
            {
                "type": "object",
                "properties": {
                    "arr": {
                        'title': 'An array of data',
                        'type': 'array',
                        "fits_hdu": ["FOO", "DQ"],

                        "items": {
                            "title": "entry",
                            "type": "object",
                            "properties": {
                                "data": {
                                    "fits_hdu": "FOO",
                                    "default": 0.0,
                                    "max_ndim": 2,
                                    "datatype": "float64"
                                },
                                "dq": {
                                    "fits_hdu": "DQ",
                                    "default": 1,
                                    "datatype": "uint8"
                                },
                            }
                        }
                    }
                }
            }
        ]
    }

    array1 = np.random.rand(5, 5)
    array2 = np.random.rand(5, 5)
    array3 = np.random.rand(5, 5)

    with DataModel(schema=data_array_schema) as x:
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
        x.to_fits(file_path)

    with DataModel(file_path, schema=data_array_schema) as x:
        assert len(x.arr) == 2
        assert_array_almost_equal(x.arr[0].data, array1)
        assert_array_almost_equal(x.arr[1].data, array3)

        del x.arr[0]
        assert len(x.arr) == 1

        x.arr = []
        assert len(x.arr) == 0
        x.arr.append({'data': np.empty((5, 5))})
        assert len(x.arr) == 1
        x.arr.extend([
            x.arr.item(data=np.empty((5, 5))),
            x.arr.item(data=np.empty((5, 5)),
                       dq=np.empty((5, 5), dtype=np.uint8))])
        assert len(x.arr) == 3
        del x.arr[1]
        assert len(x.arr) == 2
        x.to_fits(file_path2, overwrite=True)

    with fits.open(file_path2) as hdulist:
        x = set()
        for hdu in hdulist:
            x.add((hdu.header.get('EXTNAME'),
                   hdu.header.get('EXTVER')))

        assert x == set(
            [('FOO', 2), ('FOO', 1), ('ASDF', None), ('DQ', 2),
             (None, None)])


@pytest.mark.parametrize("keyword,result", [
    ("BZERO", True),
    ("TFORM53", True),
    ("SIMPLE", True),
    ("EXTEND", True),
    ("INSTRUME", False),
])
def test_is_builtin_fits_keyword(keyword, result):
    assert fits_support.is_builtin_fits_keyword(keyword) is result


def test_no_asdf_extension(tmp_path):
    """Verify an ASDF extension is not written out"""
    path = tmp_path / "no_asdf.fits"

    with PureFitsModel((5, 5)) as m:
        m.save(path)

    with fits.open(path, memmap=False) as hdulist:
        assert "ASDF" not in hdulist


def test_no_asdf_extension_extra_fits(tmp_path):
    path = tmp_path / "no_asdf.fits"

    extra_fits = {
        'ASDF': {
            'header': [
                ['CHECKSUM', '9kbGAkbF9kbFAkbF', 'HDU checksum updated 2018-03-07T08:48:27'],
                ['DATASUM', '136453353', 'data unit checksum updated 2018-03-07T08:48:27']
            ]
        }
    }

    with PureFitsModel((5, 5)) as m:
        m.extra_fits = {}
        m.extra_fits.instance.update(extra_fits)
        assert "ASDF" in m.extra_fits.instance
        assert "CHECKSUM" in m.extra_fits.ASDF.header[0]
        assert "DATASUM" in m.extra_fits.ASDF.header[1]
        m.save(path)

    with fits.open(path, memmap=False) as hdulist:
        assert "ASDF" not in hdulist

    with PureFitsModel(path) as m:
        with pytest.raises(AttributeError):
            m.extra_fits


def test_ndarray_validation(tmp_path):
    file_path = tmp_path / "test.fits"

    # Wrong dtype
    hdu = fits.ImageHDU(data=np.ones((4, 4), dtype=np.float64), name="SCI")
    hdul = fits.HDUList([fits.PrimaryHDU(), hdu])
    hdul.writeto(file_path)

    # Should be able to cast
    with FitsModel(file_path, strict_validation=True, validate_arrays=True) as model:
        model.validate()

    # But raise an error when casting is disabled
    with pytest.raises(ValidationError, match="Array datatype 'float64' is not compatible with 'float32'"):
        with FitsModel(file_path, strict_validation=True, cast_fits_arrays=False, validate_arrays=True) as model:
            model.validate()

    # Wrong dimensions
    hdu = fits.ImageHDU(data=np.ones((4,), dtype=np.float64), name="SCI")
    hdul = fits.HDUList([fits.PrimaryHDU(), hdu])
    hdul.writeto(file_path, overwrite=True)

    # Can't cast this problem away
    with pytest.raises(ValueError, match="Array has wrong number of dimensions"):
        with FitsModel(file_path, strict_validation=True, validate_arrays=True) as model:
            model.validate()

    # Should also be caught by validation
    with pytest.raises(ValidationError, match="Wrong number of dimensions: Expected 2, got 1"):
        with FitsModel(file_path, strict_validation=True, cast_fits_arrays=False, validate_arrays=True) as model:
            model.validate()


def test_resave_duplication_bug(tmp_path):
    """
    An issue in asdf (https://github.com/asdf-format/asdf/issues/1232)
    resulted in duplication of data when a model was read from and then
    written to a fits file.
    """
    fn1 = tmp_path / "test1.fits"
    fn2 = tmp_path / "test2.fits"

    arr = np.zeros((1000, 100), dtype='f4')
    m = FitsModel(arr)
    m.save(fn1)

    m2 = FitsModel.from_fits(fn1)
    m2.save(fn2)

    with fits.open(fn1) as ff1, fits.open(fn2) as ff2:
        assert ff1['ASDF'].size == ff2['ASDF'].size
