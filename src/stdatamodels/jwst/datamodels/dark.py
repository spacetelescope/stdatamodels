from stdatamodels.jwst.datamodels.model_base import _DQMixin

from .reference import ReferenceFileModel

__all__ = ["DarkMIRIModel", "DarkModel", "DarkNirspecModel"]


class DarkModel(ReferenceFileModel, _DQMixin):
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


class DarkMIRIModel(ReferenceFileModel, _DQMixin):
    """
    A data model for dark MIRI reference files.

    Attributes
    ----------
    data : numpy float32 array
         Dark current array
    dq : numpy uint32 array
         2-D data quality array for all planes
    dq_def : numpy table
         DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/darkMIRI.schema"


class DarkNirspecModel(ReferenceFileModel, _DQMixin):
    """
    A data model for NIRSpec dark reference files.

    Attributes
    ----------
    data : numpy float32 array
         Dark current array
    dq : numpy uint32 array
         2-D data quality array for all planes
    dq_def : numpy table
         DQ flag definitions
    average_dark_current: numpy float32 array
         Average dark current for each pixel
    dark_rate : numpy float32 array
         Dark rate used by NIRSpec team
    dark_rate_unc : numpy float32 array
         Dark rate uncertainties
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/dark_nirspec.schema"
