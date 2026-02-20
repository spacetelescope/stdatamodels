import numpy as np
from astropy.io import fits

from .reference import ReferenceFileModel

__all__ = ["RSCDModel"]


def _migrate_rscd_table(hdulist):
    # Files produced with RSCDModel
    # prior to https://github.com/spacetelescope/stdatamodels/pull/638
    # did not have a column in the RSCD table for the number of groups
    # to skip in the first int
    # To allow these older files to load, this function
    # fills in the missing group_skip1 column.
    # There is just 1 ext in the hdulist

    for ext in hdulist:
        # RSCD tables are usually in the first BinTableHDU
        if ext.name == "RSCD_GROUP_SKIP" and isinstance(ext, fits.BinTableHDU):
            if ext.data is not None and len(ext.data) > 0:
                table_data = ext.data
                # 1. check if the column exist
                if "group_skip1" not in table_data.dtype.names:
                    # Create the missing column.
                    # Defaulting to -1. If the JWST RSCD step see -1 it will issue
                    # a warning that an old rscd file is being used and set the
                    # the value to 1.

                    new_col = fits.Column(
                        name="group_skip1",
                        format="J",
                        array=np.full(len(ext.data), -1, dtype=">i4"),
                    )

                    # 2. Create a new HDU by merging existing columns with the new one
                    new_cols = fits.ColDefs(ext.columns) + fits.ColDefs([new_col])

                    # 3. Create a temporary HDU to extract the correct data and header
                    new_hdu = fits.BinTableHDU.from_columns(new_cols)

                    # Update the existing extension's data and header
                    ext.data = new_hdu.data
                    ext.header = new_hdu.header
                    ext.header["EXTNAME"] = "RSCD_GROUP_SKIP"

    return hdulist


class RSCDModel(ReferenceFileModel):
    """
    A data model for the RSCD reference file.

    Attributes
    ----------
    rscd_group_skip_table : numpy table
        Reference table for RSCD correction baseline correction
        A table with 4 columns that set the number of groups to skip for each
        subarray and readpatt
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/rscd.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, fits.HDUList):
            init = _migrate_rscd_table(init)

        #  Pass the repaired init to the actual DataModel machinery
        super().__init__(init=init, **kwargs)

    def _migrate_hdulist(self, hdulist):
        return _migrate_rscd_table(hdulist)
