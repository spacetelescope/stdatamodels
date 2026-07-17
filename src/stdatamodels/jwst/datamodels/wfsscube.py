from .model_base import DefaultDQMixin, DefaultErrMixin, JwstDataModel

__all__ = ["WFSSCubeModel"]


class WFSSCubeModel(JwstDataModel, DefaultDQMixin, DefaultErrMixin):
    """
    A data model for WFSS multi-wavelength direct image data cubes.

    Attributes
    ----------
    data : numpy float32 array
         The science data
    dq : numpy uint32 array
         Data quality array
    err : numpy float32 array
         Error array
    wavelength : numpy float32 array
         Wavelength value for planes, same shape as 0th axis of data
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/wfsscube.schema"
