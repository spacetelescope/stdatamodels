import contextlib
import os
import warnings

from asdf.exceptions import ValidationError
from astropy.io import fits
from astropy.table import Table
from astropy.time import Time
from numpy.lib.recfunctions import merge_arrays
from numpy.testing import assert_allclose, assert_array_equal
import numpy as np
from numpy.lib.recfunctions import drop_fields
import pytest

from stdatamodels.jwst.datamodels import (JwstDataModel, ImageModel, MaskModel, AsnModel,
                                          MultiSlitModel, SlitModel,
                                          NirspecFlatModel, NirspecQuadFlatModel,
                                          SlitDataModel, IFUImageModel, ABVegaOffsetModel)
from stdatamodels.jwst import datamodels
from stdatamodels.jwst.datamodels import _defined_models as defined_models

ROOT_DIR = os.path.join(os.path.dirname(__file__), 'data')
FITS_FILE = os.path.join(ROOT_DIR, 'test.fits')
ASN_FILE = os.path.join(ROOT_DIR, 'association.json')


@pytest.fixture
def make_models(tmp_path):
    """Create basic models

    Returns
    -------
    path_just_fits, path_model : (str, str)
        `path_just_fits` is a FITS file of `JwstDataModel` without the ASDF extension.
        `path_model` is a FITS file of `JwstDataModel` with the ASDF extension.
    """
    path_just_fits = tmp_path / 'just_fits.fits'
    path_model = tmp_path / 'model.fits'
    primary_hdu = fits.PrimaryHDU()
    primary_hdu.header['EXP_TYPE'] = 'NRC_IMAGE'
    primary_hdu.header['DATAMODL'] = "JwstDataModel"
    hduls = fits.HDUList([primary_hdu])
    hduls.writeto(path_just_fits)
    model = JwstDataModel(hduls)
    model.save(path_model)
    return {
        'just_fits': path_just_fits,
        'model': path_model
    }


def test_init_from_pathlib(tmp_path):
    """Test initializing model from a Path object"""
    path = tmp_path / "pathlib.fits"
    model1 = datamodels.ImageModel((50, 50))
    model1.save(path)
    with datamodels.open(path) as model:
        # Test is basically, did we open the model?
        assert isinstance(model, ImageModel)


@pytest.mark.parametrize('which_file, skip_fits_update, expected_exp_type',
                         [
                             ('just_fits', None, 'FGS_DARK'),
                             ('just_fits', False, 'FGS_DARK'),
                             ('just_fits', True, 'FGS_DARK'),
                             ('model', None, 'FGS_DARK'),
                             ('model', False, 'FGS_DARK'),
                             ('model', True, 'NRC_IMAGE')
                         ]
                         )
@pytest.mark.parametrize('use_env', [False, True])
def test_skip_fits_update(jail_environ,
                          use_env,
                          make_models,
                          which_file,
                          skip_fits_update,
                          expected_exp_type):
    """Test skip_fits_update setting"""
    # Setup the FITS file, modifying a header value
    path = make_models[which_file]
    with fits.open(path) as hduls:
        hduls[0].header['exp_type'] = 'FGS_DARK'

        # Decide how to skip. If using the environmental,
        # set that and pass None to the open function.
        try:
            del os.environ['SKIP_FITS_UPDATE']
        except KeyError:
            # No need to worry, environmental doesn't exist anyways
            pass

        if skip_fits_update is not None:
            ctx = pytest.warns(DeprecationWarning, match="skip_fits_update is deprecated")
        else:
            ctx = contextlib.nullcontext()

        if use_env:
            if skip_fits_update is not None:
                os.environ['SKIP_FITS_UPDATE'] = str(skip_fits_update)
                skip_fits_update = None

        with ctx:
            with datamodels.open(hduls, skip_fits_update=skip_fits_update) as model:
                assert model.meta.exposure.type == expected_exp_type


def test_asnmodel_table_size_zero():
    with AsnModel() as dm:
        assert len(dm.asn_table) == 0


def test_imagemodel():
    shape = (10, 10)
    with ImageModel(shape) as dm:
        assert dm.data.shape == shape
        assert dm.err.shape == shape
        assert dm.dq.shape == shape
        assert dm.data.mean() == 0.0
        assert dm.err.mean() == 0.0
        assert dm.dq.mean() == 0.0
        assert dm.zeroframe.shape == shape
        assert dm.area.shape == shape
        assert dm.pathloss_point.shape == shape
        assert dm.pathloss_uniform.shape == shape


def test_model_with_nonstandard_primary_array():
    class NonstandardPrimaryArrayModel(JwstDataModel):
        schema_url = os.path.join(ROOT_DIR, "nonstandard_primary_array.schema.yaml")

        # The wavelength array is the primary array.
        # Try commenting this function out and the problem goes away.
        def get_primary_array_name(self):
            return 'wavelength'

    m = NonstandardPrimaryArrayModel((10,))
    assert 'wavelength' in list(m.keys())
    assert m.wavelength.sum() == 0


def test_image_with_extra_keyword_to_multislit(tmp_path):
    path = tmp_path / "extra_keyword_image.fits"
    path2 = tmp_path / "extra_keyword_multislit.fits"
    with ImageModel((32, 32)) as im:
        im.save(path)

    from astropy.io import fits
    with fits.open(path, mode="update", memmap=False) as hdulist:
        hdulist[1].header['BUNIT'] = 'x'

    with ImageModel(path) as im:
        with MultiSlitModel() as ms:
            ms.update(im)
            for i in range(3):
                ms.slits.append(ImageModel((4, 4)))
            assert len(ms.slits) == 3

            ms.save(path2)

    with MultiSlitModel(path2) as ms:
        assert len(ms.slits) == 3
        for slit in ms.slits:
            assert slit.data.shape == (4, 4)


@pytest.fixture
def datamodel_for_update(tmp_path):
    """Provide ImageModel with one keyword each defined in PRIMARY and SCI
    extensions from the schema, and one each not in the schema"""
    path = tmp_path / "old.fits"
    with ImageModel((5, 5)) as im:
        # Add schema keywords, one to each extension
        im.meta.telescope = "JWST"
        im.meta.wcsinfo.crval1 = 5

        im.save(path)
    # Add non-schema keywords that will get dumped in the extra_fits attribute
    with fits.open(path, mode="update") as hdulist:
        hdulist["PRIMARY"].header["FOO"] = "BAR"
        hdulist["SCI"].header["BAZ"] = "BUZ"

    return path


@pytest.mark.parametrize("extra_fits", [True, False])
@pytest.mark.parametrize("only", [None, "PRIMARY", "SCI"])
def test_update_from_datamodel(tmp_path, datamodel_for_update, only, extra_fits):
    """Test update method does not update from extra_fits unless asked"""
    path = tmp_path / "new.fits"
    with ImageModel((5, 5)) as newim:
        with ImageModel(datamodel_for_update) as oldim:

            # Verify the fixture returns keywords we expect
            assert oldim.meta.telescope == "JWST"
            assert oldim.meta.wcsinfo.crval1 == 5
            assert oldim.extra_fits.PRIMARY.header == [['FOO', 'BAR', '']]
            assert oldim.extra_fits.SCI.header == [['BAZ', 'BUZ', '']]

            newim.update(oldim, only=only, extra_fits=extra_fits)
        newim.save(path)

    with fits.open(path) as hdulist:
        if extra_fits:
            if only == "PRIMARY":
                assert "TELESCOP" in hdulist["PRIMARY"].header
                assert "CRVAL1" not in hdulist["SCI"].header
                assert "FOO" in hdulist["PRIMARY"].header
                assert "BAZ" not in hdulist["SCI"].header
            elif only == "SCI":
                assert "TELESCOP" not in hdulist["PRIMARY"].header
                assert "CRVAL1" in hdulist["SCI"].header
                assert "FOO" not in hdulist["PRIMARY"].header
                assert "BAZ" in hdulist["SCI"].header
            else:
                assert "TELESCOP" in hdulist["PRIMARY"].header
                assert "CRVAL1" in hdulist["SCI"].header
                assert "FOO" in hdulist["PRIMARY"].header
                assert "BAZ" in hdulist["SCI"].header

        else:
            assert "FOO" not in hdulist["PRIMARY"].header
            assert "BAZ" not in hdulist["SCI"].header

            if only == "PRIMARY":
                assert "TELESCOP" in hdulist["PRIMARY"].header
                assert "CRVAL1" not in hdulist["SCI"].header
            elif only == "SCI":
                assert "TELESCOP" not in hdulist["PRIMARY"].header
                assert "CRVAL1" in hdulist["SCI"].header
            else:
                assert "TELESCOP" in hdulist["PRIMARY"].header
                assert "CRVAL1" in hdulist["SCI"].header


def test_update_from_dict(tmp_path):
    """Test update method from a dictionary"""
    path = tmp_path / "update.fits"
    with ImageModel((5, 5)) as im:
        update_dict = dict(meta=dict(telescope="JWST", wcsinfo=dict(crval1=5)))
        im.update(update_dict)
        im.save(path)

    with fits.open(path) as hdulist:
        assert "TELESCOP" in hdulist[0].header
        assert "CRVAL1" in hdulist[1].header


def test_mask_model():
    with MaskModel((10, 10)) as dm:
        assert dm.dq.dtype == np.uint32


def test_multislit_model():
    data = np.arange(24).reshape((6, 4))
    err = np.arange(24).reshape((6, 4)) + 2
    wav = np.arange(24).reshape((6, 4)) + 3
    dq = np.arange(24).reshape((6, 4)) + 1
    s0 = SlitDataModel(data=data, err=err, dq=dq, wavelength=wav)
    s1 = SlitDataModel(data=data + 1, err=err + 1, dq=dq + 1, wavelength=wav + 1)

    ms = MultiSlitModel()
    ms.slits.append(s0)
    ms.slits.append(s1)
    ms.meta.instrument.name = 'NIRSPEC'
    ms.meta.exposure.type = 'NRS_IMAGE'
    slit1 = ms[1]
    assert isinstance(slit1, SlitModel)
    assert slit1.meta.instrument.name == 'NIRSPEC'
    assert slit1.meta.exposure.type == 'NRS_IMAGE'
    assert_allclose(slit1.data, data + 1)


def test_slit_from_image():
    data = np.arange(24, dtype=np.float32).reshape((6, 4))
    im = ImageModel(data=data, err=data / 2, dq=data)
    im.meta.instrument.name = "MIRI"
    slit_dm = SlitDataModel(im)
    assert_allclose(im.data, slit_dm.data)
    assert hasattr(slit_dm, 'wavelength')
    # this should be enabled after gwcs starts using non-coordinate inputs
    # assert not hasattr(slit_dm, 'meta')

    slit = SlitModel(im)
    assert_allclose(im.data, slit.data)
    assert_allclose(im.err, slit.err)
    assert hasattr(slit, 'wavelength')
    assert slit.meta.instrument.name == "MIRI"

    im = ImageModel(slit)
    assert type(im) == ImageModel

    im = ImageModel(slit_dm)
    assert type(im) == ImageModel


def test_ifuimage():
    data = np.arange(24).reshape((6, 4))
    im = ImageModel(data=data, err=data / 2, dq=data)
    ifuimage = IFUImageModel(im)
    assert_array_equal(im.data, ifuimage.data)
    assert_array_equal(im.err, ifuimage.err)
    assert_array_equal(im.dq, ifuimage.dq)

    im = ImageModel(ifuimage)
    assert type(im) == ImageModel


def test_abvega_offset_model():
    path = os.path.join(ROOT_DIR, 'nircam_abvega_offset.asdf')
    with ABVegaOffsetModel(path) as model:
        assert isinstance(model, ABVegaOffsetModel)
        assert hasattr(model, 'abvega_offset')
        assert isinstance(model.abvega_offset, Table)
        assert model.abvega_offset.colnames == ['filter', 'pupil', 'abvega_offset']
        model.validate()


@pytest.mark.parametrize("model", [v for v in defined_models.values()])
def test_all_datamodels_init(model):
    """
    Test that all current datamodels can be initialized.
    """
    model()


def test_meta_date_management(tmp_path):
    model = JwstDataModel({"meta": {"date": "2000-01-01T00:00:00.000"}})
    assert model.meta.date == "2000-01-01T00:00:00.000"
    model.save(str(tmp_path / "test.fits"))
    assert abs((Time.now() - Time(model.meta.date)).value) < 1.0

    model = JwstDataModel()
    assert abs((Time.now() - Time(model.meta.date)).value) < 1.0


def test_ramp_model_zero_frame_open_file(tmpdir):
    """
    Ensures opening a FITS with ZEROFRAME results in a good ZEROFRAME.
    """
    nints, ngroups, nrows, ncols = 2, 10, 5, 5
    dims = nints, ngroups, nrows, ncols
    zdims = (nints, nrows, ncols)

    dbase = 1000.
    zbase = dbase * .75

    data = np.ones(dims, dtype=float) * dbase
    err = np.zeros(dims, dtype=float)
    pdq = np.zeros(dims[-2:], dtype=np.uint32)
    gdq = np.zeros(dims, dtype=np.uint8)

    # Test default exposure zero_frame
    ramp = datamodels.RampModel(data=data, err=err, pixeldq=pdq, groupdq=gdq)

    ramp.meta.exposure.zero_frame = True
    ramp.zeroframe = np.ones(zdims, dtype=ramp.data.dtype) * zbase

    ofile = "my_temp_ramp.fits"
    fname = os.path.join(tmpdir, ofile)
    ramp.save(fname)

    # Check opening a file doesn't change the dimensions
    with datamodels.RampModel(fname) as ramp1:
        assert ramp1.zeroframe.shape == ramp.zeroframe.shape
        zframe0 = ramp.zeroframe
        zframe1 = ramp1.zeroframe
        np.testing.assert_allclose(zframe0, zframe1, 1.e-5)


def test_ramp_model_zero_frame_by_dimensions():
    """
    Ensures creating a RampModel by dimensions results in the correct
    dimensions for ZEROFRAME.
    """
    nints, ngroups, nrows, ncols = 2, 10, 5, 5
    dims = (nints, ngroups, nrows, ncols)
    zdims = (nints, nrows, ncols)

    with datamodels.RampModel(dims) as ramp:
        assert ramp.zeroframe.shape == zdims


@pytest.fixture
def oifits_ami_model():
    m = datamodels.AmiOIModel()
    m.meta.telescope = 'JWST'
    m.meta.origin = 'STScI'
    m.meta.instrument.name = 'NIRISS'
    m.meta.program.pi_name = 'UNKNOWN'
    m.meta.target.proposer_name = 'AB DOR'
    m.meta.observation.date = '2022-06-05'
    m.meta.oifits.array_name = 'g7s6'
    m.meta.oifits.instrument_mode = 'NRM'

    m.array = [
        (
            'A1', 'A1', 1, 0.,
            [ 2.64000000e+00, -1.61653377e-16,  0.00000000e+00], 5.04539835,
            'RADIUS', [ 2.60973996, -0.39856915]
        ),
        (
            'A2', 'A2', 2, 0.,
            [ 1.39996111e-16,  2.28631000e+00,  0.00000000e+00], 5.04539835,
            'RADIUS', [-0.34517145, -2.260104  ]
        ),
        (
            'A3', 'A3', 3, 0.,
            [ 1.32000010e+00, -2.28631000e+00,  0.00000000e+00], 5.04539835,
            'RADIUS', [ 1.65004153,  2.06081941]
        )
    ]
    m.target = [(
        1, 'AB DOR', 82.18704833, -65.44869139, 2000., 0., 0., 0., 'UNKNOWN',
        'OPTICAL', 29.15, 164.421, 0., 0., 65.3199, 0., 'K0V')]
    m.t3 = [
        (
            1, 0., 59735., 0.3772, 0.71125417, 0.73752607, -1.81575411, 0.73752607,
            1.86153485, 2.9549114, -4.32092341, -1.99521297, [1, 2, 3],  0
        ),
    ]
    m.vis = [
        (
            1, 0., 59735., 0.3772, 0.84231787, 0.00669874, -10.57082496, 1.89098664,
            1.86153485,  2.9549114 , [1, 2],  0
        ),
        (
            1, 0., 59735., 0.3772, 0.91448467, 0.00621287, -22.26334374, 1.27637574,
            -2.45938856,  0.95969843, [1, 3],  0
        )
    ]
    m.vis2 = [
        (1, 0., 59735., 0.3772, 0.70949939, 0.01131277,  1.86153485, 2.9549114 , [1, 2],  0),
        (1, 0., 59735., 0.3772, 0.8362822 , 0.0113618 , -2.45938856, 0.95969843, [1, 3],  0)
    ]
    m.wavelength = [(4.817e-06, 2.98e-07)]
    return m


def test_amioi_model_oifits_validate(oifits_ami_model):
    oifits_ami_model.validate()


def test_amioi_model_oifits_update(oifits_ami_model):
    oifits_ami_model.update({})


def test_amioi_model_oifits_compliance(tmp_path, oifits_ami_model):
    """
    This test cannot fully test oifits compliance but the schema for the model
    provides some checks. This test checks that the model in the oifits_ami_model
    fixture provides a 'passable' OIFITS file.
    """
    fn = tmp_path / "test.fits"
    oifits_ami_model.save(fn)


@pytest.mark.parametrize('attr',
                         [
                             'meta.telescope',
                             'meta.origin',
                             'meta.instrument.name',
                             'meta.program.pi_name',
                             'meta.target.proposer_name',
                             'meta.observation.date',
                             'meta.oifits.array_name',
                             'meta.oifits.instrument_mode',
                             'array',
                             'target',
                             'wavelength',
                         ])
def test_amioi_model_oifits_keyword_validation(tmp_path, oifits_ami_model, attr):
    """
    Remove some critical keywords or tables and make sure the model fails to
    save/validate This test cannot fully test oifits compliance but at least
    does some sanity checks that a file produced using AmiOiModel produces a
    file containing items that should make it oifits compliant
    """
    fn = tmp_path / "test.fits"

    node = oifits_ami_model
    *branches, leaf = attr.split('.')
    for branch in branches:
        node = getattr(node, branch)
    delattr(node, leaf)

    with pytest.raises(ValidationError):
        oifits_ami_model.save(fn)


@pytest.mark.parametrize('keep', ['vis', 'vis2', 't3'])
def test_amioi_model_oifits_datatable(tmp_path, oifits_ami_model, keep):
    fn = tmp_path / "test.fits"
    for table in ('vis', 'vis2', 't3'):
        if table == keep:
            continue
        delattr(oifits_ami_model, table)

    # since we have 1 data table, this should pass
    oifits_ami_model.save(fn)

    # removing the data table should cause saving to fail
    delattr(oifits_ami_model, keep)
    with pytest.raises(ValidationError):
        oifits_ami_model.save(fn)


@pytest.mark.parametrize('table_name', ['array', 'target', 'vis', 'vis2', 't3', 'wavelength'])
def test_amioi_model_oifits_extra_columns(tmp_path, oifits_ami_model, table_name):
    table_data = getattr(oifits_ami_model, table_name)
    new_table_data = merge_arrays([table_data, np.zeros(table_data.size, dtype=[('extra', 'f8')])], flatten=True)
    setattr(oifits_ami_model, table_name, new_table_data)
    fn = tmp_path / "test.fits"
    oifits_ami_model.save(fn)


def test_dq_def_roundtrip(tmp_path):
    """
    Open a MaskModel with a defined DQ array and dq_def that modifies the
    DQ array on open.  Save the model to a new name.  Open the new model
    to verify the DQ array is equal to the original DQ array.  This validates
    that the dynamic_mask is invertible and computes the same values.
    """
    bname = "jwst_nircam_mask_ref.fits"
    nbname = bname.replace("ref", "ref_dummy")

    fname = os.path.join(ROOT_DIR, bname)
    new_fname = os.path.join(tmp_path, nbname)

    diff = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # Open the MaskModel and save it to another file.  It should not save
        # the "uncompressed" DQ array that is in memory, but "recompress" the
        # "uncompressed" DQ array to saved.
        with MaskModel(fname) as mask:
            mask.save(new_fname)

        # Open the original and new mask model to ensure the roundtrip
        # results in the same values.  The ensures the dynamic_mask function
        # that uncompresses and compresses the DQ array based on the dq_def
        # table roundtrips to the same values.
        with MaskModel(fname) as mask, MaskModel(new_fname) as new_mask:
            diff = np.zeros(mask.dq.shape, dtype=int)
            diff[mask.dq != new_mask.dq] = 1

    assert diff is not None
    total_diff = sum(sum(diff))
    assert total_diff == 0


@pytest.mark.parametrize("shape", [None, 10])
@pytest.mark.parametrize("model", [NirspecFlatModel, NirspecQuadFlatModel])
def test_nirspec_flat_table_migration(tmp_path, model, shape):
    fn = tmp_path / 'test.fits'

    def make_data(table_dtype):
        if shape:
            fake_data = [('ABC', shape, [0.1] * shape, [2.0] * shape, [3.0] * shape)]
            dtype = [(n, table_dtype[n], shape if n != 'slit_name' else ()) for n in table_dtype.fields]
        else:
            fake_data = [('ABC', 1, 0.1, 2.0, 3.0)]
            dtype = table_dtype
        return np.array(fake_data, dtype=dtype)

    m = model()
    if model == NirspecQuadFlatModel:
        m.quadrants.append(m.quadrants.item())
        m.quadrants[0].flat_table = make_data(m.quadrants[0].flat_table.dtype)
    else:
        m.flat_table = make_data(m.flat_table.dtype)
    m.save(fn)
    with fits.open(fn) as ff:
        for ext in ff:
            if ext.name != 'FAST_VARIATION':
                continue
            # drop the error column
            ext.data = drop_fields(ext.data, 'error')
        ff.writeto(fn, overwrite=True)

    def check_error_column(model):
        if isinstance(model, NirspecQuadFlatModel):
            table = model.quadrants[0].flat_table
        else:
            table = model.flat_table
        assert np.all(np.isnan(table['error']))

    # check that migration works with datamodels.open
    with datamodels.open(fn) as dm:
        check_error_column(dm)
    # and with DataModel(fn)
    with model(fn) as dm:
        check_error_column(dm)
