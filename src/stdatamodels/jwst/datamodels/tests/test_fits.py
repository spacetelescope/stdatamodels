from asdf import schema as mschema
from astropy.io import fits
from numpy.testing import assert_array_equal
import numpy as np
import pytest

from stdatamodels.jwst import datamodels
from stdatamodels.jwst.datamodels import ImageModel, JwstDataModel, RampModel, SpecModel, FlatModel


@pytest.fixture
def fits_file(tmp_path):
    path = str(tmp_path / "miri_ramp.fits")
    hdulist = fits.HDUList()
    hdulist.append(fits.PrimaryHDU())
    data = np.zeros((5, 35, 40, 32))
    image = fits.ImageHDU(data=data, name="SCI", ver=1)
    hdulist.append(image)
    header = hdulist[0].header
    # header["DATAMODL"] = "JwstDataModel"
    # Add invalid keyword
    header["INSTRUME"] = "MIRI"
    hdulist.writeto(path)
    return path


def test_from_fits(fits_file):
    with RampModel(fits_file) as dm:
        assert dm.meta.instrument.name == 'MIRI'
        assert dm.shape == (5, 35, 40, 32)


def test_delete(fits_file):
    with JwstDataModel() as dm:
        dm.meta.instrument.name = 'NIRCAM'
        assert dm.meta.instrument.name == 'NIRCAM'
        del dm.meta.instrument.name
        assert dm.meta.instrument.name is None


def test_fits_without_sci():
    schema = {
        "allOf": [
            mschema.load_schema("http://stsci.edu/schemas/jwst_datamodel/core.schema",
                                resolve_references=True),
            {
                "type": "object",
                "properties": {
                    "coeffs": {
                        'max_ndim': 1,
                        'fits_hdu': 'COEFFS',
                        'datatype': 'float32'
                    }
                }
            }
        ]
    }

    hdulist = fits.HDUList()
    hdulist.append(fits.PrimaryHDU())
    hdulist.append(fits.ImageHDU(name='COEFFS', data=np.array([0.0], np.float32)))

    with JwstDataModel(hdulist, schema=schema) as dm:
        assert_array_equal(dm.coeffs, [0.0])


def test_casting():
    with RampModel((5, 5, 10, 10)) as dm:
        total = dm.data.sum()
        dm.data = dm.data + 2
        assert dm.data.sum() > total


def test_resave_duplication_bug(tmp_path):
    """
    An issue in asdf (https://github.com/asdf-format/asdf/issues/1232)
    resulted in duplication of data when a model was read from and then
    written to a fits file. A resave results in array data being written to
    both hdus and as internal blocks within the asdf tree (which is then
    stored in the asdf hdu).
    """
    fn1 = tmp_path / "test1.fits"
    fn2 = tmp_path / "test2.fits"

    arr = np.zeros((1000, 100), dtype='f4')
    m = ImageModel(arr)
    m.save(fn1)

    with datamodels.open(fn1) as m2:
        m2.save(fn2)

    with fits.open(fn1) as ff1, fits.open(fn2) as ff2:
        assert ff1['ASDF'].size == ff2['ASDF'].size


def test_units_roundtrip(tmp_path):
    m = SpecModel()
    # this next line is required for stdatamodels to cast
    # spec_table to a FITS_rec (similar to having data assigned
    # to the attribute)
    m.spec_table = m.spec_table
    m.spec_table.columns['WAVELENGTH'].unit = 'nm'

    fn = tmp_path / "test1.fits"
    m.save(fn)

    m = datamodels.open(fn)
    assert m.spec_table.columns['WAVELENGTH'].unit == 'nm'


def test_flatmodel_dqdef_roundtrip(tmp_path):
    '''Covers an old bug where this roundtrip would fail due to
    a mix-up between signed and unsigned integer data types, leading to flag values
    like 2147483649 instead of 0'''
    flatdata = [(0,1,2),(3,4,5),(6,7,8)]
    flatflags = [(0, 1, "DO_NOT_USE", "Bad pixel. Do not use."),
                 (1, 2, "NON_SCIENCE", "Pixel not on science portion of detector"),
                 (2, 4, "UNRELIABLE_FLAT", "Flat variance large")]
    flatmodel = FlatModel( data=flatdata, dq_def=flatflags )

    fn = tmp_path / "test_flat.fits"
    flatmodel.save(fn)

    with datamodels.open(fn) as flatmodel2:
        assert np.allclose(flatmodel2.data, flatdata)
        for i, flag in enumerate(flatmodel2.dq_def):
            for j in range(2):
                # tuples do not directly assert True because datamodels.open() returns np.int32
                # which is not technically of type int. So must check their equality directly
                assert flag[j] == flatflags[i][j]
