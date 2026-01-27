from stdatamodels.jwst.datamodels.model_base import DQMixin

from .reference import ReferenceFileModel

__all__ = ["SuperBiasModel"]


class SuperBiasModel(ReferenceFileModel, DQMixin):
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
