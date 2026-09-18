from .reference import ReferenceFileModel

__all__ = ["MirMrsPFPCModel"]


class MirMrsPFPCModel(ReferenceFileModel):
    """
    A data model for point fixed pattern correction (PFPC) reference files for MIRI MRS.

    Attributes
    ----------
    pfpc_table : numpy table
        Table of PFPC corrections. The columns must include "wavelength" and
        "correction". All other columns are FITS keyword names, to be matched
        against the input data.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/mirmrs_pfpc.schema"

    def __init__(self, init=None, **kwargs):
        super(MirMrsPFPCModel, self).__init__(init=init, **kwargs)
