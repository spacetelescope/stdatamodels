import numpy as np
from astropy.io import fits
from numpy.lib.recfunctions import append_fields

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
        if ext.data is None or not isinstance(ext, fits.BinTableHDU):
            continue

        table_data = ext.data
        if "group_skip1" not in table_data.dtype.names:
            # Create the missing column.
            # Defaulting to 1 as per the baseline requirement.
            new_col = np.full(table_data.shape[0], 1, dtype=">i4")

            # This returns a new structured array with the column attached
            ext.data = append_fields(
                table_data, "group_skip1", new_col, usemask=False, asrecarray=True
            )

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
