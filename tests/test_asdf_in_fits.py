import pytest
from astropy.io import fits
import numpy as np
from numpy.testing import assert_array_almost_equal
import yaml

from stdatamodels import asdf_in_fits

from models import FitsModel


def test_write_linked(tmp_path):
    hdulist = fits.HDUList()
    sci = np.arange(512, dtype=float)
    dq = np.arange(512, dtype=float) + 1
    hdulist.append(fits.ImageHDU(sci, name='SCI'))
    hdulist.append(fits.ImageHDU(dq, name='DQ'))

    tree = {
        'meta': {
            'foo': 'bar',
        },
        'model': {
            'sci': {
                'data': hdulist['SCI'].data,
            },
            'dq': {
                'data': hdulist['DQ'].data,
            }
        }
    }

    fn = tmp_path / "test.fits"

    asdf_in_fits.write(fn, tree, hdulist)

    # confirm it matches
    with asdf_in_fits.open(fn) as af:
        assert_array_almost_equal(af['model']['sci']['data'], sci)
        assert_array_almost_equal(af['model']['dq']['data'], dq)
        assert af['meta']['foo'] == 'bar'

    with fits.open(fn) as read_hdulist:
        # hdu should have sci, dq, and ASDF
        assert len(read_hdulist) == 3
        # check asdf extension has no blocks by looking for bytes
        # after the end of the yaml document for the tree
        bs = read_hdulist['ASDF'].data['ASDF_METADATA'].tobytes()
        assert len(bs.strip().split(b'...')[1]) == 0


def test_write_asdf_in_fits_no_hdulist(tmp_path):
    sci = np.arange(512, dtype=float)
    dq = np.arange(512, dtype=float) + 1
    tree = {
        'meta': {
            'foo': 'bar',
        },
        'model': {
            'sci': {
                'data': sci,
            },
            'dq': {
                'data': dq,
            }
        }
    }
    fn = tmp_path / "test.fits"

    asdf_in_fits.write(fn, tree)

    # confirm it matches
    with asdf_in_fits.open(fn) as af:
        assert_array_almost_equal(af['model']['sci']['data'], sci)
        assert_array_almost_equal(af['model']['dq']['data'], dq)
        assert af['meta']['foo'] == 'bar'

    with fits.open(fn) as read_hdulist:
        # hdu should have primary and ASDF
        assert len(read_hdulist) == 2
        # check asdf extension has blocks by looking at the block index
        bs = read_hdulist['ASDF'].data['ASDF_METADATA'].tobytes()
        block_index_bs = bs.split(b'BLOCK INDEX')[1].strip()
        block_offsets = yaml.load(block_index_bs, yaml.SafeLoader)
        assert len(block_offsets) == 2


def test_write_asdf_in_fits_partial_hdulist(tmp_path):
    hdulist = fits.HDUList()
    # add other data to hdulist
    hdulist.append(fits.PrimaryHDU())

    sci = np.arange(512, dtype=float)
    dq = np.arange(512, dtype=float) + 1
    tree = {
        'meta': {
            'foo': 'bar',
        },
        'model': {
            'sci': {
                'data': sci,
            },
            'dq': {
                'data': dq,
            }
        }
    }
    fn = tmp_path / "test.fits"

    asdf_in_fits.write(fn, tree, hdulist)

    # confirm it matches
    with asdf_in_fits.open(fn) as af:
        assert_array_almost_equal(af['model']['sci']['data'], sci)
        assert_array_almost_equal(af['model']['dq']['data'], dq)
        assert af['meta']['foo'] == 'bar'

    with fits.open(fn) as read_hdulist:
        # hdu should have primary and ASDF
        assert len(read_hdulist) == 2
        # check asdf extension has blocks by looking at the block index
        bs = read_hdulist['ASDF'].data['ASDF_METADATA'].tobytes()
        block_index_bs = bs.split(b'BLOCK INDEX')[1].strip()
        block_offsets = yaml.load(block_index_bs, yaml.SafeLoader)
        assert len(block_offsets) == 2


@pytest.fixture
def test_array():
    return np.arange(1000, dtype='f4').reshape((100, 10))


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
    assert_array_almost_equal(af['data'], test_array)
    af.close()


def test_open_asdf_in_fits_context(saved_array_model, test_array):
    # read it back as a context
    with asdf_in_fits.open(saved_array_model) as af:
        # confirm it matches
        assert_array_almost_equal(af['data'], test_array)


def test_open_asdf_in_fits_hdu(saved_array_model, test_array):
    """
    Test that asdf_in_fits.open can read from an already
    opened HDUList and that it does not close the HDUList
    when the AsdfFile is closed
    """
    with fits.open(saved_array_model) as hdu:
        with asdf_in_fits.open(hdu) as af:
            assert_array_almost_equal(af['data'], test_array)
        # make sure file was not closed with context
        assert not hdu.fileinfo(0)['file'].closed
