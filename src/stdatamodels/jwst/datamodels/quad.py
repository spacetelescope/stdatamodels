from .model_base import JwstDataModel, _DefaultDQMixin, _DefaultErrMixin

__all__ = ["QuadModel"]


class QuadModel(JwstDataModel, _DefaultDQMixin, _DefaultErrMixin):
    """
    A data model for 4D image arrays.

    Attributes
    ----------
    data : numpy float32 array
         The science data
    dq : numpy uint32 array
         Data quality array
    err : numpy float32 array
         Error array
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/quad.schema"
