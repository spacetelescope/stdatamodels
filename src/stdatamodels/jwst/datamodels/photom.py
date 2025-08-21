import numpy as np

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


class _PhotomModel(ReferenceFileModel):
    """Implement a validation scheme for photom models."""

    def validate(self):
        """
        Validate optional timecoeff extensions.

        If present, timecoeff_linear, timecoeff_exponential, and timecoeff_powerlaw
        extensions must match the length and descriptive columns present in the
        phot_table extension.
        """
        super().validate()
        try:
            timecoeff = ["timecoeff_linear", "timecoeff_exponential", "timecoeff_powerlaw"]
            for extension in timecoeff:
                message = f"Model.phot_table and Model.{extension} do not match"
                if self.hasattr("phot_table") and self.hasattr(extension):
                    table = getattr(self, extension)
                    assert len(self.phot_table) == len(table), message

                    phot_columns = [
                        dtype["name"]
                        for dtype in self.schema["properties"]["phot_table"]["datatype"]
                    ]
                    timecoeff_columns = [
                        dtype["name"] for dtype in self.schema["properties"][extension]["datatype"]
                    ]
                    for col in phot_columns:
                        if col in timecoeff_columns:
                            assert np.all(self.phot_table[col] == table[col]), message

        except AssertionError as errmsg:
            self.print_err(str(errmsg))


class FgsImgPhotomModel(_PhotomModel):
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


class MirImgPhotomModel(_PhotomModel):
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

    def __init__(self, init=None, **kwargs):
        super(MirImgPhotomModel, self).__init__(init=init, **kwargs)


class MirLrsPhotomModel(_PhotomModel):
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

    The MIRI MRS photom model does not yet have multiple timecoeff
    tables, so it inherits directly from ReferenceFileModel, unlike
    the other photom models.

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
    timecoeff_powerlaw_ch1 : numpy table
        A table of time and wavelength dependent throughput corrections
        for channel 1 using powerlaw model.
    timecoeff_powerlaw_ch2 : numpy table
        A table of time and wavelength dependent throughput corrections
        for channel 2 using powerlaw model.
    timecoeff_powerlaw_ch3 : numpy table
        A table of time and wavelength dependent throughput corrections
        for channel 3 using powerlaw model.
    timecoeff_powerlaw_ch4 : numpy table
        A table of time and wavelength dependent throughput corrections
        for channel 4 using powerlaw model.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/mirmrs_photom.schema"

    def __init__(self, init=None, **kwargs):
        super(MirMrsPhotomModel, self).__init__(init=init, **kwargs)

        self.dq = dynamic_mask(self, pixel)


class NrcImgPhotomModel(_PhotomModel):
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


class NrcWfssPhotomModel(_PhotomModel):
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


class NisImgPhotomModel(_PhotomModel):
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


class NisWfssPhotomModel(_PhotomModel):
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


class NisSossPhotomModel(_PhotomModel):
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


class NrsFsPhotomModel(_PhotomModel):
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


class NrsMosPhotomModel(_PhotomModel):
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
