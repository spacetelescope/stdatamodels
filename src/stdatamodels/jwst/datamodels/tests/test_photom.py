"""Tests for photom models."""

import numpy as np
from astropy.io import fits

from stdatamodels.jwst.datamodels import MirImgPhotomModel


def mir_img_phot_table():
    """Make a MIRI image PHOTOM table."""
    filter_list = ["F1800W", "F2100W", "F2550W"]
    subarray = ["SUB256", "SUB256", "SUB256"]
    nrows = len(filter_list)

    photmjsr = np.linspace(3.1, 3.1 + (nrows - 1.0) * 0.1, nrows)
    uncertainty = np.zeros(nrows, dtype=np.float32)

    dtype = np.dtype(
        [("filter", "S12"), ("subarray", "S15"), ("photmjsr", "<f4"), ("uncertainty", "<f4")]
    )
    reftab = np.array(
        list(zip(filter_list, subarray, photmjsr, uncertainty, strict=True)), dtype=dtype
    )
    return reftab


def mir_img_timecoeff(phot_table):
    """Make a MIRI image TIMECOEFF table (old-style)."""
    nrows = len(phot_table)
    timecoeff_amp = np.linspace(2.1, 2.1 + (nrows - 1.0) * 0.1, nrows)
    timecoeff_tau = np.full(nrows, 145)
    timecoeff_t0 = np.full(nrows, 59720)
    dtypec = np.dtype([("amplitude", "<f4"), ("tau", "<f4"), ("t0", "<f4")])
    reftabc = np.array(
        list(zip(timecoeff_amp, timecoeff_tau, timecoeff_t0, strict=True)),
        dtype=dtypec,
    )
    return reftabc


def mir_img_timecoeff_exponential(phot_table):
    """Make a MIRI image TIMECOEFF_EXPONENTIAL table (new-style)."""
    nrows = len(phot_table)
    photmjsr = phot_table["photmjsr"]
    timecoeff_amp = np.linspace(2.1, 2.1 + (nrows - 1.0) * 0.1, nrows) / photmjsr
    timecoeff_tau = np.full(nrows, 145)
    timecoeff_t0 = np.full(nrows, 59720)
    timecoeff_const = np.full(nrows, 1.0)
    dtypec = np.dtype([("amplitude", "<f4"), ("tau", "<f4"), ("t0", "<f4"), ("const", "<f4")])
    reftabc = np.array(
        list(zip(timecoeff_amp, timecoeff_tau, timecoeff_t0, timecoeff_const, strict=True)),
        dtype=dtypec,
    )
    return reftabc


def mir_img_phot_hdulist(old_style=False):
    """Make a MIRI image PHOTOM HDUList."""
    primary = fits.PrimaryHDU()

    phot_table = mir_img_phot_table()
    phot = fits.BinTableHDU(phot_table, name="PHOTOM")

    if old_style:
        timecoeff_table = mir_img_timecoeff(phot_table)
        timecoeff = fits.BinTableHDU(timecoeff_table, name="TIMECOEFF")
    else:
        timecoeff_table = mir_img_timecoeff_exponential(phot_table)
        timecoeff = fits.BinTableHDU(timecoeff_table, name="TIMECOEFF_EXPONENTIAL")

    hdulist = fits.HDUList([primary, phot, timecoeff])
    return hdulist


def test_initialize_from_timecoeff():
    """Test that old-style MIRI image time dependence is migrated correctly."""
    with mir_img_phot_hdulist(old_style=True) as old_style_phot_hdul:
        migrated_model = MirImgPhotomModel(old_style_phot_hdul)
    with mir_img_phot_hdulist(old_style=False) as new_style_phot_hdul:
        model = MirImgPhotomModel(new_style_phot_hdul)

    np.testing.assert_equal(migrated_model.timecoeff_exponential, model.timecoeff_exponential)
