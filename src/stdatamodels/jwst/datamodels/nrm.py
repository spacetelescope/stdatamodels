from .reference import ReferenceFileModel


__all__ = ['NRMModel']


class NRMModel(ReferenceFileModel):
    """
    A data model for Non-Redundant Mask.

    Parameters
    __________
    nrm : numpy float32 array
         Non-Redundant Mask
    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/nrm.schema"
