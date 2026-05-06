from .reference import ReferenceFileModel

__all__ = ["SpecPsfModel"]


def _migrate_psf_keywords(hdulist):
    """
    Migrate PSF keywords from primary HDU to first PSF extension.

    Files produced with SpecPsfModel prior to
    https://github.com/spacetelescope/stdatamodels/pull/734
    expected a single PSF/WAVE extension, with descriptive keywords
    in the primary header. This function copies these keywords to
    the correct place in the new schema that allows for multiple
    PSFs in the same file.

    Parameters
    ----------
    hdulist : HDUList
        FITS HDUList to read.

    Returns
    -------
    hdulist : HDUList
        The updated HDUList.
    """
    keys_to_copy = ["APERTURE", "CENTCOL", "CENTROW", "SUBPIX"]
    if len(hdulist) == 3:
        primary_header = hdulist[0].header
        psf_ext = hdulist[1]
        if psf_ext.name != "PSF":
            return hdulist
        for key in keys_to_copy:
            if key == "APERTURE":
                value = primary_header.get(key, "ANY")
            else:
                value = primary_header.get(key, None)
            if value is not None:
                psf_ext.header[key] = value

    return hdulist


class SpecPsfModel(ReferenceFileModel):
    """
    A data model for spectral PSF reference data.

    PSF models are contained in a list, under the ``apertures``
    attribute.

    Attributes
    ----------
    apertures.items.data : ndarray
        2D PSF image.
    apertures.items.wave : ndarray
        1D wavelength image.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/specpsf.schema"

    def __init__(self, init=None, **kwargs):
        super(SpecPsfModel, self).__init__(init=init, **kwargs)

    def _migrate_hdulist(self, hdulist):
        return _migrate_psf_keywords(hdulist)
