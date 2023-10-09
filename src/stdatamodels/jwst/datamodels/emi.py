from .reference import ReferenceFileModel
from stdatamodels.dynamicdq import dynamic_mask
from .dqflags import pixel


__all__ = ['EmiModel']


class EmiModel(ReferenceFileModel):
    """
    A data model to correct MIRI images for EMI contamination.

    Parameters
    __________
    data : numpy float32 array
         The science data

    dq : numpy uint32 array
         Data quality array

    err : numpy float32 array
         Error array

    dq_def : numpy table
         DQ flag definitions
    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/emi.schema"

    def __init__(self, init=None, **kwargs):
        super(EmiModel, self).__init__(init=init, **kwargs)

        self.dq = dynamic_mask(self, pixel)

        # Implicitly create arrays
        self.err = self.err

