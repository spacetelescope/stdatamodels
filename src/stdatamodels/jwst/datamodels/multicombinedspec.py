import numpy as np
from astropy.io import fits
from numpy.lib.recfunctions import merge_arrays

from .combinedspec import CombinedSpecModel
from .model_base import JwstDataModel

__all__ = ["MultiCombinedSpecModel", "WFSSMultiCombinedSpecModel"]


class MultiCombinedSpecModel(JwstDataModel):
    """
    A data model for multi-spec images.

    This model has a special member ``spec`` that can be used to
    deal with an entire spectrum at a time.  It behaves like a list::

       >>> from stdatamodels.jwst.datamodels import CombinedSpecModel
       >>> multispec_model = MultiCombinedSpecModel()
       >>> multispec_model.spec.append(CombinedSpecModel())
       >>> multispec_model.spec[0] # doctest: +SKIP
       <CombinedSpecModel>

    If ``init`` is a `~stdatamodels.jwst.datamodels.CombinedSpecModel`
    instance, an empty `~stdatamodels.jwst.datamodels.CombinedSpecModel`
    will be created and assigned to attribute ``spec[0]``, and the ``spec_table``
    attribute from the input `~stdatamodels.jwst.datamodels.CombinedSpecModel`
    instance will be copied to the first element of ``spec``.
    `~stdatamodels.jwst.datamodels.CombinedSpecModel` objects can be appended
    to the ``spec`` attribute by using its ``append`` method.

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

    This model differs from the
    `~stdatamodels.jwst.datamodels.MultiCombinedSpecModel` class in that
    it is designed to hold all the spectra in a WFSS observation in a single
    "flat" table format. Therefore, it contains one spec per spectral order,
    each of which has a ``spec_table`` attribute that contains the spectral data
    and metadata for all sources in the observation.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/wfss_multicombinedspec.schema"

    def _migrate_hdulist(self, hdulist):
        """Handle old-style files lacking contam estimate table columns."""  # numpydoc ignore: RT01
        for ext in hdulist:
            if ext.name == "COMBINE1D" and isinstance(ext, fits.BinTableHDU):
                table_data = ext.data.view(np.recarray)
                # for both missing attributes, find the schema-defined table index and datatype
                expected = self.schema["properties"]["spec"]["items"]["properties"]["spec_table"][
                    "datatype"
                ]
                expected_names = [col["name"] for col in expected]
                names = ["CONTAM_FLUX", "CONTAM_SURF_BRIGHT"]
                for name in names:
                    if name not in table_data.dtype.names:
                        # Make the new column and fill it with NaN
                        idx = expected_names.index(name)
                        if table_data.dtype["FLUX"].shape:
                            dtype = [(name, "f4", table_data.dtype["FLUX"].shape)]
                        else:
                            dtype = [(name, "f4")]
                        new_column = np.full(table_data.shape[0], np.nan, dtype=dtype)

                        # Insert new column into the correct position in the table data
                        before_names = [
                            field
                            for field in expected_names[:idx]
                            if field in table_data.dtype.names
                        ]
                        after_names = [
                            field
                            for field in expected_names[idx + 1 :]
                            if field in table_data.dtype.names
                        ]
                        arrays_to_merge = (
                            table_data[before_names],
                            new_column,
                            table_data[after_names],
                        )

                        # Merge them and cast the flat fields back into a recarray
                        table_data = merge_arrays(arrays_to_merge, flatten=True, asrecarray=True)
                ext.data = table_data

        return hdulist
