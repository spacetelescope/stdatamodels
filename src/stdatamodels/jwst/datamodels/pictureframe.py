from stdatamodels.dynamicdq import dynamic_mask

from .dqflags import pixel
from .reference import ReferenceFileModel

__all__ = ["PictureFrameModel"]


class PictureFrameModel(ReferenceFileModel):
    """
    A data model for 2D thermal picture frame reference files.

    Attributes
    ----------
    data : numpy float32 array
        The science data
    dq : numpy uint32 array
        Data quality array
    err : numpy float32 array
        Error array
    dq_def : numpy table
        DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/pictureframe.schema"

    def __init__(self, init=None, **kwargs):
        super(PictureFrameModel, self).__init__(init=init, **kwargs)

        self.dq = dynamic_mask(self, pixel)
