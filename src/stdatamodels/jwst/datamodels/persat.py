from stdatamodels.jwst.datamodels.model_base import _DQMixin

from .reference import ReferenceFileModel

__all__ = ["PersistenceSatModel"]


class PersistenceSatModel(ReferenceFileModel, _DQMixin):
    """
    A data model for the persistence saturation value (full well).

    Attributes
    ----------
    data : numpy float32 array
         Persistence saturation threshold
    dq : numpy uint32 array
         data quality array
    dq_def : numpy table
         DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/persat.schema"
