from stdatamodels.dynamicdq import dynamic_mask
from .dqflags import pixel
from .reference import ReferenceFileModel


__all__ = ["WfssBkgModel"]


class SossBkgModel(ReferenceFileModel):
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

    def __init__(self, init=None, **kwargs):
        super(SossBkgModel, self).__init__(init=init, **kwargs)


class WfssBkgModel(ReferenceFileModel):
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

    def __init__(self, init=None, **kwargs):
        super(WfssBkgModel, self).__init__(init=init, **kwargs)

        self.dq = dynamic_mask(self, pixel)

        # Implicitly create arrays
        self.dq = self.dq
        self.err = self.err
