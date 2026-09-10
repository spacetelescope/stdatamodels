import numpy as np
from asdf.tags.core.ndarray import asdf_datatype_to_numpy_dtype
from astropy.io import fits

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
                table_data = ext.data
                # for both missing attributes, find the schema-defined table index and datatype
                expected = self.schema["properties"]["spec"]["items"]["properties"]["spec_table"][
                    "datatype"
                ]
                expected_names = [col["name"] for col in expected]
                expected_dtypes = [
                    asdf_datatype_to_numpy_dtype(col["datatype"]) for col in expected
                ]
                names = ["CONTAM_FLUX", "CONTAM_SURF_BRIGHT"]
                for name in names:
                    if name not in table_data.dtype.names:
                        # 1. Create new NaN-filled Column object based on data type from schema
                        nelem = ext.data["FLUX"].shape[1]
                        idx = expected_names.index(name)
                        numpy_dtype = expected_dtypes[idx]
                        fits_dtype_str = fits.column._ColumnFormat.from_recformat(numpy_dtype)
                        new_col = fits.Column(
                            name=name,
                            format=f"{nelem}{fits_dtype_str}",
                            dim=f"({nelem})",
                            array=np.full(ext.data["FLUX"].shape, np.nan, dtype=numpy_dtype),
                        )
                        # 2. Create a new HDU by merging existing columns with the new one
                        new_cols = (
                            fits.ColDefs(ext.columns[:idx])
                            + fits.ColDefs([new_col])
                            + fits.ColDefs(ext.columns[idx:])
                        )

                        # 3. Create a temporary HDU to extract the correct data and header
                        new_hdu = fits.BinTableHDU.from_columns(new_cols)
                        ext.data = new_hdu.data
                        ext.header.update(new_hdu.header)

        return hdulist
