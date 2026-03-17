import numpy as np

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
            # This is a band-aid solution to allow multistripe modes to
            # have 3D pixeldq, but set the default appropriately for
            # all other RampModels.

            # If we can move multi-stripe RampModels to their own model
            # type, we can resume using the schema to make a default pixeldq:
            # self.pixeldq = self.get_default("pixeldq")

            self.pixeldq = np.zeros(self.data.shape[-2:], dtype=np.uint32)

        if self.groupdq is None:
            self.groupdq = self.get_default("groupdq")
