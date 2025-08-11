import numpy as np
from asdf.tags.core.ndarray import asdf_datatype_to_numpy_dtype
from numpy.lib.recfunctions import merge_arrays

from stdatamodels.dynamicdq import dynamic_mask

from .dqflags import pixel
from .reference import ReferenceFileModel

__all__ = [
    "FgsImgPhotomModel",
    "MirImgPhotomModel",
    "MirLrsPhotomModel",
    "MirMrsPhotomModel",
    "NrcImgPhotomModel",
    "NrcWfssPhotomModel",
    "NisImgPhotomModel",
    "NisSossPhotomModel",
    "NisWfssPhotomModel",
    "NrsFsPhotomModel",
    "NrsMosPhotomModel",
]


class FgsImgPhotomModel(ReferenceFileModel):
    """
    A data model for FGS photom reference files.

    Attributes
    ----------
    phot_table : numpy table
        Photometric flux conversion factors table
        A table-like object containing row selection criteria made up
        of instrument mode parameters and photometric conversion
        factors associated with those modes.

        - photmjsr: float32
        - uncertainty: float32
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/fgsimg_photom.schema"


class MirImgPhotomModel(ReferenceFileModel):
    """
    A data model for MIRI imaging photom reference files.

    Attributes
    ----------
    phot_table : numpy table
        Photometric flux conversion factors table
        A table-like object containing row selection criteria made up
        of instrument mode parameters and photometric conversion
        factors associated with those modes.

       - filter: str[12]
       - subarray: str[15]
       - photmjsr: float32
       - uncertainty: float32

    timecoeff : numpy table
        Table with the coefficients for the time-dependent correction.

       - amplitude: float32
       - tau: float32
       - t0: float32
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/mirimg_photom.schema"

    def _migrate_hdulist(self, hdulist):
        """
        Accommodate old-style time dependence coefficients.

        This method is only called when a datamodel is constructed using a
        HDUList or a string (not when the DataModel is cloned or created
        from an existing DataModel).

        The migration occurs prior to loading the ASDF extension.

        Parameters
        ----------
        hdulist : HDUList
            The opened hdulist that this method should migrate.

        Returns
        -------
        migrated_hdulist : HDUList
            The migrated/updated hdulist. This is identical to the
            input hdulist if no migration is needed.
        """
        # Get the timecoeff extension, if present
        if "TIMECOEFF" not in hdulist or "PHOTOM" not in hdulist:
            return hdulist
        timecoeff = hdulist["TIMECOEFF"]

        # Get defaults for the current table
        subschema = self.schema["properties"]["timecoeff_exponential"]
        table_dtypes = subschema["datatype"]
        table_defaults = subschema["default"]

        # Migrate existing additive correction to a multiplicative one.
        # Assume the timecoeff table size matches the photom table.
        table_data = timecoeff.data
        table_data["amplitude"] /= hdulist["PHOTOM"].data["photmjsr"]

        # Make new arrays from default values
        arrays_to_merge = [table_data]
        n_rows = table_data.shape[0]
        for i, col in enumerate(table_dtypes):
            if col["name"] in table_data.names:
                continue
            else:
                default = table_defaults[i]

            np_dtype = asdf_datatype_to_numpy_dtype(col["datatype"])
            new_col = np.full(n_rows, default, dtype=[(col["name"], np_dtype)])
            arrays_to_merge.append(new_col)
        timecoeff.data = merge_arrays(arrays_to_merge, flatten=True)
        timecoeff.name = "TIMECOEFF_EXPONENTIAL"

        return hdulist

    def __init__(self, init=None, **kwargs):
        super(MirImgPhotomModel, self).__init__(init=init, **kwargs)


class MirLrsPhotomModel(ReferenceFileModel):
    """
    A data model for MIRI LRS photom reference files.

    Attributes
    ----------
    phot_table : numpy table
        Photometric flux conversion factors table
        A table-like object containing row selection criteria made up
        of instrument mode parameters and photometric conversion
        factors associated with those modes.

       - filter: str[12]
       - subarray: str[15]
       - photmjsr: float32
       - uncertainty: float32
       - nelem: int16
       - wavelength: float32[*]
       - relresponse: float32[*]
       - reluncertainty: float32[*]
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/mirlrs_photom.schema"


class MirMrsPhotomModel(ReferenceFileModel):
    """
    A data model for MIRI MRS photom reference files.

    Attributes
    ----------
    init : any
        Any of the initializers supported by `~jwst.datamodels.DataModel`.
    data : numpy array
        An array-like object containing the pixel-by-pixel conversion values
        in units of (MJy / pixel) / (DN / sec).
    err : numpy array
        An array-like object containing the uncertainties in the conversion
        values, in the same units as the data array.
    dq : numpy array
        An array-like object containing bit-encoded data quality flags,
        indicating problem conditions for values in the data array.
    dq_def : numpy array
        A table-like object containing the data quality definitions table.
    pixsiz : numpy array
        An array-like object containing pixel-by-pixel size values, in units of
        square arcseconds (arcsec^2).
    timecoeff_ch1 : numpy table
        A table of time and wavelength dependent throughput corrections
        for channel 1
    timecoeff_ch2 : numpy table
        A table of time and wavelength dependent throughput corrections
        for channel 2
    timecoeff_ch3 : numpy table
        A table of time and wavelength dependent throughput corrections
        for channel 3
    timecoeff_ch4 : numpy table
        A table of time and wavelength dependent throughput corrections
        for channel 4
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/mirmrs_photom.schema"

    def __init__(self, init=None, **kwargs):
        super(MirMrsPhotomModel, self).__init__(init=init, **kwargs)

        self.dq = dynamic_mask(self, pixel)


class NrcImgPhotomModel(ReferenceFileModel):
    """
    A data model for NIRCam imaging photom reference files.

    Attributes
    ----------
    phot_table : numpy table
        Photometric flux conversion factors table
        A table-like object containing row selection criteria made up
        of instrument mode parameters and photometric conversion
        factors associated with those modes.
        The subarray column may appear in newer versions of the photom
        files: it is allowed, but not specified by the schema.

        - filter: str[12]
        - pupil: str[12]
        - photmjsr: float32
        - uncertainty: float32
        - subarray: str[12], optional
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/nrcimg_photom.schema"


class NrcWfssPhotomModel(ReferenceFileModel):
    """
    A data model for NIRCam WFSS photom reference files.

    Attributes
    ----------
    phot_table : numpy table
        Photometric flux conversion factors table
        A table-like object containing row selection criteria made up
        of instrument mode parameters and photometric conversion
        factors associated with those modes.

        - filter: str[12]
        - pupil: str[15]
        - order: int16
        - photmjsr: float32
        - uncertainty: float32
        - nelem: int16
        - wavelength: float32[*]
        - relresponse: float32[*]
        - reluncertainty: float32[*]
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/nrcwfss_photom.schema"


class NisImgPhotomModel(ReferenceFileModel):
    """
    A data model for NIRISS imaging photom reference files.

    Attributes
    ----------
    phot_table : numpy table
        Photometric flux conversion factors table
        A table-like object containing row selection criteria made up
        of instrument mode parameters and photometric conversion
        factors associated with those modes.

        - filter: str[12]
        - pupil: str[12]
        - photmjsr: float32
        - uncertainty: float32
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/nisimg_photom.schema"


class NisWfssPhotomModel(ReferenceFileModel):
    """
    A data model for NIRISS WFSS photom reference files.

    Attributes
    ----------
    phot_table : numpy table
        Photometric flux conversion factors table
        A table-like object containing row selection criteria made up
        of instrument mode parameters and photometric conversion
        factors associated with those modes.

        - filter: str[12]
        - pupil: str[15]
        - order: int16
        - photmjsr: float32
        - uncertainty: float32
        - nelem: int16
        - wavelength: float32[*]
        - relresponse: float32[*]
        - reluncertainty: float32[*]
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/niswfss_photom.schema"


class NisSossPhotomModel(ReferenceFileModel):
    """
    A data model for NIRISS SOSS photom reference files.

    Attributes
    ----------
    phot_table : numpy table
        Photometric flux conversion factors table
        A table-like object containing row selection criteria made up
        of instrument mode parameters and photometric conversion
        factors associated with those modes.

        - filter: str[12]
        - pupil: str[15]
        - order: int16
        - photmj: float32
        - uncertainty: float32
        - nelem: int16
        - wavelength: float32[*]
        - relresponse: float32[*]
        - reluncertainty: float32[*]
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/nissoss_photom.schema"


class NrsFsPhotomModel(ReferenceFileModel):
    """
    A data model for NIRSpec Fixed-Slit photom reference files.

    Attributes
    ----------
    phot_table : numpy table
        Photometric flux conversion factors table
        A table-like object containing row selection criteria made up
        of instrument mode parameters and photometric conversion
        factors associated with those modes.

        - filter: str[12]
        - grating: str[15]
        - slit: str[15]
        - photmj: float32
        - uncertainty: float32
        - nelem: int16
        - wavelength: float32[*]
        - relresponse: float32[*]
        - reluncertainty: float32[*]
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/nrsfs_photom.schema"


class NrsMosPhotomModel(ReferenceFileModel):
    """
    A data model for NIRSpec MOS and IFU photom reference files.

    Attributes
    ----------
    phot_table : numpy table
        Photometric flux conversion factors table
        A table-like object containing row selection criteria made up
        of instrument mode parameters and photometric conversion
        factors associated with those modes.

        - filter: str[12]
        - grating: str[15]
        - photmj: float32
        - uncertainty: float32
        - nelem: int16
        - wavelength: float32[*]
        - relresponse: float32[*]
        - reluncertainty: float32[*]
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/nrsmos_photom.schema"
