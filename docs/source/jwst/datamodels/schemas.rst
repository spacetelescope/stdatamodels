Schemas
=======

What is a schema?
-----------------
A schema is a machine- and human-readable description of the structure of a datamodel;
it defines the expected data and metadata fields, their types, and any constraints
on their values. When a datamodel is read from or saved
to a file, a model's tree is validated against its schema
to ensure that it conforms to the expected structure.

``stdatamodels`` defines its metadata using `Draft 4 of
the JSON Schema specification
<http://tools.ietf.org/html/draft-zyp-json-schema-04>`_, but
``stdatamodels`` uses YAML for the syntax.

Data model schemas
------------------

.. note::

   For users familiar with the
   `JWST Keyword Dictionary <https://mast.stsci.edu/portal/Mashup/Clients/jwkeywords/index.html>`_
   it is important to note that the keyword dictionary is not used by stdatamodels.
   Instead the datamodel schemas contain independent descriptions of the JWST files.
   This is in part due to the unique requirements for the keyword dictionary and
   datamodel schemas. If inconsistencies are found please open an
   `issue <https://github.com/spacetelescope/stdatamodels/issues>`_.

JWST datamodels are in part defined by an ASDF schema.
For example ``RampModel`` uses the schema found in ``ramp.schema.yaml``.
These data model schemas typically contain many references
to other schemas to allow common structures to be shared across
data models. Here is a (partial) example:

.. code-block:: yaml

  %YAML 1.1
  ---
  $schema: "http://stsci.edu/schemas/asdf/asdf-schema-1.1.0"
  id: "http://stsci.edu/schemas/jwst_datamodel/ramp.schema"
  allOf:
  - $ref: core.schema
  - $ref: bunit.schema
  - $ref: photometry.schema
  - $ref: wcsinfo.schema
  - type: object

Each ``$ref`` above will pull in the common structure defined
in the referenced schema. All data model schemas reference
``core.schema``.


Reference file schemas
----------------------

JWST reference file schemas are similar to the data model schemas
but use a different set of shared schemas.

.. code-block:: yaml

  %YAML 1.1
  ---
  $schema: "http://stsci.edu/schemas/asdf/asdf-schema-1.1.0"
  id: "http://stsci.edu/schemas/jwst_datamodel/dark.schema"
  title: Dark current data model
  allOf:
  - $ref: referencefile.schema
  - $ref: keyword_exptype.schema
  - $ref: keyword_readpatt.schema

Note that reference file schemas ``$ref`` ``referencefile.schema``.

Reference file keywords and use by CRDS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Reference file schemas often contain references to ``keyword_*``
schemas (for example ``keyword_exptype.schema`` above). These define
standard keywords that are used for reference file selection
by CRDS. For the above example, the ``exptype`` from a science file
is matched with the CRDS ``parkey`` of the same name to determine
the appropriate reference file. When crafting (or updating) a reference file
schema it's important to make sure that the referenced keyword
schemas match those expected by CRDS.

This can involve adding "pattern" keywords (for example
``keyword_pexptype.schema``) when a reference file might be used
for several keyword values. For example, if a single reference file
matches all filters, it can reference ``keyword_pfilter.schema`` and then
CRDS can use a "pattern" to avoid hosting copies of the same file for every filter.
See the
`CRDS docs <https://hst-crds.stsci.edu/static/users_guide/reference_conventions.html#matching-keyword-patterns>`_
for more details about patterns.

Transform schemas
-----------------
The WCS transforms defined in :py:mod:`stdatamodels.jwst.transforms`
also have associated ASDF schemas for validating their representation
in ASDF files. See :ref:`the transforms documentation <jwst-transforms-index>`
for more details.

Custom Schema Keywords
----------------------

In addition to the standard JSON Schema keywords, ``stdatamodels``
also supports the following additional keywords.  For users, these
keywords should behave the same as their standard JSON Schema counterparts.
This section is included primarily for developers to understand how the
``stdatamodels`` schema language has been extended.

Arrays
^^^^^^

The following keywords have to do with validating n-dimensional arrays:

- ``ndim``: The number of dimensions of the array.

- ``max_ndim``: The maximum number of dimensions of the array.

- ``datatype``: For defining an array, ``datatype`` should be a string.
  For defining a table, it should be a list.

- **array**: ``datatype`` should be one of the following strings,
  representing fixed-length datatypes:

  bool8, int8, int16, int32, int64, uint8, uint16, uint32,
  uint64, float16, float32, float64, float128, complex64,
  complex128, complex256

Or, for fixed-length strings, an array ``[ascii, XX]`` where
``XX`` is the maximum length of the string.

(Datatypes whose size depend on the platform are not supported
since this would make files less portable).

- **table**: ``datatype`` should be a list of dictionaries.  Each
  element in the list defines a column and has the following keys:

  - ``datatype``: A string to select the type of the column.
    This is the same as the ``datatype`` for an array (as
    described above).

  - ``name`` (optional): An optional name for the column.

  - ``shape`` (optional): The shape of the data in the column.
    May be either an integer (for a single-dimensional shape),
    or a list of integers.

FITS-specific Schema Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``stdatamodels`` also adds some new keys to the schema language in
order to handle reading and writing FITS files.  These attributes all
have the prefix ``fits_``.

- ``fits_keyword``: Specifies the FITS keyword to store the value in.
  Must be a string with a maximum length of 8 characters.

- ``fits_hdu``: Specifies the FITS HDU to store the value in.  May be
  a number (to specify the nth HDU) or a name (to specify the
  extension with the given ``EXTNAME``).  By default this is set to 0,
  and therefore refers to the primary HDU.
