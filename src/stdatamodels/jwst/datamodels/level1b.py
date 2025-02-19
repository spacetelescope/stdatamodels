from .model_base import JwstDataModel
import numpy as np
from numpy.lib.recfunctions import merge_arrays

__all__ = ["Level1bModel"]


def _migrate_moving_target_table(hdulist):
    """
    Add missing columns to prevent validation issues for `jwst` 1.16.0.

    Files produced prior to Build 11.1 will not have columns `mt_v2` or
    `mt_v3` in the moving_target_table; loading these old files with
    stdatamodels>=2.1.0 will encounter validation errors due to the
    missing columns. This function adds NaN-filled columns where needed
    to pass validation.

    Parameters
    ----------
    hdulist : HDUList
        The input HDUList

    Returns
    -------
    hdulist : HDUList
        The modified HDUList
    """
    for ext in hdulist:
        if ext.name != "MOVING_TARGET_POSITION":
            continue
        table_data = ext.data
        if "mt_v2" not in table_data.dtype.fields:
            dtype_v2 = [("mt_v2", ">f8")]
            dtype_v3 = [("mt_v3", ">f8")]
            mt_v2_col = np.full(table_data.shape[0], np.nan, dtype=dtype_v2)
            mt_v3_col = np.full(table_data.shape[0], np.nan, dtype=dtype_v3)
            table_data = merge_arrays((table_data, mt_v2_col, mt_v3_col), flatten=True)
            ext.data = table_data
    return hdulist


class Level1bModel(JwstDataModel):
    """
    A data model for raw 4D ramps level-1b products.

    Attributes
    ----------
    data : numpy uint16 array
         The science data
    zeroframe : numpy uint16 array
         Zeroframe array
    refout : numpy uint16 array
         Reference Output
    group : numpy table
         group parameters table
    int_times : numpy table
         table of times for each integration
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/level1b.schema"

    def _migrate_hdulist(self, hdulist):
        return _migrate_moving_target_table(hdulist)
