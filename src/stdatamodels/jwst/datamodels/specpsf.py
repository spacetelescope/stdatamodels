from .reference import ReferenceFileModel


__all__ = ["SpecPsfModel"]


class SpecPsfModel(ReferenceFileModel):
    """
    A data model for spectral PSF reference data.

    Attributes
    ----------
    data : numpy float32 array
         The PSF image
    wave : numpy float32 array
         Wavelength image
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/specpsf.schema"

    def __init__(self, init=None, **kwargs):
        super(SpecPsfModel, self).__init__(init=init, **kwargs)
