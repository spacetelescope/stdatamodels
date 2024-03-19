from io import BytesIO

import asdf
from asdf.constants import ASDF_MAGIC
import numpy as np
from numpy.testing import assert_array_equal
from astropy.io import fits

from models import FitsModel
from stdatamodels.fits_support import _NDARRAY_TAG


def create_fits_model():
    data = np.asarray(np.random.rand(50, 50), np.float32)
    dq = np.random.randint(np.iinfo(np.uint32).max, size=(50, 50), dtype=np.uint32)
    err = np.asarray(np.random.rand(50, 50), np.float32)

    model = FitsModel((50, 50))
    model["data"] = data
    model["dq"] = dq
    model["err"] = err

    return model, data, dq, err


def open_embedded_asdf(file_path):
    with fits.open(file_path) as hdul:
        return asdf.util.load_yaml(
            BytesIO(hdul["ASDF"].data["ASDF_METADATA"].tobytes()),
            tagged=True,
        )


def test_asdf_hdu_format(tmp_path):
    file_path = tmp_path / "test.fits"

    model, _, _, _ = create_fits_model()
    model.save(file_path)

    with fits.open(file_path) as hdul:
        # One for the primary HDU, three for the arrays, and one for the ASDF HDU
        assert len(hdul) == 5

        # ASDF-in-FITS should be saved to a binary table HDU named "ASDF"
        # with a single uint8 column named "ASDF_METADATA".
        assert "ASDF" in hdul
        asdf_hdu = hdul["ASDF"]
        assert isinstance(asdf_hdu, fits.hdu.table.BinTableHDU)
        assert asdf_hdu.data.dtype.type == np.record
        assert len(asdf_hdu.data.dtype) == 1
        assert asdf_hdu.data.dtype.names == ("ASDF_METADATA",)
        assert asdf_hdu.data.dtype[0].base == np.uint8
        assert asdf_hdu.data.dtype[0].ndim == 1

        # Does it smell like an ASDF file?
        asdf_bytes = asdf_hdu.data["ASDF_METADATA"].tobytes()
        assert asdf_bytes.startswith(ASDF_MAGIC)

        # "assert" no exceptions when opening the content as ASDF.
        # Force raw types to avoid errors when the ndarray converter
        # encounters the linked FITS arrays.
        fd = BytesIO(asdf_bytes)
        asdf.open(fd)


def test_linked_arrays(tmp_path):
    file_path = tmp_path / "test.fits"

    model, data, dq, err = create_fits_model()
    model.save(file_path)

    tagged_tree = open_embedded_asdf(file_path)

    assert "data" in tagged_tree
    tagged_data = tagged_tree["data"]
    assert tagged_data._tag == _NDARRAY_TAG
    assert tagged_data["source"] == "fits:SCI,1"
    assert tagged_data["datatype"] == "float32"
    assert tagged_data["byteorder"] == "big"
    assert tagged_data["shape"] == [50, 50]

    assert "dq" in tagged_tree
    tagged_dq = tagged_tree["dq"]
    assert tagged_dq._tag == _NDARRAY_TAG
    assert tagged_dq["source"] == "fits:DQ,1"
    assert tagged_dq["datatype"] == "uint32"
    assert tagged_dq["byteorder"] == "big"
    assert tagged_dq["shape"] == [50, 50]

    assert "err" in tagged_tree
    tagged_err = tagged_tree["err"]
    assert tagged_err._tag == _NDARRAY_TAG
    assert tagged_err["source"] == "fits:ERR,1"
    assert tagged_err["datatype"] == "float32"
    assert tagged_err["byteorder"] == "big"
    assert tagged_err["shape"] == [50, 50]

    with fits.open(file_path) as hdul:
        with FitsModel(hdul) as dm:
            assert_array_equal(dm.data, data)
            # If linking wasn't working correctly, these would be different objects:
            assert dm.data is hdul["SCI"].data

            assert_array_equal(dm.dq, dq)
            assert dm.dq is hdul["DQ"].data

            assert_array_equal(dm.err, err)
            assert dm.err is hdul["ERR"].data


def test_non_fits_array(tmp_path):
    file_path = tmp_path / "test.fits"

    model, _, _, _ = create_fits_model()
    favorite_integers = np.random.randint(np.iinfo(np.uint32).max, size=(500,), dtype=np.uint32)
    model["favorite_integers"] = favorite_integers
    model.save(file_path)

    with fits.open(file_path) as hdul:
        # We shouldn't have gained an HDU:
        assert len(hdul) == 5

    tagged_tree = open_embedded_asdf(file_path)
    assert "favorite_integers" in tagged_tree
    # Should be an integer internal block source and not a string FITS source:
    assert isinstance(tagged_tree["favorite_integers"]["source"], int)

    with FitsModel(file_path) as dm:
        assert_array_equal(dm.favorite_integers, favorite_integers)


def test_non_fits_metadata(tmp_path):
    file_path = tmp_path / "test.fits"

    model, _, _, _ = create_fits_model()
    model["splines"] = "reticulated"
    model.save(file_path)

    with fits.open(file_path) as hdul:
        assert "splines" not in hdul[0].header

    tagged_tree = open_embedded_asdf(file_path)
    assert tagged_tree["splines"] == "reticulated"

    with FitsModel(file_path) as dm:
        assert dm.splines == "reticulated"


def test_array_update_and_save_new_file(tmp_path):
    file_path = tmp_path / "test.fits"
    updated_file_path = tmp_path / "updated.fits"

    model, _, _, _ = create_fits_model()
    model.save(file_path)

    new_data = np.asarray(np.random.rand(50, 50), np.float32)
    with FitsModel(file_path) as dm:
        dm.data = new_data
        dm.save(updated_file_path)

    tagged_tree = open_embedded_asdf(updated_file_path)
    assert tagged_tree["data"]["source"] == "fits:SCI,1"

    with fits.open(updated_file_path) as hdul:
        with FitsModel(hdul) as dm:
            assert_array_equal(dm.data, new_data)
            assert dm.data is hdul["SCI"].data


def test_array_update_and_save_same_file(tmp_path):
    file_path = tmp_path / "test.fits"

    model, _, _, _ = create_fits_model()
    model.save(file_path)

    new_data = np.asarray(np.random.rand(50, 50), np.float32)
    with FitsModel(file_path) as dm:
        dm.data = new_data
        dm.save(file_path)

    tagged_tree = open_embedded_asdf(file_path)
    assert tagged_tree["data"]["source"] == "fits:SCI,1"

    with fits.open(file_path) as hdul:
        with FitsModel(hdul) as dm:
            assert_array_equal(dm.data, new_data)
            assert dm.data is hdul["SCI"].data


def test_fits_array_view(tmp_path):
    """
    The old ASDF-in-FITS support provided by the asdf library
    was able to write views over FITS arrays to the embedded
    ASDF as views.  JWST doesn't make use of that feature, so
    this package doesn't bother and instead writes the view
    as a separate array in the ASDF tree.
    """
    file_path = tmp_path / "test.fits"

    model, _, _, _ = create_fits_model()
    view = model.data[:25, :]
    model["view"] = view
    model.save(file_path)

    tagged_tree = open_embedded_asdf(file_path)
    assert isinstance(tagged_tree["view"]["source"], int)

    with fits.open(file_path) as hdul:
        # We shouldn't have gained an HDU:
        assert len(hdul) == 5

    with FitsModel(file_path) as dm:
        assert_array_equal(dm["view"], view)


def test_hdu_link_independence(tmp_path):
    """
    As links between arrays and hdu items are made during
    saving, it's possible that if this goes wrong links
    might be made between multiple arrays and a single hdu.
    In this case, modifying one array will change memory
    shared with another array. This test creates a file
    with multiple arrays, writes it to a fits file,
    reads it back in and then modifies the contents of
    each array to check for this possible error.
    """
    file_path = tmp_path / "test.fits"

    model, _, _, _ = create_fits_model()
    model.save(file_path)

    with FitsModel(file_path) as dm:
        # assign new values
        dm.data[:] = 1
        dm.dq[:] = 2
        dm.err[:] = 3

        assert np.all(dm.data == 1)
        assert np.all(dm.dq == 2)
        assert np.all(dm.err == 3)


def test_resave_breaks_hdulist_tree_array_link(tmp_path):
    """
    Test that writing, reading and rewriting an AsdfInFits file
    maintains links between hdus and arrays in the asdf tree

    If the link is broken, data can be duplicated (exist both
    as a hdu and as an internal block in the asdf tree).

    See issues:
        https://github.com/asdf-format/asdf/issues/1232
        https://github.com/spacetelescope/jwst/issues/7354
        https://github.com/spacetelescope/jwst/issues/7274
    """
    file_path_1 = tmp_path / "test1.fits"
    file_path_2 = tmp_path / "test2.fits"

    model, _, _, _ = create_fits_model()
    model.save(file_path_1)

    with FitsModel(file_path_1) as dm:
        dm.save(file_path_2)

    # check that af1 (original write) and af2 (rewrite) do not contain internal ASDF blocks
    with fits.open(file_path_1) as af1, fits.open(file_path_2) as af2:
        for f in (af1, af2):
            block_bytes = f["ASDF"].data.tobytes().split(b"...")[1].strip()
            assert len(block_bytes) == 0
