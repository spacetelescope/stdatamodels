from stdatamodels.dynamicdq import dynamic_mask
from .dqflags import pixel
from .reference import ReferenceFileModel


__all__ = ["WfssBkgModel"]


class WfssBkgModel(ReferenceFileModel):
    """A data model for 2D WFSS master background reference files."""

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/wfssbkg.schema"

    def __init__(self, init=None, **kwargs):
        super(WfssBkgModel, self).__init__(init=init, **kwargs)

        self.dq = dynamic_mask(self, pixel)

        # Implicitly create arrays
        self.dq = self.dq
        self.err = self.err
