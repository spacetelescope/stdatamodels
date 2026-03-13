import warnings

from gwcs import WCS, EmptyFrame, EmptyFrameDeprecationWarning, Frame2D, Step

from .model_base import JwstDataModel

__all__ = ["IFUImageModel"]


class IFUImageModel(JwstDataModel):
    """
    A data model for 2D IFU images.

    Attributes
    ----------
    data : numpy float32 array
         The science data
    dq : numpy uint32 array
         Data quality array
    err : numpy float32 array
         Error array
    zeroframe : numpy float32 array
         Zeroframe array
    var_poisson : numpy float32 array
         variance due to poisson noise
    var_rnoise : numpy float32 array
         variance due to read noise
    wavelength : numpy float32 array
         wavelength
    pathloss_point : numpy float32 array
         pathloss correction for point source
    pathloss_uniform : numpy float32 array
         pathloss correction for uniform source
    area : numpy float32 array
         Pixel area map array
    regions : numpy float32 array
         Slice regions map array
    trace_model : numpy float32 array
         Trace model array
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/ifuimage.schema"

    def __init__(self, init=None, **kwargs):
        # Catch the possible usage of a string as the name of a frame for IFUImageModel.
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", EmptyFrameDeprecationWarning)
            super(IFUImageModel, self).__init__(init=init, **kwargs)

        if any(issubclass(warn.category, EmptyFrameDeprecationWarning) for warn in w):
            self._fix_wcs_empty_frame_name()

        # Implicitly create arrays
        self.dq = self.dq
        self.err = self.err

    def _fix_wcs_empty_frame_name(self):
        """Fix the name of the default frame if it was set to a string."""
        input_step = self.meta.wcs.pipeline[0]
        if not isinstance(input_step.frame, EmptyFrame):
            raise TypeError("Cannot recover from unexpected string frame in WCS pipeline.")
        else:
            pipeline = [
                Step(
                    frame=Frame2D(name=input_step.frame.name, axes_order=(0, 1)),
                    transform=input_step.transform,
                )
            ]
            pipeline.extend(self.meta.wcs.pipeline[1:])

            self.meta.wcs = WCS(forward_transform=pipeline)
