from .model_base import JwstDataModel


__all__ = ["SpecModel", "MRSSpecModel"]


class SpecModel(JwstDataModel):
    """
    A data model for 1D spectra.

    Parameters
    __________
    spec_table : numpy table
        Extracted spectral data table.
        A table with at least four columns:  wavelength, flux, an error
        estimate for the flux, and data quality flags.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/spec.schema"


class MRSSpecModel(SpecModel):
    """
    A data model for MIRI MRS 1D spectra with residual fringe corrections.

    Parameters
    __________
    spec_table : numpy table
        Extracted spectral data table.
        A table with the standard spectral columns plus three extra
        columns for residual fringe corrected data: flux, surface brightness,
        and background.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/mrs_spec.schema"
