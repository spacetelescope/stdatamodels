from .reference import ReferenceFileModel


__all__ = ['ConvKernelModel']


class ConvKernelModel(ReferenceFileModel):
    """
    A data model for the NIR Optimized Convolution Kernel Fourier Coefficients.

    Parameters
    __________
    data : numpy table
        The reference waves to correct for 1/f at the REFPIX step for NIR data.
        A table-like object containing the Fourier Coefficients for the
        optimized convolution kernel. The format is the same for all NIR files
        - Detector name: str
        - gamma: float32 1D array
        - zeta: float32 1D array
    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/conv_kernel.schema"
    reftype = "conv_kernel"

    def __init__(self, init=None, **kwargs):
        super(ConvKernelModel, self).__init__(init=init, **kwargs)

    def on_save(self, path=None):
        self.meta.reftype = self.reftype

    def validate(self):
        super(ConvKernelModel, self).validate()
