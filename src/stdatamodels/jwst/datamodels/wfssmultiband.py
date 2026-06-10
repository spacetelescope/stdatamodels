from .model_base import DefaultDQMixin, DefaultErrMixin, JwstDataModel

__all__ = ["WFSSMultiBandModel"]


class WFSSMultiBandModel(JwstDataModel, DefaultDQMixin, DefaultErrMixin):
    """
    A data model for WFSS multi-band direct image data.

    Attributes
    ----------
    data : numpy float32 array
         The science data
    dq : numpy uint32 array
         Data quality array
    err : numpy float32 array
         Error array
    wavetable : numpy table
         Wavelength value for slices
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/wfssmultiband.schema"
