from .model_base import JwstDataModel


__all__ = ['CubeModel']


class CubeModel(JwstDataModel):
    """
    A data model for 3D image cubes.

    Parameters
    __________
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

    def __init__(self, init=None, **kwargs):

        super(CubeModel, self).__init__(init=init, **kwargs)

        # Implicitly create arrays
        self.dq = self.dq
        self.err = self.err
