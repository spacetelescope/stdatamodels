from stdatamodels.jwst.datamodels.model_base import DefaultErrMixin, DQMixin

from .reference import ReferenceFileModel

__all__ = ["LastFrameModel"]


class LastFrameModel(ReferenceFileModel, DQMixin, DefaultErrMixin):
    """
    A data model for Last frame correction reference files.

    Attributes
    ----------
    data : numpy float32 array
         Last Frame Correction array
    dq : numpy uint32 array
         2-D data quality array
    err : numpy float32 array
         Error array
    dq_def : numpy table
         DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/lastframe.schema"
