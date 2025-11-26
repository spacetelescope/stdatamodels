.. _datamodels:

Working with models
===================

Creating a data model from scratch
----------------------------------

To create a new :class:`~stdatamodels.jwst.datamodels.ImageModel`,
just call its constructor.  To create a
new model where all of the arrays will have default values, simply
provide a shape as the first argument::

    from stdatamodels.jwst.datamodels import ImageModel
    with ImageModel((1024, 1024)) as im:
        ...

In this form, the memory for the arrays will not be allocated until
the arrays are accessed.  This is useful if, for example, you don't
need a data quality array -- the memory for such an array will not be
consumed::

  # Print out the data array.  It is allocated here on first access
  # and defaults to being filled with zeros.
  print(im.data)

If you already have data in a numpy array, you can also create a model
using that array by passing it in as a data keyword argument::

    data = np.empty((50, 50))
    dq = np.empty((50, 50))
    with ImageModel(data=data, dq=dq) as im:
        ...

Loading a data model from a file
--------------------------------

The :func:`~stdatamodels.jwst.datamodels.open` function is a convenient way to create a
model from a file on disk.  It may be passed any of the following:

    - a path to a FITS file
    - a path to an ASDF file
    - a :class:`astropy.io.fits.HDUList` object
    - a readable file-like object

The file will be opened, and based on the nature of the data in the
file, the correct data model class will be returned.  For example, if
the file contains 2-dimensional data, an :class:`~stdatamodels.jwst.datamodels.ImageModel` instance will be
returned.  You will generally want to instantiate a model using a
``with`` statement so that the file will be closed automatically when
exiting the ``with`` block.

::

    from stdatamodels.jwst import datamodels
    with datamodels.open("myimage.fits") as im:
        assert isinstance(im, datamodels.ImageModel)

If you know the type of data stored in the file, or you want to ensure
that what is being loaded is of a particular type, use the constructor
of the desired concrete class.  For example, if you want to ensure
that the file being opened contains 2-dimensional image data::

    from stdatamodels.jwst.datamodels import ImageModel
    with ImageModel("myimage.fits") as im:
        # raises exception if myimage.fits is not an image file
        pass

This will raise an exception if the file contains data of the wrong
shape.

Saving a data model to a file
-----------------------------

Simply call the :meth:`~stdatamodels.DataModel.save` method on the model instance.  The format to
save into will either be deduced from the filename (if provided) or
the ``format`` keyword argument::

    im.save("myimage.fits")

.. note::

   Unlike :mod:`astropy.io.fits`, :meth:`~stdatamodels.DataModel.save` always clobbers the output file.

Reading Metadata Only
---------------------

The ``datamodels.open`` method loads the entire file into memory and validates it against
its schema. While this is a good thing in most cases, there are times when read-only
access to metadata is useful.
To access the metadata without loading the entire file, use the
``datamodels.read_metadata`` method.  For example, to access the ``s_region``, use
the following code::

.. doctest-skip::

    >>> from stdatamodels.jwst.datamodels import read_metadata
    >>> meta = read_metadata("myfile.fits")
    >>> print(meta["meta.wcsinfo.s_region"])

Notice that the metadata is returned as a flat dictionary by default.
The keys are the dot-separated names of the metadata elements, and
the values are the corresponding values in the file. A nested dictionary
will be returned instead if the ``flatten`` keyword argument is set to False.

.. warning::
  
  This method bypasses schema validation, so use it with caution.
  It also only returns metadata that is mapped to FITS keywords,
  so some useful items (e.g. ``meta.wcs``) will be missing.

Looking at the contents of a model
----------------------------------

Use :meth:`~stdatamodels.DataModel.info` to look at the contents of a data model. It renders
the underlying ASDF tree starting at the root or a specified ``node``.
The number of displayed rows is controlled by the ``max_row`` argument::

  im.info()
  root.tree (AsdfObject)
  ├─asdf_library (Software)
  │ ├─author (str): Space Telescope Science Institute
  │ ├─homepage (str): http://github.com/spacetelescope/asdf
  │ ├─name (str): asdf
  │ └─version (str): 2.5.2a1.dev12+g12aa460
  ├─history (dict)
  │ └─extensions (list) ...
  ├─data (ndarray): shape=(2048, 2048), dtype=float32
  ├─dq (ndarray): shape=(2048, 2048), dtype=uint32
  ├─err (ndarray): shape=(2048, 2048), dtype=float32
  ├─meta (dict)
  │ ├─aperture (dict) ...
  │ ├─bunit_data (str): DN/s
  │ ├─bunit_err (str): DN/s
  │ ├─cal_step (dict) ...
  │ ├─calibration_software_revision (str): 3bfd782b
  │ ├─calibration_software_version (str): 0.14.3a1.dev133+g3bfd782b.d20200216
  │ ├─coordinates (dict) ...
  │ └─28 not shown
  ├─var_poisson (ndarray): shape=(2048, 2048), dtype=float32
  ├─var_rnoise (ndarray): shape=(2048, 2048), dtype=float32
  └─extra_fits (dict) ...
  Some nodes not shown.


Searching a model
-----------------

:meth:`~stdatamodels.DataModel.search` can be used to search the ASDF tree by ``key`` or
``value``::

  im.search(key='filter')

  root.tree (AsdfObject)
  └─meta (dict)
  ├─instrument (dict)
  │ └─filter (str): F170LP
  └─ref_file (dict)
    └─filteroffset (dict)

Data Arrays
-----------
Most datamodels have one or more data arrays as attributes.
For most datamodels containing science data, the primary data array is
accessible through the ``data`` attribute.  Other commonly used data arrays
are ``dq`` (data quality) and ``err`` (uncertainty/error).

The ``data``, ``err``, ``dq``, etc., attributes of most models are assumed to be
numpy.ndarray arrays, or at least objects that have some of the attributes
of these arrays.  ``numpy`` is used explicitly to create these arrays in some
cases (e.g. when a default value is needed).  The ``data`` and ``err`` arrays
are a floating point type, and the data quality arrays are an integer type.

Metadata
--------
Metadata information associated with a data model is accessed through
its `meta` member.  For example, to access the date that an
observation was made::

    print(model.meta.observation.date)

Metadata values are automatically type-checked against the schema when
they are set. Therefore, setting a keyword which expects a number to a
string will raise an exception::

    >>> from stdatamodels.jwst.datamodels import ImageModel
    >>> model = ImageModel()
    >>> model.meta.target.ra = "foo"    # doctest: +SKIP
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "site-packages/jwst.datamodels/schema.py", line 672, in __setattr__
        object.__setattr__(self, attr, val)
      File "site-packages/jwst.datamodels/schema.py", line 490, in __set__
        val = self.to_basic_type(val)
      File "site-packages/jwst.datamodels/schema.py", line 422, in to_basic_type
        raise ValueError(e.message)
    ValueError: 'foo' is not of type u'number'

The set of available metadata elements is defined in a YAML Schema
that ships with `jwst.datamodels`.

There is also a utility method for finding elements in the metadata
schema.  `search_schema` will search the schema for the given
substring in metadata names as well as their documentation.  The
search is case-insensitive::

    >>> from stdatamodels.jwst.datamodels import ImageModel
    >>> # Create a model of the desired type
    >>> model = ImageModel()
    >>> # Call `search_schema` on it to find possibly related elements.
    >>> model.search_schema('target')
    meta.target
    <BLANKLINE>
    meta.target.catalog_name
    <BLANKLINE>
    meta.target.category
    <BLANKLINE>
    meta.target.dec
    <BLANKLINE>
    meta.target.dec_uncertainty
    <BLANKLINE>
    meta.target.description
    <BLANKLINE>
    meta.target.proper_motion_dec
    <BLANKLINE>
    meta.target.proper_motion_epoch
    <BLANKLINE>
    meta.target.proper_motion_ra
    <BLANKLINE>
    meta.target.proposer_dec
    <BLANKLINE>
    meta.target.proposer_name
    <BLANKLINE>
    meta.target.proposer_ra
    <BLANKLINE>
    meta.target.ra
    <BLANKLINE>
    meta.target.ra_uncertainty
    <BLANKLINE>
    meta.target.source_type
    <BLANKLINE>
    meta.target.source_type_apt
    <BLANKLINE>
    meta.target.type
    <BLANKLINE>
    meta.visit.internal_target
    <BLANKLINE>


An alternative method to get and set metadata values is to use a
dot-separated name as a dictionary lookup.  This is useful for
databases, such as CRDS, where the path to the metadata element is
most conveniently stored as a string.  The following two lines are
equivalent::

    print(model['meta.observation.date'])
    print(model.meta.observation.date)

Copying a model
---------------

To create a new model based on another model, simply use its :meth:`~stdatamodels.DataModel.copy`
method.  This will perform a deep-copy: that is, no changes to the
original model will propagate to the new model::

    new_model = old_model.copy()

It is also possible to copy all of the known metadata from one
model into a new one using the :meth:`~stdatamodels.DataModel.update` method::

    new_model.update(old_model)

History information
-------------------

Models contain a list of history records, accessed through the
``history`` attribute.  This is just an ordered list of strings --
nothing more sophisticated.

To get to the history::

    entries = model.history
    for entry in entries:
      pass

To add an entry to the history, first create the entry by calling
``stdatamodels.util.create_history_entry`` and appending the entry to the model
history::

    import stdatamodels
    entry = stdatamodels.util.create_history_entry("Processed through the frobulator step")
    model.history.append(entry)

These history entries are stored in ``HISTORY`` keywords when saving
to FITS format. As an option, history entries can contain a dictionary
with a description of the software used. The dictionary must have the
following keys:

  ``name``: The name of the software
  ``author``: The author or institution that produced the software
  ``homepage``: A URI to the homepage of the software
  ``version``: The version of the software

The calling sequence to create  a history entry with the software
description is::

  entry =  stdatamodels.util.create_history_entry(description, software=software_dict)

where the second argument is the dictionary with the keywords
mentioned.

Working with lists
------------------

Unlike ordinary Python lists, lists in the schema may be restricted to
only accept a certain set of values.  Items may be added to lists in
two ways: by passing a dictionary containing the desired key/value
pairs for the object, or using the lists special method `item` to
create a metadata object and then assigning that to the list.

For example, suppose the metadata element `meta.transformations` is a
list of transformation objects, each of which has a `type` (string)
and a `coeff` (number) member.  We can assign elements to the list in
the following equivalent ways::

.. doctest-skip::

    >>> trans = model.meta.transformations.item()
    >>> trans.type = 'SIN'
    >>> trans.coeff = 42.0
    >>> model.meta.transformations.append(trans)
    >>> model.meta.transformations.append({'type': 'SIN', 'coeff': 42.0})

When accessing the items of the list, the result is a normal metadata
object where the attributes are type-checked::

.. doctest-skip::
  
    >>> trans = model.meta.transformations[0]
    >>> print(trans)
    <jwst.datamodels.schema.Transformations object at 0x123a810>
    >>> print(trans.type)
    SIN
    >>> trans.type = 42.0
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "site-packages/jwst.datamodels/schema.py", line 672, in __setattr__
         object.__setattr__(self, attr, val)
      File "site-packages/jwst.datamodels/schema.py", line 490, in __set__
         val = self.to_basic_type(val)
      File "site-packages/jwst.datamodels/schema.py", line 422, in to_basic_type
         raise ValueError(e.message)
    ValueError: 42.0 is not of type u'string'

Environment Variables
---------------------

There are a number of environment variables that affect how models are read.

PASS_INVALID_VALUES
  Used by :class:`~stdatamodels.jwst.datamodels.JwstDataModel` when instantiating
  a model from a file. If ``True``, values that do not validate the schema will
  still be added to the metadata. If ``False``, they will be set to ``None``.
  Default is ``False``.

STRICT_VALIDATION
  Used by :class:`~stdatamodels.jwst.datamodels.JwstDataModel` when instantiating a model from a file.
  If ``True``, schema validation errors will generate an exception.
  If ``False``, they will generate a warning.
  Default is ``False``.

DMODEL_ALLOWED_MEMORY
  Used by
  ``jwst.outlier_detection.OutlierDetectionStep`` and
  ``jwst.resample.ResampleStep``. When defined, determines how much of currently
  available memory should be used to instantiated an output resampled image. If
  not defined, no check is made.

  Examples would be: ``1.0`` would allow all available memory to be used. ``0.5``
  would allow only half the available memory to be used.

For flag or boolean variables, any value in ``('true', 't', 'yes', 'y')`` or a
non-zero number, will evaluate as ``True``. Any value in ``('false', 'f', 'no',
'n', '0')`` will evaluate as ``False``. The values are case-insensitive.

All of the environment variables have equivalent function arguments in the API
for the relevant code. The environment variables are used only if explicit
values had not been used in a script. In other words, values in code override
environment variables.
