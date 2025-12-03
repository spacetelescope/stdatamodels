Switching over from ``astropy.io.fits``
=======================================

This section describes how to port code that uses :mod:`astropy.io.fits`
to use :mod:`stdatamodels.jwst.datamodels`. Please note that ``stdatamodels``
is only intended for use with JWST data products, and is not a general-purpose
FITS file reader/writer. If you attempt to load arbitrary FITS files, you may
encounter unexpected behavior.

.. _datamodels-open:

Opening a file
--------------

Instead of::

    from astropy.io import fits
    with fits.open("myfile.fits") as hdulist:
        ...

use::

    from stdatamodels.jwst import datamodels
    with datamodels.open("myfile.fits") as model:
        ...

The :func:`~stdatamodels.jwst.datamodels.open` method checks if the ``DATAMODL`` FITS keyword has
been set (or, for ASDF files, the ``meta.model_type`` attribute), 
which records the DataModel that was used to create the file.
If the keyword is not set, then :func:`~stdatamodels.jwst.datamodels.open` does its best to
guess the best DataModel to use and emits a :class:`~stdatamodels.exceptions.NoTypeWarning`.

An alternative is to use::

    from stdatamodels.jwst.datamodels import ImageModel
    with ImageModel("myfile.fits") as model:
        ...

In place of :class:`~stdatamodels.jwst.datamodels.ImageModel`, use the type of data one expects to find in
the file.  For example, if a spectrum is expected, use
:class:`~stdatamodels.jwst.datamodels.SpecModel`.

Accessing data
--------------

Data should be accessed through one of the pre-defined data members on
the model (``data``, ``dq``, ``err``).  There is no longer a need to search
through the HDU list to find the data.

Instead of::

    hdulist['SCI'].data
    hdulist['DQ'].data
    hdulist['ERR'].data

use::

    model.data
    model.dq
    model.err

Accessing keywords
------------------

The data model hides direct access to FITS header keywords.  Instead,
use the :ref:`metadata` tree.

There is a convenience method, :meth:`~stdatamodels.DataModel.find_fits_keyword` to find where a
FITS keyword is used in the metadata tree::

    >>> from stdatamodels.jwst.datamodels import JwstDataModel
    >>> # First, create a model of the desired type
    >>> model = JwstDataModel()
    >>> model.find_fits_keyword('DATE-OBS')
    ['meta.observation.date']

This information shows that instead of::

    print(hdulist[0].header['DATE-OBS'])

use::

    print(model.meta.observation.date)

Extra FITS keywords
-------------------

When loading FITS files, there may be keywords that are not
listed in the schema for that data model.  These "extra" FITS keywords
are put into the model in the ``extra_fits`` namespace.

Under the ``extra_fits`` namespace is a section for each FITS extension
that contains schema-unmapped header information or data,
and within those are the extra FITS keywords.  For example, if
the FITS file contains keywords ``FOO="bar"`` and ``BAZ="qux"`` in the primary header
that are not defined in the schema, they will be loaded into::
    
    model.extra_fits.PRIMARY.header

as a list-of-lists: ``[['FOO', 'bar', ''], ['BAZ', 'qux', '']]``.

The ``extra_fits`` namespace may also hold entire hdus that are not
mapped to a data model.  For example, if the FITS file contains an
extension called ``EXTRA``, it can be accessed using::

    model.extra_fits.EXTRA

and its data array can be accessed using::

    model.extra_fits.EXTRA.data

To get a list of everything in ``extra_fits`` as a dictionary, use::

    model.extra_fits.instance

(``instance`` can be used at any node in the tree, not just ``extra_fits``,
to return a dictionary of rest of the tree structure at that node.)

.. note::

    The ``jwst`` pipeline never directly accesses information
    from ``extra_fits``, as this would bypass the schema validation and partly defeat
    the purpose of the data model. If you are developing a model for pipeline use, 
    it is strongly recommended to define any new
    (meta)data in the datamodel schema early on in the development process.
