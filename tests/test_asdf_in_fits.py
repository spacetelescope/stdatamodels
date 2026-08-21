import numpy as np
import pytest
import yaml
from astropy.io import fits
from numpy.testing import assert_array_almost_equal

from stdatamodels import asdf_in_fits

from .models import FitsModel


def test_write_linked(tmp_path):
    hdulist = fits.HDUList()
    sci = np.arange(512, dtype=float)
    dq = np.arange(512, dtype=float) + 1
    hdulist.append(fits.ImageHDU(sci, name="SCI"))
    hdulist.append(fits.ImageHDU(dq, name="DQ"))

    tree = {
        "meta": {
            "foo": "bar",
        },
        "model": {
            "sci": {
                "data": hdulist["SCI"].data,
            },
            "dq": {
                "data": hdulist["DQ"].data,
            },
        },
    }

    fn = tmp_path / "test.fits"

    asdf_in_fits.write(fn, tree, hdulist)

    # confirm it matches
    with asdf_in_fits.open(fn) as af:
        assert_array_almost_equal(af["model"]["sci"]["data"], sci)
        assert_array_almost_equal(af["model"]["dq"]["data"], dq)
        assert af["meta"]["foo"] == "bar"

    with fits.open(fn) as read_hdulist:
        # hdu should have sci, dq, and ASDF
        assert len(read_hdulist) == 3
        # check asdf extension has no blocks by looking for bytes
        # after the end of the yaml document for the tree
        bs = read_hdulist["ASDF"].data["ASDF_METADATA"].tobytes()
        assert len(bs.strip().split(b"...")[1]) == 0


def test_write_asdf_in_fits_no_hdulist(tmp_path):
    sci = np.arange(512, dtype=float)
    dq = np.arange(512, dtype=float) + 1
    tree = {
        "meta": {
            "foo": "bar",
        },
        "model": {
            "sci": {
                "data": sci,
            },
            "dq": {
                "data": dq,
            },
        },
    }
    fn = tmp_path / "test.fits"

    asdf_in_fits.write(fn, tree)

    # confirm it matches
    with asdf_in_fits.open(fn) as af:
        assert_array_almost_equal(af["model"]["sci"]["data"], sci)
        assert_array_almost_equal(af["model"]["dq"]["data"], dq)
        assert af["meta"]["foo"] == "bar"

    with fits.open(fn) as read_hdulist:
        # hdu should have primary and ASDF
        assert len(read_hdulist) == 2
        # check asdf extension has blocks by looking at the block index
        bs = read_hdulist["ASDF"].data["ASDF_METADATA"].tobytes()
        block_index_bs = bs.split(b"BLOCK INDEX")[1].strip()
        block_offsets = yaml.load(block_index_bs, yaml.SafeLoader)
        assert len(block_offsets) == 2


def test_write_asdf_in_fits_partial_hdulist(tmp_path):
    hdulist = fits.HDUList()
    # add other data to hdulist
    hdulist.append(fits.PrimaryHDU())

    sci = np.arange(512, dtype=float)
    dq = np.arange(512, dtype=float) + 1
    tree = {
        "meta": {
            "foo": "bar",
        },
        "model": {
            "sci": {
                "data": sci,
            },
            "dq": {
                "data": dq,
            },
        },
    }
    fn = tmp_path / "test.fits"

    asdf_in_fits.write(fn, tree, hdulist)

    # confirm it matches
    with asdf_in_fits.open(fn) as af:
        assert_array_almost_equal(af["model"]["sci"]["data"], sci)
        assert_array_almost_equal(af["model"]["dq"]["data"], dq)
        assert af["meta"]["foo"] == "bar"

    with fits.open(fn) as read_hdulist:
        # hdu should have primary and ASDF
        assert len(read_hdulist) == 2
        # check asdf extension has blocks by looking at the block index
        bs = read_hdulist["ASDF"].data["ASDF_METADATA"].tobytes()
        block_index_bs = bs.split(b"BLOCK INDEX")[1].strip()
        block_offsets = yaml.load(block_index_bs, yaml.SafeLoader)
        assert len(block_offsets) == 2


def test_to_hdulist():
    sci = np.arange(512, dtype=float)
    dq = np.arange(512, dtype=float) + 1
    tree = {
        "meta": {
            "foo": "bar",
        },
        "model": {
            "sci": {
                "data": sci,
            },
            "dq": {
                "data": dq,
            },
        },
    }

    hdulist = asdf_in_fits.to_hdulist(tree)

    # hdu should have primary and ASDF
    assert len(hdulist) == 2
    # check asdf extension has blocks by looking at the block index
    bs = hdulist["ASDF"].data["ASDF_METADATA"].tobytes()
    block_index_bs = bs.split(b"BLOCK INDEX")[1].strip()
    block_offsets = yaml.load(block_index_bs, yaml.SafeLoader)
    assert len(block_offsets) == 2


@pytest.fixture
def test_array():
    return np.arange(1000, dtype="f4").reshape((100, 10))


@pytest.fixture
def saved_array_model(tmp_path, test_array):
    # make a model
    fn = tmp_path / "test.fits"
    m = FitsModel(test_array)
    m.save(fn)
    return fn


def test_open_asdf_in_fits(saved_array_model, test_array):
    # read it back (not in a context)
    af = asdf_in_fits.open(saved_array_model)
    # confirm it matches
    assert_array_almost_equal(af["data"], test_array)
    af.close()


def test_open_asdf_in_fits_context(saved_array_model, test_array):
    # read it back as a context
    with asdf_in_fits.open(saved_array_model) as af:
        # confirm it matches
        assert_array_almost_equal(af["data"], test_array)


def test_open_asdf_in_fits_hdu(saved_array_model, test_array):
    """
    Test that asdf_in_fits.open can read from an already
    opened HDUList and that it does not close the HDUList
    when the AsdfFile is closed
    """
    with fits.open(saved_array_model) as hdu:
        with asdf_in_fits.open(hdu) as af:
            assert_array_almost_equal(af["data"], test_array)
        # make sure file was not closed with context
        assert not hdu.fileinfo(0)["file"].closed


def test_non_named_hdus(tmp_path):
    fn = tmp_path / "test.fits"
    ff = fits.HDUList([fits.PrimaryHDU()] + [fits.ImageHDU([i]) for i in range(10)])
    # give a few names so that the index of nameless hdus
    # doesn't match the index of all hdus
    ff[5].name = "FOO"
    ff[5].ver = 1
    ff[7].name = "FOO"
    ff[7].ver = 2
    tree = {"hdus": [hdu.data for hdu in ff[1:]]}
    asdf_in_fits.write(fn, tree, ff)

    with asdf_in_fits.open(fn) as af:
        for i, hdu in enumerate(af.tree["hdus"]):
            assert hdu[0] == i


def test_expected_source_indexing(tmp_path):
    """
    Test that expected indexing scheme of FITS extensions can be read.

    The ASDF extension references FITS extensions using a specific indexing scheme,
    with named extensions having NAME,IDX where IDX is the index among extensions with
    that exact name, and unnamed extensions have just IDX, where IDX is the index
    among all extensions.
    It's possible to break the indexing scheme on write but also update the indexing scheme
    on read to match, such that we would be silently breaking read of old files.
    This test catches that case by explicitly defining the asdf bytes with the expected
    indexing scheme and forcing the reader to be able to parse that correctly.
    """
    ff = fits.HDUList()
    ff.append(fits.PrimaryHDU())
    ff.append(fits.ImageHDU([0]))
    ff.append(fits.ImageHDU([1], name="SCI"))
    ff.append(fits.ImageHDU([2]))

    asdf_bytes = b"#ASDF 1.0.0\n#ASDF_STANDARD 1.6.0\n%YAML 1.1\n%TAG ! tag:stsci.edu:asdf/\n--- !core/asdf-1.1.0\narrs:\n- !core/ndarray-1.1.0\n  source: fits:1\n  datatype: int64\n  byteorder: big\n  shape: [1]\n- !core/ndarray-1.1.0\n  source: fits:SCI,1\n  datatype: int64\n  byteorder: big\n  shape: [1]\n- !core/ndarray-1.1.0\n  source: fits:3\n  datatype: int64\n  byteorder: big\n  shape: [1]\n..."

    data = np.frombuffer(asdf_bytes, dtype=np.uint8)[None, :]
    fmt = f"{len(data[0])}B"
    column = fits.Column(array=data, format=fmt, name="ASDF_METADATA")
    ff.append(fits.BinTableHDU.from_columns([column], name="ASDF"))

    foo_fn = tmp_path / "foo.fits"
    ff.writeto(foo_fn, overwrite=True)
    ff.close()

    with asdf_in_fits.open(foo_fn) as af:
        assert af["arrs"][0][0] == 0
        assert af["arrs"][1][0] == 1
        assert af["arrs"][2][0] == 2
        assert af["arrs"][2][0] == 2
