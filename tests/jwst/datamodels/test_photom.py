"""Tests for photom models."""

import numpy as np
import pytest
from astropy.io import fits

import stdatamodels.jwst.datamodels as dm
from stdatamodels.exceptions import ValidationWarning


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


def mir_img_timecoeff_exponential(phot_table):
    """Make a MIRI image TIMECOEFF_EXPONENTIAL table."""
    nrows = len(phot_table)
    photmjsr = phot_table["photmjsr"]
    timecoeff_amp = np.linspace(2.1, 2.1 + (nrows - 1.0) * 0.1, nrows) / photmjsr
    timecoeff_tau = np.full(nrows, 145)
    timecoeff_t0 = np.full(nrows, 59720)
    timecoeff_const = np.full(nrows, 1.0)
    dtypec = np.dtype(
        [
            ("filter", "S12"),
            ("subarray", "S15"),
            ("amplitude", "<f4"),
            ("tau", "<f4"),
            ("t0", "<f4"),
            ("const", "<f4"),
        ]
    )
    reftabc = np.array(
        list(
            zip(
                phot_table["filter"],
                phot_table["subarray"],
                timecoeff_amp,
                timecoeff_tau,
                timecoeff_t0,
                timecoeff_const,
                strict=True,
            )
        ),
        dtype=dtypec,
    )
    return reftabc


def mir_img_phot_hdulist():
    """Make a MIRI image PHOTOM HDUList."""
    primary = fits.PrimaryHDU()

    # Add required metadata
    primary.header["DESCRIP"] = "Test description"
    primary.header["REFTYPE"] = "photom"
    primary.header["AUTHOR"] = "Test Author"
    primary.header["PEDIGREE"] = "test"
    primary.header["USEAFTER"] = "2024-01-01"
    primary.header["INSTRUME"] = "MIRI"

    phot_table = mir_img_phot_table()
    phot = fits.BinTableHDU(phot_table, name="PHOTOM")

    timecoeff_table = mir_img_timecoeff_exponential(phot_table)
    timecoeff = fits.BinTableHDU(timecoeff_table, name="TIMECOEFF_EXPONENTIAL")

    hdulist = fits.HDUList([primary, phot, timecoeff])
    return hdulist


def test_valid_timecoeff():
    """Test validation for valid timecoeff extensions."""
    with mir_img_phot_hdulist() as phot_hdul:
        # Input models should be validate
        assert len(phot_hdul["PHOTOM"].data) == len(phot_hdul["TIMECOEFF_EXPONENTIAL"].data)
        assert np.all(phot_hdul["PHOTOM"].data["filter"] == phot_hdul["PHOTOM"].data["filter"])
        assert np.all(phot_hdul["PHOTOM"].data["subarray"] == phot_hdul["PHOTOM"].data["subarray"])

        # No errors thrown with strict validation
        model = dm.MirImgPhotomModel(phot_hdul, strict_validation=True)
        model.validate()

        # Empty extensions are not added
        assert not model.hasattr("timecoeff_linear")
        assert not model.hasattr("timecoeff_powerlaw")


@pytest.mark.parametrize("strict", [True, False])
def test_invalid_timecoeff_mismatched_length(strict):
    """Test validation for timecoeff extensions with mismatched table length."""
    with mir_img_phot_hdulist() as phot_hdul:
        # Truncate the exponential timecoeff table
        phot_hdul["TIMECOEFF_EXPONENTIAL"].data = phot_hdul["TIMECOEFF_EXPONENTIAL"].data[1:]
        assert len(phot_hdul["PHOTOM"].data) != len(phot_hdul["TIMECOEFF_EXPONENTIAL"].data)

        model = dm.MirImgPhotomModel(phot_hdul, strict_validation=strict)
        expected_message = "Model.phot_table and Model.timecoeff_exponential do not match"
        if strict:
            with pytest.raises(ValueError, match=expected_message):
                model.validate()
        else:
            with pytest.warns(ValidationWarning, match=expected_message):
                model.validate()

        # Empty extensions are not added
        assert not model.hasattr("timecoeff_linear")
        assert not model.hasattr("timecoeff_powerlaw")


@pytest.mark.parametrize("strict", [True, False])
def test_invalid_timecoeff_mismatched_values(strict):
    """Test validation for timecoeff extensions with mismatched table order."""
    with mir_img_phot_hdulist() as phot_hdul:
        # Reorder the exponential timecoeff table
        phot_hdul["TIMECOEFF_EXPONENTIAL"].data = phot_hdul["TIMECOEFF_EXPONENTIAL"].data[::-1]
        assert len(phot_hdul["PHOTOM"].data) == len(phot_hdul["TIMECOEFF_EXPONENTIAL"].data)

        model = dm.MirImgPhotomModel(phot_hdul, strict_validation=strict)
        expected_message = "Model.phot_table and Model.timecoeff_exponential do not match"
        if strict:
            with pytest.raises(ValueError, match=expected_message):
                model.validate()
        else:
            with pytest.warns(ValidationWarning, match=expected_message):
                model.validate()

        # Empty extensions are not added
        assert not model.hasattr("timecoeff_linear")
        assert not model.hasattr("timecoeff_powerlaw")


@pytest.mark.parametrize("strict", [True, False])
def test_invalid_phot_table(strict):
    """Test validation for missing phot_table."""
    with mir_img_phot_hdulist() as phot_hdul:
        del phot_hdul["PHOTOM"]
        model = dm.MirImgPhotomModel(phot_hdul, strict_validation=strict)
        expected_message = "Model.phot_table is not present"
        if strict:
            with pytest.raises(ValueError, match=expected_message):
                model.validate()
        else:
            with pytest.warns(ValidationWarning, match=expected_message):
                model.validate()

        # Empty extensions are not added
        assert model.hasattr("timecoeff_exponential")
        assert not model.hasattr("phot_table")
        assert not model.hasattr("timecoeff_linear")
        assert not model.hasattr("timecoeff_powerlaw")


@pytest.fixture
def mir_lrs_phot_model():
    nrows = 2
    nelem = 5
    dtype = np.dtype(
        [
            ("filter", "S12"),
            ("subarray", "S15"),
            ("photmjsr", "<f4"),
            ("uncertainty", "<f4"),
            ("nelem", "<i2"),
            ("wavelength", "<f4", (nelem,)),
            ("relresponse", "<f4", (nelem,)),
            ("reluncertainty", "<f4", (nelem,)),
        ]
    )
    phot_table = np.zeros(nrows, dtype=dtype)
    phot_table["filter"] = ["P750L", "P750L"]
    phot_table["subarray"] = ["FULL", "SUB64"]
    phot_table["photmjsr"] = [3.1, 3.2]
    phot_table["uncertainty"] = [0.01, 0.02]
    phot_table["nelem"] = nelem
    phot_table["wavelength"] = np.linspace(5.0, 14.0, nelem)
    phot_table["relresponse"] = 1.0
    phot_table["reluncertainty"] = 0.05

    model = dm.MirLrsPhotomModel()
    model.phot_table = phot_table
    return model


def test_tdim_not_duplicated_on_save(tmp_path, mir_lrs_phot_model):
    """
    Cover a round-tripping bug for MIRI photom models.

    TDIM keywords from the phot_table, which are created for the
    wavelength, relresponse, and reluncertainty array-like columns,
    were being handled as extra_fits instead of fits builtins.
    This caused them to get duplicated in the FITS file every time the model was saved.
    """
    path = tmp_path / "test_photom.fits"
    mir_lrs_phot_model.save(path)

    with fits.open(path) as fitsmodel:
        # verify at least one TDIM header keyword is present in the fits file
        assert any(k.startswith("TDIM") for k in fitsmodel["PHOTOM"].header.keys())

    with dm.open(path) as model:
        assert "extra_fits" not in model.instance
