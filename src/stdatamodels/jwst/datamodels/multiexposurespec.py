"""Datamodels holding spectra from multiple exposures."""

from .model_base import JwstDataModel
from .multispec import WFSSMultiSpecModel

__all__ = ["WFSSMultiExposureSpecModel"]


class WFSSMultiExposureSpecModel(JwstDataModel):
    """
    A data model for a collection of spectra from multiple exposures.

    Attributes
    ----------
    exposures : list of `~jwst.datamodels.WFSSMultiSpecModel`
        A list of WFSSMultiSpecModel objects, each containing the
        spectra from a single exposure.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/wfss_multiexposurespec.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, WFSSMultiSpecModel):
            # If init is a WFSSMultiSpecModel, convert it to a list
            init = [init]
        super().__init__(init=init, **kwargs)
