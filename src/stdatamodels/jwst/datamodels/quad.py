from stdatamodels.jwst.datamodels.model_base import DQMixin, JwstDataModel

__all__ = ["QuadModel"]


class QuadModel(JwstDataModel, DQMixin):
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
