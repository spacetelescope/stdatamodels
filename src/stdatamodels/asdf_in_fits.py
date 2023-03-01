import asdf
from astropy.io import fits

from . import fits_support


__all__ = [
    'write',
    'open'
]


def write(filename, tree, hdulist=None, **kwargs):
    """Write ASDF data inside a fits file

    Parameters
    ----------
    filename : str or path
        Filename where the resulting fits file containing the ASDF
        data will be saved. This is passed on to
        :func:`astropy.io.fits.HDUList.writeto`

    tree : ASDF tree or dict
        ASDF data to save in the fits file

    kwargs : variable keyword arguments
        Passed on to :func:`astropy.io.fits.HDUList.writeto`
    """
    hdulist = fits_support.to_fits(tree, None, hdulist=hdulist)  # no custom schema
    hdulist.writeto(filename, **kwargs)


def open(filename_or_hdu, **kwargs):
    """Read ASDF data embedded in a fits file

    Parameters
    ----------
    filename_or_hdu : str, path, `astropy.io.fits.HDUList`
        Filename of the fits file or an open `astropy.io.fits.HDUList`
        containing the ASDF data. If a filename is provided it
        will be opened with :func:`astropy.io.fits.open`.

    kwargs : variable keyword arguments
        Passed on to :func:`asdf.open`

    Returns
    -------
    af : :obj:`asdf.AsdfFile`
        :obj:`asdf.AsdfFile` created from ASDF data embeded in the opened
        fits file.
    """

    is_hdu = isinstance(filename_or_hdu, fits.HDUList)
    hdulist = filename_or_hdu if is_hdu else fits.open(filename_or_hdu)
    if 'ignore_missing_extensions' not in kwargs:
        kwargs['ignore_missing_extensions'] = False
    af = fits_support.from_fits_asdf(hdulist, **kwargs)

    if is_hdu:
        # no need to wrap close if input was an HDUList
        return af

    # on close, close hdulist
    def wrap_close(af, hdulist):
        def close():
            asdf.AsdfFile.close(af)
            hdulist.close()
        return close

    af.close = wrap_close(af, hdulist)
    return af
