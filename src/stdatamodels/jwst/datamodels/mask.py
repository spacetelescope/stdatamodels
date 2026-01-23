from stdatamodels.dynamicdq import dynamic_mask

from .dqflags import pixel
from .reference import ReferenceFileModel

__all__ = ["MaskModel"]


class MaskModel(ReferenceFileModel):
    """
    A data model for 2D masks.

    Attributes
    ----------
    dq : numpy uint32 array
         The mask
    dq_def : numpy table
         DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/mask.schema"

    def __init__(self, init=None, **kwargs):
        super(MaskModel, self).__init__(init=init, **kwargs)

        if getattr(self, "dq", None) is not None or getattr(self, "dq_def", None) is not None:
            self.dq = dynamic_mask(self, pixel)

    def get_primary_array_name(self):  # noqa: D102
        return "dq"
