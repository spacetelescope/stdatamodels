from stdatamodels.dynamicdq import dynamic_mask
from .dqflags import pixel
from .reference import ReferenceFileModel


__all__ = ["ResetModel"]


class ResetModel(ReferenceFileModel):
    """
    A data model for reset correction reference files.

    Attributes
    ----------
    data : numpy float32 array
         Reset Correction array
    dq : numpy uint32 array
         2-D data quality array for each integration
    err : numpy float32 array
         Error array
    dq_def : numpy table
         DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/reset.schema"

    def __init__(self, init=None, **kwargs):
        super(ResetModel, self).__init__(init=init, **kwargs)

        self.dq = dynamic_mask(self, pixel)

        # Implicitly create arrays
        self.dq = self.dq
        self.err = self.err
