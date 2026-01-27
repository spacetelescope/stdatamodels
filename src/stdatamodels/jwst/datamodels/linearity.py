from stdatamodels.jwst.datamodels.model_base import DQMixin

from .reference import ReferenceFileModel

__all__ = ["LinearityModel"]


class LinearityModel(ReferenceFileModel, DQMixin):
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
