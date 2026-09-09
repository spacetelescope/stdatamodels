import numpy as np
from asdf.tags.core.ndarray import asdf_datatype_to_numpy_dtype
from astropy.io import fits

from .model_base import JwstDataModel

__all__ = ["CombinedSpecModel", "WFSSCombinedSpecModel"]


class CombinedSpecModel(JwstDataModel):
    """
    A data model for combined 1D spectra.

    Attributes
    ----------
    spec_table : numpy table
         Combined, extracted spectral data table
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/combinedspec.schema"


class WFSSCombinedSpecModel(JwstDataModel):
    """
    A data model for NIRCam and NIRISS WFSS exposure-averaged 1D spectra.

    This model is designed to hold the combined spectra from a WFSS observation,
    with each spectrum represented as a single row in the ``spec_table`` attribute.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/wfss_combinedspec.schema"

    def _migrate_hdulist(self, hdulist):
        """Handle old-style files lacking contam estimate table columns."""  # numpydoc ignore: RT01
        for ext in hdulist:
            if ext.name == "COMBINE1D" and isinstance(ext, fits.BinTableHDU):
                table_data = ext.data
                # for both missing attributes, find the schema-defined table index and datatype
                expected = self.schema["properties"]["spec_table"]["datatype"]
                expected_names = [col["name"] for col in expected]
                expected_dtypes = [
                    asdf_datatype_to_numpy_dtype(col["datatype"]) for col in expected
                ]
                names = ["CONTAM_FLUX", "CONTAM_SURF_BRIGHT"]
                for name in names:
                    if name not in table_data.dtype.names:
                        # 1. Create new NaN-filled Column object based on data type from schema
                        idx = expected_names.index(name)
                        numpy_dtype = expected_dtypes[idx]
                        fits_dtype_str = fits.column._ColumnFormat.from_recformat(numpy_dtype)
                        new_col = fits.Column(
                            name=name,
                            format=fits_dtype_str,
                            array=np.full(len(ext.data), np.nan, dtype=numpy_dtype),
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
