from .model_base import JwstDataModel


__all__ = ["SpecModel", "MRSSpecModel", "TSOSpecModel"]


class SpecModel(JwstDataModel):
    """
    A data model for 1D spectra.

    Attributes
    ----------
    spec_table : numpy table
        Extracted spectral data table.
        A table with at least four columns:  wavelength, flux, an error
        estimate for the flux, and data quality flags.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/spec.schema"

    def get_primary_array_name(self):  # noqa: D102
        return "spec_table"


class MRSSpecModel(JwstDataModel):
    """
    A data model for MIRI MRS 1D spectra with residual fringe corrections.

    Attributes
    ----------
    spec_table : numpy table
        Extracted spectral data table.
        A table with the standard spectral columns plus three extra
        columns for residual fringe corrected data: flux, surface brightness,
        and background.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/mrs_spec.schema"

    def get_primary_array_name(self):  # noqa: D102
        return "spec_table"


class TSOSpecModel(JwstDataModel):
    """
    A data model for TSO 1D spectra with multiple integrations.

    Attributes
    ----------
    spec_table : numpy table
        Extracted spectral data table.
        A table with the standard spectral columns plus two extra
        columns for TSO data: segment, integration. Column data
        is 2D for this model, with each row containing the spectrum
        for a single integration.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/tso_spec.schema"

    def get_primary_array_name(self):  # noqa: D102
        return "spec_table"
