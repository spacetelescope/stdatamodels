from .model_base import DefaultDQMixin
from .reference import ReferenceFileModel

__all__ = ["SaturationModel"]


class SaturationModel(ReferenceFileModel, DefaultDQMixin):
    """
    A data model for saturation checking information.

    Attributes
    ----------
    data : numpy float32 array
         Saturation threshold
    dq : numpy uint32 array
         2-D data quality array for all planes
    dq_def : numpy table
         DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/saturation.schema"
