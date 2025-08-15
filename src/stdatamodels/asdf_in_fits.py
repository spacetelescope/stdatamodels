import warnings

import asdf
from astropy.io import fits

from . import fits_support

__all__ = ["write", "open", "to_hdulist"]

# This API is intended to replace the removed asdf.AsdfInFits
# for community (non-pipeline) usage. When considering changes
# a wider search for usage beyond pipeline code and documentation
# is recommended as well as longer deprecation periods that
# aren't as closely linked to pipeline releases.


def to_hdulist(tree, hdulist=None):
    """
    Add ASDF data to an hdulist (or create one if needed).

    Parameters
    ----------
    tree : ASDF tree or dict
        ASDF data to add to the hdulist

    hdulist : `astropy.io.fits.HDUList`
        Optional HDUList to add the ASDF data to. If not provided,
        a new HDUList will be created.

    Returns
    -------
    `astropy.io.fits.HDUList` :
        HDUList with added ASDF data.
    """
    return fits_support.to_fits(tree, None, hdulist=hdulist)  # no custom schema


def write(filename, tree, hdulist=None, **kwargs):
    """
    Write ASDF data inside a FITS file.

    Parameters
    ----------
    filename : str or path
        Filename where the resulting fits file containing the ASDF
        data will be saved. This is passed on to
        :meth:`astropy.io.fits.HDUList.writeto`
    tree : ASDF tree or dict
        ASDF data to save in the fits file
    hdulist : `astropy.io.fits.HDUList`
        Optional HDUList to write the ASDF data to. If not provided,
        a new HDUList will be created.
    **kwargs
        Additional keyword arguments to pass to :meth:`astropy.io.fits.HDUList.writeto`
    """
    to_hdulist(tree, hdulist=hdulist).writeto(filename, **kwargs)


def open(filename_or_hdu, ignore_missing_extensions=False, ignore_unrecognized_tag=False, **kwargs):  # noqa: A001
    """
    Read ASDF data embedded in a fits file.

    Parameters
    ----------
    filename_or_hdu : str, path, `astropy.io.fits.HDUList`
        Filename of the FITS file or an open `astropy.io.fits.HDUList`
        containing the ASDF data. If a filename is provided it
        will be opened with :func:`astropy.io.fits.open`.
    ignore_missing_extensions : bool, optional
        If `True`, ignore missing extensions in the FITS file.
        Defaults to `False`.
    ignore_unrecognized_tag : bool, optional
        If `True`, ignore unrecognized tags in the ASDF data.
        Defaults to `False`.
    **kwargs
        Additional keyword arguments to pass to asdf.open.
        Usage of kwargs is deprecated and will be removed in a future version.

    Returns
    -------
    af : :obj:`asdf.AsdfFile`
        :obj:`asdf.AsdfFile` created from ASDF data embedded in the opened
        FITS file.
    """
    if kwargs:
        warnings.warn(
            "Passing additional keyword arguments from asdf_in_fits.open into asdf.open "
            "is deprecated and will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )
    is_hdu = isinstance(filename_or_hdu, fits.HDUList)
    hdulist = filename_or_hdu if is_hdu else fits.open(filename_or_hdu)
    af = fits_support.from_fits_asdf(
        hdulist,
        ignore_missing_extensions=ignore_missing_extensions,
        ignore_unrecognized_tag=ignore_unrecognized_tag,
        **kwargs,
    )

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
