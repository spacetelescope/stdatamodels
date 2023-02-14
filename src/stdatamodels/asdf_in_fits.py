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


def open(filename, **kwargs):
    """Read ASDF data embedded in a fits file

    Parameters
    ----------
    filename : str, path
        Filename of the fits file containing the ASDF data. This will
        be opened with :func:`astropy.io.fits.open`

    kwargs : variable keyword arguments
        Passed on to :func:`asdf.open`

    Returns
    -------
    af : :obj:`asdf.AsdfFile`
        :obj:`asdf.AsdfFile` created from ASDF data embeded in the opened
        fits file.
    """

    hdulist = fits.open(filename)
    if 'ignore_missing_extensions' not in kwargs:
        kwargs['ignore_missing_extensions'] = False
    af = fits_support.from_fits_asdf(hdulist, **kwargs)

    # on close, close hdulist
    def wrap_close(af, hdulist):
        def close():
            asdf.AsdfFile.close(af)
            hdulist.close()
        return close

    af.close = wrap_close(af, hdulist)
    return af
