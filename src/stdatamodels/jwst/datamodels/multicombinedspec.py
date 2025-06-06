from .model_base import JwstDataModel
from .combinedspec import CombinedSpecModel


__all__ = ["MultiCombinedSpecModel", "WFSSMultiCombinedSpecModel"]


class MultiCombinedSpecModel(JwstDataModel):
    """
    A data model for multi-spec images.

    This model has a special member `spec` that can be used to
    deal with an entire spectrum at a time.  It behaves like a list::

       >>> from stdatamodels.jwst.datamodels import CombinedSpecModel
       >>> multispec_model = MultiCombinedSpecModel()
       >>> multispec_model.spec.append(CombinedSpecModel())
       >>> multispec_model.spec[0] # doctest: +SKIP
       <CombinedSpecModel>

    If `init` is a `CombinedSpecModel` instance, an empty `CombinedSpecModel`
    will be created and assigned to attribute `spec[0]`, and the `spec_table`
    attribute from the input `CombinedSpecModel` instance will be copied to
    the first element of `spec`.  `CombinedSpecModel` objects can be appended
    to the `spec` attribute by using its `append` method.

    Attributes
    ----------
    int_times : numpy table
         table of times for each integration
    spec.items.spec_table : numpy table
         Extracted spectral data table
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/multicombinedspec.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, CombinedSpecModel):
            super(MultiCombinedSpecModel, self).__init__(init=None, **kwargs)
            self.spec.append(self.spec.item())
            self.spec[0].spec_table = init.spec_table
            return

        super(MultiCombinedSpecModel, self).__init__(init=init, **kwargs)


class WFSSMultiCombinedSpecModel(JwstDataModel):
    """
    A data model for NIRCam and NIRISS WFSS exposure-averaged 1D spectra.

    This model differs from the other MultiCombinedSpecModel classes in that
    it is designed to hold all the spectra in a WFSS observation in a single
    "flat" table format. Therefore, it contains one spec per spectral order,
    each of which has a `spec_table` attribute that contains the spectral data
    and metadata for all sources in the observation.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/wfss_multicombinedspec.schema"
