.. _asdf_in_fits:

==========
AsdfInFits
==========

:py:mod:`stdatamodels.asdf_in_fits` contains functions to help migrate code that
uses the AsdfInFits format (ASDF data stored in a FITS file)
from `ASDF <https://asdf.readthedocs.io>`_ (which is dropping
support for AsdfInFits) to stdatamodels.

Opening AsdfInFits files
========================

AsdfInFits files can be opened with :func:`stdatamodels.asdf_in_fits.open`.
This function aims to replace previous calls to :func:`asdf.open` or
:func:`asdf.AsdfInFits.open` and can similarly be used in a
`with <https://docs.python.org/3/reference/compound_stmts.html#with>`_
statement. ::

    with stdatamodels.asdf_in_fits.open('some_file.fits') as af:
        # access the contents of `af` as a normal `asdf.AsdfFile`
        pass

It is recommended that a with statement is used to ensure the resulting
`asdf.AsdfFile <https://asdf.readthedocs.io/en/stable/api/asdf.AsdfFile.html>`_
and `astropy.io.fits.HDUList <https://docs.astropy.org/en/stable/io/fits/api/hdulists.html#hdulist>`_ are closed properly.

If a ``with`` statement cannot be used,
:func:`stdatamodels.asdf_in_fits.open` can be used as a regular function
(be sure to close the file when done). ::

    af = stdatamodels.asdf_in_fits.open('some_file.fits')
    # access the contents of `af` as a normal `asdf.AsdfFile`
    af.close()

Writing AsdfInFits files
========================

:func:`stdatamodels.asdf_in_fits.write` can be used to write ASDF data
within a FITS file. ::

    tree = {'sci': [1, 2, 3]}   # data to be stored in ASDF format
    stdatamodels.asdf_in_fits.write('some_file.fits', tree)

This functions is meant to replace calls to :func:`asdf.AsdfInFits.write_to`.
Please see the :func:`stdatamodels.asdf_in_fits.write` documentation for all
available arguments.

:func:`stdatamodels.asdf_in_fits.write` supports references to array data
within the :class:`astropy.io.fits.HDUList`. This can be accomplished by
first creating a :class:`astropy.io.fits.HDUList` and populating it with
data ::

    from astropy.io import fits

    hdulist = fits.HDUList()
    hdulist.append(fits.ImageHDU(np.arange(512, dtype=float), name='SCI'))
    hdulist.append(fits.ImageHDU(np.arange(512, dtype=float), name='DQ'))

Then constructing a tree with references to the **same** data. ::

    tree = {
        'model': {
            'sci': {
                'data': hdulist['SCI'].data,
            },
            'dq': {
                'data': hdulist['DQ'].data,
            }
        }
    }

Finally providing the tree and hdulist to
:func:`stdatamodels.asdf_in_fits.write`. ::

    stdatamodels.asdf_in_fits.write('some_file.fits', tree, hdulist)

When read back with :func:`stdatamodels.asdf_in_fits.open` the data for
``sci`` and ``dq`` will be read from the HDUList instead of from the
ASDF data embeded in the HDUList.
