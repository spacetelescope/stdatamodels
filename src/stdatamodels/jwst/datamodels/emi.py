from .reference import ReferenceFileModel


__all__ = ['EmiModel']


class EmiModel(ReferenceFileModel):
    """
    A data model to correct MIRI images for EMI contamination.

    Parameters
    __________
    data : numpy table
         The reference waves to correct for MIRI EMI.
        A table-like object containing phase amplitude values
        corresponding to the appropriate frequency
        - Hz390: float32 1D array
        - Hz218a: float32 1D array
        - Hz218b: float32 1D array
        - Hz218c: float32 1D array
        - Hz164: float32 1D array
        - Hz10: float32 1D array
    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/emi.schema"
