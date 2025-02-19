from stdatamodels.dynamicdq import dynamic_mask
from .dqflags import pixel
from .reference import ReferenceFileModel


__all__ = ["LinearityModel"]


class LinearityModel(ReferenceFileModel):
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

    def __init__(self, init=None, **kwargs):
        super(LinearityModel, self).__init__(init=init, **kwargs)

        self.dq = dynamic_mask(self, pixel)

        # Implicitly create arrays
        self.dq = self.dq

    def get_primary_array_name(self):  # noqa: D102
        return "coeffs"
