from .reference import ReferenceFileModel

__all__ = ['MirMrsPtCorrModel']


class MirMrsPtCorrModel(ReferenceFileModel):
    """
    A data model for MIRI mrs IFU across-slice corrections file.

    Parameters
    __________
    init : any
        Any of the initializers supported by `~jwst.datamodels.DataModel`.

    leakcor_table : numpy table
         IFU spectral leak correction (fractional, Jy to Jy)

    tracor_table : numpy table
         IFU across slice transmission correction

    wavcorr_optical_table : numpy table
         IFU across slice wavelength offset table 1

    wavcorr_xslice_table : numpy table
         IFU across slice wavelength offset table 2

    wavcorr_shift_table : numpy table
         IFU across slice wavelength offset table 3

    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/miri_mrsptcorr.schema"
