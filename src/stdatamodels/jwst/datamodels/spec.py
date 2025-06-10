from .model_base import JwstDataModel


__all__ = ["SpecModel", "MRSSpecModel", "TSOSpecModel", "WFSSSpecModel"]


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


class WFSSSpecModel(JwstDataModel):
    """
    A data model for NIRCam and NIRISS WFSS 1D spectra.

    This model differs from the SpecModel base class in that
    it is designed to hold all the spectra from a single WFSS exposure.
    Its `spec_table` attribute contains the spectral data and metadata
    for all sources in the exposure.

    Attributes
    ----------
    spec_table : numpy table
        Table containing the extracted spectral data for all sources in a WFSS exposure.
        The table still has the standard spectral columns, but also has additional
        metadata columns that are used to identify the source
        and the spectral extraction region.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/wfss_spec.schema"

    def get_primary_array_name(self):  # noqa: D102
        return "spec_table"
