import numpy as np
from astropy.io import fits
from numpy.lib.recfunctions import merge_arrays

from stdatamodels.dynamicdq import dynamic_mask
from .dqflags import pixel
from .reference import ReferenceFileModel


__all__ = ['NirspecFlatModel', 'NirspecQuadFlatModel']


def _migrate_fast_variation_table(hdulist):
    # Files produced with NirspecFlatModel and NirspecQuadFlatModel
    # prior to https://github.com/spacetelescope/stdatamodels/pull/183
    # have flat_table tables (stored in the FAST_VARIATION extension)
    # that do not have an "error" column
    # To allow these older files to load, this function
    # fills in the missing error column.
    # We have to iterate over the extensions as the tabl
    for ext in hdulist:
        if ext.name != 'FAST_VARIATION':
            continue
        # check that table has the required columns
        # for older files they might be missing an 'err' column
        table_data = ext.data
        if 'error' not in table_data.dtype.fields:
            if table_data.dtype['wavelength'].shape:
                dtype = [('error', '>f4', table_data.dtype['wavelength'].shape)]
            else:
                dtype = [('error', '>f4')]
            err_column = np.full(table_data.shape[0], np.nan, dtype=dtype)
            table_data = merge_arrays((table_data, err_column), flatten=True)
            ext.data = table_data
    return hdulist


class NirspecFlatModel(ReferenceFileModel):
    """A data model for NIRSpec flat-field reference files.

    Parameters
    __________
    data : numpy float32 array
         NIRSpec flat-field reference data

    dq : numpy uint32 array
         Data quality array

    err : numpy float32 array
         Error estimate

    wavelength : numpy table
         Table of wavelengths for image planes

    flat_table : numpy table
         Table for quickly varying component of flat field

    dq_def : numpy table
         DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/nirspec_flat.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, fits.HDUList):
            init = _migrate_fast_variation_table(init)

        super(NirspecFlatModel, self).__init__(init=init, **kwargs)

        if self.dq is not None or self.dq_def is not None:
            self.dq = dynamic_mask(self, pixel)

        # Implicitly create arrays
        self.dq = self.dq
        self.err = self.err

    def _migrate_hdulist(self, hdulist):
        return _migrate_fast_variation_table(hdulist)


class NirspecQuadFlatModel(ReferenceFileModel):
    """A data model for NIRSpec flat-field files that differ by quadrant.

    Parameters
    __________
    quadrants.items.data : numpy float32 array


    quadrants.items.dq : numpy uint32 array


    quadrants.items.err : numpy float32 array


    quadrants.items.wavelength : numpy table
         Table of wavelengths for image planes

    quadrants.items.flat_table : numpy table
         Table for quickly varying component of flat field

    dq_def : numpy table
         DQ flag definitions
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/nirspec_quad_flat.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, fits.HDUList):
            init = _migrate_fast_variation_table(init)

        if isinstance(init, NirspecFlatModel):
            super(NirspecQuadFlatModel, self).__init__(init=None, **kwargs)
            self.update(init)
            self.quadrants.append(self.quadrants.item())
            self.quadrants[0].data = init.data
            self.quadrants[0].dq = init.dq
            self.quadrants[0].err = init.err
            self.quadrants[0].wavelength = init.wavelength
            self.quadrants[0].flat_table = init.flat_table
            self.quadrants[0].dq_def = init.dq_def
            self.quadrants[0].dq = dynamic_mask(self.quadrants[0])
            return

        super(NirspecQuadFlatModel, self).__init__(init=init, **kwargs)

    def _migrate_hdulist(self, hdulist):
        return _migrate_fast_variation_table(hdulist)
