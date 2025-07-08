"""
Test datamodel.open
"""

import os
import io
from pathlib import Path, PurePath
import warnings

import pytest
import numpy as np
from astropy.io import fits
from stdatamodels import DataModel
from stdatamodels.validate import ValidationError

from stdatamodels.jwst.datamodels import (
    JwstDataModel,
    ImageModel,
    IFUImageModel,
    RampModel,
    CubeModel,
    ReferenceFileModel,
    ReferenceImageModel,
    ReferenceCubeModel,
    ReferenceQuadModel,
    SlitModel
)
from stdatamodels.jwst import datamodels
from stdatamodels.exceptions import NoTypeWarning, ValidationWarning

import asdf


@pytest.mark.parametrize("guess", [True, False])
def test_guess(guess):
    """Test the guess parameter to the open func"""
    path = Path(t_path("test.fits"))

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "model_type not found")
        if guess is None or guess:
            # Default is to guess at the model type.
            with datamodels.open(path, guess=guess) as model:
                assert isinstance(model, JwstDataModel)
        else:
            # Without guessing, the call should fail.
            with pytest.raises(TypeError):
                with datamodels.open(path, guess=guess) as model:
                    pass


def test_open_from_pathlib():
    """Test opening a PurePath object"""
    path = Path(t_path("test.fits"))
    assert isinstance(path, PurePath)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "model_type not found")
        with datamodels.open(path) as model:
            assert isinstance(model, JwstDataModel)


def test_open_from_buffer():
    """
    Test opening a model from buffer.
    
    Should raise a TypeError in datamodel __init__
    """
    buff = io.BytesIO()
    hdul = fits.HDUList(fits.PrimaryHDU())
    hdul.writeto(buff)
    buff.seek(0)
    assert isinstance(buff, io.BytesIO)
    with pytest.raises(TypeError):
        JwstDataModel(buff)
    with pytest.raises(TypeError):
        datamodels.open(buff)


def test_open_from_bytes():
    """
    Test opening a model from bytes.
    
    Should raise ValueError: Unrecognized file type since the bytes do not represent a file path.
    """
    fits_file = t_path("test.fits")
    with open(fits_file, "rb") as f:
        data = f.read()
    assert isinstance(data, bytes)
    with pytest.raises(TypeError):
        datamodels.open(data)
    with pytest.raises(TypeError):
        JwstDataModel(data)


def test_open_from_filename_as_bytes():
    """Test opening a model where the filename is passed as a byte string"""
    fname = t_path("test.fits").as_posix().encode("utf-8")
    assert isinstance(fname, bytes)
    with pytest.raises(TypeError):
        datamodels.open(fname)
    with pytest.raises(TypeError):
        JwstDataModel(fname)


def test_open_fits():
    """Test opening a model from a FITS file"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "model_type not found")
        fits_file = t_path("test.fits")
        with datamodels.open(fits_file) as model:
            assert isinstance(model, JwstDataModel)


def test_open_none():
    with datamodels.open() as model:
        assert isinstance(model, JwstDataModel)


def test_open_shape():
    shape = (50, 20)
    with datamodels.open(shape) as model:
        assert isinstance(model, ImageModel)
        assert model.shape == shape


def test_open_illegal():
    with pytest.raises(TypeError):
        init = 5
        datamodels.open(init)


def test_open_hdulist(tmp_path):
    hdulist = fits.HDUList()
    primary = fits.PrimaryHDU()
    data = np.empty((50, 50), dtype=np.float32)
    science = fits.ImageHDU(data=data, name="SCI", ver=1)
    hdulist.append(primary)
    hdulist.append(science)

    # datamodels.open() can't open pathlib objects
    path = str(tmp_path / "jwst_image.fits")
    hdulist.writeto(path)

    with datamodels.open(hdulist) as model:
        assert isinstance(model, ImageModel)

    with pytest.warns(NoTypeWarning) as record:
        with datamodels.open(path) as model:
            assert isinstance(model, ImageModel)
            assert len(record) == 1
            assert "model_type not found" in record[0].message.args[0]


def test_open_ramp(tmp_path):
    """Open 4D data without a DQ as RampModel"""
    path = str(tmp_path / "ramp.fits")
    shape = (2, 3, 4, 5)
    with fits.HDUList(fits.PrimaryHDU()) as hdulist:
        hdulist.append(fits.ImageHDU(data=np.zeros(shape), name="SCI", ver=1))
        hdulist.writeto(path)

    with pytest.warns(NoTypeWarning):
        with datamodels.open(path) as model:
            assert isinstance(model, RampModel)


def test_open_cube(tmp_path):
    """Open 3D data as CubeModel"""
    path = str(tmp_path / "ramp.fits")
    shape = (2, 3, 4)
    with fits.HDUList(fits.PrimaryHDU()) as hdulist:
        hdulist.append(fits.ImageHDU(data=np.zeros(shape), name="SCI", ver=1))
        hdulist.writeto(path)

    with pytest.warns(NoTypeWarning):
        with datamodels.open(path) as model:
            assert isinstance(model, CubeModel)


@pytest.mark.parametrize(
    "model_class, shape",
    [
        (ReferenceFileModel, None),
        (ReferenceImageModel, (10, 10)),
        (ReferenceCubeModel, (3, 3, 3)),
        (ReferenceQuadModel, (2, 2, 2, 2)),
    ],
)
def test_open_reffiles(tmp_path, model_class, shape):
    """Try opening files with a REFTYPE keyword and different data/dq shapes"""
    path = str(tmp_path / "reffile.fits")
    with fits.HDUList(fits.PrimaryHDU()) as hdulist:
        hdulist["PRIMARY"].header.append(("REFTYPE", "foo"))
        if shape is not None:
            hdulist.append(fits.ImageHDU(data=np.zeros(shape), name="SCI", ver=1))
            hdulist.append(fits.ImageHDU(data=np.zeros(shape, dtype=np.uint), name="DQ", ver=1))
        hdulist.writeto(path)

    with pytest.warns(NoTypeWarning):
        with datamodels.open(path) as model:
            assert isinstance(model, model_class)


@pytest.mark.parametrize("suffix", [".asdf", ".fits"])
def test_open_readonly(tmp_path, suffix):
    """Test opening a FITS-format datamodel that is read-only on disk"""
    path = str(tmp_path / f"readonly{suffix}")

    with ImageModel(data=np.zeros((10, 10))) as model:
        model.meta.telescope = "JWST"
        model.meta.instrument.name = "NIRCAM"
        model.meta.instrument.detector = "NRCA4"
        model.meta.instrument.channel = "SHORT"
        model.save(path)

    Path(path).chmod(0o440)
    assert os.access(path, os.W_OK) is False

    with datamodels.open(path) as model:
        assert model.meta.telescope == "JWST"
        assert isinstance(model, ImageModel)


# Utilities
def t_path(partial_path):
    """Construction the full path for test files"""
    test_dir = Path(__file__).parent / "data"
    return test_dir / partial_path


@pytest.mark.parametrize("suffix", ["asdf", "fits"])
def test_open_asdf_no_datamodel_class(tmp_path, suffix):
    path = str(tmp_path / f"no_model.{suffix}")
    model = DataModel()
    model.save(path)

    # previously, only the fits file issued a NoTypeWarning
    # this was a quirk of the deprecated (and now removed) jwst.DataModel
    # sharing the same class name as stdatamodels.DataModel (used here)
    # now that jwst.DataModel is removed, both the fits and asdf
    # files correctly report NoTypeWarning
    with pytest.warns(NoTypeWarning):
        with datamodels.open(path) as m:
            assert isinstance(m, DataModel)


def test_open_asdf(tmp_path):
    path = str(tmp_path / "straight_asdf.asdf")
    tree = {"foo": 42, "bar": 13, "seq": np.arange(100)}
    with asdf.AsdfFile(tree) as af:
        af.write_to(path)

    with pytest.warns(NoTypeWarning):
        with datamodels.open(path) as m:
            assert isinstance(m, DataModel)


def test_open_kwargs_asdf(tmp_path):
    """
    Test that unrecognized kwargs to the datamodels.open function
    are passed on to the model class constructor.
    """
    file_path = tmp_path / "test.asdf"

    with pytest.warns(ValidationWarning):
        model = ImageModel((4, 4), pass_invalid_values=True)
        model.meta.instrument.name = "CELESTRON"
        model.save(file_path)

    with pytest.raises(ValidationError):
        with datamodels.open(file_path, strict_validation=True) as model:
            model.validate()


def test_open_kwargs_fits(tmp_path):
    """
    Test that unrecognized kwargs to the datamodels.open function
    are passed on to the model class constructor.  Similar to the
    above, except the invalid file must be created differently
    because DataModel can't save an invalid .fits file.
    """
    file_path = tmp_path / "test.fits"

    model = ImageModel((4, 4))
    model.save(file_path)

    with fits.open(file_path, mode="update") as hdul:
        hdul[0].header["INSTRUME"] = "CELESTRON"
        hdul.flush()

    with pytest.raises(ValidationError):
        with datamodels.open(file_path, strict_validation=True) as model:
            model.validate()


@pytest.mark.parametrize("InitClass", [SlitModel, ImageModel])
def test_open_does_not_clear_wht(InitClass):
    """Cover a bug where the open function cleared the wht attribute in SlitModel."""
    m0 = InitClass((27, 1299))
    m0.wht[:] = 1

    m1 = datamodels.open(m0)
    np.testing.assert_equal(m1.wht, 1)

    m2 = datamodels.SlitModel(m0)
    np.testing.assert_equal(m2.wht, 1)


@pytest.mark.parametrize("InitClass", [IFUImageModel, ImageModel])
def test_open_does_not_clear_zeroframe(InitClass):
    """Cover a bug where the open function cleared the zeroframe attribute in IFUImageModel."""
    m0 = InitClass((10,10))
    m0.zeroframe = np.ones((10, 10))

    m1 = datamodels.open(m0)
    np.testing.assert_equal(m1.zeroframe, 1)

    m2 = datamodels.IFUImageModel(m0)
    np.testing.assert_equal(m2.zeroframe, 1)


def test_memmap_deprecation(tmp_path):
    """
    Test that the deprecation warning for memmap=True is raised.
    """
    path = str(tmp_path / "test.fits")
    model = ImageModel((10, 10))
    model.save(path)

    with pytest.warns(DeprecationWarning, match="Memory mapping is no longer supported"):
        with datamodels.open(path, memmap=True):
            pass
