.. -*- coding: utf-8 -*-


Defining a new model type
=========================

In this tutorial, we'll go through the process of creating a new type
of model. This example will be built as a third-party Python package, i.e. not
part of ``stdatamodels`` itself.  Doing so adds a few extra wrinkles
to the process, and it's most helpful to show what those wrinkles are.

We will name our new model ``BadpixModel``, and it will be designed to hold
data quality information about bad pixels in an image, some metadata about
those pixels, and a required custom ``reference_data`` array.

Directory layout
----------------

The bare minimum directory layout for a Python package that creates a
custom model is as below::

  .
  |-- lib
  |   |--- __init__.py
  |   |--- badpix.py
  |   |--- schemas
  |       |--- badpix.schema.yaml
  |   |--- tests
  |       |--- __init__.py
  |       |--- test_badpix.py
  |--- setup.py

The main pieces are the new schema in ``badpix.schema.yaml``,
the custom model class in ``badpix.py``, a
``setup.py`` file to install the package, and some unit tests and
associated data.  Normally, you would also have some code that *uses*
the custom model included in the package, but that isn't included in
this minimal example.

The schema file
----------------

Let's start with the schema file, ``badpix.schema.yaml``.
There are a few things it needs to do:

   1) It should contain all of the core metadata from the core schema
      that ships with ``stdatamodels``.  In JSON Schema parlance, this
      schema "extends" the core schema.

   2) Define the data arrays it needs. In this case, we will define
      a data quality (DQ) array containing information about bad pixels.  This will be
      an integer for each pixel where each bit is ascribed a particular meaning.
      We will also define the ``reference_data`` array of 32-bit floats representing
      some custom type of information that every ``BadpixModel`` instance is assumed
      to have.

   3) Define a table describing what each of the bit fields in the
      DQ array means.  This will have three columns: one for the
      bit field's number (a power of 2), one for a name token to
      identify it, and one with a human-readable description.

At the top level, every JSON schema must be a mapping (dictionary) of
type "object", and should include the core schema:

.. code-block:: yaml

  allOf:
     - $ref: "http://jwst.stsci.edu/schemas/core.schema.yaml"
     - type: object
       properties:
          ...

There's a lot going on in this one item.  ``$ref`` declares the schema
fragment that we want to include (the "base class" schema).  Here, the
``$ref`` mapping causes the system to go out and fetch the content at
the given URL, and then replace the mapping with that content.

The ``$ref`` URL can be a relative URL, in which case it is relative
to the schema file where ``$ref`` is used.  In our case, however, it's
an absolute URL.  Before you visit that URL to see what's there, I'll
save you the trouble: there is nothing at that HTTP address.  The host
``jwst.stsci.edu`` is recognized as a "special" address by the
system that causes the schema to be looked up alongside installed
Python code.  For example, to refer to a (hypothetical)
``my_instrument`` schema that ships with a Python package called
``astroboy``, use the following URL::

  http://jwst.stsci.edu/schemas/astroboy/my_instrument.schema.yaml

The "package" portion may be omitted to refer to schemas in the
``stdatamodels`` core, which is how we arrive at the URL we're using
here::

  http://jwst.stsci.edu/schemas/core.schema.yaml

.. note::

   At some time in the future, we will actually be hosting schemas at
   a URL similar to the one above.  This will allow schemas to be
   shared with tools built in languages other than Python.  Until we
   have that hosting established, this works quite well and does not
   require any coordination among Python packages that define new
   models.  Keep an eye out if you use this feature, though -- the
   precise URL used may change.

The next part of the file describes the array data; that is, things
that are Numpy arrays on the Python side and images or tables on the
FITS side.

First, we describe the main arrays, ``"dq"`` and ``"reference_data"``.
They are both declared to be 2-dimensional. Each element of the DQ array
is an unsigned 16-bit integer, defaults to being zero-filled, and maps onto
the FITS extension "DQ". The ``reference_data`` array has 32-bit float type,
defaults to being filled with 2s, and maps to the FITS extension "REFERENCE".

.. code-block:: yaml

    properties:
      dq:
        title: Bad pixel mask
        fits_hdu: DQ
        default: 0
        ndim: 2
        datatype: uint16
      reference_data:
        title: Array needed by all model instances
        fits_hdu: REFERENCE
        default: 2.0
        datatype: float32

The next entry describes a table that will store the mapping between
bit fields and their meanings.  This table has four columns:

   - ``BIT``: The value of the bit field (a power of 2)

   - ``VALUE``: The value resulting when raising 2 to the BIT power

   - ``NAME``: The name used to refer to the bit field

   - ``DESCRIPTION``: A longer, human-readable description of the bit field

.. code-block:: yaml

        dq_def:
          title: DQ flag definitions
          fits_hdu: DQ_DEF
          dtype:
            - name: BIT
              datatype: uint32
            - name: VALUE
              datatype: uint32
            - name: NAME
              datatype: [ascii, 40]
            - name: DESCRIPTION
              datatype: [ascii, 80]


And finally, we add a metadata element that is specific to this
format.  To avoid recomputing it repeatedly, we'd like to store a sum
of all of the "bad" (i.e. non-zero) pixels stored in the bad pixel
mask array.  In the model, we want to refer to this value as
``model.meta.bad_pixel_count``.  In the FITS file, lets store this in
the primary header in a keyword named ``BPCOUNT``:

.. code-block:: yaml

        meta:
          properties:
            bad_pixel_count:
              type: integer
              title: Total count of all bad pixels
              fits_keyword: BPCOUNT


That's all there is to the schema file, and that's the hardest part.

The model class
----------------

Now, let's see how this schema is tied in with a new Python class for
the model.

First, we need to import the :class:`~stdatamodels.jwst.datamodels.JwstDataModel`
class, which is the base class for all models::

  from stdatamodels.jwst.datamodels import JwstDataModel

Then we create a new Python class that inherits from
:class:`~stdatamodels.jwst.datamodels.JwstDataModel`, and
set its ``schema_url`` class member to point to the schema that we just
defined above:

.. code-block:: python

  class BadpixModel(JwstDataModel):
      """
      Custom handling of bad pixels.

      Attributes
      ----------
      dq : numpy array
          The data quality array.
      dq_def : numpy array
          The data quality definitions table.
      reference_data : np.ndarray
          An array that is assumed to exist for all BadpixModel instances,
          and is set to default on init.
      """
      schema_url = "badpix.schema.yaml"

This is already a fully-defined model class and we could use it as-is.
For example, we could do::

  dq = np.zeros((10,10), dtype=np.uint16)
  model = BadpixModel(dq=dq)

This might seem a bit odd: how does BadpixModel know what to do with
the ``dq`` keyword argument?  The answer is that the base class constructor
assumes that any keyword arguments passed to it are meant to be array attributes of the model.
Many models therefore don't need to define a custom constructor at all - the default ``__init__``
behavior from the base class is sufficient.
See the docstring of :class:`~stdatamodels.jwst.datamodels.JwstDataModel` for more information
about what the base constructor does.

In the example above, the ``schema_url`` has all of the "magical" URL abilities
described earlier when we used the ``$ref`` feature.  However, here we
are using a relative URL.  In this case, it is relative to the file in
which this class is defined, with a small twist to avoid intermingling
Python code and schema files: It looks for the given file in a
directory called ``schemas`` inside the directory containing the
Python module in which the class is defined.

As an alternative, we could just as easily have said that we want to
use the ``image`` schema from the core without defining any extra
elements, by setting ``schema_url`` to::

  schema_url = "http://jwst.stsci.edu/schemas/image.schema.yaml"

.. note::

  At this point you may be wondering why both the schema and the class
  have to inherit from base classes.  Certainly, it would have been
  more convenient to have the inheritance on the Python side
  automatically create the inheritance on the schema side (or vice
  versa).  The reason we can't is that the schema files are designed
  to be language-agnostic: it is possible to use them from an entirely
  different implementation of the ``stdatamodels`` framework possibly
  even written in a language other than Python.  So the schemas need
  to "stand alone" from the Python classes.  It's certainly possible
  to have the schema inherit from one thing and the Python class
  inherit from another, and the ``stdatamodels`` framework won't and
  can't really complain, but doing that is only going to lead to
  confusion, so just don't do it.


Let's now add a custom constructor to the class.
Custom constructors are useful when you want to do something special on init, such as
handle a custom type of ``init`` value, or set some default arrays.
All model constructors must take the highly polymorphic ``init`` value
as the first argument. This can be a file, another model, or
all kinds of other things. See the docstring of
:class:`~stdatamodels.jwst.datamodels.JwstDataModel` for more information.
Here, we are going to ensure that the ``reference_data`` array is always set on init,
initializing it to the default if not provided. This pattern can be helpful
if calling code assumes an attribute is always set and it's ok for the default
value to be passed:

.. code-block:: python

    def __init__(self, init=None, reference_data=None, **kwargs):
        """
        A data model to represent bad pixel masks.

        Parameters
        ----------
        init : any
            Any of the initializers supported by `~stdatamodels.jwst.datamodels.JwstDataModel`.
        reference_data : np.ndarray, optional
            An array to use for the `reference_data` attribute.
            Set to default of 2.0 if not provided.
        """
        super().__init__(init=init, **kwargs)

        if reference_data is None:
            self.reference_data = self.get_default("reference_data")
        else:
            self.reference_data = reference_data

Now we can do e.g.::

  model = BadpixModel((10,10))
  "reference_data" in model.instance # True
  print(model.reference_data) # shape (10,10), filled with value 2.0

The ``super...`` line is just the standard Python way of calling the
constructor of the base class.  The rest of the constructor sets the
reference value either to the provided array or to its default.

We also want to handle ``dq`` and ``dq_def``. These are common enough that
``stdatamodels`` provides a convenient way to map the ``dq`` array to the standard
values using its ``dq_def`` table on initialization. This is accomplished by letting
the model inherit from the
:class:`~stdatamodels.jwst.datamodels.model_base.DefaultDQMixin` class::

  from stdatamodels.jwst.datamodels import JwstDataModel, DefaultDQMixin

  class BadpixModel(JwstDataModel, DefaultDQMixin):
      ...

No additional code changes are needed.
Note that this also causes the ``dq`` array to be initialized into
memory when the class is constructed.

Our model has one additional nonstandard feature, which is that its "primary"
array is not called "data" (the assumed default). Instead, we want
the primary array to be called "dq".  To accomplish this, we must simply define
the special ``get_primary_array_name`` method to return the name of the primary array::
  
      def get_primary_array_name(self):
          return "dq"

Other methods of your class may provide additional conveniences on
top of the underlying file format.  This is completely optional and if
your file format is supported well enough by the underlying schema
alone, it may not be necessary to define any extra methods.

In the case of our example, it would be nice to have a function that,
given the name of a bit field, would return a new array that is ``True``
wherever that bit field is true in the main mask array.  Since the
order and content of the bit fields are defined in the ``dq_def``
table, the function should use it in order to do this work:

.. code-block:: python

    def get_mask_for_field(self, name):
        """
        Returns an array that is `True` everywhere a given bitfield is
        True in the mask.

        Parameters
        ----------
        name : str
            The name of the bit field to retrieve

        Returns
        -------
        array : boolean numpy array
            `True` everywhere the requested bitfield is `True`.  This
            is the same shape as the mask array.  This array is a copy
            and changes to it will not affect the underlying model.
        """
        # Find the field value that corresponds to the given name
        field_value = None
        for value, field_name, title in self.dq_def:
            if field_name == name:
                field_value = value
                break
        if field_value is None:
            raise ValueError("Field name {0} not found".format(name))

        # Create an array that is `True` only for the requested
        # bit field
        return (self.dq & field_value) > 0

One thing to note here: this array is semantically a "copy" of the
underlying data.  Most Numpy arrays in the model framework are
mutable, and we expect that changing their values will update the
model itself, and be saved out by subsequent saves to disk.  Since the
array we are returning here has no connection back to the model's main
data array (``dq``), it's helpful to remind the user of that in the
docstring, and not present it as a member or property, but as a getter
function.

Lastly, remember the ``meta.bad_pixel_count`` element we defined
above?  We need some way to make sure that whenever the file is
written out that it has the correct value.  The model may have been
loaded and modified.  For this, ``JwstDataModel`` has the ``on_save`` method
hook, which may be overridden by the subclass to add anything that
should happen just before saving:

.. code-block:: python

    def on_save(self, path):
        super().on_save(path)

        self.meta.bad_pixel_count = np.sum(self.dq != 0)

Note that here, like in the constructor, it is important to "chain up"
to the base class so that any things that the base class wants to do
right before saving also happen.

The `setup.py` script
---------------------

Writing a ``setup.py`` script is beyond the scope of this
tutorial but it's worth noting one thing.  Since the schema files are
not Python files, they are not automatically picked up by ``setuptools``,
and must be included in the ``package_data`` option.  A complete, yet
minimal, ``setup.py`` is presented below:

.. code-block:: python

  #!/usr/bin/env python

  from setuptools import setup

  setup(
      name='badpix',
      description='Custom model example for jwst.datamodels',
      packages=['badpix', 'badpix.tests'],
      package_dir={'badpix': 'lib'},
      package_data={'badpix': ['schemas/*.schema.yaml'],}
      )

Using the new model
-------------------

The new model can now be used.  For example, to get the locations of
all of the "hot" pixels::

   from lib.badpix import BadpixModel

   with BadpixModel("bad_pixel_mask.fits") as dm:
       hot_pixels = dm.get_mask_for_field('HOT')

A table-based model
-------------------

In addition to n-dimensional data arrays, models can also contain tabular
data. For example, the photometric correction reference file used in the
JWST calibration pipeline consists of a table with several columns. The schema
file for one of these models looks like this:

.. code-block:: yaml

    title: NIRISS SOSS photometric flux conversion data model
    allOf:
      - $ref: "referencefile.schema.yaml"
      - $ref: "keyword_exptype.schema.yaml"
      - $ref: "keyword_pexptype.schema.yaml"
      - $ref: "keyword_pixelarea.schema.yaml"
      - type: object
        properties:
          phot_table:
            title: Photometric flux conversion factors table
            fits_hdu: PHOTOM
            datatype:
              - name: filter
                datatype: [ascii, 12]
              - name: pupil
                datatype: [ascii, 15]
              - name: order
                datatype: int16
              - name: photmj
                datatype: float32
              - name: uncertainty
                datatype: float32
              - name: nelem
                datatype: int16
              - name: wavelength
                datatype: float32
                ndim: 1
              - name: relresponse
                datatype: float32
                ndim: 1
              - name: reluncertainty
                datatype: float32
                ndim: 1

In this particular table the first 6 columns contain scalar entries of types
string, float, and integer. The entries in the final 3 columns, on the other
hand, contain 1-D float arrays (vectors). The "ndim" attribute is used to
specify the number of dimensions the arrays are allowed to have.

The corresponding python module containing the data model class is quite
simple:

.. code-block:: python

    class NisSossPhotomModel(ReferenceFileModel):
        """
        A data model for NIRISS SOSS photom reference files.
        """
        schema_url = "nissoss_photom.schema"
    
    def get_primary_array_name(self):
        return "phot_table"
