from .model_base import _DefaultDQMixin
from .reference import ReferenceFileModel

__all__ = ["LinearityModel"]


class LinearityModel(ReferenceFileModel, _DefaultDQMixin):
    """
    A data model for linearity correction information.

    Attributes
    ----------
    coeffs : numpy float32 array
         Linearity coefficients
    dq : numpy uint32 array
         Data quality flags
    dq_def : numpy table
         DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/linearity.schema"

    def get_primary_array_name(self):  # noqa: D102
        return "coeffs"
