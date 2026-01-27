from stdatamodels.jwst.datamodels.model_base import DQMixin

from .reference import ReferenceFileModel

__all__ = ["TrapDensityModel"]


class TrapDensityModel(ReferenceFileModel, DQMixin):
    """
    A data model for the trap density of a detector, for persistence.

    Attributes
    ----------
    data : numpy float32 array
         Trap density
    dq : numpy uint32 array
         data quality array
    dq_def : numpy table
         DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/trapdensity.schema"
