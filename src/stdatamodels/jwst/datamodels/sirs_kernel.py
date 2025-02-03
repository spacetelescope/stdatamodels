from .reference import ReferenceFileModel


__all__ = ["SIRSKernelModel"]


class SIRSKernelModel(ReferenceFileModel):
    """
    A data model for the NIR Optimized Convolution Kernel Fourier Coefficients,
    also called Simple Improved Reference Subtraction (SIRS).

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

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/sirs_kernel.schema"
    reftype = "sirskernel"

    def __init__(self, init=None, **kwargs):
        super(SIRSKernelModel, self).__init__(init=init, **kwargs)

    def on_save(self, path=None):
        self.meta.reftype = self.reftype

    def validate(self):
        super(SIRSKernelModel, self).validate()
