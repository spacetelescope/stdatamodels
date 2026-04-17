import warnings

import numpy as np

from stdatamodels.exceptions import ValidationWarning

from .model_base import JwstDataModel

__all__ = ["RampModel"]


class RampModel(JwstDataModel):
    """
    A data model for 4D ramps.

    Attributes
    ----------
    data : numpy float32 array
         The science data
    pixeldq : numpy uint32 array
         2-D data quality array for all planes
    groupdq : numpy uint8 array
         4-D data quality array for each plane
    average_dark_current: numpy float32 array
         Average dark current for each pixel
    zeroframe : numpy float32 array
         Zeroframe array
    group : numpy table
         group parameters table
    int_times : numpy table
         table of times for each integration
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/ramp.schema"

    def __init__(self, init=None, **kwargs):
        super(RampModel, self).__init__(init=init, **kwargs)

        # Ensure that if data exists, pixeldq and groupdq arrays exist
        if self.data is None:
            return
        if self.pixeldq is None:
            self.pixeldq = self.get_default("pixeldq")
        if self.groupdq is None:
            self.groupdq = self.get_default("groupdq")

    def get_default(self, attr):
        """
        Retrieve the schema-defined default value of an attribute.

        Override the parent method to set pixeldq to a 2D array if
        data is defined; 3D array if ``meta.subarray.num_superstripe``
        is also defined.

        Override the parent method to give zeroframe the correct shape
        if data is defined.

        Parameters
        ----------
        attr : str
            Attribute to set to its default value.

        Returns
        -------
        object or None
            The default value for the given attribute. If the attribute is schema-defined
            but has no default value in the schema, this will return None.

        Raises
        ------
        AttributeError
            If the given attribute is not defined in the schema.
        """
        if self.data is not None:
            image_shape = self.data.shape[-2:]
            nstripe = self.meta.subarray.num_superstripe

            if attr == "pixeldq":
                # Make a 3D array for superstripe data
                if nstripe is not None and nstripe > 0:
                    return np.zeros((nstripe, *image_shape), dtype=np.uint32)

                # Otherwise, make a 2D array
                return np.zeros(image_shape, dtype=np.uint32)

            if attr == "zeroframe":
                return np.zeros((self.data.shape[0], *image_shape), dtype=np.float32)

        return super().get_default(attr)

    def validate(self):
        """
        Validate the model instance against its schema.

        Override the parent method to check the pixeldq dimensionality.
        If ``meta.subarray.num_superstripe`` is greater than zero,
        the pixeldq should be 3D, with the first dimension matching
        the number of stripes.
        """
        super().validate()

        if self.data is None or self.pixeldq is None:
            return

        try:
            nstripe = getattr(self.meta.subarray, "num_superstripe", None)
            image_shape = self.data.shape[-2:]
            if nstripe is None or nstripe == 0:
                message = f"Pixeldq array must have shape {image_shape}"
                assert self.pixeldq.shape == image_shape, message
            else:
                pdims = (nstripe, *image_shape)
                message = (
                    f"Pixeldq array must have shape {pdims} for "
                    f"num_superstripe={nstripe}, image shape {image_shape}"
                )
                assert self.pixeldq.shape == pdims, message

        except AssertionError as error_message:
            if self._strict_validation:
                raise
            else:
                warnings.warn(str(error_message), ValidationWarning, stacklevel=2)
