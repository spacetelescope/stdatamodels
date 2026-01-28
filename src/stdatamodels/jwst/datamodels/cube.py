from stdatamodels.jwst.datamodels.model_base import DefaultErrMixin, DQMixin, JwstDataModel

__all__ = ["CubeModel"]


class CubeModel(JwstDataModel, DQMixin, DefaultErrMixin):
    """
    A data model for 3D image cubes.

    Attributes
    ----------
    data : numpy float32 array
         The science data
    dq : numpy uint32 array
         Data quality array
    err : numpy float32 array
         Error array
    zeroframe : numpy float32 array
         Zero frame array
    area : numpy float32 array
         Pixel area map array
    int_times : numpy table
         table of times for each integration
    wavelength : numpy float32 array
         Wavelength array
    var_poisson : numpy float32 array
         Integration-specific variances of slope due to Poisson noise
    var_rnoise : numpy float32 array
         Integration-specific variances of slope due to read noise
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/cube.schema"
