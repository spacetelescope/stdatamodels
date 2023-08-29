from .reference import ReferenceFileModel


__all__ = ['EmiModel']


class EmiModel(ReferenceFileModel):
    """
    A data model to correct MIRI images for EMI contamination.

    Parameters
    __________
    rfc_freq_short : numpy table
    rfc_freq_medium : numpy table
    rfc_freq_long : numpy table
    max_amp : numpy table
    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/emi.schema"

