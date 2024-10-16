from .reference import ReferenceFileModel


__all__ = ['PsfModel']


class PsfModel(ReferenceFileModel):
    """
    A data model for 2-D PSF reference images

    Parameters
    __________
    data : numpy float32 array
         The PSF image

    wave : numpy float32 array
         Wavelength image

    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/psf.schema"

    def __init__(self, init=None, **kwargs):
        super(PsfModel, self).__init__(init=init, **kwargs)

