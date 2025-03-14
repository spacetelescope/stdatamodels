from astropy.io import fits
from astropy.time import Time
from asdf.exceptions import ValidationError
import numpy as np
from numpy.testing import assert_array_equal
import pytest

from stdatamodels.jwst.datamodels import MultiSlitModel, ImageModel, SlitModel


def test_multislit_model():
    rng = np.random.default_rng(42)
    array1 = np.asarray(rng.random((2, 2)), dtype="float32")
    array2 = np.asarray(rng.random((2, 2)), dtype="float32")

    with MultiSlitModel() as ms:
        assert len(ms.slits) == 0
        ms.slits.append(ms.slits.item())
        ms.slits[-1].data = array1
        assert len(ms.slits) == 1
        ms.slits.append(ms.slits.item())
        ms.slits[-1].data = array2
        assert len(ms.slits) == 2
        for i, slit in enumerate(ms.slits):
            assert slit == ms.slits[i]
        ms2 = ms.copy()
        assert len(ms2.slits) == 2
        assert_array_equal(ms.slits[-1].data, array2)
        del ms.slits[0]
        assert len(ms.slits) == 1
        assert_array_equal(ms.slits[0].data, array2)


def test_multislit_move_from_fits(tmp_path):
    path = tmp_path / "multislit_move.fits"

    hdulist = fits.HDUList()
    hdulist.append(fits.PrimaryHDU())
    for i in range(5):
        hdu = fits.ImageHDU(data=np.zeros((64, 64)), name="SCI")
        hdu.ver = i + 1
        hdulist.append(hdu)

    hdulist.writeto(path)

    n = MultiSlitModel()
    with MultiSlitModel(path) as m:
        n.slits.append(m.slits[2])

        assert len(n.slits) == 1


def test_multislit_append_string():
    with pytest.raises(ValidationError):
        m = MultiSlitModel(strict_validation=True)
        m.slits.append("junk")


def test_multislit():
    rng = np.random.default_rng(42)
    with MultiSlitModel() as dm:
        dm.slits.append(dm.slits.item())
        slit = dm.slits[-1]
        slit.data = rng.random((5, 5))
        slit.dm = rng.random((5, 5))
        slit.err = rng.random((5, 5))
        assert slit.wavelength.shape == (0, 0)
        assert slit.pathloss_point.shape == (0, 0)
        assert slit.pathloss_uniform.shape == (0, 0)
        assert slit.barshadow.shape == (0, 0)


def test_multislit_from_image():
    with ImageModel((64, 64)) as im:
        with MultiSlitModel(im) as ms:
            assert len(ms.slits) == 1
            assert ms.slits[0].data.shape == (64, 64)


def test_multislit_from_saved_imagemodel(tmp_path):
    path = tmp_path / "multislit_from_image.fits"
    with ImageModel((64, 64)) as im:
        im.save(path)

    with MultiSlitModel(path) as ms:
        assert len(ms.slits) == 1
        assert ms.slits[0].data.shape == (64, 64)

        for i, slit in enumerate(ms.slits):
            assert slit.data is ms.slits[i].data

        ms2 = ms.copy()
        ms2.slits = ms.slits
        assert len(ms2.slits) == 1


def test_multislit_metadata():
    with MultiSlitModel() as ms:
        with ImageModel((64, 64)) as im:
            ms.slits.append(ms.slits.item())
            ms.slits[-1].data = im.data
        slit = ms.slits[0]
        slit.name = "FOO"
        assert ms.slits[0].name == "FOO"


def test_multislit_metadata2():
    with MultiSlitModel() as ms:
        ms.slits.append(ms.slits.item())
        for _, val in ms.items():
            assert isinstance(val, (bytes, str, int, float, bool, Time))


def test_multislit_copy(tmp_path):
    path = tmp_path / "multislit.fits"
    with MultiSlitModel() as input_file:
        for _ in range(4):
            input_file.slits.append(input_file.slits.item(data=np.empty((50, 50), dtype="float32")))

        assert len(input_file.slits) == 4
        input_file.save(path)

        output = input_file.copy()
        assert len(output.slits) == 4

    with fits.open(path, memmap=False) as hdulist:
        assert len(hdulist) == 6

    with MultiSlitModel(path) as model:
        for i, _ in enumerate(model.slits):  # noqa: B007
            pass
        assert i + 1 == 4

        output = model.copy()
        assert len(output.slits) == 4


def test_copy_multislit():
    model1 = MultiSlitModel()
    model2 = MultiSlitModel()

    model1.slits.append(ImageModel(np.ones((1024, 1024))))
    model2.slits.append(ImageModel(np.ones((1024, 1024)) * 2))

    # Create the output model as a copy of the first input
    output = model1.copy()

    assert len(model1.slits) == 1
    assert len(model2.slits) == 1
    assert len(output.slits) == 1

    assert model1.slits[0].data[330, 330] == 1
    assert output.slits[0].data[330, 330] == 1
    assert id(model1.slits[0].data) != id(output.slits[0].data)

    output.slits[0].data = model1.slits[0].data - model2.slits[0].data

    assert model1.slits[0].data[330, 330] == 1
    assert output.slits[0].data[330, 330] == -1


def test_slit_from_multislit():
    model = MultiSlitModel()
    slit = SlitModel()
    # access int_times so it's created
    slit.int_times = slit.int_times
    model.slits.append(slit)
    slit = SlitModel(model.slits[0].instance)
