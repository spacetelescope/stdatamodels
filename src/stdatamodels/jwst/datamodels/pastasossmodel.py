from .reference import ReferenceFileModel


__all__ = ['PastasossModel']


class PastasossModel(ReferenceFileModel):
    """
    A data model to hold NIRISS SOSS wavelength grids.
    This 1-D array of wavelengths can be saved from a processing run
    and applied to future input products.

    Parameters
    __________
    wavegrid : numpy float32 array
        1-D array of the wavelengths corresponding to the ATOCA fit.
    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/pastasossmodel.schema"
