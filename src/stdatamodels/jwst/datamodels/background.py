from stdatamodels.jwst.datamodels.model_base import DQMixin

from .reference import ReferenceFileModel

__all__ = ["WfssBkgModel"]


class SossBkgModel(ReferenceFileModel, DQMixin):
    """
    A data model of 2D background reference templates for NIRISS SOSS data.

    Attributes
    ----------
    data : float32 ndarray
        The background flux array templates.
    dq : uint32 ndarray
        The dq arrays for the background templates.
    err : float32 ndarray
        The error arrays associated with the background templates.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/sossbkg.schema"


class WfssBkgModel(ReferenceFileModel, DQMixin):
    """
    A data model for 2D WFSS master background reference files.

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

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/wfssbkg.schema"
