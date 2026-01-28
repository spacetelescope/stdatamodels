from stdatamodels.jwst.datamodels.model_base import DefaultErrMixin, DQMixin

from .reference import ReferenceFileModel

__all__ = ["FlatModel"]


class FlatModel(ReferenceFileModel, DQMixin, DefaultErrMixin):
    """
    A data model for 2D flat-field images.

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

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/flat.schema"
