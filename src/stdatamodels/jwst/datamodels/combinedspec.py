from .model_base import JwstDataModel


__all__ = ["CombinedSpecModel", "WFSSCombinedSpecModel"]


class CombinedSpecModel(JwstDataModel):
    """
    A data model for combined 1D spectra.

    Attributes
    ----------
    spec_table : numpy table
         Combined, extracted spectral data table
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/combinedspec.schema"


class WFSSCombinedSpecModel(JwstDataModel):
    """
    A data model for NIRCam and NIRISS WFSS exposure-averaged 1D spectra.

    This model is designed to hold the combined spectra from a WFSS observation,
    with each spectrum represented as a single row in the `spec_table` attribute.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/wfss_combinedspec.schema"
