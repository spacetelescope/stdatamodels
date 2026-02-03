from .model_base import _DefaultErrMixin, _DQMixin
from .reference import ReferenceFileModel

__all__ = ["SuperBiasModel"]


class SuperBiasModel(ReferenceFileModel, _DQMixin, _DefaultErrMixin):
    """
    A data model for 2D super-bias images.

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

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/superbias.schema"
