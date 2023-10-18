from .reference import ReferenceFileModel
from .dqflags import pixel


__all__ = ['EmiModel']


class EmiModel(ReferenceFileModel):
    """
    A data model to correct MIRI images for EMI contamination.

    Parameters
    __________
    data : numpy float32 array
         The science data
    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/emi.schema"

    def __init__(self, init=None, **kwargs):
        super(EmiModel, self).__init__(init=init, **kwargs)


