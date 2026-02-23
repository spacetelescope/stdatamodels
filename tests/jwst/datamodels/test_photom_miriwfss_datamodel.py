from datetime import datetime

import numpy as np
from astropy import units as u
from astropy.table import Table

from stdatamodels.jwst import datamodels


def test_miri_wfss_photom():
    """Test the MIRI WFSS photom data is of the correct form."""

    phot_model = datamodels.MirWfssPhotomModel()

    wfss_photmjsr = 5.53750e-01 * u.MJy * (1 / u.steradian) * (1 / u.DN) * (u.second)
    nelem = 380
    wfss_photmjsr_error = 2.608179e-01

    wavelength = np.linspace(5.0, 14.0, nelem) * u.micron
    relresponse = np.linspace(0.001, 0.01, nelem)
    reluncertainty = np.linspace(0.001, 0.01, nelem)

    new_dtype = np.dtype(
        [
            ("filter", "S12"),
            ("photmjsr", "f4"),
            ("uncertainty", "f4"),
            ("nelem", "i2"),  # int16 per schema
            ("wavelength", "O"),
            ("relresponse", "O"),
            ("reluncertainty", "O"),
        ]
    )

    data_array = np.array(
        [
            (
                "P750L",
                float(wfss_photmjsr.value),
                float(wfss_photmjsr_error),
                len(wavelength),
                wavelength,
                relresponse,
                reluncertainty,
            )
        ],
        dtype=new_dtype,
    )

    # These MUST match the schema keys in your error message exactly
    names = (
        "filter",
        "photmjsr",
        "uncertainty",
        "nelem",
        "wavelength",
        "relresponse",
        "reluncertainty",  # Schema says 'reluncertainty', not 'relres_err'
    )

    # Create the table with the explicit names from the schema
    temp_table = Table(rows=data_array, names=names)

    p_unit_str = str(wfss_photmjsr.unit)
    w_unit_str = str(wavelength.unit)

    phot_model.phot_unit = p_unit_str
    phot_model.wave_unit = w_unit_str

    # Now the model will recognize the columns
    phot_model.phot_table = np.array(temp_table)
    phot_model.meta.filename = "MIR_WFSS_PHOTOM.FITS"
    phot_model.meta.author = "A. Petric"
    phot_model.meta.origin = "STScI"
    phot_model.meta.instrument.name = "MIRI"  # Ensure instrument is set
    phot_model.meta.exposure.type = "MIR_WFSS"
    phot_model.meta.description = "MIRI WFSS PHOTOM reference file."
    phot_model.meta.pedigree = "INFLIGHT 2022-07-08 2024-05-09"
    phot_model.meta.useafter = "2022-04-01T00:00:00"
    phot_model.meta.reftype = "photom"
    phot_model.meta.instrument.detector = "MIRIMAGE"

    # Use datetime.now(timezone.utc) as utcnow() is deprecated in newer Python
    phot_model.meta.date = datetime.now().isoformat()
    phot_model.validate()

    assert phot_model.meta.instrument.name == "MIRI"
    assert phot_model.meta.instrument.detector == "MIRIMAGE"
    assert phot_model.meta.reftype == "photom"
    assert phot_model.meta.exposure.type == "MIR_WFSS"
    assert phot_model.phot_unit == p_unit_str
    assert phot_model.wave_unit == w_unit_str
    assert phot_model.phot_table.filter == "P750L"
    assert phot_model.phot_table.photmjsr == float(wfss_photmjsr.value)
    assert phot_model.phot_table.uncertainty == float(wfss_photmjsr_error)
    np.testing.assert_allclose(phot_model.phot_table.wavelength[0], wavelength.value, atol=1e-7)
    np.testing.assert_allclose(phot_model.phot_table.relresponse[0], relresponse, atol=1e-7)
    np.testing.assert_allclose(phot_model.phot_table.reluncertainty[0], reluncertainty, atol=1e-7)
