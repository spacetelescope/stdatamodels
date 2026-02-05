from .model_base import _DefaultDQMixin
from .reference import ReferenceFileModel

__all__ = ["MaskModel"]


class MaskModel(ReferenceFileModel, _DefaultDQMixin):
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

    def get_primary_array_name(self):  # noqa: D102
        return "dq"
