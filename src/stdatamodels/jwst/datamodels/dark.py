from stdatamodels.dynamicdq import dynamic_mask
from .dqflags import pixel
from .reference import ReferenceFileModel


__all__ = ["DarkModel"]


class DarkModel(ReferenceFileModel):
    """
    A data model for dark reference files.

    Attributes
    ----------
    data : numpy float32 array
         Dark current array
    dq : numpy uint32 array
         2-D data quality array for all planes
    dq_def : numpy table
         DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/dark.schema"

    def __init__(self, init=None, **kwargs):
        super(DarkModel, self).__init__(init=init, **kwargs)

        self.dq = dynamic_mask(self, pixel)

        # Implicitly create arrays
        self.dq = self.dq
