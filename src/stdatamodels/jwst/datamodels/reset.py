from stdatamodels.jwst.datamodels.model_base import DefaultErrMixin, DQMixin

from .reference import ReferenceFileModel

__all__ = ["ResetModel"]


class ResetModel(ReferenceFileModel, DQMixin, DefaultErrMixin):
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
